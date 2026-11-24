# GuardPay PowerShell Startup Script
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Starting GuardPay Stack (Backend, Merchant, MCP, Frontend)" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$root = $PSScriptRoot

# 1. Start Backend
Write-Host "`n[1/4] Starting GuardPay Backend on port 8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; python seed.py; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

Start-Sleep -Seconds 2

# 2. Start Mock Merchant
Write-Host "[2/4] Starting Mock Merchant on port 8001..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\mock_merchant'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload"

Start-Sleep -Seconds 2

# 3. Start MCP Server Bridge
Write-Host "[3/4] Starting MCP Server Bridge on port 8002..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\mcp_server'; python server.py --http"

Start-Sleep -Seconds 2

# 4. Start Frontend
Write-Host "[4/4] Starting Operator Console on port 3000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host "GuardPay stack launched successfully!" -ForegroundColor Green
Write-Host "Operator Console: http://localhost:3000" -ForegroundColor White
Write-Host "Backend API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "Mock Merchant:    http://localhost:8001/catalog" -ForegroundColor White
Write-Host "MCP Server Tools: http://localhost:8002/docs" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Green
