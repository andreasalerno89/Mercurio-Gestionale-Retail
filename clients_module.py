import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import database

class ClientsModule(ctk.CTkFrame):
    def __init__(self, parent, app_instance=None):
        super().__init__(parent)
        self.app_instance = app_instance
        self.tutti_clienti = []

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Intestazione & Ricerca
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        header_frame.grid_columnconfigure(1, weight=1)

        lbl_titolo = ctk.CTkLabel(header_frame, text="👥 Anagrafica Clienti & Fidelity", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_titolo.grid(row=0, column=0, sticky="w")

        self.entry_cerca = ctk.CTkEntry(header_frame, placeholder_text="🔍 Cerca cliente o codice carta...", width=300)
        self.entry_cerca.grid(row=0, column=1, sticky="e", padx=10)
        self.entry_cerca.bind("<KeyRelease>", self.filtra_clienti)

        # 2. Toolbar Azioni
        toolbar_frame = ctk.CTkFrame(self, fg_color="transparent")
        toolbar_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        btn_aggiungi = ctk.CTkButton(toolbar_frame, text="➕ Nuovo Cliente", fg_color="#2e7d32", font=ctk.CTkFont(weight="bold"), command=self.apri_finestra_nuovo_cliente)
        btn_aggiungi.pack(side="left", padx=(0, 10))

        btn_aggiorna = ctk.CTkButton(toolbar_frame, text="🔄 Aggiorna", fg_color="#1565c0", command=self.carica_clienti)
        btn_aggiorna.pack(side="left")

        # 3. Lista Clienti Scrollabile
        self.scroll_clienti = ctk.CTkScrollableFrame(self, label_text="Clienti Registrati e Punti Fidelity")
        self.scroll_clienti.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.scroll_clienti.grid_columnconfigure(0, weight=1)

        self.carica_clienti()

    def carica_clienti(self):
        """Carica l'elenco dei clienti dal database"""
        try:
            db = database._db_manager if hasattr(database, "_db_manager") else database.DatabaseManager()
            self.tutti_clienti = db.ottieni_clienti()
            self.mostra_lista(self.tutti_clienti)
        except Exception as e:
            messagebox.showerror("Errore Database", f"Impossibile caricare i clienti:\n{e}")

    def mostra_lista(self, lista_clienti):
        """Disegna la lista dei clienti"""
        for w in self.scroll_clienti.winfo_children():
            w.destroy()

        if not lista_clienti:
            lbl_vuoto = ctk.CTkLabel(self.scroll_clienti, text="Nessun cliente registrato in anagrafica.", text_color="gray", font=ctk.CTkFont(size=14))
            lbl_vuoto.pack(pady=30)
            return

        for cli in lista_clienti:
            frame_riga = ctk.CTkFrame(self.scroll_clienti, fg_color=("#f0f0f0", "#2b2b2b"), corner_radius=8)
            frame_riga.pack(fill="x", padx=10, pady=5)

            nome_completo = f"{cli['nome']} {cli['cognome']}"
            tel = f"📞 {cli['telefono']}" if cli['telefono'] else "📞 Senza telefono"
            carta = f"💳 {cli['codice_carta']}" if cli['codice_carta'] else "💳 No Fidelity"
            punti = f"⭐ {cli['punti']} punti" if cli['punti'] is not None else "⭐ 0 punti"

            lbl_info = ctk.CTkLabel(
                frame_riga, 
                text=f"👤 {nome_completo}   |   {tel}",
                anchor="w",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            lbl_info.pack(side="left", padx=15, pady=12)

            frame_destro = ctk.CTkFrame(frame_riga, fg_color="transparent")
            frame_destro.pack(side="right", padx=10)

            lbl_card = ctk.CTkLabel(frame_destro, text=f"{carta}  ({punti})", font=ctk.CTkFont(size=12))
            lbl_card.pack(side="left", padx=10)

            btn_elimina = ctk.CTkButton(
                frame_destro, text="🗑️ Elimina", width=80, height=30, fg_color="#c62828",
                command=lambda id_c=cli['id_cliente']: self.elimina_cliente(id_c)
            )
            btn_elimina.pack(side="left", padx=5)

    def filtra_clienti(self, event=None):
        """Filtra la lista clienti"""
        query = self.entry_cerca.get().lower().strip()
        if not query:
            self.mostra_lista(self.tutti_clienti)
            return

        filtrati = [
            cli for cli in self.tutti_clienti 
            if query in f"{cli['nome']} {cli['cognome']}".lower() or 
               query in str(cli.get('codice_carta', '')).lower() or
               query in str(cli.get('telefono', '')).lower()
        ]
        self.mostra_lista(filtrati)

    def apri_finestra_nuovo_cliente(self):
        win = ctk.CTkToplevel(self)
        win.title("Registrazione Nuovo Cliente - Dati Completi")
        win.geometry("550x700")
        win.grab_set()

        db = database._db_manager if hasattr(database, "_db_manager") else database.DatabaseManager()

        scroll_form = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll_form.pack(fill="both", expand=True, padx=15, pady=15)

        # Campi Anagrafici
        ctk.CTkLabel(scroll_form, text="Nome *:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        entry_nome = ctk.CTkEntry(scroll_form, width=480, height=32)
        entry_nome.pack()

        ctk.CTkLabel(scroll_form, text="Cognome *:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        entry_cognome = ctk.CTkEntry(scroll_form, width=480, height=32)
        entry_cognome.pack()

        ctk.CTkLabel(scroll_form, text="Azienda:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        entry_azienda = ctk.CTkEntry(scroll_form, width=480, height=32)
        entry_azienda.pack()

        # Indirizzo
        frame_ind = ctk.CTkFrame(scroll_form, fg_color="transparent")
        frame_ind.pack(fill="x", pady=5)
        
        ctk.CTkLabel(frame_ind, text="Indirizzo:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=(0,5))
        entry_indirizzo = ctk.CTkEntry(frame_ind, width=350, height=32)
        entry_indirizzo.grid(row=1, column=0, sticky="w", padx=(0,5))

        ctk.CTkLabel(frame_ind, text="N. Civico:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="w")
        entry_civico = ctk.CTkEntry(frame_ind, width=115, height=32)
        entry_civico.grid(row=1, column=1, sticky="w")

        # CAP, Località, Prov
        frame_geo = ctk.CTkFrame(scroll_form, fg_color="transparent")
        frame_geo.pack(fill="x", pady=5)

        ctk.CTkLabel(frame_geo, text="CAP:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w")
        entry_cap = ctk.CTkEntry(frame_geo, width=90, height=32)
        entry_cap.grid(row=1, column=0, sticky="w", padx=(0,10))

        ctk.CTkLabel(frame_geo, text="Località / Città:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="w")
        entry_localita = ctk.CTkEntry(frame_geo, width=280, height=32)
        entry_localita.grid(row=1, column=1, sticky="w", padx=(0,10))

        ctk.CTkLabel(frame_geo, text="Prov:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, sticky="w")
        entry_prov = ctk.CTkEntry(frame_geo, width=70, height=32)
        entry_prov.grid(row=1, column=2, sticky="w")

        # Dati Fiscali e Contatti
        ctk.CTkLabel(scroll_form, text="Codice Fiscale:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        entry_cf = ctk.CTkEntry(scroll_form, width=480, height=32)
        entry_cf.pack()

        ctk.CTkLabel(scroll_form, text="Partita IVA:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        entry_piva = ctk.CTkEntry(scroll_form, width=480, height=32)
        entry_piva.pack()

        ctk.CTkLabel(scroll_form, text="Telefono:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        entry_tel = ctk.CTkEntry(scroll_form, width=480, height=32)
        entry_tel.pack()

        ctk.CTkLabel(scroll_form, text="Email / PEC:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        entry_email = ctk.CTkEntry(scroll_form, width=480, height=32)
        entry_email.pack()

        # Fidelity Card
        ctk.CTkLabel(scroll_form, text="Codice Fidelity Card:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        entry_fid = ctk.CTkEntry(scroll_form, width=480, height=32)
        entry_fid.pack()
        entry_fid.insert(0, db.genera_prossimo_codice_fidelity())

        def salva():
            nome = entry_nome.get().strip()
            cognome = entry_cognome.get().strip()
            if not nome or not cognome:
                messagebox.showwarning("Attenzione", "Inserisci almeno Nome e Cognome.")
                return
            try:
                conn = db.connetti()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO clienti (nome, cognome, azienda, partita_iva, codice_fiscale, indirizzo, numero_civico, cap, localita, provincia, telefono, email)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (nome, cognome, entry_azienda.get(), entry_piva.get(), entry_cf.get(), entry_indirizzo.get(), 
                      entry_civico.get(), entry_cap.get(), entry_localita.get(), entry_prov.get(), entry_tel.get(), entry_email.get()))
                id_cliente = cursor.lastrowid
                
                if entry_fid.get().strip():
                    cursor.execute("INSERT OR REPLACE INTO fidelity_card (codice_carta, id_cliente, punti) VALUES (?, ?, 0)", 
                                   (entry_fid.get().strip(), id_cliente))
                conn.commit()
                conn.close()
                messagebox.showinfo("Successo", "Cliente registrato con successo!")
                win.destroy()
                self.carica_clienti()
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile salvare il cliente:\n{e}")

        btn_salva = ctk.CTkButton(win, text="💾 Salva Cliente", fg_color="#2e7d32", height=45, font=ctk.CTkFont(weight="bold"), command=salva)
        btn_salva.pack(fill="x", padx=15, pady=15)

    def elimina_cliente(self, id_cliente):
        if messagebox.askyesno("Conferma", "Vuoi davvero eliminare questo cliente e la sua carta fidelity?"):
            try:
                db = database._db_manager if hasattr(database, "_db_manager") else database.DatabaseManager()
                db.elimina_cliente(id_cliente)
                self.carica_clienti()
                messagebox.showinfo("Eliminato", "Cliente eliminato con successo.")
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile eliminare il cliente:\n{e}")