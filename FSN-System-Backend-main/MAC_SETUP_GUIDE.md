# 🍎 Mac Setup Guide for FSN System

## Overview
This guide helps you set up the local agent on your Mac to connect your physical phone to the cloud system.

## Prerequisites
- ✅ Mac computer
- ✅ iPhone connected via USB
- ✅ Xcode installed (for iOS development)
- ✅ Node.js installed
- ✅ Homebrew (recommended)

## Step 1: Install Dependencies

### Install Node.js (if not already installed)
```bash
# Using Homebrew
brew install node

# Or download from https://nodejs.org
```

### Install Appium
```bash
npm install -g appium
npx appium driver install xcuitest  # For iOS
npx appium driver install uiautomator2  # For Android
```

### Install iOS Dependencies
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install ios-deploy
npm install -g ios-deploy

# Install libimobiledevice
brew install libimobiledevice
```

## Step 2: Set Up the Agent

### Clone/Download the Project
```bash
# Navigate to your project directory
cd /path/to/FSN-System-Backend-main/local-agent
```

### Install Dependencies
```bash
npm install
```

### Configure the Agent
```bash
node setup.js
```

When prompted:
- Backend URL: `https://fsn-system-backend.onrender.com`
- Log level: `info`

## Step 3: Connect Your Phone

### For iPhone:
1. Connect iPhone via USB
2. Trust your Mac when prompted on the phone
3. Enable Developer Mode in Settings > Privacy & Security > Developer Mode
4. Enable USB Debugging (if available)

### For Android:
1. Connect Android phone via USB
2. Enable Developer Options
3. Enable USB Debugging
4. Trust your computer when prompted

## Step 4: Start the Agent

### Start the Real Agent
```bash
node agent.js
```

### Or Start the Simple Agent (if Appium has issues)
```bash
node simple-agent.js
```

## Step 5: Verify Connection

1. Check the agent logs for successful registration
2. Check your web interface - device should appear as "online"
3. Try clicking "Connect" on your device in the web interface

## Troubleshooting

### Appium Won't Start
```bash
# Check if Appium is installed
npx appium --version

# Install missing drivers
npx appium driver install xcuitest
npx appium driver install uiautomator2

# Check iOS setup
ios-deploy --detect
```

### Device Not Detected
```bash
# For iOS
idevice_id -l  # Should list your device UDID

# For Android
adb devices  # Should list your device
```

### Agent Registration Fails
- Check your internet connection
- Verify the backend URL is correct
- Wait a few minutes for backend deployment to complete

## Expected Output

When everything works, you should see:
```
🚀 Starting FSN Local Agent...
✅ Appium server started successfully
✅ Tunnel created: https://abc123.ngrok.io
✅ Successfully registered with backend
📱 Found 1 device(s): [{"udid":"your-device-udid",...}]
✅ Device your-device-udid assigned to agent
✅ Agent running on port 3001
```

## Next Steps

Once the agent is running:
1. Your device should appear as "online" in the web interface
2. You can click "Connect" to start the device process
3. The 503 error should be resolved
4. You can now control your phone from the cloud!

## Need Help?

If you encounter issues:
1. Check the agent logs for specific error messages
2. Verify all dependencies are installed
3. Make sure your phone is properly connected
4. Check that the backend is accessible from your Mac
