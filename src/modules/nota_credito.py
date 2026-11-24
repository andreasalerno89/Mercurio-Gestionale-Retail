import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime

from database import get_connection

log = logging.getLogger("mercurio.nota_credito")


class NotaCreditoDialog(tk.Toplevel):
    """Finestra per emettere una nota di credito su una fattura."""

    def __init__(self, parent, fattura_id, numero_fattura, callback=None):
        super().__init__(parent)
        self.parent = parent
        self.fattura_id = fattura_id
        self.numero_fattura = numero_fattura
        self.callback = callback
        self.righe = []

        self.title(f"Nota di Credito su {numero_fattura}")
        self.geometry("650x600")
        self.resizable(False, False)
        self.transient(parent)
        self.wait_visibility()
        self.grab_set()

        self.create_widgets()
        self.carica_righe()

    def create_widgets(self):
        header = tk.Frame(self, padx=15, pady=10)
        header.pack(fill="x")
        tk.Label(header, text=f"Storno fattura {self.numero_fattura}",
                 font=("Arial", 13, "bold")).pack(anchor="w")
        tk.Label(header,
                 text="Seleziona le righe da stornare (o tutte per uno storno totale).",
                 font=("Arial", 9)).pack(anchor="w")

        motivo_frame = tk.Frame(self, padx=15, pady=5)
        motivo_frame.pack(fill="x")
        tk.Label(motivo_frame, text="Motivo:", font=("Arial", 9, "bold")).pack(side="left")
        self.combo_motivo = ttk.Combobox(
            motivo_frame,
            values=["Reso merce", "Errore emissione", "Sconto post-vendita", "Altro"],
            width=30, state="readonly")
        self.combo_motivo.pack(side="left", padx=5)
        self.combo_motivo.set("Reso merce")

        table_frame = tk.Frame(self, padx=15, pady=10)
        table_frame.pack(fill="both", expand=True)

        columns = ("sel", "descrizione", "quantita", "prezzo", "totale")
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", selectmode="browse",
                                 height=10)
        self.tree.heading("sel", text="✓")
        self.tree.heading("descrizione", text="Descrizione")
        self.tree.heading("quantita", text="Q.tà")
        self.tree.heading("prezzo", text="P. Unit.")
        self.tree.heading("totale", text="Totale")

        self.tree.column("sel", width=30, anchor="center")
        self.tree.column("descrizione", width=260, anchor="w")
        self.tree.column("quantita", width=70, anchor="center")
        self.tree.column("prezzo", width=90, anchor="e")
        self.tree.column("totale", width=90, anchor="e")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Button-1>", self.toggle_riga)

        btn_frame = tk.Frame(self, padx=15, pady=5)
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="Seleziona tutte", bg="#6c757d", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.seleziona_tutte).pack(side="left", padx=3)
        tk.Button(btn_frame, text="Deseleziona tutte", bg="#6c757d", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.deseleziona_tutte).pack(side="left", padx=3)

        self.lbl_totale = tk.Label(self, text="Totale nota di credito: € 0.00",
                                   font=("Arial", 12, "bold"), fg="#dc3545")
        self.lbl_totale.pack(pady=10)

        actions = tk.Frame(self, padx=15, pady=10)
        actions.pack(fill="x")
        tk.Button(actions, text="Annulla", bg="#6c757d", fg="white",
                  font=("Arial", 10, "bold"),
                  command=self.destroy).pack(side="right", padx=5)
        tk.Button(actions, text="Emetti Nota di Credito", bg="#dc3545", fg="white",
                  font=("Arial", 10, "bold"),
                  command=self.conferma).pack(side="right", padx=5)

    def carica_righe(self):
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, articolo_id, descrizione, quantita, prezzo_unitario,
                       aliquota_iva, totale_riga
                FROM documenti_righe
                WHERE documento_id = ?
                ORDER BY id ASC
            """, (self.fattura_id,))
            self.righe = cursor.fetchall()

            for r in self.righe:
                self.tree.insert("", "end", iid=str(r["id"]), values=(
                    "☐",
                    r["descrizione"],
                    f"{r['quantita']:.2f}",
                    f"€ {r['prezzo_unitario']:.2f}",
                    f"€ {r['totale_riga']:.2f}",
                ))
        except Exception as e:
            log.exception("Errore caricamento righe fattura per nota credito")
            messagebox.showerror("Errore",
                                 f"Impossibile caricare le righe: {e}",
                                 parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def toggle_riga(self, event):
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return
        vals = list(self.tree.item(row_id, "values"))
        vals[0] = "☐" if vals[0] == "☑" else "☑"
        self.tree.item(row_id, values=vals)
        self.aggiorna_totale()

    def seleziona_tutte(self):
        for row_id in self.tree.get_children():
            vals = list(self.tree.item(row_id, "values"))
            vals[0] = "☑"
            self.tree.item(row_id, values=vals)
        self.aggiorna_totale()

    def deseleziona_tutte(self):
        for row_id in self.tree.get_children():
            vals = list(self.tree.item(row_id, "values"))
            vals[0] = "☐"
            self.tree.item(row_id, values=vals)
        self.aggiorna_totale()

    def aggiorna_totale(self):
        totale = 0.0
        for row_id in self.tree.get_children():
            vals = self.tree.item(row_id, "values")
            if vals[0] == "☑":
                for r in self.righe:
                    if str(r["id"]) == row_id:
                        totale += float(r["totale_riga"] or 0.0)
                        break
        self.lbl_totale.config(text=f"Totale nota di credito: € {totale:.2f}")

    def conferma(self):
        righe_selezionate = []
        for row_id in self.tree.get_children():
            vals = self.tree.item(row_id, "values")
            if vals[0] == "☑":
                for r in self.righe:
                    if str(r["id"]) == row_id:
                        righe_selezionate.append(r)
                        break

        if not righe_selezionate:
            messagebox.showwarning(
                "Attenzione",
                "Seleziona almeno una riga da stornare.",
                parent=self)
            return

        motivo = self.combo_motivo.get().strip() or "Altro"

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            anno_corrente = datetime.now().strftime('%Y')
            cursor.execute("""
                SELECT ultimo_numero FROM contatori
                WHERE tipo_documento = 'NOTA_CREDITO' AND anno = ?
            """, (anno_corrente,))
            row_cnt = cursor.fetchone()
            if row_cnt is None:
                nuovo_numero = 1
                cursor.execute("""
                    INSERT INTO contatori (tipo_documento, anno, ultimo_numero)
                    VALUES ('NOTA_CREDITO', ?, ?)
                """, (anno_corrente, nuovo_numero))
            else:
                nuovo_numero = (row_cnt["ultimo_numero"] or 0) + 1
                cursor.execute("""
                    UPDATE contatori SET ultimo_numero = ?
                    WHERE tipo_documento = 'NOTA_CREDITO' AND anno = ?
                """, (nuovo_numero, anno_corrente))
            numero_nc = f"NC-{anno_corrente}-{nuovo_numero:04d}"

            totale_nc = sum(float(r["totale_riga"] or 0.0) for r in righe_selezionate)
            imponibile_nc = 0.0
            for r in righe_selezionate:
                aliquota = float(r["aliquota_iva"] or 0.0)
                if aliquota > 0:
                    imponibile_nc += float(r["totale_riga"] or 0.0) / (1 + aliquota / 100.0)
                else:
                    imponibile_nc += float(r["totale_riga"] or 0.0)

            cursor.execute(
                "SELECT cliente_id, pagamento, tipo_soggetto FROM documenti WHERE id = ?",
                (self.fattura_id,))
            fatt_orig = cursor.fetchone()

            cursor.execute("""
                INSERT INTO documenti
                    (tipo_documento, numero, data_emissione, cliente_id,
                     imponibile, totale_documento, stato_xml, pagamento,
                     documento_origine_id, motivo_annullo, tipo_soggetto,
                     stato_documento)
                VALUES ('NOTA_CREDITO', ?, datetime('now','localtime'), ?, ?, ?,
                        'PRONTO_SDI', ?, ?, ?, ?, 'EMESSO')
            """, (
                numero_nc,
                fatt_orig["cliente_id"],
                -imponibile_nc,
                -totale_nc,
                fatt_orig["pagamento"],
                self.fattura_id,
                motivo,
                fatt_orig["tipo_soggetto"] or "CLIENTE",
            ))
            nc_id = cursor.lastrowid

            for r in righe_selezionate:
                cursor.execute("""
                    INSERT INTO documenti_righe
                        (documento_id, articolo_id, descrizione, quantita,
                         prezzo_unitario, aliquota_iva, totale_riga,
                         sconto_riga, tipo_sconto_riga)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    nc_id,
                    r["articolo_id"],
                    r["descrizione"],
                    -float(r["quantita"] or 0.0),
                    float(r["prezzo_unitario"] or 0.0),
                    r["aliquota_iva"],
                    -float(r["totale_riga"] or 0.0),
                    0.0,
                    "%",
                ))

                if r["articolo_id"]:
                    cursor.execute("""
                        UPDATE articoli SET giacenza = giacenza + ? WHERE id = ?
                    """, (float(r["quantita"] or 0.0), r["articolo_id"]))
                    cursor.execute("""
                        INSERT INTO movimenti_magazzino
                            (articolo_id, tipo_movimento, quantita, causale,
                             riferimento_id)
                        VALUES (?, 'RESO', ?, ?, ?)
                    """, (r["articolo_id"], float(r["quantita"] or 0.0),
                          f"Nota di credito {numero_nc} su {self.numero_fattura}",
                          nc_id))

            conn.commit()
            self.callback and self.callback()
            self.destroy()
            messagebox.showinfo(
                "Nota di Credito Emessa",
                f"Nota di credito {numero_nc} emessa con successo.\n"
                f"Totale stornato: € {totale_nc:.2f}\n"
                f"Motivo: {motivo}",
                parent=self.parent)
        except Exception as e:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
            log.exception("Errore emissione nota di credito")
            messagebox.showerror("Errore",
                                 f"Impossibile emettere la nota di credito: {e}",
                                 parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass