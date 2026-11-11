import sqlite3
import os
import sys
import logging

log = logging.getLogger("mercurio.database")


def _get_db_path():
    """Restituisce il path del DB, adatto sia allo sviluppo che all'exe."""
    if getattr(sys, "frozen", False):
        # App compilata con PyInstaller: usa %LOCALAPPDATA%\MercurioGestionale
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        app_dir = os.path.join(base, "MercurioGestionale")
    else:
        # Sviluppo: DB accanto a src/
        app_dir = os.path.abspath(
            os.path.normpath(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
            )
        )
    os.makedirs(app_dir, exist_ok=True)
    return os.path.join(app_dir, "gestionale.db")


DB_PATH = _get_db_path()
DB_TIMEOUT = 10.0

def get_connection():
    """Restituisce una connessione al database SQLite con row_factory."""
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
    conn.row_factory = sqlite3.Row
    # Foreign keys attive (utile per i riferimenti fornitore_id / articolo_id)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _column_exists(cursor, table, column):
    """True se `column` esiste in `table`."""
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def _safe_add_column(cursor, table, column, ddl_type):
    """Aggiunge una colonna se non esiste. Non solleva se la colonna esiste già."""
    if not _column_exists(cursor, table, column):
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}")
            log.info("Migrazione: aggiunta colonna %s.%s", table, column)
        except sqlite3.OperationalError as e:
            # Race condition: qualcun altro l'ha aggiunta nel frattempo.
            log.warning("ALTER %s.%s ignorato: %s", table, column, e)


def init_db():
    """Inizializza tutte le tabelle del database e applica le migrazioni automatiche.
    Idempotente: può essere chiamata più volte senza effetti collaterali."""
    conn = get_connection()
    try:
        cursor = conn.cursor()

         # 1. Tabella Azienda/Impostazioni Generali e RT
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS impostazioni_azienda (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ragione_sociale TEXT,
                partita_iva TEXT,
                codice_fiscale TEXT,
                indirizzo TEXT,
                civico TEXT,
                cap TEXT,
                localita TEXT,
                provincia TEXT,
                iban TEXT,
                email TEXT,
                rt_tipo_connessione TEXT DEFAULT 'IP',
                rt_ip TEXT DEFAULT '192.168.1.100',
                rt_porta INTEGER DEFAULT 5000,
                rt_seriale TEXT DEFAULT 'COM1',
                rt_baudrate INTEGER DEFAULT 9600,
                rt_protocollo TEXT DEFAULT 'XON_XOFF_SERIALE',
                fidi_euro_per_punto REAL DEFAULT 1.0,
                fidi_soglia_punti REAL DEFAULT 200.0,
                fidi_sconto_valore REAL DEFAULT 20.0
            )
        """)

        # 2. Tabella Articoli (Magazzino avanzato)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articoli (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codice_interno TEXT UNIQUE,
                codice_ean TEXT,
                descrizione TEXT NOT NULL,
                categoria TEXT,
                unita_misura TEXT DEFAULT 'pz',
                peso_netto REAL DEFAULT 0.0,
                peso_lordo REAL DEFAULT 0.0,
                prezzo_acquisto_netto REAL DEFAULT 0.0,
                prezzo_acquisto_ivato REAL DEFAULT 0.0,
                prezzo_vendita_netto REAL DEFAULT 0.0,
                prezzo_vendita REAL DEFAULT 0.0,
                aliquota_iva TEXT DEFAULT '22%',
                giacenza REAL DEFAULT 0.0,
                soglia_minima REAL DEFAULT 5.0,
                scorta_minima REAL DEFAULT 5.0,
                fornitore_id INTEGER,
                foto_path TEXT,
                FOREIGN KEY (fornitore_id) REFERENCES fornitori(id)
            )
        """)

        # 3. Tabella Clienti & Fidelity
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clienti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ragione_sociale TEXT NOT NULL,
                codice_fiscale TEXT,
                partita_iva TEXT,
                numero_fidelity TEXT UNIQUE,
                indirizzo TEXT,
                civico TEXT,
                cap TEXT,
                localita TEXT,
                provincia TEXT,
                email TEXT,
                telefono TEXT,
                punti_fidelity REAL DEFAULT 0.0
            )
        """)

        # 4. Tabella Fornitori (con colonne per fatturazione elettronica
        #    e gestione pagamenti: codice_univoco = SDI, istituto_bancario,
        #    metodo_pagamento)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fornitori (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ragione_sociale TEXT NOT NULL,
                partita_iva TEXT,
                codice_fiscale TEXT,
                indirizzo TEXT,
                civico TEXT,
                cap TEXT,
                localita TEXT,
                provincia TEXT,
                email TEXT,
                pec TEXT,
                iban TEXT,
                telefono TEXT,
                codice_univoco TEXT,
                istituto_bancario TEXT,
                metodo_pagamento TEXT
            )
        """)

            # 5. Tabella Documenti Fiscali (Scontrini, Fatture, DDT, Annulli)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documenti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_documento TEXT,
                numero TEXT,
                data_emissione TEXT,
                cliente_id INTEGER,
                imponibile REAL,
                totale_documento REAL,
                stato_xml TEXT,
                pagamento TEXT,
                metodo_pagamento TEXT,
                fidelity_utilizzati REAL DEFAULT 0.0,
                punti_guadagnati REAL DEFAULT 0.0,
                scontrino_origine_id INTEGER,
                documento_origine_id INTEGER,
                tipo_soggetto TEXT DEFAULT 'OCCASIONALE',
                motivo_annullo TEXT,
                riferimento_esterno TEXT,
                FOREIGN KEY (cliente_id) REFERENCES clienti(id)
            )
        """)

        # 6. Tabella Movimenti di Magazzino
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movimenti_magazzino (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                articolo_id INTEGER,
                tipo_movimento TEXT,
                quantita REAL,
                causale TEXT,
                riferimento_id INTEGER,
                data_movimento TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (articolo_id) REFERENCES articoli(id)
            )
        """)

        # 7. Tabella Contatori Documenti
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contatori (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_documento TEXT UNIQUE,
                anno INTEGER,
                ultimo_numero INTEGER DEFAULT 0
            )
        """)

        # 8. Tabella Righe Documenti
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documenti_righe (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                documento_id INTEGER,
                articolo_id INTEGER,
                descrizione TEXT,
                quantita REAL,
                prezzo_unitario REAL,
                aliquota_iva REAL,
                totale_riga REAL,
                sconto_riga REAL DEFAULT 0.0,
                tipo_sconto_riga TEXT DEFAULT '%',
                FOREIGN KEY (documento_id) REFERENCES documenti(id),
                FOREIGN KEY (articolo_id) REFERENCES articoli(id)
            )
        """)

                # 8b. Tabella Dati DDT (Documento di Trasporto)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ddt_dati (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                documento_id INTEGER,
                vettore TEXT,
                destinatario_indirizzo TEXT,
                destinatario_cap TEXT,
                destinatario_localita TEXT,
                destinatario_provincia TEXT,
                causale_trasporto TEXT,
                data_ritiro TEXT,
                aspettativa TEXT,
                FOREIGN KEY (documento_id) REFERENCES documenti(id)
            )
        """)

        # 9. Tabella Corrispettivi Giornalieri (Chiusura Z)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS corrispettivi_giornalieri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_chiusura TEXT UNIQUE,
                num_scontrini INTEGER,
                totale_incassato REAL,
                contanti REAL,
                pos REAL,
                iva_22 REAL,
                iva_10 REAL,
                iva_4 REAL,
                esente REAL,
                stato TEXT
            )
        """)

        # ==========================================
        # MIGRAZIONI AUTOMATICHE PER DB ESISTENTI
        # ==========================================

                       # --- documenti ---------------------------------------------------
        _safe_add_column(cursor, "documenti", "pagamento", "TEXT")
        _safe_add_column(cursor, "documenti", "metodo_pagamento", "TEXT")
        _safe_add_column(cursor, "documenti", "scontrino_origine_id", "INTEGER")
        _safe_add_column(cursor, "documenti", "documento_origine_id", "INTEGER")
        _safe_add_column(cursor, "documenti", "tipo_soggetto", "TEXT DEFAULT 'OCCASIONALE'")
        _safe_add_column(cursor, "documenti", "motivo_annullo", "TEXT")
        _safe_add_column(cursor, "documenti", "riferimento_esterno", "TEXT")

        # --- documenti_righe ---------------------------------------------
        _safe_add_column(cursor, "documenti_righe", "sconto_riga", "REAL DEFAULT 0.0")
        _safe_add_column(cursor, "documenti_righe", "tipo_sconto_riga", "TEXT DEFAULT '%'")

        # --- ddt_dati (tabella creata via CREATE TABLE IF NOT EXISTS) ----

        # --- impostazioni_azienda ----------------------------------------
        _safe_add_column(cursor, "impostazioni_azienda", "rt_protocollo",
                         "TEXT DEFAULT 'XON_XOFF_SERIALE'")

        # --- corrispettivi_giornalieri -----------------------------------
        # (iva_4 ed esente potrebbero mancare in DB molto vecchi)
        _safe_add_column(cursor, "corrispettivi_giornalieri", "iva_4", "REAL")
        _safe_add_column(cursor, "corrispettivi_giornalieri", "esente", "REAL")

        # Commit unico finale: se qualcosa è andato storto prima,
        # SQLite fa rollback automatico alla chiusura della connessione.
        conn.commit()
        log.info("Database inizializzato e controllato: %s", DB_PATH)
        print(f"[DEBUG] Database inizializzato e controllato con successo: {DB_PATH}")
    except Exception:
        # Rollback esplicito in caso di errore non gestito
        try:
            conn.rollback()
        except Exception:
            pass
        log.exception("Errore critico in init_db()")
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    init_db()