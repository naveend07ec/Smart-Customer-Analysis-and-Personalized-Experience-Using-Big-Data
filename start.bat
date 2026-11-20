@echo off
setlocal

echo =====================================================================
echo   SMART Big Data Platform - Starting Services...
echo =====================================================================
echo.

:: Check virtual environment
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Please run setup.bat first.
    exit /b 1
)

:: 1. Start Flask Backend
echo [1/2] Starting Flask Backend REST API on http://127.0.0.1:5000 ...
start "SMART Backend API (Port 5000)" cmd /k ".venv\Scripts\python.exe backend\app.py"

:: Wait 3 seconds for backend to initialize
timeout /t 3 /nobreak >nul

:: 2. Start Frontend Dev Server
echo [2/2] Starting Vite React Frontend on http://localhost:3000 ...
cd frontend
start "SMART React Frontend (Port 3000)" cmd /k "npm run dev"
cd ..

:: Wait 2 seconds and open browser
timeout /t 2 /nobreak >nul
echo.
echo =====================================================================
echo   Both services are running!
echo   Frontend: http://localhost:3000
echo   Backend:  http://127.0.0.1:5000/api/health
echo =====================================================================
echo Opening dashboard in your browser...
start http://localhost:3000
exit /b 0

