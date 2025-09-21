const express = require('express');
const { spawn } = require('child_process');
const axios = require('axios');
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');
const fs = require('fs');
const path = require('path');

// Load configuration
const configFile = require('./config.js');

const CONFIG = {
    // Cloud backend URL (your Render backend)
    BACKEND_URL: process.env.BACKEND_URL || configFile.BACKEND_URL || 'https://fsn-system-backend.onrender.com',
    // Local Appium settings
    APPIUM_HOST: 'localhost',
    APPIUM_PORT: 4741, // Device 4's port
    // Agent settings
    AGENT_ID: `real_agent_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    HEARTBEAT_INTERVAL: 10000, // 10 seconds
    // Logging
    LOG_LEVEL: process.env.LOG_LEVEL || configFile.LOG_LEVEL || 'info'
};

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

class RealAgent {
    constructor() {
        this.agentId = CONFIG.AGENT_ID;
        this.backendUrl = CONFIG.BACKEND_URL;
        this.appiumProcess = null;
        this.tunnelUrl = null;
        this.deviceUdid = 'ae6f609c40f74faeadc5a83c8c96bf8c6d0b3ccf'; // Device 4
    }

    async start() {
        try {
            logger.info('🚀 Starting FSN Real Agent (Mac Production)...');
            logger.info(`🆔 Agent ID: ${this.agentId}`);
            logger.info(`📱 Target Device: ${this.deviceUdid}`);
            logger.info(`🔌 Appium Port: ${CONFIG.APPIUM_PORT}`);

            // Register with backend
            await this.registerWithBackend();
            
            // Start Appium server
            await this.startAppium();
            
            // Start heartbeat
            setInterval(() => this.sendHeartbeat(), CONFIG.HEARTBEAT_INTERVAL);

            logger.info('✅ Real Agent started successfully');
            logger.info('📱 Appium is running and ready to control your physical device!');
            
        } catch (error) {
            logger.error('❌ Failed to start real agent:', error.message);
            process.exit(1);
        }
    }

    async registerWithBackend() {
        logger.info('📡 Registering with backend...');
        try {
            const response = await axios.post(`${this.backendUrl}/api/v1/agents/register`, {
                agent_id: this.agentId,
                appium_url: `http://${CONFIG.APPIUM_HOST}:${CONFIG.APPIUM_PORT}`,
                tunnel_url: `http://${CONFIG.APPIUM_HOST}:${CONFIG.APPIUM_PORT}`, // Same as appium_url for local
                status: 'online',
                platform: 'iOS'
            });
            logger.info('✅ Agent registered with backend:', response.data);
        } catch (error) {
            logger.error('❌ Failed to register with backend:', error.message);
            throw error;
        }
    }

    async startAppium() {
        return new Promise((resolve, reject) => {
            logger.info(`🔧 Starting Appium server on port ${CONFIG.APPIUM_PORT}...`);
            
            // Appium command with device-specific settings
            const appiumArgs = [
                'server',
                '--port', CONFIG.APPIUM_PORT.toString(),
                '--allow-insecure', 'adb_shell',
                '--log-level', 'info',
                '--session-override',
                '--relaxed-security'
            ];

            this.appiumProcess = spawn('appium', appiumArgs, {
                stdio: ['pipe', 'pipe', 'pipe'],
                env: { ...process.env }
            });

            this.appiumProcess.stdout.on('data', (data) => {
                const output = data.toString();
                logger.info('📱 Appium:', output.trim());
                
                if (output.includes('Appium REST http interface listener started')) {
                    logger.info('✅ Appium server started successfully');
                    resolve();
                }
            });

            this.appiumProcess.stderr.on('data', (data) => {
                const error = data.toString();
                logger.error('❌ Appium Error:', error.trim());
            });

            this.appiumProcess.on('close', (code) => {
                logger.warn(`⚠️ Appium process exited with code ${code}`);
            });

            this.appiumProcess.on('error', (error) => {
                logger.error('❌ Failed to start Appium:', error.message);
                reject(error);
            });

            // Timeout after 30 seconds
            setTimeout(() => {
                if (!this.appiumProcess || this.appiumProcess.killed) {
                    reject(new Error('Appium startup timeout'));
                }
            }, 30000);
        });
    }

    async sendHeartbeat() {
        try {
            await axios.post(`${this.backendUrl}/api/v1/agents/${this.agentId}/heartbeat`);
            logger.debug('❤️ Heartbeat sent');
        } catch (error) {
            logger.warn('💔 Failed to send heartbeat:', error.message);
        }
    }

    async stop() {
        logger.info('🛑 Stopping Real Agent...');
        
        if (this.appiumProcess) {
            this.appiumProcess.kill();
            logger.info('🔌 Appium server stopped');
        }
        
        process.exit(0);
    }
}

// Handle graceful shutdown
process.on('SIGINT', async () => {
    logger.info('🛑 Received SIGINT, shutting down gracefully...');
    const agent = new RealAgent();
    await agent.stop();
});

process.on('SIGTERM', async () => {
    logger.info('🛑 Received SIGTERM, shutting down gracefully...');
    const agent = new RealAgent();
    await agent.stop();
});

// Start the agent
const agent = new RealAgent();
agent.start();
