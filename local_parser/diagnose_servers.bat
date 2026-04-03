@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: Принудительно устанавливаем рабочую директорию в папку скрипта
cd /d "%~dp0"

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                    🔍 ДИАГНОСТИКА СЕРВЕРОВ                                   ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

:: Настройка цветов
for /f %%A in ('echo prompt $E ^| cmd') do set "ESC=%%A"
set "GREEN=%ESC%[32m"
set "RED=%ESC%[31m"
set "YELLOW=%ESC%[33m"
set "BLUE=%ESC%[34m"
set "RESET=%ESC%[0m"

echo %YELLOW%🔍 Проверяю все доступные серверы:%RESET%
echo    • k4db-jl2g-6d7c.gw-1a.dockhost.net (текущий)
echo    • pcconf.ru (новый домен)  
echo    • 31.186.100.50 (IP адрес)
echo.

:: Проверяем наличие скрипта
if not exist "debug_server.py" (
    echo %RED%❌ Файл debug_server.py не найден!%RESET%
    pause
    exit /b 1
)

:: Находим Python
call :find_python
if !ERRORLEVEL! neq 0 (
    echo %RED%❌ Python не найден!%RESET%
    pause
    exit /b 1
)

echo %BLUE%🚀 Запускаю детальную диагностику...%RESET%
echo.

:: Запускаем диагностику
"!PYTHON_CMD!" "%~dp0debug_server.py"

echo.
echo %GREEN%✅ Диагностика завершена%RESET%
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