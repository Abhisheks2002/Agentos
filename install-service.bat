@echo off
REM AgentOS Windows Service Installer
REM Run as Administrator

echo ==========================================
echo   AgentOS Windows Service Installer
echo ==========================================
echo.

set SERVICE_NAME=AgentOS
set DISPLAY_NAME=AgentOS - AI Agent Governance
set DESCRIPTION=AI Agent Governance Platform
set EXE_PATH=%~dp0node.exe
set APP_PATH=%~dp0server.js

REM Check if Node.js is installed
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

REM Create logs directory
if not exist "%APPDATA%\AgentOS\logs" mkdir "%APPDATA%\AgentOS\logs"

REM Check if service exists
sc query %SERVICE_NAME% >nul 2>nul
if %errorlevel% equ 0 (
    echo Service already exists. Stopping and removing...
    net stop %SERVICE_NAME% 2>nul
    sc delete %SERVICE_NAME% 2>nul
)

echo Installing AgentOS as Windows Service...
echo.

REM Create the service
sc create %SERVICE_NAME% binPath= "\"%EXE_PATH%\" \"%APP_PATH%\"" DisplayName= "%DISPLAY_NAME%" start= auto
sc description %SERVICE_NAME% "%DESCRIPTION%"
sc config %SERVICE_NAME% obj= "NT AUTHORITY\LocalService"

REM Set recovery options
sc failure %SERVICE_NAME% reset= 86400 actions= restart/60000/restart/60000/restart/60000

echo.
echo ==========================================
echo   Installation Complete!
echo ==========================================
echo.
echo Service Name: %SERVICE_NAME%
echo Display Name: %DISPLAY_NAME%
echo.
echo To manage the service:
echo   Start:   net start %SERVICE_NAME%
echo   Stop:    net stop %SERVICE_NAME%
echo   Status:  sc query %SERVICE_NAME%
echo.
echo To uninstall:
echo   sc delete %SERVICE_NAME%
echo.
pause
