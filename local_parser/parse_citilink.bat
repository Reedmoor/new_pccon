@echo off
chcp 65001 >nul
echo ====================================================
echo        ПАРСИНГ CITILINK — ВЫБОР КАТЕГОРИИ
echo ====================================================
echo.

cd /d "%~dp0"
call get_python.bat

for /f %%i in ('where "%PYTHON_CMD%" 2^>nul') do set FULL_PYTHON_PATH=%%i
if "%FULL_PYTHON_PATH%"=="" set FULL_PYTHON_PATH=%PYTHON_CMD%

set citi_dir=..\app\utils\Citi_parser

echo Доступные категории:
echo   1. videokarty          (Видеокарты)
echo   2. processory          (Процессоры)
echo   3. operativnaya-pamyat (Оперативная память)  —  используй citilink: moduli-pamyati
echo   4. moduli-pamyati      (Модули памяти / ОЗУ)
echo   5. materinskie-platy   (Материнские платы)
echo   6. sistemy-ohlazhdeniya-processora (Кулеры)
echo   7. korpusa             (Корпуса)
echo   8. bloki-pitaniya      (Блоки питания)
echo   9. zhestkie-diski      (Жёсткие диски)
echo  10. ssd-nakopiteli      (SSD накопители)
echo.

set /p cat_num="Введите номер категории (1-10): "

if "%cat_num%"=="1"  set cat_name=videokarty
if "%cat_num%"=="2"  set cat_name=processory
if "%cat_num%"=="3"  set cat_name=operativnaya-pamyat
if "%cat_num%"=="4"  set cat_name=moduli-pamyati
if "%cat_num%"=="5"  set cat_name=materinskie-platy
if "%cat_num%"=="6"  set cat_name=sistemy-ohlazhdeniya-processora
if "%cat_num%"=="7"  set cat_name=korpusa
if "%cat_num%"=="8"  set cat_name=bloki-pitaniya
if "%cat_num%"=="9"  set cat_name=zhestkie-diski
if "%cat_num%"=="10" set cat_name=ssd-nakopiteli

if not defined cat_name (
    echo ❌ Неверный номер категории!
    pause
    exit /b 1
)

echo.
echo 📋 Выбрана категория: %cat_name%
set /p max_products="Введите количество товаров для парсинга (Enter = без лимита): "

set max_products_clean=%max_products%
if not "%max_products_clean%"=="" (
    set non_digit=
    for /f "delims=0123456789" %%A in ("%max_products_clean%") do set non_digit=%%A
    if defined non_digit (
        echo ❌ Количество должно быть числом!
        pause
        exit /b 1
    )
)

set /p confirm="Начать парсинг? (y/n): "
if /i not "%confirm%"=="y" (
    echo Отменено.
    pause
    exit /b 0
)

REM Записываем .env с категорией для Citi_parser
echo CATEGORY=%cat_name%> "%citi_dir%\.env"
if not "%max_products_clean%"=="" (
    echo MAX_PRODUCTS=%max_products_clean%>> "%citi_dir%\.env"
    echo ✅ .env записан: CATEGORY=%cat_name%, MAX_PRODUCTS=%max_products_clean%
) else (
    echo ✅ .env записан: CATEGORY=%cat_name% (без лимита)
)

REM Удаляем старый флаг остановки
if exist "%citi_dir%\STOP_PARSER.flag" del "%citi_dir%\STOP_PARSER.flag"

echo.
echo 🚀 Запуск Citilink парсера...
echo.

set ORIGINAL_DIR=%CD%
cd /d "%citi_dir%"

"%FULL_PYTHON_PATH%" main.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Парсер завершился с ошибкой (код %errorlevel%)
    cd /d "%ORIGINAL_DIR%"
    pause
    exit /b 1
)

cd /d "%ORIGINAL_DIR%"

echo.
echo ✅ Парсинг завершён!
echo 📁 Данные сохранены в: %citi_dir%\data\%cat_name%\Товары.json
echo.

REM Предлагаем сразу загрузить
set /p upload_choice="Загрузить данные на сервер сейчас? (y/n): "
if /i "%upload_choice%"=="y" (
    call upload_citilink_auto.bat
)

pause
exit /b 0
