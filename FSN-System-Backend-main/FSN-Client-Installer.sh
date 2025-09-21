#!/bin/bash

# FSN Phone Controller - Client Installer
# This script makes it super easy for clients to connect their iPhone

echo "🍎 FSN Phone Controller - Client Installer"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed."
    echo "📥 Please install Python 3 first:"
    echo "   Visit: https://www.python.org/downloads/"
    echo "   Or run: brew install python3"
    echo ""
    read -p "Press Enter after installing Python 3..."
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed."
    echo "📥 Please install pip3 first:"
    echo "   Visit: https://pip.pypa.io/en/stable/installation/"
    echo ""
    read -p "Press Enter after installing pip3..."
fi

# Create FSN directory
FSN_DIR="$HOME/FSN-Phone-Controller"
mkdir -p "$FSN_DIR"
cd "$FSN_DIR"

echo "📥 Downloading FSN Phone Controller..."
echo ""

# Download the backend code
if [ ! -d "backend" ]; then
    echo "⬇️  Downloading FSN backend..."
    curl -L -o fsn-backend.zip "https://github.com/fsndevelopment/FSN-System-Backend/archive/refs/heads/main.zip"
    unzip -q fsn-backend.zip
    mv FSN-System-Backend-main backend
    rm fsn-backend.zip
    echo "✅ Backend downloaded"
fi

# Install dependencies
echo "📦 Installing dependencies..."
cd backend
pip3 install -r requirements.txt
echo "✅ Dependencies installed"

# Get local IP
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

echo ""
echo "🎉 Setup Complete!"
echo "=================="
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
