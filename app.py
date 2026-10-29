import customtkinter as ctk
from database import DatabaseManager
from pos_module import ModuloPOS
from warehouse_module import ModuloMagazzino
from clients_module import ModuloClienti
from settings_module import ModuloImpostazioni

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class MercurioERP(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()

        self.title("Mercurio Gestionale Retail - v0.1.0-alpha")
        self.geometry("1250x720")

        # Configurazione Icona Finestra e UI
        try:
            self.iconbitmap("icona.ico")
        except Exception:
            pass

        try:
            from PIL import Image, ImageTk
            img_icon = Image.open("icona.ico")
            self.iconphoto(True, ImageTk.PhotoImage(img_icon))
        except Exception:
            pass

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Sidebar di navigazione
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.sidebar, text="MERCURIO\nRETAIL", font=ctk.CTkFont(size=22, weight="bold")).pack(padx=20, pady=30)

        ctk.CTkButton(self.sidebar, text="Cassa / POS", height=42, command=self.mostra_pos).pack(padx=20, pady=10, fill="x")
        ctk.CTkButton(self.sidebar, text="Gestione Magazzino", height=42, command=self.mostra_magazzino).pack(padx=20, pady=10, fill="x")
        ctk.CTkButton(self.sidebar, text="Clienti & Fidelity", height=42, command=self.mostra_clienti).pack(padx=20, pady=10, fill="x")
        ctk.CTkButton(self.sidebar, text="Impostazioni & RT", height=42, fg_color="#7f8c8d", hover_color="#626567", command=self.mostra_impostazioni).pack(padx=20, pady=(30, 10), fill="x")

        # Contenitore dei moduli
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)

        self.mostra_pos()

    def reset_content(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

    def mostra_pos(self):
        self.reset_content()
        pos = ModuloPOS(self.content_frame, self.db)
        pos.pack(fill="both", expand=True)

    def mostra_magazzino(self):
        self.reset_content()
        mag = ModuloMagazzino(self.content_frame, self.db)
        mag.pack(fill="both", expand=True)

    def mostra_clienti(self):
        self.reset_content()
        cli = ModuloClienti(self.content_frame, self.db)
        cli.pack(fill="both", expand=True)

    def mostra_impostazioni(self):
        self.reset_content()
        settings = ModuloImpostazioni(self.content_frame)
        settings.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = MercurioERP()
    app.mainloop()