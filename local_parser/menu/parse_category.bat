@echo off
setlocal EnableExtensions
chcp 65001 >nul

echo ====================================================
echo           PARSING KATEGORII DNS
echo ====================================================
echo.

call "%~dp0_paths.bat"
if errorlevel 1 (
    echo ERROR: ne udalos zagruzit puti/Python
    pause
    exit /b 1
)

echo Python: %PYTHON_CMD%
echo Server: %SERVER_URL%
echo.

for /f %%i in ('where "%PYTHON_CMD%" 2^>nul') do set "FULL_PYTHON_PATH=%%i"
if not defined FULL_PYTHON_PATH set "FULL_PYTHON_PATH=%PYTHON_CMD%"

echo Dostupnye kategorii:
echo   1. videokarty
echo   2. processory
echo   3. operativnaya-pamyat
echo   4. materinskie-platy
echo   5. kulery
echo   6. korpusa
echo   7. bloki-pitaniya
echo   8. zhestkie-diski
echo   9. ssd-m2
echo  10. ssd-sata
echo.

set /p category="Nomer kategorii 1-10: "

set "cat_name="
if "%category%"=="1" set "cat_name=videokarty"
if "%category%"=="2" set "cat_name=processory"
if "%category%"=="3" set "cat_name=operativnaya-pamyat"
if "%category%"=="4" set "cat_name=materinskie-platy"
if "%category%"=="5" set "cat_name=kulery"
if "%category%"=="6" set "cat_name=korpusa"
if "%category%"=="7" set "cat_name=bloki-pitaniya"
if "%category%"=="8" set "cat_name=zhestkie-diski"
if "%category%"=="9" set "cat_name=ssd-m2"
if "%category%"=="10" set "cat_name=ssd-sata"

if not defined cat_name (
    echo Nevernyj nomer kategorii
    pause
    exit /b 1
)

echo.
set /p limit="Kolichestvo tovarov, Enter=10: "
if "%limit%"=="" set "limit=10"

echo.
echo Vybrano: %cat_name%, limit %limit%
echo.

set /p confirm="Nachat parsing? y/n: "
if /i not "%confirm%"=="y" (
    echo Otmeneno
    pause
    exit /b 0
)

set "DNS_DIR=%LP_ROOT%\..\app\utils\old_dns_parser"
echo Zapusk parsera v %DNS_DIR%
cd /d "%DNS_DIR%"

if not exist "main.py" (
    echo ERROR: main.py ne najden
    pause
    exit /b 1
)

"%FULL_PYTHON_PATH%" main.py %cat_name% %limit%
set "PARSE_ERR=%errorlevel%"

cd /d "%LP_ROOT%"

if not "%PARSE_ERR%"=="0" (
    echo.
    echo ERROR: parser zavershilsya s kodom %PARSE_ERR%
    echo Proverite dns_parser.log v papke old_dns_parser
    pause
    exit /b 1
)

echo.
echo Parsing zavershen
echo Dannye: %DNS_DIR%\data\dns\dns_%cat_name%_*.json
echo.

echo ====================================================
echo           AVTOMATICHESKAYA ZAGRUZKA
echo ====================================================
echo   1 - zagruzit tolko etot parsing na %SERVER_URL%
echo   2 - propustit zagruzku
echo.
set /p upload_choice="Vybor 1/2: "

if "%upload_choice%"=="1" (
    call "%~dp0upload_latest_dns.bat"
    if errorlevel 1 (
        echo Oshibka zagruzki. Poprobujte upload_from_old_parser.bat
    ) else (
        echo Parsing i zagruzka zaversheny uspeshno
    )
) else (
    echo Zagruzka propushchena. Zapustite upload_from_old_parser.bat
)

echo.
echo Itog: kategoriya %cat_name%, limit %limit%
echo Server: %SERVER_URL%
echo.
pause
exit /b 0
