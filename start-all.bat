@echo off
setlocal EnableDelayedExpansion
title Standardify — Dev Launcher

:: ═══════════════════════════════════════════════════════════
::   STANDARDIFY — Local Development Launcher
::   Team Trailblazers · SIH26107
:: ═══════════════════════════════════════════════════════════
echo.
echo   ╔═══════════════════════════════════════════════╗
echo   ║       STANDARDIFY  —  Dev Environment         ║
echo   ║  Team Trailblazers · SIH26107                 ║
echo   ╠═══════════════════════════════════════════════╣
echo   ║  Backend   →  http://127.0.0.1:8000           ║
echo   ║  Frontend  →  http://localhost:5173            ║
echo   ║  API Docs  →  http://127.0.0.1:8000/docs      ║
echo   ╚═══════════════════════════════════════════════╝
echo.

:: ── Pre-flight: Python venv ──────────────────────────────────
if not exist "%~dp0backend\venv\Scripts\activate.bat" (
    echo   [ERROR] Python venv not found.
    echo   Run setup.bat first to create it.
    echo.
    pause
    exit /b 1
)

:: ── Pre-flight: Frontend node_modules ───────────────────────
if not exist "%~dp0frontend\node_modules" (
    echo   [ERROR] node_modules not found in frontend/.
    echo   Run setup.bat first to install dependencies.
    echo.
    pause
    exit /b 1
)

:: ── Pre-flight: backend .env ────────────────────────────────
if not exist "%~dp0backend\.env" (
    echo   [WARN]  backend/.env not found — copying from .env.example.
    copy /Y "%~dp0backend\.env.example" "%~dp0backend\.env" >nul
    echo   [WARN]  Add your GROQ_API_KEY and GEMINI_API_KEY to backend/.env before use.
    echo.
)

:: ── Pre-flight: frontend .env ───────────────────────────────
if not exist "%~dp0frontend\.env" (
    copy /Y "%~dp0frontend\.env.example" "%~dp0frontend\.env" >nul
)

echo   Starting services...
echo.

:: ── 1. Launch Backend ────────────────────────────────────────
start "Standardify — Backend [port 8000]" cmd /k ^
  "title Standardify Backend && cd /d ""%~dp0backend"" && call venv\Scripts\activate.bat && echo. && echo   Backend ready at http://127.0.0.1:8000 && echo   API docs at   http://127.0.0.1:8000/docs && echo. && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

:: ── 2. Wait for backend to become ready (health check loop) ─
echo   Waiting for backend to be ready...
set /a tries=0
:health_loop
timeout /t 2 /nobreak >nul
set /a tries+=1

:: Use PowerShell to probe the health endpoint silently
powershell -NoProfile -Command ^
  "try { $r=(Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/v1/health' -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop).StatusCode; if($r -eq 200){exit 0}else{exit 1} } catch { exit 1 }" >nul 2>&1

if %errorlevel%==0 goto backend_ready

if %tries% geq 20 (
    echo   [WARN]  Backend didn't respond after 40s — starting frontend anyway.
    echo   Check the backend window for errors.
    goto start_frontend
)
goto health_loop

:backend_ready
echo   [OK]    Backend is live at http://127.0.0.1:8000

:: ── 3. Launch Frontend ───────────────────────────────────────
:start_frontend
echo   Starting frontend dev server...
start "Standardify — Frontend [port 5173]" cmd /k ^
  "title Standardify Frontend && cd /d ""%~dp0frontend"" && echo. && npm run dev"

:: ── 4. Wait briefly for Vite to spin up, then open browser ──
timeout /t 4 /nobreak >nul
echo   Opening browser...
start "" "http://localhost:5173"

:: ── 5. Summary ───────────────────────────────────────────────
echo.
echo   ╔═══════════════════════════════════════════════╗
echo   ║  Both services are running in separate        ║
echo   ║  terminal windows.                            ║
echo   ║                                               ║
echo   ║  Frontend  →  http://localhost:5173           ║
echo   ║  Backend   →  http://127.0.0.1:8000           ║
echo   ║  API Docs  →  http://127.0.0.1:8000/docs      ║
echo   ║                                               ║
echo   ║  Close the terminal windows to stop.          ║
echo   ╚═══════════════════════════════════════════════╝
echo.
pause
