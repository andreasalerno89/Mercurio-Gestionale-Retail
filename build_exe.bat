@echo off
echo ========================================================
echo  Compilazione Mercurio Gestionale ERP in corso...
echo ========================================================

pip install pyinstaller customtkinter pyserial pillow

:: Aggiunto il parametro --icon="icona.ico" per incorporare l'icona nel file .exe
pyinstaller --noconfirm --onedir --windowed --name "Mercurio Gestionale ERP" --icon="icona.ico" --collect-all customtkinter app.py

echo.
echo ========================================================
echo  Compilazione completata!
echo  L'eseguibile si trova nella cartella: dist\Mercurio Gestionale ERP\
echo ========================================================
pause