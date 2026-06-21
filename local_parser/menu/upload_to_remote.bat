@echo off
chcp 65001 >nul
call "%~dp0_paths.bat"

echo ====================================================
echo      ЗАГРУЗКА НА УДАЛЁННЫЙ СЕРВЕР (PCCONF.RU)
echo ====================================================
echo.
echo Сервер: %SERVER_URL%
echo.

call "%~dp0upload_to_pcconf.bat"
exit /b %errorlevel%
