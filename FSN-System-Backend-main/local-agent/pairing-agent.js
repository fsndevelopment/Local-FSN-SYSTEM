#!/usr/bin/env node

/**
 * FSN Pairing Agent
 * Updated agent with pairing and tunnel support
 */

const express = require('express');
const axios = require('axios');
const WebSocket = require('ws');
const { spawn, exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

// Load configuration
const configFile = require('./config.js');

// Configuration
const CONFIG = {
    BACKEND_URL: process.env.FSN_BACKEND_BASE || configFile.BACKEND_URL || 'https://fsn-system-backend.onrender.com',
    APPIUM_PORT: 4735,
    APPIUM_HOST: 'localhost',
    AGENT_PORT: 3001,
    HEARTBEAT_INTERVAL: 10000, // 10 seconds
    DISCOVERY_INTERVAL: 60000, // 1 minute
    LOG_LEVEL: process.env.LOG_LEVEL || configFile.LOG_LEVEL || 'info'
};

// Storage for agent credentials
const STORAGE_FILE = path.join(process.env.HOME || process.env.USERPROFILE, '.fsn-agent.json');

class FSNPairingAgent {
    constructor() {
        this.app = express();
        this.appiumProcess = null;
        this.tunnelProcess = null;
        this.tunnelUrl = null;
        this.agentId = null;
        this.agentToken = null;
        this.licenseId = null;
        this.registeredDevices = new Map();
        this.isPaired = false;
        this.isOnline = false;
        
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
                isPaired: this.isPaired,
                isOnline: this.isOnline,
                appiumRunning: this.appiumProcess !== null,
                tunnelUrl: this.tunnelUrl,
                registeredDevices: Array.from(this.registeredDevices.keys()),
                timestamp: new Date().toISOString()
            });
        });

        // Pairing status endpoint
        this.app.get('/pairing-status', (req, res) => {
            res.json({
                isPaired: this.isPaired,
                agentId: this.agentId,
                licenseId: this.licenseId
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
                console.error('Appium proxy error:', error.message);
                res.status(500).json({ error: 'Appium proxy failed' });
            }
        });

        // Device discovery endpoint
        this.app.get('/devices', async (req, res) => {
            try {
                const devices = await this.discoverDevices();
                res.json({ devices });
            } catch (error) {
                console.error('Device discovery error:', error.message);
                res.status(500).json({ error: 'Device discovery failed' });
            }
        });
    }

    setupWebSocket() {
        this.wss = new WebSocket.Server({ port: 8080 });
        
        this.wss.on('connection', (ws) => {
            console.log('WebSocket client connected');
            
            ws.on('message', (message) => {
                try {
                    const data = JSON.parse(message);
                    this.handleWebSocketMessage(ws, data);
                } catch (error) {
                    console.error('WebSocket message error:', error.message);
                }
            });

            ws.on('close', () => {
                console.log('WebSocket client disconnected');
            });
        });
    }

    setupCronJobs() {
        // Heartbeat to backend
        setInterval(() => {
            this.sendHeartbeat();
        }, CONFIG.HEARTBEAT_INTERVAL);

        // Device discovery
        setInterval(() => {
            this.discoverAndRegisterDevices();
        }, CONFIG.DISCOVERY_INTERVAL);
    }

    async loadCredentials() {
        try {
            if (fs.existsSync(STORAGE_FILE)) {
                const data = fs.readFileSync(STORAGE_FILE, 'utf8');
                const credentials = JSON.parse(data);
                
                this.agentId = credentials.agentId;
                this.agentToken = credentials.agentToken;
                this.licenseId = credentials.licenseId;
                this.isPaired = true;
                
                console.log('✅ Loaded agent credentials');
                return true;
            }
            return false;
        } catch (error) {
            console.error('❌ Failed to load credentials:', error.message);
            return false;
        }
    }

    async saveCredentials() {
        try {
            const credentials = {
                agentId: this.agentId,
                agentToken: this.agentToken,
                licenseId: this.licenseId,
                savedAt: new Date().toISOString()
            };
            
            fs.writeFileSync(STORAGE_FILE, JSON.stringify(credentials, null, 2));
            console.log('✅ Saved agent credentials');
        } catch (error) {
            console.error('❌ Failed to save credentials:', error.message);
        }
    }

    async start() {
        try {
            console.log('🚀 Starting FSN Pairing Agent...');
            
            // Try to load existing credentials
            const hasCredentials = await this.loadCredentials();
            
            if (!hasCredentials) {
                console.log('🔐 No credentials found. Starting pairing process...');
                await this.startPairingProcess();
            }
            
            // Start Appium server
            await this.startAppium();
            
            // Create tunnel
            await this.createTunnel();
            
            // Register with backend
            await this.registerWithBackend();
            
            // Start Express server
            this.app.listen(CONFIG.AGENT_PORT, () => {
                console.log(`✅ Agent running on port ${CONFIG.AGENT_PORT}`);
                console.log(`🌐 Tunnel URL: ${this.tunnelUrl}`);
            });

            // Initial device discovery
            await this.discoverAndRegisterDevices();

        } catch (error) {
            console.error('❌ Failed to start agent:', error.message);
            process.exit(1);
        }
    }

    async startPairingProcess() {
        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout
        });

        return new Promise((resolve) => {
            console.log('\n🔐 Agent Pairing Process');
            console.log('1. Go to your FSN web interface');
            console.log('2. Navigate to Devices > Connect Device');
            console.log('3. Click "Generate Pair Code"');
            console.log('4. Copy the pair token or scan the QR code');
            console.log('\nEnter the pair token:');
            
            rl.question('Pair token: ', async (pairToken) => {
                try {
                    await this.pairWithToken(pairToken.trim());
                    rl.close();
                    resolve();
                } catch (error) {
                    console.error('❌ Pairing failed:', error.message);
                    console.log('Please try again...');
                    rl.close();
                    await this.startPairingProcess();
                    resolve();
                }
            });
        });
    }

    async pairWithToken(pairToken) {
        try {
            console.log('🔐 Pairing with backend...');
            
            const response = await axios.post(`${CONFIG.BACKEND_URL}/api/v1/agents/pair`, {
                pair_token: pairToken,
                agent_name: `Agent-${process.platform}-${Date.now()}`,
                platform: process.platform,
                app_version: '1.0.0'
            });

            if (response.status === 200) {
                const data = response.data;
                this.agentId = data.agent_id;
                this.agentToken = data.agent_token;
                this.licenseId = data.license_id || 'default_license';
                this.isPaired = true;
                
                await this.saveCredentials();
                console.log('✅ Agent paired successfully!');
            } else {
                throw new Error(`Pairing failed: ${response.status}`);
            }

        } catch (error) {
            console.error('❌ Pairing failed:', error.message);
            throw error;
        }
    }

    async startAppium() {
        return new Promise((resolve, reject) => {
            console.log(`🔧 Starting Appium server on port ${CONFIG.APPIUM_PORT}...`);
            
            // Check if Appium is already running
            exec(`curl -s http://${CONFIG.APPIUM_HOST}:${CONFIG.APPIUM_PORT}/status`, (error, stdout) => {
                if (!error && stdout.includes('value')) {
                    console.log('✅ Appium server already running');
                    resolve();
                    return;
                }

                // Start Appium server
                this.appiumProcess = spawn('appium', [
                    '--port', CONFIG.APPIUM_PORT.toString(),
                    '--base-path', '/wd/hub',
                    '--allow-cors'
                ], {
                    stdio: 'pipe'
                });

                this.appiumProcess.stdout.on('data', (data) => {
                    const output = data.toString();
                    if (output.includes('Appium REST http interface listener started')) {
                        console.log('✅ Appium server started successfully');
                        resolve();
                    }
                });

                this.appiumProcess.stderr.on('data', (data) => {
                    console.warn('Appium stderr:', data.toString());
                });

                this.appiumProcess.on('error', (error) => {
                    console.error('❌ Failed to start Appium:', error.message);
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
            console.log('🌐 Creating secure tunnel...');
            
            // Use cloudflared by default, ngrok if NGROK_AUTHTOKEN is set
            const useNgrok = process.env.NGROK_AUTHTOKEN;
            
            if (useNgrok) {
                await this.createNgrokTunnel();
            } else {
                await this.createCloudflaredTunnel();
            }

        } catch (error) {
            console.error('❌ Failed to create tunnel:', error.message);
            throw error;
        }
    }

    async createCloudflaredTunnel() {
        return new Promise((resolve, reject) => {
            this.tunnelProcess = spawn('cloudflared', [
                'tunnel',
                '--url', `http://localhost:${CONFIG.AGENT_PORT}`
            ], {
                stdio: 'pipe'
            });

            let tunnelUrl = null;
            
            this.tunnelProcess.stderr.on('data', (data) => {
                const output = data.toString();
                console.log('Cloudflared:', output);
                
                // Look for tunnel URL in output
                const urlMatch = output.match(/https:\/\/[a-zA-Z0-9-]+\.trycloudflare\.com/);
                if (urlMatch) {
                    tunnelUrl = urlMatch[0];
                    this.tunnelUrl = tunnelUrl;
                    console.log(`✅ Cloudflared tunnel created: ${tunnelUrl}`);
                    resolve();
                }
            });

            this.tunnelProcess.on('error', (error) => {
                console.error('❌ Failed to start cloudflared:', error.message);
                reject(error);
            });

            // Timeout after 30 seconds
            setTimeout(() => {
                if (!tunnelUrl) {
                    reject(new Error('Cloudflared tunnel creation timeout'));
                }
            }, 30000);
        });
    }

    async createNgrokTunnel() {
        try {
            const ngrok = require('ngrok');
            
            this.tunnelUrl = await ngrok.connect({
                addr: CONFIG.AGENT_PORT,
                proto: 'http'
            });

            console.log(`✅ Ngrok tunnel created: ${this.tunnelUrl}`);
            
        } catch (error) {
            console.error('❌ Failed to create ngrok tunnel:', error.message);
            throw error;
        }
    }

    async registerWithBackend() {
        try {
            if (!this.isPaired) {
                console.log('⚠️ Agent not paired, skipping registration');
                return;
            }

            const devices = await this.discoverDevices();
            const endpoints = devices.map(device => ({
                udid: device.udid,
                local_appium_port: CONFIG.APPIUM_PORT,
                public_url: this.tunnelUrl,
                appium_base_path: '/wd/hub',
                wda_local_port: 8100, // Default WDA port
                mjpeg_port: 9100 // Default MJPEG port
            }));

            const response = await axios.post(
                `${CONFIG.BACKEND_URL}/api/v1/agents/register`,
                {
                    agent_name: `Agent-${process.platform}`,
                    license_id: this.licenseId,
                    endpoints: endpoints
                },
                {
                    headers: {
                        'Authorization': `Bearer ${this.agentToken}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: 10000
                }
            );

            if (response.status === 200) {
                this.isOnline = true;
                console.log('✅ Successfully registered with backend');
            } else {
                throw new Error(`Registration failed: ${response.status}`);
            }

        } catch (error) {
            console.error('❌ Failed to register with backend:', error.message);
            // Don't throw - we'll retry in heartbeat
        }
    }

    async sendHeartbeat() {
        if (!this.isPaired || !this.agentToken) {
            return;
        }

        try {
            const devices = await this.discoverDevices();
            const udids = devices.map(device => device.udid);

            await axios.post(
                `${CONFIG.BACKEND_URL}/api/v1/agents/heartbeat`,
                {
                    agent_id: this.agentId,
                    udids: udids,
                    uptime: process.uptime(),
                    version: '1.0.0'
                },
                {
                    headers: {
                        'Authorization': `Bearer ${this.agentToken}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: 5000
                }
            );
        } catch (error) {
            console.warn('Heartbeat failed:', error.message);
            this.isOnline = false;
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
            console.error('Device discovery error:', error.message);
        }

        return devices;
    }

    async discoverAndroidDevices() {
        return new Promise((resolve) => {
            exec('adb devices -l', (error, stdout) => {
                const devices = [];
                
                if (error) {
                    console.warn('ADB not found or failed');
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
                    console.warn('libimobiledevice not found');
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
                    this.registeredDevices.set(device.udid, device);
                    console.log(`📱 Discovered device: ${device.name} (${device.udid})`);
                }
            }

        } catch (error) {
            console.error('Device discovery error:', error.message);
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
                console.warn('Unknown WebSocket message type:', data.type);
        }
    }

    async handleStartDevice(deviceId) {
        console.log(`🚀 Starting device: ${deviceId}`);
        // Implementation for starting device automation
    }

    async handleStopDevice(deviceId) {
        console.log(`🛑 Stopping device: ${deviceId}`);
        // Implementation for stopping device automation
    }

    async stop() {
        console.log('🛑 Stopping FSN Pairing Agent...');
        
        if (this.appiumProcess) {
            this.appiumProcess.kill();
        }

        if (this.tunnelProcess) {
            this.tunnelProcess.kill();
        }

        process.exit(0);
    }
}

// Handle graceful shutdown
process.on('SIGINT', async () => {
    console.log('Received SIGINT, shutting down gracefully...');
    await agent.stop();
});

process.on('SIGTERM', async () => {
    console.log('Received SIGTERM, shutting down gracefully...');
    await agent.stop();
});

// Start the agent
const agent = new FSNPairingAgent();
agent.start().catch(error => {
    console.error('Failed to start agent:', error);
    process.exit(1);
});
