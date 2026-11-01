@echo off
SETLOCAL EnableDelayedExpansion

:: Spostati automaticamente nella cartella in cui si trova questo file batch
cd /d "%~dp0"

echo =======================================================================
echo     MERCURIO GESTIONALE RETAIL v0.3.0 Alpha (Build ^& Setup Automation)
echo =======================================================================
echo.

:: [0/5] Verifiche preliminari
echo [0/5] Verifica prerequisiti...

python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERRORE] Python non trovato nel PATH. Installalo o attivalo prima di procedere.
    goto error
)

IF NOT EXIST "icona.ico" (
    echo [ERRORE] File "icona.ico" non trovato nella cartella radice del progetto.
    goto error
)

IF NOT EXIST "setup_script.iss" (
    echo [ERRORE] File "setup_script.iss" non trovato. Necessario per Inno Setup.
    goto error
)

IF NOT EXIST "src\main.py" (
    echo [ERRORE] File "src\main.py" non trovato. Sei nella cartella corretta?
    goto error
)
echo [OK] Prerequisiti verificati.
echo.

:: [1/5] Pulizia vecchi file di compilazione
echo [1/5] Pulizia vecchi file di compilazione...
IF EXIST "build" rmdir /s /q "build"
IF EXIST "dist" rmdir /s /q "dist"
del /f /q *.spec 2>nul
echo [OK] Pulizia completata.
echo.

:: [2/5] Generazione eseguibile con PyInstaller
echo [2/5] Generazione eseguibile con PyInstaller...
python -m PyInstaller --noconfirm --clean --onedir --windowed ^
    --name "MercurioGestionale" ^
    --icon "icona.ico" ^
    --paths "src" ^
    "src/main.py"

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRORE] La compilazione PyInstaller e' fallita.
    goto error
)
echo [OK] Eseguibile generato con successo nella cartella dist\.
echo.

:: [3/5] Compilazione Installer con Inno Setup
echo [3/5] Compilazione del pacchetto di installazione con Inno Setup...

SET "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
IF NOT EXIST "%ISCC_PATH%" SET "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"

IF NOT EXIST "%ISCC_PATH%" (
    echo [ERRORE] Impossibile trovare il compilatore di Inno Setup (ISCC.exe).
    echo         Installa Inno Setup 6 da https://jrsoftware.org/isdl.php
    goto error
)

"%ISCC_PATH%" "setup_script.iss"

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRORE] La compilazione di Inno Setup e' fallita.
    goto error
)
echo [OK] Installer creato con successo nella cartella Output\.
echo.

:: [4/5] Completamento
echo =======================================================================
echo     PROCESSO COMPLETATO CON SUCCESSO!
echo     L'installer e' pronto nella cartella Output\
echo =======================================================================
goto end

:error
echo.
echo [ERRORE] Il processo di build e' stato interrotto a causa di un errore.
pause
exit /b %ERRORLEVEL%

:end
echo.
pause