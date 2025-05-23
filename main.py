##from gui_oeffnen import MainUI
from cli_chat import start_cli
import sys
import os, toml

CONFIG_PATH = "config.toml"

def initialisiere_nutzer():
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


def main():
    print("Starte BSRN Chat")
    initialisiere_nutzer()
    print("1 = GUI starten")
    print("2 = CLI starten")
    auswahl = input("Auswahl (1/2): ").strip()

    if auswahl == "1":
        ##from PyQt5.QtWidgets import QApplication
        ##app = QApplication(sys.argv)
        ##ui = MainUI()
        ##ui.show()
        ##sys.exit(app.exec_())
        print("Not available yet")
    if auswahl == "2":
        start_cli()
    else:
        print("Ungültige Auswahl")


if __name__ == "__main__":
    main()


