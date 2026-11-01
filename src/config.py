import os
import json
import sqlite3
import shutil
import logging
from datetime import datetime
from pathlib import Path

from database import get_connection, init_db, DB_PATH

log = logging.getLogger("mercurio.config")

# Percorso predefinito della cartella Backup nei Documenti dell'utente
DOCUMENTS_DIR = Path.home() / "Documents" / "MercurioBackup"


def get_company_data():
    """Recupera la configurazione aziendale, i parametri RT e Fidelity dal database.
    Restituisce None SOLO se la tabella non esiste o è vuota. In caso di errore
    reale (DB corrotto, schema mancante) rilancia l'eccezione, così main.py
    può distinguere "primo avvio" da "problema di database"."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM impostazioni_azienda LIMIT 1")
        row = cursor.fetchone()
        if row is None:
            return None
        return dict(row)
    except sqlite3.OperationalError as e:
        # Tabella inesistente = primo avvio legittimo.
        # Altri OperationalError (DB locked, ecc.) vanno propagati.
        if "no such table" in str(e).lower():
            log.info("Tabella impostazioni_azienda assente: primo avvio.")
            return None
        log.exception("Errore DB in get_company_data")
        raise
    except Exception:
        log.exception("Errore imprevisto in get_company_data")
        raise
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def save_company_data(data):
    """Salva o aggiorna i dati aziendali, i parametri RT e le regole Fidelity.
    I campi non presenti in `data` NON vengono sovrascritti: si mantiene
    il valore esistente (o il default della tabella in caso di INSERT)."""
    init_db()

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM impostazioni_azienda LIMIT 1")
        row = cursor.fetchone()

        fields = [
            "ragione_sociale", "partita_iva", "codice_fiscale",
            "indirizzo", "civico", "cap", "localita", "provincia",
            "iban", "email",
            "rt_tipo_connessione", "rt_ip", "rt_porta", "rt_seriale", "rt_baudrate",
            "fidi_euro_per_punto", "fidi_soglia_punti", "fidi_sconto_valore",
        ]

        # Solo i campi effettivamente presenti in `data` vengono aggiornati.
        # In questo modo il wizard (che invia solo i 10 campi anagrafici) non
        # azzera i parametri RT/Fidelity impostati altrove.
        present_fields = [f for f in fields if f in data]
        if not present_fields:
            raise ValueError("save_company_data: nessun campo valido da salvare")

        values = [data[f] for f in present_fields]

        if row:
            set_clause = ", ".join([f"{f} = ?" for f in present_fields])
            query = f"UPDATE impostazioni_azienda SET {set_clause} WHERE id = ?"
            cursor.execute(query, values + [row["id"]])
        else:
            cols = ", ".join(present_fields)
            placeholders = ", ".join(["?"] * len(present_fields))
            query = f"INSERT INTO impostazioni_azienda ({cols}) VALUES ({placeholders})"
            cursor.execute(query, values)

        conn.commit()
        log.info("Impostazioni aziendali salvate (campi aggiornati: %s).",
                 ", ".join(present_fields))
    except Exception:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        log.exception("Errore in save_company_data")
        raise
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def esegui_backup_sistema(foto_dir=None):
    r"""
    Esegue il backup completo del DB e della cartella foto salvandoli in
    C:\Users\<utente>\Documents\MercurioBackup\
    Restituisce (True, path_backup) in caso di successo, (False, messaggio) altrimenti.
    """
    try:
        DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Backup Database SQLite — usa lo stesso DB_PATH di database.py,
        # così il backup è sempre del file effettivamente usato dall'app.
        db_source = DB_PATH
        if not os.path.exists(db_source):
            return False, f"Database non trovato: {db_source}"

        db_target = DOCUMENTS_DIR / f"gestionale_backup_{timestamp}.db"
        shutil.copy2(db_source, db_target)
        log.info("Backup DB salvato in %s", db_target)

        # Backup Cartella Foto Articoli (se specificata o presente)
        if foto_dir and os.path.exists(foto_dir):
            foto_target = DOCUMENTS_DIR / f"foto_articoli_{timestamp}"
            shutil.copytree(foto_dir, foto_target)
            log.info("Backup foto salvato in %s", foto_target)

        return True, str(DOCUMENTS_DIR)
    except Exception as e:
        log.exception("Errore durante il backup")
        return False, str(e)