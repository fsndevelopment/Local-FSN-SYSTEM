#!/usr/bin/env node

/**
 * FSN Local Agent
 * Bridges physical devices to cloud backend via secure tunnel
 */

const express = require('express');
const axios = require('axios');
const WebSocket = require('ws');
const ngrok = require('ngrok');
const cron = require('node-cron');
const winston = require('winston');
const { spawn, exec } = require('child_process');
const fs = require('fs');
const path = require('path');

// Load configuration
const configFile = require('./config.js');

// Configuration
const CONFIG = {
    // Cloud backend URL (your Render backend)
    BACKEND_URL: process.env.BACKEND_URL || configFile.BACKEND_URL || 'https://your-backend.onrender.com',
    
    // Local Appium configuration
    APPIUM_PORT: 4735,
    APPIUM_HOST: 'localhost',
    
    // Agent configuration
    AGENT_PORT: 3001,
    HEARTBEAT_INTERVAL: 30000, // 30 seconds
    
    // Device discovery
    DISCOVERY_INTERVAL: 60000, // 1 minute
    
    // Logging
    LOG_LEVEL: process.env.LOG_LEVEL || configFile.LOG_LEVEL || 'info'
};

// Logger setup
const logger = winston.createLogger({
    level: CONFIG.LOG_LEVEL,
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
    ),
    transports: [
        new winston.transports.Console({
            format: winston.format.combine(
                winston.format.colorize(),
                winston.format.simple()
            )
        }),
        new winston.transports.File({ filename: 'agent.log' })
    ]
});

class FSNLocalAgent {
    constructor() {
        this.app = express();
        this.appiumProcess = null;
        this.tunnelUrl = null;
        this.agentId = `agent_${Date.now()}`;
        this.registeredDevices = new Map();
        this.isRegistered = false;
        
        this.setupExpress();
        this.setupWebSocket();
        this.setupCronJobs();
    }

    setupExpress() {
        this.app.use(express.json());
        
        // Health check endpoint
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'healthy',
                agentId: this.agentId,
                appiumRunning: this.appiumProcess !== null,
                tunnelUrl: this.tunnelUrl,
                registeredDevices: Array.from(this.registeredDevices.keys()),
                timestamp: new Date().toISOString()
            });
        });

        // Appium proxy endpoints
        this.app.all('/appium/*', async (req, res) => {
            try {
                const appiumUrl = `http://${CONFIG.APPIUM_HOST}:${CONFIG.APPIUM_PORT}${req.path.replace('/appium', '')}`;
                
                const response = await axios({
                    method: req.method,
                    url: appiumUrl,
                    data: req.body,
                    headers: {
                        ...req.headers,
                        'content-type': 'application/json'
                    },
                    timeout: 30000
                });

                res.status(response.status).json(response.data);
            } catch (error) {
                logger.error('Appium proxy error:', error.message);
                res.status(500).json({ error: 'Appium proxy failed' });
            }
        });

        // Device discovery endpoint
        this.app.get('/devices', async (req, res) => {
            try {
                const devices = await this.discoverDevices();
                res.json({ devices });
            } catch (error) {
                logger.error('Device discovery error:', error.message);
                res.status(500).json({ error: 'Device discovery failed' });
            }
        });
    }

    setupWebSocket() {
        this.wss = new WebSocket.Server({ port: 8080 });
        
        this.wss.on('connection', (ws) => {
            logger.info('WebSocket client connected');
            
            ws.on('message', (message) => {
                try {
                    const data = JSON.parse(message);
                    this.handleWebSocketMessage(ws, data);
                } catch (error) {
                    logger.error('WebSocket message error:', error.message);
                }
            });

            ws.on('close', () => {
                logger.info('WebSocket client disconnected');
            });
        });
    }

    setupCronJobs() {
        // Heartbeat to backend
        cron.schedule('*/30 * * * * *', () => {
            this.sendHeartbeat();
        });

        // Device discovery
        cron.schedule('*/60 * * * * *', () => {
            this.discoverAndRegisterDevices();
        });
    }

    async start() {
        try {
            logger.info('🚀 Starting FSN Local Agent...');
            
            // Start Appium server
            await this.startAppium();
            
            // Create tunnel
            await this.createTunnel();
            
            // Register with backend
            await this.registerWithBackend();
            
            // Start Express server
            this.app.listen(CONFIG.AGENT_PORT, () => {
                logger.info(`✅ Agent running on port ${CONFIG.AGENT_PORT}`);
                logger.info(`🌐 Tunnel URL: ${this.tunnelUrl}`);
            });

            // Initial device discovery
            await this.discoverAndRegisterDevices();

        } catch (error) {
            logger.error('❌ Failed to start agent:', error.message);
            process.exit(1);
        }
    }

    async startAppium() {
        return new Promise((resolve, reject) => {
            logger.info(`🔧 Starting Appium server on port ${CONFIG.APPIUM_PORT}...`);
            
            // Check if Appium is already running
            exec(`powershell -Command "try { Invoke-WebRequest -Uri 'http://${CONFIG.APPIUM_HOST}:${CONFIG.APPIUM_PORT}/status' -UseBasicParsing | Select-Object -ExpandProperty Content } catch { '' }"`, (error, stdout) => {
                if (!error && stdout.includes('value')) {
                    logger.info('✅ Appium server already running');
                    resolve();
                    return;
                }

                // Start Appium server
                this.appiumProcess = spawn('appium', [
                    'server',
                    '--port', CONFIG.APPIUM_PORT.toString(),
                    '--allow-insecure', 'adb_shell',
                    '--log-level', 'info'
                ], {
                    stdio: 'pipe'
                });

                this.appiumProcess.stdout.on('data', (data) => {
                    const output = data.toString();
                    if (output.includes('Appium REST http interface listener started')) {
                        logger.info('✅ Appium server started successfully');
                        resolve();
                    }
                });

                this.appiumProcess.stderr.on('data', (data) => {
                    logger.warn('Appium stderr:', data.toString());
                });

                this.appiumProcess.on('error', (error) => {
                    logger.error('❌ Failed to start Appium:', error.message);
                    reject(error);
                });

                // Timeout after 30 seconds
                setTimeout(() => {
                    if (!this.appiumProcess) {
                        reject(new Error('Appium startup timeout'));
                    }
                }, 30000);
            });
        });
    }

    async createTunnel() {
        try {
            logger.info('🌐 Creating secure tunnel...');
            
            // Use ngrok to create tunnel
            this.tunnelUrl = await ngrok.connect({
                addr: CONFIG.AGENT_PORT,
                proto: 'http'
            });

            logger.info(`✅ Tunnel created: ${this.tunnelUrl}`);
            
            // Handle tunnel disconnection
            ngrok.on('disconnect', () => {
                logger.warn('⚠️ Tunnel disconnected, attempting to reconnect...');
                this.createTunnel();
            });

        } catch (error) {
            logger.error('❌ Failed to create tunnel:', error.message);
            throw error;
        }
    }

    async registerWithBackend() {
        try {
            const registrationData = {
                agentId: this.agentId,
                tunnelUrl: this.tunnelUrl,
                appiumUrl: `${this.tunnelUrl}/appium`,
                capabilities: {
                    platform: process.platform,
                    nodeVersion: process.version,
                    appiumPort: CONFIG.APPIUM_PORT
                },
                timestamp: new Date().toISOString()
            };

            const response = await axios.post(
                `${CONFIG.BACKEND_URL}/api/agents/register`,
                registrationData,
                { timeout: 10000 }
            );

            if (response.status === 200) {
                this.isRegistered = true;
                logger.info('✅ Successfully registered with backend');
            } else {
                throw new Error(`Registration failed: ${response.status}`);
            }

        } catch (error) {
            logger.error('❌ Failed to register with backend:', error.message);
            // Don't throw - we'll retry in heartbeat
        }
    }

    async sendHeartbeat() {
        if (!this.isRegistered) {
            await this.registerWithBackend();
            return;
        }

        try {
            await axios.post(
                `${CONFIG.BACKEND_URL}/api/agents/${this.agentId}/heartbeat`,
                {
                    status: 'online',
                    appiumRunning: this.appiumProcess !== null,
                    tunnelUrl: this.tunnelUrl,
                    registeredDevices: Array.from(this.registeredDevices.keys()),
                    timestamp: new Date().toISOString()
                },
                { timeout: 5000 }
            );
        } catch (error) {
            logger.warn('Heartbeat failed:', error.message);
            this.isRegistered = false;
        }
    }

    async discoverDevices() {
        const devices = [];

        try {
            // Discover Android devices
            const androidDevices = await this.discoverAndroidDevices();
            devices.push(...androidDevices);

            // Discover iOS devices (if on macOS)
            if (process.platform === 'darwin') {
                const iosDevices = await this.discoverIOSDevices();
                devices.push(...iosDevices);
            }

        } catch (error) {
            logger.error('Device discovery error:', error.message);
        }

        return devices;
    }

    async discoverAndroidDevices() {
        return new Promise((resolve) => {
            exec('adb devices -l', (error, stdout) => {
                const devices = [];
                
                if (error) {
                    logger.warn('ADB not found or failed');
                    resolve(devices);
                    return;
                }

                const lines = stdout.split('\n').slice(1);
                for (const line of lines) {
                    if (line.includes('device') && !line.includes('List of devices')) {
                        const parts = line.split(/\s+/);
                        const udid = parts[0];
                        
                        if (udid) {
                            devices.push({
                                udid,
                                platform: 'Android',
                                name: `Android-${udid.substring(0, 8)}`,
                                status: 'online',
                                lastSeen: new Date().toISOString()
                            });
                        }
                    }
                }

                resolve(devices);
            });
        });
    }

    async discoverIOSDevices() {
        return new Promise((resolve) => {
            exec('idevice_id -l', (error, stdout) => {
                const devices = [];
                
                if (error) {
                    logger.warn('libimobiledevice not found');
                    resolve(devices);
                    return;
                }

                const udids = stdout.trim().split('\n').filter(udid => udid.trim());
                
                for (const udid of udids) {
                    devices.push({
                        udid: udid.trim(),
                        platform: 'iOS',
                        name: `iOS-${udid.substring(0, 8)}`,
                        status: 'online',
                        lastSeen: new Date().toISOString()
                    });
                }

                resolve(devices);
            });
        });
    }

    async discoverAndRegisterDevices() {
        try {
            const devices = await this.discoverDevices();
            
            for (const device of devices) {
                if (!this.registeredDevices.has(device.udid)) {
                    await this.registerDevice(device);
                }
            }

        } catch (error) {
            logger.error('Device discovery and registration error:', error.message);
        }
    }

    async registerDevice(device) {
        try {
            const deviceData = {
                ...device,
                agentId: this.agentId,
                tunnelUrl: this.tunnelUrl,
                appiumUrl: `${this.tunnelUrl}/appium`
            };

            const response = await axios.post(
                `${CONFIG.BACKEND_URL}/api/devices/register`,
                deviceData,
                { timeout: 10000 }
            );

            if (response.status === 200) {
                this.registeredDevices.set(device.udid, device);
                logger.info(`✅ Registered device: ${device.name} (${device.udid})`);
            }

        } catch (error) {
            logger.error(`❌ Failed to register device ${device.udid}:`, error.message);
        }
    }

    handleWebSocketMessage(ws, data) {
        // Handle real-time commands from backend
        switch (data.type) {
            case 'start_device':
                this.handleStartDevice(data.deviceId);
                break;
            case 'stop_device':
                this.handleStopDevice(data.deviceId);
                break;
            default:
                logger.warn('Unknown WebSocket message type:', data.type);
        }
    }

    async handleStartDevice(deviceId) {
        logger.info(`🚀 Starting device: ${deviceId}`);
        // Implementation for starting device automation
    }

    async handleStopDevice(deviceId) {
        logger.info(`🛑 Stopping device: ${deviceId}`);
        // Implementation for stopping device automation
    }

    async stop() {
        logger.info('🛑 Stopping FSN Local Agent...');
        
        if (this.appiumProcess) {
            this.appiumProcess.kill();
        }

        if (this.tunnelUrl) {
            await ngrok.disconnect();
        }

        process.exit(0);
    }
}

// Handle graceful shutdown
process.on('SIGINT', async () => {
    logger.info('Received SIGINT, shutting down gracefully...');
    await agent.stop();
});

process.on('SIGTERM', async () => {
    logger.info('Received SIGTERM, shutting down gracefully...');
    await agent.stop();
});

// Start the agent
const agent = new FSNLocalAgent();
agent.start().catch(error => {
    logger.error('Failed to start agent:', error);
    process.exit(1);
});
