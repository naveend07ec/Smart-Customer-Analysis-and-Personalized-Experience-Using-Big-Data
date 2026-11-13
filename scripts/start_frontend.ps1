# PowerShell script to launch the React frontend dev server
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$frontendDir = Join-Path $projectRoot "frontend"

Set-Location $frontendDir

if (!(Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
}

Write-Host "Starting Vite React development server on http://localhost:3000..." -ForegroundColor Cyan
npm run dev
