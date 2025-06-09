@echo off
setlocal EnableDelayedExpansion

echo ====================================================
echo    ЛОКАЛЬНЫЙ ПАРСИНГ + ОТПРАВКА НА DOCKER СЕРВЕР
echo ====================================================
echo.

:: Переходим в папку парсера
cd /d "%~dp0"

:: Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python и добавьте его в PATH
    echo.
    pause
    exit /b 1
)

echo 🐍 Python найден
echo.

:: Проверяем соединение с Docker сервером
echo 🔍 Проверка соединения с Docker сервером...
python upload_to_docker.py --test-connection
if errorlevel 1 (
    echo.
    echo ❌ Не удается подключиться к Docker серверу!
    echo    Убедитесь что Docker сервер запущен на порту 5000
    echo.
    echo 🚀 Попробуйте запустить Docker сервер командой:
    echo    docker-compose up -d
    echo.
    pause
    exit /b 1
)

echo ✅ Docker сервер доступен
echo.

:: Показываем текущие локальные данные
echo 📁 Проверка локальных данных...
python upload_to_docker.py --status
echo.

:: Спрашиваем пользователя что делать
echo ====================================================
echo Выберите действие:
echo.
echo 1. Запустить локальный парсинг (1 товар с каждой категории)
echo 2. Запустить локальный парсинг (5 товаров с каждой категории) 
echo 3. Запустить локальный парсинг (10 товаров с каждой категории)
echo 4. Отправить существующие данные на Docker сервер
echo 5. Показать статус локальных данных
echo 6. Выход
echo.
set /p choice="Введите номер (1-6): "

if "%choice%"=="1" goto parse_local_1
if "%choice%"=="2" goto parse_local_5
if "%choice%"=="3" goto parse_local_10
if "%choice%"=="4" goto upload_existing
if "%choice%"=="5" goto show_status
if "%choice%"=="6" goto end

echo ❌ Неверный выбор!
pause
goto end

:parse_local_1
echo.
echo 🔄 Запуск локального парсинга (1 товар с категории)...
echo ====================================================
python local_dns_parser.py --limit 1 --headless
if errorlevel 1 (
    echo ❌ Ошибка при парсинге!
    pause
    goto end
)
goto upload_after_parsing

:parse_local_5
echo.
echo 🔄 Запуск локального парсинга (5 товаров с категории)...
echo ====================================================
python local_dns_parser.py --limit 5 --headless
if errorlevel 1 (
    echo ❌ Ошибка при парсинге!
    pause
    goto end
)
goto upload_after_parsing

:parse_local_10
echo.
echo 🔄 Запуск локального парсинга (10 товаров с категории)...
echo ====================================================
python local_dns_parser.py --limit 10 --headless
if errorlevel 1 (
    echo ❌ Ошибка при парсинге!
    pause
    goto end
)
goto upload_after_parsing

:upload_after_parsing
echo.
echo ✅ Парсинг завершен!
echo.
echo 📤 Отправка данных на Docker сервер...
echo ====================================================
python upload_to_docker.py --upload --cleanup
if errorlevel 1 (
    echo ❌ Ошибка при отправке на Docker сервер!
    pause
    goto end
)

echo.
echo 🎉 Данные успешно отправлены на Docker сервер!
echo.
goto show_final_status

:upload_existing
echo.
echo 📤 Отправка существующих данных на Docker сервер...
echo ====================================================
python upload_to_docker.py --upload
if errorlevel 1 (
    echo ❌ Ошибка при отправке на Docker сервер!
    pause
    goto end
)

echo.
echo 🎉 Данные успешно отправлены на Docker сервер!
echo.
goto show_final_status

:show_status
echo.
echo 📊 Статус локальных данных:
echo ====================================================
python upload_to_docker.py --status
echo.
pause
goto end

:show_final_status
echo 📊 Проверка данных на Docker сервере...
echo ====================================================
python check_server_data.py
echo.

echo ✅ Процесс завершен!
echo    Данные спарсены локально и отправлены на Docker сервер
echo.
pause

:end
echo.
echo До свидания!
pause 