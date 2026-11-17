@echo off
title Starter Phinx Accounting...
echo Starter Phinx Accounting System...
echo [1/2] Starter Python FastAPI Backend (Port 8000)...
start "Phinx Backend" cmd /k "cd backend && .\venv\Scripts\python -m uvicorn app.main:app --reload --port 8000"

echo [2/2] Starter Next.js Frontend (Port 3000)...
start "Phinx Frontend" cmd /k "cd frontend && npm.cmd run dev"

echo.
echo ========================================================
echo Phinx Accounting kjorer na!
echo Frontend: http://localhost:3000
echo Backend API Docs: http://localhost:8000/docs
echo ========================================================
pause
