@echo off
REM ============================================================
REM  E-Commerce AI Manager -- one-click demo launcher (Windows)
REM  Double-click this file to start everything for a demo.
REM ============================================================

cd /d "%~dp0"

echo.
echo === E-Commerce AI Manager: starting up ===
echo.

REM --- 1. Make sure Ollama is running (it usually auto-starts) ---
echo [1/4] Checking Ollama...
tasklist /FI "IMAGENAME eq ollama.exe" | find /I "ollama.exe" >nul
if errorlevel 1 (
    echo       Ollama not running -- starting it...
    start "" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
    timeout /t 5 /nobreak >nul
) else (
    echo       Ollama is already running.
)

REM --- 2. Pre-warm the model so the first reply is fast ---
echo [2/4] Warming up the language model (this can take ~30s the first time)...
call venv\Scripts\python.exe -m app.warmup

REM --- 3. Start the backend API in its own window ---
echo [3/4] Starting the backend API...
start "AI Manager - Backend" cmd /k "venv\Scripts\python.exe -m uvicorn app.main:app"

REM       Give the backend a few seconds to come up before the UI.
timeout /t 6 /nobreak >nul

REM --- 4. Start the Streamlit UI in its own window (opens the browser) ---
echo [4/4] Starting the chat UI (your browser will open)...
start "AI Manager - UI" cmd /k "venv\Scripts\python.exe -m streamlit run frontend/chat_app.py"

echo.
echo === Done. Two windows opened: Backend and UI. ===
echo The app will open in your browser at http://localhost:8501
echo.
echo To stop everything, double-click stop_demo.bat (or close both windows).
echo.
pause
