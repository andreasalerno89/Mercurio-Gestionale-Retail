import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import logging

from database import get_connection

log = logging.getLogger("mercurio.pos")

# winsound è disponibile solo su Windows: l'import è protetto per non far
# crashare il modulo su altri sistemi operativi.
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


def _parse_aliquota(iva_str):
    """Converte '22%' / '10%' / '5%' / '4%' / 'Esente' in float (percentuale)."""
    s = (iva_str or "").strip().lower().replace("%", "")
    if s in ("esente", "esente iva", ""):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 22.0


class PosFrame(tk.Frame):
    """Interfaccia Cassa POS avanzata con reparti programmabili, sconti e popup cassa."""

    def __init__(self, parent):
        super().__init__(parent)
        self.carrello = []
        self.reparti_config = {
            "REP 1": {"nome": "Reparto 1 (Generico)", "iva": "22%"},
            "REP 2": {"nome": "Reparto 2 (Varie)", "iva": "10%"},
        }
        self.create_widgets()
        self.aggiorna_combos_clienti()

    def create_widgets(self):
        left_pane = tk.Frame(self)
        left_pane.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        right_pane = tk.Frame(self, width=380, bg="#f8f9fa", padx=10, pady=10)
        right_pane.pack(side="right", fill="y", padx=10, pady=10)
        right_pane.pack_propagate(False)

        # DISPLAY LCD VERDE
        lcd_frame = tk.Frame(left_pane, bg="black", padx=10, pady=8,
                             relief="sunken", bd=3)
        lcd_frame.pack(fill="x", pady=(0, 5))
        self.lcd_line1 = tk.Label(lcd_frame, text="MERCURIO POS — PRONTO",
                                  bg="black", fg="#00ff00",
                                  font=("Consolas", 11, "bold"), anchor="w")
        self.lcd_line1.pack(fill="x")
        self.lcd_line2 = tk.Label(lcd_frame, text="TOTALE: € 0.00",
                                  bg="black", fg="#00ff00",
                                  font=("Consolas", 16, "bold"), anchor="e")
        self.lcd_line2.pack(fill="x")

        # BARRA RICERCA ARTICOLO
        top_bar = tk.Frame(left_pane, bg="#e9ecef", padx=10, pady=8)
        top_bar.pack(fill="x", pady=5)
        top_bar.columnconfigure(1, weight=1)
        tk.Label(top_bar, text="Cerca (EAN / Nome):", bg="#e9ecef",
                 font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", padx=2)
        self.ean_entry = tk.Entry(top_bar, width=22, font=("Arial", 11))
        self.ean_entry.grid(row=0, column=1, sticky="ew", padx=2)
        self.ean_entry.focus()
        self.ean_entry.bind("<Return>", self.aggiungi_articolo_da_ricerca)
        tk.Button(top_bar, text="➕ Aggiungi", bg="#007bff", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.aggiungi_articolo_da_ricerca).grid(
            row=0, column=2, padx=5)

        # TABELLA CARRELLO
        table_frame = tk.Frame(left_pane)
        table_frame.pack(fill="both", expand=True, pady=5)
        columns = ("id", "ean", "descrizione", "prezzo",
                   "quantita", "sconto", "iva", "totale")
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", selectmode="browse")
        self.tree.bind("<Double-1>", self.modifica_riga_selezionata)
        for col, label in [
            ("id", "ID"), ("ean", "EAN / Cod"),
            ("descrizione", "Descrizione Articolo"),
            ("prezzo", "P. Unit (€)"), ("quantita", "Q.tà"),
            ("sconto", "Sc."), ("iva", "IVA"), ("totale", "Totale (€)"),
        ]:
            self.tree.heading(col, text=label)
        self.tree.column("id", width=30, anchor="center")
        self.tree.column("ean", width=80, anchor="center")
        self.tree.column("descrizione", width=210, anchor="w")
        self.tree.column("prezzo", width=70, anchor="e")
        self.tree.column("quantita", width=40, anchor="center")
        self.tree.column("sconto", width=55, anchor="center")
        self.tree.column("iva", width=45, anchor="center")
        self.tree.column("totale", width=80, anchor="e")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # PULSANTI GESTIONE CARRELLO
        cart_toolbar = tk.Frame(left_pane, pady=5)
        cart_toolbar.pack(fill="x")
        tk.Button(cart_toolbar, text="✏️ Modifica Riga", bg="#ffc107", fg="black",
                  font=("Arial", 9, "bold"),
                  command=self.modifica_riga_selezionata).pack(side="left", padx=2)
        tk.Button(cart_toolbar, text="➖ Annulla Riga", bg="#dc3545", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.rimuovi_riga).pack(side="left", padx=2)
        tk.Button(cart_toolbar, text="✂️ Sconto Totale", bg="#17a2b8", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.applica_sconto_totale).pack(side="left", padx=2)
        tk.Button(cart_toolbar, text="🗑️ Annulla Scontrino", bg="#343a40", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.svuota_carrello).pack(side="left", padx=2)
        tk.Button(cart_toolbar, text="⚙️ Config. Reparti", bg="#6c757d", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.apri_config_reparti).pack(side="left", padx=2)

        # PANNELLO DESTRA
        tk.Label(right_pane, text="CASSA & TASTIERINO TOUCH", bg="#f8f9fa",
                 font=("Arial", 11, "bold")).pack(pady=2)
        fid_frame = tk.Frame(right_pane, bg="#f8f9fa")
        fid_frame.pack(fill="x", pady=2)
        tk.Label(fid_frame, text="Cliente / Fidelity (Digita e premi Invio):",
                 bg="#f8f9fa", anchor="w", font=("Arial", 9)).pack(fill="x")
        self.cliente_combo = ttk.Combobox(fid_frame, state="normal", width=32)
        self.cliente_combo.pack(fill="x", pady=2)
        self.cliente_combo.bind("<Return>", self.cerca_cliente_rapido)
        tot_frame = tk.Frame(right_pane, bg="#e2e3e5", padx=8, pady=6)
        tot_frame.pack(fill="x", pady=5)
        tk.Label(tot_frame, text="TOTALE:", bg="#e2e3e5",
                 font=("Arial", 10, "bold")).pack(side="left")
        self.lbl_totale = tk.Label(tot_frame, text="€ 0.00", bg="#e2e3e5",
                                   fg="#28a745", font=("Arial", 18, "bold"))
        self.lbl_totale.pack(side="right")
        pay_input_frame = tk.Frame(right_pane, bg="#f8f9fa")
        pay_input_frame.pack(fill="x", pady=2)
        tk.Label(pay_input_frame, text="Input Cassa (€):", bg="#f8f9fa",
                 font=("Arial", 9, "bold")).pack(side="left")
        self.entry_input = tk.Entry(pay_input_frame, font=("Arial", 12),
                                    width=15, justify="right")
        self.entry_input.pack(side="right")

        # TASTIERINO NUMERICO TOUCH
        keypad_frame = tk.Frame(right_pane, bg="#dee2e6", padx=3, pady=3)
        keypad_frame.pack(fill="x", pady=4)
        buttons = [
            ('7', 0, 0), ('8', 0, 1), ('9', 0, 2), ('REP 1', 0, 3),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2), ('REP 2', 1, 3),
            ('1', 2, 0), ('2', 2, 1), ('3', 2, 2), ('QTA*', 2, 3),
            ('0', 3, 0), ('.', 3, 1), ('⌫', 3, 2), ('SC%', 3, 3),
        ]
        for (text, r, c) in buttons:
            if text in ("REP 1", "REP 2"):
                cmd = lambda t=text: self.batti_reparto(t)
                bg_col, fg_col = "#17a2b8", "white"
            elif text in ("QTA*", "SC%"):
                cmd = lambda t=text: self.esegui_funzione_tastierino(t)
                bg_col, fg_col = "#ffc107", "black"
            elif text == '⌫':
                cmd = self.cancella_ultimo_input
                bg_col, fg_col = "#dc3545", "white"
            else:
                cmd = lambda t=text: self.premi_tastierino(t)
                bg_col, fg_col = "white", "black"
            tk.Button(keypad_frame, text=text, font=("Arial", 9, "bold"),
                      width=5, height=1, bg=bg_col, fg=fg_col,
                      command=cmd).grid(row=r, column=c, padx=1, pady=1,
                                        sticky="nsew")
        for i in range(4):
            keypad_frame.rowconfigure(i, weight=1)
        for j in range(4):
            keypad_frame.columnconfigure(j, weight=1)

        pay_btn_frame = tk.Frame(right_pane, bg="#f8f9fa")
        pay_btn_frame.pack(fill="x", pady=(8, 2))
        tk.Button(pay_btn_frame, text="💵 PAGA CONTANTI", bg="#28a745", fg="white",
                  font=("Arial", 10, "bold"),
                  command=lambda: self.concludi_vendita("CONTANTI")).pack(
            side="left", expand=True, fill="x", padx=1)
        tk.Button(pay_btn_frame, text="💳 PAGA POS", bg="#007bff", fg="white",
                  font=("Arial", 10, "bold"),
                  command=lambda: self.concludi_vendita("POS")).pack(
            side="right", expand=True, fill="x", padx=1)

    # ------------------------------------------------------------------ #
    # Clienti
    # ------------------------------------------------------------------ #

    def aggiorna_combos_clienti(self):
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ragione_sociale, punti_fidelity
                FROM clienti ORDER BY ragione_sociale ASC
            """)
            clienti = cursor.fetchall()
            values = ["[ Cliente Occasionale ]"] + [
                f"{c[0]} - {c[1]} (Punti: {(c[2] or 0):.0f})" for c in clienti
            ]
            self.cliente_combo['values'] = values
            if not self.cliente_combo.get():
                self.cliente_combo.current(0)
        except Exception:
            log.exception("Errore aggiornamento combo clienti")
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def cerca_cliente_rapido(self, event=None):
        query = self.cliente_combo.get().strip().lower()
        if not query or query.startswith("["):
            return
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ragione_sociale, punti_fidelity
                FROM clienti
                WHERE LOWER(ragione_sociale) LIKE ?
                   OR COALESCE(codice_fiscale, '') LIKE ?
                LIMIT 1
            """, (f"%{query}%", f"%{query}%"))
            match = cursor.fetchone()
            if match:
                self.cliente_combo.set(
                    f"{match[0]} - {match[1]} (Punti: {(match[2] or 0):.0f})")
                self.suona_beep("ok")
            else:
                messagebox.showwarning(
                    "Non Trovato",
                    "Nessun cliente trovato con i criteri inseriti.",
                    parent=self)
        except Exception:
            log.exception("Errore ricerca cliente (query=%r)", query)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    # ------------------------------------------------------------------ #
    # Beep & tastierino
    # ------------------------------------------------------------------ #

    def suona_beep(self, tipo="ok"):
        if not HAS_WINSOUND:
            return
        try:
            if tipo == "ok":
                winsound.Beep(1200, 100)
            elif tipo == "errore":
                winsound.Beep(400, 300)
            elif tipo == "totale":
                winsound.Beep(1800, 150)
        except Exception:
            pass

    def premi_tastierino(self, char):
        self.suona_beep("ok")
        self.entry_input.insert(tk.END, char)

    def cancella_ultimo_input(self):
        self.suona_beep("ok")
        current = self.entry_input.get()
        if current:
            self.entry_input.delete(len(current) - 1, tk.END)

    def esegui_funzione_tastierino(self, funzione):
        self.suona_beep("ok")
        val_str = self.entry_input.get().strip()
        if not val_str:
            return
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "Attenzione",
                "Seleziona prima una riga nel carrello.",
                parent=self)
            return
        try:
            val = float(val_str.replace(",", "."))
            item_index = self.tree.index(selected[0])
            item = self.carrello[item_index]
            if funzione == 'QTA*':
                item['quantita'] = val
                item['totale'] = (item['prezzo'] *
                                  (1 - item['sconto_val'] / 100.0)) * val
            elif funzione == 'SC%':
                item['sconto_val'] = val
                item['totale'] = (item['prezzo'] *
                                  (1 - val / 100.0)) * item['quantita']
            self.entry_input.delete(0, tk.END)
            self.aggiorna_vista_carrello()
        except ValueError:
            self.suona_beep("errore")
            messagebox.showerror("Errore", "Valore digitato non valido.",
                                 parent=self)

    def apri_config_reparti(self):
        dialog = tk.Toplevel(self)
        dialog.title("Configurazione Reparti Cassa")
        dialog.geometry("400x320")
        dialog.transient(self)
        dialog.grab_set()
        tk.Label(dialog, text="Programmazione Reparti 1 e 2",
                 font=("Arial", 11, "bold")).pack(pady=10)
        tk.Label(dialog, text="Reparto 1 - Nome:",
                 font=("Arial", 9, "bold")).pack(anchor="w", padx=15)
        rep1_name = tk.Entry(dialog, width=35)
        rep1_name.pack(padx=15, pady=2)
        rep1_name.insert(0, self.reparti_config["REP 1"]["nome"])
        tk.Label(dialog, text="Reparto 1 - IVA:",
                 font=("Arial", 9)).pack(anchor="w", padx=15)
        rep1_iva = ttk.Combobox(dialog,
                                values=["22%", "10%", "5%", "4%", "Esente"],
                                width=32, state="readonly")
        rep1_iva.pack(padx=15, pady=2)
        rep1_iva.set(self.reparti_config["REP 1"]["iva"])
        tk.Label(dialog, text="Reparto 2 - Nome:",
                 font=("Arial", 9, "bold")).pack(anchor="w", padx=15, pady=(10, 0))
        rep2_name = tk.Entry(dialog, width=35)
        rep2_name.pack(padx=15, pady=2)
        rep2_name.insert(0, self.reparti_config["REP 2"]["nome"])
        tk.Label(dialog, text="Reparto 2 - IVA:",
                 font=("Arial", 9)).pack(anchor="w", padx=15)
        rep2_iva = ttk.Combobox(dialog,
                                values=["22%", "10%", "5%", "4%", "Esente"],
                                width=32, state="readonly")
        rep2_iva.pack(padx=15, pady=2)
        rep2_iva.set(self.reparti_config["REP 2"]["iva"])

        def salva():
            self.reparti_config["REP 1"]["nome"] = rep1_name.get().strip() or "Reparto 1"
            self.reparti_config["REP 1"]["iva"] = rep1_iva.get()
            self.reparti_config["REP 2"]["nome"] = rep2_name.get().strip() or "Reparto 2"
            self.reparti_config["REP 2"]["iva"] = rep2_iva.get()
            self.suona_beep("ok")
            dialog.destroy()

        tk.Button(dialog, text="Salva Configurazione", bg="#28a745",
                  fg="white", font=("Arial", 10, "bold"),
                  command=salva).pack(pady=15, fill="x", padx=15)

    def batti_reparto(self, codice_rep):
        val_str = self.entry_input.get().replace(",", ".").strip()
        if not val_str:
            messagebox.showwarning(
                "Attenzione",
                "Digita prima l'importo sul tastierino.",
                parent=self)
            return
        try:
            prezzo = float(val_str)
            if prezzo <= 0:
                raise ValueError()
            conf = self.reparti_config.get(codice_rep,
                                           {"nome": codice_rep, "iva": "22%"})
            self.carrello.append({
                "id": None,
                "ean": codice_rep,
                "descrizione": conf["nome"],
                "prezzo": prezzo,
                "quantita": 1.0,
                "sconto_val": 0.0,
                "sconto_tipo": "%",
                "iva": conf["iva"],
                "totale": prezzo,
            })
            self.entry_input.delete(0, tk.END)
            self.aggiorna_vista_carrello()
            self.suona_beep("ok")
        except ValueError:
            self.suona_beep("errore")
            messagebox.showerror("Errore", "Importo non valido.", parent=self)

    def aggiungi_articolo_da_ricerca(self, event=None):
        query = self.ean_entry.get().strip()
        if not query:
            return
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, codice_ean, descrizione, prezzo_vendita,
                       giacenza, aliquota_iva
                FROM articoli
                WHERE codice_ean = ?
                   OR CAST(id AS TEXT) = ?
                   OR LOWER(descrizione) LIKE ?
                LIMIT 1
            """, (query, query, f"%{query.lower()}%"))
            articolo = cursor.fetchone()
            if not articolo:
                self.suona_beep("errore")
                messagebox.showwarning(
                    "Non Trovato",
                    f"Nessun articolo trovato per '{query}'",
                    parent=self)
                return
            art_id, ean, descrizione, prezzo, giacenza, aliquota = articolo
            giacenza = float(giacenza or 0.0)
            if giacenza <= 0:
                self.suona_beep("errore")
                messagebox.showwarning(
                    "Giacenza Esaurita",
                    f"L'articolo '{descrizione}' ha giacenza {giacenza:.1f}.\n"
                    f"Impossibile venderlo.",
                    parent=self)
                return
            prezzo_unitario = float(prezzo or 0.0)
            aliquota_str = aliquota or "22%"
            self.carrello.append({
                "id": art_id,
                "ean": ean or "",
                "descrizione": descrizione,
                "prezzo": prezzo_unitario,
                "quantita": 1.0,
                "sconto_val": 0.0,
                "sconto_tipo": "%",
                "iva": aliquota_str,
                "totale": prezzo_unitario,
            })
            self.ean_entry.delete(0, tk.END)
            self.ean_entry.focus()
            self.aggiorna_vista_carrello()
            self.suona_beep("ok")
            self.lcd_line1.config(text=f"> {descrizione[:22]}")
        except Exception as e:
            log.exception("Errore aggiunta articolo (query=%r)", query)
            self.suona_beep("errore")
            messagebox.showerror("Errore",
                                 f"Impossibile aggiungere l'articolo: {e}",
                                 parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def aggiorna_vista_carrello(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        totale_generale = 0.0
        for item in self.carrello:
            totale_generale += item["totale"]
            sc_val = item.get('sconto_val', 0.0)
            sc_tipo = item.get('sconto_tipo', '%')
            sc_str = f"{sc_val:.1f}{sc_tipo}" if sc_val > 0 else "0%"
            formatted_row = (
                item["id"] if item["id"] else "LIB",
                item["ean"],
                item["descrizione"],
                f"€ {item['prezzo']:.2f}",
                f"{item['quantita']:.1f}",
                sc_str,
                item["iva"],
                f"€ {item['totale']:.2f}",
            )
            self.tree.insert("", "end", values=formatted_row)
        self.lbl_totale.config(text=f"€ {totale_generale:.2f}")
        self.lcd_line2.config(text=f"TOTALE: € {totale_generale:.2f}")

    def modifica_riga_selezionata(self, event=None):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attenzione",
                                   "Seleziona una riga da modificare.",
                                   parent=self)
            return
        item_index = self.tree.index(selected[0])
        item = self.carrello[item_index]
        dialog = tk.Toplevel(self)
        dialog.title("Modifica Riga Carrello")
        dialog.geometry("350x260")
        dialog.transient(self)
        dialog.grab_set()
        tk.Label(dialog, text="Quantità:",
                 font=("Arial", 9, "bold")).pack(anchor="w", padx=15, pady=(10, 2))
        qta_e = tk.Entry(dialog, width=30, font=("Arial", 11))
        qta_e.pack(padx=15)
        qta_e.insert(0, str(item['quantita']))
        tk.Label(dialog, text="Sconto Singolo (Valore o %):",
                 font=("Arial", 9, "bold")).pack(anchor="w", padx=15, pady=(10, 2))
        sc_frame = tk.Frame(dialog)
        sc_frame.pack(fill="x", padx=15)
        sc_e = tk.Entry(sc_frame, width=15, font=("Arial", 11))
        sc_e.pack(side="left")
        sc_e.insert(0, str(item.get('sconto_val', 0.0)))
        sc_tipo_cb = ttk.Combobox(sc_frame, values=["%", "€"], width=8,
                                  state="readonly")
        sc_tipo_cb.pack(side="left", padx=5)
        sc_tipo_cb.set(item.get('sconto_tipo', '%'))

        def salva():
            try:
                nqta = float(qta_e.get().replace(",", "."))
                nsc_val = float(sc_e.get().replace(",", ".").strip() or 0.0)
                nsc_tipo = sc_tipo_cb.get()
                if nsc_tipo == "%":
                    prezzo_scontato = item['prezzo'] * (1 - nsc_val / 100.0)
                else:
                    prezzo_scontato = max(0.0, item['prezzo'] - nsc_val)
                item['quantita'] = nqta
                item['sconto_val'] = nsc_val
                item['sconto_tipo'] = nsc_tipo
                item['totale'] = prezzo_scontato * nqta
                self.aggiorna_vista_carrello()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Errore", "Valori non validi.",
                                     parent=dialog)

        tk.Button(dialog, text="Aggiorna Riga", bg="#28a745", fg="white",
                  font=("Arial", 10, "bold"),
                  command=salva).pack(pady=20, fill="x", padx=15)

    def applica_sconto_totale(self):
        if not self.carrello:
            messagebox.showwarning("Attenzione", "Il carrello è vuoto.",
                                   parent=self)
            return
        totale_attuale = sum(item["totale"] for item in self.carrello)
        dialog = tk.Toplevel(self)
        dialog.title("Sconto / Arrotondamento sul Totale")
        dialog.geometry("380x250")
        dialog.transient(self)
        dialog.grab_set()
        tk.Label(dialog, text=f"Totale attuale: € {totale_attuale:.2f}",
                 font=("Arial", 11, "bold")).pack(pady=10)
        tipo_var = tk.StringVar(value="%")
        frame_tipo = tk.Frame(dialog)
        frame_tipo.pack(fill="x", padx=15, pady=2)
        tk.Radiobutton(frame_tipo, text="Percentuale (%)",
                       variable=tipo_var, value="%").pack(side="left", padx=10)
        tk.Radiobutton(frame_tipo, text="Valore Fisso (€)",
                       variable=tipo_var, value="EUR").pack(side="left", padx=10)
        tk.Label(dialog, text="Valore dello Sconto / Arrotondamento:",
                 font=("Arial", 9, "bold")).pack(anchor="w", padx=15, pady=(5, 2))
        val_entry = tk.Entry(dialog, width=25, font=("Arial", 12))
        val_entry.pack(padx=15, pady=2)

        def conferma():
            try:
                valore = float(val_entry.get().replace(",", ".").strip())
                tipo = tipo_var.get()
                if tipo == "%":
                    sconto_euro = totale_attuale * (valore / 100.0)
                    desc_sconto = f"Sconto Totale {valore:.1f}%"
                else:
                    sconto_euro = valore
                    desc_sconto = f"Sconto / Arrotondamento di € {valore:.2f}"
                if sconto_euro <= 0 or sconto_euro >= totale_attuale:
                    messagebox.showerror("Errore",
                                         "Valore di sconto non valido.",
                                         parent=dialog)
                    return
                self.carrello.append({
                    "id": None,
                    "ean": "SCONTO-TOT",
                    "descrizione": desc_sconto,
                    "prezzo": -sconto_euro,
                    "quantita": 1.0,
                    "sconto_val": 0.0,
                    "sconto_tipo": "%",
                    "iva": "22%",
                    "totale": -sconto_euro,
                })
                self.aggiorna_vista_carrello()
                self.suona_beep("ok")
                dialog.destroy()
            except ValueError:
                self.suona_beep("errore")
                messagebox.showerror("Errore", "Inserisci un numero valido.",
                                     parent=dialog)

        tk.Button(dialog, text="Applica Sconto Totale", bg="#ffc107",
                  fg="black", font=("Arial", 10, "bold"),
                  command=conferma).pack(pady=15, fill="x", padx=15)

    def rimuovi_riga(self):
        selected = self.tree.selection()
        if not selected:
            return
        item_index = self.tree.index(selected[0])
        del self.carrello[item_index]
        self.aggiorna_vista_carrello()

    def svuota_carrello(self):
        if self.carrello and messagebox.askyesno(
                "Conferma", "Annullare lo scontrino in corso?", parent=self):
            self.carrello = []
            self.aggiorna_vista_carrello()
            self.entry_input.delete(0, tk.END)
            self.lcd_line1.config(text="MERCURIO POS — PRONTO")
            self.lcd_line2.config(text="TOTALE: € 0.00")

    # ------------------------------------------------------------------ #
    # Conclusione vendita
    # ------------------------------------------------------------------ #

    def _estrai_cliente_id(self):
        sel = self.cliente_combo.get().strip()
        if not sel or sel.startswith("["):
            return None
        first = sel.split(" - ", 1)[0].strip()
        if first.isdigit():
            return int(first)
        return None

    def _calcola_imponibile(self, totale):
        if totale <= 0:
            return 0.0
        somma_iva = 0.0
        for item in self.carrello:
            if item.get("ean") == "SCONTO-TOT":
                continue
            aliquota = _parse_aliquota(item.get("iva", "22%"))
            if aliquota <= 0:
                continue
            imponibile_item = item["totale"] / (1 + aliquota / 100.0)
            iva_item = item["totale"] - imponibile_item
            somma_iva += iva_item
        return max(0.0, totale - somma_iva)

    def concludi_vendita(self, metodo_pagamento="CONTANTI"):
        if not self.carrello:
            self.suona_beep("errore")
            messagebox.showwarning("Carrello Vuoto",
                                   "Aggiungi articoli prima di pagare.",
                                   parent=self)
            return
        totale = sum(item["totale"] for item in self.carrello)
        if totale <= 0:
            self.suona_beep("errore")
            messagebox.showwarning(
                "Totale non valido",
                "Il totale dello scontrino è zero o negativo. "
                "Verifica sconti e quantità.",
                parent=self)
            return
        ricevuto = totale

        if metodo_pagamento == "CONTANTI":
            popup = tk.Toplevel(self)
            popup.title("Pagamento Contanti — Apertura Cassetto")
            popup.geometry("350x280")
            popup.transient(self)
            popup.grab_set()
            tk.Label(popup, text=f"TOTALE DOVUTO: € {totale:.2f}",
                     font=("Arial", 13, "bold"), fg="#28a745").pack(pady=15)
            frame_input = tk.Frame(popup)
            frame_input.pack(fill="x", padx=20, pady=5)
            tk.Label(frame_input, text="Contanti ricevuti (€):",
                     font=("Arial", 10, "bold")).pack(side="left")
            ricevuto_entry = tk.Entry(frame_input, font=("Arial", 13),
                                      width=12, justify="right")
            ricevuto_entry.pack(side="right")
            ricevuto_entry.insert(0, f"{totale:.2f}")
            ricevuto_entry.focus()
            ricevuto_entry.select_range(0, tk.END)
            lbl_resto_popup = tk.Label(popup, text="RESTO: € 0.00",
                                       font=("Arial", 15, "bold"), fg="#007bff")
            lbl_resto_popup.pack(pady=10)

            def calcola_resto_popup(e=None):
                try:
                    rcv_str = ricevuto_entry.get().replace(",", ".").strip()
                    rcv = float(rcv_str) if rcv_str else 0.0
                    rst = rcv - totale
                    if rst >= 0:
                        lbl_resto_popup.config(text=f"RESTO: € {rst:.2f}",
                                               fg="#007bff")
                    else:
                        lbl_resto_popup.config(
                            text=f"Mancano € {abs(rst):.2f}", fg="#dc3545")
                except ValueError:
                    lbl_resto_popup.config(text="Inserisci importo valido",
                                           fg="#dc3545")

            ricevuto_entry.bind("<KeyRelease>", calcola_resto_popup)
            risultato = {"completato": False, "ricevuto": totale}

            def conferma_pagamento():
                try:
                    rcv_str = ricevuto_entry.get().replace(",", ".").strip()
                    rcv = float(rcv_str) if rcv_str else totale
                    if rcv < totale:
                        messagebox.showerror(
                            "Errore",
                            "I contanti ricevuti sono inferiori al totale.",
                            parent=popup)
                        return
                    risultato["completato"] = True
                    risultato["ricevuto"] = rcv
                    popup.destroy()
                except ValueError:
                    messagebox.showerror("Errore",
                                         "Inserisci un importo valido.",
                                         parent=popup)

            tk.Button(popup, text="Conferma & Apri Cassetto", bg="#28a745",
                      fg="white", font=("Arial", 11, "bold"),
                      command=conferma_pagamento).pack(pady=15, fill="x", padx=20)
            self.wait_window(popup)
            if not risultato["completato"]:
                return
            ricevuto = risultato["ricevuto"]

        conn = None
        try:
            cliente_id = self._estrai_cliente_id()
            imponibile = self._calcola_imponibile(totale)

            # Controllo giacenza prima di procedere
            for item in self.carrello:
                if item["id"] is None:
                    continue
                conn = conn or get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT giacenza, descrizione FROM articoli WHERE id = ?",
                    (item["id"],))
                row = cursor.fetchone()
                if row is None:
                    messagebox.showerror(
                        "Errore",
                        f"Articolo id={item['id']} non trovato in magazzino.",
                        parent=self)
                    return
                giacenza_attuale = float(row[0] or 0.0)
                if giacenza_attuale < item["quantita"]:
                    messagebox.showerror(
                        "Giacenza insufficiente",
                        f"'{row[1]}': disponibili {giacenza_attuale:.1f}, "
                        f"richiesti {item['quantita']:.1f}.",
                        parent=self)
                    return

            conn = conn or get_connection()
            cursor = conn.cursor()
            data_ora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            numero = f"SCON-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:17]}"
            cursor.execute(
                "SELECT id FROM documenti WHERE numero = ?", (numero,))
            if cursor.fetchone() is not None:
                numero = numero + "-1"
            cursor.execute("""
                INSERT INTO documenti
                    (tipo_documento, numero, data_emissione, cliente_id,
                     imponibile, totale_documento, stato_xml,
                     pagamento, metodo_pagamento)
                VALUES ('SCONTRINO', ?, ?, ?, ?, ?, 'EMESSO', ?, ?)
            """, (numero, data_ora, cliente_id,
                  imponibile, totale,
                  metodo_pagamento, metodo_pagamento))
            doc_id = cursor.lastrowid

            # Inserisci le righe del documento in documenti_righe
            for item in self.carrello:
                if item.get("ean") == "SCONTO-TOT":
                    continue

                aliquota_num = _parse_aliquota(item.get("iva", "22%"))
                prezzo_unit = float(item.get("prezzo", 0.0))
                quantita = float(item.get("quantita", 1.0))
                totale_riga = float(item.get("totale", 0.0))
                sconto_val = float(item.get("sconto_val", 0.0))
                sconto_tipo = item.get("sconto_tipo", "%")

                cursor.execute("""
                    INSERT INTO documenti_righe
                        (documento_id, articolo_id, descrizione, quantita,
                         prezzo_unitario, aliquota_iva, totale_riga,
                         sconto_riga, tipo_sconto_riga)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_id,
                    item.get("id"),
                    item.get("descrizione", ""),
                    quantita,
                    prezzo_unit,
                    aliquota_num,
                    totale_riga,
                    sconto_val,
                    sconto_tipo,
                ))

                if item["id"]:
                    cursor.execute(
                        "UPDATE articoli SET giacenza = giacenza - ? WHERE id = ?",
                        (item["quantita"], item["id"]))
                    cursor.execute("""
                        INSERT INTO movimenti_magazzino
                            (articolo_id, tipo_movimento, quantita, causale,
                             riferimento_id)
                        VALUES (?, 'VENDITA', ?, 'Vendita POS', ?)
                    """, (item["id"], item["quantita"], doc_id))

            if cliente_id:
                punti = int(max(0, totale))
                cursor.execute(
                    "UPDATE clienti SET punti_fidelity = punti_fidelity + ? "
                    "WHERE id = ?", (punti, cliente_id))
            conn.commit()
            self.suona_beep("totale")
            resto = max(0.0, ricevuto - totale)
            messagebox.showinfo(
                "Vendita Conclusa",
                f"Scontrino {numero} registrato con successo!\n"
                f"Metodo: {metodo_pagamento}\n"
                f"Totale: € {totale:.2f}\n"
                f"Ricevuto: € {ricevuto:.2f}\n"
                f"Resto: € {resto:.2f}",
                parent=self)
            self.svuota_carrello()
            self.aggiorna_combos_clienti()
        except Exception as e:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
            log.exception("Errore registrazione vendita (metodo=%s)",
                          metodo_pagamento)
            self.suona_beep("errore")
            messagebox.showerror(
                "Errore",
                f"Impossibile registrare la vendita: {e}",
                parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass