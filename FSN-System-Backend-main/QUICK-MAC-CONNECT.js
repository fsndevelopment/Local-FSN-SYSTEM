#!/usr/bin/env node

/**
 * Quick Mac Connect - Direct device registration
 * This will register your iPhone directly with the backend
 */

const axios = require('axios');
const { exec } = require('child_process');

console.log('🚀 Quick Mac Connect - Registering iPhone with FSN System');
console.log('');

const BACKEND_URL = 'https://fsn-system-backend.onrender.com';
const LICENSE_ID = '651A6308E6BD453C8E8C10EEF4F334A2';

// Generate a unique device ID
const deviceId = 'mac-iphone-' + Date.now();
const udid = 'ios-' + Math.random().toString(36).substr(2, 9);

console.log('📱 Device Info:');
console.log(`   Device ID: ${deviceId}`);
console.log(`   UDID: ${udid}`);
console.log('');

// Register device directly
async function registerDevice() {
    try {
        console.log('📡 Registering device with backend...');
        
        const deviceData = {
            udid: udid,
            platform: 'iOS',
            name: 'iPhone (Mac Agent)',
            status: 'active',
            appium_port: 4720,
            wda_port: 8100,
            mjpeg_port: 9100,
            last_seen: new Date().toISOString()
        };
        
        const response = await axios.post(`${BACKEND_URL}/api/devices`, deviceData, {
            headers: {
                'Content-Type': 'application/json',
                'X-License-Key': LICENSE_ID
            },
            timeout: 15000
        });
        
        console.log('✅ Device registered successfully!');
        console.log(`   Backend Device ID: ${response.data.id}`);
        console.log('');
        console.log('🎉 Your iPhone is now connected to the FSN system!');
        console.log('   You can now start automation jobs from the web interface');
        console.log('');
        console.log('📊 Next Steps:');
        console.log('   1. Go to fsndevelopment.com/devices');
        console.log('   2. You should see your iPhone in the device list');
        console.log('   3. Start automation jobs from the frontend');
        console.log('');
        console.log('🔄 Keep this terminal open to maintain connection');
        console.log('   Press Ctrl+C to disconnect');
        
        // Send heartbeat every 30 seconds
        setInterval(async () => {
            try {
                await axios.post(`${BACKEND_URL}/api/devices/${response.data.id}/heartbeat`, {
                    status: 'active',
                    last_seen: new Date().toISOString()
                }, {
                    headers: {
                        'X-License-Key': LICENSE_ID
                    },
                    timeout: 5000
                });
                console.log('💓 Heartbeat sent');
            } catch (error) {
                console.log('⚠️  Heartbeat failed:', error.message);
            }
        }, 30000);
        
    } catch (error) {
        console.log('❌ Failed to register device:', error.message);
        if (error.response) {
            console.log('   Response:', error.response.data);
        }
        process.exit(1);
    }
}

// Handle shutdown
process.on('SIGINT', () => {
    console.log('\n🛑 Disconnecting device...');
    process.exit(0);
});

// Start registration
registerDevice();
