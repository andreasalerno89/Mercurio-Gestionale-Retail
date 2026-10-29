@echo off
TITLE Mercurio Gestionale Retail - Automazione Build & Installer
COLOR 0A

echo =======================================================================
echo         MERCURIO GESTIONALE RETAIL v0.2.1-alpha (Build System)
echo =======================================================================
echo.

:: 0. Assicura che esista almeno un file config_mercurio.json di base
IF NOT EXIST "config_mercurio.json" (
    echo [INFO] Creo un file config_mercurio.json predefinito...
    echo { "nome_negozio": "Mercurio Store", "piva": "", "modalita": "IP", "ip": "192.168.1.100", "porta_ip": 9100, "com": "COM1", "baudrate": 9600, "flusso": "XON/XOFF" } > config_mercurio.json
)

:: 1. Pulizia cartelle di build precedenti (Preservando la cartella Output)
echo [1/3] Pulizia vecchi file di compilazione...
IF EXIST "build" RD /S /Q "build"
IF EXIST "dist" RD /S /Q "dist"
:: Nota: La cartella Output viene preservata per non perdere i vecchi installer
IF EXIST "*.spec" DEL /F /Q "*.spec"
echo [OK] Pulizia completata.
echo.

:: 2. Compilazione con PyInstaller
echo [2/3] Generazione eseguibile con PyInstaller...
pyinstaller --noconfirm --onedir --windowed ^
    --icon="icona.ico" ^
    --add-data "config_mercurio.json;." ^
    --name "app" ^
    app.py

IF %ERRORLEVEL% NEQ 0 (
    COLOR 0C
    echo [ERRORE] La compilazione PyInstaller e' fallita.
    pause
    exit /b %ERRORLEVEL%
)
echo [OK] Eseguibile PyInstaller generato con successo in dist\app.
echo.

:: 3. Compilazione Installer con Inno Setup (Cerca Inno Setup 6)
echo [3/3] Generazione pacchetto di installazione con Inno Setup...
SET "INNO_PATH="

IF EXIST "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    SET "INNO_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
) ELSE IF EXIST "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    SET "INNO_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"
)

IF DEFINED INNO_PATH (
    "%INNO_PATH%" "setup_script.iss"
    IF %ERRORLEVEL% EQU 0 (
        COLOR 0A
        echo.
        echo =======================================================================
        echo [SUCCESSO] BUILD E INSTALLER GENERATI CON SUCCESSO!
        echo L'installer e' pronto nella cartella Output\
        echo =======================================================================
    ) ELSE (
        COLOR 0E
        echo [ATTENZIONE] Errore durante la compilazione con Inno Setup.
    )
) ELSE (
    COLOR 0E
    echo [INFO] Inno Setup 6 (ISCC.exe) non trovato nei percorsi standard.
    echo Puoi aprire 'setup_script.iss' direttamente dall'interfaccia di Inno Setup.
)

echo.
pause