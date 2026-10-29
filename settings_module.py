import customtkinter as ctk
from tkinter import messagebox
import json
import os

CONFIG_FILE = "config.json"

class ModuloImpostazioni(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Configurazione Hardware & Registratore Telematico", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 15))

        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        self.form_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.form_frame, text="Modalità Connessione RT:").grid(row=0, column=0, sticky="w", padx=15, pady=15)
        self.combo_modalita = ctk.CTkComboBox(self.form_frame, values=["IP (Socket)", "Seriale (RS232 XON/XOFF)"], width=250)
        self.combo_modalita.grid(row=0, column=1, sticky="w", padx=15, pady=15)

        ctk.CTkLabel(self.form_frame, text="Indirizzo IP RT:").grid(row=1, column=0, sticky="w", padx=15, pady=15)
        self.entry_ip = ctk.CTkEntry(self.form_frame, width=250, placeholder_text="Es. 192.168.1.100")
        self.entry_ip.grid(row=1, column=1, sticky="w", padx=15, pady=15)

        ctk.CTkLabel(self.form_frame, text="Porta Seriale (COM):").grid(row=2, column=0, sticky="w", padx=15, pady=15)
        self.combo_com = ctk.CTkComboBox(self.form_frame, values=["COM1", "COM2", "COM3", "COM4", "COM5", "USB0"], width=250)
        self.combo_com.grid(row=2, column=1, sticky="w", padx=15, pady=15)

        ctk.CTkLabel(self.form_frame, text="Controllo di Flusso:").grid(row=3, column=0, sticky="w", padx=15, pady=15)
        self.lbl_xon = ctk.CTkLabel(self.form_frame, text="XON/XOFF (Nativo Abilitato)", text_color="green", font=ctk.CTkFont(weight="bold"))
        self.lbl_xon.grid(row=3, column=1, sticky="w", padx=15, pady=15)

        self.btn_salva = ctk.CTkButton(self, text="Salva Configurazione Hardware", fg_color="#27ae60", height=40, command=self.salva_impostazioni)
        self.btn_salva.grid(row=2, column=0, sticky="w", padx=20, pady=20)

        self.carica_impostazioni()

    def carica_impostazioni(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    cfg = json.load(f)
                    self.combo_modalita.set(cfg.get("modalita", "IP (Socket)"))
                    self.entry_ip.insert(0, cfg.get("ip", "192.168.1.100"))
                    self.combo_com.set(cfg.get("com", "COM1"))
            except Exception:
                pass

    def salva_impostazioni(self):
        cfg = {
            "modalita": self.combo_modalita.get(),
            "ip": self.entry_ip.get().strip(),
            "com": self.combo_com.get()
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=4)
        messagebox.showinfo("Impostazioni Salvate", "I parametri di comunicazione con il Registratore Telematico sono stati aggiornati con successo!")