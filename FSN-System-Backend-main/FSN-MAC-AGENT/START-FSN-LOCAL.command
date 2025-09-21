#!/bin/bash

echo "🍎 FSN Local Backend for Mac"
echo "============================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "   Please install Python 3 from: https://python.org"
    exit 1
fi

# Install required packages
echo "📦 Installing required packages..."
pip3 install fastapi uvicorn requests psutil

echo ""
echo "🚀 Starting FSN Local Backend..."
echo "   This will connect to your frontend at fsndevelopment.com"
echo "   Press Ctrl+C to stop"
echo ""

# Start the local backend
python3 local-backend.py
