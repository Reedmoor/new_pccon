@echo off
chcp 65001 >nul
title Система управления парсера ПК

REM Определяем команду Python
call get_python.bat

REM Настройки сервера по умолчанию
set DEFAULT_SERVER=pcconf.ru
set DEFAULT_PORT=80
set CURRENT_SERVER=%DEFAULT_SERVER%

:menu
cls
echo ====================================================
echo         СИСТЕМА УПРАВЛЕНИЯ ПАРСЕРА ПК
echo ====================================================
echo.
echo 🐍 Python: %PYTHON_CMD%
echo 🌐 Сервер: %CURRENT_SERVER%
echo.
echo 🔧 Основные операции:
echo.
echo   1. 🚀 Парсинг и загрузка данных
echo   2. 📤 Загрузка данных на сервер
echo   3. 🔍 Тест соединения с сервером
echo   4. ⚙️  Изменить адрес сервера
echo   5. 🧹 Очистка логов
echo.
echo   0. ❌ Выход
echo.
echo ====================================================

set /p choice="Выберите операцию (0-5): "

if "%choice%"=="1" goto parse_and_upload
if "%choice%"=="2" goto upload_only
if "%choice%"=="3" goto test_connection
if "%choice%"=="4" goto change_server
if "%choice%"=="5" goto clean_logs
if "%choice%"=="0" goto exit

echo.
echo ❌ Неверный выбор! Нажмите любую клавишу...
pause >nul
goto menu

:parse_and_upload
cls
echo 🚀 Запуск парсинга и загрузки данных...
echo.
echo Сервер: %CURRENT_SERVER%
echo.
"%PYTHON_CMD%" parse_category.py
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Парсинг завершен, загружаем данные...
    "%PYTHON_CMD%" upload_to_pcconf.py --url "http://%CURRENT_SERVER%"
) else (
    echo ❌ Ошибка при парсинге!
)
echo.
pause
goto menu

:upload_only
cls
echo 📤 Загрузка данных на сервер...
echo.
echo Сервер: %CURRENT_SERVER%
echo.
"%PYTHON_CMD%" upload_to_pcconf.py --url "http://%CURRENT_SERVER%"
echo.
pause
goto menu

:test_connection
cls
echo 🔍 Тестирование соединения с сервером...
echo.
echo Сервер: %CURRENT_SERVER%
echo.
"%PYTHON_CMD%" -c "from ssl_config import create_configured_session; session, config = create_configured_session(); response = session.get('http://%CURRENT_SERVER%/', timeout=10); print(f'✅ Соединение успешно: {response.status_code}' if response.status_code == 200 else f'❌ Ошибка: {response.status_code}')"
echo.
pause
goto menu

:change_server
cls
echo ⚙️ Изменение адреса сервера
echo.
echo Текущий сервер: %CURRENT_SERVER%
echo.
echo Примеры:
echo   - pcconf.ru (по умолчанию)
echo   - k4db-jl2g-6d7c.gw-1a.dockhost.net (прямой nginx endpoint)
echo   - localhost:5000 (локальный сервер)
echo   - 192.168.1.100 (ваш IP)
echo   - your-domain.com
echo.
echo 💡 Если pcconf.ru не работает, попробуйте nginx endpoint
echo.
set /p new_server="Введите новый адрес сервера (или Enter для отмены): "

if "%new_server%"=="" (
    echo Отменено.
    pause
    goto menu
)

set CURRENT_SERVER=%new_server%
echo.
echo ✅ Сервер изменен на: %CURRENT_SERVER%
echo.
pause
goto menu

:clean_logs
cls
echo 🧹 Очистка файлов логов...
echo.
if exist "upload_to_pcconf.log" (
    del "upload_to_pcconf.log"
    echo ✅ upload_to_pcconf.log удален
)
if exist "parse_category.log" (
    del "parse_category.log" 
    echo ✅ parse_category.log удален
)
if exist "*.log" (
    del "*.log"
    echo ✅ Все остальные .log файлы удалены
)
echo.
echo ✅ Очистка завершена
pause
goto menu

:exit
echo.
echo 👋 До свидания!
echo.
exit /b 0 