@echo off
echo ====================================================
echo      СИНХРОНИЗАЦИЯ СЕРВЕРОВ 5001 -> 5000 (DOCKER)
echo ====================================================
echo.

cd /d "%~dp0"

echo 🔍 Проверка соединения с обоими серверами...
python sync_servers.py --test-only
if errorlevel 1 (
    echo.
    echo ❌ Один или оба сервера недоступны!
    echo.
    echo 🔧 Проверьте:
    echo    - Сервер 5001 запущен: run.py должен работать на порту 5001
    echo    - Docker сервер 5000: docker-compose up -d
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Оба сервера доступны!
echo.

echo 📊 Получение информации о сервере 5001...
python sync_servers.py --info
echo.

echo 🔄 Начинаем синхронизацию данных...
echo    ИЗ: 127.0.0.1:5001 (исходный сервер)
echo    В:  127.0.0.1:5000 (Docker сервер)
echo ====================================================

python sync_servers.py --sync

if errorlevel 1 (
    echo.
    echo ❌ Ошибка синхронизации!
    pause
    exit /b 1
)

echo.
echo ✅ Синхронизация завершена успешно!
echo.

echo 📊 Проверка данных на Docker сервере...
python check_server_data.py

echo.
echo 🎉 Готово! Данные перенесены с 5001 на 5000
pause 