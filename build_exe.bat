@echo off
SETLOCAL EnableDelayedExpansion

:: Mercurio Gestionale Retail
:: Copyright (C) 2026 Andrea Salerno
::
:: This program is free software: you can redistribute it and/or modify
:: it under the terms of the GNU General Public License as published by
:: the Free Software Foundation, either version 3 of the License, or
:: (at your option) any later version.
::
:: This program is distributed in the hope that it will be useful,
:: but WITHOUT ANY WARRANTY; without even the implied warranty of
:: MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
:: GNU General Public License for more details.
::
:: You should have received a copy of the GNU General Public License
:: along with this program.  If not, see <https://www.gnu.org/licenses/>.

:: Spostati automaticamente nella cartella in cui si trova questo file batch
cd /d "%~dp0"

echo =================================================================
echo     MERCURIO GESTIONALE RETAIL v0.3.2-alpha (Build ^& Setup Automation)
echo =================================================================
echo.

:: [0/4] Verifiche preliminari
echo [0/4] Verifica prerequisiti...

python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERRORE] Python non trovato nel PATH. Installalo o attivalo prima di procedere.
    goto error
)

python -m PyInstaller --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERRORE] PyInstaller non trovato. Attiva l'ambiente virtuale con:
    echo         .venv\Scripts\activate.bat
    echo         oppure installalo con: python -m pip install pyinstaller
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

:: [1/4] Pulizia cartelle di build precedenti
echo [1/4] Pulizia cartelle di build...
IF EXIST "build" rmdir /s /q "build"
IF EXIST "dist" rmdir /s /q "dist"
del /f /q *.spec 2>nul
IF NOT EXIST "Output" mkdir "Output"
echo [OK] Pulizia completata.
echo.

:: [2/4] Generazione eseguibile con PyInstaller
echo [2/4] Generazione eseguibile con PyInstaller...
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

:: [3/4] Compilazione Installer con Inno Setup
echo [3/4] Compilazione del pacchetto di installazione con Inno Setup...

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

:: [4/4] Completamento
echo =================================================================
echo     PROCESSO COMPLETATO CON SUCCESSO!
echo     L'installer e' pronto in: Output\mercurio_gestionale_retail-v0.3.2-alpha-win64-setup.exe
echo =================================================================
goto end

:error
echo.
echo [ERRORE] Il processo di build e' stato interrotto a causa di un errore.
pause
exit /b %ERRORLEVEL%

:end
echo.
pause