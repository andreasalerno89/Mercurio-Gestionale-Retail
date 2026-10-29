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
        return sqlite3.connect(self.db_path)

    def crea_tabelle(self):
        with self.connetti() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clienti (
                    id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    cognome TEXT NOT NULL,
                    azienda TEXT,
                    partita_iva TEXT,
                    codice_fiscale TEXT,
                    telefono TEXT,
                    email TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fidelity_card (
                    id_card INTEGER PRIMARY KEY AUTOINCREMENT,
                    codice_carta TEXT UNIQUE NOT NULL,
                    id_cliente INTEGER,
                    punti INTEGER DEFAULT 0,
                    FOREIGN KEY (id_cliente) REFERENCES clienti(id_cliente)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fornitori (
                    id_fornitore INTEGER PRIMARY KEY AUTOINCREMENT,
                    ragione_sociale TEXT NOT NULL,
                    partita_iva TEXT,
                    email TEXT,
                    telefono TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articoli (
                    id_articolo INTEGER PRIMARY KEY AUTOINCREMENT,
                    codice_ean TEXT UNIQUE NOT NULL,
                    nome TEXT NOT NULL,
                    quantita INTEGER DEFAULT 0,
                    prezzo_acquisto REAL,
                    prezzo_vendita REAL NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documenti (
                    id_documento INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_documento TEXT NOT NULL,
                    numero_documento TEXT NOT NULL,
                    data_documento TEXT NOT NULL,
                    id_cliente INTEGER,
                    totale REAL DEFAULT 0.0,
                    metodo_pagamento TEXT,
                    FOREIGN KEY (id_cliente) REFERENCES clienti(id_cliente)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dettagli_documento (
                    id_dettaglio INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_documento INTEGER NOT NULL,
                    id_articolo INTEGER NOT NULL,
                    quantita INTEGER NOT NULL,
                    prezzo_unitario REAL NOT NULL,
                    subtotale REAL NOT NULL,
                    FOREIGN KEY (id_documento) REFERENCES documenti(id_documento),
                    FOREIGN KEY (id_articolo) REFERENCES articoli(id_articolo)
                )
            """)
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