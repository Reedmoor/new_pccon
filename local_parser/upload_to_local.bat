@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: Принудительно устанавливаем рабочую директорию в папку скрипта
cd /d "%~dp0"

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                   🐳 ЗАГРУЗКА НА ЛОКАЛЬНЫЙ DOCKER                           ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

:: Настройка цветов
for /f %%A in ('echo prompt $E ^| cmd') do set "ESC=%%A"
set "GREEN=%ESC%[32m"
set "RED=%ESC%[31m"
set "YELLOW=%ESC%[33m"
set "BLUE=%ESC%[34m"
set "RESET=%ESC%[0m"

echo %BLUE%🐳 Локальный Docker: %GREEN%http://127.0.0.1:5000%RESET%
echo %YELLOW%📁 Рабочая папка: %GREEN%!CD!%RESET%
echo.

:: Проверяем Docker
echo %YELLOW%🔍 Проверка Docker...%RESET%
docker ps >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo %RED%❌ Docker не запущен или недоступен!%RESET%
    echo %BLUE%💡 Запустите Docker Desktop и выполните:%RESET%
    echo %BLUE%   cd ..%RESET%
    echo %BLUE%   docker-compose up -d%RESET%
    pause
    exit /b 1
) else (
    echo %GREEN%✅ Docker доступен%RESET%
)

:: Проверяем контейнеры
echo %YELLOW%🐳 Проверка контейнеров...%RESET%
docker ps | findstr pccon_web >nul
if !ERRORLEVEL! neq 0 (
    echo %RED%❌ Контейнер pccon_web не запущен!%RESET%
    echo %BLUE%💡 Запустите контейнеры:%RESET%
    echo %BLUE%   cd .. && docker-compose up -d%RESET%
    pause
    exit /b 1
) else (
    echo %GREEN%✅ Контейнер pccon_web запущен%RESET%
)

:: Проверяем файлы
echo %YELLOW%🔍 Проверка файлов...%RESET%
if not exist "upload_to_local.py" (
    echo %RED%❌ Файл upload_to_local.py не найден!%RESET%
    pause
    exit /b 1
) else (
    echo %GREEN%✅ upload_to_local.py найден%RESET%
)

:: Находим Python
call :find_python
if !ERRORLEVEL! neq 0 (
    echo %RED%❌ Python не найден!%RESET%
    pause
    exit /b 1
)

echo %YELLOW%📤 Запускаю загрузку на локальный Docker...%RESET%
echo.

:: Запускаем загрузку
"!PYTHON_CMD!" "%~dp0upload_to_local.py"

if !ERRORLEVEL! equ 0 (
    echo.
    echo %GREEN%✅ Загрузка завершена!%RESET%
    echo %BLUE%🌐 Проверьте результат: http://127.0.0.1:5000%RESET%
    echo %BLUE%🌐 Или через nginx: http://localhost%RESET%
    echo.
    echo %YELLOW%💡 Теперь данные доступны в локальном Docker%RESET%
) else (
    echo.
    echo %RED%❌ Ошибка загрузки данных!%RESET%
    echo %YELLOW%🔧 Проверьте логи: docker logs pccon_web%RESET%
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

echo %RED%❌ Python не найден! Установите Python%RESET%
exit /b 1

:python_found
echo !PYTHON_CMD! > "%~dp0python_cmd.txt"
echo %GREEN%🐍 Python найден: !PYTHON_CMD!%RESET%
exit /b 0 