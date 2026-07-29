@echo off
REM ============================================================
REM  ShopSphere -- stop the demo servers (Windows)
REM  Double-click to shut down the backend and storefront.
REM ============================================================

echo Stopping the backend and storefront...

REM Backend (uvicorn) runs as python.exe; the Vite storefront runs as node.exe.
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1

echo Done. (Ollama, if running, is left alone -- it uses little memory idle.)
echo.
pause
