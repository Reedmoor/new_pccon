@echo off
chcp 65001 >nul
echo ====================================================
echo           ТЕСТИРОВАНИЕ DOCKER ИНТЕГРАЦИИ
echo ====================================================
echo.

cd /d "%~dp0"

echo 🔍 Проверка статуса серверов...
echo.

echo 1️⃣ Проверка локального сервера (5001)...
curl -s http://127.0.0.1:5001/health >nul 2>&1
if errorlevel 1 (
    echo ❌ Локальный сервер 5001 недоступен
    echo 💡 Запустите: cd .. ^&^& python run.py
) else (
    echo ✅ Локальный сервер 5001 работает
)

echo.
echo 2️⃣ Проверка Docker сервера (5000)...
curl -s http://127.0.0.1:5000/health >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker сервер 5000 недоступен
    echo 💡 Запустите: docker-compose up -d
) else (
    echo ✅ Docker сервер 5000 работает
)

echo.
echo 3️⃣ Проверка API endpoints...
echo.

echo 📊 Проверка API статуса парсера...
curl -s http://127.0.0.1:5001/api/parser-status >nul 2>&1
if errorlevel 1 (
    echo ❌ API parser-status недоступен
) else (
    echo ✅ API parser-status работает
)

echo.
echo 📤 Проверка API экспорта продуктов...
curl -s http://127.0.0.1:5001/api/export-products >nul 2>&1
if errorlevel 1 (
    echo ❌ API export-products недоступен
) else (
    echo ✅ API export-products работает
)

echo.
echo 🐳 Проверка Docker API загрузки...
curl -s http://127.0.0.1:5000/api/parser-status >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker API недоступен
) else (
    echo ✅ Docker API работает
)

echo.
echo ====================================================
echo                  РЕЗУЛЬТАТ ПРОВЕРКИ
echo ====================================================

echo.
echo 💡 Доступные действия:
echo    • Синхронизация: sync_5001_to_5000_docker.bat
echo    • Анализ дублей: analyze_duplicates.bat
echo    • Локальные дубли: analyze_local_duplicates.bat
echo    • Веб-интерфейс: http://127.0.0.1:5001/admin/import
echo.

pause 