@echo off
chcp 65001 >nul
echo ====================================================
echo       ЗАГРУЗКА ДАННЫХ ИЗ СТАРОГО ПАРСЕРА
echo ====================================================
echo.

cd /d "%~dp0"

REM Определяем команду Python
call get_python.bat
echo 🐍 Используется Python: %PYTHON_CMD%
echo.

REM Настройки сервера (загружаем на веб-сервер 5000)
set server_url=http://127.0.0.1:5000
set server_name=Веб-сервер
echo 🎯 Целевой сервер: %server_name% (%server_url%)
echo 💡 Примечание: Данные будут обработаны и сохранены в базу
echo.

echo 🔍 Проверка файла данных...

REM Проверяем наличие файла данных
set data_file=..\app\utils\old_dns_parser\product_data.json
if not exist "%data_file%" (
    echo ❌ Файл product_data.json не найден в old_dns_parser!
    echo 💡 Сначала запустите парсинг через parse_category.bat
    pause
    exit /b 1
)

echo ✅ Файл найден: %data_file%
echo.

echo 📋 Параметры загрузки:
echo    Файл: %data_file%
echo    Сервер: %server_name%
echo    URL: %server_url%
echo.

set /p confirm="Начать загрузку? (y/n): "
if /i not "%confirm%"=="y" (
    echo Операция отменена
    pause
    exit /b 0
)

echo.
echo 🚀 Загрузка данных на сервер...
echo.

REM Загружаем данные на веб-сервер (5000) который имеет API
"%PYTHON_CMD%" upload_single_file.py --server-url %server_url% --data-file "%data_file%"

if %errorlevel% neq 0 (
    echo.
    echo ❌ Ошибка при загрузке данных!
    echo 💡 Проверьте что сервер запущен
    echo 💡 Команда: docker-compose up -d
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Данные успешно загружены!
echo.
echo 💡 Проверить результат можно:
echo    • Веб-интерфейс парсера: http://127.0.0.1:5001
echo    • Веб-интерфейс Docker: %server_url%
echo    • Статус API: %server_url%/api/parser-status
echo.
echo 📝 Для смены на хостинг отредактируйте строку:
echo    set server_url=%server_url%
echo.
pause 