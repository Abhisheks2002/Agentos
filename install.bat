@echo off
setlocal enabledelayedexpansion

echo ================================================
echo   AgentOS - Installation Script
echo   AI Agent Governance Platform
echo ================================================
echo.

:: Check for Node.js
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not installed.
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo [1/5] Installing Node.js dependencies...
npm install
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo     Done.

:: Check for Python (optional)
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [2/5] Checking Python modules...
    python -c "import sqlite3" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo     Installing sqlite3 support...
    )
)

echo [3/5] Creating workspace directory...
set WORKSPACE=%USERPROFILE%\AgentOS_Workspace
if not exist "%WORKSPACE%" mkdir "%WORKSPACE%"
echo     Workspace: %WORKSPACE%

echo [4/5] Creating startup configuration...
:: Create Windows startup entry
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v AgentOS >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v AgentOS /t REG_SZ /d "\"%CD%\agentos.bat\" --startup" /f
    echo     Added to Windows startup
) else (
    echo     Already in startup
)

echo [5/5] Creating service script...
echo @echo off > agentos.bat
echo cd /d "%%~dp0" >> agentos.bat
echo start /b node server.js >> agentos.bat
echo start /b "" index.html >> agentos.bat

echo.
echo ================================================
echo   Installation Complete!
echo ================================================
echo.
echo To start AgentOS:
echo   Run: node server.js
echo   Or:  Double-click index.html
echo.
echo To start with Electron:
echo   Run: npm start
echo.
echo Workspace directory: %WORKSPACE%
echo.
pause
