#!/bin/bash

# FSN Phone Controller - Mac Installer
# Double-click this file to install

echo "🍎 FSN Phone Controller - Mac Installer"
echo "======================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed."
    echo "📥 Please install Python 3 first:"
    echo "   1. Visit: https://www.python.org/downloads/"
    echo "   2. Download and install Python 3"
    echo "   3. Or run: brew install python3"
    echo ""
    read -p "Press Enter after installing Python 3..."
    
    # Check again
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 still not found. Please install it and try again."
        echo ""
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

echo "✅ Python 3 is installed"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed."
    echo "📥 Please install pip3 first:"
    echo "   1. Visit: https://pip.pypa.io/en/stable/installation/"
    echo "   2. Or run: python3 -m ensurepip --upgrade"
    echo ""
    read -p "Press Enter after installing pip3..."
    
    # Check again
    if ! command -v pip3 &> /dev/null; then
        echo "❌ pip3 still not found. Please install it and try again."
        echo ""
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

echo "✅ pip3 is installed"

# Create FSN directory
FSN_DIR="$HOME/FSN-Phone-Controller"
echo "📁 Creating FSN directory at: $FSN_DIR"
mkdir -p "$FSN_DIR"
cd "$FSN_DIR"

# Download the backend code
if [ ! -d "backend" ]; then
    echo "⬇️  Downloading FSN backend..."
    curl -L -o fsn-backend.zip "https://github.com/fsndevelopment/FSN-System-Backend/archive/refs/heads/main.zip"
    
    if [ $? -eq 0 ]; then
        echo "✅ Backend downloaded successfully"
        unzip -q fsn-backend.zip
        mv FSN-System-Backend-main backend
        rm fsn-backend.zip
        echo "✅ Backend extracted"
    else
        echo "❌ Failed to download backend. Please check your internet connection."
        echo ""
        read -p "Press Enter to exit..."
        exit 1
    fi
else
    echo "✅ Backend already exists, skipping download"
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
cd backend
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies. Please check your internet connection."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Get local IP
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

echo ""
echo "🎉 Installation Complete!"
echo "========================"
echo ""
echo "✅ Your FSN Phone Controller is ready!"
echo ""
echo "📱 To start the service:"
echo "   1. Double-click 'FSN-Phone-Controller.app'"
echo "   2. Or run: ./START.command"
echo ""
echo "🌐 After starting:"
echo "   1. Connect your iPhone via USB"
echo "   2. Trust this computer when prompted"
echo "   3. Go to https://fsndevelopment.com"
echo "   4. Your iPhone will be controllable!"
echo ""
echo "📁 Installation directory: $FSN_DIR"
echo "🔌 Local server will run at: http://$LOCAL_IP:8000"
echo ""
echo "Press Enter to start the service now, or close this window to start later..."
read -p ""

# Ask if user wants to start now
echo ""
echo "🚀 Starting FSN Phone Controller..."
echo ""

# Start the backend
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
