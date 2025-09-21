# FSN System - Local Agent Setup Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    FSN System - Local Agent Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/4] Installing Node.js dependencies..." -ForegroundColor Yellow
Set-Location "local-agent"
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[2/4] Setting up local agent..." -ForegroundColor Yellow
node setup.js
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to setup local agent" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[3/4] Starting local agent..." -ForegroundColor Yellow
Write-Host "Make sure your phone is connected via USB!" -ForegroundColor Green
Write-Host "Press any key to start the agent..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host ""
Write-Host "[4/4] Starting agent..." -ForegroundColor Yellow
node agent.js

Read-Host "Press Enter to exit"
