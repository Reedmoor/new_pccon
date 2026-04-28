@echo off
chcp 1251 >nul
title Sistema upravleniya dannymi PK

REM Opredelyaem komandu Python
call get_python.bat

:menu
cls
echo ====================================================
echo         SISTEMA UPRAVLENIYA DANNYMI PK
echo ====================================================
echo.
echo Python: %PYTHON_CMD%
echo.
echo [DNS] Osnovnye operatsii:
echo.
echo   1. Parsing + avtozagruzka (rekomenduetsya)
echo   2. Import dannykh na server
echo   3. Sinhronizatsiya serverov (5001-^>5000)
echo   4. Zagruzka na udalennyy server
echo   5. Bystraya zagruzka na VASH server
echo   6. Analiz dubley
echo   7. Testirovanie Docker integratsii
echo   8. Zagruzka na pcconf.ru
echo   9. Parsing + zagruzka na pcconf.ru
echo.
echo [Dop] Dopolnitelno:
echo.
echo  10. Proverka dannykh na serverakh
echo  11. Upravlenie lokalnymi dannymi
echo  12. Zagruzka sushchestvuyushchikh dannykh
echo  13. Ruchnaya zagruzka iz starogo parsera
echo  14. Nastroyka Python okruzheniya
echo.
echo [CITILINK]:
echo.
echo  15. Parsing Citilink (vybor kategorii + zagruzka)
echo  16. Zagruzit dannyye Citilink na server
echo.
echo   0. Vyhod
echo.
echo ====================================================

set /p choice="Vybor (0-16): "

if "%choice%"=="1"  goto parse_category
if "%choice%"=="2"  goto import_data
if "%choice%"=="3"  goto sync_servers
if "%choice%"=="4"  goto upload_remote
if "%choice%"=="5"  goto quick_upload
if "%choice%"=="6"  goto analyze_duplicates
if "%choice%"=="7"  goto test_integration
if "%choice%"=="8"  goto upload_pcconf
if "%choice%"=="9"  goto parse_and_upload_pcconf
if "%choice%"=="10" goto check_data
if "%choice%"=="11" goto manage_local
if "%choice%"=="12" goto upload_existing
if "%choice%"=="13" goto upload_old_parser
if "%choice%"=="14" goto setup_python
if "%choice%"=="15" goto parse_citilink
if "%choice%"=="16" goto upload_citilink
if "%choice%"=="0"  goto exit

echo.
echo Neverno! Nazhmi lyubuyu klavishu...
pause >nul
goto menu

:parse_category
cls
echo Zapusk parsinga s avtozagruzkoy...
call parse_category.bat
goto menu

:import_data
cls
echo Zapusk importa dannykh...
call import_data.bat
goto menu

:sync_servers
cls
echo Zapusk sinhronizatsii serverov...
call sync_5001_to_5000_docker.bat
goto menu

:upload_remote
cls
echo Zagruzka dannykh na udalennyy server...
call upload_to_remote.bat
goto menu

:quick_upload
cls
echo Bystraya zagruzka na vash server...
call quick_upload.bat
goto menu

:analyze_duplicates
cls
echo Analiz dubley...
echo.
echo Vyberi tip analiza:
echo 1. Lokalnye dubli (local_data)
echo 2. Dubli na Docker servere
echo.
set /p dup_choice="Vybor (1-2): "

if "%dup_choice%"=="1" (
    "%PYTHON_CMD%" cleanup_local_data.py --analyze
    pause
) else if "%dup_choice%"=="2" (
    "%PYTHON_CMD%" cleanup_duplicates.py --analyze
    pause
) else (
    echo Neverno!
    pause
)
goto menu

:test_integration
cls
echo Testirovanie Docker integratsii...
call test_docker_integration.bat
goto menu

:upload_pcconf
cls
echo Zagruzka dannykh na pcconf.ru...
call upload_to_pcconf.bat
goto menu

:parse_and_upload_pcconf
cls
echo Parsing i zagruzka na pcconf.ru...
call parse_and_upload_to_pcconf.bat
goto menu

:check_data
cls
echo Proverka dannykh na serverakh...
"%PYTHON_CMD%" check_server_data.py
echo.
pause
goto menu

:manage_local
cls
echo Upravlenie lokalnymi dannymi...
"%PYTHON_CMD%" local_data_manager.py --stats
echo.
pause
goto menu

:upload_existing
cls
echo Zagruzka sushchestvuyushchikh dannykh...
call upload_existing_to_docker.bat
goto menu

:upload_old_parser
cls
echo Ruchnaya zagruzka dannykh iz starogo parsera...
call upload_from_old_parser.bat
goto menu

:setup_python
cls
echo Nastroyka Python okruzheniya...
call setup_python.bat
call get_python.bat
goto menu

:parse_citilink
cls
echo [CITILINK] Zapusk parsinga...
call parse_citilink.bat
goto menu

:upload_citilink
cls
echo [CITILINK] Zagruzka dannykh na server...
call upload_citilink_auto.bat
goto menu

:exit
echo.
echo Do svidaniya!
echo.
exit /b 0
