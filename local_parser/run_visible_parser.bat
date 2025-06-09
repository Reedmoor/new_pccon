@echo off
chcp 65001 >nul
title DNS Parser - Visible Mode (Old DNS Parser)

echo ==============================================
echo  DNS Parser - Visible Browser Mode
echo       Using old_dns_parser logic
echo ==============================================
echo Starting at: %date% %time%
echo Arguments: %*
echo.

REM Переходим в директорию парсера
cd /d "%~dp0"

REM Активируем виртуальное окружение
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found, using system Python
)

REM Запускаем обёртку old_dns_parser с переданными аргументами
echo Running DNS parser wrapper with arguments: %*
python dns_parser_wrapper.py %*

echo.
echo ==============================================
echo Parser finished at: %date% %time%
echo Press any key to close...
pause >nul 