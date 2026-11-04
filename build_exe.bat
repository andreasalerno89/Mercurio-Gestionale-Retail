@echo off
:: Mercurio Gestionale Retail
:: Copyright (C) 2026 Andrea Salerno
::
:: This program is free software: you can redistribute it and/or modify
:: it under the terms of the GNU General Public License as published by
:: the Free Software Foundation, either version 3 of the License, or
:: (at your option) any later version.

echo =================================================================
echo     MERCURIO GESTIONALE RETAIL v0.3.1-alpha (Build ^& Setup Automation)
echo =================================================================

:: 1. Pulizia cartelle di build precedenti
echo Pulizia cartelle di build...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist Output mkdir Output

:: 2. Esecuzione PyInstaller
echo Avvio PyInstaller...
python -m PyInstaller --noconfirm --clean --onedir --windowed ^
    --name "MercurioGestionale" ^
    --icon "icona.ico" ^
    --paths "src" ^
    "src/main.py"

if %errorlevel% neq 0 (
    echo [ERRORE] PyInstaller fallito!
    pause
    exit /b %errorlevel%
)

:: 3. Esecuzione Inno Setup
echo Avvio Inno Setup...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup_script.iss

if %errorlevel% neq 0 (
    echo [ERRORE] Inno Setup fallito!
    pause
    exit /b %errorlevel%
)

echo.
echo =================================================================
echo     Build e Setup completati con successo!
echo     File disponibile in: Output\mercurio_gestionale_retail-v0.3.1-alpha-win64-setup.exe
echo =================================================================
pause
