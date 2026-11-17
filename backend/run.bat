@echo off
cd /d "%~dp0"
echo [Backend] Starter Phink FastAPI pa port 8000...
venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [Backend Feil] Uvicorn stoppet med feilkode %ERRORLEVEL%.
    pause
)
