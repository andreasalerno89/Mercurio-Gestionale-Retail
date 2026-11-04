import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import date

from database import get_connection

log = logging.getLogger("mercurio.corrispettivi")


class CorrispettiviManagerTab(tk.Frame):
    """Modulo per la Chiusura Giornaliera (Z di Cassa) e il Registro Corrispettivi."""

    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        self.carica_corrispettivi()

    # ------------------------------------------------------------------ #
    # Costruzione UI
    # ------------------------------------------------------------------ #

    def create_widgets(self):
        top_frame = tk.Frame(self, padx=10, pady=10)
        top_frame.pack(fill="x")

        tk.Label(top_frame,
                 text="📅 Registro Corrispettivi & Chiusura Giornaliera (Z)",
                 font=("Arial", 12, "bold")).pack(side="left")

        tk.Button(top_frame, text="🖨️ Esegui Chiusura Z (Oggi)",
                  bg="#28a745", fg="white", font=("Arial", 10, "bold"),
                  command=self.esegui_chiusura_oggi).pack(side="right", padx=5)

        tk.Button(top_frame, text="🔄 Aggiorna Elenco",
                  bg="#6c757d", fg="white", font=("Arial", 9, "bold"),
                  command=self.carica_corrispettivi).pack(side="right", padx=5)

        # Tabella storico chiusure / corrispettivi giornalieri
        table_frame = tk.Frame(self, padx=10, pady=5)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "data", "num_scontrini", "totale_incassato",
                   "contanti", "pos", "iva_22", "iva_10", "stato")
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("data", text="Data Chiusura")
        self.tree.heading("num_scontrini", text="N. Scontrini")
        self.tree.heading("totale_incassato", text="Totale (€)")
        self.tree.heading("contanti", text="Contanti (€)")
        self.tree.heading("pos", text="POS (€)")
        self.tree.heading("iva_22", text="IVA 22% (€)")
        self.tree.heading("iva_10", text="IVA 10% (€)")
        self.tree.heading("stato", text="Stato RT")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("data", width=110, anchor="center")
        self.tree.column("num_scontrini", width=80, anchor="center")
        self.tree.column("totale_incassato", width=100, anchor="e")
        self.tree.column("contanti", width=100, anchor="e")
        self.tree.column("pos", width=90, anchor="e")
        self.tree.column("iva_22", width=90, anchor="e")
        self.tree.column("iva_10", width=90, anchor="e")
        self.tree.column("stato", width=90, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        bottom_frame = tk.Frame(self, bg="#f8f9fa", padx=15, pady=10,
                                relief="solid", bd=1)
        bottom_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(bottom_frame, text="ℹ️ Nota Fiscale:",
                 font=("Arial", 9, "bold"), bg="#f8f9fa").pack(anchor="w")
        tk.Label(bottom_frame,
                 text=("La Chiusura Z calcola i corrispettivi giornalieri "
                       "aggregando i documenti emessi dalla cassa POS. "
                       "Gli scontrini annullati sono esclusi dal conteggio e "
                       "compensati dal relativo scontrino di annullo (storno RT). "
                       "Il registro telematico è predisposto per la conservazione "
                       "e l'invio all'Agenzia delle Entrate."),
                 font=("Arial", 9), bg="#f8f9fa", justify="left").pack(anchor="w")

    # ------------------------------------------------------------------ #
    # Lettura registro
    # ------------------------------------------------------------------ #

    def carica_corrispettivi(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            # La tabella è già creata da init_db() in database.py.
            # Non ricrearla qui: violerebbe la regola "schema solo in database.py".
            cursor.execute("""
                SELECT id, data_chiusura, num_scontrini, totale_incassato,
                       contanti, pos, iva_22, iva_10, stato
                FROM corrispettivi_giornalieri
                ORDER BY data_chiusura DESC
            """)
            rows = cursor.fetchall()

            for r in rows:
                formatted_row = (
                    r[0],
                    r[1],
                    r[2],
                    f"€ {r[3]:.2f}" if r[3] is not None else "€ 0.00",
                    f"€ {r[4]:.2f}" if r[4] is not None else "€ 0.00",
                    f"€ {r[5]:.2f}" if r[5] is not None else "€ 0.00",
                    f"€ {r[6]:.2f}" if r[6] is not None else "€ 0.00",
                    f"€ {r[7]:.2f}" if r[7] is not None else "€ 0.00",
                    r[8],
                )
                self.tree.insert("", "end", values=formatted_row)
        except Exception as e:
            log.exception("Errore caricamento corrispettivi")
            messagebox.showerror("Errore Database",
                                 f"Impossibile caricare i corrispettivi: {e}",
                                 parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    # ------------------------------------------------------------------ #
    # Raccolta dati giornalieri (cuore fiscale)
    # ------------------------------------------------------------------ #

    def _raccogli_dati_giornalieri(self, cursor, data_iso):
        """Legge dai documenti del giorno:
           - numero scontrini VALIDI (esclusi annullati)
           - numero annulli (storni RT)
           - totale e imponibile complessivi (scontrini validi + annulli negativi)
           - ripartizione per tipo di pagamento (contanti/pos/altro)
           - IVA per aliquota (22/10/4/esente)

           Regola di inclusione:
             - SCONTRINO con stato_xml != 'ANNULLATO_RT'  -> valido, conta +1
             - SCONTRINO con stato_xml == 'ANNULLATO_RT'  -> escluso (compensato)
             - ANNULLO (importo negativo)                 -> incluso nel totale

           Restituisce un dict oppure None se non ci sono documenti utili.
           Logga warning per dati incoerenti (es. imponibile NULL, annulli orfani).
        """

        filtro_giornaliero = """
            DATE(data_emissione) = ?
            AND (
                (tipo_documento = 'SCONTRINO'
                 AND (stato_xml IS NULL OR stato_xml != 'ANNULLATO_RT'))
                OR tipo_documento = 'ANNULLO'
            )
        """

        # 1. Totali, numero scontrini validi, numero annulli
        cursor.execute(f"""
            SELECT
              COALESCE(SUM(CASE WHEN tipo_documento = 'SCONTRINO' THEN 1 ELSE 0 END), 0),
              COALESCE(SUM(totale_documento), 0),
              COALESCE(SUM(imponibile), 0),
              COALESCE(SUM(CASE WHEN tipo_documento = 'SCONTRINO'
                                  AND imponibile IS NULL THEN 1 ELSE 0 END), 0),
              COALESCE(SUM(CASE WHEN tipo_documento = 'ANNULLO' THEN 1 ELSE 0 END), 0)
            FROM documenti
            WHERE {filtro_giornaliero}
        """, (data_iso,))
        row = cursor.fetchone()
        num_scontrini = int(row[0] or 0)
        totale = float(row[1] or 0.0)
        imponibile = float(row[2] or 0.0)
        scontrini_senza_imponibile = int(row[3] or 0)
        num_annulli = int(row[4] or 0)

        if num_scontrini == 0 and num_annulli == 0:
            return None

        if scontrini_senza_imponibile > 0:
            log.warning(
                "Chiusura Z %s: %d scontrini con imponibile NULL. "
                "L'IVA calcolata potrebbe essere inesatta.",
                data_iso, scontrini_senza_imponibile,
            )

        if num_scontrini == 0 and num_annulli > 0:
            log.warning(
                "Chiusura Z %s: presenti %d annulli ma nessuno scontrino valido "
                "nella stessa giornata. Il totale sarà negativo o zero.",
                data_iso, num_annulli,
            )

        # 2. Ripartizione pagamenti (stesso filtro degli scontrini validi + annulli)
        cursor.execute(f"""
            SELECT
              COALESCE(SUM(CASE WHEN UPPER(COALESCE(pagamento, metodo_pagamento, '')) = 'CONTANTI'
                                THEN totale_documento ELSE 0 END), 0),
              COALESCE(SUM(CASE WHEN UPPER(COALESCE(pagamento, metodo_pagamento, '')) = 'POS'
                                THEN totale_documento ELSE 0 END), 0),
              COALESCE(SUM(CASE WHEN UPPER(COALESCE(pagamento, metodo_pagamento, '')) NOT IN ('CONTANTI', 'POS')
                                THEN totale_documento ELSE 0 END), 0)
            FROM documenti
            WHERE {filtro_giornaliero}
        """, (data_iso,))
        pag = cursor.fetchone()
        contanti = float(pag[0] or 0.0)
        pos = float(pag[1] or 0.0)
        altro = float(pag[2] or 0.0)

        if altro > 0.001:
            log.warning(
                "Chiusura Z %s: € %.2f di documenti con pagamento non "
                "classificato (né CONTANTI né POS).",
                data_iso, altro,
            )

        # 3. IVA. Come prima: tutto su iva_22.
        #    TODO v0.4: aliquota_iva per riga documento per ripartire 22/10/4/esente.
        iva_totale = totale - imponibile
        iva_22 = iva_totale
        iva_10 = 0.0
        iva_4 = 0.0
        esente = 0.0

        return {
            "num_scontrini": num_scontrini,
            "num_annulli": num_annulli,
            "totale_incassato": totale,
            "imponibile": imponibile,
            "contanti": contanti,
            "pos": pos,
            "altro": altro,
            "iva_22": iva_22,
            "iva_10": iva_10,
            "iva_4": iva_4,
            "esente": esente,
        }

    # ------------------------------------------------------------------ #
    # Chiusura Z
    # ------------------------------------------------------------------ #

    def esegui_chiusura_oggi(self):
        oggi = date.today().strftime("%Y-%m-%d")
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Controlla se esiste già una chiusura per oggi
            cursor.execute(
                "SELECT id FROM corrispettivi_giornalieri WHERE data_chiusura = ?",
                (oggi,))
            esiste = cursor.fetchone() is not None

            if esiste:
                if not messagebox.askyesno(
                    "Conferma Sovrascrittura",
                    f"Esiste già una Chiusura Z registrata per la data odierna "
                    f"({oggi}). Vuoi ricalcolarla e sovrascriverla?",
                    parent=self,
                ):
                    return

            dati = self._raccogli_dati_giornalieri(cursor, oggi)
            if dati is None:
                messagebox.showwarning(
                    "Attenzione",
                    f"Nessuno scontrino trovato per la data odierna ({oggi}). "
                    f"Impossibile eseguire la chiusura.",
                    parent=self,
                )
                return

            # Transazione atomica: DELETE + INSERT insieme.
            # Se l'INSERT fallisce, il DELETE viene rollbackato.
            if esiste:
                cursor.execute(
                    "DELETE FROM corrispettivi_giornalieri WHERE data_chiusura = ?",
                    (oggi,))

            cursor.execute("""
                INSERT INTO corrispettivi_giornalieri
                    (data_chiusura, num_scontrini, totale_incassato,
                     contanti, pos, iva_22, iva_10, iva_4, esente, stato)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'TRASMESSO_RT')
            """, (
                oggi,
                dati["num_scontrini"],
                dati["totale_incassato"],
                dati["contanti"],
                dati["pos"],
                dati["iva_22"],
                dati["iva_10"],
                dati["iva_4"],
                dati["esente"],
            ))

            conn.commit()

            self.carica_corrispettivi()
            messagebox.showinfo(
                "Chiusura Z Effettuata",
                f"Chiusura Giornaliera registrata con successo!\n\n"
                f"Data: {oggi}\n"
                f"Scontrini validi: {dati['num_scontrini']}\n"
                f"Annulli registrati: {dati['num_annulli']}\n"
                f"Totale Corrispettivi: € {dati['totale_incassato']:.2f}\n"
                f"• Contanti: € {dati['contanti']:.2f}\n"
                f"• POS: € {dati['pos']:.2f}\n"
                f"• IVA 22%: € {dati['iva_22']:.2f}",
                parent=self,
            )
        except Exception as e:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
            log.exception("Errore chiusura Z per data %s", oggi)
            messagebox.showerror(
                "Errore",
                f"Impossibile completare la chiusura giornaliera:\n{e}",
                parent=self,
            )
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass