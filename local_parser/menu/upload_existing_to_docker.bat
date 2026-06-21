@echo off
echo ====================================================
echo        ОТПРАВКА ЛОКАЛЬНЫХ ДАННЫХ НА DOCKER СЕРВЕР
echo ====================================================
echo.

call "%~dp0_paths.bat"

echo 🔍 Проверка соединения с Docker сервером...
"%PYTHON_CMD%" "%LP_ROOT%\upload_to_docker.py" --test-connection
if errorlevel 1 (
    echo.
    echo ❌ Docker сервер недоступен!
    echo 🚀 Запустите Docker сервер командой: docker-compose up -d
    echo.
    pause
    exit /b 1
)

echo.
echo 📁 Проверка локальных данных...
"%PYTHON_CMD%" "%LP_ROOT%\upload_to_docker.py" --status
echo.

echo 📤 Отправка всех локальных данных на Docker сервер...
echo ====================================================
"%PYTHON_CMD%" "%LP_ROOT%\upload_to_docker.py" --upload

if errorlevel 1 (
    echo.
    echo ❌ Ошибка при отправке!
    pause
    exit /b 1
)

echo.
echo ✅ Данные успешно отправлены на Docker сервер!
echo.
echo 📊 Проверка данных на сервере...
"%PYTHON_CMD%" "%LP_ROOT%\check_server_data.py"

pause
