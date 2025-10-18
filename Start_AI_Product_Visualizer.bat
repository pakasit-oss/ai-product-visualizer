@echo off
chcp 65001 >nul
title AI Product Visualizer

:: Get the script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo.
echo ========================================
echo   AI Product Visualizer
echo ========================================
echo.
echo 🚀 Starting Streamlit app...
echo.
echo 💡 Tip: Leave this window open while using the app
echo    Press Ctrl+C to stop the server
echo.
echo ========================================
echo.

:: Wait 2 seconds then open browser
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8501"

:: Run Streamlit
streamlit run main.py

:: If streamlit exits, pause
pause
