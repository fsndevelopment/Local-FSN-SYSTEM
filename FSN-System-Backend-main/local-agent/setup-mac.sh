#!/bin/bash

echo "🍎 FSN Real Agent Setup for Mac"
echo "================================"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first:"
    echo "   brew install node"
    exit 1
fi

# Check if Appium is installed
if ! command -v appium &> /dev/null; then
    echo "❌ Appium is not installed. Installing Appium..."
    npm install -g appium
    npm install -g appium-doctor
fi

# Check if iOS driver is installed
if ! appium driver list | grep -q "xcuitest"; then
    echo "📱 Installing iOS driver..."
    appium driver install xcuitest
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Check Appium installation
echo "🔍 Checking Appium installation..."
appium-doctor --ios

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 To start the real agent:"
echo "   node real-agent.js"
echo ""
echo "📱 Make sure your iPhone is connected via USB and trusted!"
echo "🔧 The agent will start Appium on port 4741 for Device 4"
