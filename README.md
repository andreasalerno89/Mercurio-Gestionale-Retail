# Mercurio Gestionale Retail (v0.2.1-alpha)

Software gestionale cross-platform sviluppato in Python, progettato specificamente per la gestione di punti vendita e attività commerciali (moduli POS ed ERP integrati).

## 🚀 Novità della versione v0.2.1-alpha

- **Tastierino Numerico POS**: Reintegrata la pulsantiera numerica touch/click (`0-9`, `.`, `C`) nel modulo POS (`pos_module.py`) per consentire la battuta rapida e precisa degli importi.
- **Vendita Libera a Reparto**: Introdotta la possibilità di assegnare l'importo digitato sul tastierino a un reparto specifico (es. *Generico*, *Alimentari*, *Abbigliamento*) per gli articoli non censiti a catalogo.
- **Modulo Contanti e Calcolo Resto**: 
  - Finestra di dialogo dedicata per l'incasso in contanti con richiesta dell'importo consegnato dal cliente.
  - Calcolo automatico e immediato del resto a schermo con riscontro visivo chiaro per l'operatore di cassa.
  - Registrazione dei campi `importo_pagato` e `resto` all'interno della tabella `movimenti_banco` del database SQLite per la quadratura di cassa.
- **Deployment e Build**: Aggiornati gli script di compilazione con PyInstaller (`build_exe.bat`) e l'installer per Windows (`setup_script.iss`).

---

## 🛠️ Architettura del Progetto

Il software adotta una struttura modulare basata su Python e Tkinter/CustomTkinter, con persistenza dati su database SQLite:

- `app.py`: Dashboard principale ed entry point dell'applicazione.
- `pos_module.py`: Modulo cassa avanzato, gestione scontrino e tastierino numerico.
- `warehouse_module.py`: Gestione magazzino, carichi e scarichi articoli.
- `clients_module.py`: Anagrafica clienti e gestione Fidelity.
- `settings_module.py` / `rt_driver.py`: Configurazione registratore di cassa e stampanti fiscali.
- `database.py`: Gestione delle connessioni e delle tabelle SQLite.

---

## 📦 Requisiti e Installazione

### Requisiti di sistema
- Python 3.10 o superiore.
- Librerie dipendenti (installabili tramite `requirements.txt`).

### Avvio da sorgente
1. Clona o scarica la repository.
2. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt