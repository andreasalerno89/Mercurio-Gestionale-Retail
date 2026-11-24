import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime

from database import get_connection

log = logging.getLogger("mercurio.fattura_manual")


class FatturaManualDialog(tk.Toplevel):
    """Finestra per creare o modificare una fattura manuale."""

    def __init__(self, parent, fattura_id=None, callback=None):
        super().__init__(parent)
        self.parent = parent
        self.fattura_id = fattura_id  # None = nuova fattura, int = modifica bozza
        self.callback = callback
        self.righe = []  # lista di dict con i dati delle righe
        self.clienti_data = {}

        titolo = "Nuova Fattura" if fattura_id is None else "Modifica Fattura"
        self.title(titolo)
        self.geometry("900x700")
        self.resizable(True, True)
        self.transient(parent)
        self.wait_visibility()
        self.grab_set()

        self.create_widgets()

        if fattura_id is not None:
            self.carica_fattura_esistente()
        else:
            self.carica_clienti_combo()
            self.carica_articoli_combo()

    def create_widgets(self):
        # Header
        header = tk.Frame(self, padx=15, pady=10)
        header.pack(fill="x")
        tk.Label(header, text="Fattura Manuale",
                 font=("Arial", 14, "bold")).pack(anchor="w")
        tk.Label(header,
                 text="Crea una fattura da zero, senza passare dallo scontrino.",
                 font=("Arial", 9), fg="#666").pack(anchor="w")

        # Dati generali (numero, data, stato)
        dati_frame = tk.Frame(self, padx=15, pady=5)
        dati_frame.pack(fill="x")
        dati_frame.columnconfigure(1, weight=1)
        dati_frame.columnconfigure(3, weight=1)

        tk.Label(dati_frame, text="Numero:", font=("Arial", 9, "bold")).grid(
            row=0, column=0, sticky="w", padx=3, pady=2)
        self.lbl_numero = tk.Label(dati_frame, text="(assegnato all'emissione)",
                                   font=("Arial", 10), fg="#666")
        self.lbl_numero.grid(row=0, column=1, sticky="w", padx=3, pady=2)

        tk.Label(dati_frame, text="Data emissione:", font=("Arial", 9, "bold")).grid(
            row=0, column=2, sticky="w", padx=3, pady=2)
        self.entry_data = tk.Entry(dati_frame, width=15, font=("Arial", 10))
        self.entry_data.grid(row=0, column=3, sticky="w", padx=3, pady=2)
        self.entry_data.insert(0, datetime.now().strftime("%Y-%m-%d"))

        tk.Label(dati_frame, text="Stato:", font=("Arial", 9, "bold")).grid(
            row=1, column=0, sticky="w", padx=3, pady=2)
        self.stato_var = tk.StringVar(value="BOZZA")
        stato_frame = tk.Frame(dati_frame)
        stato_frame.grid(row=1, column=1, columnspan=3, sticky="w", padx=3, pady=2)
        tk.Radiobutton(stato_frame, text="Bozza", variable=self.stato_var,
                       value="BOZZA").pack(side="left", padx=3)
        tk.Radiobutton(stato_frame, text="Emetti subito", variable=self.stato_var,
                       value="EMESSO").pack(side="left", padx=3)

        # Cliente
        cliente_frame = tk.LabelFrame(self, text="Cliente", padx=10, pady=5)
        cliente_frame.pack(fill="x", padx=15, pady=5)
        cliente_frame.columnconfigure(1, weight=1)
        cliente_frame.columnconfigure(3, weight=1)

        self.tipo_soggetto_var = tk.StringVar(value="CLIENTE")
        tk.Radiobutton(cliente_frame, text="Cliente censito",
                       variable=self.tipo_soggetto_var, value="CLIENTE",
                       command=self.on_tipo_soggetto_change).grid(
            row=0, column=0, sticky="w", padx=3, pady=2)
        tk.Radiobutton(cliente_frame, text="Cliente occasionale",
                       variable=self.tipo_soggetto_var, value="OCCASIONALE",
                       command=self.on_tipo_soggetto_change).grid(
            row=0, column=1, columnspan=3, sticky="w", padx=3, pady=2)

        tk.Label(cliente_frame, text="Seleziona cliente:",
                 font=("Arial", 9, "bold")).grid(
            row=1, column=0, sticky="w", padx=3, pady=2)
        self.cliente_combo = ttk.Combobox(cliente_frame, state="readonly", width=40)
        self.cliente_combo.grid(row=1, column=1, columnspan=3, sticky="ew",
                                padx=3, pady=2)
        self.cliente_combo.bind("<<ComboboxSelected>>", self.on_cliente_change)

        tk.Label(cliente_frame, text="Nome / Ragione Sociale:",
                 font=("Arial", 9, "bold")).grid(
            row=2, column=0, sticky="w", padx=3, pady=2)
        self.entry_nome = tk.Entry(cliente_frame, width=40, font=("Arial", 10))
        self.entry_nome.grid(row=2, column=1, columnspan=3, sticky="ew",
                             padx=3, pady=2)

        tk.Label(cliente_frame, text="Indirizzo:",
                 font=("Arial", 9, "bold")).grid(
            row=3, column=0, sticky="w", padx=3, pady=2)
        self.entry_indirizzo = tk.Entry(cliente_frame, width=40, font=("Arial", 10))
        self.entry_indirizzo.grid(row=3, column=1, columnspan=3, sticky="ew",
                                  padx=3, pady=2)

        tk.Label(cliente_frame, text="CAP / Città:",
                 font=("Arial", 9, "bold")).grid(
            row=4, column=0, sticky="w", padx=3, pady=2)
        self.entry_cap = tk.Entry(cliente_frame, width=10, font=("Arial", 10))
        self.entry_cap.grid(row=4, column=1, sticky="w", padx=3, pady=2)
        self.entry_localita = tk.Entry(cliente_frame, width=25, font=("Arial", 10))
        self.entry_localita.grid(row=4, column=2, columnspan=2, sticky="ew",
                                 padx=3, pady=2)

        tk.Label(cliente_frame, text="Provincia:",
                 font=("Arial", 9, "bold")).grid(
            row=5, column=0, sticky="w", padx=3, pady=2)
        self.entry_provincia = tk.Entry(cliente_frame, width=10, font=("Arial", 10))
        self.entry_provincia.grid(row=5, column=1, sticky="w", padx=3, pady=2)

        tk.Label(cliente_frame, text="CF / P.IVA:",
                 font=("Arial", 9, "bold")).grid(
            row=6, column=0, sticky="w", padx=3, pady=2)
        self.entry_cf = tk.Entry(cliente_frame, width=20, font=("Arial", 10))
        self.entry_cf.grid(row=6, column=1, sticky="w", padx=3, pady=2)
        self.entry_piva = tk.Entry(cliente_frame, width=20, font=("Arial", 10))
        self.entry_piva.grid(row=6, column=2, columnspan=2, sticky="w",
                             padx=3, pady=2)

        # Pagamento
        pag_frame = tk.LabelFrame(self, text="Pagamento", padx=10, pady=5)
        pag_frame.pack(fill="x", padx=15, pady=5)
        pag_frame.columnconfigure(1, weight=1)
        pag_frame.columnconfigure(3, weight=1)

        tk.Label(pag_frame, text="Metodo:", font=("Arial", 9, "bold")).grid(
            row=0, column=0, sticky="w", padx=3, pady=2)
        self.combo_pagamento = ttk.Combobox(
            pag_frame,
            values=["CONTANTI", "POS", "BONIFICO_IMMEDIATO", "BONIFICO_DIFFERITO"],
            state="readonly", width=25)
        self.combo_pagamento.grid(row=0, column=1, sticky="w", padx=3, pady=2)
        self.combo_pagamento.set("CONTANTI")
        self.combo_pagamento.bind("<<ComboboxSelected>>", self.on_pagamento_change)

        tk.Label(pag_frame, text="IBAN:", font=("Arial", 9, "bold")).grid(
            row=1, column=0, sticky="w", padx=3, pady=2)
        self.entry_iban = tk.Entry(pag_frame, width=40, font=("Arial", 10))
        self.entry_iban.grid(row=1, column=1, columnspan=3, sticky="ew",
                             padx=3, pady=2)

        tk.Label(pag_frame, text="Scadenza (se differito):",
                 font=("Arial", 9, "bold")).grid(
            row=2, column=0, sticky="w", padx=3, pady=2)
        self.entry_scadenza = tk.Entry(pag_frame, width=15, font=("Arial", 10))
        self.entry_scadenza.grid(row=2, column=1, sticky="w", padx=3, pady=2)

        # Note
        note_frame = tk.LabelFrame(self, text="Note", padx=10, pady=5)
        note_frame.pack(fill="x", padx=15, pady=5)
        self.text_note = tk.Text(note_frame, height=3, width=80, font=("Arial", 10))
        self.text_note.pack(fill="x")

        # Righe
        righe_frame = tk.LabelFrame(self, text="Righe fattura", padx=10, pady=5)
        righe_frame.pack(fill="both", expand=True, padx=15, pady=5)

        art_toolbar = tk.Frame(righe_frame)
        art_toolbar.pack(fill="x", pady=3)
        tk.Label(art_toolbar, text="Articolo:", font=("Arial", 9)).pack(side="left")
        self.art_combo = ttk.Combobox(art_toolbar, state="readonly", width=45)
        self.art_combo.pack(side="left", padx=5)
        tk.Label(art_toolbar, text="Q.tà:", font=("Arial", 9)).pack(side="left")
        self.qta_entry = tk.Entry(art_toolbar, width=6, font=("Arial", 10))
        self.qta_entry.pack(side="left", padx=3)
        self.qta_entry.insert(0, "1")
        tk.Button(art_toolbar, text="➕ Aggiungi", bg="#007bff", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.aggiungi_riga).pack(side="left", padx=5)
        tk.Button(art_toolbar, text="🆓 Riga libera", bg="#6c757d", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.aggiungi_riga_libera).pack(side="left", padx=5)

        table_frame = tk.Frame(righe_frame)
        table_frame.pack(fill="both", expand=True, pady=3)

        columns = ("id", "descrizione", "quantita", "prezzo", "iva", "sconto", "totale")
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", selectmode="browse", height=8)
        self.tree.heading("id", text="ID")
        self.tree.heading("descrizione", text="Descrizione")
        self.tree.heading("quantita", text="Q.tà")
        self.tree.heading("prezzo", text="P. Unit.")
        self.tree.heading("iva", text="IVA")
        self.tree.heading("sconto", text="Sconto")
        self.tree.heading("totale", text="Totale")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("descrizione", width=300, anchor="w")
        self.tree.column("quantita", width=70, anchor="center")
        self.tree.column("prezzo", width=90, anchor="e")
        self.tree.column("iva", width=60, anchor="center")
        self.tree.column("sconto", width=80, anchor="center")
        self.tree.column("totale", width=90, anchor="e")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self.modifica_riga)

        btn_riga = tk.Frame(righe_frame)
        btn_riga.pack(fill="x", pady=3)
        tk.Button(btn_riga, text="✏️ Modifica riga", bg="#ffc107", fg="black",
                  font=("Arial", 9, "bold"),
                  command=self.modifica_riga).pack(side="left", padx=3)
        tk.Button(btn_riga, text="🗑️ Rimuovi riga", bg="#dc3545", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.rimuovi_riga).pack(side="left", padx=3)

        # Totali
        totali_frame = tk.Frame(self, padx=15, pady=5)
        totali_frame.pack(fill="x")
        self.lbl_imponibile = tk.Label(totali_frame, text="Imponibile: € 0.00",
                                       font=("Arial", 10))
        self.lbl_imponibile.pack(side="right", padx=10)
        self.lbl_iva = tk.Label(totali_frame, text="IVA: € 0.00",
                                font=("Arial", 10))
        self.lbl_iva.pack(side="right", padx=10)
        self.lbl_totale = tk.Label(totali_frame, text="Totale: € 0.00",
                                   font=("Arial", 12, "bold"), fg="#28a745")
        self.lbl_totale.pack(side="right", padx=10)

        # Pulsanti finali
        actions = tk.Frame(self, padx=15, pady=10)
        actions.pack(fill="x")
        tk.Button(actions, text="Annulla", bg="#6c757d", fg="white",
                  font=("Arial", 10, "bold"),
                  command=self.destroy).pack(side="right", padx=5)
        tk.Button(actions, text="Salva bozza", bg="#17a2b8", fg="white",
                  font=("Arial", 10, "bold"),
                  command=self.salva_bozza).pack(side="right", padx=5)
        tk.Button(actions, text="Emetti fattura", bg="#28a745", fg="white",
                  font=("Arial", 10, "bold"),
                  command=self.emetti_fattura).pack(side="right", padx=5)
            # ------------------------------------------------------------------ #
    # Caricamento dati
    # ------------------------------------------------------------------ #

    def carica_clienti_combo(self):
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ragione_sociale, indirizzo, cap, localita, provincia,
                       codice_fiscale, partita_iva
                FROM clienti ORDER BY ragione_sociale ASC
            """)
            clienti = cursor.fetchall()
            self.clienti_data = {}
            values = ["[ Cliente Occasionale ]"]
            for c in clienti:
                display = f"{c['id']} - {c['ragione_sociale']}"
                values.append(display)
                self.clienti_data[c['id']] = dict(c)
            self.cliente_combo['values'] = values
            if values:
                self.cliente_combo.set(values[0])
        except Exception as e:
            log.exception("Errore caricamento clienti per fattura manuale")
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def carica_articoli_combo(self):
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, descrizione, prezzo_vendita, aliquota_iva
                FROM articoli ORDER BY descrizione ASC
            """)
            articoli = cursor.fetchall()
            self.articoli_data = {}
            values = []
            for a in articoli:
                display = f"{a['id']} - {a['descrizione']} (€{a['prezzo_vendita']:.2f})"
                values.append(display)
                self.articoli_data[a['id']] = dict(a)
            self.art_combo['values'] = values
            if values:
                self.art_combo.current(0)
        except Exception as e:
            log.exception("Errore caricamento articoli per fattura manuale")
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def carica_fattura_esistente(self):
        """Carica i dati di una fattura esistente (solo se in bozza)."""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM documenti WHERE id = ? AND tipo_documento = 'FATTURA'
            """, (self.fattura_id,))
            doc = cursor.fetchone()

            if not doc:
                messagebox.showerror("Errore", "Fattura non trovata.", parent=self)
                self.destroy()
                return

            if doc["stato_documento"] != "BOZZA":
                messagebox.showwarning(
                    "Attenzione",
                    "Questa fattura è già stata emessa e non può essere modificata.",
                    parent=self)
                self.destroy()
                return

            # Numero (in bozza, mostra "BOZZA-{id}")
            self.lbl_numero.config(text=f"BOZZA-{doc['id']}")
            self.entry_data.delete(0, tk.END)
            self.entry_data.insert(0, doc["data_emissione"] or "")

            # Cliente
            if doc["cliente_id"]:
                self.tipo_soggetto_var.set("CLIENTE")
                if doc["cliente_id"] in self.clienti_data:
                    c = self.clienti_data[doc["cliente_id"]]
                    display = f"{c['id']} - {c['ragione_sociale']}"
                    self.cliente_combo.set(display)
            else:
                self.tipo_soggetto_var.set("OCCASIONALE")
                self.cliente_combo.set("[ Cliente Occasionale ]")

            self.entry_nome.delete(0, tk.END)
            self.entry_nome.insert(0, doc["tipo_soggetto"] == "OCCASIONALE" and "" or "")
            # I campi liberi per il cliente occasionale non sono salvati in DB,
            # quindi li lasciamo vuoti per ora.

            # Pagamento
            self.combo_pagamento.set(doc["pagamento"] or "CONTANTI")
            self.entry_iban.delete(0, tk.END)
            self.entry_scadenza.delete(0, tk.END)

            # Note
            self.text_note.delete("1.0", tk.END)
            if doc["note"]:
                self.text_note.insert("1.0", doc["note"])

            # Righe
            cursor.execute("""
                SELECT id, articolo_id, descrizione, quantita, prezzo_unitario,
                       aliquota_iva, totale_riga, sconto_riga, tipo_sconto_riga
                FROM documenti_righe
                WHERE documento_id = ?
                ORDER BY id ASC
            """, (self.fattura_id,))
            righe = cursor.fetchall()
            self.righe = []
            for r in righe:
                self.righe.append({
                    "articolo_id": r["articolo_id"],
                    "descrizione": r["descrizione"],
                    "quantita": r["quantita"],
                    "prezzo_unitario": r["prezzo_unitario"],
                    "aliquota_iva": r["aliquota_iva"],
                    "totale_riga": r["totale_riga"],
                    "sconto_riga": r["sconto_riga"],
                    "tipo_sconto_riga": r["tipo_sconto_riga"],
                })
            self.aggiorna_tree()
            self.aggiorna_totali()
        except Exception as e:
            log.exception("Errore caricamento fattura esistente id=%s", self.fattura_id)
            messagebox.showerror("Errore", f"Impossibile caricare la fattura: {e}", parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    # ------------------------------------------------------------------ #
    # Gestione cliente
    # ------------------------------------------------------------------ #

    def on_tipo_soggetto_change(self):
        tipo = self.tipo_soggetto_var.get()
        if tipo == "CLIENTE":
            self.cliente_combo.config(state="readonly")
        else:
            self.cliente_combo.set("[ Cliente Occasionale ]")
            self.cliente_combo.config(state="disabled")
            # Svuota i campi precompilati
            for e in (self.entry_nome, self.entry_indirizzo, self.entry_cap,
                      self.entry_localita, self.entry_provincia, self.entry_cf,
                      self.entry_piva):
                e.delete(0, tk.END)

    def on_cliente_change(self, event=None):
        sel = self.cliente_combo.get().strip()
        if not sel or sel.startswith("["):
            return
        first = sel.split(" - ", 1)[0].strip()
        if first.isdigit():
            cid = int(first)
            if cid in self.clienti_data:
                c = self.clienti_data[cid]
                self.entry_nome.delete(0, tk.END)
                self.entry_nome.insert(0, c.get("ragione_sociale") or "")
                self.entry_indirizzo.delete(0, tk.END)
                self.entry_indirizzo.insert(0, c.get("indirizzo") or "")
                self.entry_cap.delete(0, tk.END)
                self.entry_cap.insert(0, c.get("cap") or "")
                self.entry_localita.delete(0, tk.END)
                self.entry_localita.insert(0, c.get("localita") or "")
                self.entry_provincia.delete(0, tk.END)
                self.entry_provincia.insert(0, c.get("provincia") or "")
                self.entry_cf.delete(0, tk.END)
                self.entry_cf.insert(0, c.get("codice_fiscale") or "")
                self.entry_piva.delete(0, tk.END)
                self.entry_piva.insert(0, c.get("partita_iva") or "")

    def on_pagamento_change(self, event=None):
        metodo = self.combo_pagamento.get()
        if metodo in ("BONIFICO_IMMEDIATO", "BONIFICO_DIFFERITO"):
            self.entry_iban.config(state="normal")
        else:
            self.entry_iban.delete(0, tk.END)
            self.entry_iban.config(state="disabled")

        if metodo == "BONIFICO_DIFFERITO":
            self.entry_scadenza.config(state="normal")
        else:
            self.entry_scadenza.delete(0, tk.END)
            self.entry_scadenza.config(state="disabled")

    # ------------------------------------------------------------------ #
    # Gestione righe
    # ------------------------------------------------------------------ #

    def _chiedi_dati_riga(self, articolo_id=None, descrizione_iniziale="",
                          prezzo_iniziale=0.0, iva_iniziale=22.0,
                          quantita_iniziale=1.0, sconto_iniziale=0.0,
                          tipo_sconto_iniziale="%"):
        """Finestra modale per chiedere i dati di una riga."""
        dialog = tk.Toplevel(self)
        dialog.title("Dati riga")
        dialog.geometry("420x340")
        dialog.transient(self)
        dialog.wait_visibility()
        dialog.grab_set()

        tk.Label(dialog, text="Descrizione:", font=("Arial", 9, "bold")).pack(anchor="w", padx=15, pady=(10, 2))
        desc_entry = tk.Entry(dialog, width=45, font=("Arial", 10))
        desc_entry.pack(padx=15)
        desc_entry.insert(0, descrizione_iniziale)

        tk.Label(dialog, text="Quantità:", font=("Arial", 9, "bold")).pack(anchor="w", padx=15, pady=(8, 2))
        qta_entry = tk.Entry(dialog, width=15, font=("Arial", 10))
        qta_entry.pack(anchor="w", padx=15)
        qta_entry.insert(0, str(quantita_iniziale))

        tk.Label(dialog, text="Prezzo unitario:", font=("Arial", 9, "bold")).pack(anchor="w", padx=15, pady=(8, 2))
        prezzo_entry = tk.Entry(dialog, width=15, font=("Arial", 10))
        prezzo_entry.pack(anchor="w", padx=15)
        prezzo_entry.insert(0, str(prezzo_iniziale))

        tk.Label(dialog, text="Aliquota IVA:", font=("Arial", 9, "bold")).pack(anchor="w", padx=15, pady=(8, 2))
        iva_combo = ttk.Combobox(dialog, values=["22", "10", "5", "4", "0"],
                                 state="readonly", width=10)
        iva_combo.pack(anchor="w", padx=15)
        iva_combo.set(str(int(iva_iniziale)))

        tk.Label(dialog, text="Sconto:", font=("Arial", 9, "bold")).pack(anchor="w", padx=15, pady=(8, 2))
        sc_frame = tk.Frame(dialog)
        sc_frame.pack(anchor="w", padx=15)
        sconto_entry = tk.Entry(sc_frame, width=10, font=("Arial", 10))
        sconto_entry.pack(side="left")
        sconto_entry.insert(0, str(sconto_iniziale))
        tipo_sconto_combo = ttk.Combobox(sc_frame, values=["%", "€"], state="readonly", width=5)
        tipo_sconto_combo.pack(side="left", padx=5)
        tipo_sconto_combo.set(tipo_sconto_iniziale)

        risultato = {"ok": False}

        def conferma():
            try:
                desc = desc_entry.get().strip()
                qta = float(qta_entry.get().replace(",", ".") or 0)
                prezzo = float(prezzo_entry.get().replace(",", ".") or 0)
                iva = float(iva_combo.get() or 22)
                sconto = float(sconto_entry.get().replace(",", ".") or 0)
                tipo_sconto = tipo_sconto_combo.get()

                if not desc or qta <= 0 or prezzo < 0:
                    messagebox.showerror("Errore", "Compila descrizione, quantità e prezzo.", parent=dialog)
                    return

                # Calcolo totale con sconto
                if tipo_sconto == "%":
                    prezzo_scontato = prezzo * (1 - sconto / 100.0)
                else:
                    prezzo_scontato = max(0.0, prezzo - sconto)
                totale = prezzo_scontato * qta

                risultato["ok"] = True
                risultato["articolo_id"] = articolo_id
                risultato["descrizione"] = desc
                risultato["quantita"] = qta
                risultato["prezzo_unitario"] = prezzo
                risultato["aliquota_iva"] = iva
                risultato["sconto_riga"] = sconto
                risultato["tipo_sconto_riga"] = tipo_sconto
                risultato["totale_riga"] = totale
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Errore", "Controlla i valori numerici.", parent=dialog)

        tk.Button(dialog, text="Conferma", bg="#28a745", fg="white",
                  font=("Arial", 10, "bold"),
                  command=conferma).pack(pady=15, fill="x", padx=15)

        self.wait_window(dialog)
        return risultato if risultato["ok"] else None

    def aggiungi_riga(self):
        sel = self.art_combo.get().strip()
        if not sel:
            return
        first = sel.split(" - ", 1)[0].strip()
        if not first.isdigit():
            return
        aid = int(first)

        art = self.articoli_data.get(aid)
        if not art:
            return

        try:
            qta = float(self.qta_entry.get().replace(",", ".") or 1)
        except ValueError:
            qta = 1.0

        dati = self._chiedi_dati_riga(
            articolo_id=aid,
            descrizione_iniziale=art['descrizione'],
            prezzo_iniziale=float(art['prezzo_vendita'] or 0.0),
            iva_iniziale=float(str(art['aliquota_iva'] or "22").replace("%", "")),
            quantita_iniziale=qta,
        )
        if dati:
            self.righe.append(dati)
            self.aggiorna_tree()
            self.aggiorna_totali()

    def aggiungi_riga_libera(self):
        dati = self._chiedi_dati_riga()
        if dati:
            self.righe.append(dati)
            self.aggiorna_tree()
            self.aggiorna_totali()

    def modifica_riga(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        if idx < 0 or idx >= len(self.righe):
            return

        r = self.righe[idx]
        dati = self._chiedi_dati_riga(
            articolo_id=r["articolo_id"],
            descrizione_iniziale=r["descrizione"],
            prezzo_iniziale=r["prezzo_unitario"],
            iva_iniziale=r["aliquota_iva"],
            quantita_iniziale=r["quantita"],
            sconto_iniziale=r["sconto_riga"],
            tipo_sconto_iniziale=r["tipo_sconto_riga"],
        )
        if dati:
            self.righe[idx] = dati
            self.aggiorna_tree()
            self.aggiorna_totali()

    def rimuovi_riga(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        if 0 <= idx < len(self.righe):
            del self.righe[idx]
            self.aggiorna_tree()
            self.aggiorna_totali()

    def aggiorna_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for r in self.righe:
            iva_str = f"{r['aliquota_iva']:.0f}%"
            sconto_str = f"{r['sconto_riga']:.1f}{r['tipo_sconto_riga']}" if r['sconto_riga'] > 0 else "0%"
            self.tree.insert("", "end", values=(
                r["articolo_id"] if r["articolo_id"] else "LIB",
                r["descrizione"],
                f"{r['quantita']:.2f}",
                f"€ {r['prezzo_unitario']:.2f}",
                iva_str,
                sconto_str,
                f"€ {r['totale_riga']:.2f}",
            ))

    def aggiorna_totali(self):
        imponibile = 0.0
        iva_totale = 0.0
        totale = 0.0
        for r in self.righe:
            t = float(r["totale_riga"] or 0.0)
            a = float(r["aliquota_iva"] or 0.0)
            imp = t / (1 + a / 100.0) if a > 0 else t
            imponibile += imp
            iva_totale += (t - imp)
            totale += t
        self.lbl_imponibile.config(text=f"Imponibile: € {imponibile:.2f}")
        self.lbl_iva.config(text=f"IVA: € {iva_totale:.2f}")
        self.lbl_totale.config(text=f"Totale: € {totale:.2f}")

    # ------------------------------------------------------------------ #
    # Salvataggio
    # ------------------------------------------------------------------ #

    def _valida_campi(self):
        if not self.righe:
            messagebox.showwarning("Attenzione", "Aggiungi almeno una riga.", parent=self)
            return False
        data_em = self.entry_data.get().strip()
        if not data_em:
            messagebox.showwarning("Attenzione", "Inserisci la data di emissione.", parent=self)
            return False
        if self.tipo_soggetto_var.get() == "CLIENTE":
            sel = self.cliente_combo.get().strip()
            if not sel or sel.startswith("["):
                messagebox.showwarning("Attenzione", "Seleziona un cliente censito.", parent=self)
                return False
        else:
            if not self.entry_nome.get().strip():
                messagebox.showwarning("Attenzione", "Inserisci il nome del cliente occasionale.", parent=self)
                return False
        return True

    def _cliente_id(self):
        if self.tipo_soggetto_var.get() != "CLIENTE":
            return None
        sel = self.cliente_combo.get().strip()
        if sel and not sel.startswith("["):
            first = sel.split(" - ", 1)[0].strip()
            if first.isdigit():
                return int(first)
        return None

    def _salva(self, stato):
        if not self._valida_campi():
            return False

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cliente_id = self._cliente_id()
            tipo_soggetto = self.tipo_soggetto_var.get()
            data_em = self.entry_data.get().strip()
            metodo = self.combo_pagamento.get()
            note = self.text_note.get("1.0", tk.END).strip()

            imponibile = 0.0
            totale = 0.0
            for r in self.righe:
                t = float(r["totale_riga"] or 0.0)
                a = float(r["aliquota_iva"] or 0.0)
                imponibile += (t / (1 + a / 100.0)) if a > 0 else t
                totale += t

            # Se bozza, non assegniamo numero definitivo
            if stato == "BOZZA":
                numero = f"BOZZA-{self.fattura_id}" if self.fattura_id else "BOZZA-NUOVA"
            else:
                anno_corrente = datetime.now().strftime('%Y')
                cursor.execute("""
                    SELECT ultimo_numero FROM contatori
                    WHERE tipo_documento = 'FATTURA' AND anno = ?
                """, (anno_corrente,))
                row_cnt = cursor.fetchone()
                if row_cnt is None:
                    nuovo_numero = 1
                    cursor.execute("""
                        INSERT INTO contatori (tipo_documento, anno, ultimo_numero)
                        VALUES ('FATTURA', ?, ?)
                    """, (anno_corrente, nuovo_numero))
                else:
                    nuovo_numero = (row_cnt["ultimo_numero"] or 0) + 1
                    cursor.execute("""
                        UPDATE contatori SET ultimo_numero = ?
                        WHERE tipo_documento = 'FATTURA' AND anno = ?
                    """, (nuovo_numero, anno_corrente))
                numero = f"FAT-{anno_corrente}-{nuovo_numero:04d}"

            if self.fattura_id:
                cursor.execute("""
                    UPDATE documenti
                    SET numero = ?, data_emissione = ?, cliente_id = ?,
                        imponibile = ?, totale_documento = ?, pagamento = ?,
                        tipo_soggetto = ?, note = ?, stato_documento = ?
                    WHERE id = ?
                """, (numero, data_em, cliente_id, imponibile, totale, metodo,
                      tipo_soggetto, note, stato, self.fattura_id))
                doc_id = self.fattura_id
                # Elimina vecchie righe e reinserisci
                cursor.execute("DELETE FROM documenti_righe WHERE documento_id = ?", (doc_id,))
            else:
                cursor.execute("""
                    INSERT INTO documenti
                        (tipo_documento, numero, data_emissione, cliente_id,
                         imponibile, totale_documento, stato_xml, pagamento,
                         tipo_soggetto, note, stato_documento)
                    VALUES ('FATTURA', ?, ?, ?, ?, ?, 'PRONTO_SDI', ?, ?, ?, ?)
                """, (numero, data_em, cliente_id, imponibile, totale,
                      metodo, tipo_soggetto, note, stato))
                doc_id = cursor.lastrowid

            for r in self.righe:
                cursor.execute("""
                    INSERT INTO documenti_righe
                        (documento_id, articolo_id, descrizione, quantita,
                         prezzo_unitario, aliquota_iva, totale_riga,
                         sconto_riga, tipo_sconto_riga)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (doc_id, r["articolo_id"], r["descrizione"],
                      r["quantita"], r["prezzo_unitario"], r["aliquota_iva"],
                      r["totale_riga"], r["sconto_riga"], r["tipo_sconto_riga"]))

            conn.commit()
            self.callback and self.callback()
            self.destroy()
            messagebox.showinfo(
                "Successo",
                f"Fattura {numero} salvata con stato: {stato}.",
                parent=self.parent)
            return True
        except Exception as e:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
            log.exception("Errore salvataggio fattura manuale")
            messagebox.showerror("Errore", f"Impossibile salvare la fattura: {e}", parent=self)
            return False
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def salva_bozza(self):
        self._salva("BOZZA")

    def emetti_fattura(self):
        self._salva("EMESSO")