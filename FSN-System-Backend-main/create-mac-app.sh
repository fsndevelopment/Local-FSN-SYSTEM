#!/bin/bash

# FSN Agent Mac App Creator
# Run this script on your Mac to create the app

echo "🍎 Creating FSN Agent Mac App..."

# Create the app bundle structure
mkdir -p "FSN-Agent.app/Contents/MacOS"
mkdir -p "FSN-Agent.app/Contents/Resources"

# Create the executable script
cat > "FSN-Agent.app/Contents/MacOS/FSN-Agent" << 'EOF'
#!/bin/bash

# FSN Agent Mac App Launcher
APP_DIR="$(dirname "$0")"
AGENT_DIR="$(dirname "$APP_DIR")/../../local-agent"

# Change to the agent directory
cd "$AGENT_DIR"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    osascript -e 'display dialog "Node.js is not installed. Please install Node.js first from https://nodejs.org" buttons {"OK"} default button "OK"'
    exit 1
fi

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    osascript -e 'display dialog "Installing dependencies... This may take a few minutes." buttons {"OK"} default button "OK"'
    npm install
fi

# Start the pairing agent
node pairing-agent.js
EOF

# Make it executable
chmod +x "FSN-Agent.app/Contents/MacOS/FSN-Agent"

# Create the Info.plist
cat > "FSN-Agent.app/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>FSN-Agent</string>
    <key>CFBundleIdentifier</key>
    <string>com.fsn.agent</string>
    <key>CFBundleName</key>
    <string>FSN Agent</string>
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
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
</dict>
</plist>
EOF

echo "✅ FSN Agent Mac App created successfully!"
echo "📱 You can now double-click 'FSN-Agent.app' to start the agent"
echo ""
echo "📋 Before running the app, make sure you have:"
echo "   1. Node.js installed (https://nodejs.org)"
echo "   2. Your iPhone connected via USB"
echo "   3. Developer Mode enabled on your iPhone"
echo ""
echo "🚀 Ready to go! Just double-click the app!"
