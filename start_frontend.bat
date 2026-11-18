@echo off
title React Frontend Dashboard - Customer Analytics
cd /d "%~dp0frontend"
echo ===================================================
echo Starting React Frontend Dashboard (http://localhost:3000)...
echo ===================================================
call npm run dev
pause

