import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv

class ModuloClienti(ctk.CTkFrame):
    def __init__(self, parent, db_manager):
        super().__init__(parent, fg_color="transparent")
        self.db = db_manager

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))

        self.btn_nuovo = ctk.CTkButton(self.top_frame, text="+ Nuovo Cliente / Fidelity", fg_color="#2980b9", command=self.apri_finestra_nuovo_cliente)
        self.btn_nuovo.pack(side="left", padx=(0, 10))

        self.btn_elimina = ctk.CTkButton(self.top_frame, text="Elimina Selezionato", fg_color="#c0392b", command=self.elimina_selezionato)
        self.btn_elimina.pack(side="left", padx=(0, 10))

        self.btn_export_csv = ctk.CTkButton(self.top_frame, text="📥 Esporta CSV", fg_color="#27ae60", hover_color="#219653", command=self.esporta_csv_clienti)
        self.btn_export_csv.pack(side="left")

        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        cols = ("ID", "Nome", "Cognome", "Azienda", "Partita IVA", "Codice Fiscale", "Telefono", "Carta Fidelity", "Punti")
        self.tree_clienti = ttk.Treeview(self.table_frame, columns=cols, show="headings")
        for col in cols:
            self.tree_clienti.heading(col, text=col)
            self.tree_clienti.column(col, width=110)
        self.tree_clienti.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.carica_dati_clienti()

    def carica_dati_clienti(self):
        for item in self.tree_clienti.get_children():
            self.tree_clienti.delete(item)
        
        for cli in self.db.ottieni_clienti():
            carta = cli[7] if cli[7] else "Nessuna"
            punti = cli[8] if cli[8] is not None else 0
            self.tree_clienti.insert("", "end", values=(cli[0], cli[1], cli[2], cli[3] or "", cli[4] or "", cli[5] or "", cli[6] or "", carta, punti))

    def apri_finestra_nuovo_cliente(self):
        win = ctk.CTkToplevel(self)
        win.title("Nuovo Cliente - Mercurio Retail")
        win.geometry("420x570")
        win.grab_set()

        ctk.CTkLabel(win, text="Anagrafica Cliente & Fidelity", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=15)

        e_nome = ctk.CTkEntry(win, placeholder_text="Nome *", width=320)
        e_nome.pack(pady=6)
        e_cognome = ctk.CTkEntry(win, placeholder_text="Cognome *", width=320)
        e_cognome.pack(pady=6)
        e_azienda = ctk.CTkEntry(win, placeholder_text="Azienda / Ragione Sociale", width=320)
        e_azienda.pack(pady=6)
        e_piva = ctk.CTkEntry(win, placeholder_text="Partita IVA", width=320)
        e_piva.pack(pady=6)
        e_cf = ctk.CTkEntry(win, placeholder_text="Codice Fiscale", width=320)
        e_cf.pack(pady=6)
        e_tel = ctk.CTkEntry(win, placeholder_text="Telefono", width=320)
        e_tel.pack(pady=6)
        e_email = ctk.CTkEntry(win, placeholder_text="Email", width=320)
        e_email.pack(pady=6)

        codice_auto_fidelity = self.db.genera_prossimo_codice_fidelity()
        
        frame_fid = ctk.CTkFrame(win, fg_color="transparent")
        frame_fid.pack(pady=6)
        
        ctk.CTkLabel(frame_fid, text="Codice Fidelity Auto:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        e_fidelity = ctk.CTkEntry(frame_fid, width=320)
        e_fidelity.insert(0, codice_auto_fidelity)
        e_fidelity.pack()

        def salva():
            nome = e_nome.get().strip()
            cognome = e_cognome.get().strip()
            if not nome or not cognome:
                messagebox.showwarning("Attenzione", "Nome e Cognome sono campi obbligatori.")
                return

            try:
                self.db.inserisci_cliente(
                    nome, cognome,
                    e_azienda.get().strip(),
                    e_piva.get().strip(),
                    e_cf.get().strip(),
                    e_tel.get().strip(),
                    e_email.get().strip(),
                    e_fidelity.get().strip()
                )
                messagebox.showinfo("Successo", f"Cliente registrato con successo!\nCarta Fidelity: {e_fidelity.get().strip()}")
                win.destroy()
                self.carica_dati_clienti()
            except sqlite3.IntegrityError:
                messagebox.showerror("Errore", "Il codice della tessera fidelity inserito è già associato a un altro cliente.")
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile salvare il cliente: {str(e)}")

        ctk.CTkButton(win, text="Salva Cliente", fg_color="#27ae60", command=salva).pack(pady=20)

    def elimina_selezionato(self):
        sel = self.tree_clienti.selection()
        if not sel:
            messagebox.showwarning("Attenzione", "Seleziona un cliente dalla tabella.")
            return
        vals = self.tree_clienti.item(sel[0], "values")
        if messagebox.askyesno("Conferma", f"Vuoi eliminare il cliente '{vals[1]} {vals[2]}' e la relativa tessera fidelity?"):
            self.db.elimina_cliente(int(vals[0]))
            self.carica_dati_clienti()

    def esporta_csv_clienti(self):
        clienti = self.db.ottieni_clienti()
        if not clienti:
            messagebox.showwarning("Attenzione", "Nessun cliente presente nel database da esportare.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("File CSV", "*.csv"), ("Tutti i file", "*.*")],
            title="Salva lista clienti CSV"
        )
        if not filepath:
            return

        try:
            with open(filepath, mode="w", newline="", encoding="utf-8-sig") as file_csv:
                writer = csv.writer(file_csv, delimiter=";")
                writer.writerow(["ID Cliente", "Nome", "Cognome", "Azienda", "Partita IVA", "Codice Fiscale", "Telefono", "Carta Fidelity", "Punti"])
                for cli in clienti:
                    carta = cli[7] if cli[7] else ""
                    punti = cli[8] if cli[8] is not None else 0
                    writer.writerow([cli[0], cli[1], cli[2], cli[3] or "", cli[4] or "", cli[5] or "", cli[6] or "", carta, punti])

            messagebox.showinfo("Esportazione Completata", f"Lista clienti esportata con successo in:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Errore Esportazione", f"Impossibile esportare il file CSV:\n{str(e)}")