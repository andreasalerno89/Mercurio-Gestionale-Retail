# Changelog

Tutti i cambiamenti rilevanti a questo progetto saranno documentati in questo file.

Il formato si basa su [Keep a Changelog](https://keepachangelog.com/it/1.0.0/)
e questo progetto rispetta il [Semantic Versioning](https://semver.org/lang/it/).

---

## [0.2.1-alpha] - 2026-10-29

### ➕ Aggiunto
- **Tastierino Numerico POS**: Reintegrata la pulsantiera numerica touch/click (`0-9`, `.`, `C`) nel modulo POS (`pos_module.py`) per la battuta rapida degli importi.
- **Vendita Libera a Reparto**: Possibilità di assegnare l'importo digitato sul tastierino a un reparto specifico (es. *Generico*, *Alimentari*, *Abbigliamento*) per gli articoli non censiti a catalogo.
- **Modulo Contanti e Calcolo Resto**:
  - Finestra di dialogo dedicata per l'incasso in contanti con richiesta dell'importo consegnato dal cliente.
  - Calcolo automatico e immediato del resto a schermo con riscontro visivo chiaro per l'operatore di cassa.
  - Registrazione dei campi `importo_pagato` e `resto` nella tabella `movimenti_banco` del database SQLite per la quadratura di cassa.

### 🔄 Modificato
- Aggiornati gli script di deployment e build:
  - `build_exe.bat` per la compilazione automatica con PyInstaller puntando al pacchetto `MercurioRetail_v0.2.1-alpha`.
  - `setup_script.iss` per la generazione dell'installer Windows `Setup_MercurioRetail_v0.2.1-alpha.exe`.

---

## [0.2.0-alpha] - 2026-10-29

### ➕ Aggiunto
- **Architettura Modulare ERP/POS**: Struttura dell'applicazione riorganizzata in moduli trasversali integrati nella dashboard principale (`app.py`).
- **Modulo POS Avanzato**: Display LCD in stile cassa, gestione scontrino dinamico e scansione rapida barcode/EAN con feedback acustico.
- **Anagrafica Clienti & Fidelity**: Gestione clienti con tracciamento storico acquisti, accumulo punti e fidelity card.
- **Modulo Documenti & Movimenti**: Registro storico degli scontrini emessi con dettaglio riga e modalità di pagamento.
- **Ristrutturazione Database**: Schema SQLite espanso per includere clienti, storico movimenti di banco e log di audit.
- **Build Pipeline & Installer**: Creazione dello script batch di build (`build_exe.bat`) e dello script Inno Setup (`setup_script.iss`) per pacchettizzare la versione eseguibile Windows.

---

## [0.1.0-alpha] - 2026-10-29

### ➕ Aggiunto
- **Prototipo Iniziale**: Prima bozza dell'interfaccia grafica sviluppata in Python con la libreria `customtkinter`.
- **Database SQLite**: Struttura iniziale della base dati locale per la gestione dell'anagrafica articoli e delle giacenze di magazzino.
- **Modulo Magazzino**: Funzionalità base per l'inserimento, la modifica e la ricerca di prodotti e reparti.
- **Setup iniziale Git**: Creazione della repository GitHub, licenza open-source e configurazione del file `.gitignore`.

---