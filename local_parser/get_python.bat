@echo off
REM Функция для определения команды Python
REM Результат сохраняется в переменной PYTHON_CMD

REM Проверяем сохраненную команду
if exist "python_cmd.txt" (
    set /p PYTHON_CMD=<python_cmd.txt
    "%PYTHON_CMD%" --version >nul 2>&1
    if %errorlevel%==0 goto :eof
)

REM 1. Виртуальное окружение venv
if exist "venv\Scripts\python.exe" (
    set PYTHON_CMD=venv\Scripts\python.exe
    goto :eof
)

REM 2. Системный Python  
where python >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python
    goto :eof
)

REM 3. Python3
where python3 >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python3
    goto :eof
)

REM 4. py launcher
where py >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=py
    goto :eof
)

REM Если ничего не найдено
set PYTHON_CMD=python
goto :eof 