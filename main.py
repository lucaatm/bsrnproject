## @file main.py
#  @brief Einstiegspunkt für das BSRN-Chatprogramm.
#  @details Initialisiert Konfiguration, Prüft auf Discovery-Prozess, startet CLI und Netzwerk-Komponenten.
import os
import sys
import toml
import tempfile
import signal
from multiprocessing import Process, Queue
from core.cli import CLI
from core.network import Network
from core.discovery import Discovery

CONFIG_PATH = "config/config.toml"
LOCKFILE_NAME = "discovery.lock"

## @brief Lädt Konfigurationsdatei.
#  @return Dictionary mit Konfigurationsdaten
def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r") as f:
        return toml.load(f)

## @brief Speichert Konfiguration in Datei.
#  @param cfg Konfigurations-Dictionary
def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        toml.dump(cfg, f)

## @brief Fragt fehlende Konfiguration vom Benutzer ab.
#  @param cfg Konfigurations-Dictionary (wird direkt bearbeitet)
def prompt_missing_config(cfg):
    if not cfg.get("handle"):
        cfg["handle"] = input("Wie heißt du? ").strip()
    if not cfg.get("port"):
        cfg["port"] = int(input("Welchen Port möchtest du verwenden? ").strip())
    if not cfg.get("whoisport"):
        cfg["whoisport"] = 4000
    if "autoreply" not in cfg:
        cfg["autoreply"] = "I am not here."
    if not cfg.get("imagepath"):
        cfg["imagepath"] = "./received"
    save_config(cfg)

## @brief Gibt Pfad zur Lockdatei zurück.
#  @return Absoluter Pfad zur temporären Lockdatei
def get_lockfile_path():
    return os.path.join(tempfile.gettempdir(), LOCKFILE_NAME)

## @brief Prüft, ob Discovery-Prozess läuft.
#  @param lockfile_path Pfad zur Lockdatei
#  @return True wenn Prozess läuft, sonst False
def check_discovery_alive(lockfile_path):
    if not os.path.exists(lockfile_path):
        return False
    try:
        with open(lockfile_path, "r") as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return True
    except:
        os.remove(lockfile_path)
        return False

## @brief Startet CLI, Netzwerk und optional Discovery-Prozess.
def main():
    config = load_config()
    prompt_missing_config(config)

    handle = config["handle"]
    port = config["port"]
    whoisport = config["whoisport"]

    # IPC Queues
    cli_to_net = Queue()
    net_to_cli = Queue()
    cli_to_disc = Queue()
    disc_to_cli = Queue()

    # Discovery vorbereiten
    lockfile_path = get_lockfile_path()
    p_disc = None
    if not check_discovery_alive(lockfile_path):
        with open(lockfile_path, "w") as f:
            f.write(str(os.getpid()))
        disc = Discovery(cli_to_disc, disc_to_cli, config['imagepath'])
        p_disc = Process(target=disc.run, name="Discovery")
        p_disc.start()

    # Network vorbereiten
    net = Network(handle, port, cli_to_net, net_to_cli, cli_to_disc, disc_to_cli, config)
    p_net = Process(target=Network.run, args=(net,), name="Network")
    p_net.start()

    # Auswahlmenü für CLI oder GUI
    print("Starte Chat:")
    print("1) CLI")
    print("2) GUI")
    auswahl = input("Bitte wähle 1 oder 2: ").strip()
    if auswahl == "2":
        from core.gui import GUI
        gui = GUI(cli_to_net, net_to_cli, handle, cli_to_disc, disc_to_cli)
        gui.run()
    else:
        cli = CLI(handle, cli_to_net, cli_to_disc, net_to_cli, disc_to_cli, config)
        cli.run()

    # Prozesse beenden
    p_net.terminate()

    if p_disc:
        p_disc.terminate()
        if os.path.exists(lockfile_path):
            os.remove(lockfile_path)

if __name__ == "__main__":
    main()

