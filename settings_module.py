import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import json
import os

CONFIG_FILE = "config_mercurio.json"

class SettingsModule(ctk.CTkFrame):
    def __init__(self, parent, app_instance=None):
        super().__init__(parent)
        self.app_instance = app_instance

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Container principale scorrevole
        main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        main_frame.grid_columnconfigure(0, weight=1)

        # Intestazione
        lbl_titolo = ctk.CTkLabel(
            main_frame, 
            text="⚙️ Configurazione Sistema & Registratore Telematico", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl_titolo.grid(row=0, column=0, sticky="w", pady=(0, 15))

        # --- Sezione Dati Negozio / Attività ---
        frame_negozio = ctk.CTkFrame(main_frame)
        frame_negozio.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        frame_negozio.grid_columnconfigure(1, weight=1)

        lbl_negozio_title = ctk.CTkLabel(frame_negozio, text="Dati Attività Commerciale", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_negozio_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(12, 5))

        ctk.CTkLabel(frame_negozio, text="Nome Attività / Negozio:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", padx=15, pady=10)
        self.entry_nome_negozio = ctk.CTkEntry(frame_negozio, placeholder_text="Es. Mercurio Store")
        self.entry_nome_negozio.grid(row=1, column=1, sticky="ew", padx=15, pady=10)

        ctk.CTkLabel(frame_negozio, text="Partita IVA:", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, sticky="w", padx=15, pady=(10, 15))
        self.entry_piva = ctk.CTkEntry(frame_negozio, placeholder_text="01234567890")
        self.entry_piva.grid(row=2, column=1, sticky="ew", padx=15, pady=(10, 15))

        # --- Sezione Hardware / Registratore Telematico (RT) ---
        frame_rt = ctk.CTkFrame(main_frame)
        frame_rt.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        frame_rt.grid_columnconfigure(1, weight=1)

        lbl_hardware = ctk.CTkLabel(frame_rt, text="Configurazione Stampante Fiscale / RT", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_hardware.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(12, 5))

        # Selezione Modalità Connessione (IP / SERIALE / USB)
        ctk.CTkLabel(frame_rt, text="Tipo di Connessione:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", padx=15, pady=10)
        self.combo_modalita = ctk.CTkOptionMenu(
            frame_rt, values=["IP (Rete)", "SERIALE (COM)", "USB (Virtuale/Diretta)"],
            command=self.aggiorna_campi_connessione
        )
        self.combo_modalita.grid(row=1, column=1, sticky="ew", padx=15, pady=10)

        # --- Frame Dinamico per Parametri IP ---
        self.frame_ip = ctk.CTkFrame(frame_rt, fg_color="transparent")
        self.frame_ip.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.frame_ip.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.frame_ip, text="Indirizzo IP RT:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=15, pady=8)
        self.entry_ip = ctk.CTkEntry(self.frame_ip, placeholder_text="192.168.1.100")
        self.entry_ip.grid(row=0, column=1, sticky="ew", padx=15, pady=8)

        ctk.CTkLabel(self.frame_ip, text="Porta TCP:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", padx=15, pady=8)
        self.entry_porta_ip = ctk.CTkEntry(self.frame_ip)
        self.entry_porta_ip.insert(0, "9100")
        self.entry_porta_ip.grid(row=1, column=1, sticky="ew", padx=15, pady=8)

        # --- Frame Dinamico per Parametri Seriale / USB ---
        self.frame_serial = ctk.CTkFrame(frame_rt, fg_color="transparent")
        self.frame_serial.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.frame_serial.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.frame_serial, text="Porta (COM / USB Device):", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=15, pady=8)
        self.entry_porta_com = ctk.CTkEntry(self.frame_serial, placeholder_text="COM1 o /dev/ttyUSB0")
        self.entry_porta_com.grid(row=0, column=1, sticky="ew", padx=15, pady=8)

        ctk.CTkLabel(self.frame_serial, text="Baudrate (Velocità):", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", padx=15, pady=8)
        self.combo_baud = ctk.CTkOptionMenu(self.frame_serial, values=["9600", "19200", "38400", "57600", "115200"])
        self.combo_baud.set("9600")
        self.combo_baud.grid(row=1, column=1, sticky="ew", padx=15, pady=8)

        ctk.CTkLabel(self.frame_serial, text="Controllo di Flusso:", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, sticky="w", padx=15, pady=8)
        self.combo_flusso = ctk.CTkOptionMenu(self.frame_serial, values=["XON/XOFF", "RTS/CTS (Hardware)", "Nessuno"])
        self.combo_flusso.set("XON/XOFF")
        self.combo_flusso.grid(row=2, column=1, sticky="ew", padx=15, pady=8)

        # Pulsante Test Connessione
        btn_test_rt = ctk.CTkButton(
            frame_rt, text="🔌 Test Connessione Registratore Telematico", fg_color="#1565c0", 
            command=self.test_connessione_rt
        )
        btn_test_rt.grid(row=4, column=0, columnspan=2, sticky="ew", padx=15, pady=(15, 15))

        # --- Pulsante Salva Inferiore ---
        frame_bottoni = ctk.CTkFrame(main_frame, fg_color="transparent")
        frame_bottoni.grid(row=3, column=0, sticky="ew", pady=10)

        btn_salva = ctk.CTkButton(
            frame_bottoni, text="💾 Salva Impostazioni", fg_color="#2e7d32", 
            height=40, font=ctk.CTkFont(weight="bold"), command=self.salva_configurazione
        )
        btn_salva.pack(side="left", expand=True, fill="x", padx=5)

        # Carica i dati salvati
        self.carica_configurazione()
        self.aggiorna_campi_connessione(self.combo_modalita.get())

    def aggiorna_campi_connessione(self, scelta):
        """Mostra o nasconde i campi IP o Seriali in base alla scelta"""
        if "IP" in scelta:
            self.frame_ip.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
            self.frame_serial.grid_forget()
        else:
            self.frame_serial.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
            self.frame_ip.grid_forget()

    def carica_configurazione(self):
        """Carica i dati dai file di configurazione"""
        for file_cfg in [CONFIG_FILE, "config.json"]:
            if os.path.exists(file_cfg):
                try:
                    with open(file_cfg, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.entry_nome_negozio.insert(0, data.get("nome_negozio", ""))
                        self.entry_piva.insert(0, data.get("piva", ""))
                        
                        mod = data.get("modalita", "IP")
                        if "IP" in mod:
                            self.combo_modalita.set("IP (Rete)")
                        elif "USB" in mod:
                            self.combo_modalita.set("USB (Virtuale/Diretta)")
                        else:
                            self.combo_modalita.set("SERIALE (COM)")

                        self.entry_ip.insert(0, data.get("ip", "192.168.1.100"))
                        self.entry_porta_ip.delete(0, "end")
                        self.entry_porta_ip.insert(0, str(data.get("porta_ip", 9100)))

                        self.entry_porta_com.insert(0, data.get("com", data.get("porta_seriale", "COM1")))
                        self.combo_baud.set(str(data.get("baudrate", 9600)))
                        self.combo_flusso.set(data.get("flusso", "XON/XOFF"))
                        break
                except Exception:
                    pass

    def salva_configurazione(self):
        """Salva le impostazioni correnti sia in config_mercurio.json che in config.json"""
        mod_selezionata = self.combo_modalita.get()
        if "IP" in mod_selezionata:
            modalita_str = "IP"
        elif "USB" in mod_selezionata:
            modalita_str = "USB"
        else:
            modalita_str = "SERIALE"

        data = {
            "nome_negozio": self.entry_nome_negozio.get().strip(),
            "piva": self.entry_piva.get().strip(),
            "modalita": modalita_str,
            "ip": self.entry_ip.get().strip(),
            "porta_ip": int(self.entry_porta_ip.get().strip() or 9100),
            "com": self.entry_porta_com.get().strip(),
            "porta_seriale": self.entry_porta_com.get().strip(),
            "baudrate": int(self.combo_baud.get().strip() or 9600),
            "flusso": self.combo_flusso.get().strip()
        }

        try:
            for file_cfg in [CONFIG_FILE, "config.json"]:
                with open(file_cfg, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
            messagebox.showinfo("Successo", "Impostazioni e parametri RT salvati correttamente!")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile salvare le impostazioni:\n{e}")

    def test_connessione_rt(self):
        """Esegue un test di connessione in base alla modalità scelta (IP o Seriale/USB)"""
        mod = self.combo_modalita.get()
        if "IP" in mod:
            ip = self.entry_ip.get().strip()
            try:
                porta = int(self.entry_porta_ip.get().strip())
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3.0)
                s.connect((ip, porta))
                s.close()
                messagebox.showinfo("Test Riuscito", f"Connessione di rete IP riuscita con successo verso {ip}:{porta}!")
            except Exception as e:
                messagebox.showwarning("Test Fallito", f"Impossibile raggiungere l'indirizzo {ip}:{porta}:\n{e}")
        else:
            porta = self.entry_porta_com.get().strip()
            baud = int(self.combo_baud.get().strip())
            flusso = self.combo_flusso.get()
            try:
                import serial
                ser = serial.Serial(
                    port=porta,
                    baudrate=baud,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    xonxoff=(flusso == "XON/XOFF"),
                    rtscts=("Hardware" in flusso),
                    timeout=2
                )
                ser.close()
                messagebox.showinfo("Test Riuscito", f"Connessione Seriale/USB stabilita con successo sulla porta {porta} ({baud} baud, {flusso})!")
            except Exception as e:
                messagebox.showwarning("Test Fallito", f"Impossibile aprire la porta {porta}:\n{e}")