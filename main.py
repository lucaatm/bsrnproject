## @file main.py
# @brief Startskript für den BSRN Chat mit GUI-/CLI-Auswahl.
# @details Lädt oder initialisiert die Konfiguration, fragt den Benutzernamen ab
#          und startet wahlweise zwei GUI-Clients parallel oder den CLI-Modus.

from config.config_loader import load_config, save_config
import cli.cli_chat as cli_chat
import sys
import os, toml
from PyQt5.QtWidgets import QApplication
from gui.chat_window import ChatWindow
from multiprocessing import Process

CONFIG_PATH = "resources/config.toml"

## @brief Erstellt eine Standard-Konfigurationsdatei, falls nicht vorhanden.
#  @details Legt `config.toml` mit Default-Werten an und fragt den Handle ab,
#           falls dieser leer ist oder fehlt.
def initialize_user():
    if not os.path.exists(CONFIG_PATH):
        print("⚠️ config.toml wurde nicht gefunden. Wird neu erstellt.")
        default_config = {
            "user": {"handle": "", "port": [5001]},
            "network": {"whoisport": 5001},
            "settings": {"autoreply": "Bin nicht da", "imagepath": "./received_images"}
        }
        with open(CONFIG_PATH, "w") as f:
            toml.dump(default_config, f)

    config = toml.load(CONFIG_PATH)
    if "handle" not in config["user"] or not config["user"]["handle"].strip():
        name = input("Wie heißt du? Gib deinen Namen ein: ").strip()
        config["user"]["handle"] = name
        with open(CONFIG_PATH, "w") as f:
            toml.dump(config, f)
        print(f"✅ Name gespeichert: {name}")
    else:
        print(f"Willkommen zurück, {config['user']['handle']}!")

## @brief Startet eine GUI-Instanz in diesem Prozess.
#  @param username Benutzer-Handle (wird aktuell nicht direkt genutzt).
#  @param port UDP-Port zum Empfang von Nachrichten.
#  @param peers Liste von `(ip, port)`-Tupeln der Chat-Teilnehmer.
def start_gui(username, port, peers):
    app = QApplication(sys.argv)
    fenster = ChatWindow(listen_port=port, peers=peers)
    sys.exit(app.exec_())

## @brief Hauptfunktion mit Auswahl zwischen GUI und CLI.
#  @details Fragt den Benutzer, ob er eine oder zwei GUI-Fenster starten möchte
#           oder in den CLI-Modus wechselt.
def main():
    print("Starte BSRN Chat")
    initialize_user()
    print("1 = GUI starten")
    print("2 = CLI starten")
    auswahl = input("Auswahl (1/2): ").strip()

    if auswahl == "1":
        # GUI-Instanzen für zwei Nutzer erzeugen
        username1 = "Sohal"
        port1 = 4567
        peers1 = [("127.0.0.1", 4568)]

        username2 = "Sumaya"
        port2 = 4568
        peers2 = [("127.0.0.1", 4567)]

        p1 = Process(target=start_gui, args=(username1, port1, peers1))
        p2 = Process(target=start_gui, args=(username2, port2, peers2))

        p1.start()
        p2.start()

        p1.join()
        p2.join()

    elif auswahl == "2":
        cli_chat.main()

    else:
        print("Ungültige Auswahl")

## @brief Entry-Point für Windows-Freeze und direkten Start.
if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    main()

