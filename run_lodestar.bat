@echo off
setlocal

title Lodestar OSINT Assistant

cd /d "%~dp0"

echo =========================================
echo       Lodestar OSINT Assistant
echo =========================================
echo.

:: Check for the virtual environment
if not exist ".venv\Scripts\python.exe" (
    echo [!] Virtual environment not found.
    echo Creating .venv...
    python -m venv .venv
    
    echo Installing requirements...
    .venv\Scripts\python.exe -m pip install --upgrade pip
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    
    echo Setup complete.
    echo.
)

:: Start the application
echo [i] Starting FastAPI server on 127.0.0.1:8420...
echo [i] Keep this window open. Close it to stop Lodestar.
echo.

:: Launch the browser (give the server a moment to start)
start "" "http://127.0.0.1:8420"

:: Run the server
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8420

endlocal
pause
