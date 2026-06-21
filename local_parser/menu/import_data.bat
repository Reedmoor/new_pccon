@echo off
chcp 65001 >nul
echo ====================================================
echo        ИМПОРТ ДАННЫХ НА СЕРВЕР
echo ====================================================
echo.

call "%~dp0_paths.bat"
echo 🐍 Используется Python: %PYTHON_CMD%
echo 🌐 Продакшн-сервер: %SERVER_URL%
echo.

echo Выберите режим импорта:
echo.
echo 1. Импорт локальных данных (local_data/*.json → веб-сервер 5000)
echo 2. Синхронизация с сервера 5001 на Docker 5000
echo 3. Экспорт для хостинга (из базы данных)
echo 4. Полный цикл: парсинг → веб-сервер 5000
echo.
echo 0. ❌ Выход
echo.

set /p choice="Выберите режим (0-4): "

if "%choice%"=="1" goto import_local
if "%choice%"=="2" goto sync_servers  
if "%choice%"=="3" goto export_hosting
if "%choice%"=="4" goto full_cycle
if "%choice%"=="0" goto exit

echo.
echo ❌ Неверный выбор!
pause
goto menu

:import_local
cls
echo ====================================================
echo 📂 Импорт локальных данных на веб-сервер 5000...
echo ====================================================
echo.

echo 🔍 Проверка наличия файлов данных...
echo.

REM Импортируем локальные данные напрямую на веб-сервер
"%PYTHON_CMD%" "%LP_ROOT%\upload_to_docker.py" --server-url http://127.0.0.1:5000

if %errorlevel% neq 0 (
    echo ❌ Ошибка импорта!
    pause
    exit /b 1
)

echo.
echo ✅ Импорт завершен!
goto sync_to_docker

:sync_servers
echo 🔄 Синхронизация серверов 5001 → 5000...
call sync_5001_to_5000_docker.bat
echo.
echo ✅ Синхронизация завершена!
echo.
pause
exit /b 0

:export_hosting
cls
echo ====================================================
echo 📤 Экспорт данных для хостинга...
echo ====================================================
echo.

"%PYTHON_CMD%" "%LP_ROOT%\upload_existing_data.py" --export-only

echo.
echo ✅ Экспорт завершен!
pause
exit /b 0

:full_cycle
cls
echo ====================================================
echo 🔄 Полный цикл: парсинг + загрузка на веб-сервер 5000...
echo ====================================================
echo.

echo Доступные категории для парсинга:
echo.
echo 1. Процессоры (processor)
echo 2. Видеокарты (graphics_card)  
echo 3. Материнские платы (motherboard)
echo 4. Оперативная память (ram)
echo 5. SSD/HDD (hard_drive)
echo 6. Блоки питания (power_supply)
echo 7. Корпуса (case)
echo 8. Кулеры (cooler)
echo.

set /p cat_choice="Выберите категорию (1-8): "

echo.
set /p limit_choice="Количество товаров для парсинга (по умолчанию 20): "
if "%limit_choice%"=="" set limit_choice=20

echo.
echo 📋 Параметры парсинга:
echo    Категория: %cat_choice%
echo    Количество: %limit_choice%
echo    Сервер: http://127.0.0.1:5000 (веб-сервер)
echo.

set /p confirm="Начать парсинг? (y/n): "
if /i not "%confirm%"=="y" (
    echo Операция отменена
    pause
    exit /b 0
)

echo.
echo 🚀 Запуск парсера...
echo.

REM Запускаем локальный парсер с загрузкой на веб-сервер
"%PYTHON_CMD%" "%LP_ROOT%\local_dns_parser.py" --category %cat_choice% --limit %limit_choice% --server-url "%SERVER_URL%"

if %errorlevel% neq 0 (
    echo ❌ Ошибка парсинга!
    pause
    exit /b 1
)

echo.
echo 📤 Загрузка данных на сервер...
"%PYTHON_CMD%" "%LP_ROOT%\upload_to_docker.py" --server-url http://127.0.0.1:5000

if %errorlevel% neq 0 (
    echo ❌ Ошибка загрузки!
    pause
    exit /b 1
)

echo.
echo ✅ Полный цикл завершен успешно!
echo.
echo 💡 Проверить результат можно:
echo    • Веб-интерфейс Docker: http://127.0.0.1:5000
echo.
pause
exit /b 0

:sync_to_docker
echo.
echo 🔄 Синхронизация с Docker сервером...
call sync_5001_to_5000_docker.bat

:exit
echo.
echo 👋 Импорт завершен!
pause
exit /b 0 