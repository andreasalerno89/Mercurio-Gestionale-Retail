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

        tk.Button(top_frame, text="↩️ Emetti Nota di Credito",
                  bg="#fd7e14", fg="white", font=("Arial", 9, "bold"),
                  command=self.emetti_nota_credito).pack(side="right", padx=3)

        tk.Button(top_frame, text="🚚 Emetti DDT",
                  bg="#e83e8c", fg="white", font=("Arial", 9, "bold"),
                  command=self.emetti_ddt).pack(side="right", padx=3)

        tk.Button(top_frame, text="📥 Copia di Cortesia (HTML/PDF)",
                  bg="#17a2b8", fg="white", font=("Arial", 9, "bold"),
                  command=self.esporta_copia_cortesia).pack(side="right", padx=3)

        tk.Button(top_frame, text="❌ Scontrino di Annullo (Storno RT)",
                  bg="#dc3545", fg="white", font=("Arial", 9, "bold"),
                  command=self.annulla_scontrino).pack(side="right", padx=3)

        tk.Button(top_frame, text="🔄 Aggiorna",
                  bg="#ffc107", fg="black", font=("Arial", 9, "bold"),
                  command=self.carica_documenti).pack(side="right", padx=3)

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
                messagebox.showerror("Errore", "Documento non trovato.",
                                     parent=self)
                return

            if not scontrino["cliente_id"]:
                messagebox.showerror(
                    "Errore",
                    "Lo scontrino selezionato non ha un cliente associato. "
                    "Associa un cliente prima di emettere la fattura.",
                    parent=self)
                return

            if scontrino["stato_xml"] == "ANNULLATO_RT":
                messagebox.showerror("Errore",
                                     "Impossibile fatturare uno scontrino annullato.",
                                     parent=self)
                return

            if scontrino["imponibile"] is None:
                messagebox.showerror(
                    "Errore",
                    "Lo scontrino non ha un imponibile valido: "
                    "impossibile generare la fattura.",
                    parent=self)
                return

            cursor.execute("""
                SELECT id FROM documenti
                WHERE tipo_documento = 'FATTURA' AND scontrino_origine_id = ?
            """, (doc_id,))
            if cursor.fetchone() is not None:
                messagebox.showerror(
                    "Errore",
                    "Esiste già una fattura collegata a questo scontrino.",
                    parent=self)
                return

            cursor.execute(
                "SELECT COUNT(*) FROM documenti_righe WHERE documento_id = ?",
                (doc_id,))
            n_righe = cursor.fetchone()[0] or 0
            if n_righe == 0:
                messagebox.showerror(
                    "Errore",
                    "Lo scontrino non ha righe di dettaglio: "
                    "impossibile generare la fattura.",
                    parent=self)
                return

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
            numero_fattura = f"FAT-{anno_corrente}-{nuovo_numero:04d}"

            cursor.execute("""
                INSERT INTO documenti
                    (tipo_documento, numero, data_emissione, cliente_id,
                     imponibile, totale_documento, stato_xml, pagamento,
                     scontrino_origine_id, tipo_soggetto)
                VALUES ('FATTURA', ?, datetime('now','localtime'), ?, ?, ?,
                        'PRONTO_SDI', ?, ?, 'CLIENTE')
            """, (
                numero_fattura,
                scontrino["cliente_id"],
                scontrino["imponibile"],
                scontrino["totale_documento"],
                scontrino["pagamento"],
                doc_id,
            ))
            fattura_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO documenti_righe
                    (documento_id, articolo_id, descrizione, quantita,
                     prezzo_unitario, aliquota_iva, totale_riga,
                     sconto_riga, tipo_sconto_riga)
                SELECT ?, articolo_id, descrizione, quantita,
                       prezzo_unitario, aliquota_iva, totale_riga,
                       sconto_riga, tipo_sconto_riga
                FROM documenti_righe
                WHERE documento_id = ?
            """, (fattura_id, doc_id))

            conn.commit()
            self.carica_documenti()
            messagebox.showinfo(
                "Successo",
                f"Fattura {numero_fattura} generata con successo "
                f"dallo scontrino #{doc_id}!\n"
                f"Righe trasferite: {n_righe}",
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

    def emetti_nota_credito(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "Attenzione",
                "Seleziona una fattura dalla tabella per emettere la nota di credito.",
                parent=self)
            return

        item_values = self.tree.item(selected[0], "values")
        doc_id = item_values[0]
        tipo = item_values[1]
        numero = item_values[2]

        if tipo != "FATTURA":
            messagebox.showwarning(
                "Attenzione",
                "La nota di credito può essere emessa solo su una FATTURA.\n"
                "Per stornare uno scontrino, usa l'annullo RT.",
                parent=self)
            return

        NotaCreditoDialog(self, doc_id, numero, callback=self.carica_documenti)

    def emetti_ddt(self):
        DDTPage(self, callback=self.carica_documenti)

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
            defaultextension=".html",
            filetypes=[("HTML Files", "*.html"), ("All Files", "*.*")],
            title="Esporta Copia di Cortesia",
        )
        if not file_path:
            return

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM impostazioni_azienda LIMIT 1")
            az_row = cursor.fetchone()
            az = dict(az_row) if az_row else {}

            cursor.execute("""
                SELECT d.tipo_documento, d.numero, d.data_emissione,
                       d.imponibile, d.totale_documento, d.pagamento,
                       d.stato_xml,
                       COALESCE(c.ragione_sociale, 'Cliente Occasionale') AS cliente_nome,
                       c.codice_fiscale, c.partita_iva,
                       c.indirizzo, c.civico, c.cap, c.localita, c.provincia
                FROM documenti d
                LEFT JOIN clienti c ON d.cliente_id = c.id
                WHERE d.id = ?
            """, (doc_id,))
            doc = cursor.fetchone()

            if not doc:
                messagebox.showerror("Errore", "Documento non trovato.",
                                     parent=self)
                return

            cursor.execute("""
                SELECT descrizione, quantita, prezzo_unitario, aliquota_iva,
                       totale_riga, sconto_riga, tipo_sconto_riga
                FROM documenti_righe
                WHERE documento_id = ?
                ORDER BY id ASC
            """, (doc_id,))
            righe = cursor.fetchall()

            def esc(s):
                if s is None:
                    return ""
                return (str(s).replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                        .replace('"', "&quot;"))

            html = []
            html.append("<!DOCTYPE html>")
            html.append("<html lang='it'>")
            html.append("<head>")
            html.append("<meta charset='UTF-8'>")
            html.append(f"<title>Copia di Cortesia - {esc(doc['numero'])}</title>")
            html.append("<style>")
            html.append("body { font-family: Arial, sans-serif; margin: 30px; color: #333; }")
            html.append("h1 { font-size: 18px; margin: 0 0 5px 0; }")
            html.append(".header { border-bottom: 2px solid #343a40; padding-bottom: 10px; margin-bottom: 20px; }")
            html.append(".azienda { font-size: 13px; line-height: 1.4; }")
            html.append(".doc-title { font-size: 16px; font-weight: bold; margin: 20px 0 10px 0; }")
            html.append("table { width: 100%; border-collapse: collapse; margin-top: 15px; }")
            html.append("th { background: #343a40; color: white; padding: 8px; text-align: left; font-size: 12px; }")
            html.append("td { padding: 6px 8px; border-bottom: 1px solid #ddd; font-size: 12px; }")
            html.append("td.num, th.num { text-align: right; }")
            html.append("td.center, th.center { text-align: center; }")
            html.append(".totale-row td { font-weight: bold; border-top: 2px solid #343a40; }")
            html.append(".firma { margin-top: 40px; font-size: 11px; color: #666; font-style: italic; }")
            html.append(".badge { display: inline-block; padding: 3px 8px; background: #ffc107; color: #000; font-size: 11px; font-weight: bold; border-radius: 3px; }")
            html.append("@media print { body { margin: 10mm; } .no-print { display: none; } }")
            html.append("</style>")
            html.append("</head>")
            html.append("<body>")

            html.append("<div class='header'>")
            html.append(f"<h1>{esc(az.get('ragione_sociale', ''))}</h1>")
            html.append("<div class='azienda'>")
            indirizzo_parts = []
            if az.get("indirizzo"):
                indirizzo_parts.append(esc(az["indirizzo"]))
            if az.get("civico"):
                indirizzo_parts.append(esc(az["civico"]))
            if indirizzo_parts:
                html.append(", ".join(indirizzo_parts) + "<br>")
            cap_loc = []
            if az.get("cap"):
                cap_loc.append(esc(az["cap"]))
            if az.get("localita"):
                cap_loc.append(esc(az["localita"]))
            if cap_loc:
                html.append(" ".join(cap_loc))
                if az.get("provincia"):
                    html.append(f" ({esc(az['provincia'])})")
                html.append("<br>")
            if az.get("partita_iva"):
                html.append(f"P.IVA: {esc(az['partita_iva'])} ")
            if az.get("codice_fiscale"):
                html.append(f"C.F.: {esc(az['codice_fiscale'])}")
            html.append("<br>")
            if az.get("email"):
                html.append(f"Email: {esc(az['email'])}<br>")
            html.append("</div>")
            html.append("</div>")

            html.append(f"<div class='doc-title'>COPIA DI CORTESIA - "
                        f"{esc(doc['tipo_documento'])} n. {esc(doc['numero'])}</div>")
            html.append(f"<div>Data: {esc(doc['data_emissione'])}</div>")
            html.append(f"<div>Pagamento: {esc(doc['pagamento'] or '-')}</div>")

            html.append("<div class='doc-title' style='margin-top:15px;'>Destinatario</div>")
            html.append(f"<div>{esc(doc['cliente_nome'])}</div>")
            cli_parts = []
            if doc["indirizzo"]:
                s = esc(doc["indirizzo"])
                if doc["civico"]:
                    s += f", {esc(doc['civico'])}"
                cli_parts.append(s)
            if doc["cap"] or doc["localita"]:
                s = ""
                if doc["cap"]:
                    s += esc(doc["cap"]) + " "
                if doc["localita"]:
                    s += esc(doc["localita"])
                if doc["provincia"]:
                    s += f" ({esc(doc['provincia'])})"
                cli_parts.append(s)
            if doc["codice_fiscale"]:
                cli_parts.append(f"C.F.: {esc(doc['codice_fiscale'])}")
            if doc["partita_iva"]:
                cli_parts.append(f"P.IVA: {esc(doc['partita_iva'])}")
            for p in cli_parts:
                html.append(f"<div>{p}</div>")

            html.append("<table>")
            html.append("<thead><tr>")
            html.append("<th>Descrizione</th>")
            html.append("<th class='center'>Q.tà</th>")
            html.append("<th class='num'>P. Unit.</th>")
            html.append("<th class='center'>IVA</th>")
            html.append("<th class='num'>Totale</th>")
            html.append("</tr></thead>")
            html.append("<tbody>")

            if righe:
                for r in righe:
                    desc = esc(r["descrizione"])
                    if r["sconto_riga"] and r["sconto_riga"] > 0:
                        desc += f" <small>(sconto {r['sconto_riga']}{r['tipo_sconto_riga']})</small>"
                    aliquota_disp = f"{r['aliquota_iva']:.0f}%" if r["aliquota_iva"] else "Esente"
                    html.append("<tr>")
                    html.append(f"<td>{desc}</td>")
                    html.append(f"<td class='center'>{r['quantita']:.2f}</td>")
                    html.append(f"<td class='num'>€ {r['prezzo_unitario']:.2f}</td>")
                    html.append(f"<td class='center'>{aliquota_disp}</td>")
                    html.append(f"<td class='num'>€ {r['totale_riga']:.2f}</td>")
                    html.append("</tr>")
            else:
                html.append("<tr><td colspan='5' style='text-align:center;color:#999;'>"
                            "Nessuna riga di dettaglio disponibile per questo documento."
                            "</td></tr>")

            html.append("</tbody>")
            html.append("</table>")

            html.append("<table style='margin-top:15px; width:50%; margin-left:auto;'>")
            imponibile = doc["imponibile"] or 0.0
            totale = doc["totale_documento"] or 0.0
            iva_totale = max(0.0, totale - imponibile)
            html.append(f"<tr><td>Imponibile</td><td class='num'>€ {imponibile:.2f}</td></tr>")
            html.append(f"<tr><td>IVA</td><td class='num'>€ {iva_totale:.2f}</td></tr>")
            html.append(f"<tr class='totale-row'><td>Totale</td><td class='num'>€ {totale:.2f}</td></tr>")
            html.append("</table>")

            html.append("<div style='margin-top:20px;'>")
            html.append("<span class='badge'>COPIA DI CORTESIA</span>")
            html.append("<span style='font-size:11px; margin-left:10px; color:#666;'>"
                        "Documento non valido ai fini fiscali.</span>")
            html.append("</div>")
            html.append("<div class='firma'>"
                        "Documento generato dal gestionale Mercurio - "
                        f"{esc(datetime.now().strftime('%d/%m/%Y %H:%M'))}"
                        "</div>")

            html.append("<div class='no-print' style='margin-top:20px;'>")
            html.append("<button onclick='window.print()' "
                        "style='padding:10px 20px;font-size:14px;cursor:pointer;'>"
                        "🖨️ Stampa / Salva come PDF</button>")
            html.append("</div>")

            html.append("</body>")
            html.append("</html>")

            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(html))

            messagebox.showinfo(
                "Esportazione Riuscita",
                f"Copia di cortesia salvata in:\n{file_path}\n\n"
                f"Apri il file nel browser e usa 'Stampa' per generare il PDF.",
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
                messagebox.showerror("Errore", "Documento non trovato.", parent=self)
                return

            if row["stato_xml"] == "ANNULLATO_RT":
                messagebox.showwarning(
                    "Attenzione",
                    f"Lo scontrino {numero} risulta già annullato. "
                    f"Impossibile annullarlo una seconda volta.",
                    parent=self)
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
                     documento_origine_id, motivo_annullo, tipo_soggetto)
                VALUES ('NOTA_CREDITO', ?, datetime('now','localtime'), ?, ?, ?,
                        'PRONTO_SDI', ?, ?, ?, ?)
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