#!/bin/bash

echo "🚀 Setting up FSN Local Device Agent..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first:"
    echo "   brew install node"
    exit 1
fi

# Check if Appium is installed
if ! command -v appium &> /dev/null; then
    echo "❌ Appium is not installed. Installing..."
    npm install -g appium
    appium driver install uiautomator2
    appium driver install xcuitest
fi

# Check if tunnel service is available
if command -v cloudflared &> /dev/null; then
    echo "✅ Cloudflared found"
elif command -v ngrok &> /dev/null; then
    echo "✅ Ngrok found"
else
    echo "⚠️  No tunnel service found. Installing cloudflared..."
    brew install cloudflared
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Make agent executable
chmod +x local-device-agent.js

echo "✅ Setup complete!"
echo ""
echo "🔧 To start the agent:"
echo "   npm start"
echo ""
echo "📱 Make sure your iPhone is:"
echo "   - Connected via USB"
echo "   - Developer Mode enabled"
echo "   - Trusted on this Mac"
echo ""
echo "🌐 The agent will:"
echo "   - Start Appium on your Mac"
echo "   - Create a secure tunnel"
echo "   - Register with your cloud backend"
echo "   - Allow cloud backend to control your phone"
