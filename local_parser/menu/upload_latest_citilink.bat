@echo off
setlocal EnableExtensions EnableDelayedExpansion

call "%~dp0_paths.bat"

set "citilink_flat=%LP_ROOT%\..\app\utils\Citi_parser\data\citilink"
set "server_url=%SERVER_URL%"

set "found="
for /f "delims=" %%F in ('dir /b /o-d "%citilink_flat%\citilink_*.json" 2^>nul') do (
    set "found=%%F"
    goto :upload_one
)

echo ERROR: net fajlov citilink_*.json v %citilink_flat%
exit /b 1

:upload_one
echo Zagruzka: !found!
"%PYTHON_CMD%" "%LP_ROOT%\upload_single_file.py" --server-url "%server_url%" --data-file "%citilink_flat%\!found!" --source citilink
exit /b !errorlevel!
