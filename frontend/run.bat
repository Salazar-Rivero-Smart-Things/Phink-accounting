@echo off
cd /d "%~dp0"
echo [Frontend] Starter Next.js Dashbord pa port 3000...
call npm.cmd run dev
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [Frontend Feil] Next.js stoppet med feilkode %ERRORLEVEL%.
    pause
)
