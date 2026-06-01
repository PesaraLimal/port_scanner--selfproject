@echo off
title SecurePort Scanner Control Center
:menu
cls
echo ======================================================================
echo             ⚡ SECUREPORT SCANNER - CONTROL CENTER ⚡
echo ======================================================================
echo.
echo Please select how you want to run the port scanner:
echo.
echo  [1] Run Desktop GUI App (No dependencies required)
echo  [2] Run Web Dashboard Server (Flask + Browser UI)
echo  [3] Install/Update Web App Dependencies (Flask, Flask-CORS)
echo  [4] Exit
echo.
echo ======================================================================
set /p choice="Enter choice (1-4): "

if "%choice%"=="1" goto run_gui
if "%choice%"=="2" goto run_web
if "%choice%"=="3" goto install_deps
if "%choice%"=="4" goto exit_app
echo [!] Invalid selection. Press any key to try again...
pause >nul
goto menu

:run_gui
echo.
echo [+] Launching Desktop GUI application...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo [!] Error launching the GUI application. Ensure Python is installed.
    pause
)
goto menu

:run_web
echo.
echo [+] Launching Web Dashboard Server...
echo [+] Checking if Flask is installed...
python -c "import flask, flask_cors" 2>nul
if %errorlevel% neq 0 (
    echo [!] Flask or Flask-CORS is not installed.
    echo [+] Installing required packages first...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [!] Failed to install dependencies automatically.
        echo [!] Please run Option [3] manually or check internet connection.
        pause
        goto menu
    )
)
echo [+] Starting Flask API + Web Server...
echo [+] Opening http://127.0.0.1:5000/ in browser...
start http://127.0.0.1:5000/
python api/index.py
if %errorlevel% neq 0 (
    echo.
    echo [!] Flask server stopped or crashed.
    pause
)
goto menu

:install_deps
echo.
echo [+] Installing requirements from requirements.txt...
pip install -r requirements.txt
if %errorlevel% eq 0 (
    echo [+] Dependencies installed successfully!
) else (
    echo [!] Error installing dependencies. Make sure Python and pip are in your PATH.
)
pause
goto menu

:exit_app
echo Goodbye!
timeout /t 2 >nul
exit
