@echo off
chcp 65001 >nul
title Система управления данными ПК

REM Определяем команду Python
call get_python.bat

:menu
cls
echo ====================================================
echo         СИСТЕМА УПРАВЛЕНИЯ ДАННЫМИ ПК
echo ====================================================
echo.
echo 🐍 Python: %PYTHON_CMD%
echo.
echo 🔧 Основные операции:
echo.
echo   1. 🚀 Парсинг + автозагрузка (рекомендуется)
echo   2. 📤 Импорт данных на сервер  
echo   3. 🔄 Синхронизация серверов (5001→5000)
echo   4. 🌐 Загрузка на удаленный сервер
echo   5. ⚡ Быстрая загрузка на ВАШ сервер
echo   6. 🧹 Анализ дублей
echo   7. 🔍 Тестирование Docker интеграции
echo.
echo 🛠️ Дополнительные операции:
echo.
echo   8. 📊 Проверка данных на серверах
echo   9. 📂 Управление локальными данными
echo   10. ⬆️ Загрузка существующих данных
echo   11. 📁 Ручная загрузка из старого парсера
echo   12. 🐍 Настройка Python окружения
echo.
echo   0. ❌ Выход
echo.
echo ====================================================

set /p choice="Выберите операцию (0-12): "

if "%choice%"=="1" goto parse_category
if "%choice%"=="2" goto import_data
if "%choice%"=="3" goto sync_servers
if "%choice%"=="4" goto upload_remote
if "%choice%"=="5" goto quick_upload
if "%choice%"=="6" goto analyze_duplicates
if "%choice%"=="7" goto test_integration
if "%choice%"=="8" goto check_data
if "%choice%"=="9" goto manage_local
if "%choice%"=="10" goto upload_existing
if "%choice%"=="11" goto upload_old_parser
if "%choice%"=="12" goto setup_python
if "%choice%"=="0" goto exit

echo.
echo ❌ Неверный выбор! Нажмите любую клавишу...
pause >nul
goto menu

:parse_category
cls
echo 🚀 Запуск парсинга с автозагрузкой...
call parse_category.bat
goto menu

:import_data
cls  
echo 📤 Запуск импорта данных...
call import_data.bat
goto menu

:sync_servers
cls
echo 🔄 Запуск синхронизации серверов...
call sync_5001_to_5000_docker.bat
goto menu

:upload_remote
cls
echo 🌐 Загрузка данных на удаленный сервер...
call upload_to_remote.bat
goto menu

:quick_upload
cls
echo ⚡ Быстрая загрузка на ваш сервер...
call quick_upload.bat
goto menu

:analyze_duplicates
cls
echo 🧹 Анализ дублей...
echo.
echo Выберите тип анализа:
echo 1. Локальные дубли (local_data)
echo 2. Дубли на Docker сервере
echo.
set /p dup_choice="Выбор (1-2): "

if "%dup_choice%"=="1" (
    "%PYTHON_CMD%" cleanup_local_data.py --analyze
    pause
) else if "%dup_choice%"=="2" (
    "%PYTHON_CMD%" cleanup_duplicates.py --analyze
    pause
) else (
    echo ❌ Неверный выбор!
    pause
)
goto menu

:test_integration
cls
echo 🔍 Тестирование Docker интеграции...
call test_docker_integration.bat
goto menu

:check_data
cls
echo 📊 Проверка данных на серверах...
"%PYTHON_CMD%" check_server_data.py
echo.
pause
goto menu

:manage_local
cls
echo 📂 Управление локальными данными...
"%PYTHON_CMD%" local_data_manager.py --stats
echo.
pause
goto menu

:upload_existing
cls
echo ⬆️ Загрузка существующих данных...
call upload_existing_to_docker.bat
goto menu

:upload_old_parser
cls
echo 📁 Ручная загрузка данных из старого парсера...
call upload_from_old_parser.bat
goto menu

:setup_python
cls
echo 🐍 Настройка Python окружения...
call setup_python.bat
call get_python.bat
goto menu

:exit
echo.
echo 👋 До свидания!
echo.
exit /b 0 