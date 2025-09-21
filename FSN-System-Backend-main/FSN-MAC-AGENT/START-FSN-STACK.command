#!/bin/bash

# macOS one-click starter: launches backend (port 8000) and frontend (port 3000)
# - Backend: FSN-System-Backend-main/FSN-MAC-AGENT/local-backend.py
# - Frontend: FSN-System-Frontend-main (npm run dev)

set -e

echo "🚀 FSN One-Click Start (Backend + Frontend)"
echo "=========================================="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR"
FRONTEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)/FSN-System-Frontend-main"

# Basic checks
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ Python 3 not found. Install from https://www.python.org/downloads/mac-osx/"
  exit 1
fi

if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "❌ Node.js/npm not found. Install via https://nodejs.org/"
  exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
  echo "❌ Frontend folder not found at: $FRONTEND_DIR"
  echo "   Make sure FSN-System-Frontend-main is at the same level as FSN-System-Backend-main"
  exit 1
fi

echo "🔧 Backend dir:   $BACKEND_DIR"
echo "🌐 Frontend dir:  $FRONTEND_DIR"

# Commands to run in separate Terminal tabs
BACKEND_CMD='cd "$BACKEND_DIR" && echo "📦 Installing backend deps (if needed)..." && python3 -m pip install -r requirements.txt >/dev/null 2>&1 || true && echo "🔐 License: set via POST http://localhost:8000/api/v1/license {\"license_key\":\"YOUR_KEY\"}" && echo "🚀 Starting backend on http://localhost:8000" && python3 local-backend.py'
FRONTEND_CMD='cd "$FRONTEND_DIR" && echo "📦 Installing frontend deps (if needed)..." && npm install >/dev/null 2>&1 || true && echo "🚀 Starting frontend on http://localhost:3000" && npm run dev'

# Open macOS Terminal with two tabs
osascript <<EOF
tell application "Terminal"
  activate
  do script "$BACKEND_CMD"
  delay 1
  do script "$FRONTEND_CMD"
end tell
EOF

echo "✅ Launched: Backend (8000) and Frontend (3000) in Terminal tabs"
echo "   If the frontend doesn't open automatically, visit: http://localhost:3000"
echo "   Backend health: http://localhost:8000/health"


