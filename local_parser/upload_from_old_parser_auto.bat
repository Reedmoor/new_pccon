@echo off
chcp 65001 >nul

REM Автоматическая загрузка данных из старого парсера (без интерактивных запросов)

cd /d "%~dp0"

REM Определяем команду Python
call get_python.bat

REM Настройки сервера (веб-сервер работает на 5000)
set server_url=http://127.0.0.1:5000
set data_file=..\app\utils\old_dns_parser\product_data.json

echo ====================================================
echo      АВТОМАТИЧЕСКАЯ ЗАГРУЗКА ДАННЫХ
echo ====================================================
echo 🎯 Целевой сервер: %server_url%
echo 📁 Файл данных: %data_file%
echo.

if not exist "%data_file%" (
    echo ❌ Файл product_data.json не найден!
    exit /b 1
)

echo 🚀 Запуск загрузки...

REM Загружаем данные на веб-сервер (5000) который имеет API
"%PYTHON_CMD%" upload_single_file.py --server-url %server_url% --data-file "%data_file%"

if %errorlevel% neq 0 (
    echo ❌ Ошибка загрузки!
    exit /b 1
)

echo ✅ Загрузка завершена!
echo 💡 Проверить: %server_url%
exit /b 0 