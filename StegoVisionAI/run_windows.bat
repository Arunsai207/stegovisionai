@echo off
setlocal
cd /d "%~dp0"
if not exist .venv (
  py -3.12 -m venv .venv
  if errorlevel 1 py -3 -m venv .venv
)
call .venv\Scripts\activate.bat
if errorlevel 1 (
  echo Could not activate .venv. Ensure Python 3.12 or newer is installed.
  pause
  exit /b 1
)
python -m pip install --upgrade pip
if errorlevel 1 goto install_error
python -m pip install -r requirements.txt
if errorlevel 1 goto install_error
set PORT=8000
netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul
if not errorlevel 1 (
  echo Port 8000 is already in use. Starting StegoVisionAI on port 8001 instead.
  set PORT=8001
)
echo.
echo Starting StegoVisionAI at http://127.0.0.1:%PORT%
echo Keep this window open while using the application.
echo Press Ctrl+C to stop the server.
python -m uvicorn app.main:app --host 127.0.0.1 --port %PORT%
exit /b %errorlevel%
:install_error
echo.
echo Dependency installation failed. Copy the error above and share it for troubleshooting.
pause
exit /b 1
