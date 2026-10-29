import customtkinter as ctk
from tkinter import ttk, messagebox
import sqlite3
from rt_driver import RegistratoreTelematico

class ModuloPOS(ctk.CTkFrame):
    def __init__(self, parent, db_manager):
        super().__init__(parent, fg_color="transparent")
        self.db = db_manager
        self.rt = RegistratoreTelematico()
        self.cart_items = []
        self.tastierino_buffer = ""

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)

        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.left_frame.grid_rowconfigure(3, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

        self.barcode_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.barcode_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 8))
        self.barcode_frame.grid_columnconfigure(0, weight=1)

        self.entry_barcode = ctk.CTkEntry(self.barcode_frame, placeholder_text="Scansiona EAN o digita codice e premi Invio...", height=38, font=ctk.CTkFont(size=13))
        self.entry_barcode.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.entry_barcode.bind("<Return>", self.cerca_e_aggiungi_da_ean)
        self.entry_barcode.focus()

        self.btn_cerca_art = ctk.CTkButton(self.barcode_frame, text="🔍 Cerca", width=80, height=38, fg_color="#2980b9", command=self.apri_finestra_ricerca_articoli)
        self.btn_cerca_art.grid(row=0, column=1, sticky="e")

        self.display_frame = ctk.CTkFrame(self.left_frame, fg_color="#000000", corner_radius=6, height=85)
        self.display_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=(0, 8))
        self.display_frame.pack_propagate(False)

        self.lbl_articolo_selezionato = ctk.CTkLabel(self.display_frame, text="Pronto alla vendita...", text_color="#2ecc71", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_articolo_selezionato.pack(anchor="w", padx=12, pady=(6, 0))

        self.lbl_totale_grande = ctk.CTkLabel(self.display_frame, text="€ 0,00", text_color="#2ecc71", font=ctk.CTkFont(size=30, weight="bold"))
        self.lbl_totale_grande.pack(anchor="e", padx=12, pady=(0, 6))

        self.table_frame = ctk.CTkFrame(self.left_frame)
        self.table_frame.grid(row=3, column=0, sticky="nsew", padx=0, pady=(0, 8))
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        cols_cart = ("Codice EAN", "Descrizione Articolo", "Q.tà", "Prezzo Unit.", "Totale")
        self.tree_cart = ttk.Treeview(self.table_frame, columns=cols_cart, show="headings")
        self.tree_cart.heading("Codice EAN", text="EAN")
        self.tree_cart.heading("Descrizione Articolo", text="Descrizione Articolo")
        self.tree_cart.heading("Q.tà", text="Q.tà")
        self.tree_cart.heading("Prezzo Unit.", text="Prezzo Unit.")
        self.tree_cart.heading("Totale", text="Totale")
        
        self.tree_cart.column("Codice EAN", width=100, anchor="w")
        self.tree_cart.column("Descrizione Articolo", width=170, anchor="w")
        self.tree_cart.column("Q.tà", width=45, anchor="center")
        self.tree_cart.column("Prezzo Unit.", width=80, anchor="e")
        self.tree_cart.column("Totale", width=80, anchor="e")
        self.tree_cart.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.summary_frame = ctk.CTkFrame(self.left_frame, fg_color="#e0e0e0", height=38, corner_radius=4)
        self.summary_frame.grid(row=4, column=0, sticky="ew")
        self.summary_frame.pack_propagate(False)

        self.lbl_voci_conteggio = ctk.CTkLabel(self.summary_frame, text="0 voci", text_color="#333333", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_voci_conteggio.pack(side="left", padx=15)

        self.lbl_voci_totale = ctk.CTkLabel(self.summary_frame, text="€ 0,00", text_color="#333333", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_voci_totale.pack(side="right", padx=15)

        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        for i in range(5):
            self.right_frame.grid_columnconfigure(i, weight=1, uniform="col")
        for i in range(8):
            self.right_frame.grid_rowconfigure(i, weight=1, uniform="row")

        btn_style = {"font": ctk.CTkFont(size=15, weight="bold"), "corner_radius": 4}

        ctk.CTkButton(self.right_frame, text="€", fg_color="#e8d8f0", text_color="#6c3483", **btn_style, command=lambda: self.premi_tasto("€")).grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="Q.tà", fg_color="#e8d8f0", text_color="#6c3483", **btn_style, command=lambda: self.premi_tasto("Q.tà")).grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="-%", fg_color="#e8d8f0", text_color="#6c3483", **btn_style, command=lambda: self.premi_tasto("-%")).grid(row=0, column=2, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="Elim", fg_color="#e8d8f0", text_color="#6c3483", **btn_style, command=self.rimuovi_articolo).grid(row=0, column=3, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="▼", fg_color="#e0e0e0", text_color="#333333", **btn_style, command=lambda: self.premi_tasto("▼")).grid(row=0, column=4, sticky="nsew", padx=2, pady=2)

        ctk.CTkButton(self.right_frame, text="CL", fg_color="#d4e6f1", text_color="#1b4f72", **btn_style, command=self.pulisci_buffer).grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="X", fg_color="#d4e6f1", text_color="#1b4f72", **btn_style, command=lambda: self.premi_tasto("X")).grid(row=1, column=1, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="Reso", fg_color="#d4e6f1", text_color="#1b4f72", **btn_style, command=lambda: self.premi_tasto("Reso")).grid(row=1, column=2, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="-", fg_color="#e5e7e9", text_color="#5d6d7e", **btn_style).grid(row=1, column=3, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="-", fg_color="#e5e7e9", text_color="#5d6d7e", **btn_style).grid(row=1, column=4, sticky="nsew", padx=2, pady=2)

        ctk.CTkButton(self.right_frame, text="7", fg_color="#eaeded", text_color="#2c3e50", **btn_style, command=lambda: self.aggiungi_cifra("7")).grid(row=2, column=0, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="8", fg_color="#eaeded", text_color="#2c3e50", **btn_style, command=lambda: self.aggiungi_cifra("8")).grid(row=2, column=1, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="9", fg_color="#eaeded", text_color="#2c3e50", **btn_style, command=lambda: self.aggiungi_cifra("9")).grid(row=2, column=2, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="-", fg_color="#e5e7e9", text_color="#5d6d7e", **btn_style).grid(row=2, column=3, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="Cart", fg_color="#fadbd8", text_color="#78281f", **btn_style, command=lambda: self.aggiungi_vendita_libera("Articolo Cartoleria")).grid(row=2, column=4, sticky="nsew", padx=2, pady=2)

        ctk.CTkButton(self.right_frame, text="4", fg_color="#eaeded", text_color="#2c3e50", **btn_style, command=lambda: self.aggiungi_cifra("4")).grid(row=3, column=0, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="5", fg_color="#eaeded", text_color="#2c3e50", **btn_style, command=lambda: self.aggiungi_cifra("5")).grid(row=3, column=1, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="6", fg_color="#eaeded", text_color="#2c3e50", **btn_style, command=lambda: self.aggiungi_cifra("6")).grid(row=3, column=2, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="4", fg_color="#eaedf0", text_color="#196f3d", **btn_style, command=lambda: self.aggiungi_vendita_libera("Reparto 4")).grid(row=3, column=3, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="Banc", fg_color="#fadbd8", text_color="#78281f", **btn_style, command=lambda: self.aggiungi_vendita_libera("Vendita Banco")).grid(row=3, column=4, sticky="nsew", padx=2, pady=2)

        ctk.CTkButton(self.right_frame, text="1", fg_color="#eaeded", text_color="#2c3e50", **btn_style, command=lambda: self.aggiungi_cifra("1")).grid(row=4, column=0, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="2", fg_color="#eaeded", text_color="#2c3e50", **btn_style, command=lambda: self.aggiungi_cifra("2")).grid(row=4, column=1, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="3", fg_color="#eaeded", text_color="#2c3e50", **btn_style, command=lambda: self.aggiungi_cifra("3")).grid(row=4, column=2, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="10", fg_color="#eaedf0", text_color="#196f3d", **btn_style, command=lambda: self.aggiungi_vendita_libera("Reparto 10")).grid(row=4, column=3, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="Non", fg_color="#fadbd8", text_color="#78281f", **btn_style, command=lambda: self.aggiungi_vendita_libera("Articolo Non Censito")).grid(row=4, column=4, sticky="nsew", padx=2, pady=2)

        ctk.CTkButton(self.right_frame, text="0", fg_color="#eaeded", text_color="#2c3e50", **btn_style, command=lambda: self.aggiungi_cifra("0")).grid(row=5, column=0, columnspan=2, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text=",", fg_color="#eaeded", text_color="#2c3e50", **btn_style, command=lambda: self.aggiungi_cifra(",")).grid(row=5, column=2, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="22", fg_color="#eaedf0", text_color="#196f3d", **btn_style, command=lambda: self.aggiungi_vendita_libera("Reparto 22% IVA")).grid(row=5, column=3, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="Cont", fg_color="#fadbd8", text_color="#78281f", **btn_style, command=lambda: self.completa_vendita("CONTANTI")).grid(row=5, column=4, sticky="nsew", padx=2, pady=2)

        ctk.CTkButton(self.right_frame, text="Nuov", fg_color="#d4e6f1", text_color="#1b4f72", **btn_style, command=self.nuovo_scontrino).grid(row=6, column=0, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="Stam", fg_color="#d4e6f1", text_color="#1b4f72", **btn_style, command=lambda: self.completa_vendita("CONTANTI")).grid(row=6, column=1, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="Ann!", fg_color="#f9e79f", text_color="#7d6608", **btn_style, command=self.nuovo_scontrino).grid(row=6, column=2, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="Cod.", fg_color="#d4e6f1", text_color="#1b4f72", **btn_style, command=lambda: self.premi_tasto("Cod.")).grid(row=6, column=3, sticky="nsew", padx=2, pady=2)
        ctk.CTkButton(self.right_frame, text="Subt", fg_color="#d4e6f1", text_color="#1b4f72", **btn_style, command=lambda: self.premi_tasto("Subt")).grid(row=6, column=4, sticky="nsew", padx=2, pady=2)

    def cerca_e_aggiungi_da_ean(self, event):
        ean = self.entry_barcode.get().strip()
        self.entry_barcode.delete(0, "end")
        if not ean:
            return

        with self.db.connetti() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_articolo, codice_ean, nome, prezzo_vendita, quantita FROM articoli WHERE codice_ean = ?", (ean,))
            res = cursor.fetchone()
            if res:
                self.aggiungi_al_carrello(res[0], res[1], res[2], res[3])
            else:
                messagebox.showwarning("Articolo non trovato", f"Nessun prodotto a magazzino corrisponde al codice EAN: {ean}")

    def apri_finestra_ricerca_articoli(self):
        win = ctk.CTkToplevel(self)
        win.title("Ricerca Articoli Magazzino - Mercurio Retail")
        win.geometry("600x400")
        win.grab_set()

        ctk.CTkLabel(win, text="Seleziona un articolo da inserire in cassa", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=10)

        cols = ("ID", "EAN", "Nome", "Giacenza", "Prezzo Vendita")
        tree = ttk.Treeview(win, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=110)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for art in self.db.ottieni_articoli():
            px_ven = f"€ {art[5]:.2f}" if art[5] is not None else "€ 0.00"
            tree.insert("", "end", values=(art[0], art[1], art[2], art[3], px_ven))

        def seleziona_e_chiudi():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Attenzione", "Seleziona un articolo.")
                return
            vals = tree.item(sel[0], "values")
            id_art = int(vals[0])
            ean = vals[1]
            nome = vals[2]
            prezzo = float(vals[4].replace("€", "").strip().replace(",", "."))
            
            self.aggiungi_al_carrello(id_art, ean, nome, prezzo)
            win.destroy()

        btn_sel = ctk.CTkButton(win, text="Aggiungi al Carrello", fg_color="#27ae60", command=seleziona_e_chiudi)
        btn_sel.pack(pady=10)

    def aggiungi_cifra(self, cifra):
        self.tastierino_buffer += cifra
        self.lbl_articolo_selezionato.configure(text=f"Digitazione: {self.tastierino_buffer}")

    def pulisci_buffer(self):
        self.tastierino_buffer = ""
        self.lbl_articolo_selezionato.configure(text="Pronto alla vendita...")

    def premi_tasto(self, funzione):
        messagebox.showinfo("Funzione POS", f"Comando '{funzione}' premuto.")

    def aggiungi_vendita_libera(self, nome_prodotto):
        prezzo = 10.00
        if self.tastierino_buffer:
            try:
                prezzo = float(self.tastierino_buffer.replace(",", "."))
            except ValueError:
                pass
        
        self.aggiungi_al_carrello(0, "LIBERO", nome_prodotto, prezzo)

    def aggiungi_al_carrello(self, id_art, ean, nome, prezzo):
        if id_art > 0:
            for item in self.cart_items:
                if item["id"] == id_art:
                    item["qta"] += 1
                    item["totale"] = item["qta"] * item["prezzo"]
                    self.aggiorna_carrello()
                    return

        self.cart_items.append({"id": id_art, "ean": ean, "nome": nome, "prezzo": prezzo, "qta": 1, "totale": prezzo})
        self.aggiorna_carrello()

    def rimuovi_articolo(self):
        sel = self.tree_cart.selection()
        if not sel:
            messagebox.showwarning("Attenzione", "Seleziona una voce nel carrello da eliminare.")
            return
        idx = self.tree_cart.index(sel[0])
        del self.cart_items[idx]
        self.aggiorna_carrello()

    def nuovo_scontrino(self):
        self.cart_items = []
        self.tastierino_buffer = ""
        self.aggiorna_carrello()

    def aggiorna_carrello(self):
        for item in self.tree_cart.get_children():
            self.tree_cart.delete(item)
        
        totale_generale = 0.0
        for item in self.cart_items:
            self.tree_cart.insert("", "end", values=(item["ean"], f"{item['nome']} (x{item['qta']})", item["qta"], f"€ {item['prezzo']:.2f}".replace(".", ","), f"€ {item['totale']:.2f}".replace(".", ",")))
            totale_generale += item["totale"]
        
        num_voci = len(self.cart_items)
        self.lbl_voci_conteggio.configure(text=f"{num_voci} voci" if num_voci != 1 else "1 voce")
        self.lbl_voci_totale.configure(text=f"€ {totale_generale:.2f}".replace(".", ","))
        
        if self.cart_items:
            ultimo = self.cart_items[-1]
            self.lbl_articolo_selezionato.configure(text=ultimo["nome"])
        else:
            self.lbl_articolo_selezionato.configure(text="Pronto alla vendita...")
            
        self.lbl_totale_grande.configure(text=f"€ {totale_generale:.2f}".replace(".", ","))
        self.entry_barcode.focus()

    def completa_vendita(self, metodo):
        if not self.cart_items:
            messagebox.showwarning("Attenzione", "Impossibile emettere lo scontrino: il carrello è vuoto.")
            return
        
        totale = sum(i["totale"] for i in self.cart_items)
        ok, msg = self.rt.emetti_scontrino(self.cart_items, totale)
        
        if ok:
            for item in self.cart_items:
                if item["id"] > 0:
                    self.db.scarica_giacenza(item["id"], item["qta"])
            
            messagebox.showinfo("Scontrino Fiscale", f"Vendita {metodo} completata!\n{msg}")
            self.nuovo_scontrino()
        else:
            messagebox.showerror("Errore Registratore Telematico", f"Errore comunicazione RT:\n{msg}")