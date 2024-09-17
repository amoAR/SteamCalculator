@echo off & setlocal EnableExtensions DisableDelayedExpansion
title SteamCalculator
pushd "%~dp0"
node -v >nul
if errorlevel 1 (
    echo:
    echo NodeJS isn't installed. Please install NodeJS first.
    start https://nodejs.org/en
    goto err
)
for /f "delims=" %%a in ('npm -v 2^>nul') do @set "npmV=%%a"
if not defined npmV (
    echo:
    echo NPM isn't installed. Let's install NPM first.
    rem start https://docs.npmjs.com/downloading-and-installing-node-js-and-npm
    echo:
    call npm install
)
python --version
if errorlevel 1 (
    echo:
    echo Python isn't installed. Please install Python first.
    goto err
)
pip install -r requirements.txt
if errorlevel 1 (
    echo:
    echo Failed to install the required packages. Check the errors above.
    goto err
)
cls
echo 1.1 >ver
attrib ver +h
call run.bat
:err
pause
exit