# FSN Mac Agent

Simple Python agent to connect your iPhone to the FSN system.

## Files in this folder:
- `fsn_agent.py` - The main Python agent
- `CONNECT-IPHONE.command` - Mac command file to run the agent
- `README.md` - This file

## How to use:

### Option 1: Run the Python file directly
```bash
python3 fsn_agent.py
```

### Option 2: Use the Mac command file
1. Double-click `CONNECT-IPHONE.command`
2. If you get a security warning, right-click and select "Open"

## What it does:
- Connects your iPhone to the FSN system
- Shows up in your frontend device list at fsndevelopment.com/devices
- Keeps the connection alive
- No tokens or complex setup needed!

## Requirements:
- Python 3 installed on your Mac
- Internet connection
- iPhone connected via USB (optional, for actual automation)

## Troubleshooting:
- If Python is not found, install it from https://python.org
- Make sure your internet connection is working
- Check that fsndevelopment.com is accessible
