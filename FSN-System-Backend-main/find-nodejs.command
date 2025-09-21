#!/bin/bash

# Find Node.js on Mac - Diagnostic Script
echo "🔍 Finding Node.js on your Mac..."
echo "=================================="
echo ""

# Check common locations
echo "Checking common Node.js locations:"
echo ""

if [ -f "/usr/local/bin/node" ]; then
    echo "✅ Found Node.js at: /usr/local/bin/node"
    /usr/local/bin/node --version
elif [ -f "/opt/homebrew/bin/node" ]; then
    echo "✅ Found Node.js at: /opt/homebrew/bin/node"
    /opt/homebrew/bin/node --version
elif [ -f "/usr/bin/node" ]; then
    echo "✅ Found Node.js at: /usr/bin/node"
    /usr/bin/node --version
else
    echo "❌ Node.js not found in common locations"
    echo ""
    echo "Let's search your entire system..."
    echo "This may take a moment..."
    
    # Search for node
    NODE_PATHS=$(find /usr -name "node" -type f 2>/dev/null | head -5)
    if [ ! -z "$NODE_PATHS" ]; then
        echo "✅ Found Node.js at these locations:"
        echo "$NODE_PATHS"
        echo ""
        echo "To use Node.js, add this to your PATH:"
        echo "export PATH=\"$(dirname $(echo "$NODE_PATHS" | head -1)):\$PATH\""
    else
        echo "❌ Node.js not found anywhere on your system"
        echo "   Please install Node.js from: https://nodejs.org"
    fi
fi

echo ""
echo "Current PATH:"
echo $PATH
echo ""
echo "To fix the PATH issue, run one of these commands:"
echo "export PATH=\"/usr/local/bin:\$PATH\""
echo "export PATH=\"/opt/homebrew/bin:\$PATH\""
echo "export PATH=\"/usr/bin:\$PATH\""
echo ""
echo "Then try running the FSN Agent again!"
