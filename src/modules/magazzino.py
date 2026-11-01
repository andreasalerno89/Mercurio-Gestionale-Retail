import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import logging

from database import get_connection

log = logging.getLogger("mercurio.magazzino")

# Campi numerici float del form
FIELDS_FLOAT = [
    "peso_netto", "peso_lordo",
    "prezzo_acquisto_netto", "prezzo_acquisto_ivato",
    "prezzo_vendita_netto", "prezzo_vendita",
    "giacenza", "soglia_minima",
]

# Campi del form (ordine di visualizzazione)
FIELDS_FORM = [
    ("Codice Interno", "codice_interno"),
    ("Codice EAN / Barcode", "codice_ean"),
    ("Descrizione Articolo *", "descrizione"),
    ("Categoria", "categoria"),
    ("Unità di Misura (pz, kg, mt, lt)", "unita_misura"),
    ("Peso Netto (kg)", "peso_netto"),
    ("Peso Lordo (kg)", "peso_lordo"),
    ("Prezzo Acquisto Netto (€)", "prezzo_acquisto_netto"),
    ("Prezzo Acquisto Ivato (€)", "prezzo_acquisto_ivato"),
    ("Prezzo Vendita Netto (€)", "prezzo_vendita_netto"),
    ("Prezzo Vendita Ivato * (€)", "prezzo_vendita"),
    ("Aliquota IVA", "aliquota_iva"),
    ("Giacenza Iniziale", "giacenza"),
    ("Soglia Minima Scorta", "soglia_minima"),
    ("Percorso Foto Articolo", "foto_path"),
]


class MagazzinoFrame(tk.Frame):
    """Modulo di gestione Magazzino avanzato."""

    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        self.carica_articoli()

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #

    def create_widgets(self):
        top_frame = tk.Frame(self, padx=10, pady=10)
        top_frame.pack(fill="x")

        tk.Label(top_frame,
                 text="📦 Gestione Magazzino & Articoli (Ecosistema Avanzato)",
                 font=("Arial", 12, "bold")).pack(side="left")

        tk.Button(top_frame, text="➕ Nuovo Articolo", bg="#28a745", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.apri_finestra_articolo).pack(side="right", padx=3)

        tk.Button(top_frame, text="🔄 Carico/Scarico Libero",
                  bg="#17a2b8", fg="white", font=("Arial", 9, "bold"),
                  command=self.apri_finestra_movimento).pack(side="right", padx=3)

        tk.Button(top_frame, text="📥 Importa CSV", bg="#ffc107", fg="black",
                  font=("Arial", 9, "bold"),
                  command=self.importa_csv).pack(side="right", padx=3)

        tk.Button(top_frame, text="📤 Esporta CSV", bg="#6c757d", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.esporta_csv).pack(side="right", padx=3)

        # Barra di Ricerca
        search_frame = tk.Frame(self, padx=10, pady=2)
        search_frame.pack(fill="x")

        tk.Label(search_frame, text="Cerca (Codice, EAN o Nome):",
                 font=("Arial", 9)).pack(side="left", padx=2)
        self.search_entry = tk.Entry(search_frame, width=30, font=("Arial", 10))
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self.filtra_articoli)

        tk.Button(search_frame, text="🔄 Aggiorna", bg="#ffc107", fg="black",
                  font=("Arial", 9, "bold"),
                  command=self.carica_articoli).pack(side="left", padx=5)

        # Tabella Articoli
        table_frame = tk.Frame(self, padx=10, pady=5)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "cod_int", "barcode", "descrizione", "categoria",
                   "um", "p_vend_ivato", "giacenza", "soglia")
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", selectmode="browse")
        self.tree.bind("<Double-1>", self.modifica_articolo_selezionato)

        for col, label in [
            ("id", "ID"), ("cod_int", "Cod. Interno"),
            ("barcode", "Codice EAN"), ("descrizione", "Descrizione Articolo"),
            ("categoria", "Categoria"), ("um", "U.M."),
            ("p_vend_ivato", "Prezzo Ivato (€)"),
            ("giacenza", "Giacenza"), ("soglia", "Soglia Min"),
        ]:
            self.tree.heading(col, text=label)

        self.tree.column("id", width=35, anchor="center")
        self.tree.column("cod_int", width=90, anchor="center")
        self.tree.column("barcode", width=95, anchor="center")
        self.tree.column("descrizione", width=220, anchor="w")
        self.tree.column("categoria", width=90, anchor="w")
        self.tree.column("um", width=45, anchor="center")
        self.tree.column("p_vend_ivato", width=90, anchor="e")
        self.tree.column("giacenza", width=65, anchor="center")
        self.tree.column("soglia", width=65, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        bottom_toolbar = tk.Frame(self, padx=10, pady=8)
        bottom_toolbar.pack(fill="x")

        tk.Button(bottom_toolbar, text="✏️ Modifica Selezionato",
                  bg="#ffc107", fg="black", font=("Arial", 9, "bold"),
                  command=self.modifica_articolo_selezionato).pack(side="left", padx=2)
        tk.Button(bottom_toolbar, text="🗑️ Elimina Articolo",
                  bg="#dc3545", fg="white", font=("Arial", 9, "bold"),
                  command=self.elimina_articolo).pack(side="left", padx=2)

    # ------------------------------------------------------------------ #
    # Caricamento
    # ------------------------------------------------------------------ #

    def _riga_formattata(self, r):
        return (
            r[0],
            r[1] or f"ART-{r[0]:04d}",
            r[2] or "",
            r[3],
            r[4] or "",
            r[5] or "pz",
            f"€ {r[6]:.2f}" if r[6] else "€ 0.00",
            f"{r[7]:.2f}" if r[7] is not None else "0.00",
            f"{r[8]:.2f}" if r[8] is not None else "0.00",
        )

    def carica_articoli(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, codice_interno, codice_ean, descrizione,
                       categoria, unita_misura, prezzo_vendita,
                       giacenza, soglia_minima
                FROM articoli ORDER BY descrizione ASC
            """)
            rows = cursor.fetchall()
            for r in rows:
                self.tree.insert("", "end", values=self._riga_formattata(r))
        except Exception as e:
            log.exception("Errore caricamento magazzino")
            messagebox.showerror("Errore",
                                 f"Impossibile caricare il magazzino: {e}",
                                 parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def filtra_articoli(self, event=None):
        query = self.search_entry.get().strip().lower()
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, codice_interno, codice_ean, descrizione,
                       categoria, unita_misura, prezzo_vendita,
                       giacenza, soglia_minima
                FROM articoli
                WHERE LOWER(descrizione) LIKE ?
                   OR LOWER(COALESCE(codice_ean, '')) LIKE ?
                   OR LOWER(COALESCE(codice_interno, '')) LIKE ?
                ORDER BY descrizione ASC
            """, (f"%{query}%", f"%{query}%", f"%{query}%"))
            rows = cursor.fetchall()
            for r in rows:
                self.tree.insert("", "end", values=self._riga_formattata(r))
        except Exception:
            log.exception("Errore filtro magazzino (query=%r)", query)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    # ------------------------------------------------------------------ #
    # Scheda articolo
    # ------------------------------------------------------------------ #

    def apri_finestra_articolo(self, articolo_id=None):
        dialog = tk.Toplevel(self)
        dialog.title("Scheda Articolo Avanzata")
        dialog.geometry("500x620")
        dialog.transient(self)
        dialog.grab_set()

        form_frame = tk.Frame(dialog, padx=15, pady=15)
        form_frame.pack(fill="both", expand=True)
        form_frame.columnconfigure(1, weight=1)

        entries = {}
        for idx, (lbl, key) in enumerate(FIELDS_FORM):
            tk.Label(form_frame, text=lbl,
                     font=("Arial", 9, "bold")).grid(
                row=idx, column=0, sticky="w", pady=2)
            if key == "aliquota_iva":
                widget = ttk.Combobox(form_frame,
                                      values=["22%", "10%", "5%", "4%", "Esente"],
                                      width=28, state="readonly")
                widget.set("22%")
            elif key == "unita_misura":
                widget = ttk.Combobox(form_frame,
                                      values=["pz", "kg", "mt", "lt"],
                                      width=28, state="readonly")
                widget.set("pz")
            else:
                widget = tk.Entry(form_frame, width=30, font=("Arial", 9))
            widget.grid(row=idx, column=1, sticky="ew", pady=2)
            entries[key] = widget

        # Caricamento in modifica
        if articolo_id:
            conn = None
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT codice_interno, codice_ean, descrizione, categoria,
                           unita_misura, peso_netto, peso_lordo,
                           prezzo_acquisto_netto, prezzo_acquisto_ivato,
                           prezzo_vendita_netto, prezzo_vendita, aliquota_iva,
                           giacenza, soglia_minima, foto_path
                    FROM articoli WHERE id = ?
                """, (articolo_id,))
                art_data = cursor.fetchone()

                if not art_data:
                    messagebox.showerror("Errore", "Articolo non trovato.",
                                         parent=dialog)
                    dialog.destroy()
                    return

                keys = [k for _, k in FIELDS_FORM]
                for key, val in zip(keys, art_data):
                    w = entries[key]
                    if isinstance(w, ttk.Combobox):
                        w.set(str(val if val is not None else ""))
                    else:
                        w.delete(0, tk.END)
                        w.insert(0, str(val if val is not None else ""))
            except Exception as e:
                log.exception("Errore caricamento articolo id=%s", articolo_id)
                messagebox.showerror("Errore",
                                     f"Impossibile caricare l'articolo: {e}",
                                     parent=dialog)
                dialog.destroy()
                return
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except Exception:
                        pass
        else:
            entries["giacenza"].insert(0, "0.0")
            entries["soglia_minima"].insert(0, "5.0")

        def salva():
            data = {}
            try:
                for k, w in entries.items():
                    raw = w.get().strip()
                    if k in FIELDS_FLOAT:
                        data[k] = float(raw.replace(",", ".") or 0.0)
                    else:
                        data[k] = raw or None

                if not data.get("descrizione"):
                    messagebox.showerror(
                        "Errore",
                        "La Descrizione Articolo è obbligatoria.",
                        parent=dialog)
                    return

                if data.get("prezzo_vendita", 0) < 0:
                    messagebox.showerror(
                        "Errore",
                        "Il Prezzo Vendita Ivato non può essere negativo.",
                        parent=dialog)
                    return
            except ValueError:
                messagebox.showerror(
                    "Errore",
                    "Controlla che i campi numerici siano corretti.",
                    parent=dialog)
                return

            conn = None
            try:
                conn = get_connection()
                cursor = conn.cursor()

                keys = list(data.keys())
                values = list(data.values())

                if articolo_id:
                    set_clause = ", ".join([f"{k} = ?" for k in keys])
                    cursor.execute(
                        f"UPDATE articoli SET {set_clause} WHERE id = ?",
                        values + [articolo_id])
                else:
                    cols = ", ".join(keys)
                    placeholders = ", ".join(["?"] * len(keys))
                    cursor.execute(
                        f"INSERT INTO articoli ({cols}) VALUES ({placeholders})",
                        values)

                conn.commit()
                self.carica_articoli()
                dialog.destroy()
                messagebox.showinfo("Successo",
                                    "Articolo salvato correttamente nel magazzino.",
                                    parent=self)
            except Exception as e:
                if conn is not None:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                log.exception("Errore salvataggio articolo (id=%s)",
                              articolo_id)
                messagebox.showerror(
                    "Errore",
                    f"Impossibile salvare l'articolo: {e}",
                    parent=dialog)
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except Exception:
                        pass

        tk.Button(form_frame, text="Salva Articolo", bg="#28a745",
                  fg="white", font=("Arial", 10, "bold"),
                  command=salva).grid(
            row=len(FIELDS_FORM), column=0, columnspan=2,
            pady=15, sticky="ew")

    def modifica_articolo_selezionato(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        item_values = self.tree.item(selected[0], "values")
        try:
            art_id = int(item_values[0])
        except (ValueError, IndexError):
            return
        self.apri_finestra_articolo(art_id)

    def elimina_articolo(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attenzione",
                                   "Seleziona un articolo da eliminare.",
                                   parent=self)
            return

        item_values = self.tree.item(selected[0], "values")
        art_id = item_values[0]
        desc = item_values[3]

        if not messagebox.askyesno(
            "Conferma Eliminazione",
            f"Sei sicuro di voler eliminare l'articolo '{desc}'?",
            parent=self,
        ):
            return

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM articoli WHERE id = ?", (art_id,))
            conn.commit()
            self.carica_articoli()
            messagebox.showinfo("Eliminato",
                                "Articolo eliminato con successo.",
                                parent=self)
        except Exception as e:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
            log.exception("Errore eliminazione articolo id=%s", art_id)
            messagebox.showerror("Errore",
                                 f"Impossibile eliminare l'articolo: {e}",
                                 parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    # ------------------------------------------------------------------ #
    # Movimento magazzino
    # ------------------------------------------------------------------ #

    def apri_finestra_movimento(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "Attenzione",
                "Seleziona un articolo dalla tabella per registrare un movimento.",
                parent=self)
            return

        item_values = self.tree.item(selected[0], "values")
        art_id = item_values[0]
        desc = item_values[3]

        dialog = tk.Toplevel(self)
        dialog.title(f"Movimento Magazzino: {desc}")
        dialog.geometry("380x320")
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text=f"Articolo: {desc}",
                 font=("Arial", 10, "bold"), wraplength=340).pack(pady=10)

        tk.Label(dialog, text="Tipo Movimento:", font=("Arial", 9)).pack(anchor="w", padx=20)
        combo_tipo = ttk.Combobox(dialog, values=["CARICO", "SCARICO", "RETTIFICA"],
                                  state="readonly", width=25)
        combo_tipo.pack(padx=20, pady=2)
        combo_tipo.set("CARICO")

        tk.Label(dialog, text="Quantità:", font=("Arial", 9)).pack(anchor="w", padx=20)
        qta_entry = tk.Entry(dialog, width=28, font=("Arial", 10))
        qta_entry.pack(padx=20, pady=2)
        qta_entry.insert(0, "1")

        tk.Label(dialog, text="Causale / Riferimento:", font=("Arial", 9)).pack(anchor="w", padx=20)
        causale_entry = tk.Entry(dialog, width=28, font=("Arial", 10))
        causale_entry.pack(padx=20, pady=2)
        causale_entry.insert(0, "Carico manuale libero")

        def conferma_movimento():
            try:
                tipo = combo_tipo.get()
                qta = float(qta_entry.get().replace(",", ".").strip())
                causale = causale_entry.get().strip()
            except ValueError:
                messagebox.showerror("Errore",
                                     "Inserisci una quantità numerica valida.",
                                     parent=dialog)
                return

            if qta < 0:
                messagebox.showerror("Errore",
                                     "La quantità non può essere negativa.",
                                     parent=dialog)
                return
            if tipo in ("CARICO", "SCARICO") and qta <= 0:
                messagebox.showerror(
                    "Errore",
                    "Per CARICO e SCARICO la quantità deve essere maggiore di 0.",
                    parent=dialog)
                return

            conn = None
            try:
                conn = get_connection()
                cursor = conn.cursor()

                if tipo == "RETTIFICA":
                    cursor.execute(
                        "UPDATE articoli SET giacenza = ? WHERE id = ?",
                        (qta, art_id))
                else:
                    var = qta if tipo == "CARICO" else -qta
                    cursor.execute(
                        "UPDATE articoli SET giacenza = giacenza + ? WHERE id = ?",
                        (var, art_id))

                cursor.execute("""
                    INSERT INTO movimenti_magazzino
                        (articolo_id, tipo_movimento, quantita, causale)
                    VALUES (?, ?, ?, ?)
                """, (art_id, tipo, qta, causale))

                conn.commit()
                self.carica_articoli()
                dialog.destroy()
                messagebox.showinfo(
                    "Successo",
                    "Movimento di magazzino registrato con successo.",
                    parent=self)
            except Exception as e:
                if conn is not None:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                log.exception("Errore movimento magazzino (id=%s, tipo=%s)",
                              art_id, tipo)
                messagebox.showerror("Errore",
                                     f"Impossibile registrare il movimento: {e}",
                                     parent=dialog)
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except Exception:
                        pass

        tk.Button(dialog, text="Registra Movimento", bg="#17a2b8",
                  fg="white", font=("Arial", 10, "bold"),
                  command=conferma_movimento).pack(pady=15, fill="x", padx=20)

    # ------------------------------------------------------------------ #
    # Export / Import CSV
    # ------------------------------------------------------------------ #

    def esporta_csv(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Esporta Magazzino in CSV",
        )
        if not file_path:
            return

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT codice_interno, codice_ean, descrizione, categoria,
                       unita_misura, peso_netto, peso_lordo, prezzo_vendita,
                       giacenza, soglia_minima
                FROM articoli
            """)
            rows = cursor.fetchall()

            with open(file_path, mode="w", newline="",
                      encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["Codice Interno", "Codice EAN", "Descrizione",
                                 "Categoria", "Unità Misura", "Peso Netto",
                                 "Peso Lordo", "Prezzo Vendita", "Giacenza",
                                 "Soglia Minima"])
                writer.writerows(rows)

            messagebox.showinfo(
                "Esportazione Riuscita",
                f"Magazzino esportato correttamente in:\n{file_path}",
                parent=self)
        except Exception as e:
            log.exception("Errore esportazione magazzino")
            messagebox.showerror("Errore",
                                 f"Impossibile esportare il file: {e}",
                                 parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def importa_csv(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv")],
            title="Importa Magazzino da CSV",
        )
        if not file_path:
            return

        dialog = tk.Toplevel(self)
        dialog.title("Opzioni Importazione CSV")
        dialog.geometry("340x200")
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog,
                 text="Il file CSV contiene l'intestazione\n(prima riga da saltare)?",
                 font=("Arial", 10, "bold"), justify="center").pack(pady=15)

        salta_header_var = tk.BooleanVar(value=True)
        tk.Checkbutton(dialog, text="Salta la prima riga (Intestazione)",
                       variable=salta_header_var,
                       font=("Arial", 9)).pack(pady=5)

        def avvia_import():
            salta = salta_header_var.get()
            dialog.destroy()

            conn = None
            importati = 0
            scartati = 0
            motivi = {}

            try:
                conn = get_connection()
                cursor = conn.cursor()

                with open(file_path, mode="r", encoding="utf-8-sig") as f:
                    reader = csv.reader(f, delimiter=";")
                    if salta:
                        next(reader, None)

                    for n, row in enumerate(reader, start=2 if salta else 1):
                        try:
                            if len(row) < 3 or not row[2].strip():
                                scartati += 1
                                motivi["riga corta o descrizione vuota"] = \
                                    motivi.get("riga corta o descrizione vuota", 0) + 1
                                continue

                            descrizione = row[2].strip()
                            ean = row[1].strip() if len(row) > 1 and row[1].strip() else None
                            cod_int = row[0].strip() if len(row) > 0 and row[0].strip() else None
                            cat = row[3].strip() if len(row) > 3 else ""
                            um = row[4].strip() if len(row) > 4 and row[4].strip() else "pz"

                            def _f(idx, default=0.0):
                                if len(row) > idx and row[idx].strip():
                                    return float(row[idx].replace(",", ".").strip())
                                return default

                            p_vend = _f(7)
                            giac = _f(8)
                            soglia = _f(9, default=5.0)

                            # Controllo duplicato su codice_interno
                            if cod_int:
                                cursor.execute(
                                    "SELECT id FROM articoli WHERE codice_interno = ?",
                                    (cod_int,))
                                if cursor.fetchone() is not None:
                                    scartati += 1
                                    motivi["codice interno duplicato"] = \
                                        motivi.get("codice interno duplicato", 0) + 1
                                    continue

                            cursor.execute("""
                                INSERT INTO articoli
                                    (codice_interno, codice_ean, descrizione,
                                     categoria, unita_misura, prezzo_vendita,
                                     giacenza, soglia_minima)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (cod_int, ean, descrizione, cat, um,
                                  p_vend, giac, soglia))
                            importati += 1
                        except (ValueError, IndexError) as row_err:
                            scartati += 1
                            key = f"errore di formato ({row_err})"
                            motivi[key] = motivi.get(key, 0) + 1

                conn.commit()
                self.carica_articoli()

                msg = f"Importati: {importati}\nScartati: {scartati}"
                if motivi:
                    msg += "\n\nDettaglio scarti:"
                    for k, v in motivi.items():
                        msg += f"\n• {k}: {v}"

                messagebox.showinfo("Importazione Completata", msg, parent=self)
            except Exception as e:
                if conn is not None:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                log.exception("Errore importazione CSV magazzino")
                messagebox.showerror("Errore Importazione",
                                     f"Impossibile importare il file:\n{e}",
                                     parent=self)
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except Exception:
                        pass

        tk.Button(dialog, text="Conferma e Importa", bg="#28a745",
                  fg="white", font=("Arial", 10, "bold"),
                  command=avvia_import).pack(pady=15, fill="x", padx=20)