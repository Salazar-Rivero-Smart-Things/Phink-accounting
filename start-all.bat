@echo off
setlocal
cd /d "%~dp0"

title Starter Phink Accounting...
echo ========================================================
echo       Starter Phink Accounting System (Enterprise)
echo ========================================================
echo.

echo [1/3] Starter Python FastAPI Backend pa port 8000...
start "Phink - Backend API (Port 8000)" cmd /k "call "%~dp0backend\run.bat""

echo [2/3] Starter Next.js Frontend pa port 3000...
start "Phink - Frontend Dashbord (Port 3000)" cmd /k "call "%~dp0frontend\run.bat""

echo.
echo Venter 3 sekunder sa serverne rekker a starte...
ping 127.0.0.1 -n 4 >nul

echo [3/3] Apner nettleseren pa http://localhost:3000 ...
start http://localhost:3000

echo.
echo ========================================================
echo Alt kjorer na!
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo Kundeservice: Klikk pa "Kundeservice Desk" i menyen!
echo ========================================================
echo.
echo (Ikke lukk de to sorte vinduene som apnet seg, de holder serverne i gang).
pause
