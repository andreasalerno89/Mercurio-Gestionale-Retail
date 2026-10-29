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

        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    cfg = json.load(f)
                    mod_str = cfg.get("modalita", "IP")
                    self.modalita = "IP" if "IP" in mod_str else "SERIALE"
                    self.ip = cfg.get("ip", "192.168.1.100")
                    self.porta_com = cfg.get("com", "COM1")
            except Exception:
                pass

    def emetti_scontrino(self, articoli_carrello, totale_finale):
        self.carica_configurazione()
        
        comando = "\x1b@\n"
        comando += "OPEN_RECEIPT\n"
        for item in articoli_carrello:
            comando += f"SALE,{item['nome']},{item['qta']},{item['prezzo']:.2f}\n"
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
                    baudrate=9600,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    xonxoff=True,  # Flusso XON/XOFF
                    rtscts=False,
                    timeout=3
                )
                ser.write(comando.encode('latin-1'))
                ser.close()
                return True, "Scontrino fiscale emesso con successo via Seriale (XON/XOFF)."
            except Exception as e:
                return False, f"Errore porta Seriale RT: {str(e)}"