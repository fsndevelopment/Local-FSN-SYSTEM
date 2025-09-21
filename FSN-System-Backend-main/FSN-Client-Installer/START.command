#!/bin/bash

# FSN Phone Controller - Start Script
# Double-click this file to start the service

echo "🍎 FSN Phone Controller - Starting..."
echo "===================================="

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BACKEND_DIR="$HOME/FSN-Phone-Controller/backend"

# Check if backend exists
if [ ! -d "$BACKEND_DIR" ]; then
    echo "❌ Backend not found. Please run INSTALL.command first."
    echo ""
    echo "To install:"
    echo "   1. Double-click INSTALL.command"
    echo "   2. Or run: ./INSTALL.command"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Change to backend directory
cd "$BACKEND_DIR"

# Get local IP
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

echo ""
echo "🚀 Starting FSN Phone Controller..."
echo "📱 Your iPhone will be accessible at: http://$LOCAL_IP:8000"
echo "🌐 Frontend URL: https://fsndevelopment.com"
echo ""
echo "⚠️  IMPORTANT:"
echo "   - Make sure your iPhone is connected via USB"
echo "   - Trust this computer when prompted on your iPhone"
echo "   - Keep this terminal window open"
echo ""
echo "🛑 To stop: Press Ctrl+C"
echo ""

# Start the backend
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
