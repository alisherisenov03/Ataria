@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul || (echo Python не найден. Установите с python.org, отметив "Add Python to PATH", и запустите снова. & pause & exit /b 1)
echo Устанавливаю зависимости...
python -m pip install -q playwright openpyxl || (pause & exit /b 1)
python -m playwright install chromium || (pause & exit /b 1)
echo Запускаю сбор. Если в браузере появится капча - пройдите её. Окно не закрывайте.
python scrape_2gis.py
echo.
echo Готово. Файл ekibastuz_damu.xlsx лежит в этой папке.
pause
