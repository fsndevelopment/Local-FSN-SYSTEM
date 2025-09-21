#!/bin/bash

# FSN Agent - Guaranteed to work with your Node.js setup
echo "🍎 FSN Agent for Mac"
echo "===================="
echo ""

# Set the correct PATH for your Node.js installation
export PATH="/opt/homebrew/bin:$PATH"

# Check if we're in the right directory
if [ ! -f "local-agent/package.json" ]; then
    echo "❌ Error: Please run this from the extracted FSN-Agent-Mac-Complete folder"
    echo "   Make sure you extracted the zip file first"
    exit 1
fi

# Check if Node.js is now accessible
if ! command -v node &> /dev/null; then
    echo "❌ Node.js still not found!"
    echo "   Your Node.js is at: /opt/homebrew/bin/node"
    echo "   Please run: export PATH=\"/opt/homebrew/bin:\$PATH\""
    exit 1
fi

echo "✅ Node.js found: $(node --version)"
echo ""

# Check if dependencies are installed
if [ ! -d "local-agent/node_modules" ]; then
    echo "📦 Installing dependencies..."
    cd local-agent
    npm install
    cd ..
fi

# Start the agent
echo "🔐 Starting FSN Agent..."
echo "   Follow the instructions to pair with your license"
echo ""
cd local-agent
node pairing-agent.js
