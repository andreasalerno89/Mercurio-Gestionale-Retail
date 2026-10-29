import sqlite3
import os

def ottieni_percorso_db(nome_db="mercurio_retail.db"):
    r"""
    Ritorna il percorso assoluto e sicuro dove salvare il database SQLite.
    Se l'app è compilata o installata in Program Files, salva il DB in %LOCALAPPDATA%\MercurioRetail
    per evitare errori di permessi di scrittura.
    """
    local_appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    cartella_app = os.path.join(local_appdata, "MercurioRetail")
    
    if not os.path.exists(cartella_app):
        os.makedirs(cartella_app, exist_ok=True)
        
    return os.path.join(cartella_app, nome_db)

class DatabaseManager:
    def __init__(self, db_name="mercurio_retail.db"):
        self.db_path = ottieni_percorso_db(db_name)
        self.crea_tabelle()

    def connetti(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def crea_tabelle(self):
        with self.connetti() as conn:
            cursor = conn.cursor()
            
            # Tabella Clienti completa
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clienti (
                    id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    cognome TEXT NOT NULL,
                    azienda TEXT,
                    partita_iva TEXT,
                    codice_fiscale TEXT,
                    indirizzo TEXT,
                    numero_civico TEXT,
                    cap TEXT,
                    localita TEXT,
                    provincia TEXT,
                    telefono TEXT,
                    email TEXT,
                    pec TEXT,
                    codice_univoco TEXT
                )
            """)

            # Tabella Fidelity Card
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fidelity_card (
                    id_card INTEGER PRIMARY KEY AUTOINCREMENT,
                    codice_carta TEXT UNIQUE NOT NULL,
                    id_cliente INTEGER,
                    punti INTEGER DEFAULT 0,
                    FOREIGN KEY (id_cliente) REFERENCES clienti(id_cliente)
                )
            """)

            # Tabella Magazzino / Articoli completa
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articoli (
                    id_articolo INTEGER PRIMARY KEY AUTOINCREMENT,
                    codice_ean TEXT UNIQUE NOT NULL,
                    nome TEXT NOT NULL,
                    descrizione TEXT,
                    categoria TEXT,
                    fornitore TEXT,
                    quantita REAL DEFAULT 0.0,
                    prezzo_acquisto REAL DEFAULT 0.0,
                    prezzo_vendita REAL NOT NULL,
                    aliquota_iva REAL DEFAULT 22.0
                )
            """)

            # Tabella Movimenti di Banco / Documenti
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movimenti_banco (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_scontrino TEXT UNIQUE NOT NULL,
                    data_ora TEXT NOT NULL,
                    totale_netto REAL NOT NULL,
                    totale_iva REAL NOT NULL,
                    totale_lordo REAL NOT NULL,
                    tipo_pagamento TEXT NOT NULL,
                    importo_pagato REAL DEFAULT 0.0,
                    resto REAL DEFAULT 0.0
                )
            """)
            conn.commit()

            # Reparti predefiniti di comodo
            cursor.execute("SELECT COUNT(*) FROM reparti")
            if cursor.fetchone()[0] == 0:
                reparti_default = [
                    ("Generico", 22.0),
                    ("Alimentari", 10.0),
                    ("Abbigliamento", 22.0),
                    ("Servizi", 22.0)
                ]
                cursor.executemany("INSERT INTO reparti (nome_reparto, aliquota_iva) VALUES (?, ?)", reparti_default)

            conn.commit()

    def cerca_fidelity(self, codice_carta):
        with self.connetti() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT T.id_card, T.punti, C.nome, C.cognome 
                FROM fidelity_card T 
                LEFT JOIN clienti C ON T.id_cliente = C.id_cliente 
                WHERE T.codice_carta = ?
            """, (codice_carta,))
            return cursor.fetchone()

    def ottieni_articoli(self):
        with self.connetti() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_articolo, codice_ean, nome, quantita, prezzo_acquisto, prezzo_vendita FROM articoli")
            return cursor.fetchall()

    def inserisci_articolo(self, ean, nome, qta, px_acq, px_ven):
        with self.connetti() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO articoli (codice_ean, nome, quantita, prezzo_acquisto, prezzo_vendita)
                VALUES (?, ?, ?, ?, ?)
            """, (ean, nome, qta, px_acq, px_ven))
            conn.commit()

    def elimina_articolo(self, id_articolo):
        with self.connetti() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM articoli WHERE id_articolo = ?", (id_articolo,))
            conn.commit()

    def scarica_giacenza(self, id_articolo, quantita_venduta):
        with self.connetti() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE articoli 
                SET quantita = quantita - ? 
                WHERE id_articolo = ?
            """, (quantita_venduta, id_articolo))
            conn.commit()

    def ottieni_clienti(self):
        with self.connetti() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT C.id_cliente, C.nome, C.cognome, C.azienda, C.partita_iva, C.codice_fiscale, C.telefono, F.codice_carta, F.punti
                FROM clienti C
                LEFT JOIN fidelity_card F ON C.id_cliente = F.id_cliente
            """)
            return cursor.fetchall()

    def genera_prossimo_codice_fidelity(self):
        with self.connetti() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id_card) FROM fidelity_card")
            res = cursor.fetchone()
            prossimo_id = (res[0] or 0) + 1 if res else 1
            return f"FID-{prossimo_id:06d}"

    def inserisci_cliente(self, nome, cognome, azienda, p_iva, cf, tel, email, codice_fidelity):
        with self.connetti() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clienti (nome, cognome, azienda, partita_iva, codice_fiscale, telefono, email)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (nome, cognome, azienda, p_iva, cf, tel, email))
            id_cliente = cursor.lastrowid
            
            if codice_fidelity:
                cursor.execute("""
                    INSERT OR REPLACE INTO fidelity_card (codice_carta, id_cliente, punti)
                    VALUES (?, ?, 0)
                """, (codice_fidelity, id_cliente))
            conn.commit()

    def elimina_cliente(self, id_cliente):
        with self.connetti() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM fidelity_card WHERE id_cliente = ?", (id_cliente,))
            cursor.execute("DELETE FROM clienti WHERE id_cliente = ?", (id_cliente,))
            conn.commit()

# --- Funzioni di comodo globali per retrocompatibilità con app.py e pos_module.py ---
_db_manager = DatabaseManager()

def get_db_connection():
    """Restituisce una connessione attiva tramite DatabaseManager."""
    return _db_manager.connetti()

def init_db():
    """Inizializza il database e le tabelle."""
    _db_manager.crea_tabelle()