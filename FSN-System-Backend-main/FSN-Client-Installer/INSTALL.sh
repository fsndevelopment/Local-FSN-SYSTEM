#!/bin/bash

# FSN Phone Controller - Main Installer
# This script sets up everything needed to connect your iPhone to the FSN system

echo "🍎 FSN Phone Controller - Installer"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Python 3 is installed
print_info "Checking Python 3 installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed."
    echo ""
    print_info "Please install Python 3 first:"
    echo "   1. Visit: https://www.python.org/downloads/"
    echo "   2. Download and install Python 3"
    echo "   3. Or run: brew install python3"
    echo ""
    read -p "Press Enter after installing Python 3..."
    
    # Check again
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 still not found. Please install it and try again."
        exit 1
    fi
fi

print_status "Python 3 is installed"

# Check if pip is installed
print_info "Checking pip installation..."
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed."
    echo ""
    print_info "Please install pip3 first:"
    echo "   1. Visit: https://pip.pypa.io/en/stable/installation/"
    echo "   2. Or run: python3 -m ensurepip --upgrade"
    echo ""
    read -p "Press Enter after installing pip3..."
    
    # Check again
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 still not found. Please install it and try again."
        exit 1
    fi
fi

print_status "pip3 is installed"

# Create FSN directory
FSN_DIR="$HOME/FSN-Phone-Controller"
print_info "Creating FSN directory at: $FSN_DIR"
mkdir -p "$FSN_DIR"
cd "$FSN_DIR"

# Download the backend code
if [ ! -d "backend" ]; then
    print_info "Downloading FSN backend..."
    curl -L -o fsn-backend.zip "https://github.com/fsndevelopment/FSN-System-Backend/archive/refs/heads/main.zip"
    
    if [ $? -eq 0 ]; then
        print_status "Backend downloaded successfully"
        unzip -q fsn-backend.zip
        mv FSN-System-Backend-main backend
        rm fsn-backend.zip
        print_status "Backend extracted"
    else
        print_error "Failed to download backend. Please check your internet connection."
        exit 1
    fi
else
    print_status "Backend already exists, skipping download"
fi

# Install dependencies
print_info "Installing Python dependencies..."
cd backend
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    print_status "Dependencies installed successfully"
else
    print_error "Failed to install dependencies. Please check your internet connection."
    exit 1
fi

# Get local IP
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

# Create start script
print_info "Creating start script..."
cat > ../START.sh << 'EOF'
#!/bin/bash

# FSN Phone Controller - Start Script
# Run this to start the FSN service

echo "🍎 FSN Phone Controller - Starting..."
echo "===================================="

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"

# Check if backend exists
if [ ! -d "$BACKEND_DIR" ]; then
    echo "❌ Backend not found. Please run INSTALL.sh first."
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
EOF

chmod +x ../START.sh
print_status "Start script created"

echo ""
print_status "Installation Complete!"
echo "========================"
echo ""
print_info "Your FSN Phone Controller is ready!"
echo ""
print_info "To start the service:"
echo "   1. Double-click START.sh"
echo "   2. Or run: ./START.sh"
echo ""
print_info "After starting:"
echo "   1. Connect your iPhone via USB"
echo "   2. Trust this computer when prompted"
echo "   3. Go to https://fsndevelopment.com"
echo "   4. Your iPhone will be controllable!"
echo ""
print_warning "Keep the terminal window open while using the system!"
echo ""
print_info "Installation directory: $FSN_DIR"
print_info "Local server will run at: http://$LOCAL_IP:8000"
echo ""
echo "Press Enter to start the service now, or close this window to start later..."
read -p ""

# Ask if user wants to start now
echo ""
print_info "Starting FSN Phone Controller..."
echo ""

# Start the backend
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
