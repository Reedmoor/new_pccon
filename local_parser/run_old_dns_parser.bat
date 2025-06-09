@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ================================
echo    DNS Parser (Old Version)
echo       VISIBLE BROWSER
echo    DOCKER SERVER: 127.0.0.1:5000
echo ================================
echo.

:: Активируем виртуальное окружение
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    echo.
) else (
    echo Virtual environment not found, using global Python...
    echo.
)

:menu
echo Select parsing mode:
echo 1. Test connection to Docker server
echo 2. Parse videokarty (limit 3)
echo 3. Parse processory (limit 3)
echo 4. Parse materinskie-platy (limit 3)
echo 5. Parse operativnaya-pamyat (limit 3)
echo 6. Parse ssd-m2 (limit 3)
echo 7. Parse custom category
echo 0. Exit
echo.
set /p choice="Enter your choice (0-7): "

if "%choice%"=="0" goto end
if "%choice%"=="1" goto test
if "%choice%"=="2" goto videokarty
if "%choice%"=="3" goto processory
if "%choice%"=="4" goto materinskie
if "%choice%"=="5" goto memory
if "%choice%"=="6" goto ssd
if "%choice%"=="7" goto custom
goto menu

:test
echo.
echo Testing connection to Docker server...
python dns_parser_wrapper.py --test-only --server-url http://127.0.0.1:5000
goto continue

:videokarty
echo.
echo Parsing videokarty (limit 3) → Docker server...
echo Browser window will open and show DNS parsing process!
python dns_parser_wrapper.py --category videokarty --limit 3 --server-url http://127.0.0.1:5000
goto continue

:processory
echo.
echo Parsing processory (limit 3) → Docker server...
echo Browser window will open and show DNS parsing process!
python dns_parser_wrapper.py --category processory --limit 3 --server-url http://127.0.0.1:5000
goto continue

:materinskie
echo.
echo Parsing materinskie-platy (limit 3) → Docker server...
echo Browser window will open and show DNS parsing process!
python dns_parser_wrapper.py --category materinskie-platy --limit 3 --server-url http://127.0.0.1:5000
goto continue

:memory
echo.
echo Parsing operativnaya-pamyat (limit 3) → Docker server...
echo Browser window will open and show DNS parsing process!
python dns_parser_wrapper.py --category operativnaya-pamyat --limit 3 --server-url http://127.0.0.1:5000
goto continue

:ssd
echo.
echo Parsing ssd-m2 (limit 3) → Docker server...
echo Browser window will open and show DNS parsing process!
python dns_parser_wrapper.py --category ssd-m2 --limit 3 --server-url http://127.0.0.1:5000
goto continue

:custom
echo.
set /p custom_category="Enter category name: "
set /p custom_limit="Enter limit (default 5): "
if "%custom_limit%"=="" set custom_limit=5
echo.
echo Parsing %custom_category% (limit %custom_limit%) → Docker server...
echo Browser window will open and show DNS parsing process!
python dns_parser_wrapper.py --category %custom_category% --limit %custom_limit% --server-url http://127.0.0.1:5000
goto continue

:continue
echo.
echo ================================
set /p again="Run again? (y/n): "
if /i "%again%"=="y" goto menu

:end
echo.
echo Goodbye!
pause 