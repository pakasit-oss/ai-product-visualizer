@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   GitHub Push Script
echo ========================================
echo.

REM ตรวจสอบว่ามี git หรือไม่
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git not installed. Please install Git first.
    pause
    exit /b 1
)

echo ⚠️  Before running this script:
echo    1. Create GitHub repository at https://github.com/new
echo    2. Copy the repository URL
echo.
set /p REPO_URL="📋 Paste your GitHub repository URL (e.g., https://github.com/username/repo.git): "

if "%REPO_URL%"=="" (
    echo ❌ Repository URL cannot be empty
    pause
    exit /b 1
)

echo.
echo 🔗 Adding remote origin: %REPO_URL%
git remote remove origin 2>nul
git remote add origin %REPO_URL%

echo.
echo 📤 Pushing to GitHub...
git push -u origin main

if errorlevel 1 (
    echo.
    echo ❌ Push failed. Common issues:
    echo    - Incorrect repository URL
    echo    - Authentication required (use GitHub personal access token)
    echo    - Repository already has content
    echo.
    echo 💡 Try this:
    echo    1. Go to https://github.com/settings/tokens
    echo    2. Generate new personal access token (classic)
    echo    3. Select 'repo' scope
    echo    4. Copy the token
    echo    5. When git asks for password, paste the token
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ Successfully pushed to GitHub!
echo ========================================
echo.
echo 🎉 Next steps:
echo    1. Go to https://share.streamlit.io
echo    2. Click "New app"
echo    3. Select your repository
echo    4. Set main file to: main.py
echo    5. Add API keys in Secrets
echo    6. Deploy!
echo.
pause
