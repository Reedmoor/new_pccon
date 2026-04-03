@echo off
chcp 65001 >nul
title Парсинг и загрузка на pcconf.ru

REM Определяем команду Python
call get_python.bat

echo ================================================================================
echo             ПАРСИНГ И АВТОМАТИЧЕСКАЯ ЗАГРУЗКА НА PCCONF.RU                  
echo ================================================================================
echo.

echo Python: %PYTHON_CMD%
echo.

REM Запускаем парсинг
echo [STEP 1] Запуск парсинга данных...
echo.
call parse_category.bat

REM Проверяем результат парсинга
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Ошибка при парсинге данных.
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [SUCCESS] Парсинг данных успешно завершен.
echo.

REM Запускаем загрузку на pcconf.ru
echo [STEP 2] Загрузка данных на pcconf.ru...
echo.
call upload_to_pcconf.bat

REM Проверяем результат загрузки
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Ошибка при загрузке данных на pcconf.ru.
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [SUCCESS] Загрузка данных на pcconf.ru успешно завершена.
echo.
echo [SUCCESS] Все операции выполнены успешно!
echo.

pause 