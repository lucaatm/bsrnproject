## @file config_loader.py
# @brief Diese Datei enthält Funktionen zum Laden und Speichern der Konfiguration aus einer TOML-Datei.
# Sie ermöglicht das einfache Management von Konfigurationseinstellungen für die Anwendung.
import toml
import os

CONFIG_PATH = "resources/config.toml"

## @brief Lädt die Konfiguration aus der angegebenen TOML-Datei.
## @return Gibt die geladene Konfiguration als Dictionary zurück.
## @note Raises FileNotFoundError Wenn die Konfigurationsdatei nicht gefunden wird.
def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"{CONFIG_PATH} nicht gefunden.")
    return toml.load(CONFIG_PATH)

## @brief Speichert die gegebene Konfiguration in der angegebenen TOML-Datei.
## @param config Der zu speichernde Dictionary-Eintrag.
def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        toml.dump(config, f)