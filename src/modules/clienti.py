import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import logging

from database import get_connection

log = logging.getLogger("mercurio.clienti")

# Colonne del database che il form gestisce direttamente.
# Tenute separate dai campi del form per evitare che aggiunte future
# al layout (es. campi calcolati o campi non persistiti) rompano la SELECT.
DB_FIELDS = [
    "ragione_sociale", "codice_fiscale", "partita_iva",
    "indirizzo", "localita", "provincia",
    "email", "telefono", "punti_fidelity",
]


class ClientiManagerTab(tk.Frame):
    """Pannello Anagrafica Clienti e Fidelity avanzato con ricerca e export."""

    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        self.carica_clienti()

    def create_widgets(self):
        # 1. Barra superiore degli strumenti e ricerca rapida
        toolbar = tk.Frame(self, bg="#f8f9fa", padx=5, pady=8)
        toolbar.pack(fill="x", padx=10, pady=5)

        tk.Button(toolbar, text="➕ Nuovo Cliente", bg="#28a745", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.apri_form_nuovo).pack(side="left", padx=3)

        tk.Button(toolbar, text="✏️ Modifica", bg="#ffc107", fg="black",
                  font=("Arial", 9, "bold"),
                  command=self.apri_form_modifica).pack(side="left", padx=3)

        tk.Button(toolbar, text="🗑️ Elimina", bg="#dc3545", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.elimina_cliente).pack(side="left", padx=3)

        tk.Button(toolbar, text="📤 Esporta CSV", bg="#17a2b8", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.esporta_csv).pack(side="left", padx=3)

        tk.Button(toolbar, text="🔄 Aggiorna", bg="#6c757d", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.carica_clienti).pack(side="right", padx=3)

        # Barra di Ricerca rapida per Nome, Codice Fiscale o Partita IVA
        search_frame = tk.Frame(self, padx=10, pady=3)
        search_frame.pack(fill="x")

        tk.Label(search_frame, text="Cerca Cliente (Nome / CF / P.IVA):",
                 font=("Arial", 9)).pack(side="left", padx=2)
        self.search_entry = tk.Entry(search_frame, width=30, font=("Arial", 10))
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self.filtra_clienti)

        # 2. Tabella / Treeview Clienti
        table_frame = tk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("id", "ragione_sociale", "codice_fiscale", "piva",
                   "email", "telefono", "punti_fidelity")
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", selectmode="browse")
        self.tree.bind("<Double-1>", self.apri_form_modifica)

        self.tree.heading("id", text="ID")
        self.tree.heading("ragione_sociale", text="Cliente / Denominazione")
        self.tree.heading("codice_fiscale", text="Codice Fiscale")
        self.tree.heading("piva", text="Partita IVA")
        self.tree.heading("email", text="Email")
        self.tree.heading("telefono", text="Telefono")
        self.tree.heading("punti_fidelity", text="Punti Fidelity")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("ragione_sociale", width=220, anchor="w")
        self.tree.column("codice_fiscale", width=140, anchor="center")
        self.tree.column("piva", width=110, anchor="center")
        self.tree.column("email", width=160, anchor="w")
        self.tree.column("telefono", width=110, anchor="center")
        self.tree.column("punti_fidelity", width=90, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ------------------------------------------------------------------ #
    # Caricamento e filtro
    # ------------------------------------------------------------------ #

    def carica_clienti(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ragione_sociale, codice_fiscale, partita_iva,
                       email, telefono, punti_fidelity
                FROM clienti ORDER BY ragione_sociale ASC
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
                    f"{row[6]:.1f}",
                )
                self.tree.insert("", "end", values=formatted_row)
        except Exception as e:
            log.exception("Errore nel caricamento clienti")
            messagebox.showerror("Errore Database",
                                 f"Impossibile caricare i clienti: {e}")
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def filtra_clienti(self, event=None):
        query = self.search_entry.get().strip().lower()
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ragione_sociale, codice_fiscale, partita_iva,
                       email, telefono, punti_fidelity
                FROM clienti
                WHERE LOWER(ragione_sociale) LIKE ?
                   OR LOWER(COALESCE(codice_fiscale, '')) LIKE ?
                   OR LOWER(COALESCE(partita_iva, '')) LIKE ?
                ORDER BY ragione_sociale ASC
            """, (f"%{query}%", f"%{query}%", f"%{query}%"))
            rows = cursor.fetchall()

            for row in rows:
                formatted_row = (
                    row[0], row[1], row[2] or "", row[3] or "",
                    row[4] or "", row[5] or "", f"{row[6]:.1f}",
                )
                self.tree.insert("", "end", values=formatted_row)
        except Exception as e:
            # Non è un errore "da popup": log e lista vuota sono sufficienti.
            log.exception("Errore nel filtro clienti (query=%r)", query)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    # ------------------------------------------------------------------ #
    # Azioni utente
    # ------------------------------------------------------------------ #

    def apri_form_nuovo(self):
        ClienteForm(self, mode="nuovo", callback=self.carica_clienti)

    def apri_form_modifica(self, event=None):
        selected = self.tree.selection()
        if not selected:
            # Se è un doppio clic su area vuota, ignora silenziosamente.
            if event is not None:
                return
            messagebox.showwarning("Attenzione",
                                   "Seleziona un cliente da modificare.")
            return
        cliente_id = self.tree.item(selected[0], "values")[0]
        ClienteForm(self, mode="modifica", cliente_id=cliente_id,
                    callback=self.carica_clienti)

    def elimina_cliente(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attenzione",
                                   "Seleziona un cliente da eliminare.")
            return
        item_values = self.tree.item(selected[0], "values")
        cliente_id = item_values[0]
        nome = item_values[1]

        if not messagebox.askyesno(
            "Conferma Eliminazione",
            f"Sei sicuro di voler eliminare il cliente:\n'{nome}'?",
        ):
            return

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clienti WHERE id = ?", (cliente_id,))
            conn.commit()
            messagebox.showinfo("Successo", "Cliente eliminato con successo.")
            self.carica_clienti()
        except Exception as e:
            log.exception("Errore eliminazione cliente id=%s", cliente_id)
            messagebox.showerror("Errore",
                                 f"Impossibile eliminare il cliente: {e}")
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def esporta_csv(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Esporta Clienti in CSV",
        )
        if not file_path:
            return

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ragione_sociale, codice_fiscale, partita_iva,
                       indirizzo, localita, provincia, email, telefono,
                       punti_fidelity
                FROM clienti
            """)
            rows = cursor.fetchall()

            with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow([
                    "Denominazione", "Codice Fiscale", "Partita IVA",
                    "Indirizzo", "Città", "Provincia", "Email",
                    "Telefono", "Punti Fidelity",
                ])
                writer.writerows(rows)

            messagebox.showinfo(
                "Esportazione Riuscita",
                f"Elenco clienti esportato correttamente in:\n{file_path}",
                parent=self,
            )
        except Exception as e:
            log.exception("Errore esportazione CSV clienti")
            messagebox.showerror("Errore",
                                 f"Impossibile esportare il file: {e}",
                                 parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass


class ClienteForm(tk.Toplevel):
    """Finestra di dialogo inserimento/modifica cliente."""

    # Campi mostrati nel form e relativa colonna DB.
    # "punti_fidelity" è gestito a parte (validazione numerica).
    FORM_FIELDS = [
        ("Denominazione / Nome *", "ragione_sociale"),
        ("Codice Fiscale",         "codice_fiscale"),
        ("Partita IVA",            "partita_iva"),
        ("Indirizzo",              "indirizzo"),
        ("CAP e Città",            "localita"),
        ("Provincia",              "provincia"),
        ("Email",                  "email"),
        ("Telefono",               "telefono"),
        ("Punti Fidelity",         "punti_fidelity"),
    ]

    def __init__(self, parent, mode="nuovo", cliente_id=None, callback=None):
        super().__init__(parent)
        self.mode = mode
        self.cliente_id = cliente_id
        self.callback = callback
        # Snapshot dei valori caricati, per capire cosa l'utente ha cambiato.
        self._original = {}

        self.title("Nuovo Cliente" if mode == "nuovo" else "Modifica Cliente")
        self.geometry("480x480")
        self.resizable(False, False)
        self.transient(parent)

        self.create_form()
        if mode == "modifica" and cliente_id:
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
            entry = tk.Entry(form_frame, width=30, font=("Arial", 10))
            entry.grid(row=idx, column=1, sticky="ew", pady=3)
            self.entries[key] = entry

        # Default solo in modalità nuovo; in modifica il valore arriva dal DB.
        if self.mode == "nuovo":
            self.entries["punti_fidelity"].insert(0, "0.0")

        tk.Button(form_frame, text="Salva Cliente", bg="#28a745", fg="white",
                  font=("Arial", 10, "bold"),
                  command=self.salva).grid(
            row=len(self.FORM_FIELDS), column=0, columnspan=2,
            pady=15, sticky="ew")

    def carica_dati(self):
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cols = ", ".join(DB_FIELDS)
            cursor.execute(f"SELECT {cols} FROM clienti WHERE id = ?",
                           (self.cliente_id,))
            row = cursor.fetchone()
            if not row:
                messagebox.showerror("Errore",
                                     "Cliente non trovato.",
                                     parent=self)
                self.destroy()
                return

            for key, val in zip(DB_FIELDS, row):
                if key not in self.entries:
                    continue
                str_val = "" if val is None else str(val)
                self.entries[key].delete(0, tk.END)
                self.entries[key].insert(0, str_val)
                self._original[key] = str_val
        except Exception as e:
            log.exception("Errore caricamento cliente id=%s", self.cliente_id)
            messagebox.showerror("Errore",
                                 f"Impossibile caricare il cliente: {e}",
                                 parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def salva(self):
        nome = self.entries["ragione_sociale"].get().strip()
        if not nome:
            messagebox.showerror(
                "Errore",
                "La denominazione o il nome del cliente sono obbligatori!",
                parent=self)
            return

        # Validazione esplicita dei punti fidelity
        punti_raw = self.entries["punti_fidelity"].get().strip().replace(",", ".")
        try:
            punti_val = float(punti_raw) if punti_raw else 0.0
        except ValueError:
            messagebox.showerror(
                "Errore",
                "I punti fidelity devono essere un numero (es. 12.5).",
                parent=self)
            return

        # Costruisci il dizionario solo con le colonne DB effettive
        data = {}
        for key in DB_FIELDS:
            if key == "punti_fidelity":
                data[key] = punti_val
            elif key in self.entries:
                data[key] = self.entries[key].get().strip() or None
        data["ragione_sociale"] = nome

        # In modifica, se i punti non sono cambiati, escludili dall'UPDATE
        # per evitare di sovrascrivere eventuali accrediti avvenuti nel
        # frattempo (es. dal POS).
        if self.mode == "modifica":
            original_punti = self._original.get("punti_fidelity", "")
            try:
                original_val = float(original_punti) if original_punti else 0.0
            except ValueError:
                original_val = 0.0
            if abs(original_val - punti_val) < 1e-9:
                data.pop("punti_fidelity", None)

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            if self.mode == "nuovo":
                keys = list(data.keys())
                cols = ", ".join(keys)
                placeholders = ", ".join(["?"] * len(keys))
                cursor.execute(
                    f"INSERT INTO clienti ({cols}) VALUES ({placeholders})",
                    list(data.values()))
            else:
                keys = list(data.keys())
                set_clause = ", ".join([f"{key} = ?" for key in keys])
                cursor.execute(
                    f"UPDATE clienti SET {set_clause} WHERE id = ?",
                    list(data.values()) + [self.cliente_id])

            conn.commit()
            messagebox.showinfo("Successo", "Cliente salvato correttamente.",
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
            log.exception("Errore salvataggio cliente (mode=%s, id=%s)",
                          self.mode, self.cliente_id)
            messagebox.showerror("Errore",
                                 f"Impossibile salvare il cliente: {e}",
                                 parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass