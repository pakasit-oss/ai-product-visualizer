@echo off
chcp 65001 >nul
title Create Desktop Shortcut

echo.
echo ========================================
echo   สร้าง Desktop Shortcut
echo ========================================
echo.

:: Get the script directory
set "SCRIPT_DIR=%~dp0"

:: Get the Desktop path
set "DESKTOP=%USERPROFILE%\Desktop"

:: Full path to the batch file
set "TARGET=%SCRIPT_DIR%Start_AI_Product_Visualizer.bat"

:: Shortcut path
set "SHORTCUT=%DESKTOP%\AI Product Visualizer.lnk"

echo 🔨 กำลังสร้าง shortcut...
echo.
echo 📂 Target: %TARGET%
echo 🖥️  Desktop: %DESKTOP%
echo.

:: Create VBScript to create shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = "%SHORTCUT%" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%TARGET%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Description = "AI Product Visualizer - Image and Video Generation" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.IconLocation = "%%SystemRoot%%\System32\imageres.dll,1" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"

:: Run VBScript
cscript //nologo "%TEMP%\CreateShortcut.vbs"

:: Clean up
del "%TEMP%\CreateShortcut.vbs"

if exist "%SHORTCUT%" (
    echo.
    echo ========================================
    echo ✅ สร้าง Desktop Shortcut สำเร็จ!
    echo ========================================
    echo.
    echo 📁 ตำแหน่ง: %DESKTOP%
    echo 📝 ชื่อ: AI Product Visualizer.lnk
    echo.
    echo 💡 คุณสามารถ:
    echo    1. Double-click shortcut เพื่อเปิด app
    echo    2. ลาก shortcut ไปที่ Taskbar เพื่อ pin
    echo    3. คลิกขวา shortcut ^> Properties ^> Change Icon เพื่อเปลี่ยน icon
    echo.
    echo 🎉 เสร็จแล้ว!
    echo.
) else (
    echo.
    echo ========================================
    echo ❌ สร้าง shortcut ไม่สำเร็จ
    echo ========================================
    echo.
    echo 💡 ลองวิธีนี้แทน:
    echo    1. คลิกขวาที่ Start_AI_Product_Visualizer.bat
    echo    2. เลือก "Send to" ^> "Desktop (create shortcut)"
    echo.
)

pause
