@echo off
echo ========================================
echo    FSN System - Local Agent Setup
echo ========================================
echo.

echo [1/4] Installing Node.js dependencies...
cd local-agent
call npm install
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/4] Setting up local agent...
call node setup.js
if %errorlevel% neq 0 (
    echo ERROR: Failed to setup local agent
    pause
    exit /b 1
)

echo.
echo [3/4] Starting local agent...
echo Make sure your phone is connected via USB!
echo Press any key to start the agent...
pause

echo.
echo [4/4] Starting agent...
call node agent.js

pause
