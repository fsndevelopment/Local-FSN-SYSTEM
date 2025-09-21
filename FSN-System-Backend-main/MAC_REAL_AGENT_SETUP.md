# 🍎 FSN Real Agent Setup for Mac

This guide will help you set up a **real local agent** on your Mac that actually runs Appium and controls your physical iPhone.

## 📋 Prerequisites

1. **Mac computer** with your iPhone connected via USB
2. **Node.js** installed (version 16 or higher)
3. **Appium** installed globally
4. **Xcode** installed (for iOS development)
5. **iPhone** with Developer Mode enabled

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
# Install Node.js (if not already installed)
brew install node

# Install Appium globally
npm install -g appium

# Install iOS driver
appium driver install xcuitest

# Verify installation
appium-doctor --ios
```

### 2. Setup Local Agent

```bash
# Navigate to the local-agent directory
cd local-agent

# Install dependencies
npm install

# Make setup script executable
chmod +x setup-mac.sh

# Run setup
./setup-mac.sh
```

### 3. Start the Real Agent

```bash
# Start the real agent (this will start Appium on port 4741)
node real-agent.js
```

## 📱 Device Configuration

Your iPhone should be configured as follows:
- **UDID**: `ae6f609c40f74faeadc5a83c8c96bf8c6d0b3ccf`
- **Appium Port**: `4741`
- **WDA Port**: `8109`
- **MJPEG Port**: `9396`
- **WDA Bundle ID**: `com.device11.wd11`

## 🔧 What the Real Agent Does

1. **Registers with the cloud backend** at `https://fsn-system-backend.onrender.com`
2. **Starts Appium server** on port 4741 (your device's configured port)
3. **Creates a tunnel** so the cloud can communicate with your local device
4. **Sends heartbeats** to keep the connection alive
5. **Actually controls your physical iPhone** through Appium

## 📊 Monitoring

When the agent is running, you'll see logs like:
```
🚀 Starting FSN Real Agent (Mac Production)...
🆔 Agent ID: real_agent_1757941234567_abc123
📱 Target Device: ae6f609c40f74faeadc5a83c8c96bf8c6d0b3ccf
🔌 Appium Port: 4741
📡 Registering with backend...
✅ Agent registered with backend
🔧 Starting Appium server on port 4741...
📱 Appium: Appium REST http interface listener started on 0.0.0.0:4741
✅ Appium server started successfully
✅ Real Agent started successfully
📱 Appium is running and ready to control your physical device!
```

## 🎯 Testing

1. **Start the agent** on your Mac
2. **Go to your frontend** at `https://fsndevelopment.com`
3. **Click "Connect"** on Device 4 (Iphone11)
4. **Check the logs** - you should see:
   - Agent registration
   - Appium server starting
   - Real session creation
   - Device actually connecting

## 🔍 Troubleshooting

### Appium Won't Start
```bash
# Check if port 4741 is available
lsof -i :4741

# Kill any process using the port
kill -9 <PID>

# Try starting Appium manually
appium --port 4741 --allow-insecure adb_shell
```

### Device Not Found
```bash
# Check if device is connected
xcrun devicectl list devices

# Check if device is trusted
# On your iPhone: Settings > General > Device Management > Trust This Computer
```

### Agent Registration Fails
- Check your internet connection
- Verify the backend URL in `config.js`
- Check if the backend is running at `https://fsn-system-backend.onrender.com`

## 🎉 Success Indicators

When everything is working, you'll see:
- ✅ Agent registered with backend
- ✅ Appium server started on port 4741
- ✅ Device shows as "connected" in frontend
- ✅ Real Appium session created
- ✅ Your iPhone actually responds to commands

## 🔄 Keeping It Running

The agent will:
- **Automatically restart** if Appium crashes
- **Send heartbeats** every 10 seconds
- **Reconnect** if the connection is lost
- **Log everything** for debugging

## 📞 Support

If you encounter issues:
1. Check the logs for error messages
2. Verify all prerequisites are installed
3. Ensure your iPhone is properly connected and trusted
4. Check that port 4741 is available

---

**This setup gives you REAL device control, not just mock sessions!** 🚀
