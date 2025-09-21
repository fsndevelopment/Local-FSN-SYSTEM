#!/bin/bash

# FSN Phone Controller - Uninstall Script
# This script removes the FSN Phone Controller from your Mac

echo "🍎 FSN Phone Controller - Uninstaller"
echo "====================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# FSN directory
FSN_DIR="$HOME/FSN-Phone-Controller"

print_info "This will remove the FSN Phone Controller from your Mac."
print_warning "This will delete all FSN files and data."
echo ""
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Uninstall cancelled."
    exit 0
fi

# Check if FSN directory exists
if [ -d "$FSN_DIR" ]; then
    print_info "Removing FSN directory: $FSN_DIR"
    rm -rf "$FSN_DIR"
    print_status "FSN directory removed"
else
    print_info "FSN directory not found, nothing to remove"
fi

# Check if any FSN processes are running
print_info "Checking for running FSN processes..."
FSN_PROCESSES=$(ps aux | grep -i fsn | grep -v grep)

if [ ! -z "$FSN_PROCESSES" ]; then
    print_warning "Found running FSN processes:"
    echo "$FSN_PROCESSES"
    echo ""
    print_info "Please stop these processes before uninstalling."
    echo "You can stop them by pressing Ctrl+C in the terminal where FSN is running."
    echo ""
    read -p "Press Enter after stopping the processes..."
fi

print_status "Uninstall complete!"
echo ""
print_info "The FSN Phone Controller has been removed from your Mac."
print_info "You can reinstall it anytime by running the installer again."
echo ""
