# Changelog

Tutte le modifiche rilevanti a questo progetto sono documentate in questo file.

Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.1.0/) e il progetto aderisce al [Semantic Versioning](https://semver.org/lang/it/).

---

## [v0.3.2-alpha] - 2026-11-11

### 🚀 Milestone 2 — Gestione Documenti (Parte 1)

#### Schema database
- **Aggiunte colonne `sconto_riga`, `tipo_sconto_riga`** a `documenti_righe`: per gestire lo sconto applicato alla singola riga (percentuale o valore).
- **Aggiunte colonne `motivo_annullo`, `riferimento_esterno`** a `documenti`: per motivare annulli/note di credito e collegare documenti esterni.
- **Aggiunta tabella `ddt_dati`**: per i dati di trasporto dei DDT (vettore, indirizzo destinatario, causale, data ritiro, aspetto esteriore).
- **Aggiornamento `database.py`**: migrazioni automatiche per le nuove colonne e tabelle.

#### POS (Cassa)
- **Popolamento `documenti_righe`**: alla conclusione della vendita, le righe del carrello vengono salvate in `documenti_righe` con articolo, quantità, prezzo, aliquota, totale, sconto.
- **Sconti totali esclusi dalle righe**: gli sconti (`SCONTO-TOT`) non generano righe di dettaglio.

#### Documenti Fiscali
- **Fattura da scontrino con trasferimento righe**: la fattura creata da uno scontrino ora copia automaticamente tutte le righe in `documenti_righe`.
- **Numerazione progressiva fatture**: `FAT-2026-0001` da tabella `contatori` (invece di `FAT-2026-{id}`).
- **Controllo duplicati**: impedisce di fatturare due volte lo stesso scontrino (check su `scontrino_origine_id`).
- **Note di credito**: nuova finestra `NotaCreditoDialog` con selezione righe, motivo, importi negativi, carico automatico a magazzino (`RESO`).
- **Numerazione progressiva note di credito**: `NC-2026-0001`.
- **DDT (Documento di Trasporto)**: nuova finestra `DDTPage` con destinatario, vettore, indirizzo, causale trasporto, data ritiro, aspetto esteriore, selezione articoli.
- **Numerazione progressiva DDT**: `DDT-2026-0001`.
- **Copia di cortesia HTML**: sostituito il CSV con un file HTML stampabile in PDF, con intestazione aziendale, dati cliente, tabella righe, riepilogo totali, badge "COPIA DI CORTESIA".

#### UI e packaging
- **Aggiornamento versione a `v0.3.2 Alpha`** in titolo finestra, dashboard e log di avvio.
- **Rimosso doppio pulsante "Genera Fattura da Scontrino"**.
- **README.md e CHANGELOG.md aggiornati** per riflettere le nuove funzionalità.

---

## [v0.3.1-alpha] - 2026-11-04

### 🚀 Milestone 1 — Fondamenta Dati

#### Schema database
- **Aggiunta tabella `contatori`**: per la gestione della numerazione progressiva dei documenti (Scontrini, Fatture, DDT, ecc.) su base annua.
- **Aggiunta tabella `documenti_righe`**: per gestire il dettaglio delle righe all'interno di ogni documento, consentendo una corretta ripartizione dell'IVA per aliquota.
- **Aggiunte colonne `scontrino_origine_id`, `documento_origine_id`, `tipo_soggetto`** a `documenti`: per collegare fatture, annulli, note di credito e DDT al documento originale, e per distinguere cliente/occasionale/fidelity.
- **Aggiunta colonna `rt_protocollo`** a `impostazioni_azienda`: predisposizione per i protocolli RT (`XON_XOFF_SERIALE`, `XON_XOFF_TCP`, `EPSON_SOAP`, `RCH_NATIVO`, `CUSTOM_NATIVO`, `3I_NATIVO`, `ESCPOS`).
- **Aggiornamento `database.py`**: implementata logica di inizializzazione e migrazione per le nuove tabelle e colonne.

#### Anagrafiche
- **Separazione indirizzo/civico e cap/località** nei form clienti e fornitori.
- **Fix `DB_FIELDS` in `clienti.py`**: rimossi duplicati `localita`/`provincia` che causavano disallineamento nella SELECT.
- **Ricerca testuale nella tab Fornitori**: barra di ricerca per nome, P.IVA o PEC, analoga a quella dei clienti.
- **Form fornitore**: aggiunti campi `civico` e `cap` separati, altezza form aumentata per ospitare i 14 campi.

#### Impostazioni
- **Campo `rt_protocollo`**: aggiunto menu a tendina nella tab RT con i 7 protocolli supportati (predisposizione, invio comandi reali previsto per v0.4.0).

#### UI e packaging
- **Aggiornamento versione a `v0.3.1 Alpha`** in titolo finestra, dashboard e log di avvio.
- **Icona finestra**: aggiunto `iconbitmap` in `main.py` per mostrare `icona.ico` nella barra del titolo e nella taskbar.
- **Rimozione "Enterprise"** dal nome software in dashboard, README e `requirements.txt`.
- **Aggiunti `requirements.txt`** (nessuna dipendenza runtime) e **`requirements-dev.txt`** (solo `pyinstaller>=6.0`).
- **`.gitignore` aggiornato**: esclusi `.clinerules` e `icona.jpg`.

#### Configurazione
- **`config.py`**: aggiunto `rt_protocollo` nella lista `fields` di `save_company_data`.

---

## [v0.3.0 Alpha] - 2026-11-01

Fase di stabilizzazione: risoluzione bug bloccanti, allineamento schema database, coerenza fiscale tra moduli, packaging per la distribuzione.

### 🐛 Corretto

#### Architettura & avvio
- **Fix `ModuleNotFoundError`**: rimossi tutti gli import con prefisso `src.` all'interno di `src/modules/` e `src/config.py`. Ora tutti i moduli interni usano import diretti (`from database import ...`) per garantire compatibilità con l'esecuzione da sorgente.
- **Fix `NameError: current_dir`** con VS Code Code Runner: identificato il problema legato ai file temporanei (`tempCodeRunnerFile.py`) e stabilizzato l'avvio tramite terminale integrato con `python src/main.py`.
- **Fix "limbo" del SetupWizard**: il wizard di primo avvio non rilasciava correttamente il `grab_set()` prima di chiamare `destroy()`, causando il blocco dell'event loop. Aggiunto `grab_release()` esplicito e rimandata la costruzione dell'interfaccia con `after_idle()`.
- **Fix popup a cascata all'avvio**: `get_company_data()` mascherava tutti gli errori restituendo `None`, causando la riapertura del wizard anche quando il problema era un DB corrotto o lockato. Ora `None` viene restituito solo se la tabella `impostazioni_azienda` non esiste; tutti gli altri errori vengono rilanciati e loggati.
- **Fix `grab_set` su finestre modali**: nei form di `clienti.py`, `fornitori.py`, `magazzino.py` il `grab_set()` viene ora chiamato dopo `wait_visibility()`, evitando grab "fantasma" su widget non ancora visibili.
- **Aggiunto handler `WM_DELETE_WINDOW`** su `MercurioApp` per chiusura pulita dell'app e flush del log.

#### Schema database e migrazioni
- **Fix `no such column: iban`, `scorta_minima`, `fornitore_id`, `metodo_pagamento`**: aggiunta una logica robusta di migrazione automatica con `PRAGMA table_info` + `ALTER TABLE` in `database.py` per aggiornare DB esistenti senza perdita di dati.
- **Aggiunte 3 colonne mancanti a `fornitori`**: `codice_univoco` (SDI), `istituto_bancario`, `metodo_pagamento`. Necessarie per il corretto funzionamento di `fornitori.py`.
- **Aggiunte `iva_4` ed `esente` in migrazione** per `corrispettivi_giornalieri`, coerentemente con il `CREATE TABLE`.
- **Fix `DB_PATH`** con `os.path.abspath(os.path.normpath(...))`: path assoluto e normalizzato, indipendente dalla CWD.
- **Fix `PRAGMA foreign_keys = ON`** in `get_connection()`: coerenza referenziale tra `fornitore_id`, `articolo_id`, `cliente_id`.
- **Aggiunto `DB_TIMEOUT = 10.0`** in `get_connection()`: evita "database is locked" in caso di concorrenza.
- **Fix path `%LOCALAPPDATA%` per l'exe**: `database.py` ora distingue `sys.frozen` e usa `%LOCALAPPDATA%\MercurioGestionale\gestionale.db` quando compilato con PyInstaller, evitando crash per permessi in `C:\Program Files\`.

#### Configurazione aziendale
- **Fix `save_company_data` non atomica**: aggiunto `try/finally` con `conn.close()` garantito e `conn.rollback()` esplicito in caso di errore.
- **Fix sovrascrittura dei campi RT/Fidelity**: `save_company_data` ora aggiorna solo i campi effettivamente presenti nel `data`, preservando i default della tabella per i campi non forniti dal wizard.
- **Fix `esegui_backup_sistema`**: usa lo stesso `DB_PATH` di `database.py`, garantendo backup del file effettivamente usato dall'app.
- **Aggiunto logging** su tutte le operazioni critiche (salvataggio config, backup, migrazioni).

#### Magazzino
- **Fix `apri_finestra_articolo`**: la SELECT non viene più costruita da `entries.keys()` (fragile) ma da una lista esplicita `FIELDS_FORM` allineata al DB.
- **Rimosso blocco su `prezzo_vendita == 0`**: ora permette articoli omaggio/campione, blocca solo prezzi negativi.
- **Fix rettifica magazzino**: `RETTIFICA` accetta anche `0` (azzeramento giacenza) e rifiuta quantità negative con messaggio chiaro.
- **Fix import CSV**: validazione riga per riga con conteggio degli scarti, controllo duplicati su `codice_interno` (UNIQUE), riepilogo finale dei motivi di scarto.
- **Fix `filtra_articoli`**: sostituito `except: pass` con `log.exception`.
- **Fix gestione `None`** in giacenza/soglia nella visualizzazione tabella.

#### Clienti
- **Fix `carica_dati`** in `ClienteForm`: SELECT basata su `DB_FIELDS` esplicito, non su `entries.keys()`.
- **Fix `punti_fidelity` in modifica**: in modalità modifica, i punti vengono esclusi dall'UPDATE se non modificati dall'utente (evita race condition con accrediti dal POS).
- **Fix validazione `punti_fidelity`**: messaggio chiaro se l'utente scrive un valore non numerico.
- **Fix `apri_form_modifica` da doppio clic**: ignora silenziosamente il doppio clic su area vuota, evitando popup inutili.
- **Fix `filtra_clienti`**: usato `COALESCE` per gestire `codice_fiscale`/`partita_iva` NULL.
- **Fix `except: pass`** in `filtra_clienti`: sostituito con `log.exception`.

#### Fornitori
- **Fix `carica_fornitori`**: rimosso `metodo_pagamento` non presente nel DB (ora presente dopo la patch).
- **Fix `elimina_fornitore`**: check preliminare su `articoli.fornitore_id` prima del DELETE, per evitare `FOREIGN KEY constraint failed` con messaggio tecnico.
- **Fix modulo riordino**: `COALESCE(scorta_minima, soglia_minima, 0)` per essere robusto qualunque sia la colonna popolata da `magazzino.py`.
- **Fix `except: pass`** in `carica_articoli_sotto_scorta`: sostituito con `log.exception`.
- **Fix `import csv`**: spostato in cima al modulo.

#### POS (Cassa)
- **Fix fiscale bloccante**: `pagamento` e `metodo_pagamento` non venivano scritti nella INSERT dello scontrino. Risultato: la chiusura Z vedeva tutti gli scontrini come "pagamento non classificato" e li buttava in "altro". Ora vengono salvati esattamente come `'CONTANTI'` o `'POS'`.
- **Fix calcolo `imponibile`**: non più `totale / 1.22` fisso, ma calcolato sull'IVA reale di ciascun item del carrello (`_calcola_imponibile`).
- **Fix IVA degli sconti totali**: gli sconti (`ean == "SCONTO-TOT"`) sono esclusi dal calcolo IVA (non hanno aliquota propria).
- **Fix `aliquota_iva`**: letta correttamente da `articoli` quando si aggiunge al carrello, non più hardcoded a 22%.
- **Fix controllo giacenza**: sia all'aggiunta al carrello sia prima di concludere la vendita, con messaggi chiari.
- **Fix `stato_xml`**: ora `'EMESSO'` invece di `'GENERATO'`, coerente con gli altri moduli.
- **Fix numerazione scontrino**: timestamp con microsecondi + controllo duplicati per evitare collisioni su scontrini emessi nello stesso secondo.
- **Fix `_estrai_cliente_id`**: verifica `isdigit()` prima del cast a int, evitando crash se l'utente scrive testo libero nella combo.
- **Fix `import winsound`**: protetto con `HAS_WINSOUND` per non far crashare il modulo su Linux/macOS.
- **Fix `except: pass`** in `aggiorna_combos_clienti` e `cerca_cliente_rapido`: sostituiti con `log.exception`.

#### Documenti fiscali
- **Fix annullo scontrino**: controllo `stato_xml == 'ANNULLATO_RT'` per evitare annulli doppi (che genererebbero storni negativi multipli).
- **Fix fattura da scontrino**: controlli di validità (scontrino annullato, fattura già emessa, imponibile NULL) prima della INSERT.
- **Fix duplicati numero fattura**: controllo preliminare su `numero` prima della INSERT.
- **Fix `datetime('now')`**: sostituito con `datetime('now','localtime')` per rispettare il fuso orario italiano (fondamentale per la datazione fiscale).
- **Fix warning fattura su scontrino annullato**: chiede conferma esplicita all'utente (l'annullo RT non sostituisce una nota di credito).
- **Fix `except: pass`** in `genera_fattura_da_scontrino`: sostituito con `log.exception`.

#### Corrispettivi (Chiusura Z)
- **Fix inclusione annulli**: la chiusura Z ora include gli `ANNULLO` (importi negativi) nel totale e nella ripartizione contanti/POS, ed esclude gli `SCONTRINO` con `stato_xml = 'ANNULLATO_RT'` (già compensati).
- **Fix contanti/POS reali**: la ripartizione non è più inventata (70%/30%) ma letta dai `documenti` con `SUM(CASE WHEN pagamento = 'CONTANTI' ...)`.
- **Fix conteggio scontrini**: `num_scontrini` conta solo scontrini validi (non annullati); `num_annulli` viene tracciato separatamente.
- **Fix IVA**: warning se ci sono scontrini con `imponibile IS NULL` (dati legacy).
- **Rimosso `CREATE TABLE` ridondante**: la tabella è già creata da `init_db()` in `database.py`, non va ricreata nel modulo.
- **Fix transazione atomica**: DELETE + INSERT in un'unica transazione con `commit()` finale, `rollback()` esplicito in caso di errore.
- **Aggiunto logging** su tutte le operazioni.

#### Impostazioni
- **Fix `civico`**: aggiunto al form (era assente, impediva di modificare il campo).
- **Fix validazione `rt_porta` / `rt_baudrate`**: interi validati separatamente con messaggio chiaro per campo.
- **Fix validazione Fidelity**: float validati separatamente, messaggio chiaro invece del generico "could not convert".
- **Fix ricarica dopo salvataggio**: `carica_dati()` viene richiamato dopo un salvataggio riuscito, per allineare i campi al DB (es. float normalizzati).
- **Fix `except: pass`** in `carica_dati`: sostituito con `log.exception`.

#### Dashboard
- **Fix KPI sottoscorta**: usa `COALESCE(scorta_minima, soglia_minima, 0)`, allineato al modulo riordino.
- **Fix `except: pass`** per singolo KPI: sostituito con `log.warning` specifico per ogni query.

### 📦 Packaging & distribuzione

- **Aggiunto `requirements.txt`**: nessuna dipendenza runtime (solo standard library).
- **Aggiunto `requirements-dev.txt`**: solo `pyinstaller>=6.0` per la build.
- **Aggiunto `build.bat`**: script di automazione build con verifica prerequisiti (Python, `icona.ico`, `setup_script.iss`), pulizia cartelle, PyInstaller con `--clean`, Inno Setup 6.
- **Aggiunto `setup_script.iss`**: script Inno Setup allineato al nome exe `MercurioGestionale.exe`, rimosso blocco `[Icons]` duplicato, aggiunto `[Code]` con `taskkill` per chiudere eventuali istanze aperte prima dell'installazione.
- **Aggiunto `CHANGELOG.md`** (questo file).
- **Aggiunto `LICENSE`** (GPL v3).

### 🔧 Migliorato

- **Logging strutturato**: aggiunto logger `mercurio.*` per ogni modulo, con formato `[%(asctime)s] [%(levelname)s] %(name)s: %(message)s`, output su file (`mercurio.log`) e console.
- **Gestione errori UI**: `MercurioApp._add_tab` cattura eccezioni di caricamento moduli e mostra un riquadro rosso nella tab invece di un popup bloccante. Traceback completo nel log.
- **Robustezza connessioni**: `try/finally` con `conn.close()` garantito in tutti i moduli.
- **Coerenza fiscale POS → Documenti → Corrispettivi**: il flusso di vendita, annullo, chiusura Z ora è coerente e i totali tornano.

### 📝 Note

- **`scorta_minima` vs `soglia_minima`**: entrambe esistono nello schema. `magazzino.py` scrive `soglia_minima`, il riordino legge `COALESCE(scorta_minima, soglia_minima)`. Per la v0.4.0 si valuterà l'unificazione.
- **IVA per aliquota**: la chiusura Z attualmente assegna tutta l'IVA a `iva_22` perché `documenti` non ha il dettaglio righe. La ripartizione esatta (22/10/4/esente) richiede una tabella `documenti_righe` prevista per la v0.4.0.
- **Integrazione RT**: la configurazione IP/Seriale viene salvata in `impostazioni_azienda`, ma l'invio dei comandi al Registratore Telematico non è ancora implementato (previsto v0.4.0).
- **Fatturazione Elettronica SDI**: i documenti `FATTURA` vengono creati con `stato_xml = 'PRONTO_SDI'` ma non viene generato l'XML FatturaPA né inviato allo SDI (previsto v0.4.0).

---

## [Prossime versioni]

### [v0.4.0] - Pianificata

- Fattura accompagnatoria (fattura + DDT in un unico documento).
- Annullo documento con reso (per fatture, note di credito, DDT).
- Generazione XML FatturaPA e predisposizione invio SDI.
- Apertura cassetto RT (XON/XOFF seriale e TCP).
- Completare la ripartizione IVA per aliquota usando `documenti_righe`.
- Unificazione `soglia_minima` / `scorta_minima`.
- Backup automatico periodico.
- Porting Linux (WSL Debian, `.deb`, `.tar.gz`, `.rpm`).

---

## [Legenda]

- **Aggiunto**: nuove funzionalità.
- **Modificato**: modifiche a funzionalità esistenti.
- **Deprecato**: funzionalità che saranno rimosse.
- **Rimosso**: funzionalità rimosse.
- **Corretto**: correzioni di bug.
- **Sicurezza**: vulnerabilità corrette.

---

**Link di confronto**: 
- [v0.3.1 Alpha](https://github.com/andreasalerno89/Mercurio-Gestionale-Retail/releases/tag/v0.3.1-alpha)
- [v0.3.0 Alpha](https://github.com/andreasalerno89/Mercurio-Gestionale-Retail/releases/tag/v0.3.0-alpha)