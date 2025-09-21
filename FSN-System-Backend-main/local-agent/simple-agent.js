#!/usr/bin/env node

/**
 * FSN Simple Local Agent
 * Registers with backend and provides device discovery
 */

const axios = require('axios');
const winston = require('winston');
const { exec } = require('child_process');

// Configuration
const CONFIG = {
    BACKEND_URL: 'https://fsn-system-backend.onrender.com',
    AGENT_ID: `agent_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    HEARTBEAT_INTERVAL: 30000, // 30 seconds
    LOG_LEVEL: 'info'
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
        })
    ]
});

class SimpleAgent {
    constructor() {
        this.agentId = CONFIG.AGENT_ID;
        this.backendUrl = CONFIG.BACKEND_URL;
        this.heartbeatInterval = null;
        this.isRegistered = false;
    }

    async start() {
        try {
            logger.info('🚀 Starting FSN Simple Agent...');
            logger.info(`🆔 Agent ID: ${this.agentId}`);
            
            // Register with backend
            await this.registerWithBackend();
            
            // Start heartbeat
            this.startHeartbeat();
            
            // Initial device discovery
            await this.discoverAndRegisterDevices();
            
            logger.info('✅ Simple Agent started successfully!');
            logger.info('📱 Connect your phone via USB and enable USB Debugging');
            logger.info('🔄 Device discovery will run every 60 seconds');
            
        } catch (error) {
            logger.error('❌ Failed to start agent:', error.message);
            process.exit(1);
        }
    }

    async registerWithBackend() {
        try {
            const agentData = {
                agent_id: this.agentId,
                name: `Local Agent ${this.agentId}`,
                platform: 'Windows',
                appium_url: 'http://localhost:4735',
                status: 'online'
            };

            logger.info('📡 Registering with backend...');
            const response = await axios.post(`${this.backendUrl}/api/v1/agents/register`, agentData);
            
            if (response.status === 200) {
                this.isRegistered = true;
                logger.info('✅ Successfully registered with backend');
            }
        } catch (error) {
            logger.error('❌ Failed to register with backend:', error.message);
            throw error;
        }
    }

    async discoverAndRegisterDevices() {
        try {
            logger.info('🔍 Discovering connected devices...');
            
            // Use adb to discover Android devices
            const devices = await this.discoverAndroidDevices();
            
            if (devices.length > 0) {
                logger.info(`📱 Found ${devices.length} device(s):`, devices);
                
                // Register each device with the backend
                for (const device of devices) {
                    await this.registerDevice(device);
                }
            } else {
                logger.info('📱 No devices found. Make sure your phone is connected via USB and USB Debugging is enabled.');
            }
        } catch (error) {
            logger.error('❌ Device discovery failed:', error.message);
        }
    }

    async discoverAndroidDevices() {
        return new Promise((resolve) => {
            exec('adb devices', (error, stdout) => {
                if (error) {
                    logger.warn('⚠️ ADB not found or not working. Install Android SDK Platform Tools.');
                    resolve([]);
                    return;
                }

                const lines = stdout.split('\n');
                const devices = [];

                for (const line of lines) {
                    if (line.includes('\tdevice')) {
                        const udid = line.split('\t')[0].trim();
                        if (udid) {
                            devices.push({
                                udid: udid,
                                platform: 'Android',
                                name: `Android Device ${udid.substring(0, 8)}`,
                                status: 'online'
                            });
                        }
                    }
                }

                resolve(devices);
            });
        });
    }

    async registerDevice(device) {
        try {
            logger.info(`📱 Registering device: ${device.udid}`);
            
            // Check if device already exists in backend
            const response = await axios.get(`${this.backendUrl}/api/v1/devices`);
            const existingDevices = response.data;
            
            const existingDevice = existingDevices.find(d => d.udid === device.udid);
            
            if (existingDevice) {
                // Update existing device with agent assignment
                logger.info(`🔄 Updating existing device ${device.udid} with agent assignment`);
                
                const updateResponse = await axios.post(
                    `${this.backendUrl}/api/v1/devices/${existingDevice.id}/assign-agent`,
                    { agent_id: this.agentId }
                );
                
                if (updateResponse.status === 200) {
                    logger.info(`✅ Device ${device.udid} assigned to agent`);
                }
            } else {
                logger.info(`ℹ️ Device ${device.udid} not found in backend database`);
            }
        } catch (error) {
            logger.error(`❌ Failed to register device ${device.udid}:`, error.message);
        }
    }

    startHeartbeat() {
        this.heartbeatInterval = setInterval(async () => {
            try {
                if (this.isRegistered) {
                    await axios.post(`${this.backendUrl}/api/v1/agents/${this.agentId}/heartbeat`);
                    logger.debug('💓 Heartbeat sent');
                }
            } catch (error) {
                logger.warn('⚠️ Heartbeat failed:', error.message);
                // Try to re-register
                try {
                    await this.registerWithBackend();
                } catch (reRegisterError) {
                    logger.error('❌ Re-registration failed:', reRegisterError.message);
                }
            }
        }, CONFIG.HEARTBEAT_INTERVAL);
    }

    stop() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }
        logger.info('🛑 Simple Agent stopped');
    }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
    logger.info('🛑 Shutting down Simple Agent...');
    process.exit(0);
});

process.on('SIGTERM', () => {
    logger.info('🛑 Shutting down Simple Agent...');
    process.exit(0);
});

// Start the agent
const agent = new SimpleAgent();
agent.start().catch(error => {
    logger.error('❌ Fatal error:', error);
    process.exit(1);
});
