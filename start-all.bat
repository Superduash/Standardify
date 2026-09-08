@echo off
echo ================================================
echo  Standardify — Starting Application
echo ================================================
echo.
echo  Backend  → http://localhost:8000
echo  Frontend → http://localhost:5173
echo.
echo  Press Ctrl+C in each window to stop.
echo ================================================
echo.

:: Start backend in a new window
start "Standardify Backend" cmd /k "cd /d "%~dp0backend" && call venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

:: Small delay so backend starts first
timeout /t 2 /nobreak >nul

:: Start frontend in a new window
start "Standardify Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"
