@echo off
setlocal
cd /d "%~dp0"

:menu
cls
echo ========================================
echo       Speech-to-Speech Backend
echo ========================================
echo.
echo   1. CPU Fast
echo   2. CPU Quality
echo   3. GPU
echo.
set "BACKEND_MODE="
set /p "BACKEND_MODE=Select a mode [1-3]: "

if "%BACKEND_MODE%"=="1" goto fast
if "%BACKEND_MODE%"=="2" goto quality
if "%BACKEND_MODE%"=="3" goto gpu

echo.
echo Invalid selection. Please enter 1, 2, or 3.
pause >nul
goto menu

:fast
echo.
echo Starting backend in CPU fast mode...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-voice-backend.ps1" -Device cpu -CpuProfile fast
set "BACKEND_EXIT_CODE=%ERRORLEVEL%"
goto finished

:quality
echo.
echo Starting backend in CPU quality mode...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-voice-backend.ps1" -Device cpu -CpuProfile quality
set "BACKEND_EXIT_CODE=%ERRORLEVEL%"
goto finished

:gpu
echo.
echo Starting backend in GPU mode...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-voice-backend.ps1" -Device gpu -CpuProfile quality
set "BACKEND_EXIT_CODE=%ERRORLEVEL%"

:finished
echo.
echo Backend exited with code %BACKEND_EXIT_CODE%.
pause
exit /b %BACKEND_EXIT_CODE%
