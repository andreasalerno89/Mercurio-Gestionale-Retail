import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

# Import dei moduli interni del gestionale
from database import init_db
from pos_module import POSModule
from warehouse_module import WarehouseModule
from clients_module import ClientsModule
from documents_module import DocumentsModule
from settings_module import SettingsModule

# Configurazione tema CustomTkinter
ctk.set_appearance_mode("System")  # "System", "Dark", "Light"
ctk.set_default_color_theme("blue")

class MercurioApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Mercurio Gestionale Retail - v0.2.1-alpha")
        self.geometry("1200x750")
        self.minsize(1000, 650)

        # Inizializzazione del Database SQLite
        init_db()

        # Layout principale a griglia
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.create_header()
        self.create_main_tabs()

    def create_header(self):
        """Crea l'intestazione grafica principale in alto"""
        header_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))
        header_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header_frame, 
            text="Mercurio Gestionale Retail", 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w")

        version_label = ctk.CTkLabel(
            header_frame, 
            text="v0.2.1-alpha (GPLv3)", 
            font=ctk.CTkFont(size=12, slant="italic")
        )
        version_label.grid(row=0, column=1, sticky="e")

    def create_main_tabs(self):
        """Crea il sistema di tab orizzontale per raccogliere tutti i moduli in un'unica finestra"""
        self.tab_view = ctk.CTkTabview(self, corner_radius=12)
        self.tab_view.grid(row=1, column=0, sticky="nsew", padx=20, pady=(5, 20))

        # Creazione delle Tab principali
        tab_pos = self.tab_view.add("🛒 Banco POS")
        tab_warehouse = self.tab_view.add("📦 Magazzino")
        tab_clients = self.tab_view.add("👥 Clienti & Fidelity")
        tab_docs = self.tab_view.add("📄 Documenti Banco")
        tab_settings = self.tab_view.add("⚙️ Impostazioni")

        # Configurazione layout interno di ogni tab
        for tab in [tab_pos, tab_warehouse, tab_clients, tab_docs, tab_settings]:
            tab.grid_rowconfigure(0, weight=1)
            tab.grid_columnconfigure(0, weight=1)

        # Inserimento dei singoli moduli all'interno delle rispettive tab
        self.pos_view = POSModule(tab_pos, app_instance=self)
        self.pos_view.grid(row=0, column=0, sticky="nsew")

        self.warehouse_view = WarehouseModule(tab_warehouse, app_instance=self)
        self.warehouse_view.grid(row=0, column=0, sticky="nsew")

        self.clients_view = ClientsModule(tab_clients, app_instance=self)
        self.clients_view.grid(row=0, column=0, sticky="nsew")

        self.documents_view = DocumentsModule(tab_docs, app_instance=self)
        self.documents_view.grid(row=0, column=0, sticky="nsew")

        self.settings_view = SettingsModule(tab_settings, app_instance=self)
        self.settings_view.grid(row=0, column=0, sticky="nsew")

if __name__ == "__main__":
    app = MercurioApp()
    app.mainloop()