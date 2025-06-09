@echo off
chcp 65001 >nul
echo ====================================================
echo          НАСТРОЙКА PYTHON ОКРУЖЕНИЯ
echo ====================================================
echo.

cd /d "%~dp0"

echo 🐍 Поиск Python...

REM Попробуем найти Python в разных местах
set PYTHON_CMD=

REM 1. Виртуальное окружение venv
if exist "venv\Scripts\python.exe" (
    set PYTHON_CMD=venv\Scripts\python.exe
    echo ✅ Найден Python в venv: %PYTHON_CMD%
    goto found
)

REM 2. Системный Python
where python >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python
    echo ✅ Найден системный Python
    goto found
)

REM 3. Python3
where python3 >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python3
    echo ✅ Найден python3
    goto found
)

REM 4. Python в Program Files
if exist "C:\Python*\python.exe" (
    for /d %%i in ("C:\Python*") do (
        if exist "%%i\python.exe" (
            set PYTHON_CMD=%%i\python.exe
            echo ✅ Найден Python в Program Files: %%i
            goto found
        )
    )
)

REM 5. Python в AppData Local
if exist "%LOCALAPPDATA%\Programs\Python\Python*\python.exe" (
    for /d %%i in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
        if exist "%%i\python.exe" (
            set PYTHON_CMD=%%i\python.exe
            echo ✅ Найден Python в AppData: %%i
            goto found
        )
    )
)

echo ❌ Python не найден!
echo.
echo 💡 Установите Python:
echo    1. Скачайте с https://python.org
echo    2. Или создайте venv: python -m venv venv
echo.
pause
exit /b 1

:found
echo.
echo 🔧 Проверка зависимостей...

REM Проверяем что Python работает
"%PYTHON_CMD%" --version
if %errorlevel% neq 0 (
    echo ❌ Python не запускается!
    pause
    exit /b 1
)

REM Устанавливаем зависимости если есть requirements.txt
if exist "requirements.txt" (
    echo 📦 Установка зависимостей...
    "%PYTHON_CMD%" -m pip install -r requirements.txt
)

echo.
echo ✅ Python настроен успешно!
echo 📋 Команда Python: %PYTHON_CMD%
echo.

REM Сохраняем команду в файл для других скриптов
echo %PYTHON_CMD% > python_cmd.txt

pause 