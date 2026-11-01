import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import logging

from database import get_connection

log = logging.getLogger("mercurio.fornitori")

# Colonne del DB che il form gestisce.
# Separate dai campi del form per evitare rotture se il layout cambia.
DB_FIELDS = [
    "ragione_sociale", "partita_iva", "codice_fiscale",
    "indirizzo", "localita", "provincia",
    "pec", "email", "codice_univoco", "iban",
    "istituto_bancario", "metodo_pagamento",
]


class FornitoriManagerFrame(ttk.Notebook):
    """Contenitore a schede per la gestione Fornitori e il Modulo Riordino."""

    def __init__(self, parent):
        super().__init__(parent)

        self.tab_fornitori = FornitoriTab(self)
        self.tab_riordino = RiordinoTab(self)

        self.add(self.tab_fornitori, text="🤝 Anagrafica Fornitori")
        self.add(self.tab_riordino, text="📦 Modulo Riordino Merce")


class FornitoriTab(tk.Frame):
    """Pannello Anagrafica Fornitori con tabella e CRUD."""

    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        self.carica_fornitori()

    def create_widgets(self):
        toolbar = tk.Frame(self, bg="#f8f9fa", padx=5, pady=5)
        toolbar.pack(fill="x", padx=10, pady=5)

        tk.Button(toolbar, text="➕ Nuovo Fornitore", bg="#28a745", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.apri_form_nuovo).pack(side="left", padx=5)

        tk.Button(toolbar, text="✏️ Modifica", bg="#ffc107", fg="black",
                  font=("Arial", 9, "bold"),
                  command=self.apri_form_modifica).pack(side="left", padx=5)

        tk.Button(toolbar, text="🗑️ Elimina", bg="#dc3545", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.elimina_fornitore).pack(side="left", padx=5)

        tk.Button(toolbar, text="🔄 Aggiorna", bg="#6c757d", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.carica_fornitori).pack(side="left", padx=5)

        table_frame = tk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("id", "ragione_sociale", "piva", "localita",
                   "telefono", "pec", "iban", "pagamento")
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("ragione_sociale", text="Ragione Sociale")
        self.tree.heading("piva", text="Partita IVA")
        self.tree.heading("localita", text="Città")
        self.tree.heading("telefono", text="Telefono / Email")
        self.tree.heading("pec", text="PEC")
        self.tree.heading("iban", text="IBAN")
        self.tree.heading("pagamento", text="Pagamento")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("ragione_sociale", width=220, anchor="w")
        self.tree.column("piva", width=110, anchor="center")
        self.tree.column("localita", width=120, anchor="w")
        self.tree.column("telefono", width=150, anchor="w")
        self.tree.column("pec", width=160, anchor="w")
        self.tree.column("iban", width=160, anchor="center")
        self.tree.column("pagamento", width=110, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def carica_fornitori(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ragione_sociale, partita_iva, localita,
                       COALESCE(NULLIF(email, ''), telefono, '') AS contatto,
                       pec, iban, metodo_pagamento
                FROM fornitori
                ORDER BY ragione_sociale ASC
            """)
            rows = cursor.fetchall()

            for row in rows:
                formatted_row = (
                    row[0],
                    row[1],
                    row[2] or "",
                    row[3] or "",
                    row[4] or "",
                    row[5] or "",
                    row[6] or "",
                    row[7] or "",
                )
                self.tree.insert("", "end", values=formatted_row)
        except Exception as e:
            log.exception("Errore caricamento fornitori")
            messagebox.showerror("Errore Database",
                                 f"Impossibile caricare i fornitori: {e}",
                                 parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def apri_form_nuovo(self):
        FornitoreForm(self, mode="nuovo", callback=self.carica_fornitori)

    def apri_form_modifica(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attenzione",
                                   "Seleziona un fornitore da modificare.",
                                   parent=self)
            return
        fornitore_id = self.tree.item(selected[0], "values")[0]
        FornitoreForm(self, mode="modifica", fornitore_id=fornitore_id,
                      callback=self.carica_fornitori)

    def elimina_fornitore(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attenzione",
                                   "Seleziona un fornitore da eliminare.",
                                   parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        fornitore_id = item_values[0]
        ragione_sociale = item_values[1]

        if not messagebox.askyesno(
            "Conferma Eliminazione",
            f"Sei sicuro di voler eliminare il fornitore:\n'{ragione_sociale}'?",
            parent=self,
        ):
            return

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Conta articoli collegati (per evitare FK constraint failure)
            cursor.execute(
                "SELECT COUNT(*) FROM articoli WHERE fornitore_id = ?",
                (fornitore_id,))
            n_articoli = cursor.fetchone()[0] or 0

            if n_articoli > 0:
                messagebox.showwarning(
                    "Impossibile eliminare",
                    f"Il fornitore '{ragione_sociale}' è associato a "
                    f"{n_articoli} articoli.\n"
                    f"Riassegna gli articoli a un altro fornitore prima di "
                    f"procedere con l'eliminazione.",
                    parent=self)
                return

            cursor.execute("DELETE FROM fornitori WHERE id = ?", (fornitore_id,))
            conn.commit()
            messagebox.showinfo("Successo",
                                "Fornitore eliminato con successo.",
                                parent=self)
            self.carica_fornitori()
        except Exception as e:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
            log.exception("Errore eliminazione fornitore id=%s", fornitore_id)
            messagebox.showerror("Errore",
                                 f"Impossibile eliminare il fornitore: {e}",
                                 parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass


class FornitoreForm(tk.Toplevel):
    """Finestra di dialogo per inserimento e modifica anagrafica fornitore."""

    FORM_FIELDS = [
        ("Ragione Sociale *", "ragione_sociale"),
        ("Partita IVA",       "partita_iva"),
        ("Codice Fiscale",    "codice_fiscale"),
        ("Indirizzo e Civico", "indirizzo"),
        ("CAP e Località",    "localita"),
        ("Provincia",         "provincia"),
        ("PEC",               "pec"),
        ("Email",             "email"),
        ("Codice Univoco (SDI)", "codice_univoco"),
        ("IBAN",              "iban"),
        ("Banca / Filiale",   "istituto_bancario"),
        ("Metodo Pagamento",  "metodo_pagamento"),
    ]

    def __init__(self, parent, mode="nuovo", fornitore_id=None, callback=None):
        super().__init__(parent)
        self.mode = mode
        self.fornitore_id = fornitore_id
        self.callback = callback

        self.title("Nuovo Fornitore" if mode == "nuovo" else "Modifica Fornitore")
        self.geometry("500x520")
        self.resizable(False, False)
        self.transient(parent)

        self.create_form()
        if mode == "modifica" and fornitore_id:
            self.carica_dati()

        self.wait_visibility()
        self.grab_set()

    def create_form(self):
        form_frame = tk.Frame(self, padx=15, pady=15)
        form_frame.pack(fill="both", expand=True)
        form_frame.columnconfigure(1, weight=1)

        self.entries = {}
        for idx, (label_text, key) in enumerate(self.FORM_FIELDS):
            tk.Label(form_frame, text=label_text, anchor="w").grid(
                row=idx, column=0, sticky="w", pady=3)
            entry = tk.Entry(form_frame, width=35)
            entry.grid(row=idx, column=1, sticky="ew", pady=3)
            self.entries[key] = entry

        tk.Button(form_frame, text="Salva Fornitore", bg="#28a745",
                  fg="white", font=("Arial", 10, "bold"),
                  command=self.salva).grid(
            row=len(self.FORM_FIELDS), column=0, columnspan=2,
            pady=15, sticky="ew")

    def carica_dati(self):
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cols = ", ".join(DB_FIELDS)
            cursor.execute(f"SELECT {cols} FROM fornitori WHERE id = ?",
                           (self.fornitore_id,))
            row = cursor.fetchone()

            if not row:
                messagebox.showerror("Errore",
                                     "Fornitore non trovato.",
                                     parent=self)
                self.destroy()
                return

            for key, val in zip(DB_FIELDS, row):
                if key not in self.entries:
                    continue
                self.entries[key].delete(0, tk.END)
                self.entries[key].insert(0, "" if val is None else str(val))
        except Exception as e:
            log.exception("Errore caricamento fornitore id=%s", self.fornitore_id)
            messagebox.showerror("Errore",
                                 f"Impossibile caricare il fornitore: {e}",
                                 parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def salva(self):
        ragione_sociale = self.entries["ragione_sociale"].get().strip()
        if not ragione_sociale:
            messagebox.showerror("Errore",
                                 "La Ragione Sociale è obbligatoria!",
                                 parent=self)
            return

        data = {}
        for key in DB_FIELDS:
            if key in self.entries:
                data[key] = self.entries[key].get().strip() or None
        data["ragione_sociale"] = ragione_sociale

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            keys = list(data.keys())
            values = list(data.values())

            if self.mode == "nuovo":
                cols = ", ".join(keys)
                placeholders = ", ".join(["?"] * len(keys))
                cursor.execute(
                    f"INSERT INTO fornitori ({cols}) VALUES ({placeholders})",
                    values)
            else:
                set_clause = ", ".join([f"{key} = ?" for key in keys])
                cursor.execute(
                    f"UPDATE fornitori SET {set_clause} WHERE id = ?",
                    values + [self.fornitore_id])

            conn.commit()
            messagebox.showinfo("Successo", "Fornitore salvato correttamente.",
                                parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
            log.exception("Errore salvataggio fornitore (mode=%s, id=%s)",
                          self.mode, self.fornitore_id)
            messagebox.showerror("Errore",
                                 f"Impossibile salvare il fornitore: {e}",
                                 parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass


class RiordinoTab(tk.Frame):
    """Modulo Riordino Merce: Articoli sotto scorta con associazione fornitore."""

    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        self.carica_articoli_sotto_scorta()

    def create_widgets(self):
        toolbar = tk.Frame(self, bg="#f8f9fa", padx=5, pady=5)
        toolbar.pack(fill="x", padx=10, pady=5)

        tk.Button(toolbar, text="🔄 Aggiorna Report Riordino",
                  bg="#17a2b8", fg="white", font=("Arial", 9, "bold"),
                  command=self.carica_articoli_sotto_scorta).pack(side="left", padx=5)

        tk.Button(toolbar, text="📄 Esporta Ordine (CSV)",
                  bg="#28a745", fg="white", font=("Arial", 9, "bold"),
                  command=self.esporta_ordine).pack(side="left", padx=5)

        table_frame = tk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("id", "ean", "descrizione", "giacenza", "scorta",
                   "da_ordinare", "fornitore", "email_fornitore")
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("ean", text="Codice EAN")
        self.tree.heading("descrizione", text="Descrizione Articolo")
        self.tree.heading("giacenza", text="Giacenza Attuale")
        self.tree.heading("scorta", text="Scorta Minima")
        self.tree.heading("da_ordinare", text="Consiglio Ordine")
        self.tree.heading("fornitore", text="Fornitore Assegnato")
        self.tree.heading("email_fornitore", text="Contatto Fornitore")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("ean", width=110, anchor="center")
        self.tree.column("descrizione", width=250, anchor="w")
        self.tree.column("giacenza", width=90, anchor="center")
        self.tree.column("scorta", width=90, anchor="center")
        self.tree.column("da_ordinare", width=100, anchor="center")
        self.tree.column("fornitore", width=180, anchor="w")
        self.tree.column("email_fornitore", width=150, anchor="w")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def carica_articoli_sotto_scorta(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            # Usa COALESCE(scorta_minima, soglia_minima) per essere robusto
            # qualunque sia la colonna popolata da magazzino.py.
            cursor.execute("""
                SELECT a.id, a.codice_ean, a.descrizione, a.giacenza,
                       COALESCE(a.scorta_minima, a.soglia_minima, 0) AS scorta_eff,
                       COALESCE(f.ragione_sociale, 'Nessun Fornitore') AS fornitore,
                       COALESCE(f.email, f.pec, '-') AS contatto
                FROM articoli a
                LEFT JOIN fornitori f ON a.fornitore_id = f.id
                WHERE a.giacenza <= COALESCE(a.scorta_minima, a.soglia_minima, 0)
                  AND COALESCE(a.scorta_minima, a.soglia_minima, 0) > 0
                ORDER BY a.giacenza ASC
            """)
            rows = cursor.fetchall()

            for row in rows:
                giac = float(row[3] or 0.0)
                scorta = float(row[4] or 0.0)
                da_ordinare = max(0.0, (scorta * 2) - giac)

                formatted_row = (
                    row[0],
                    row[1] or "",
                    row[2],
                    f"{giac:.1f}",
                    f"{scorta:.1f}",
                    f"{da_ordinare:.1f}",
                    row[5],
                    row[6],
                )
                self.tree.insert("", "end", values=formatted_row)
        except Exception as e:
            log.exception("Errore report riordino")
            messagebox.showerror("Errore",
                                 f"Impossibile generare il report di riordino: {e}",
                                 parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def esporta_ordine(self):
        children = self.tree.get_children()
        if not children:
            messagebox.showinfo("Info",
                                "Nessun articolo da ordinare presente nel report.",
                                parent=self)
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("File CSV", "*.csv")],
            title="Esporta Ordine Fornitori",
        )
        if not file_path:
            return

        try:
            with open(file_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["ID", "Codice EAN", "Descrizione",
                                 "Giacenza", "Scorta Minima",
                                 "Consiglio Ordine", "Fornitore", "Contatto"])
                for child in children:
                    writer.writerow(self.tree.item(child, "values"))
            messagebox.showinfo("Successo",
                                f"Ordine esportato con successo in:\n{file_path}",
                                parent=self)
        except Exception as e:
            log.exception("Errore esportazione ordine")
            messagebox.showerror("Errore",
                                 f"Impossibile esportare il file: {e}",
                                 parent=self)