@echo off
cd /d "%~dp0"
set "PY="
py -3 --version >nul 2>nul && set "PY=py -3"
if not defined PY python --version >nul 2>nul && set "PY=python"
if not defined PY (
  echo Python not found. Install it from https://www.python.org/downloads/ - tick "Add Python to PATH" - then run this file again.
  pause
  exit /b 1
)
echo Python: %PY%
echo Checking libraries...
%PY% -m pip install -q playwright openpyxl
if errorlevel 1 (
  echo ERROR: pip install failed
  pause
  exit /b 1
)
echo Starting. A Microsoft Edge window will open with 2GIS. If a captcha appears - solve it. Do not close this window.
echo If it stops (reboot, error) - just run this file again: it continues where it stopped.
%PY% scrape_2gis.py
echo.
echo Done. Opening ekibastuz_damu.xlsx
if exist ekibastuz_damu.xlsx start "" "ekibastuz_damu.xlsx"
pause
