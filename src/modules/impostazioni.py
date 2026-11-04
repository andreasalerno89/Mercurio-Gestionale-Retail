import tkinter as tk
from tkinter import ttk, messagebox
import logging

from config import get_company_data, save_company_data, esegui_backup_sistema

log = logging.getLogger("mercurio.impostazioni")

# Campi anagrafici mostrati nel form.
FIELDS_AZIENDA = [
    ("Ragione Sociale *", "ragione_sociale"),
    ("Partita IVA *", "partita_iva"),
    ("Codice Fiscale", "codice_fiscale"),
    ("Indirizzo", "indirizzo"),
    ("Civico", "civico"),
    ("CAP", "cap"),
    ("Località / Città", "localita"),
    ("Provincia", "provincia"),
    ("IBAN", "iban"),
    ("Email / PEC", "email"),
]

# Campi RT numerici (validazione dedicata)
FIELDS_RT_INT = ["rt_porta", "rt_baudrate"]

# Protocolli RT supportati (predisposizione: la scelta viene salvata,
# ma i comandi reali saranno implementati in una milestone successiva)
RT_PROTOCOLLI = [
    "XON_XOFF_SERIALE",
    "XON_XOFF_TCP",
    "EPSON_SOAP",
    "RCH_NATIVO",
    "CUSTOM_NATIVO",
    "3I_NATIVO",
    "ESCPOS",
]

# Campi Fidelity numerici (validazione dedicata)
FIELDS_FIDI_FLOAT = [
    "fidi_euro_per_punto",
    "fidi_soglia_punti",
    "fidi_sconto_valore",
]


class ImpostazioniFrame(tk.Frame):
    """Pannello di configurazione globale: Dati Azienda, RT, Fidelity e Backup."""

    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        self.carica_dati()

    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_azienda = tk.Frame(notebook, padx=15, pady=15)
        notebook.add(self.tab_azienda, text="🏢 Dati Fiscali Azienda")
        self.build_azienda_tab()

        self.tab_rt = tk.Frame(notebook, padx=15, pady=15)
        notebook.add(self.tab_rt, text="🖨️ Registratore Telematico (RT)")
        self.build_rt_tab()

        self.tab_fidelity = tk.Frame(notebook, padx=15, pady=15)
        notebook.add(self.tab_fidelity, text="💳 Regole Fidelity")
        self.build_fidelity_tab()

        self.tab_backup = tk.Frame(notebook, padx=15, pady=15)
        notebook.add(self.tab_backup, text="💾 Backup Dati & Foto")
        self.build_backup_tab()

        tk.Button(self, text="💾 Salva Tutte le Impostazioni",
                  bg="#28a745", fg="white", font=("Arial", 11, "bold"),
                  command=self.salva_tutto).pack(fill="x", padx=15, pady=10)

    def build_azienda_tab(self):
        self.entries_az = {}
        for idx, (lbl, key) in enumerate(FIELDS_AZIENDA):
            tk.Label(self.tab_azienda, text=lbl,
                     font=("Arial", 9, "bold")).grid(
                row=idx, column=0, sticky="w", pady=4)
            entry = tk.Entry(self.tab_azienda, width=45, font=("Arial", 10))
            entry.grid(row=idx, column=1, sticky="w", pady=4, padx=10)
            self.entries_az[key] = entry

    def build_rt_tab(self):
        self.entries_rt = {}

        # Tipo connessione (IP / SERIALE)
        tk.Label(self.tab_rt, text="Tipo Connessione RT:",
                 font=("Arial", 9, "bold")).grid(row=0, column=0,
                                                  sticky="w", pady=6)
        self.combo_rt_conn = ttk.Combobox(self.tab_rt,
                                          values=["IP", "SERIALE"],
                                          state="readonly", width=25)
        self.combo_rt_conn.grid(row=0, column=1, sticky="w", pady=6, padx=10)
        self.combo_rt_conn.set("IP")

        # Protocollo RT (nuovo campo)
        tk.Label(self.tab_rt, text="Protocollo RT:",
                 font=("Arial", 9, "bold")).grid(row=1, column=0,
                                                  sticky="w", pady=6)
        self.combo_rt_protocollo = ttk.Combobox(
            self.tab_rt, values=RT_PROTOCOLLI,
            state="readonly", width=25)
        self.combo_rt_protocollo.grid(row=1, column=1, sticky="w", pady=6, padx=10)
        self.combo_rt_protocollo.set("XON_XOFF_SERIALE")

        # Campi RT (IP / porta / seriale / baudrate)
        rt_fields = [
            ("Indirizzo IP RT", "rt_ip"),
            ("Porta TCP RT", "rt_porta"),
            ("Porta Seriale (COM)", "rt_seriale"),
            ("Baudrate Seriale (XON/XOFF)", "rt_baudrate"),
        ]
        for idx, (lbl, key) in enumerate(rt_fields, start=2):
            tk.Label(self.tab_rt, text=lbl,
                     font=("Arial", 9, "bold")).grid(
                row=idx, column=0, sticky="w", pady=4)
            entry = tk.Entry(self.tab_rt, width=25, font=("Arial", 10))
            entry.grid(row=idx, column=1, sticky="w", pady=4, padx=10)
            self.entries_rt[key] = entry

    def build_fidelity_tab(self):
        self.entries_fidi = {}
        fidi_fields = [
            ("Euro spesi per 1 Punto Fidelity (€)", "fidi_euro_per_punto"),
            ("Soglia Punti per Sconto", "fidi_soglia_punti"),
            ("Valore Sconto al Raggiungimento Soglia (€)", "fidi_sconto_valore"),
        ]
        for idx, (lbl, key) in enumerate(fidi_fields):
            tk.Label(self.tab_fidelity, text=lbl,
                     font=("Arial", 9, "bold")).grid(
                row=idx, column=0, sticky="w", pady=6)
            entry = tk.Entry(self.tab_fidelity, width=15, font=("Arial", 10))
            entry.grid(row=idx, column=1, sticky="w", pady=6, padx=10)
            self.entries_fidi[key] = entry

    def build_backup_tab(self):
        tk.Label(self.tab_backup, text="Backup dei Dati e delle Foto",
                 font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        tk.Label(self.tab_backup,
                 text=("I file di backup verranno archiviati automaticamente "
                       "nella cartella 'Documents/MercurioBackup'."),
                 font=("Arial", 9)).pack(anchor="w", pady=5)

        tk.Button(self.tab_backup, text="🚀 Esegui Backup Adesso",
                  bg="#17a2b8", fg="white", font=("Arial", 10, "bold"),
                  command=self.avvia_backup).pack(anchor="w", pady=15)

    # ------------------------------------------------------------------ #
    # Caricamento
    # ------------------------------------------------------------------ #

    def carica_dati(self):
        try:
            data = get_company_data()
        except Exception:
            log.exception("Errore in get_company_data() durante il caricamento")
            return

        if not data:
            log.info("Nessun dato aziendale da caricare (primo avvio?).")
            return

        for k, entry in self.entries_az.items():
            entry.delete(0, tk.END)
            entry.insert(0, str(data.get(k) or ""))

        self.combo_rt_conn.set(data.get("rt_tipo_connessione") or "IP")
        self.combo_rt_protocollo.set(
            data.get("rt_protocollo") or "XON_XOFF_SERIALE")
        for k, entry in self.entries_rt.items():
            entry.delete(0, tk.END)
            entry.insert(0, str(data.get(k) or ""))

        for k, entry in self.entries_fidi.items():
            entry.delete(0, tk.END)
            entry.insert(0, str(data.get(k) or ""))

    # ------------------------------------------------------------------ #
    # Salvataggio
    # ------------------------------------------------------------------ #

    def _valida_intero(self, value, campo):
        """Restituisce int(value) oppure solleva ValueError con messaggio chiaro."""
        s = (value or "").strip()
        if not s:
            return None
        try:
            return int(s)
        except ValueError:
            raise ValueError(
                f"Il campo '{campo}' deve essere un numero intero (es. 5000).")

    def _valida_float(self, value, campo):
        """Restituisce float(value) oppure solleva ValueError con messaggio chiaro."""
        s = (value or "").strip().replace(",", ".")
        if not s:
            return 0.0
        try:
            return float(s)
        except ValueError:
            raise ValueError(
                f"Il campo '{campo}' deve essere un numero (es. 12.50).")

    def salva_tutto(self):
        data = {}

        try:
            # 1. Campi anagrafici (stringhe, nessuna validazione)
            for k, entry in self.entries_az.items():
                data[k] = entry.get().strip()

            # 2. Tipo connessione RT e protocollo
            data["rt_tipo_connessione"] = self.combo_rt_conn.get()
            data["rt_protocollo"] = self.combo_rt_protocollo.get()

            # 3. Campi RT: stringhe per IP/seriale, interi per porta/baudrate
            for k, entry in self.entries_rt.items():
                raw = entry.get().strip()
                if k in FIELDS_RT_INT:
                    data[k] = self._valida_intero(raw, k)
                else:
                    data[k] = raw

            # 4. Campi Fidelity (float con validazione chiara)
            for k, entry in self.entries_fidi.items():
                data[k] = self._valida_float(entry.get(), k)

        except ValueError as ve:
            messagebox.showerror("Errore di validazione", str(ve),
                                 parent=self)
            return

        # 5. Salvataggio
        try:
            save_company_data(data)
        except Exception as e:
            log.exception("Errore salvataggio impostazioni")
            messagebox.showerror("Errore",
                                 f"Impossibile salvare le impostazioni: {e}",
                                 parent=self)
            return

        messagebox.showinfo("Successo",
                            "Impostazioni aggiornate con successo!",
                            parent=self)
        self.carica_dati()

    # ------------------------------------------------------------------ #
    # Backup
    # ------------------------------------------------------------------ #

    def avvia_backup(self):
        try:
            esito, percorso = esegui_backup_sistema()
        except Exception:
            log.exception("Errore imprevisto durante il backup")
            messagebox.showerror("Errore Backup",
                                 "Errore imprevisto durante il backup. "
                                 "Controlla mercurio.log.",
                                 parent=self)
            return

        if esito:
            messagebox.showinfo("Backup Completato",
                                f"Backup salvato con successo in:\n{percorso}",
                                parent=self)
        else:
            messagebox.showerror("Errore Backup",
                                 f"Errore durante il backup:\n{percorso}",
                                 parent=self)