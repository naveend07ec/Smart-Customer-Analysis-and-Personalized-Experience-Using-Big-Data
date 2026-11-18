@echo off
title Starting Smart Customer Analysis Platform
cd /d "%~dp0"
echo =========================================================
echo  Starting Smart Customer Analysis & Recommendation System
echo =========================================================
echo.
echo [1/2] Launching Flask REST API Backend (Port 5000)...
start "Flask Backend (Port 5000)" cmd /k "cd /d "%~dp0" && .venv\Scripts\python.exe backend\app.py"

timeout /t 3 /nobreak >nul

echo [2/2] Launching React Frontend Dashboard (Port 3000)...
start "React Dashboard (Port 3000)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo =========================================================
echo  Platform is running!
echo  - Backend API:  http://127.0.0.1:5000/api/health
echo  - Frontend UI:  http://localhost:3000
echo =========================================================
timeout /t 5 >nul

