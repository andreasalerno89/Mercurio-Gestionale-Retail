# Mercurio Gestionale Retail Enterprise

Software gestionale open-source per il commercio al dettaglio: Touch-screen POS, Gestione Magazzino avanzata e Fiscalità Italiana RT/SDI.

Versione: v0.3.0 Alpha
Licenza: GNU General Public License v3.0
Python: 3.9+
GUI: Tkinter
Database: SQLite3
Sistema Operativo: Windows 10 / 11 (64-bit)

---

## Caratteristiche Principali

- Dashboard & Analytics: monitoraggio in tempo reale del fatturato, incassi suddivisi per Contanti/POS e analisi scontrini con filtri temporali dinamici (Mese/Anno).
- Magazzino Avanzato:
  - Unità di misura parametriche (pz, kg, mt, lt).
  - Gestione prezzi netti e ivati con aliquota IVA parametrica (22% / 10% / 5% / 4% / Esente).
  - Gestione pesi lordo/netto, percorso immagine del prodotto e controllo scorte minime.
  - Operazioni di carico, scarico e rettifica manuale libera.
  - Importazione ed esportazione avanzata in formato CSV.
- Cassa POS & Fidelity:
  - Interfaccia touch-screen rapida e intuitiva per la vendita al banco.
  - Gestione clienti con associazione Fidelity Card e calcolo dinamico di punti e sconti.
  - Pagamento in contanti (con calcolo resto e conferma) o POS.
- Documenti Fiscali & RT:
  - Registrazione scontrini con tracciamento del metodo di pagamento (CONTANTI / POS).
  - Emissione scontrini di annullo (Storno RT) con rettifica automatica dei corrispettivi.
  - Predisposizione per la fatturazione elettronica: creazione di documenti FATTURA con stato PRONTO_SDI e generazione di copie di cortesia.
  - Configurazione dei parametri di connessione al Registratore Telematico (IP/TCP o Seriale XON/XOFF). L'invio effettivo dei comandi RT è previsto per la v0.4.0.
- Corrispettivi & Chiusura Z: chiusura giornaliera con ripartizione Contanti/POS/Altro e calcolo IVA aggregato. Gli scontrini annullati sono esclusi dal conteggio e compensati dallo scontrino di annullo.
- Backup Integrato: copia di sicurezza manuale del database SQLite nella cartella utente (Documents/MercurioBackup).

---

## Requisiti di Sistema & Tecnologie

- Linguaggio: Python 3.9+
- Interfaccia Grafica: Tkinter (libreria standard)
- Database: SQLite3
- Sistema Operativo: Windows 10 / 11 (ottimizzato per 64-bit)
- Dipendenze esterne: nessuna. Solo standard library.
- Dipendenze di build (opzionali): PyInstaller, Inno Setup 6.

---

## Installazione & Avvio

Utente finale:
Scarica l'installer (Output\mercurio_gestionale_retail_v0.3.0-Alpha-Win64-setup.exe) dalla release e installalo. Non servono prerequisiti: l'app è autocontenuta.
Il database viene creato al primo avvio in: %LOCALAPPDATA%\MercurioGestionale\gestionale.db
Questo garantisce che l'app funzioni anche installata in C:\Program Files\ senza richiedere privilegi amministrativi.

Sviluppo:
git clone https://github.com/andreasalerno89/Mercurio-Gestionale-Retail.git
cd Mercurio-Gestionale-Retail
python src/main.py
In sviluppo il database viene creato nella root del progetto (gestionale.db). Non è necessaria alcuna installazione di dipendenze.

Build dell'installer:
build.bat
Lo script automatizza: pulizia cartelle -> PyInstaller -> Inno Setup. L'output finale è in Output\.

---

## Struttura del Progetto

Gestionale Mercurio Retail/
├── CHANGELOG.md
├── LICENSE
├── README.md
├── requirements.txt             (nessuna dipendenza runtime)
├── requirements-dev.txt         (solo per la build: PyInstaller)
├── icona.ico
├── build.bat                    (script di automazione build e Inno Setup)
├── setup_script.iss             (script di configurazione per Inno Setup)
├── gestionale.db                (DB in sviluppo; in %LOCALAPPDATA% nell'exe)
├── mercurio.log                 (log applicativo, generato al primo avvio)
└── src/
    ├── config.py                (configurazione aziendale, RT e regole backup)
    ├── database.py              (schema SQLite, connessioni e migrazioni)
    ├── main.py                  (entry point dell'applicazione)
    └── modules/
        ├── clienti.py           (anagrafica clienti e Fidelity Card)
        ├── corrispettivi.py     (chiusure di cassa Z)
        ├── documenti.py         (gestione documenti, fatture e annulli RT)
        ├── fornitori.py         (anagrafica fornitori e modulo riordino)
        ├── impostazioni.py      (pannello di configurazione globale)
        ├── magazzino.py         (gestione articoli, giacenze e CSV)
        └── pos.py               (interfaccia Cassa Touch/POS)

---

## Stato del Progetto

v0.3.0 Alpha - Fase di stabilizzazione. I flussi principali (POS -> Documenti -> Corrispettivi) sono allineati e testati. Le funzionalità di integrazione RT e Fatturazione Elettronica SDI sono predisposte ma non ancora operative: vedi CHANGELOG.md per la roadmap.

Roadmap v0.4.0:
- Tabella documenti_righe per la ripartizione IVA per aliquota.
- Contatore progressivo scontrini/fatture per anno.
- Unificazione colonne soglia_minima / scorta_minima.
- Integrazione RT (comandi IP/TCP e Seriale XON/XOFF).
- Generazione XML FatturaPA e predisposizione invio SDI.
- Backup automatico periodico.

---

## Licenza e Copyright

Copyright (C) 2026 Andrea Salerno
https://github.com/andreasalerno89/Mercurio-Gestionale-Retail

Questo programma è software libero: puoi ridistribuirlo e/o modificarlo secondo i termini della GNU General Public License come pubblicata dalla Free Software Foundation, versione 3 della Licenza, o (a tua scelta) qualsiasi versione successiva.

Questo programma è distribuito nella speranza che sia utile, ma SENZA ALCUNA GARANZIA; senza nemmeno la garanzia implicita di COMMERCIABILITÀ o IDONEITÀ PER UN PARTICOLARE SCOPO. Vedi la GNU General Public License per maggiori dettagli.

Dovresti aver ricevuto una copia della GNU General Public License insieme a questo programma. Se così non fosse, vedi https://www.gnu.org/licenses/.

Il testo completo della licenza è nel file LICENSE.