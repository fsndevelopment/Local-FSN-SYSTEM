#!/bin/bash

echo "🍎 FSN iPhone Connection"
echo "========================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed!"
    echo "   Please install Node.js from: https://nodejs.org"
    exit 1
fi

# Install axios if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install axios
fi

# Run the simple agent
echo "🚀 Starting FSN Mac Agent..."
echo ""
node SIMPLE-MAC-AGENT.js