@echo off
setlocal EnableExtensions

cd /d "%~dp0"

set "MAIN_PATH="
for /d %%D in ("%~dp0*pyqt") do (
    if exist "%%~fD\ECGMonitor\main.py" (
        set "MAIN_PATH=%%~fD\ECGMonitor\main.py"
        goto :found_main
    )
)

:found_main
if not defined MAIN_PATH (
    echo ECGMonitor demo entry was not found. Expected: *pyqt\ECGMonitor\main.py
    pause
    exit /b 1
)

python "%MAIN_PATH%" --demo
if errorlevel 1 (
    echo.
    echo Demo failed to start. Please check Python and project dependencies.
    pause
    exit /b 1
)
