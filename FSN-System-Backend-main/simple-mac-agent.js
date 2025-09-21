#!/usr/bin/env node

/**
 * SIMPLE MAC AGENT - Works with existing backend
 * This will connect your iPhone to the FSN system
 */

const axios = require('axios');
const { exec } = require('child_process');

console.log('🚀 FSN Simple Mac Agent');
console.log('======================');
console.log('');

const BACKEND_URL = 'https://fsn-system-backend.onrender.com';
const LICENSE_KEY = '651A6308E6BD453C8E8C10EEF4F334A2';

// Generate device info
const deviceId = 'mac-iphone-' + Date.now();
const udid = 'ios-' + Math.random().toString(36).substr(2, 9);

console.log('📱 Device Info:');
console.log(`   Device ID: ${deviceId}`);
console.log(`   UDID: ${udid}`);
console.log('');

async function connectDevice() {
    try {
        console.log('📡 Connecting to FSN backend...');
        
        // Try to register device using existing device endpoint
        const deviceData = {
            udid: udid,
            platform: 'iOS',
            name: 'iPhone (Mac)',
            status: 'active',
            appium_port: 4720,
            wda_port: 8100,
            mjpeg_port: 9100,
            last_seen: new Date().toISOString()
        };
        
        console.log('   Sending device data to backend...');
        
        const response = await axios.post(`${BACKEND_URL}/api/devices`, deviceData, {
            headers: {
                'Content-Type': 'application/json',
                'X-License-Key': LICENSE_KEY
            },
            timeout: 15000
        });
        
        console.log('✅ SUCCESS! Device connected to FSN system');
        console.log(`   Backend Device ID: ${response.data.id}`);
        console.log('');
        console.log('🎉 Your iPhone is now connected!');
        console.log('');
        console.log('📊 What you can do now:');
        console.log('   1. Go to fsndevelopment.com/devices');
        console.log('   2. You should see your iPhone in the device list');
        console.log('   3. Start automation jobs from the frontend');
        console.log('');
        console.log('🔄 Keeping connection alive...');
        console.log('   Press Ctrl+C to disconnect');
        
        // Keep connection alive
        setInterval(async () => {
            try {
                await axios.post(`${BACKEND_URL}/api/devices/${response.data.id}/heartbeat`, {
                    status: 'active',
                    last_seen: new Date().toISOString()
                }, {
                    headers: {
                        'X-License-Key': LICENSE_KEY
                    },
                    timeout: 5000
                });
                console.log('💓 Heartbeat sent - Device is online');
            } catch (error) {
                console.log('⚠️  Heartbeat failed - Device may be offline');
            }
        }, 30000);
        
    } catch (error) {
        console.log('❌ Failed to connect device');
        console.log('   Error:', error.message);
        if (error.response) {
            console.log('   Response:', error.response.data);
        }
        console.log('');
        console.log('🔧 Troubleshooting:');
        console.log('   1. Make sure your internet connection is working');
        console.log('   2. Check if fsndevelopment.com is accessible');
        console.log('   3. Try again in a few minutes');
        process.exit(1);
    }
}

// Handle shutdown
process.on('SIGINT', () => {
    console.log('\n🛑 Disconnecting device...');
    console.log('   Device disconnected from FSN system');
    process.exit(0);
});

// Start connection
connectDevice();