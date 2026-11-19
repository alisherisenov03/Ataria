@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PY="
py -3 --version >nul 2>nul && set "PY=py -3"
if not defined PY python --version >nul 2>nul && set "PY=python"
if not defined PY (
  echo Python не установлен. Ставлю Python 3.12 через winget...
  winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
  echo.
  echo Python установлен. ЗАКРОЙТЕ это окно и снова запустите run_windows.bat
  echo Если winget не сработал - скачайте Python с https://www.python.org/downloads/ ^(галочка "Add Python to PATH"^)
  pause
  exit /b 1
)
echo Python: %PY%
echo Устанавливаю зависимости...
%PY% -m pip install playwright openpyxl || (echo ОШИБКА pip & pause & exit /b 1)
echo Запускаю сбор. Если в браузере появится капча - пройдите её. Окно не закрывайте.
%PY% scrape_2gis.py
echo.
echo Готово. Файл ekibastuz_damu.xlsx лежит в этой папке.
pause
