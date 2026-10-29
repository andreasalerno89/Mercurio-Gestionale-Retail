import socket
import serial
import json
import os

class RegistratoreTelematico:
    def __init__(self):
        self.carica_configurazione()

    def carica_configurazione(self):
        self.modalita = "IP"
        self.ip = "192.168.1.100"
        self.porta_ip = 9100
        self.porta_com = "COM1"
        self.baudrate = 9600
        self.flusso = "XON/XOFF"

        for file_cfg in ["config_mercurio.json", "config.json"]:
            if os.path.exists(file_cfg):
                try:
                    with open(file_cfg, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        mod_str = cfg.get("modalita", "IP")
                        if "IP" in mod_str:
                            self.modalita = "IP"
                        elif "USB" in mod_str:
                            self.modalita = "USB"
                        else:
                            self.modalita = "SERIALE"

                        self.ip = cfg.get("ip", "192.168.1.100")
                        self.porta_ip = int(cfg.get("porta_ip", 9100))
                        self.porta_com = cfg.get("com", cfg.get("porta_seriale", "COM1"))
                        self.baudrate = int(cfg.get("baudrate", 9600))
                        self.flusso = cfg.get("flusso", "XON/XOFF")
                        break
                except Exception:
                    pass

    def emetti_scontrino(self, articoli_carrello, totale_finale):
        self.carica_configurazione()
        
        comando = "\x1b@\n"
        comando += "OPEN_RECEIPT\n"
        for item in articoli_carrello:
            nome = item.get("nome", item.get("descrizione", "Articolo"))
            qta = item.get("quantita", 1.0)
            prezzo = item.get("prezzo_vendita", item.get("prezzo_unitario", 0.0))
            comando += f"SALE,{nome},{qta},{prezzo:.2f}\n"
        comando += f"PAYMENT_CASH,{totale_finale:.2f}\n"
        comando += "CLOSE_RECEIPT\n"

        if self.modalita == "IP":
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3.0)
                s.connect((self.ip, self.porta_ip))
                s.sendall(comando.encode('latin-1'))
                s.close()
                return True, "Scontrino fiscale emesso con successo via IP."
            except Exception as e:
                return False, f"Errore connessione IP RT: {str(e)}"
        else:
            try:
                ser = serial.Serial(
                    port=self.porta_com,
                    baudrate=self.baudrate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    xonxoff=(self.flusso == "XON/XOFF"),
                    rtscts=("Hardware" in self.flusso),
                    timeout=3
                )
                ser.write(comando.encode('latin-1'))
                ser.close()
                return True, f"Scontrino fiscale emesso con successo via {self.modalita} ({self.porta_com}, {self.baudrate} baud)."
            except Exception as e:
                return False, f"Errore porta {self.modalita} RT: {str(e)}"