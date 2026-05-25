@echo off
echo ========================================
echo   AgentOS Starting...
echo ========================================
cd /d "%~dp0"

:: Kill any existing node process on port 3000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a 2>nul
)

start /b node server.js
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   AgentOS Ready!
echo   Opening browser...
echo ========================================
start http://localhost:3000