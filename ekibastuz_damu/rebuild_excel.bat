@echo off
cd /d "%~dp0"
set "PY="
py -3 --version >nul 2>nul && set "PY=py -3"
if not defined PY python --version >nul 2>nul && set "PY=python"
echo Rebuilding Excel from raw_2gis.json (no 2GIS access)...
%PY% scrape_2gis.py --excel-only
echo.
echo Done: ekibastuz_damu.xlsx and rubrics_report.csv
pause
