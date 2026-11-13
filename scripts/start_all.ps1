# Master Startup Script for Big Data Customer Analytics Platform
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting Smart Customer Analysis Platform" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verify Virtual Environment
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (!(Test-Path $pythonExe)) {
    Write-Host "Error: Virtual environment not found. Run scripts/run_pyspark_pipeline.ps1 first." -ForegroundColor Red
    exit 1
}

# 2. Start Backend Server in a new window
Write-Host "Launching Flask REST API server on http://127.0.0.1:5000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; & '$pythonExe' backend/app.py"

# Short pause to allow backend to bind port
Start-Sleep -Seconds 2

# 3. Start Frontend Dev Server in a new window
Write-Host "Launching React + Vite Frontend Dashboard on http://localhost:3000..." -ForegroundColor Green
$frontendDir = Join-Path $projectRoot "frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendDir'; npm run dev"

Write-Host ""
Write-Host "Both servers launched successfully!" -ForegroundColor Cyan
Write-Host "  * Backend API: http://127.0.0.1:5000/api/health" -ForegroundColor Yellow
Write-Host "  * Web Dashboard: http://localhost:3000" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
