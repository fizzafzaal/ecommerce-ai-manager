@echo off
REM ============================================================
REM  E-Commerce AI Manager -- stop the demo servers (Windows)
REM  Double-click to shut down the backend and UI cleanly.
REM ============================================================

echo Stopping the backend API and chat UI...

REM The backend (uvicorn) and UI (streamlit) both run as python.exe.
REM This stops them. It does NOT stop Ollama, which can keep running.
taskkill /F /IM python.exe >nul 2>&1

if errorlevel 1 (
    echo Nothing was running.
) else (
    echo Servers stopped.
)

echo.
echo Note: Ollama is left running (it uses little memory when idle).
echo.
pause
