# PowerShell execution script for Big Data PySpark Pipeline
$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " Running PySpark Big Data Processing Pipeline" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (!(Test-Path $pythonExe)) {
    Write-Host "Virtual environment not found. Creating .venv..." -ForegroundColor Yellow
    python -m venv .venv
    & .\.venv\Scripts\pip.exe install -r backend/requirements.txt
}

Write-Host "Executing PySpark Pipeline via $pythonExe..." -ForegroundColor Green
& $pythonExe big_data/run_pipeline.py

Write-Host "Pipeline execution complete! Check outputs in data/processed/" -ForegroundColor Green
