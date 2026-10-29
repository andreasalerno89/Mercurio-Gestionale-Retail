import customtkinter as ctk
from tkinter import ttk, messagebox
import sqlite3

class ModuloMagazzino(ctk.CTkFrame):
    def __init__(self, parent, db_manager):
        super().__init__(parent, fg_color="transparent")
        self.db = db_manager

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))

        self.btn_nuovo = ctk.CTkButton(self.top_frame, text="+ Nuovo Articolo", fg_color="#2980b9", command=self.apri_finestra_nuovo)
        self.btn_nuovo.pack(side="left", padx=(0, 10))

        self.btn_elimina = ctk.CTkButton(self.top_frame, text="Elimina Selezionato", fg_color="#c0392b", command=self.elimina_selezionato)
        self.btn_elimina.pack(side="left")

        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        cols = ("ID", "Codice EAN", "Nome Articolo", "Giacenza", "Prezzo Acquisto", "Prezzo Vendita")
        self.tree_art = ttk.Treeview(self.table_frame, columns=cols, show="headings")
        for col in cols:
            self.tree_art.heading(col, text=col)
            self.tree_art.column(col, width=130)
        self.tree_art.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.carica_dati()

    def carica_dati(self):
        for item in self.tree_art.get_children():
            self.tree_art.delete(item)
        for art in self.db.ottieni_articoli():
            px_acq = f"€ {art[4]:.2f}" if art[4] is not None else "€ 0.00"
            px_ven = f"€ {art[5]:.2f}" if art[5] is not None else "€ 0.00"
            self.tree_art.insert("", "end", values=(art[0], art[1], art[2], art[3], px_acq, px_ven))

    def apri_finestra_nuovo(self):
        win = ctk.CTkToplevel(self)
        win.title("Nuovo Articolo")
        win.geometry("380x420")
        win.grab_set()

        ctk.CTkLabel(win, text="Inserisci Articolo a Magazzino", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=15)

        e_ean = ctk.CTkEntry(win, placeholder_text="Codice EAN", width=300)
        e_ean.pack(pady=8)
        e_nome = ctk.CTkEntry(win, placeholder_text="Nome Articolo", width=300)
        e_nome.pack(pady=8)
        e_qta = ctk.CTkEntry(win, placeholder_text="Giacenza Iniziale", width=300)
        e_qta.pack(pady=8)
        e_acq = ctk.CTkEntry(win, placeholder_text="Prezzo Acquisto (€)", width=300)
        e_acq.pack(pady=8)
        e_ven = ctk.CTkEntry(win, placeholder_text="Prezzo Vendita (€)", width=300)
        e_ven.pack(pady=8)

        def salva():
            try:
                ean = e_ean.get().strip()
                nome = e_nome.get().strip()
                qta = int(e_qta.get().strip() or 0)
                px_acq = float(e_acq.get().strip().replace(",", ".") or 0.0)
                px_ven = float(e_ven.get().strip().replace(",", ".") or 0.0)
                if not ean or not nome: raise ValueError()
                
                self.db.inserisci_articolo(ean, nome, qta, px_acq, px_ven)
                messagebox.showinfo("Successo", "Articolo salvato correttamente!")
                win.destroy()
                self.carica_dati()
            except Exception:
                messagebox.showerror("Errore", "Verifica i campi inseriti o EAN già esistente.")

        ctk.CTkButton(win, text="Salva", fg_color="#27ae60", command=salva).pack(pady=20)

    def elimina_selezionato(self):
        sel = self.tree_art.selection()
        if not sel:
            messagebox.showwarning("Attenzione", "Seleziona un articolo da eliminare.")
            return
        vals = self.tree_art.item(sel[0], "values")
        if messagebox.askyesno("Conferma", f"Vuoi eliminare l'articolo '{vals[2]}'?"):
            self.db.elimina_articolo(int(vals[0]))
            self.carica_dati()