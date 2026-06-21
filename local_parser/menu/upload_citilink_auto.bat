@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

call "%~dp0_paths.bat"

set server_url=%SERVER_URL%
set citi_data_dir=%LP_ROOT%\..\app\utils\Citi_parser\data
set citilink_flat=%citi_data_dir%\citilink

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

set uploaded=0
set failed=0

REM 1) Новый формат: data/citilink/citilink_YYYYMMDD_HHMMSS.json
if exist "%citilink_flat%\citilink_*.json" (
    echo 📦 Загрузка дампов citilink_*.json ...
    for /f "delims=" %%F in ('dir /b /o-d "%citilink_flat%\citilink_*.json" 2^>nul') do (
        echo.
        echo 📄 Файл: %%F
        "%PYTHON_CMD%" "%LP_ROOT%\upload_single_file.py" ^
            --server-url %server_url% ^
            --data-file "%citilink_flat%\%%F" ^
            --source citilink
        if !errorlevel! equ 0 (
            echo ✅ Загружено: %%F
            set /a uploaded+=1
        ) else (
            echo ❌ Ошибка: %%F
            set /a failed+=1
        )
    )
)

REM 2) Старый формат: data/{категория}/Товары.json
for /d %%D in ("%citi_data_dir%\*") do (
    if /i not "%%~nxD"=="citilink" (
        if exist "%%D\Товары.json" (
            echo.
            echo 📂 Категория: %%~nxD
            "%PYTHON_CMD%" "%LP_ROOT%\upload_single_file.py" ^
                --server-url %server_url% ^
                --data-file "%%D\Товары.json" ^
                --source citilink
            if !errorlevel! equ 0 (
                echo ✅ Загружено: %%~nxD
                set /a uploaded+=1
            ) else (
                echo ❌ Ошибка: %%~nxD
                set /a failed+=1
            )
        )
    )
)

echo.
echo ====================================================
echo 📊 Итог: загружено %uploaded% файлов, ошибок: %failed%
echo ====================================================

if %uploaded% gtr 0 (
    echo ✅ Данные Citilink загружены и импортированы в БД на %server_url%
) else (
    echo ⚠️  Файлы для загрузки не найдены в %citi_data_dir%
    echo 💡 Ожидается: data\citilink\citilink_*.json
)

if "%~1"=="--no-pause" exit /b 0
pause
exit /b 0
