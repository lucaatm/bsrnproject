## @file image_handler.py
#  @brief Funktionen zum Speichern, Öffnen und Verarbeiten von Bildern.

import os
import platform
import uuid

## @brief Speichert ein Bild und öffnet es im Standardprogramm.
#  @param sender Name des Absenders
#  @param binary_data Bilddaten als Bytes
#  @param imagepath Zielordner zum Speichern
#  @return Vollständiger Pfad der gespeicherten Datei oder None bei Fehler
def save_and_open_image(sender, binary_data, imagepath):
    try:
        folder = os.path.abspath(imagepath)
        os.makedirs(folder, exist_ok=True)

        filename = f"{sender}_{uuid.uuid4().hex[:8]}.jpg"
        full_path = os.path.join(folder, filename)

        with open(full_path, "wb") as f:
            f.write(binary_data)

        try:
            if platform.system() == "Windows":
                os.startfile(full_path)
            elif platform.system() == "Darwin":
                os.system(f"open \"{full_path}\"")
            else:
                os.system(f"xdg-open \"{full_path}\"")
        except Exception as e:
            print(f"[⚠️ Fehler beim Öffnen des Bildes] {e}")

        return full_path

    except Exception as e:
        print(f"[❌ Fehler beim Speichern des Bildes] {e}")
        return None

## @brief Lädt ein Bild als Bytes aus einer Datei.
#  @param path Pfad zur Bilddatei
#  @return Bilddaten oder None bei Fehler
def load_image_as_bytes(path):
    try:
        with open(path, "rb") as f:
            return f.read()
    except Exception as e:
        print(f"[❌ Fehler beim Laden der Bilddatei: {path}] {e}")
        return None

## @brief Teilt einen base64-String in kleinere Stücke.
#  @param b64_string Base64-kodierte Bilddaten
#  @param max_size Maximale Länge pro Stück (Standard: 512)
#  @return Liste mit String-Chunks
def chunk_image_data(b64_string, max_size=512):
    return [b64_string[i:i+max_size] for i in range(0, len(b64_string), max_size)]