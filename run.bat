@echo off
REM Double-click entrypoint for the project. This calls the PowerShell helper with the project folder as argument.
setlocal enabledelayedexpansion
SET "SCRIPT_DIR=%~dp0"
REM Remove trailing backslash
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Call PowerShell helper with execution policy bypass for this run only
powershell -NoProfile -ExecutionPolicy Bypass -Command "& '%SCRIPT_DIR%\run_helper.ps1' -ProjectDir '%SCRIPT_DIR%'"
if %errorlevel% neq 0 (
    echo Error: helper script failed with exit code %errorlevel%
    pause
)
