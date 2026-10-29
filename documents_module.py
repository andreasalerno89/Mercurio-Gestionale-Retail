import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import database

class DocumentsModule(ctk.CTkFrame):
    def __init__(self, parent, app_instance=None):
        super().__init__(parent)
        self.app_instance = app_instance
        self.tutti_documenti = []

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Intestazione & Ricerca
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        header_frame.grid_columnconfigure(1, weight=1)

        lbl_titolo = ctk.CTkLabel(header_frame, text="📄 Storico Scontrini e Movimenti di Banco", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_titolo.grid(row=0, column=0, sticky="w")

        self.entry_cerca = ctk.CTkEntry(header_frame, placeholder_text="🔍 Cerca numero scontrino o data...", width=300)
        self.entry_cerca.grid(row=0, column=1, sticky="e", padx=10)
        self.entry_cerca.bind("<KeyRelease>", self.filtra_documenti)

        # 2. Toolbar
        toolbar_frame = ctk.CTkFrame(self, fg_color="transparent")
        toolbar_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        btn_aggiorna = ctk.CTkButton(toolbar_frame, text="🔄 Aggiorna Storico", fg_color="#1565c0", command=self.carica_documenti)
        btn_aggiorna.pack(side="left")

        # 3. Lista Storico Scrollabile
        self.scroll_doc = ctk.CTkScrollableFrame(self, label_text="Registro Corrispettivi e Scontrini Emessi")
        self.scroll_doc.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.scroll_doc.grid_columnconfigure(0, weight=1)

        self.carica_documenti()

    def carica_documenti(self):
        """Carica i documenti di cassa dal database"""
        try:
            conn = database.get_db_connection()
            self.tutti_documenti = conn.execute(
                "SELECT * FROM movimenti_banco ORDER BY id DESC LIMIT 150"
            ).fetchall()
            conn.close()
            self.mostra_lista(self.tutti_documenti)
        except Exception as e:
            messagebox.showerror("Errore Database", f"Impossibile caricare lo storico documenti:\n{e}")

    def mostra_lista(self, lista_movimenti):
        """Disegna la lista dei movimenti di cassa"""
        for w in self.scroll_doc.winfo_children():
            w.destroy()

        if not lista_movimenti:
            lbl_vuoto = ctk.CTkLabel(self.scroll_doc, text="Nessun documento o scontrino emesso al banco.", text_color="gray", font=ctk.CTkFont(size=14))
            lbl_vuoto.pack(pady=30)
            return

        for mov in lista_movimenti:
            frame_riga = ctk.CTkFrame(self.scroll_doc, fg_color=("#f0f0f0", "#2b2b2b"), corner_radius=8)
            frame_riga.pack(fill="x", padx=10, pady=5)

            num_scontrino = mov["numero_scontrino"]
            data_ora = mov["data_ora"]
            totale = mov["totale_lordo"]
            pagamento = mov["tipo_pagamento"]
            resto = mov["resto"] if "resto" in mov.keys() else 0.0

            testo_sx = f"🧾 {num_scontrino}   |   📅 {data_ora}"
            testo_dx = f"Pagamento: {pagamento}   |   Totale: € {totale:.2f}"
            if pagamento == "CONTANTI":
                testo_dx += f"   (Resto: € {resto:.2f})"

            lbl_info = ctk.CTkLabel(
                frame_riga, 
                text=testo_sx,
                anchor="w",
                font=ctk.CTkFont(size=13, weight="bold")
            )
            lbl_info.pack(side="left", padx=15, pady=12)

            lbl_dett = ctk.CTkLabel(
                frame_riga, 
                text=testo_dx,
                font=ctk.CTkFont(size=13),
                text_color="#2e7d32" if pagamento == "CONTANTI" else "#1565c0"
            )
            lbl_dett.pack(side="right", padx=15, pady=12)

    def filtra_documenti(self, event=None):
        """Filtra lo storico documenti"""
        query = self.entry_cerca.get().lower().strip()
        if not query:
            self.mostra_lista(self.tutti_documenti)
            return

        filtrati = [
            mov for mov in self.tutti_documenti 
            if query in str(mov['numero_scontrino']).lower() or 
               query in str(mov['data_ora']).lower() or
               query in str(mov['tipo_pagamento']).lower()
        ]
        self.mostra_lista(filtrati)