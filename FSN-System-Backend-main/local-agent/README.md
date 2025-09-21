# FSN Local Agent

This local agent bridges your physical phone to the cloud backend, allowing you to control your device from your website while keeping everything else on the cloud.

## 🚀 Quick Start

### 1. Prerequisites

**For macOS (iPhone):**
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install node appium ios-deploy libimobiledevice
npm install -g appium
appium driver install uiautomator2
appium driver install xcuitest
```

**For Windows (Android):**
```bash
# Install Node.js from https://nodejs.org/
# Install Android SDK Platform Tools
# Install Appium
npm install -g appium
appium driver install uiautomator2
```

### 2. Setup

```bash
# Clone or download the local agent
cd local-agent

# Install dependencies
npm install

# Run setup
npm run setup
```

### 3. Configure

The setup script will ask for:
- Your backend URL (e.g., `https://your-backend.onrender.com`)
- Log level (info/debug/error)

### 4. Start the Agent

```bash
# Start the agent
npm start

# Or on Windows
start.bat

# Or on macOS/Linux
./start.sh
```

## 📱 How It Works

1. **Local Agent** runs on your Mac/PC
2. **Starts Appium** server locally on port 4735
3. **Creates secure tunnel** using ngrok
4. **Registers with cloud backend** via API
5. **Discovers your phone** and registers it
6. **Proxies Appium commands** from cloud to your phone

## 🔧 Configuration

### Environment Variables

```bash
export BACKEND_URL="https://your-backend.onrender.com"
export LOG_LEVEL="info"
```

### Manual Configuration

Edit `config.js`:
```javascript
module.exports = {
    BACKEND_URL: 'https://your-backend.onrender.com',
    LOG_LEVEL: 'info'
};
```

## 📋 Device Requirements

### iPhone
- iOS device connected via USB
- Developer Mode enabled
- Trusted on your Mac
- Xcode installed (for WebDriverAgent)

### Android
- Android device connected via USB
- USB Debugging enabled
- Developer Options enabled
- Trusted on your PC

## 🔍 Troubleshooting

### Agent won't start
```bash
# Check if Appium is installed
appium --version

# Check if Node.js is installed
node --version

# Check logs
tail -f agent.log
```

### Phone not detected
```bash
# For iPhone
idevice_id -l

# For Android
adb devices
```

### Tunnel issues
```bash
# Check ngrok status
curl http://localhost:4040/api/tunnels

# Restart agent
npm start
```

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:3001/health
```

### Agent Status
The agent provides real-time status at:
- Health endpoint: `http://localhost:3001/health`
- Device discovery: `http://localhost:3001/devices`

## 🔄 Updates

To update the agent:
```bash
git pull
npm install
npm start
```

## 🆘 Support

If you encounter issues:
1. Check the logs in `agent.log`
2. Verify your phone is connected and trusted
3. Ensure your backend URL is correct
4. Check that all prerequisites are installed

## 📝 Logs

Logs are stored in:
- Console output (real-time)
- `agent.log` file (persistent)

Log levels:
- `error`: Only errors
- `info`: General information (default)
- `debug`: Detailed debugging information
