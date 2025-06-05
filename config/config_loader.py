import toml
import os

CONFIG_PATH = "resources/config.toml"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"{CONFIG_PATH} nicht gefunden.")
    return toml.load(CONFIG_PATH)

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        toml.dump(config, f)