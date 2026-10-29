# 🛒 Mercurio Gestionale Retail (v0.2.1-alpha)

**Mercurio Gestionale Retail** è un software gestionale moderno, leggero e modulare sviluppato in Python, pensato per ottimizzare e semplificare le attività di vendita al banco, gestione del magazzino, anagrafica clienti e fatturazione per esercizi commerciali e punti vendita.

L'interfaccia grafica è realizzata interamente con **CustomTkinter**, offrendo un design moderno, pulito e nativo in stile Dark/Light mode.

---

## 🚀 Architettura Modulare

Il progetto adotta una struttura modulare per facilitare la manutenzione, l'estensibilità e la scalabilità delle funzioni:

*   **`app.py`** - File principale di avvio e gestione del layout di navigazione (Sidebar / Router dei moduli).
*   **`pos_module.py`** - Modulo Punto Vendita (Cassa, carrello, scontrini, calcolo del resto e gestione transazioni).
*   **`warehouse_module.py`** - Gestione Magazzino (Carico/scarico merci, giacenze, prezzi e ricerca articoli).
*   **`clients_module.py`** - Anagrafica Clienti & Fidelity (Gestione tessere, storico acquisti e dati anagrafici).
*   **`documents_module.py`** - Gestione Documenti (Emissione scontrini, fatture e documenti commerciali).
*   **`settings_module.py`** - Impostazioni di Sistema e configurazione parametri negozio.
*   **`database.py`** - Livello di astrazione e gestione del database locale.
*   **`registratore_telematico.py`** - Integrazione e comunicazione con i registratori telematici per la trasmissione dei corrispettivi.

---

## 🛠️ Requisiti di Sistema e Dipendenze

Per eseguire o compilare il progetto in locale, assicurati di avere installato:
*   **Python 3.10+**
*   Librerie Python principali:
    *   `customtkinter`
    *   Altre dipendenze specificate nel progetto.
*   **PyInstaller** (per la generazione dell'eseguibile standalone).
*   **Inno Setup 6** (opzionale, per la compilazione del pacchetto di installazione Windows).

---

## ⚙️ Compilazione Automatica (Build System)

Il progetto include uno script batch automatizzato (`build_exe.bat`) che gestisce la pulizia della cache, la compilazione tramite **PyInstaller** (generando la cartella `dist\app`) e la preparazione dei file di configurazione (`config_mercurio.json`).

Per creare l'eseguibile in autonomia:
1. Avvia il prompt dei comandi nella cartella del progetto.
2. Esegui lo script:
   ```cmd
   build_exe.bat
L'eseguibile e le risorse saranno pronti all'interno della cartella dist\app\.

Per generare il pacchetto di installazione definitivo (Setup_Mercurio_Retail_v0.2.1-alpha.exe), apri il file setup_script.iss con Inno Setup Compiler e premi F9.

📦 Struttura del Repository
Plaintext
├── app.py                     # Entry point principale
├── pos_module.py              # Modulo Punto Vendita / Cassa
├── warehouse_module.py        # Modulo Gestione Magazzino
├── clients_module.py          # Modulo Anagrafica Clienti
├── documents_module.py        # Modulo Gestione Documenti
├── settings_module.py         # Modulo Impostazioni
├── database.py                # Connettore e gestione Database
├── registratore_telematico.py # Interfaccia RT
├── config_mercurio.json       # Configurazione locale predefinita
├── build_exe.bat              # Script di automazione build
├── setup_script.iss           # Script Inno Setup per l'Installer
└── README.md                  # Documentazione del progetto
👤 Autore & Licenza
Sviluppatore: Andrea Salerno

Versione: 0.2.1-alpha