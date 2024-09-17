@echo off
title SteamCalculator
chcp 65001 >nul
pushd "%~dp0"
if not exist ver call setup.bat
set /p ver=<ver
:main
cls
echo Installed ver: v%ver%
echo:
python -u "%~dp0app.py"
runas /u: "" >nul | set /p = "Press ENTER to continue... "
goto main
rem exit /b 0