import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import database

class WarehouseModule(ctk.CTkFrame):
    def __init__(self, parent, app_instance=None):
        super().__init__(parent)
        self.app_instance = app_instance
        self.tutti_articoli = []

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Intestazione & Ricerca
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        header_frame.grid_columnconfigure(1, weight=1)

        lbl_titolo = ctk.CTkLabel(header_frame, text="📦 Gestione Magazzino", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_titolo.grid(row=0, column=0, sticky="w")

        # Barra di ricerca rapida
        self.entry_cerca = ctk.CTkEntry(header_frame, placeholder_text="🔍 Cerca per codice EAN o nome articolo...", width=320)
        self.entry_cerca.grid(row=0, column=1, sticky="e", padx=10)
        self.entry_cerca.bind("<KeyRelease>", self.filtra_articoli)

        # 2. Pulsantiera Azioni Rapide
        toolbar_frame = ctk.CTkFrame(self, fg_color="transparent")
        toolbar_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        btn_aggiungi = ctk.CTkButton(toolbar_frame, text="➕ Nuovo Articolo", fg_color="#2e7d32", font=ctk.CTkFont(weight="bold"), command=self.apri_finestra_nuovo_articolo)
        btn_aggiungi.pack(side="left", padx=(0, 10))

        btn_aggiorna = ctk.CTkButton(toolbar_frame, text="🔄 Aggiorna", fg_color="#1565c0", command=self.carica_articoli)
        btn_aggiorna.pack(side="left")

        # 3. Tabella / Lista Articoli Scrollabile
        self.scroll_articoli = ctk.CTkScrollableFrame(self, label_text="Catalogo Articoli & Giacenze")
        self.scroll_articoli.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.scroll_articoli.grid_columnconfigure(0, weight=1)

        self.carica_articoli()

    def carica_articoli(self):
        """Carica gli articoli dal database"""
        try:
            conn = database.get_db_connection()
            self.tutti_articoli = conn.execute("SELECT * FROM articoli").fetchall()
            conn.close()
            self.mostra_lista(self.tutti_articoli)
        except Exception as e:
            messagebox.showerror("Errore Database", f"Impossibile caricare gli articoli:\n{e}")

    def mostra_lista(self, lista_articoli):
        """Disegna le righe degli articoli all'interno del frame scrollabile"""
        for w in self.scroll_articoli.winfo_children():
            w.destroy()

        if not lista_articoli:
            lbl_vuoto = ctk.CTkLabel(self.scroll_articoli, text="Nessun articolo trovato in magazzino.", text_color="gray", font=ctk.CTkFont(size=14))
            lbl_vuoto.pack(pady=30)
            return

        for art in lista_articoli:
            frame_riga = ctk.CTkFrame(self.scroll_articoli, fg_color=("#f0f0f0", "#2b2b2b"), corner_radius=8)
            frame_riga.pack(fill="x", padx=10, pady=5)

            codice = art["codice_ean"] if "codice_ean" in art.keys() else art["codice_interno"]
            desc = art["nome"] if "nome" in art.keys() else art["descrizione"]
            qta = art["quantita"] if "quantita" in art.keys() else art["giacenza"]
            prezzo = art["prezzo_vendita"] if "prezzo_vendita" in art.keys() else art["prezzo_vendita_lordo"]

            # Colore evidenzia giacenza bassa
            colore_qta = "#d32f2f" if qta <= 0 else ("#2e7d32" if qta > 5 else "#f57c00")

            lbl_info = ctk.CTkLabel(
                frame_riga, 
                text=f"🏷️ [{codice}]  {desc}", 
                anchor="w",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            lbl_info.pack(side="left", padx=15, pady=10)

            lbl_dettagli = ctk.CTkLabel(
                frame_riga, 
                text=f"Giacenza: {qta} pz  |  Prezzo: € {prezzo:.2f}",
                font=ctk.CTkFont(size=13),
                text_color=colore_qta
            )
            lbl_dettagli.pack(side="right", padx=15, pady=10)

    def filtra_articoli(self, event=None):
        """Filtra gli articoli in tempo reale in base alla ricerca"""
        query = self.entry_cerca.get().lower().strip()
        if not query:
            self.mostra_lista(self.tutti_articoli)
            return

        filtrati = [
            art for art in self.tutti_articoli 
            if query in str(art.get("codice_ean", art.get("codice_interno", ""))).lower() or 
               query in str(art.get("nome", art.get("descrizione", ""))).lower()
        ]
        self.mostra_lista(filtrati)

    def apri_finestra_nuovo_articolo(self):
        win = ctk.CTkToplevel(self)
        win.title("Nuovo Articolo - Gestione Avanzata")
        win.geometry("450x600")
        win.grab_set()

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(scroll, text="Codice EAN / Articolo *:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        entry_ean = ctk.CTkEntry(scroll, width=390, height=32)
        entry_ean.pack()

        ctk.CTkLabel(scroll, text="Nome / Descrizione *:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        entry_nome = ctk.CTkEntry(scroll, width=390, height=32)
        entry_nome.pack()

        ctk.CTkLabel(scroll, text="Categoria:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        entry_cat = ctk.CTkEntry(scroll, width=390, height=32)
        entry_cat.pack()

        ctk.CTkLabel(scroll, text="Fornitore:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        entry_forn = ctk.CTkEntry(scroll, width=390, height=32)
        entry_forn.pack()

        ctk.CTkLabel(scroll, text="Prezzo di Acquisto (€):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        entry_acq = ctk.CTkEntry(scroll, width=390, height=32)
        entry_acq.insert(0, "0.00")
        entry_acq.pack()

        ctk.CTkLabel(scroll, text="Prezzo di Vendita Lordo (€) *:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        entry_prezzo = ctk.CTkEntry(scroll, width=390, height=32)
        entry_prezzo.pack()

        ctk.CTkLabel(scroll, text="Giacenza Iniziale:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        entry_qta = ctk.CTkEntry(scroll, width=390, height=32)
        entry_qta.insert(0, "0")
        entry_qta.pack()

        def salva():
            ean = entry_ean.get().strip()
            nome = entry_nome.get().strip()
            try:
                prezzo = float(entry_prezzo.get().replace(',', '.'))
                acq = float(entry_acq.get().replace(',', '.'))
                qta = float(entry_qta.get().replace(',', '.'))
            except ValueError:
                messagebox.showerror("Errore", "Valori numerici non validi.")
                return

            if not ean or not nome:
                messagebox.showwarning("Campi Vuoti", "Inserisci codice e nome articolo.")
                return

            try:
                conn = database.get_db_connection()
                conn.execute("""
                    INSERT INTO articoli (codice_ean, nome, categoria, fornitore, prezzo_acquisto, prezzo_vendita, quantita)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (ean, nome, entry_cat.get(), entry_forn.get(), acq, prezzo, qta))
                conn.commit()
                conn.close()
                messagebox.showinfo("Successo", "Articolo salvato correttamente!")
                win.destroy()
                self.carica_articoli()
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile salvare l'articolo:\n{e}")

        btn_salva = ctk.CTkButton(win, text="💾 Salva Articolo", fg_color="#2e7d32", height=45, font=ctk.CTkFont(weight="bold"), command=salva)
        btn_salva.pack(fill="x", padx=15, pady=15)

        def salva():
            ean = entry_ean.get().strip()
            nome = entry_nome.get().strip()
            try:
                prezzo = float(entry_prezzo.get().replace(',', '.'))
                qta = float(entry_qta.get().replace(',', '.'))
            except ValueError:
                messagebox.showerror("Errore", "Prezzo o giacenza non validi.")
                return

            if not ean or not nome:
                messagebox.showwarning("Campi Vuoti", "Inserisci codice e descrizione.")
                return

            try:
                conn = database.get_db_connection()
                conn.execute(
                    "INSERT INTO articoli (codice_ean, nome, quantita, prezzo_vendita) VALUES (?, ?, ?, ?)",
                    (ean, nome, qta, prezzo)
                )
                conn.commit()
                conn.close()
                messagebox.showinfo("Successo", "Articolo aggiunto con successo!")
                win.destroy()
                self.carica_articoli()
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile salvare l'articolo (Codice duplicato?):\n{e}")

        btn_salva = ctk.CTkButton(win, text="Salva Articolo", fg_color="#2e7d32", height=40, font=ctk.CTkFont(weight="bold"), command=salva)
        btn_salva.pack(pady=30, padx=30, fill="x")