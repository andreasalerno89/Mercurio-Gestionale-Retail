import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime

from database import get_connection

log = logging.getLogger("mercurio.ddt")


class DDTPage(tk.Toplevel):
    """Finestra per emettere un DDT (Documento di Trasporto)."""

    def __init__(self, parent, callback=None):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        self.righe = []
        self.articoli_disponibili = []

        self.title("Emetti DDT (Documento di Trasporto)")
        self.geometry("750x700")
        self.resizable(True, True)
        self.transient(parent)
        self.wait_visibility()
        self.grab_set()

        self.create_widgets()
        self.carica_articoli()

    def create_widgets(self):
        header = tk.Frame(self, padx=15, pady=10)
        header.pack(fill="x")
        tk.Label(header, text="Nuovo DDT (Documento di Trasporto)",
                 font=("Arial", 13, "bold")).pack(anchor="w")
        tk.Label(header,
                 text="Il DDT non è un documento fiscale. Serve per accompagnare la merce.",
                 font=("Arial", 9), fg="#666").pack(anchor="w")

        form = tk.Frame(self, padx=15, pady=5)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        tk.Label(form, text="Destinatario:", font=("Arial", 9, "bold")).grid(
            row=0, column=0, sticky="w", padx=3, pady=2)
        self.cliente_combo = ttk.Combobox(form, state="normal", width=35)
        self.cliente_combo.grid(row=0, column=1, columnspan=3, sticky="ew", padx=3, pady=2)
        self.carica_clienti_combo()

        tk.Label(form, text="Vettore:", font=("Arial", 9, "bold")).grid(
            row=1, column=0, sticky="w", padx=3, pady=2)
        self.entry_vettore = tk.Entry(form, width=35)
        self.entry_vettore.grid(row=1, column=1, columnspan=3, sticky="ew", padx=3, pady=2)

        tk.Label(form, text="Indirizzo consegna:", font=("Arial", 9, "bold")).grid(
            row=2, column=0, sticky="w", padx=3, pady=2)
        self.entry_indirizzo = tk.Entry(form, width=35)
        self.entry_indirizzo.grid(row=2, column=1, columnspan=3, sticky="ew", padx=3, pady=2)

        tk.Label(form, text="CAP:", font=("Arial", 9, "bold")).grid(
            row=3, column=0, sticky="w", padx=3, pady=2)
        self.entry_cap = tk.Entry(form, width=10)
        self.entry_cap.grid(row=3, column=1, sticky="w", padx=3, pady=2)
        tk.Label(form, text="Località:", font=("Arial", 9, "bold")).grid(
            row=3, column=2, sticky="w", padx=3, pady=2)
        self.entry_localita = tk.Entry(form, width=20)
        self.entry_localita.grid(row=3, column=3, sticky="ew", padx=3, pady=2)

        tk.Label(form, text="Provincia:", font=("Arial", 9, "bold")).grid(
            row=4, column=0, sticky="w", padx=3, pady=2)
        self.entry_provincia = tk.Entry(form, width=10)
        self.entry_provincia.grid(row=4, column=1, sticky="w", padx=3, pady=2)

        tk.Label(form, text="Causale trasporto:", font=("Arial", 9, "bold")).grid(
            row=5, column=0, sticky="w", padx=3, pady=2)
        self.combo_causale = ttk.Combobox(
            form,
            values=["Vendita", "Conto visione", "Reso", "Riparazione", "Altro"],
            width=32, state="readonly")
        self.combo_causale.grid(row=5, column=1, columnspan=3, sticky="w", padx=3, pady=2)
        self.combo_causale.set("Vendita")

        tk.Label(form, text="Data ritiro:", font=("Arial", 9, "bold")).grid(
            row=6, column=0, sticky="w", padx=3, pady=2)
        self.entry_data_ritiro = tk.Entry(form, width=15)
        self.entry_data_ritiro.grid(row=6, column=1, sticky="w", padx=3, pady=2)
        self.entry_data_ritiro.insert(0, datetime.now().strftime("%Y-%m-%d"))

        tk.Label(form, text="Aspetto esteriore:", font=("Arial", 9, "bold")).grid(
            row=7, column=0, sticky="w", padx=3, pady=2)
        self.entry_aspetto = tk.Entry(form, width=35)
        self.entry_aspetto.grid(row=7, column=1, columnspan=3, sticky="ew", padx=3, pady=2)
        self.entry_aspetto.insert(0, "Colli")

        tk.Label(self, text="Articoli da includere nel DDT:",
                 font=("Arial", 10, "bold"), padx=15).pack(anchor="w", pady=(10, 0))

        art_frame = tk.Frame(self, padx=15, pady=5)
        art_frame.pack(fill="x")
        tk.Label(art_frame, text="Aggiungi articolo:", font=("Arial", 9)).pack(side="left")
        self.art_combo = ttk.Combobox(art_frame, state="readonly", width=45)
        self.art_combo.pack(side="left", padx=5)
        tk.Button(art_frame, text="➕ Aggiungi", bg="#007bff", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.aggiungi_articolo).pack(side="left", padx=5)

        qta_frame = tk.Frame(art_frame)
        qta_frame.pack(side="left", padx=5)
        tk.Label(qta_frame, text="Q.tà:", font=("Arial", 9)).pack(side="left")
        self.qta_entry = tk.Entry(qta_frame, width=8)
        self.qta_entry.pack(side="left")
        self.qta_entry.insert(0, "1")

        table_frame = tk.Frame(self, padx=15, pady=5)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "descrizione", "quantita", "prezzo", "totale")
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", selectmode="browse", height=8)
        self.tree.heading("id", text="ID")
        self.tree.heading("descrizione", text="Descrizione")
        self.tree.heading("quantita", text="Q.tà")
        self.tree.heading("prezzo", text="P. Unit.")
        self.tree.heading("totale", text="Totale")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("descrizione", width=350, anchor="w")
        self.tree.column("quantita", width=70, anchor="center")
        self.tree.column("prezzo", width=90, anchor="e")
        self.tree.column("totale", width=90, anchor="e")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        btn_riga = tk.Frame(self, padx=15, pady=5)
        btn_riga.pack(fill="x")
        tk.Button(btn_riga, text="Rimuovi riga selezionata", bg="#dc3545",
                  fg="white", font=("Arial", 9, "bold"),
                  command=self.rimuovi_riga).pack(side="left")

        self.lbl_totale = tk.Label(self, text="Totale indicativo DDT: € 0.00",
                                   font=("Arial", 12, "bold"), fg="#6c757d")
        self.lbl_totale.pack(pady=5)

        actions = tk.Frame(self, padx=15, pady=10)
        actions.pack(fill="x")
        tk.Button(actions, text="Annulla", bg="#6c757d", fg="white",
                  font=("Arial", 10, "bold"),
                  command=self.destroy).pack(side="right", padx=5)
        tk.Button(actions, text="Emetti DDT", bg="#e83e8c", fg="white",
                  font=("Arial", 10, "bold"),
                  command=self.conferma).pack(side="right", padx=5)

    def carica_clienti_combo(self):
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ragione_sociale, indirizzo, cap, localita, provincia
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
            self.cliente_combo.set(values[0])
            self.cliente_combo.bind("<<ComboboxSelected>>", self.on_cliente_change)
        except Exception as e:
            log.exception("Errore caricamento clienti per DDT")
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def on_cliente_change(self, event=None):
        sel = self.cliente_combo.get().strip()
        if not sel or sel.startswith("["):
            return
        first = sel.split(" - ", 1)[0].strip()
        if first.isdigit():
            cid = int(first)
            if cid in self.clienti_data:
                c = self.clienti_data[cid]
                self.entry_indirizzo.delete(0, tk.END)
                self.entry_indirizzo.insert(0, c.get("indirizzo") or "")
                self.entry_cap.delete(0, tk.END)
                self.entry_cap.insert(0, c.get("cap") or "")
                self.entry_localita.delete(0, tk.END)
                self.entry_localita.insert(0, c.get("localita") or "")
                self.entry_provincia.delete(0, tk.END)
                self.entry_provincia.insert(0, c.get("provincia") or "")

    def carica_articoli(self):
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, descrizione, prezzo_vendita, giacenza
                FROM articoli ORDER BY descrizione ASC
            """)
            self.articoli_disponibili = [dict(r) for r in cursor.fetchall()]
            values = [f"{a['id']} - {a['descrizione']} (€{a['prezzo_vendita']:.2f})"
                      for a in self.articoli_disponibili]
            self.art_combo['values'] = values
            if values:
                self.art_combo.current(0)
        except Exception as e:
            log.exception("Errore caricamento articoli per DDT")
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def aggiungi_articolo(self):
        sel = self.art_combo.get().strip()
        if not sel:
            return
        first = sel.split(" - ", 1)[0].strip()
        if not first.isdigit():
            return
        aid = int(first)
        try:
            qta = float(self.qta_entry.get().replace(",", ".").strip() or 0)
        except ValueError:
            messagebox.showerror("Errore", "Quantità non valida.", parent=self)
            return
        if qta <= 0:
            messagebox.showerror("Errore", "Quantità deve essere > 0.", parent=self)
            return

        art = next((a for a in self.articoli_disponibili if a['id'] == aid), None)
        if not art:
            return

        riga = {
            "articolo_id": aid,
            "descrizione": art['descrizione'],
            "quantita": qta,
            "prezzo_unitario": float(art['prezzo_vendita'] or 0.0),
            "totale_riga": qta * float(art['prezzo_vendita'] or 0.0),
        }
        self.righe.append(riga)
        self.aggiorna_tree()

    def rimuovi_riga(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        if 0 <= idx < len(self.righe):
            del self.righe[idx]
            self.aggiorna_tree()

    def aggiorna_tree(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        totale = 0.0
        for riga in self.righe:
            totale += riga["totale_riga"]
            self.tree.insert("", "end", values=(
                riga["articolo_id"],
                riga["descrizione"],
                f"{riga['quantita']:.2f}",
                f"€ {riga['prezzo_unitario']:.2f}",
                f"€ {riga['totale_riga']:.2f}",
            ))
        self.lbl_totale.config(text=f"Totale indicativo DDT: € {totale:.2f}")

    def conferma(self):
        if not self.righe:
            messagebox.showwarning("Attenzione",
                                   "Aggiungi almeno un articolo al DDT.",
                                   parent=self)
            return

        cliente_sel = self.cliente_combo.get().strip()
        cliente_id = None
        if cliente_sel and not cliente_sel.startswith("["):
            first = cliente_sel.split(" - ", 1)[0].strip()
            if first.isdigit():
                cliente_id = int(first)

        vettore = self.entry_vettore.get().strip()
        indirizzo = self.entry_indirizzo.get().strip()
        cap = self.entry_cap.get().strip()
        localita = self.entry_localita.get().strip()
        provincia = self.entry_provincia.get().strip()
        causale = self.combo_causale.get().strip()
        data_ritiro = self.entry_data_ritiro.get().strip()
        aspetto = self.entry_aspetto.get().strip()

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            anno_corrente = datetime.now().strftime('%Y')
            cursor.execute("""
                SELECT ultimo_numero FROM contatori
                WHERE tipo_documento = 'DDT' AND anno = ?
            """, (anno_corrente,))
            row_cnt = cursor.fetchone()
            if row_cnt is None:
                nuovo_numero = 1
                cursor.execute("""
                    INSERT INTO contatori (tipo_documento, anno, ultimo_numero)
                    VALUES ('DDT', ?, ?)
                """, (anno_corrente, nuovo_numero))
            else:
                nuovo_numero = (row_cnt["ultimo_numero"] or 0) + 1
                cursor.execute("""
                    UPDATE contatori SET ultimo_numero = ?
                    WHERE tipo_documento = 'DDT' AND anno = ?
                """, (nuovo_numero, anno_corrente))
            numero_ddt = f"DDT-{anno_corrente}-{nuovo_numero:04d}"

            totale = sum(r["totale_riga"] for r in self.righe)
            imponibile = totale / 1.22

            cursor.execute("""
                INSERT INTO documenti
                    (tipo_documento, numero, data_emissione, cliente_id,
                     imponibile, totale_documento, stato_xml, pagamento,
                     tipo_soggetto, stato_documento)
                VALUES ('DDT', ?, ?, ?, ?, ?, 'EMESSO', NULL, 'CLIENTE', 'EMESSO')
            """, (numero_ddt, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  cliente_id, imponibile, totale))
            doc_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO ddt_dati
                    (documento_id, vettore, destinatario_indirizzo,
                     destinatario_cap, destinatario_localita,
                     destinatario_provincia, causale_trasporto,
                     data_ritiro, aspettativa)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (doc_id, vettore, indirizzo, cap, localita, provincia,
                  causale, data_ritiro, aspetto))

            for riga in self.righe:
                cursor.execute("""
                    INSERT INTO documenti_righe
                        (documento_id, articolo_id, descrizione, quantita,
                         prezzo_unitario, aliquota_iva, totale_riga,
                         sconto_riga, tipo_sconto_riga)
                    VALUES (?, ?, ?, ?, ?, 22.0, ?, 0.0, '%')
                """, (doc_id, riga["articolo_id"], riga["descrizione"],
                      riga["quantita"], riga["prezzo_unitario"],
                      riga["totale_riga"]))

            conn.commit()
            self.callback and self.callback()
            self.destroy()
            messagebox.showinfo(
                "DDT Emesso",
                f"DDT {numero_ddt} emesso con successo.\n"
                f"Righe: {len(self.righe)}\n"
                f"Totale indicativo: € {totale:.2f}",
                parent=self.parent)
        except Exception as e:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
            log.exception("Errore emissione DDT")
            messagebox.showerror("Errore",
                                 f"Impossibile emettere il DDT: {e}",
                                 parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass