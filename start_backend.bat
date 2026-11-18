@echo off
title Flask Backend Server - Customer Analytics
cd /d "%~dp0"
echo ===================================================
echo Starting Flask Backend Server (http://127.0.0.1:5000)...
echo ===================================================
if not exist ".venv\Scripts\python.exe" (
    echo Error: Python virtual environment not found in .venv!
    pause
    exit /b 1
)
.venv\Scripts\python.exe backend\app.py
pause

