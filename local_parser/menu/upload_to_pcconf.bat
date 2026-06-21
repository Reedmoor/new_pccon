@echo off
chcp 65001 >nul
title Загрузка данных на pcconf.ru

call "%~dp0_paths.bat"

echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                      ЗАГРУЗКА НА PCCONF.RU                                  ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.
echo Python: %PYTHON_CMD%
echo Сервер: %SERVER_URL%
echo.

if not exist "%LP_ROOT%\upload_to_pcconf.py" (
    echo [ERROR] Файл upload_to_pcconf.py не найден!
    pause
    exit /b 1
)

set "CMD_ARGS=--url %SERVER_URL%"
"%PYTHON_CMD%" "%LP_ROOT%\upload_to_pcconf.py" %CMD_ARGS%

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Произошла ошибка при выполнении скрипта.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [SUCCESS] Операция завершена!
echo.
pause
