@echo off
setlocal

echo ================================================
echo  Standardify — Setup
echo ================================================
echo.

:: ── 1. Backend Python venv ──────────────────────
echo [1/4] Creating Python virtual environment...
cd /d "%~dp0backend"

if not exist venv (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create venv. Is Python 3.10+ installed?
        pause
        exit /b 1
    )
) else (
    echo       venv already exists — skipping.
)

:: ── 2. Install Python deps ──────────────────────
echo.
echo [2/4] Installing Python dependencies (this may take a few minutes)...
call venv\Scripts\activate.bat
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo ERROR: pip install failed. Check requirements.txt and your internet connection.
    pause
    exit /b 1
)
echo       Python dependencies installed.

:: ── 3. Ingest seed standards ─────────────────────
echo.
echo [3/4] Ingesting seed standards into ChromaDB...
echo       NOTE: First run downloads the BGE-M3 embedding model (~1.1 GB).
echo       Subsequent runs are instant.
python ingest.py
if errorlevel 1 (
    echo ERROR: Ingestion failed. See error above.
    pause
    exit /b 1
)
echo       Ingestion complete.

:: ── 4. Frontend npm install ──────────────────────
echo.
echo [4/4] Installing frontend dependencies...
cd /d "%~dp0frontend"
npm install --silent
if errorlevel 1 (
    echo ERROR: npm install failed. Is Node.js 18+ installed?
    pause
    exit /b 1
)
echo       Frontend dependencies installed.

echo.
echo ================================================
echo  Setup complete!
echo  Run start-all.bat to launch the application.
echo ================================================
pause
