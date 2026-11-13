# PowerShell script to launch the Flask REST API server
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (!(Test-Path $pythonExe)) {
    Write-Host "Virtual environment not found. Run scripts/run_pyspark_pipeline.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "Starting Flask REST API server on http://127.0.0.1:5000..." -ForegroundColor Cyan
& $pythonExe backend/app.py
