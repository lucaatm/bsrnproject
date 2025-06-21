## @file cli.py
#  @brief Benutzeroberfläche (CLI) für den BSRN-Chat.
#  @details Nimmt Eingaben entgegen und steuert die Kommunikation mit Network und Discovery.

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
import threading
import sys
import socket
import base64
import re
from core.image_handler import load_image_as_bytes
import uuid
from core.image_handler import chunk_image_data
import os

## @class CLI
#  @brief Command-Line Interface des BSRN-Chatprogramms.
#  @details Ermöglicht das Senden von Nachrichten, Bildern und Steuerbefehlen durch Benutzereingabe.
class CLI:
    ## @brief Konstruktor.
    #  @param username Benutzername
    #  @param to_net Queue an Network
    #  @param to_disc Queue an Discovery
    #  @param from_net Queue von Network
    #  @param from_disc Queue von Discovery
    #  @param config Konfiguration
    def __init__(self, username, to_net, to_disc, from_net, from_disc, config):
        ## @var self.username
        #  @brief Benutzername
        self.username  = username

        ## @var self.to_net
        #  @brief Queue an Network
        self.to_net    = to_net

        ## @var self.to_disc
        #  @brief Queue an Discovery
        self.to_disc   = to_disc

        ## @var self.from_net
        #  @brief Queue von Network
        self.from_net  = from_net

        ## @var self.from_disc
        #  @brief Queue von Discovery
        self.from_disc = from_disc

        ## @var self.config
        #  @brief Konfigurationsdaten
        self.config    = config

        print(f"[CLI] gestartet für {self.username}")
        print(f"Autoreply: \"{self.config.get('autoreply','')}\"")
        print("Verfügbare Befehle:")
        print("  MSG <name> <text>")
        print("  IMG <name> <pfad>")
        print("  JOIN [<name> <ip> <port>]")
        print("  WHO")
        print("  LEAVE")
        print("  HELP\n")

    ## @brief Startet die CLI-Eingabeschleife
    def run(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except:
            ip = "127.0.0.1"
        port = self.config.get("port", 5000)

        self.to_net.put(["JOIN", self.username, ip, port])

        session = PromptSession(f"[{self.username}]> ")

        threading.Thread(target=self._network_listener, daemon=True).start()

        with patch_stdout():
            while True:
                try:
                    text = session.prompt()
                except (EOFError, KeyboardInterrupt):
                    # CTRL-D / CTRL-C: Chat verlassen
                    self.to_net.put(["LEAVE", self.username])
                    break

                parts = text.strip().split(" ", 3)
                cmd = parts[0].upper() if parts else ""

                if cmd == "MSG" and len(parts) >= 3:
                    # 1. IP/Port vom Discovery holen
                    target, msg_text = parts[1], " ".join(parts[2:])
                    self.to_disc.put(["GET_QUEUE", self.username, target])
                    found = None
                    while True:
                        resp = self.from_disc.get()
                        if isinstance(resp, list) and resp and resp[0] == "FOUND" and resp[1] == target:
                            found = resp
                            break
                        elif isinstance(resp, list) and resp and resp[0] == "NOT_FOUND" and resp[1] == target:
                            found = None
                            break

                    if not found:
                        print(f"❌ Nutzer '{target}' nicht gefunden.")
                        continue

                    ip = found[2]
                    port = found[3]
                    self.to_net.put(["MSG", self.username, target, msg_text, ip, port])

                elif cmd == "IMG" and len(parts) >= 3:
                    target, path = parts[1], " ".join(parts[2:])
                    img_bytes = load_image_as_bytes(path)
                    if img_bytes is None:
                        print(f"❌ Fehler: Bilddatei '{path}' konnte nicht geladen werden.")
                        continue

                    img_b64 = base64.b64encode(img_bytes).decode('ascii')
                    filename = os.path.basename(path)

                    # Hole IP/Port vom Ziel
                    self.to_disc.put(["GET_QUEUE", self.username, target])
                    found = None
                    while True:
                        resp = self.from_disc.get()
                        if isinstance(resp, list) and resp and resp[0] == "FOUND" and resp[1] == target:
                            found = resp
                            break
                        elif isinstance(resp, list) and resp and resp[0] == "NOT_FOUND" and resp[1] == target:
                            found = None
                            break

                    if not found:
                        print(f"❌ Nutzer '{target}' nicht gefunden.")
                        continue

                    ip = found[2]
                    port = found[3]

                    # TCP-Versand: direkter JSON-Block
                    import json
                    payload = json.dumps([self.username, filename, img_b64]).encode()
                    try:
                        with socket.create_connection((ip, port + 100), timeout=5) as sock:
                            print(f"[TCP-Client] Sende an {ip}:{port + 100}")
                            sock.sendall(payload)
                            print(f"[TCP] Bild erfolgreich an {target} gesendet.")
                    except Exception as e:
                        print(f"[TCP Fehler] Bildversand an {target} fehlgeschlagen: {e}")
                    continue

                elif cmd == "JOIN":
                    if len(parts) == 1:
                        self.to_net.put(["JOIN", self.username, ip, port])
                    elif len(parts) == 4:
                        _, h, ipa, pstr = parts
                        self.to_net.put(["JOIN", h, ipa, pstr])
                    else:
                        print("❌ Ungültiger JOIN-Befehl. Syntax: JOIN [<name> <ip> <port>]")

                elif cmd == "WHO":
                    self.to_net.put(["WHO", self.username])

                elif cmd == "LEAVE":
                    self.to_net.put(["LEAVE", self.username])
                    print("Verlasse den Chat…")
                    break

                elif cmd == "HELP":
                    print("Befehle: MSG, IMG, JOIN, WHO, LEAVE, HELP")

                else:
                    if cmd:
                        print("❌ Ungültiger Befehl.")

    ## @brief Gibt eingehende Nachrichten formatiert aus
    def _network_listener(self):
        """
        Läuft im Hintergrund und gibt eingehende Nachrichten sofort aus.
        Behandelt alle Nachrichten, die über Network hereinkommen.
        """
        while True:
            msg = self.from_net.get()  # blockierend warten
            if isinstance(msg, str):
                m = re.match(r'^\[(.+)\] Bild erhalten: (.+)$', msg)
                if m:
                    print(msg)
                    print(f"[Hinweis] Bild gespeichert unter: {m.group(2)}")
                    continue
                if msg.startswith(f"[{self.username}]"):
                    continue
            # Formatierte Ausgabe für KNOWNUSERS
            if isinstance(msg, str) and msg.startswith("KNOWNUSERS "):
                from prettytable import PrettyTable
                users_str = msg[len("KNOWNUSERS "):]
                entries = users_str.split(", ")
                user_data = []
                for entry in entries:
                    parts = entry.strip().split(" ")
                    if len(parts) == 3:
                        name, ip, port = parts
                        if name == self.username:
                            name += " 🟢 Du"
                        user_data.append((name, ip, port))
                user_data.sort(key=lambda x: x[0].lower())
                t = PrettyTable(['Name', 'IP', 'Port'])
                for row in user_data:
                    t.add_row(row)
                print("Bekannte Teilnehmer:")
                print(t)
            elif isinstance(msg, list) and msg and msg[0] == "KNOWNUSERS":
                continue
            else:
                print(msg)