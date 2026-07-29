@echo off
REM ============================================================
REM  ShopSphere -- one-click demo launcher (Windows)
REM  Double-click this file to start the store for a demo.
REM  Requires: internet (for the Groq AI) and GROQ_API_KEY in .env.
REM ============================================================

cd /d "%~dp0"

echo.
echo === ShopSphere: starting up ===
echo.

REM --- 1. Backend API in its own window ---
echo [1/2] Starting the backend API (takes ~15-20s to warm up)...
start "ShopSphere - Backend" cmd /k "venv\Scripts\python.exe -m uvicorn app.main:app"

REM      Give the backend time to load before the storefront/browser.
timeout /t 8 /nobreak >nul

REM --- 2. React storefront (Vite) in its own window ---
echo [2/2] Starting the storefront...
start "ShopSphere - Storefront" cmd /k "cd storefront && npm run dev"

REM      Let Vite boot, then open the browser.
timeout /t 6 /nobreak >nul
start "" http://localhost:5173

echo.
echo === Done. Two windows opened: Backend and Storefront. ===
echo The store is at http://localhost:5173
echo (If the page can't reach the backend yet, wait a few seconds and refresh.)
echo.
echo To stop everything, double-click stop_demo.bat (or close both windows).
echo.
pause
