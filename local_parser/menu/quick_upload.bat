@echo off
chcp 65001 >nul
call "%~dp0_paths.bat"
call "%~dp0_resolve_dns_dump.bat"

echo ====================================================
echo       ZAGRUZKA POSLEDNEGO DNS-DAMPA
echo ====================================================
echo.
echo Server: %SERVER_URL%
echo.

if not defined DNS_DATA_FILE (
    echo Net fajla dns_*.json v data/dns/
    pause
    exit /b 1
)

call "%~dp0upload_latest_dns.bat"
pause
exit /b %errorlevel%
