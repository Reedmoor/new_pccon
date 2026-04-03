@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: Принудительно устанавливаем рабочую директорию в папку скрипта
cd /d "%~dp0"

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                   🚀 БЫСТРАЯ ЗАГРУЗКА НА ВАШ СЕРВЕР                         ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

:: Настройка цветов
for /f %%A in ('echo prompt $E ^| cmd') do set "ESC=%%A"
set "GREEN=%ESC%[32m"
set "RED=%ESC%[31m"
set "YELLOW=%ESC%[33m"
set "BLUE=%ESC%[34m"
set "RESET=%ESC%[0m"

:: URL вашего сервера (HTTP для решения SSL проблем)
set "SERVER_URL=http://k4db-jl2g-6d7c.gw-1a.dockhost.net"

echo %BLUE%🎯 Сервер: %GREEN%!SERVER_URL!%RESET%
echo %YELLOW%📁 Рабочая папка: %GREEN%!CD!%RESET%
echo.

:: Проверяем файлы
echo %YELLOW%🔍 Проверка файлов...%RESET%
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

echo %YELLOW%📤 Загружаю последние данные парсера на ваш сервер...%RESET%
echo.

:: Запускаем загрузку с полным путем к скрипту
"!PYTHON_CMD!" "%~dp0upload_to_remote_server.py" --server-url "!SERVER_URL!" --latest

if !ERRORLEVEL! equ 0 (
    echo.
    echo %GREEN%✅ Данные успешно загружены на ваш сервер!%RESET%
    echo %BLUE%🌐 Проверьте результат: !SERVER_URL!%RESET%
    echo.
    echo %YELLOW%💡 Совет: Теперь можете открыть ваш сайт в браузере%RESET%
) else (
    echo.
    echo %RED%❌ Ошибка загрузки данных!%RESET%
    echo %YELLOW%🔧 Попробуйте upload_to_remote_fixed.bat для диагностики%RESET%
    echo %BLUE%💡 Или попробуйте HTTPS: https://k4db-jl2g-6d7c.gw-1a.dockhost.net%RESET%
)

echo.
pause
exit /b 0

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