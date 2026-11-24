@echo off
echo ========================================================
echo Starting GuardPay Stack (Backend, Merchant, MCP, Frontend)
echo ========================================================

echo 1. Seeding default mandate...
start "GuardPay Backend [Port 8000]" cmd /k "cd backend && python seed.py && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 2 /nobreak > nul

echo 2. Starting Mock Merchant...
start "GuardPay Mock Merchant [Port 8001]" cmd /k "cd mock_merchant && uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload"

timeout /t 2 /nobreak > nul

echo 3. Starting MCP Server Bridge...
start "GuardPay MCP Gateway [Port 8002]" cmd /k "cd mcp_server && python server.py --http"

timeout /t 2 /nobreak > nul

echo 4. Starting Frontend Console...
start "GuardPay Operator Console [Port 3000]" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================================
echo GuardPay stack launched!
echo Operator Console: http://localhost:3000
echo Backend API Docs: http://localhost:8000/docs
echo Mock Merchant:    http://localhost:8001/catalog
echo MCP Server Tools: http://localhost:8002/docs
echo ========================================================
pause
