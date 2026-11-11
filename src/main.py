import os
import sys
import logging
import traceback
from pathlib import Path

# Assicura che la cartella 'src' sia sempre nel path di Python (priorità massima)
current_dir = os.path.abspath(os.path.dirname(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

# Import diretti senza il prefisso 'src.'
from config import get_company_data, save_company_data
from database import init_db, get_connection, DB_PATH
from modules.magazzino import MagazzinoFrame
from modules.fornitori import FornitoriManagerFrame
from modules.clienti import ClientiManagerTab
from modules.pos import PosFrame
from modules.documenti import DocumentiManagerTab
from modules.corrispettivi import CorrispettiviManagerTab
from modules.impostazioni import ImpostazioniFrame

# ---------------------------------------------------------------
# Logging di base (file + console)
# ---------------------------------------------------------------
# Il log va nella stessa cartella del database:
# - in sviluppo: <root>/mercurio.log
# - nell'exe: %LOCALAPPDATA%\MercurioGestionale\mercurio.log
LOG_PATH = os.path.join(os.path.dirname(DB_PATH), "mercurio.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("mercurio.main")

class SetupWizard(tk.Toplevel):
    """Finestra di primo avvio per la configurazione dei dati aziendali e fiscali."""

    def __init__(self, parent, on_complete_callback):
        super().__init__(parent)
        self.title("Mercurio Gestionale Retail - Configurazione Iniziale")
        self.geometry("520x620")
        self.resizable(False, False)
        self.on_complete_callback = on_complete_callback
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        tk.Label(self, text="Benvenuto in Mercurio Gestionale Retail",
                 font=("Arial", 14, "bold")).pack(pady=15)
        tk.Label(self, text="Inserisci i dati fiscali dell'attività per iniziare:",
                 font=("Arial", 10)).pack(pady=5)

        form_frame = tk.Frame(self)
        form_frame.pack(padx=20, pady=10, fill="both", expand=True)

        self.entries = {}
        fields = [
            ("Ragione Sociale *", "ragione_sociale"),
            ("Partita IVA *", "partita_iva"),
            ("Codice Fiscale", "codice_fiscale"),
            ("Indirizzo", "indirizzo"),
            ("Civico", "civico"),
            ("CAP", "cap"),
            ("Località / Città", "localita"),
            ("Provincia", "provincia"),
            ("IBAN", "iban"),
            ("PEC / Email", "email"),
        ]

        for idx, (label_text, key) in enumerate(fields):
            tk.Label(form_frame, text=label_text, anchor="w").grid(
                row=idx, column=0, sticky="w", pady=3)
            entry = tk.Entry(form_frame, width=35, font=("Arial", 10))
            entry.grid(row=idx, column=1, sticky="ew", pady=3)
            self.entries[key] = entry

        btn_salva = tk.Button(
            form_frame,
            text="Salva e Avvia Gestionale",
            bg="#28a745", fg="white", font=("Arial", 10, "bold"),
            command=self.salva_config,
        )
        btn_salva.grid(row=len(fields), column=0, columnspan=2, pady=15, sticky="ew")

    def salva_config(self):
        data = {key: entry.get().strip() for key, entry in self.entries.items()}
        if not data["ragione_sociale"] or not data["partita_iva"]:
            messagebox.showerror(
                "Errore",
                "Ragione Sociale e Partita IVA sono obbligatorie!",
                parent=self,
            )
            return

        try:
            log.info("Salvataggio dati aziendali...")
            save_company_data(data)
            log.info("Inizializzazione database SQLite...")
            init_db()
            log.info("Configurazione completata.")
        except Exception as e:
            log.exception("Errore durante il salvataggio della configurazione")
            messagebox.showerror(
                "Errore",
                f"Salvataggio fallito:\n{e}",
                parent=self,
            )
            return

        messagebox.showinfo("Successo", "Configurazione completata!", parent=self)

        # Rilascio esplicito del grab PRIMA di distruggere il wizard,
        # altrimenti l'event loop resta "appeso" e la finestra principale non risponde.
        try:
            self.grab_release()
        except tk.TclError:
            pass

        master = self.master
        self.destroy()

        # Rimanda la costruzione dell'interfaccia all'event loop,
        # quando il wizard è definitivamente scomparso.
        master.after_idle(self.on_complete_callback)

    def on_close(self):
        # Chiusura esplicita del wizard: usciamo dall'applicazione.
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()
        sys.exit(0)


class DashboardFrame(tk.Frame):
    """Pannello Dashboard con KPI, fatturato e scontrini filtrabili per mese/anno."""

    def __init__(self, parent):
        super().__init__(parent, bg="#f8f9fa")
        self.create_widgets()
        self.aggiorna_statistiche()

    def create_widgets(self):
        header = tk.Frame(self, bg="#f8f9fa", padx=15, pady=15)
        header.pack(fill="x")

        tk.Label(header, text="📊 Dashboard & Centro di Controllo",
                 font=("Arial", 16, "bold"), bg="#f8f9fa", fg="#343a40").pack(side="left")

        # Filtri Mese e Anno
        filter_frame = tk.Frame(header, bg="#f8f9fa")
        filter_frame.pack(side="right")

        tk.Label(filter_frame, text="Mese:", bg="#f8f9fa",
                 font=("Arial", 9, "bold")).pack(side="left", padx=2)
        self.mesi_cb = ttk.Combobox(
            filter_frame,
            values=["Tutti", "01 - Gennaio", "02 - Febbraio", "03 - Marzo",
                    "04 - Aprile", "05 - Maggio", "06 - Giugno", "07 - Luglio",
                    "08 - Agosto", "09 - Settembre", "10 - Ottobre",
                    "11 - Novembre", "12 - Dicembre"],
            width=12, state="readonly",
        )
        self.mesi_cb.pack(side="left", padx=5)
        self.mesi_cb.set("Tutti")
        self.mesi_cb.bind("<<ComboboxSelected>>", lambda e: self.aggiorna_statistiche())

        tk.Label(filter_frame, text="Anno:", bg="#f8f9fa",
                 font=("Arial", 9, "bold")).pack(side="left", padx=2)
        anni_disponibili = [
            "Tutti",
            str(datetime.now().year),
            str(datetime.now().year - 1),
            str(datetime.now().year - 2),
        ]
        self.anni_cb = ttk.Combobox(filter_frame, values=anni_disponibili,
                                    width=8, state="readonly")
        self.anni_cb.pack(side="left", padx=5)
        self.anni_cb.set(str(datetime.now().year))
        self.anni_cb.bind("<<ComboboxSelected>>", lambda e: self.aggiorna_statistiche())

        tk.Button(filter_frame, text="🔄 Aggiorna", bg="#6c757d", fg="white",
                  font=("Arial", 9, "bold"),
                  command=self.aggiorna_statistiche).pack(side="left", padx=5)

        # Griglia KPI Cards (Riga 1)
        cards_frame = tk.Frame(self, bg="#f8f9fa", padx=15)
        cards_frame.pack(fill="x", pady=5)

        self.lbl_fatturato_val = self.crea_kpi_card(
            cards_frame, "Fatturato Totale", "€ 0.00", 0, 0, "#28a745")
        self.lbl_scontrini_val = self.crea_kpi_card(
            cards_frame, "Scontrini Emessi", "0", 0, 1, "#007bff")
        self.lbl_contanti_val = self.crea_kpi_card(
            cards_frame, "Incasso Contanti", "€ 0.00", 0, 2, "#17a2b8")
        self.lbl_pos_val = self.crea_kpi_card(
            cards_frame, "Incasso POS", "€ 0.00", 0, 3, "#6f42c1")

        # Griglia KPI Cards (Riga 2)
        cards_frame_2 = tk.Frame(self, bg="#f8f9fa", padx=15)
        cards_frame_2.pack(fill="x", pady=5)

        self.lbl_valore_mag = self.crea_kpi_card(
            cards_frame_2, "Valore Magazzino", "€ 0.00", 0, 0, "#20c997")
        self.lbl_sottoscorta_val = self.crea_kpi_card(
            cards_frame_2, "Articoli Sottoscorta", "0", 0, 1, "#dc3545")
        self.lbl_clienti_val = self.crea_kpi_card(
            cards_frame_2, "Clienti / Fidelity", "0", 0, 2, "#ffc107")

               # Sezione informativa inferiore
        info_frame = tk.Frame(self, bg="white", padx=20, pady=20, relief="solid", bd=1)
        info_frame.pack(fill="both", expand=True, padx=20, pady=15)

        tk.Label(info_frame, text="Panoramica Operativa & Stato Sistema",
                 font=("Arial", 12, "bold"), bg="white", fg="#333").pack(anchor="w", pady=(0, 10))

        testo_info = (
            f"• Software: Mercurio Gestionale Retail (v0.3.2 Alpha)\n"
            f"• Database: SQLite3 (multi-tabella, pesi, unità di misura, logiche fiscali RT)\n"
            f"• Stato: Pronto per la gestione integrata di magazzino, cassa POS, "
            f"corrispettivi e fatturazione."
        )
        tk.Label(info_frame, text=testo_info, font=("Arial", 10),
                 bg="white", justify="left").pack(anchor="w")
        
    def crea_kpi_card(self, parent, titolo, valore_iniziale, riga, colonna, colore_bordo):
        card = tk.Frame(parent, bg="white", relief="solid", bd=1, padx=15, pady=12)
        card.grid(row=riga, column=colonna, padx=8, pady=5, sticky="nsew")
        parent.columnconfigure(colonna, weight=1)

        strip = tk.Frame(card, bg=colore_bordo, height=4)
        strip.pack(fill="x", pady=(0, 8))

        tk.Label(card, text=titolo.upper(), font=("Arial", 8, "bold"),
                 bg="white", fg="#6c757d").pack(anchor="w")
        lbl_valore = tk.Label(card, text=valore_iniziale,
                              font=("Arial", 15, "bold"), bg="white", fg="#343a40")
        lbl_valore.pack(anchor="w", pady=(2, 0))
        return lbl_valore

    def aggiorna_statistiche(self):
        """Aggiorna i KPI in modo resiliente: ogni query è isolata, così un errore
        su una tabella non blocca le altre metriche né apre popup indesiderati."""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            mese_sel = self.mesi_cb.get()
            anno_sel = self.anni_cb.get()

            # --- 1. Documenti / scontrini ------------------------------------
            tot_scontrini = 0
            fatturato = 0.0
            incasso_contanti = 0.0
            incasso_pos = 0.0
            try:
                query_doc = (
                    "SELECT COUNT(*), "
                    "SUM(totale_documento), "
                    "SUM(CASE WHEN pagamento = 'CONTANTI' THEN totale_documento ELSE 0 END), "
                    "SUM(CASE WHEN pagamento = 'POS' THEN totale_documento ELSE 0 END) "
                    "FROM documenti WHERE tipo_documento = 'SCONTRINO'"
                )
                params = []
                conditions = []
                if anno_sel != "Tutti":
                    conditions.append("strftime('%Y', data_emissione) = ?")
                    params.append(anno_sel)
                if mese_sel != "Tutti":
                    num_mese = mese_sel.split(" - ")[0]
                    conditions.append("strftime('%m', data_emissione) = ?")
                    params.append(num_mese)
                if conditions:
                    query_doc += " AND " + " AND ".join(conditions)

                cursor.execute(query_doc, params)
                res_doc = cursor.fetchone() or (0, 0, 0, 0)
                tot_scontrini = res_doc[0] or 0
                fatturato = res_doc[1] or 0.0
                incasso_contanti = res_doc[2] or 0.0
                incasso_pos = res_doc[3] or 0.0
            except Exception as e:
                log.warning("KPI documenti non disponibili: %s", e)

            # --- 2. Valore magazzino ----------------------------------------
            valore_merce = 0.0
            try:
                cursor.execute(
                    "SELECT COUNT(*), SUM(prezzo_vendita * giacenza) FROM articoli"
                )
                res_art = cursor.fetchone() or (0, 0.0)
                valore_merce = res_art[1] or 0.0
            except Exception as e:
                log.warning("KPI valore magazzino non disponibile (tabella articoli?): %s", e)

            # --- 3. Sottoscorta ---------------------------------------------
            # Usa COALESCE(scorta_minima, soglia_minima) per essere robusto
            # qualunque sia la colonna popolata da magazzino.py.
            tot_sottoscorta = 0
            try:
                cursor.execute(
                    "SELECT COUNT(*) FROM articoli "
                    "WHERE giacenza <= COALESCE(scorta_minima, soglia_minima, 0) "
                    "AND COALESCE(scorta_minima, soglia_minima, 0) > 0"
                )
                tot_sottoscorta = cursor.fetchone()[0] or 0
            except Exception as e:
                log.warning("KPI sottoscorta non disponibile: %s", e)

            # --- 4. Clienti -------------------------------------------------
            tot_clienti = 0
            try:
                cursor.execute("SELECT COUNT(*) FROM clienti")
                tot_clienti = cursor.fetchone()[0] or 0
            except Exception as e:
                log.warning("KPI clienti non disponibile: %s", e)

            # --- Aggiornamento UI -------------------------------------------
            self.lbl_fatturato_val.config(text=f"€ {fatturato:.2f}")
            self.lbl_scontrini_val.config(text=str(tot_scontrini))
            self.lbl_contanti_val.config(text=f"€ {incasso_contanti:.2f}")
            self.lbl_pos_val.config(text=f"€ {incasso_pos:.2f}")
            self.lbl_valore_mag.config(text=f"€ {valore_merce:.2f}")
            self.lbl_sottoscorta_val.config(text=str(tot_sottoscorta))
            self.lbl_clienti_val.config(text=str(tot_clienti))
        except Exception:
            log.exception("Errore imprevisto nell'aggiornamento dashboard")
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass


class MercurioApp(tk.Tk):
    """Finestra principale del gestionale."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Imposta l'icona della finestra (Windows e Linux)
        try:
            icon_path = os.path.join(current_dir, "..", "icona.ico")
            self.iconbitmap(icon_path)
        except Exception:
            pass

        self.title("Mercurio Gestionale Retail (v0.3.2 Alpha)")
        self.geometry("1250x780")
        self.minsize(1024, 600)

        # Chiudi in modo pulito: nessuna risorsa resta appesa
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        log.info("Avvio applicazione Mercurio Gestionale Retail...")
        company_data = get_company_data()
        if not company_data:
            log.info("Configurazione non trovata: avvio Setup Wizard.")
            self.withdraw()
            # NIENTE grab_set/wait_visibility: il wizard è una Toplevel normale
            wizard = SetupWizard(self, self.avvia_interfaccia_principale)
            wizard.focus_force()   # porta il wizard in primo piano
        else:
            log.info("Configurazione trovata: inizializzazione DB e avvio GUI.")
            try:
                init_db()
            except Exception:
                log.exception("Errore critico durante init_db()")
                messagebox.showerror(
                    "Errore database",
                    "Impossibile inizializzare il database.\n"
                    "Controlla mercurio.log per i dettagli.",
                )
                self.destroy()
                return
            self.avvia_interfaccia_principale()

    def avvia_interfaccia_principale(self):
        log.info("Costruzione interfaccia principale...")
        try:
            self.deiconify()
        except tk.TclError:
            pass

        company = get_company_data()
        ragione_sociale = company.get("ragione_sociale", "Azienda") if company else "Gestionale"

        # Header superiore
        header_frame = tk.Frame(self, bg="#343a40", height=50)
        header_frame.pack(fill="x")

        tk.Label(
            header_frame,
            text=f"Mercurio Gestionale Retail — {ragione_sociale}",
            fg="white", bg="#343a40", font=("Arial", 11, "bold"),
        ).pack(side="left", padx=15, pady=12)

        # Notebook principale
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Le tab sono aggiunte con helper per non duplicare codice e per
        # isolare gli errori di caricamento di ciascun modulo.
        self._add_tab(notebook, "📊 Dashboard", lambda p: DashboardFrame(p), critical=True)
        self._add_tab(notebook, "📦 Magazzino", lambda p: MagazzinoFrame(p))
        self._add_tab(notebook, "🤝 Fornitori", lambda p: FornitoriManagerFrame(p))
        self._add_tab(notebook, "⚡ Cassa POS", lambda p: PosFrame(p))
        self._add_tab(notebook, "👥 Clienti & Fidelity", lambda p: ClientiManagerTab(p))
        self._add_tab(notebook, "🧾 Documenti & SDI", lambda p: DocumentiManagerTab(p))
        self._add_tab(notebook, "📅 Corrispettivi Z", lambda p: CorrispettiviManagerTab(p))
        self._add_tab(notebook, "⚙️ Impostazioni", lambda p: ImpostazioniFrame(p))

    def _add_tab(self, notebook, title, factory, critical=False):
        """Crea una tab e vi inserisce il frame del modulo. Se il modulo
        solleva un'eccezione in costruzione, la mostra come label nella tab
        e logga il traceback completo: nessun popup, nessun blocco."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=title)
        try:
            frame = factory(tab)
            frame.pack(fill="both", expand=True)
            return frame
        except Exception:
            log.exception("Errore nel caricamento del modulo '%s'", title)
            err_text = traceback.format_exc()
            # Mostra solo la prima riga dell'errore nella UI; il resto è nel log.
            first_line = err_text.strip().splitlines()[-1] if err_text.strip() else "errore sconosciuto"
            lbl = tk.Label(
                tab,
                text=f"⚠️ Errore caricamento {title}:\n{first_line}\n\n"
                     f"Dettagli completi in mercurio.log",
                fg="#842029", bg="#f8d7da",
                font=("Arial", 10), justify="left", anchor="w",
                padx=15, pady=15,
            )
            lbl.pack(fill="both", expand=True, padx=20, pady=20)
            if critical:
                log.error("Modulo critico '%s' non caricato: l'app resta avviata "
                          "ma la funzionalità è assente.", title)
            return None

    def on_close(self):
        log.info("Chiusura applicazione.")
        self.destroy()


if __name__ == "__main__":
    app = MercurioApp()
    app.mainloop()