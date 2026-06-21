@echo off
setlocal EnableExtensions
chcp 65001 >nul
call "%~dp0_paths.bat"
call "%~dp0_resolve_dns_dump.bat"

echo ====================================================
echo       ZAGRUZKA DANNYH DNS
echo ====================================================
echo.
echo Server: %SERVER_URL%
echo.

set "data_file=%DNS_DATA_FILE%"
if not defined data_file (
    echo Net fajla dns_*.json v data/dns/
    echo Snachala zapustite parse_category.bat
    pause
    endlocal
    exit /b 1
)

echo Fajl: %data_file%
echo.

set /p confirm="Nachat zagruzku? y/n: "
if /i not "%confirm%"=="y" (
    pause
    endlocal
    exit /b 0
)

"%PYTHON_CMD%" "%LP_ROOT%\upload_single_file.py" --server-url "%SERVER_URL%" --data-file "%data_file%" --source dns
set "ERR=%errorlevel%"
pause
endlocal
exit /b %ERR%
