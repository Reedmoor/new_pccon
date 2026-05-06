@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM Автоматическая загрузка данных Citilink на эндпоинт /api/upload-products
REM Аналог upload_from_old_parser_auto.bat, но для всех категорий Citi_parser

cd /d "%~dp0"
call get_python.bat

for /f %%i in ('where "%PYTHON_CMD%" 2^>nul') do set FULL_PYTHON_PATH=%%i
if "%FULL_PYTHON_PATH%"=="" set FULL_PYTHON_PATH=%PYTHON_CMD%

set server_url=http://127.0.0.1:5000
set citi_data_dir=..\app\utils\Citi_parser\data

echo ====================================================
echo      ЗАГРУЗКА ДАННЫХ CITILINK НА СЕРВЕР
echo ====================================================
echo 🎯 Сервер: %server_url%
echo 📁 Источник: %citi_data_dir%
echo.

if not exist "%citi_data_dir%" (
    echo ❌ Папка данных Citilink не найдена: %citi_data_dir%
    echo 💡 Сначала запустите парсинг: parse_citilink.bat
    pause
    exit /b 1
)

REM Перебираем все категории в папке data
set uploaded=0
set failed=0

for /d %%D in ("%citi_data_dir%\*") do (
    set data_file=%%D\Товары.json
    if exist "%%D\Товары.json" (
        echo.
        echo 📂 Категория: %%~nxD
        echo 📄 Файл: %%D\Товары.json

        "%FULL_PYTHON_PATH%" upload_single_file.py ^
            --server-url %server_url% ^
            --data-file "%%D\Товары.json" ^
            --source citilink

        if !errorlevel! equ 0 (
            echo ✅ Загружено: %%~nxD
            set /a uploaded+=1
        ) else (
            echo ❌ Ошибка загрузки: %%~nxD
            set /a failed+=1
        )
    )
)

echo.
echo ====================================================
echo 📊 Итог: загружено %uploaded% категорий, ошибок: %failed%
echo ====================================================
echo.

if %uploaded% gtr 0 (
    echo ✅ Данные Citilink успешно загружены на сервер!
    echo 💡 Проверить: %server_url%/admin/import
) else (
    echo ⚠️  Ни одна категория не была загружена.
    echo 💡 Убедитесь, что:
    echo    - Сервер запущен на %server_url%
    echo    - Данные спаршены в %citi_data_dir%
)

pause
exit /b 0
