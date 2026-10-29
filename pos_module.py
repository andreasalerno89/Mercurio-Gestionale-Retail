import winsound
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import database
from datetime import datetime

class POSModule(ctk.CTkFrame):
    def __init__(self, parent, app_instance=None):
        super().__init__(parent)
        self.app_instance = app_instance

        # Stato della cassa e carrello
        self.carrello = []
        self.quantita_moltiplicatore = 1.0
        self.cliente_selezionato = None
        self.importo_tastierino = ""

        # Layout principale POS: 2 colonne (Sinistra: Carrello/LCD, Destra: Tastierino/Reparti/Azioni)
        self.grid_columnconfigure(0, weight=6)
        self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(0, weight=1)

        self._crea_colonna_sinistra()
        self._crea_colonna_destra()
        self.carica_reparti()

    def play_beep(self):
        """Emette un suono acustico di conferma scansione/battuta."""
        try:
            winsound.Beep(1800, 80)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # COLONNA SINISTRA: Display LCD + Tabella Carrello + Input Barcode
    # -------------------------------------------------------------------------
    def _crea_colonna_sinistra(self):
        frame_sx = ctk.CTkFrame(self, fg_color="transparent")
        frame_sx.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        frame_sx.grid_columnconfigure(0, weight=1)
        frame_sx.grid_rowconfigure(2, weight=1)

        # 1. Display LCD
        self.frame_lcd = ctk.CTkFrame(frame_sx, fg_color="#0d2818", corner_radius=10, height=110)
        self.frame_lcd.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.frame_lcd.grid_columnconfigure(0, weight=1)

        self.lbl_lcd_articolo = ctk.CTkLabel(
            self.frame_lcd, text="PRONTO ALLA VENDITA",
            font=ctk.CTkFont(family="Consolas", size=16, weight="bold"),
            text_color="#2ec4b6", anchor="w"
        )
        self.lbl_lcd_articolo.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 0))

        self.lbl_lcd_totale = ctk.CTkLabel(
            self.frame_lcd, text="€ 0.00",
            font=ctk.CTkFont(family="Consolas", size=38, weight="bold"),
            text_color="#80ed99", anchor="e"
        )
        self.lbl_lcd_totale.grid(row=1, column=0, sticky="e", padx=15, pady=(0, 10))

        # 2. Input Barcode e Ricerca Veloce
        frame_input = ctk.CTkFrame(frame_sx)
        frame_input.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        frame_input.grid_columnconfigure(1, weight=1)

        lbl_bc = ctk.CTkLabel(frame_input, text="Barcode / Codice:", font=ctk.CTkFont(weight="bold"))
        lbl_bc.grid(row=0, column=0, padx=10, pady=8)

        self.entry_barcode = ctk.CTkEntry(frame_input, placeholder_text="Scansiona EAN o digita codice...")
        self.entry_barcode.grid(row=0, column=1, sticky="ew", padx=5, pady=8)
        self.entry_barcode.bind("<Return>", self.cerca_e_aggiungi_articolo)

        btn_add = ctk.CTkButton(frame_input, text="Aggiungi", width=80, command=self.cerca_e_aggiungi_articolo)
        btn_add.grid(row=0, column=2, padx=10, pady=8)

        # 3. Tabella / Lista Carrello
        self.scroll_carrello = ctk.CTkScrollableFrame(frame_sx, label_text="Articoli in Scontrino")
        self.scroll_carrello.grid(row=2, column=0, sticky="nsew")
        self.scroll_carrello.grid_columnconfigure(1, weight=1)

    # -------------------------------------------------------------------------
    # COLONNA DESTRA: Tastierino Numerico + Reparti + Pagamento
    # -------------------------------------------------------------------------
    def _crea_colonna_destra(self):
        frame_dx = ctk.CTkFrame(self)
        frame_dx.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        frame_dx.grid_columnconfigure((0, 1, 2), weight=1)

        # --- Display Tastierino Digitale ---
        self.lbl_disp_tastierino = ctk.CTkLabel(
            frame_dx, text="Importo: € 0.00",
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=("#e0e0e0", "#2b2b2b"), corner_radius=6, height=40
        )
        self.lbl_disp_tastierino.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(10, 5))

        # --- Tastierino Numerico (0-9, ., 00, C) ---
        tasti = [
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2),
            ('C', 4, 0), ('0', 4, 1), ('.', 4, 2)
        ]

        for (testo, riga, col) in tasti:
            cmd = lambda t=testo: self._pressione_tastierino(t)
            colore = "#a83232" if testo == 'C' else None
            btn = ctk.CTkButton(frame_dx, text=testo, font=ctk.CTkFont(size=16, weight="bold"),
                                fg_color=colore, height=45, command=cmd)
            btn.grid(row=riga, column=col, sticky="nsew", padx=3, pady=3)

        # --- Sezione Reparti Rapidi ---
        lbl_rep = ctk.CTkLabel(frame_dx, text="Seleziona Reparto per Vendita Libera:", font=ctk.CTkFont(size=11, weight="bold"))
        lbl_rep.grid(row=5, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 2))

        self.frame_reparti = ctk.CTkFrame(frame_dx, fg_color="transparent")
        self.frame_reparti.grid(row=6, column=0, columnspan=3, sticky="ew", padx=5)
        self.frame_reparti.grid_columnconfigure((0, 1), weight=1)

        # --- Pulsanti Pagamento Veloce ---
        btn_contanti = ctk.CTkButton(frame_dx, text="💵 CONTANTI (Calcolo Resto)", fg_color="#2e7d32", height=50,
                                     font=ctk.CTkFont(size=15, weight="bold"), command=lambda: self.concludi_vendita("CONTANTI"))
        btn_contanti.grid(row=7, column=0, columnspan=3, sticky="ew", padx=10, pady=(15, 5))

        btn_pos = ctk.CTkButton(frame_dx, text="💳 POS / CARTA", fg_color="#1565c0", height=50,
                                font=ctk.CTkFont(size=15, weight="bold"), command=lambda: self.concludi_vendita("POS"))
        btn_pos.grid(row=8, column=0, columnspan=3, sticky="ew", padx=10, pady=5)

        btn_annulla = ctk.CTkButton(frame_dx, text="❌ Annulla Scontrino", fg_color="#c62828", height=35,
                                    command=self.svuota_carrello)
        btn_annulla.grid(row=9, column=0, columnspan=3, sticky="ew", padx=10, pady=(5, 10))

    # -------------------------------------------------------------------------
    # LOGICA TASTIERINO NUMERICO E REPARTI
    # -------------------------------------------------------------------------
    def _pressione_tastierino(self, valore):
        """Gestisce l'immissione di numeri o del tasto Clear sul tastierino."""
        if valore == 'C':
            self.importo_tastierino = ""
        elif valore == '.':
            if '.' not in self.importo_tastierino:
                self.importo_tastierino += '.' if self.importo_tastierino else '0.'
        else:
            self.importo_tastierino += valore

        txt = f"Importo: € {self.importo_tastierino}" if self.importo_tastierino else "Importo: € 0.00"
        self.lbl_disp_tastierino.configure(text=txt)

    def carica_reparti(self):
        """Carica dinamicamente i reparti dal DB e crea i pulsanti di vendita libera."""
        for w in self.frame_reparti.winfo_children():
            w.destroy()

        conn = database.get_db_connection()
        reparti = conn.execute("SELECT * FROM reparti").fetchall()
        conn.close()

        r, c = 0, 0
        for rep in reparti:
            r_id = rep["id"]
            r_nome = rep["nome_reparto"]
            btn = ctk.CTkButton(
                self.frame_reparti, text=r_nome, fg_color="#37474f", height=35,
                command=lambda id_rep=r_id, nome_rep=r_nome: self.aggiungi_vendita_libera(id_rep, nome_rep)
            )
            btn.grid(row=r, column=c, sticky="ew", padx=3, pady=3)
            c += 1
            if c > 1:
                c = 0
                r += 1

    def aggiungi_vendita_libera(self, reparto_id, nome_reparto):
        """Aggiunge una voce libera a carrello basata sull'importo digitato sul tastierino."""
        if not self.importo_tastierino:
            messagebox.showwarning("Tastierino Vuoto", "Digita un importo sul tastierino numerico prima di selezionare il reparto.")
            return

        try:
            prezzo = float(self.importo_tastierino)
            if prezzo <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Errore Importo", "Inserisci un importo valido per la vendita libera.")
            return

        item = {
            "articolo_id": None,
            "codice": f"REP-{reparto_id}",
            "descrizione": f"Vendita Libera ({nome_reparto})",
            "quantita": self.quantita_moltiplicatore,
            "prezzo_unitario": prezzo,
            "aliquota_iva": 22.0,
            "totale": prezzo * self.quantita_moltiplicatore
        }

        self.carrello.append(item)
        self.play_beep()
        self.quantita_moltiplicatore = 1.0
        self.importo_tastierino = ""
        self.lbl_disp_tastierino.configure(text="Importo: € 0.00")
        self.aggiorna_interfaccia_carrello()

    # -------------------------------------------------------------------------
    # GESTIONE CARRELLO E SCANSIONE
    # -------------------------------------------------------------------------
    def cerca_e_aggiungi_articolo(self, event=None):
        codice = self.entry_barcode.get().strip()
        if not codice:
            return

        conn = database.get_db_connection()
        art = conn.execute(
            "SELECT * FROM articoli WHERE barcode_ean = ? OR codice_interno = ?",
            (codice, codice)
        ).fetchone()
        conn.close()

        if art:
            item = {
                "articolo_id": art["id"],
                "codice": art["codice_interno"],
                "descrizione": art["descrizione"],
                "quantita": self.quantita_moltiplicatore,
                "prezzo_unitario": art["prezzo_vendita_lordo"],
                "aliquota_iva": 22.0,
                "totale": art["prezzo_vendita_lordo"] * self.quantita_moltiplicatore
            }
            self.carrello.append(item)
            self.play_beep()
            self.quantita_moltiplicatore = 1.0
            self.entry_barcode.delete(0, 'end')
            self.aggiorna_interfaccia_carrello()
        else:
            messagebox.showwarning("Non Trovato", f"Nessun articolo trovato con codice: {codice}")

    def aggiorna_interfaccia_carrello(self):
        for w in self.scroll_carrello.winfo_children():
            w.destroy()

        totale_generale = 0.0

        for idx, item in enumerate(self.carrello):
            totale_generale += item["totale"]
            
            frame_riga = ctk.CTkFrame(self.scroll_carrello)
            frame_riga.pack(fill="x", padx=5, pady=2)

            lbl_desc = ctk.CTkLabel(frame_riga, text=f"{item['descrizione']}", anchor="w", font=ctk.CTkFont(weight="bold"))
            lbl_desc.pack(side="left", padx=10, expand=True, fill="x")

            lbl_dett = ctk.CTkLabel(frame_riga, text=f"{item['quantita']} x € {item['prezzo_unitario']:.2f} = € {item['totale']:.2f}")
            lbl_dett.pack(side="left", padx=10)

            btn_del = ctk.CTkButton(frame_riga, text="X", width=30, fg_color="#c62828", command=lambda i=idx: self.rimuovi_riga(i))
            btn_del.pack(side="right", padx=5)

        self.lbl_lcd_totale.configure(text=f"€ {totale_generale:.2f}")
        if self.carrello:
            self.lbl_lcd_articolo.configure(text=f"ULTIMO: {self.carrello[-1]['descrizione'][:25]}")
        else:
            self.lbl_lcd_articolo.configure(text="PRONTO ALLA VENDITA")

    def rimuovi_riga(self, indice):
        if 0 <= indice < len(self.carrello):
            self.carrello.pop(indice)
            self.aggiorna_interfaccia_carrello()

    def svuota_carrello(self):
        self.carrello.clear()
        self.importo_tastierino = ""
        self.lbl_disp_tastierino.configure(text="Importo: € 0.00")
        self.aggiorna_interfaccia_carrello()

    # -------------------------------------------------------------------------
    # CHIUSURA E REGISTRAZIONE VENDITA CON CALCOLO RESTO CONTANTI
    # -------------------------------------------------------------------------
    def concludi_vendita(self, tipo_pagamento):
        if not self.carrello:
            messagebox.showwarning("Carrello Vuoto", "Inserisci almeno un articolo o una vendita libera prima di incassare.")
            return

        totale = sum(item["totale"] for item in self.carrello)
        importo_pagato = totale
        resto = 0.0

        # Se il pagamento è in contanti, chiediamo quanto denaro ha consegnato il cliente
        if tipo_pagamento == "CONTANTI":
            dialog = ctk.CTkInputDialog(
                text=f"Totale scontrino: € {totale:.2f}\n\nInserisci contante ricevuto dal cliente:", 
                title="Incasso Contanti - Calcolo Resto"
            )
            valore_inserito = dialog.get_input()
            
            if valore_inserito is None:
                return  # Operazione annullata dall'operatore
                
            try:
                importo_pagato = float(valore_inserito.replace(',', '.'))
            except ValueError:
                messagebox.showerror("Errore", "L'importo inserito non è valido.")
                return

            if importo_pagato < totale:
                messagebox.showerror(
                    "Importo Insufficiente", 
                    f"Il contante inserito (€ {importo_pagato:.2f}) è inferiore al totale dello scontrino (€ {totale:.2f})!"
                )
                return

            resto = importo_pagato - totale

        conn = database.get_db_connection()
        cur = conn.cursor()

        # Genera Numero Scontrino Univoco
        now = datetime.now()
        num_scontrino = f"SC-{now.strftime('%Y%m%d%H%M%S')}"

        # Inserisce Testata Movimento con importo pagato e resto registrati
        cur.execute("""
        INSERT INTO movimenti_banco (numero_scontrino, data_ora, totale_netto, totale_iva, totale_lordo, tipo_pagamento, importo_pagato, resto)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (num_scontrino, now.strftime('%Y-%m-%d %H:%M:%S'), totale * 0.78, totale * 0.22, totale, tipo_pagamento, importo_pagato, resto))

        movimento_id = cur.lastrowid

        # Inserisce Dettagli e Scarico Magazzino
        for item in self.carrello:
            cur.execute("""
            INSERT INTO dettaglio_scontrini (movimento_id, articolo_id, descrizione_articolo, quantita, prezzo_unitario, aliquota_iva, totale_riga)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (movimento_id, item["articolo_id"], item["descrizione"], item["quantita"], item["prezzo_unitario"], item["aliquota_iva"], item["totale"]))

            if item["articolo_id"]:
                cur.execute("UPDATE articoli SET giacenza = giacenza - ? WHERE id = ?", (item["quantita"], item["articolo_id"]))

        conn.commit()
        conn.close()

        self.play_beep()

        # Messaggio di riepilogo con evidenza del Resto per l'operatore
        messaggio = f"Scontrino {num_scontrino} emesso con successo!\n\n"
        messaggio += f"• Totale Scontrino: € {totale:.2f}\n"
        if tipo_pagamento == "CONTANTI":
            messaggio += f"• Contante Ricevuto: € {importo_pagato:.2f}\n"
            messaggio += f"👉 RESTO DA DARE: € {resto:.2f}\n\n"
        messaggio += f"Metodo: {tipo_pagamento}"

        messagebox.showinfo("Incasso Completato", messaggio)
        self.svuota_carrello()