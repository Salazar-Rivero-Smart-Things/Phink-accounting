$root = $PSScriptRoot
Write-Host "Starter Phinx Accounting..." -ForegroundColor Cyan

# Start Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; .\venv\Scripts\python -m uvicorn app.main:app --reload --port 8000"

# Start Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm.cmd run dev"

Start-Sleep -Seconds 3
Start-Process "http://localhost:3000"

Write-Host "Phinx Accounting er startet på http://localhost:3000 !" -ForegroundColor Green
