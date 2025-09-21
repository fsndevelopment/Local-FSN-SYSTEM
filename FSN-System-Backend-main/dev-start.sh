#!/bin/bash

# Development startup script for FSN Appium Farm
# Starts both backend API and frontend development servers

echo "🚀 Starting FSN Appium Farm Development Environment"
echo "=================================================="

# Start API server in background
echo "📡 Starting FastAPI backend server..."
cd api
source venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000 --reload &
API_PID=$!
cd ..

# Wait for API to start
sleep 3

# Check if API is running
if curl -s http://127.0.0.1:8000/health > /dev/null; then
    echo "✅ API server running on http://127.0.0.1:8000"
else
    echo "❌ API server failed to start"
    kill $API_PID 2>/dev/null
    exit 1
fi

# Start Next.js frontend
echo "🎨 Starting Next.js frontend..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "🎉 Development environment started successfully!"
echo "📡 API Server: http://127.0.0.1:8000"
echo "🎨 Frontend: http://localhost:3000"
echo "📖 API Docs: http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down development environment..."
    kill $API_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ All servers stopped"
    exit 0
}

# Set trap to cleanup on Ctrl+C
trap cleanup SIGINT

# Wait for processes
wait
