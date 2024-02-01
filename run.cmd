@echo off
:main
cls
python -u %~dp0app.py
runas /u: "" >nul | set /p = "Press ENTER to continue... "
goto main
rem exit /b 0