import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import logging
from datetime import datetime

from database import get_connection

log = logging.getLogger("mercurio.documenti")


class DocumentiManagerTab(tk.Frame):
    """Modulo di gestione Documenti Fiscali: Scontrini, Fatture, Copie di Cortesia
    e Annulli RT."""

    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        self.carica_documenti()

    def create_widgets(self):
        top_frame = tk.Frame(self, padx=10, pady=10)
        top_frame.pack(fill="x")

        tk.Label(top_frame, text="🧾 Gestione Documenti, Scontrini & Fatture",
                 font=("Arial", 12, "bold")).pack(side="left")

        tk.Button(top_frame, text="📄 Genera Fattura da Scontrino",
                  bg="#28a745", fg="white", font=("Arial", 9, "bold"),
                  command=self.genera_fattura_da_scontrino).pack(side="right", padx=3)

        tk.Button(top_frame, text="📥 Copia di Cortesia (PDF/CSV)",
                  bg="#17a2b8", fg="white", font=("Arial", 9, "bold"),
                  command=self.esporta_copia_cortesia).pack(side="right", padx=3)

        tk.Button(top_frame, text="❌ Scontrino di Annullo (Storno RT)",
                  bg="#dc3545", fg="white", font=("Arial", 9, "bold"),
                  command=self.annulla_scontrino).pack(side="right", padx=3)

        tk.Button(top_frame, text="🔄 Aggiorna",
                  bg="#ffc107", fg="black", font=("Arial", 9, "bold"),
                  command=self.carica_documenti).pack(side="right", padx=3)

        # Tabella Documenti
        table_frame = tk.Frame(self, padx=10, pady=5)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "tipo", "numero", "data", "cliente",
                   "totale", "pagamento", "stato_xml")
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("tipo", text="Tipo Doc.")
        self.tree.heading("numero", text="N. Doc")
        self.tree.heading("data", text="Data Emissione")
        self.tree.heading("cliente", text="Cliente Associato")
        self.tree.heading("totale", text="Totale (€)")
        self.tree.heading("pagamento", text="Pagamento")
        self.tree.heading("stato_xml", text="Stato SDI / RT")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("tipo", width=95, anchor="center")
        self.tree.column("numero", width=90, anchor="center")
        self.tree.column("data", width=130, anchor="center")
        self.tree.column("cliente", width=180, anchor="w")
        self.tree.column("totale", width=90, anchor="e")
        self.tree.column("pagamento", width=90, anchor="center")
        self.tree.column("stato_xml", width=120, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ------------------------------------------------------------------ #
    # Lettura documenti
    # ------------------------------------------------------------------ #

    def carica_documenti(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.id, d.tipo_documento, d.numero, d.data_emissione,
                       COALESCE(c.ragione_sociale, 'Cliente Anonimo / Banco') AS cliente,
                       d.totale_documento, d.pagamento, d.stato_xml
                FROM documenti d
                LEFT JOIN clienti c ON d.cliente_id = c.id
                ORDER BY d.id DESC
            """)
            rows = cursor.fetchall()

            for r in rows:
                formatted_row = (
                    r[0],
                    r[1],
                    r[2] or f"DOC-{r[0]}",
                    r[3],
                    r[4],
                    f"€ {r[5]:.2f}" if r[5] is not None else "€ 0.00",
                    r[6] or "CONTANTI",
                    r[7] or "EMESSO",
                )
                self.tree.insert("", "end", values=formatted_row)
        except Exception as e:
            log.exception("Errore caricamento documenti")
            messagebox.showerror("Errore",
                                 f"Impossibile caricare i documenti: {e}",
                                 parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    # ------------------------------------------------------------------ #
    # Fattura da scontrino
    # ------------------------------------------------------------------ #

    def genera_fattura_da_scontrino(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "Attenzione",
                "Seleziona uno scontrino dalla tabella per generare la fattura corrispondente.",
                parent=self)
            return

        item_values = self.tree.item(selected[0], "values")
        doc_id = item_values[0]
        tipo = item_values[1]

        if tipo != "SCONTRINO":
            messagebox.showwarning(
                "Attenzione",
                "Puoi generare una fattura solo partendo da uno Scontrino di vendita al banco.",
                parent=self)
            return

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cliente_id, imponibile, totale_documento,
                       pagamento, stato_xml
                FROM documenti WHERE id = ?
            """, (doc_id,))
            scontrino = cursor.fetchone()

            if not scontrino:
                messagebox.showerror("Errore",
                                     "Documento non trovato.",
                                     parent=self)
                return

            # Controlli di validità
            if not scontrino["cliente_id"]:
                messagebox.showerror(
                    "Errore",
                    "Lo scontrino selezionato non ha un cliente associato. "
                    "Associa un cliente prima di emettere la fattura.",
                    parent=self)
                return

            if scontrino["stato_xml"] == "ANNULLATO_RT":
                messagebox.showerror(
                    "Errore",
                    "Impossibile fatturare uno scontrino annullato.",
                    parent=self)
                return

            if scontrino["imponibile"] is None:
                log.warning("Scontrino id=%s con imponibile NULL", doc_id)
                messagebox.showerror(
                    "Errore",
                    "Lo scontrino non ha un imponibile valido: "
                    "impossibile generare la fattura. Verifica i dati del POS.",
                    parent=self)
                return

            numero_fattura = f"FAT-{datetime.now().strftime('%Y')}-{int(doc_id):03d}"

            # Verifica duplicati sul numero fattura
            cursor.execute(
                "SELECT id FROM documenti WHERE tipo_documento = 'FATTURA' AND numero = ?",
                (numero_fattura,))
            if cursor.fetchone() is not None:
                messagebox.showerror(
                    "Errore",
                    f"Esiste già una fattura con numero {numero_fattura}. "
                    f"Impossibile generarne un'altra.",
                    parent=self)
                return

            # datetime('now','localtime') per rispettare il fuso orario italiano
            cursor.execute("""
                INSERT INTO documenti
                    (tipo_documento, numero, data_emissione, cliente_id,
                     imponibile, totale_documento, stato_xml, pagamento)
                VALUES ('FATTURA', ?, datetime('now','localtime'), ?, ?, ?,
                        'PRONTO_SDI', ?)
            """, (
                numero_fattura,
                scontrino["cliente_id"],
                scontrino["imponibile"],
                scontrino["totale_documento"],
                scontrino["pagamento"],
            ))

            conn.commit()
            self.carica_documenti()
            messagebox.showinfo(
                "Successo",
                f"Fattura {numero_fattura} generata con successo dalla vendita al banco!",
                parent=self)
        except Exception as e:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
            log.exception("Errore generazione fattura da scontrino id=%s", doc_id)
            messagebox.showerror("Errore",
                                 f"Impossibile generare la fattura: {e}",
                                 parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    # ------------------------------------------------------------------ #
    # Copia di cortesia
    # ------------------------------------------------------------------ #

    def esporta_copia_cortesia(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "Attenzione",
                "Seleziona un documento dalla tabella per esportare la copia di cortesia.",
                parent=self)
            return

        item_values = self.tree.item(selected[0], "values")
        doc_id = item_values[0]

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt")],
            title="Esporta Copia di Cortesia",
        )
        if not file_path:
            return

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.tipo_documento, d.numero, d.data_emissione,
                       c.ragione_sociale, d.totale_documento, d.pagamento
                FROM documenti d
                LEFT JOIN clienti c ON d.cliente_id = c.id
                WHERE d.id = ?
            """, (doc_id,))
            doc = cursor.fetchone()

            if not doc:
                messagebox.showerror("Errore",
                                     "Documento non trovato.",
                                     parent=self)
                return

            with open(file_path, mode="w", newline="",
                      encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["=== COPIA DI CORTESIA DOCUMENTO FISCALE ==="])
                writer.writerow(["Tipo Documento", doc[0]])
                writer.writerow(["Numero", doc[1]])
                writer.writerow(["Data", doc[2]])
                writer.writerow(["Cliente", doc[3] or "Cliente Anonimo"])
                writer.writerow(["Totale", f"€ {doc[4]:.2f}" if doc[4] is not None else "€ 0.00"])
                writer.writerow(["Pagamento", doc[5]])

            messagebox.showinfo(
                "Esportazione Riuscita",
                f"Copia di cortesia salvata correttamente in:\n{file_path}",
                parent=self)
        except Exception as e:
            log.exception("Errore esportazione copia di cortesia id=%s", doc_id)
            messagebox.showerror("Errore",
                                 f"Impossibile generare la copia di cortesia: {e}",
                                 parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    # ------------------------------------------------------------------ #
    # Annullo scontrino
    # ------------------------------------------------------------------ #

    def annulla_scontrino(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attenzione",
                                   "Seleziona uno scontrino da annullare.",
                                   parent=self)
            return

        item_values = self.tree.item(selected[0], "values")
        doc_id = item_values[0]
        tipo = item_values[1]
        numero = item_values[2]

        if tipo != "SCONTRINO":
            messagebox.showwarning(
                "Attenzione",
                "È possibile effettuare lo storno/annullo solo sui documenti di tipo SCONTRINO.",
                parent=self)
            return

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT stato_xml FROM documenti WHERE id = ?", (doc_id,))
            row = cursor.fetchone()

            if not row:
                messagebox.showerror("Errore",
                                     "Documento non trovato.", parent=self)
                return

            if row["stato_xml"] == "ANNULLATO_RT":
                messagebox.showwarning(
                    "Attenzione",
                    f"Lo scontrino {numero} risulta già annullato. "
                    f"Impossibile annullarlo una seconda volta.",
                    parent=self)
                return

            # Verifica se esiste già una fattura per questo scontrino
            # (per evitare annulli di scontrini fatturati, che richiedono
            # una nota di credito, non un semplice annullo RT).
            cursor.execute("""
                SELECT id FROM documenti
                WHERE tipo_documento = 'FATTURA' AND numero = ?
            """, (f"FAT-{datetime.now().strftime('%Y')}-{int(doc_id):03d}",))
            if cursor.fetchone() is not None:
                if not messagebox.askyesno(
                    "Fattura Presente",
                    f"Risulta già emessa una fattura per lo scontrino {numero}.\n"
                    f"L'annullo RT NON sostituisce una nota di credito.\n"
                    f"Procedere comunque con l'annullo RT?",
                    parent=self,
                ):
                    return

            if not messagebox.askyesno(
                "Conferma Scontrino di Annullo",
                f"Vuoi emettere uno Scontrino di Annullo (Storno RT) "
                f"per il documento {numero}?",
                parent=self,
            ):
                return

            cursor.execute(
                "UPDATE documenti SET stato_xml = 'ANNULLATO_RT' WHERE id = ?",
                (doc_id,))
            cursor.execute("""
                INSERT INTO documenti
                    (tipo_documento, numero, data_emissione,
                     imponibile, totale_documento, stato_xml, pagamento)
                SELECT 'ANNULLO', 'STNO-' || numero, datetime('now','localtime'),
                       -imponibile, -totale_documento, 'TRASMESSO_RT', pagamento
                FROM documenti WHERE id = ?
            """, (doc_id,))

            conn.commit()
            self.carica_documenti()
            messagebox.showinfo(
                "Annullamento Effettuato",
                "Comando di scontrino di annullo inviato con successo al "
                "Registratore Telematico.",
                parent=self)
        except Exception as e:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
            log.exception("Errore annullo scontrino id=%s numero=%s",
                          doc_id, numero)
            messagebox.showerror("Errore",
                                 f"Impossibile completare l'annullo: {e}",
                                 parent=self)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass