@echo off
setlocal EnableExtensions
call "%~dp0_paths.bat"
call "%~dp0_resolve_dns_dump.bat"

set "server_url=%SERVER_URL%"
set "data_file=%DNS_DATA_FILE%"

if not defined data_file (
    echo ERROR: net DNS-dampov. Snachala parsing.
    endlocal
    exit /b 1
)

echo AVTOMATICHESKAYA ZAGRUZKA DNS
echo Server: %server_url%
echo File: %data_file%
echo.

"%PYTHON_CMD%" "%LP_ROOT%\upload_single_file.py" --server-url "%server_url%" --data-file "%data_file%" --source dns
set "ERR=%errorlevel%"
endlocal
exit /b %ERR%
