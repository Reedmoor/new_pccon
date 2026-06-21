@echo off
set "ROOT=%~dp0.."
cd /d "%ROOT%"

if not defined PYTHON_CMD call "%ROOT%\get_python.bat"

for /f "usebackq delims=" %%i in (`"%PYTHON_CMD%" "%ROOT%\lib\print_server_url.py"`) do (
    set "SERVER_URL=%%i"
    goto :done
)

set "SERVER_URL=https://pcconf.ru"
:done
