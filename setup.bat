@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo   SMART Big Data Customer Analytics - Automated Setup Script
echo =====================================================================
echo.

:: 1. Check Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10 or 3.11 from https://www.python.org/
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo [OK] Detected %PYTHON_VER%

:: 2. Check Node.js and npm
where npm >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js and npm are not installed or not in your PATH.
    echo Please install Node.js (v18+) from https://nodejs.org/
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version 2^>^&1') do set NODE_VER=%%i
echo [OK] Detected Node.js %NODE_VER%

:: 3. Check Java (Required by PySpark)
where java >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Java is not detected in your PATH.
    echo PySpark requires Java JDK 8 or 11.
    echo If Java is installed in a custom location, specify JAVA_HOME in .env
) else (
    echo [OK] Detected Java runtime in PATH.
)

:: 4. Setup Python Virtual Environment (.venv)
if not exist ".venv" (
    echo [INFO] Creating Python virtual environment in .venv...
    python -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
) else (
    echo [OK] Virtual environment .venv already exists.
)

:: 5. Install Python Dependencies
echo [INFO] Installing Python dependencies from requirements.txt...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.venv\Scripts\pip.exe install -r requirements.txt --quiet
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install Python dependencies.
    exit /b 1
)
echo [OK] Python dependencies installed successfully.

:: 6. Install Frontend Dependencies
echo [INFO] Installing Frontend npm dependencies in frontend/...
cd frontend
call npm install --silent
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install npm packages.
    cd ..
    exit /b 1
)
cd ..
echo [OK] Frontend packages installed successfully.

:: 7. Create .env if not exists
if not exist ".env" (
    echo [INFO] Copying .env.example to .env...
    copy .env.example .env >nul
    echo [OK] Created .env configuration file.
)

:: 8. Summary
echo.
echo =====================================================================
echo   SETUP COMPLETED SUCCESSFULLY!
echo =====================================================================
echo   To launch the entire platform:
echo     Run: start.bat
echo.
echo   Or run manually:
echo     Backend:  .venv\Scripts\python backend\app.py
echo     Frontend: cd frontend ^&^& npm run dev
echo.
echo   Open in your browser: http://localhost:3000
echo =====================================================================
exit /b 0

