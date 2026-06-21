@echo off
REM Chitaet put k poslednemu DNS-dampu v peremennuyu DNS_DATA_FILE
set "DNS_DATA_DIR=%LP_ROOT%\..\app\utils\old_dns_parser\data\dns"
set "DNS_DATA_FILE="

if exist "%DNS_DATA_DIR%\last_session.txt" (
    set /p "DNS_DATA_FILE=" < "%DNS_DATA_DIR%\last_session.txt"
)

if not defined DNS_DATA_FILE (
    for /f "delims=" %%F in ('dir /b /o-d "%DNS_DATA_DIR%\dns_*.json" 2^>nul') do (
        set "DNS_DATA_FILE=%DNS_DATA_DIR%\%%F"
        goto :eof
    )
)

if not exist "%DNS_DATA_FILE%" set "DNS_DATA_FILE="
