#!/bin/bash

# FSN Agent Simple Launcher
# Double-click this file to run the agent

echo "🚀 Starting FSN Agent..."
echo ""

# Check if we're in the right directory
if [ ! -f "local-agent/package.json" ]; then
    echo "❌ Error: Please run this from the FSN-System-Backend-main folder"
    echo "   Make sure you're in the correct directory"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    # Try common Node.js installation paths
    if [ -f "/usr/local/bin/node" ]; then
        export PATH="/usr/local/bin:$PATH"
    elif [ -f "/opt/homebrew/bin/node" ]; then
        export PATH="/opt/homebrew/bin:$PATH"
    elif [ -f "/usr/bin/node" ]; then
        export PATH="/usr/bin:$PATH"
    else
        echo "❌ Node.js is not found in PATH!"
        echo "   Please add Node.js to your PATH or install from: https://nodejs.org"
        echo "   Common locations: /usr/local/bin/node or /opt/homebrew/bin/node"
        echo "   Try running: export PATH=\"/usr/local/bin:\$PATH\""
        exit 1
    fi
fi

# Check if dependencies are installed
if [ ! -d "local-agent/node_modules" ]; then
    echo "📦 Installing dependencies..."
    cd local-agent
    npm install
    cd ..
fi

# Start the agent
echo "🔐 Starting pairing process..."
echo "   Follow the instructions to pair with your license"
echo ""
cd local-agent
node pairing-agent.js
