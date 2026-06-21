@echo off
REM Obshij prefiks: LP_ROOT, PYTHON_CMD, SERVER_URL dlya menu/*.bat
cd /d "%~dp0\.."
set "LP_ROOT=%CD%"
if not defined PYTHON_CMD call "%LP_ROOT%\get_python.bat"
if not defined SERVER_URL (
    if exist "%LP_ROOT%\config\server.url" (
        set /p "SERVER_URL=" < "%LP_ROOT%\config\server.url"
    )
)
if not defined SERVER_URL set "SERVER_URL=https://pcconf.ru"
