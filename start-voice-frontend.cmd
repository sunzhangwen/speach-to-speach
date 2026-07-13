@echo off
setlocal
cd /d "%~dp0"

echo Starting speech-to-speech frontend...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-voice-frontend.ps1"
set "FRONTEND_EXIT_CODE=%ERRORLEVEL%"

echo.
echo Frontend exited with code %FRONTEND_EXIT_CODE%.
pause
exit /b %FRONTEND_EXIT_CODE%
