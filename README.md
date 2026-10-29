# Mercurio Gestionale Retail 🚀
**Un sistema ERP e POS open-source moderno, leggero e intuitivo per la gestione del punto vendita.**

![Versione](https://img.shields.io/badge/versione-0.1.0--alpha-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-yellow.svg)
![Licenza](https://img.shields.io/badge/licenza-GPL%20v3-green.svg)

---

## 📋 Descrizione del Progetto
**Mercurio Gestionale Retail** è un software gestionale (ERP/POS) progettato specificamente per le attività commerciali al dettaglio. Sviluppato in Python con un'interfaccia moderna basata su **CustomTkinter**, offre una soluzione nativa per Windows stabile, veloce e totalmente indipendente da costosi servizi cloud di terze parti.

I dati aziendali vengono salvati in sicurezza all'interno della cartella `%LOCALAPPDATA%\MercurioRetail`, garantendo la massima compatibilità con i permessi di scrittura di Windows (anche in ambienti multi-utente o di esecuzione da `Programmi`).

---

## 🛠️ Moduli Principali
* **Cassa / POS**: Interfaccia di vendita rapida per la scansione di codici EAN, gestione carrello, calcolo del resto e applicazione di sconti.
* **Gestione Magazzino**: Monitoraggio delle giacenze, inserimento articoli, controllo dei prezzi d'acquisto e di vendita e scarico automatico delle scorte.
* **Clienti & Fidelity**: Anagrafica clienti completa, gestione P.IVA/Codice Fiscale e programmi fedeltà con raccolta punti tramite codici carta dedicati (`FID-XXXXXX`).
* **Impostazioni & RT**: Configurazione dei parametri di sistema e simulazione dell'interfacciamento con i registratori telematici.

---

## ⚙️ Stack Tecnologico
* **Linguaggio**: Python 3.10+
* **Interfaccia Grafica**: CustomTkinter
* **Database**: SQLite3
* **Gestione Immagini**: Pillow (PIL)
* **Packaging & Distribuzione**: PyInstaller & Inno Setup

---

## 📦 Installazione e Compilazione

### 1. Requisiti di Sistema
Assicurati di avere Python 3.10 o superiore installato sul tuo sistema.

### 2. Installazione delle dipendenze
Clona il repository e installa i pacchetti necessari tramite pip:
```bash
pip install -r requirements.txt
3. Avvio in modalità sviluppo
Bash
python app.py
4. Generazione dell'Eseguibile e dell'Installer
Compilazione tramite script batch:
Esegui il file build_exe.bat per generare la cartella di distribuzione tramite PyInstaller con l'icona personalizzata incorporata.

Creazione del pacchetto di setup (.exe):
Apri il file setup_script.iss con Inno Setup Compiler e compialo per generare l'installer ufficiale nella cartella Output/.

🤝 Contribuire
I contributi, le segnalazioni di problemi (issues) e le richieste di nuove funzionalità sono ben accetti. Trattandosi di un software open-source, sentiti libero di aprire una Pull Request.

📄 Licenza
Questo progetto è rilasciato sotto i termini della GNU General Public License v3.0. Vedi il file LICENSE per maggiori dettagli.

Autore: Andrea Salerno