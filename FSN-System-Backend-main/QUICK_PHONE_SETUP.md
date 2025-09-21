# 🚀 Quick Phone Setup Guide

## The Problem
Your device `ae6f609c40f74faeadc5a83c8c96bf8c6d0b3ccf` exists in the database but has no agent assigned to it. This is why you're getting the 503 error.

## The Solution
You need to run a local agent on your computer to bridge your physical phone to the cloud system.

## Step-by-Step Setup

### 1. Prerequisites
- ✅ Node.js installed on your computer
- ✅ Your phone connected via USB
- ✅ USB Debugging enabled on your phone

### 2. Quick Setup (Windows)

**Option A: Run the batch file**
```bash
# Double-click this file:
setup-local-agent.bat
```

**Option B: Run the PowerShell script**
```powershell
# Right-click and "Run with PowerShell":
setup-local-agent.ps1
```

### 3. Manual Setup

If the scripts don't work, run these commands manually:

```bash
# Navigate to local agent folder
cd local-agent

# Install dependencies
npm install

# Setup the agent
node setup.js

# Start the agent (make sure phone is connected!)
node agent.js
```

### 4. What Happens Next

1. **Agent Registration**: The local agent will register itself with your cloud backend
2. **Device Discovery**: It will discover your connected phone
3. **Tunnel Creation**: It will create a secure tunnel to expose your phone to the cloud
4. **Device Assignment**: Your device will be automatically assigned to the agent

### 5. Verify It's Working

After the agent starts, check:
- Your device should appear as "online" in the web interface
- The 503 error should be resolved
- You should be able to start the device process

## Troubleshooting

### If you get "No devices found":
- Make sure your phone is connected via USB
- Enable USB Debugging in Developer Options
- Try a different USB cable/port

### If you get "Agent registration failed":
- Check your internet connection
- Verify the backend URL is correct
- Check the agent logs for specific errors

### If the device still shows 503 error:
- Wait 30 seconds for the agent to fully register
- Try refreshing the web interface
- Check that the device is assigned to an agent in the database

## Need Help?

If you're still having issues, check the agent logs for specific error messages and let me know what you see!
