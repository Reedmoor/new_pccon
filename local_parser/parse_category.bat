@echo off
chcp 65001 >nul
echo ====================================================
echo           ПАРСИНГ КАТЕГОРИИ С ВЫБОРОМ
echo ====================================================
echo.

cd /d "%~dp0"

REM Определяем команду Python
call get_python.bat
echo 🐍 Используется Python: %PYTHON_CMD%

REM Получаем полный путь к Python для использования в другой папке
for /f %%i in ('where "%PYTHON_CMD%"') do set FULL_PYTHON_PATH=%%i
if "%FULL_PYTHON_PATH%"=="" (
    REM Если where не работает, пробуем относительный путь
    if exist "%~dp0%PYTHON_CMD%" (
        set FULL_PYTHON_PATH=%~dp0%PYTHON_CMD%
    ) else (
        set FULL_PYTHON_PATH=%PYTHON_CMD%
    )
)

echo 🔍 Полный путь Python: %FULL_PYTHON_PATH%
echo.

echo Доступные категории:
echo 1. videokarty (Видеокарты)
echo 2. processory (Процессоры) 
echo 3. operativnaya-pamyat (Оперативная память)
echo 4. materinskie-platy (Материнские платы)
echo 5. kulery (Кулеры)
echo 6. korpusa (Корпуса)
echo 7. bloki-pitaniya (Блоки питания)
echo 8. zhestkie-diski (Жесткие диски)
echo 9. ssd-m2 (SSD M.2 накопители)
echo 10. ssd-sata (SSD SATA накопители)
echo.

set /p category="Введите номер категории (1-10): "

if "%category%"=="1" set cat_name=videokarty
if "%category%"=="2" set cat_name=processory
if "%category%"=="3" set cat_name=operativnaya-pamyat
if "%category%"=="4" set cat_name=materinskie-platy
if "%category%"=="5" set cat_name=kulery
if "%category%"=="6" set cat_name=korpusa
if "%category%"=="7" set cat_name=bloki-pitaniya
if "%category%"=="8" set cat_name=zhestkie-diski
if "%category%"=="9" set cat_name=ssd-m2
if "%category%"=="10" set cat_name=ssd-sata

if not defined cat_name (
    echo ❌ Неверный номер категории!
    pause
    exit /b 1
)

echo.
set /p limit="Введите количество товаров для парсинга (по умолчанию 10): "
if "%limit%"=="" set limit=10

echo.
echo 📋 Выбрано:
echo    Категория: %cat_name%
echo    Количество: %limit%
echo    Парсер: old_dns_parser (прямой запуск)
echo.

set /p confirm="Начать парсинг? (y/n): "
if /i not "%confirm%"=="y" (
    echo Операция отменена
    pause
    exit /b 0
)

echo.
echo 🚀 Запуск старого DNS парсера...
echo.

REM Сохраняем текущую папку
set ORIGINAL_DIR=%CD%

REM Переходим в папку old_dns_parser
echo 📂 Переход в папку: ..\app\utils\old_dns_parser
cd /d "..\app\utils\old_dns_parser"

if not exist "main.py" (
    echo ❌ Файл main.py не найден в папке old_dns_parser!
    echo 💡 Текущая папка: %CD%
    pause
    cd /d "%ORIGINAL_DIR%"
    exit /b 1
)

echo ✅ Найден main.py, запускаем парсер...
echo 🐍 Используемая команда: "%FULL_PYTHON_PATH%" main.py %cat_name% %limit%

REM Запускаем парсер напрямую
"%FULL_PYTHON_PATH%" main.py %cat_name% %limit%

if %errorlevel% neq 0 (
    echo.
    echo ❌ Ошибка при запуске парсера!
    echo 💡 Проверьте что Chrome установлен и доступен
    echo 💡 Проверьте логи в dns_parser.log
    echo.
    pause
    cd /d "%ORIGINAL_DIR%"
    exit /b 1
)

echo.
echo ✅ Парсинг завершен!
echo 📁 Результаты сохранены в product_data.json
echo.

REM Возвращаемся в исходную папку
cd /d "%ORIGINAL_DIR%"

echo ====================================================
echo            АВТОМАТИЧЕСКАЯ ЗАГРУЗКА ДАННЫХ
echo ====================================================
echo.
echo 🎯 Парсинг успешно завершен!
echo 📊 Данные готовы к отправке на сервер
echo.
echo 💡 Варианты действий:
echo    1. Автоматически загрузить на сервер (рекомендуется)
echo    2. Проверить данные вручную
echo    3. Завершить без загрузки
echo.

set /p upload_choice="Выберите действие (1/2/3): "

if "%upload_choice%"=="1" (
    echo.
    echo 🚀 Автоматическая загрузка данных на сервер...
    echo ====================================================
    echo.
    
    REM Запускаем upload_from_old_parser.bat автоматически
    call upload_from_old_parser_auto.bat
    
    if %errorlevel% equ 0 (
        echo.
        echo 🎉 ПОЛНЫЙ WORKFLOW ЗАВЕРШЕН УСПЕШНО!
        echo ✅ Данные спарсены и загружены на сервер
    ) else (
        echo.
        echo ❌ Ошибка при загрузке данных
        echo 💡 Попробуйте запустить upload_from_old_parser.bat вручную
    )
    
) else if "%upload_choice%"=="2" (
    echo.
    echo 📁 Данные сохранены в: old_dns_parser\product_data.json
    echo 💡 Для загрузки на сервер запустите: upload_from_old_parser.bat
    
) else if "%upload_choice%"=="3" (
    echo.
    echo ⏸️ Парсинг завершен, загрузка пропущена
    echo 💡 Для загрузки позже запустите: upload_from_old_parser.bat
    
) else (
    echo.
    echo ❌ Неверный выбор! Завершение без загрузки
    echo 💡 Для загрузки позже запустите: upload_from_old_parser.bat
)

echo.
echo 📋 Итоги:
echo    • Категория: %cat_name%
echo    • Количество: %limit%
echo    • Файл данных: old_dns_parser\product_data.json
echo    • Веб-интерфейс: http://127.0.0.1:5000
echo.
pause 