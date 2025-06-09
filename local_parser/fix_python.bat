@echo off
chcp 65001 >nul
echo ====================================================
echo            БЫСТРОЕ ИСПРАВЛЕНИЕ PYTHON
echo ====================================================
echo.

cd /d "%~dp0"

echo 🔍 Диагностика проблемы с Python...
echo.

REM Проверяем все возможные команды Python
echo Проверка команд Python:
echo.

echo 📋 1. Проверка "python":
where python >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Команда python найдена
    python --version 2>nul
) else (
    echo ❌ Команда python НЕ найдена
)

echo.
echo 📋 2. Проверка "python3":
where python3 >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Команда python3 найдена
    python3 --version 2>nul
) else (
    echo ❌ Команда python3 НЕ найдена
)

echo.
echo 📋 3. Проверка "py":
where py >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Команда py найдена
    py --version 2>nul
) else (
    echo ❌ Команда py НЕ найдена
)

echo.
echo 📋 4. Проверка venv:
if exist "venv\Scripts\python.exe" (
    echo ✅ Виртуальное окружение найдено
    venv\Scripts\python.exe --version 2>nul
) else (
    echo ❌ Виртуальное окружение НЕ найдено
)

echo.
echo ====================================================
echo                  РЕШЕНИЯ
echo ====================================================
echo.
echo 💡 Варианты решения:
echo.
echo   1. 🔧 Активировать venv (если есть)
echo   2. 📦 Создать новый venv  
echo   3. 🌐 Установить Python с python.org
echo   4. 🚀 Использовать py launcher
echo.

set /p solution="Выберите решение (1-4): "

if "%solution%"=="1" goto activate_venv
if "%solution%"=="2" goto create_venv
if "%solution%"=="3" goto install_python
if "%solution%"=="4" goto use_py

echo ❌ Неверный выбор!
pause
exit /b 1

:activate_venv
echo.
echo 🔧 Активация существующего venv...
if exist "venv\Scripts\python.exe" (
    echo venv\Scripts\python.exe > python_cmd.txt
    echo ✅ venv активирован! Сохранена команда в python_cmd.txt
) else (
    echo ❌ venv не найден!
)
goto end

:create_venv
echo.
echo 📦 Создание нового venv...
echo.

REM Пробуем разные команды для создания venv
python -m venv venv 2>nul
if %errorlevel%==0 goto venv_created

python3 -m venv venv 2>nul
if %errorlevel%==0 goto venv_created

py -m venv venv 2>nul
if %errorlevel%==0 goto venv_created

echo ❌ Не удалось создать venv!
echo 💡 Сначала установите Python
goto end

:venv_created
echo ✅ venv создан успешно!
echo 📦 Установка зависимостей...
venv\Scripts\python.exe -m pip install -r requirements.txt
echo venv\Scripts\python.exe > python_cmd.txt
echo ✅ Готово! Команда сохранена в python_cmd.txt
goto end

:install_python  
echo.
echo 🌐 Установка Python...
echo.
echo 📋 Шаги для установки:
echo   1. Откройте https://python.org/downloads/
echo   2. Скачайте Python 3.8 или новее
echo   3. При установке отметьте "Add to PATH"
echo   4. Перезагрузите командную строку
echo   5. Запустите этот скрипт снова
echo.
start https://python.org/downloads/
goto end

:use_py
echo.
echo 🚀 Настройка py launcher...
where py >nul 2>&1
if %errorlevel%==0 (
    echo py > python_cmd.txt
    echo ✅ py launcher настроен!
) else (
    echo ❌ py launcher не найден!
    echo 💡 Установите Python с python.org
)
goto end

:end
echo.
echo ====================================================
echo.
echo 🔧 Диагностика завершена!
echo.
echo 💡 Теперь можно запускать:
echo    • main_menu.bat - главное меню
echo    • parse_category.bat - парсинг
echo    • import_data.bat - импорт
echo.
pause 