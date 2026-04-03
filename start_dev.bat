@echo off
chcp 65001 > nul
title PC Configurator — Dev Server

echo ============================================
echo   PC Configurator — локальный запуск
echo ============================================
echo.

:: Проверяем наличие виртуального окружения
if not exist ".venv\Scripts\python.exe" (
    echo [ОШИБКА] Виртуальное окружение не найдено.
    echo Создайте его: python -m venv .venv
    echo Установите зависимости: .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

:: Переменные окружения для разработки
set FLASK_ENV=development
set FLASK_DEBUG=1
set SECRET_KEY=dev-secret-key-local-only

:: Инициализируем БД (SQLite) если её нет
if not exist "instance\pccon.db" (
    echo [INFO] База данных не найдена — создаём SQLite...
    .venv\Scripts\python.exe -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('[OK] Таблицы созданы')"
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось инициализировать базу данных.
        pause
        exit /b 1
    )
    echo.
)

echo [INFO] База данных: SQLite (instance\pccon.db)
echo [INFO] Режим: разработка (debug=on)
echo [INFO] Адрес: http://127.0.0.1:5000
echo.
echo Для остановки нажмите Ctrl+C
echo ============================================
echo.

.venv\Scripts\python.exe run.py

pause
