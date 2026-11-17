@echo off
setlocal
cd /d "%~dp0"
if not exist "..\Frontend\welcome.html" (
  echo Extract welcome.html into main\Frontend first.
  pause
  exit /b 1
)
if not exist "..\..\.venv\Scripts\python.exe" (
  py -3 -m venv "..\..\.venv"
  if errorlevel 1 goto failed
)
"..\..\.venv\Scripts\python.exe" -c "import fastapi, uvicorn; from backend.main import app" >nul 2>&1
if errorlevel 1 (
  "..\..\.venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto failed
)
echo Open http://127.0.0.1:8010/ in your browser.
"..\..\.venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8010
if errorlevel 1 goto failed
exit /b 0
:failed
echo Startup failed. Check the error above. Python 3.11+ is required.
pause
exit /b 1

