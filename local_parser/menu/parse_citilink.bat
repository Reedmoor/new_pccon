@echo off
setlocal EnableExtensions
chcp 65001 >nul

echo ====================================================
echo           PARSING CITILINK
echo ====================================================
echo.

call "%~dp0_paths.bat"
if errorlevel 1 (
    echo ERROR: ne udalos zagruzit puti/Python
    pause
    exit /b 1
)

echo Server: %SERVER_URL%
echo.

for /f %%i in ('where "%PYTHON_CMD%" 2^>nul') do set "FULL_PYTHON_PATH=%%i"
if not defined FULL_PYTHON_PATH set "FULL_PYTHON_PATH=%PYTHON_CMD%"

set "CITI_DIR=%LP_ROOT%\..\app\utils\Citi_parser"

echo Dostupnye kategorii:
echo   1. videokarty
echo   2. processory
echo   3. operativnaya-pamyat  - dlya Citilink luchshe 4
echo   4. moduli-pamyati
echo   5. materinskie-platy
echo   6. sistemy-ohlazhdeniya-processora
echo   7. korpusa
echo   8. bloki-pitaniya
echo   9. zhestkie-diski
echo  10. ssd-nakopiteli
echo.

set /p cat_num="Nomer kategorii 1-10: "

set "cat_name="
if "%cat_num%"=="1" set "cat_name=videokarty"
if "%cat_num%"=="2" set "cat_name=processory"
if "%cat_num%"=="3" set "cat_name=operativnaya-pamyat"
if "%cat_num%"=="4" set "cat_name=moduli-pamyati"
if "%cat_num%"=="5" set "cat_name=materinskie-platy"
if "%cat_num%"=="6" set "cat_name=sistemy-ohlazhdeniya-processora"
if "%cat_num%"=="7" set "cat_name=korpusa"
if "%cat_num%"=="8" set "cat_name=bloki-pitaniya"
if "%cat_num%"=="9" set "cat_name=zhestkie-diski"
if "%cat_num%"=="10" set "cat_name=ssd-nakopiteli"

if not defined cat_name (
    echo Nevernyj nomer kategorii
    pause
    exit /b 1
)

echo.
echo Vybrana kategoriya: %cat_name%
set /p max_products="Kolichestvo tovarov, Enter=bez limita: "

set "max_products_clean=%max_products%"
if not "%max_products_clean%"=="" (
    set "non_digit="
    for /f "delims=0123456789" %%A in ("%max_products_clean%") do set "non_digit=%%A"
    if defined non_digit (
        echo Kolichestvo dolzhno byt chislom
        pause
        exit /b 1
    )
)

set /p confirm="Nachat parsing? y/n: "
if /i not "%confirm%"=="y" (
    echo Otmeneno
    pause
    exit /b 0
)

echo CATEGORY=%cat_name%> "%CITI_DIR%\.env"
if not "%max_products_clean%"=="" (
    echo MAX_PRODUCTS=%max_products_clean%>> "%CITI_DIR%\.env"
    echo .env: CATEGORY=%cat_name%, MAX_PRODUCTS=%max_products_clean%
) else (
    echo .env: CATEGORY=%cat_name%, bez limita
)

if exist "%CITI_DIR%\STOP_PARSER.flag" del "%CITI_DIR%\STOP_PARSER.flag"

echo.
echo Zapusk Citilink parsera...
cd /d "%CITI_DIR%"

"%FULL_PYTHON_PATH%" main.py
set "PARSE_ERR=%errorlevel%"

cd /d "%LP_ROOT%"

if not "%PARSE_ERR%"=="0" (
    echo.
    echo ERROR: parser zavershilsya s kodom %PARSE_ERR%
    pause
    exit /b 1
)

echo.
echo Parsing zavershen
echo Dannye: %CITI_DIR%\data\citilink\citilink_*.json
echo.

echo Avtozagruzka na %SERVER_URL% ...
call "%~dp0upload_latest_citilink.bat"
if errorlevel 1 (
    echo Avtozagruzka ne udalas. Poprobujte upload_citilink_auto.bat
) else (
    echo Tovary zagruzheny i importirovany v BD
)

pause
exit /b 0
