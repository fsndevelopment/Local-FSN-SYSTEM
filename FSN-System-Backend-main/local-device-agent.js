#!/usr/bin/env node

/**
 * FSN Local Device Agent
 * 
 * Runs on your Mac to bridge cloud backend to physical devices
 * - Starts Appium server locally
 * - Exposes via secure tunnel (ngrok/cloudflared)
 * - Registers with cloud backend
 */

const { spawn } = require('child_process');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

class LocalDeviceAgent {
  constructor() {
    this.appiumProcess = null;
    this.tunnelUrl = null;
    this.backendUrl = 'https://fsn-system-backend.onrender.com';
    this.licenseKey = '651A6308E6BD453C8E8C10EEF4F334A2';
    this.deviceId = 'device-1757926045137-7to4mmwao';
    this.appiumPort = 4735;
  }

  async start() {
    console.log('🚀 Starting FSN Local Device Agent...');
    
    try {
      // 1. Start Appium server
      await this.startAppium();
      
      // 2. Start tunnel (ngrok or cloudflared)
      await this.startTunnel();
      
      // 3. Register with cloud backend
      await this.registerWithBackend();
      
      // 4. Keep running
      this.keepAlive();
      
    } catch (error) {
      console.error('❌ Agent failed to start:', error.message);
      process.exit(1);
    }
  }

  async startAppium() {
    console.log('📱 Starting Appium server...');
    
    return new Promise((resolve, reject) => {
      this.appiumProcess = spawn('appium', [
        'server',
        '--port', this.appiumPort.toString(),
        '--allow-insecure', 'adb_shell',
        '--relaxed-security'
      ], {
        stdio: 'pipe'
      });

      this.appiumProcess.stdout.on('data', (data) => {
        const output = data.toString();
        if (output.includes('Appium REST http interface listener started')) {
          console.log('✅ Appium server started on port', this.appiumPort);
          resolve();
        }
      });

      this.appiumProcess.stderr.on('data', (data) => {
        console.error('Appium error:', data.toString());
      });

      this.appiumProcess.on('error', (error) => {
        reject(new Error(`Failed to start Appium: ${error.message}`));
      });

      // Timeout after 30 seconds
      setTimeout(() => {
        reject(new Error('Appium startup timeout'));
      }, 30000);
    });
  }

  async startTunnel() {
    console.log('🌐 Starting secure tunnel...');
    
    // Try cloudflared first, fallback to ngrok
    try {
      await this.startCloudflared();
    } catch (error) {
      console.log('Cloudflared not available, trying ngrok...');
      try {
        await this.startNgrok();
      } catch (ngrokError) {
        throw new Error('No tunnel service available. Install cloudflared or ngrok.');
      }
    }
  }

  async startCloudflared() {
    return new Promise((resolve, reject) => {
      const cloudflared = spawn('cloudflared', [
        'tunnel',
        '--url', `http://localhost:${this.appiumPort}`,
        '--no-autoupdate'
      ], {
        stdio: 'pipe'
      });

      cloudflared.stdout.on('data', (data) => {
        const output = data.toString();
        const urlMatch = output.match(/https:\/\/[a-z0-9-]+\.trycloudflare\.com/);
        if (urlMatch) {
          this.tunnelUrl = urlMatch[0];
          console.log('✅ Cloudflared tunnel:', this.tunnelUrl);
          resolve();
        }
      });

      cloudflared.stderr.on('data', (data) => {
        console.error('Cloudflared error:', data.toString());
      });

      setTimeout(() => {
        reject(new Error('Cloudflared tunnel timeout'));
      }, 30000);
    });
  }

  async startNgrok() {
    return new Promise((resolve, reject) => {
      const ngrok = spawn('ngrok', [
        'http', this.appiumPort.toString(),
        '--log', 'stdout'
      ], {
        stdio: 'pipe'
      });

      ngrok.stdout.on('data', (data) => {
        const output = data.toString();
        const urlMatch = output.match(/https:\/\/[a-z0-9-]+\.ngrok\.io/);
        if (urlMatch) {
          this.tunnelUrl = urlMatch[0];
          console.log('✅ Ngrok tunnel:', this.tunnelUrl);
          resolve();
        }
      });

      ngrok.stderr.on('data', (data) => {
        console.error('Ngrok error:', data.toString());
      });

      setTimeout(() => {
        reject(new Error('Ngrok tunnel timeout'));
      }, 30000);
    });
  }

  async registerWithBackend() {
    console.log('🔗 Registering with cloud backend...');
    
    try {
      const response = await axios.post(`${this.backendUrl}/api/v1/devices/register-agent`, {
        tunnel_url: this.tunnelUrl,
        appium_port: this.appiumPort,
        license_key: this.licenseKey,
        device_id: this.deviceId
      }, {
        headers: {
          'Content-Type': 'application/json',
          'X-License-Key': this.licenseKey,
          'X-Device-ID': this.deviceId
        }
      });

      console.log('✅ Registered with backend:', response.data);
    } catch (error) {
      console.error('❌ Failed to register with backend:', error.response?.data || error.message);
      throw error;
    }
  }

  keepAlive() {
    console.log('🔄 Agent running... Press Ctrl+C to stop');
    
    // Heartbeat every 30 seconds
    setInterval(async () => {
      try {
        await axios.post(`${this.backendUrl}/api/v1/devices/heartbeat`, {
          tunnel_url: this.tunnelUrl,
          status: 'active'
        }, {
          headers: {
            'X-License-Key': this.licenseKey,
            'X-Device-ID': this.deviceId
          }
        });
        console.log('💓 Heartbeat sent');
      } catch (error) {
        console.error('❌ Heartbeat failed:', error.message);
      }
    }, 30000);

    // Graceful shutdown
    process.on('SIGINT', () => {
      console.log('\n🛑 Shutting down agent...');
      if (this.appiumProcess) {
        this.appiumProcess.kill();
      }
      process.exit(0);
    });
  }
}

// Start the agent
const agent = new LocalDeviceAgent();
agent.start().catch(console.error);
