@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: Принудительно устанавливаем рабочую директорию в папку скрипта
cd /d "%~dp0"

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                   🌐 ЗАГРУЗКА НА УДАЛЕННЫЙ СЕРВЕР (ИСПРАВЛЕНО)              ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

:: Настройка цветов
for /f %%A in ('echo prompt $E ^| cmd') do set "ESC=%%A"
set "GREEN=%ESC%[32m"
set "RED=%ESC%[31m"
set "YELLOW=%ESC%[33m"
set "BLUE=%ESC%[34m"
set "RESET=%ESC%[0m"

echo %YELLOW%📁 Рабочая папка: %GREEN%!CD!%RESET%
echo.

:: Проверяем наличие скрипта
if not exist "upload_to_remote_server.py" (
    echo %RED%❌ Файл upload_to_remote_server.py не найден в текущей папке!%RESET%
    echo %BLUE%   Текущая папка: !CD!%RESET%
    echo %BLUE%   Содержимое папки:%RESET%
    dir *.py
    pause
    exit /b 1
) else (
    echo %GREEN%✅ upload_to_remote_server.py найден%RESET%
)

:: Проверяем и находим Python
call :find_python
if !ERRORLEVEL! neq 0 (
    echo %RED%❌ Python не найден! Запустите fix_python.bat%RESET%
    pause
    exit /b 1
)

:: Устанавливаем URL сервера по умолчанию (HTTP для решения SSL проблем)
if "%REMOTE_SERVER_URL%"=="" (
    set "REMOTE_SERVER_URL=http://k4db-jl2g-6d7c.gw-1a.dockhost.net"
)

:main_menu
cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                   🌐 ЗАГРУЗКА НА УДАЛЕННЫЙ СЕРВЕР (ИСПРАВЛЕНО)              ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

echo %BLUE%🎯 Текущий сервер: %GREEN%!REMOTE_SERVER_URL!%RESET%
echo %YELLOW%📁 Рабочая папка: %GREEN%!CD!%RESET%
echo.
echo %YELLOW%Выберите действие:%RESET%
echo.
echo   1. 🧪 Проверить подключение к серверу
echo   2. 📊 Показать статус сервера
echo   3. 📤 Загрузить последние данные парсера
echo   4. 📁 Загрузить конкретный файл
echo   5. 🔧 Диагностика подключения
echo   6. 🔄 Изменить URL сервера
echo   0. 🚪 Выход
echo.

set /p "choice=👉 Ваш выбор (0-6): "

if "%choice%"=="1" goto test_connection
if "%choice%"=="2" goto show_status
if "%choice%"=="3" goto upload_latest
if "%choice%"=="4" goto upload_file
if "%choice%"=="5" goto diagnose
if "%choice%"=="6" goto change_url
if "%choice%"=="0" goto exit
goto main_menu

:test_connection
echo.
echo %YELLOW%🧪 Проверка подключения к серверу...%RESET%
echo.

"!PYTHON_CMD!" "%~dp0upload_to_remote_server.py" --server-url "!REMOTE_SERVER_URL!" --test-connection

if !ERRORLEVEL! equ 0 (
    echo.
    echo %GREEN%✅ Подключение успешно!%RESET%
) else (
    echo.
    echo %RED%❌ Ошибка подключения! Попробуйте диагностику (пункт 5).%RESET%
)

echo.
pause
goto main_menu

:show_status
echo.
echo %YELLOW%📊 Получение статуса сервера...%RESET%
echo.

"!PYTHON_CMD!" "%~dp0upload_to_remote_server.py" --server-url "!REMOTE_SERVER_URL!" --status

echo.
pause
goto main_menu

:upload_latest
echo.
echo %YELLOW%📤 Поиск и загрузка последних данных парсера...%RESET%
echo.

"!PYTHON_CMD!" "%~dp0upload_to_remote_server.py" --server-url "!REMOTE_SERVER_URL!" --latest

if !ERRORLEVEL! equ 0 (
    echo.
    echo %GREEN%✅ Данные успешно загружены на удаленный сервер!%RESET%
    echo %BLUE%🌐 Проверьте результат: !REMOTE_SERVER_URL!%RESET%
) else (
    echo.
    echo %RED%❌ Ошибка загрузки данных! Попробуйте диагностику (пункт 5).%RESET%
)

echo.
pause
goto main_menu

:upload_file
echo.
echo %YELLOW%📁 Загрузка конкретного файла%RESET%
echo.

:: Показываем доступные файлы
echo %BLUE%Доступные файлы данных:%RESET%
echo.

if exist "..\old_dns_parser\product_data.json" (
    echo   • ..\old_dns_parser\product_data.json %GREEN%(старый парсер)%RESET%
)

if exist "..\data\local_parser_data_*.json" (
    echo   • Файлы в ..\data\local_parser_data_*.json %GREEN%(локальные данные)%RESET%
)

echo.
set /p "file_path=📝 Путь к файлу: "

if "%file_path%"=="" (
    echo %RED%❌ Путь к файлу не указан!%RESET%
    pause
    goto main_menu
)

if not exist "%file_path%" (
    echo %RED%❌ Файл не найден: %file_path%%RESET%
    pause
    goto main_menu
)

echo.
echo %YELLOW%📤 Загрузка файла на удаленный сервер...%RESET%
echo.

"!PYTHON_CMD!" "%~dp0upload_to_remote_server.py" --server-url "!REMOTE_SERVER_URL!" --data-file "%file_path%"

if !ERRORLEVEL! equ 0 (
    echo.
    echo %GREEN%✅ Файл успешно загружен на удаленный сервер!%RESET%
    echo %BLUE%🌐 Проверьте результат: !REMOTE_SERVER_URL!%RESET%
) else (
    echo.
    echo %RED%❌ Ошибка загрузки файла!%RESET%
)

echo.
pause
goto main_menu

:diagnose
echo.
echo %YELLOW%🔧 Диагностика подключения к серверу...%RESET%
echo.
echo %BLUE%Проверяю различные способы подключения:%RESET%
echo   • HTTP и HTTPS
echo   • Разные endpoints
echo   • С проверкой SSL и без
echo.

"!PYTHON_CMD!" "%~dp0upload_to_remote_server.py" --server-url "!REMOTE_SERVER_URL!" --diagnose

echo.
pause
goto main_menu

:change_url
echo.
echo %YELLOW%🔄 Изменение URL сервера%RESET%
echo.
echo %BLUE%Текущий URL: %GREEN%!REMOTE_SERVER_URL!%RESET%
echo.
echo %BLUE%Введите новый URL сервера:%RESET%
echo    HTTP (рекомендуется): http://k4db-jl2g-6d7c.gw-1a.dockhost.net
echo    HTTPS: https://k4db-jl2g-6d7c.gw-1a.dockhost.net
echo    Другой сервер: http://your-server.com
echo.
set /p "new_url=📝 Новый URL (Enter для сброса к HTTP): "

if "%new_url%"=="" (
    set "REMOTE_SERVER_URL=http://k4db-jl2g-6d7c.gw-1a.dockhost.net"
    echo %GREEN%✅ URL сброшен к HTTP: !REMOTE_SERVER_URL!%RESET%
) else (
    set "REMOTE_SERVER_URL=%new_url%"
    echo %GREEN%✅ URL изменен на: !REMOTE_SERVER_URL!%RESET%
)

echo.
pause
goto main_menu

:find_python
:: Автоопределение команды Python
set "PYTHON_CMD="

:: Проверяем venv в текущей папке
if exist "%~dp0venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0venv\Scripts\python.exe"
    goto python_found
)

:: Проверяем сохраненную команду
if exist "%~dp0python_cmd.txt" (
    set /p PYTHON_CMD<"%~dp0python_cmd.txt"
    "!PYTHON_CMD!" --version >nul 2>&1
    if !ERRORLEVEL! equ 0 goto python_found
)

:: Проверяем стандартные команды
for %%c in (python python3 py) do (
    %%c --version >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        set "PYTHON_CMD=%%c"
        goto python_found
    )
)

echo %RED%❌ Python не найден! Установите Python или запустите fix_python.bat%RESET%
exit /b 1

:python_found
echo !PYTHON_CMD! > "%~dp0python_cmd.txt"
echo %GREEN%🐍 Python найден: !PYTHON_CMD!%RESET%
exit /b 0

:exit
echo.
echo %GREEN%👋 До свидания!%RESET%
echo.
pause
exit /b 0 