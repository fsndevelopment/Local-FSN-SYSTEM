#!/usr/bin/env python3
"""
Create a simple Mac app for FSN clients
This will create a .app bundle that clients can just double-click
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def create_mac_app():
    """Create a Mac app bundle for FSN clients"""
    
    print("🍎 Creating FSN Mac App for Clients...")
    
    # Create app bundle structure
    app_name = "FSN-Phone-Controller"
    app_path = Path(f"{app_name}.app")
    
    # Remove existing app if it exists
    if app_path.exists():
        shutil.rmtree(app_path)
    
    # Create app bundle directories
    contents_path = app_path / "Contents"
    macos_path = contents_path / "MacOS"
    resources_path = contents_path / "Resources"
    
    for path in [contents_path, macos_path, resources_path]:
        path.mkdir(parents=True, exist_ok=True)
    
    # Create Info.plist
    info_plist = contents_path / "Info.plist"
    info_plist.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>FSN-Phone-Controller</string>
    <key>CFBundleIdentifier</key>
    <string>com.fsndevelopment.phone-controller</string>
    <key>CFBundleName</key>
    <string>FSN Phone Controller</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>""")
    
    # Create the main executable script
    main_script = macos_path / "FSN-Phone-Controller"
    main_script.write_text("""#!/bin/bash

# FSN Phone Controller - Simple Mac App
# This app connects your iPhone to the FSN cloud system

echo "🍎 FSN Phone Controller Starting..."
echo "=================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first:"
    echo "   Visit: https://www.python.org/downloads/"
    echo ""
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    echo ""
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
RESOURCES_DIR="$SCRIPT_DIR/../Resources"

# Check if this is the first run
if [ ! -f "$RESOURCES_DIR/requirements.txt" ]; then
    echo "🔧 First time setup - downloading FSN backend..."
    
    # Create resources directory
    mkdir -p "$RESOURCES_DIR"
    
    # Download the backend code
    cd "$RESOURCES_DIR"
    curl -L -o fsn-backend.zip "https://github.com/fsndevelopment/FSN-System-Backend/archive/refs/heads/main.zip"
    unzip -q fsn-backend.zip
    mv FSN-System-Backend-main/* .
    rm -rf FSN-System-Backend-main fsn-backend.zip
    
    echo "📦 Installing Python dependencies..."
    pip3 install -r requirements.txt
    
    echo "✅ Setup complete!"
fi

# Change to the backend directory
cd "$RESOURCES_DIR"

# Get the local IP address
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

echo ""
echo "🚀 Starting FSN Phone Controller..."
echo "📱 Your iPhone will be accessible at: http://$LOCAL_IP:8000"
echo "🌐 Frontend URL: https://fsndevelopment.com"
echo ""
echo "⚠️  Make sure your iPhone is connected via USB and trusted!"
echo "⚠️  Keep this window open while using the system!"
echo ""
echo "Press Ctrl+C to stop the service"
echo ""

# Start the backend
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
""")
    
    # Make the script executable
    os.chmod(main_script, 0o755)
    
    print(f"✅ Mac app created: {app_path}")
    print("")
    print("📱 For your clients:")
    print(f"1. Send them the '{app_path}' file")
    print("2. They just double-click it to run")
    print("3. It will automatically download and setup everything")
    print("4. Their iPhone will be accessible through the website")
    print("")
    print("🎯 The app will:")
    print("   - Download the FSN backend automatically")
    print("   - Install Python dependencies")
    print("   - Start the local server")
    print("   - Connect their iPhone to the cloud system")
    
    return app_path

if __name__ == "__main__":
    create_mac_app()
