@echo off
REM Opredelenie komandy Python -> PYTHON_CMD

if exist "python_cmd.txt" (
    set /p "PYTHON_CMD=" < "python_cmd.txt"
    if defined PYTHON_CMD (
        "%PYTHON_CMD%" --version >nul 2>&1
        if not errorlevel 1 goto :eof
    )
)

if exist "venv\Scripts\python.exe" (
    set "PYTHON_CMD=%CD%\venv\Scripts\python.exe"
    goto :eof
)

where python >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    goto :eof
)

where py >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
    goto :eof
)

set "PYTHON_CMD=python"
goto :eof
