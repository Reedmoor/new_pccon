@echo off
chcp 65001 >nul
echo ====================================================
echo        СИНХРОНИЗАЦИЯ СЕРВЕРОВ 5001 -> DOCKER
echo ====================================================
echo.

call "%~dp0_paths.bat"
set "PROJECT_ROOT=%LP_ROOT%\.."

echo 🔍 Проверка Docker контейнеров...
docker ps | findstr pccon_web >nul
if errorlevel 1 (
    echo.
    echo ❌ Docker контейнер pccon_web не запущен!
    echo.
    echo 🚀 Запускаем Docker контейнеры...
    cd /d "%PROJECT_ROOT%"
    docker-compose up -d
    if errorlevel 1 (
        echo ❌ Ошибка запуска Docker!
        pause
        exit /b 1
    )
    echo ✅ Docker контейнеры запущены
    echo ⏳ Ждем 10 секунд для инициализации...
    timeout /t 10 /nobreak >nul
    cd /d "%LP_ROOT%"
) else (
    echo ✅ Docker контейнер pccon_web запущен
)

echo.
echo 🔍 Определение правильных URL серверов...

:: Проверяем локальный сервер 5001
echo   • Проверка сервера 5001...
"%PYTHON_CMD%" "%LP_ROOT%\sync_servers.py" --source-url http://127.0.0.1:5001 --target-url http://127.0.0.1:5000 --test-only
if errorlevel 1 (
    echo.
    echo ❌ Проблема с серверами!
    echo.
    echo 🔧 Возможные решения:
    echo    1. Запустите локальный сервер: cd .. ^&^& python run.py
    echo    2. Проверьте Docker: docker-compose ps
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Серверы доступны!
echo.

echo 📊 Получение информации о данных...
"%PYTHON_CMD%" "%LP_ROOT%\sync_servers.py" --source-url http://127.0.0.1:5001 --target-url http://127.0.0.1:5000 --info
echo.

echo 🔄 Начинаем синхронизацию данных...
echo    ИЗ: 127.0.0.1:5001 (локальный сервер)
echo    В:  127.0.0.1:5000 (Docker контейнер pccon_web)
echo ====================================================

"%PYTHON_CMD%" "%LP_ROOT%\sync_servers.py" --source-url http://127.0.0.1:5001 --target-url http://127.0.0.1:5000 --sync

if errorlevel 1 (
    echo.
    echo ❌ Ошибка синхронизации!
    echo 📋 Проверьте логи выше для деталей
    pause
    exit /b 1
)

echo.
echo ✅ Синхронизация завершена успешно!
echo.

echo 📊 Проверка результатов...
echo ====================================================
"%PYTHON_CMD%" "%LP_ROOT%\check_server_data.py"

echo.
echo 🌐 Веб-интерфейс Docker сервера: http://127.0.0.1:5000
echo 📊 API статус: http://127.0.0.1:5000/api/parser-status
echo.
echo 🎉 Готово! Данные синхронизированы
pause 