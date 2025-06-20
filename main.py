from config.config_loader import load_config, save_config
import cli.cli_chat as cli_chat
import sys
import os, toml
from PyQt5.QtWidgets import QApplication
from gui.chat_window import ChatWindow
from multiprocessing import Process

CONFIG_PATH = "resources/config.toml"

# Erstellt Konfigurationsdatei, falls nicht vorhanden
def initialize_user():
    if not os.path.exists(CONFIG_PATH):
        print("⚠️ config.toml wurde nicht gefunden. Wird neu erstellt.")
        default_config = {
            "user": {
                "handle": "",
                "port": [5001]
            },
            "network": {
                "whoisport": 5001
            },
            "settings": {
                "autoreply": "Bin nicht da",
                "imagepath": "./received_images"
            }
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

# Startet eine GUI-Instanz mit übergebenen Parametern
def start_gui(username, port, peers):
    app = QApplication(sys.argv)
    fenster = ChatWindow(listen_port=port, peers=peers)

    sys.exit(app.exec_())

# Hauptfunktion mit GUI/CLI Auswahl
def main():
    print("Starte BSRN Chat")
    initialize_user()
    print("1 = GUI starten (Sohal + Sumaya)")
    print("2 = CLI starten")
    auswahl = input("Auswahl (1/2): ").strip()

    if auswahl == "1":
        # GUI 1l
        username1 = "Sohal"
        port1 = 4567
        peers1 = [("127.0.0.1", 4568)]

        # GUI 2
        username2 = "Sumaya"
        port2 = 4568
        peers2 = [("127.0.0.1", 4567)]

        # Beide GUIs parallel in eigenen Prozessen starten
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


if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()  
    main()
