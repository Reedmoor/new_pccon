@echo off
chcp 65001 >nul
title Загрузка данных на pcconf.ru

REM Определяем команду Python
call get_python.bat

echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                      ЗАГРУЗКА НА PCCONF.RU                                  ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

echo Python: %PYTHON_CMD%
echo.

REM Проверяем наличие файла скрипта
if not exist "upload_to_pcconf.py" (
    echo [ERROR] Файл upload_to_pcconf.py не найден!
    echo.
    echo Пожалуйста, убедитесь, что файл находится в текущей директории.
    echo.
    pause
    exit /b 1
)

echo [INFO] Проверка соединения с pcconf.ru...
echo.

REM Спрашиваем пользователя о настройках
set USE_HTTP=
set /p USE_HTTP="Использовать HTTP вместо HTTPS? (y/n, по умолчанию - n): "

set CUSTOM_URL=
set /p CUSTOM_URL="Введите альтернативный URL (оставьте пустым для pcconf.ru): "

REM Формируем параметры командной строки
set "CMD_ARGS="

if /i "%USE_HTTP%"=="y" (
    set "CMD_ARGS=%CMD_ARGS% --no-ssl-verify"
    if "%CUSTOM_URL%"=="" (
        set "CMD_ARGS=%CMD_ARGS% --url http://pcconf.ru"
    )
)

if not "%CUSTOM_URL%"=="" (
    set "CMD_ARGS=%CMD_ARGS% --url %CUSTOM_URL%"
)

REM Запускаем скрипт загрузки с параметрами
"%PYTHON_CMD%" upload_to_pcconf.py %CMD_ARGS%

REM Проверяем код возврата
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Произошла ошибка при выполнении скрипта.
    echo.
    echo Проверьте:
    echo  - Подключение к интернету
    echo  - Доступность сайта pcconf.ru
    echo  - Наличие данных для загрузки в папке data/
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [SUCCESS] Операция завершена!
echo.

pause 