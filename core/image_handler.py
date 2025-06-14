## @file image_handler.py
# @brief Diese Datei enthält Funktionen zum Senden und Empfangen von Bildern über UDP.
# Sie ermöglicht das einfache Teilen von Bildern zwischen Benutzern in einem Netzwerk.
# @note Diese Datei wird in SLCPChat verwendet, um Bilder zu senden und zu empfangen.

import socket
import os
import platform
import subprocess
import toml

## Die Konfigurationsdatei wird eingelesen, um alle wichtigen Benutzereinstellungen zu laden.
config = toml.load("resources/config.toml")

# Buffer Size beschreibt die maximale Größe eines Datenpakets, das über UDP gesendet werden soll.
BUFFER_SIZE = 512

# Image Path ist der Pfad, in dem empfangene Bilder gespeichert werden sollen. Dieser kann in der Konfigurationsdatei festgelegt werden.
IMAGEPATH = config["image"]["imagepath"]

## @brief Sendet ein Bild über UDP an die angegebene IP-Adresse und den Port.
# @param image_path Der Pfad zum Bild, das gesendet werden soll.
# @param target_ip Die IP-Adresse des Empfängers.
# @param target_port Der Port des Empfängers, an den das Bild gesendet werden soll.
# @details Diese Funktion teilt das Bild in kleinere Pakete (mit der Größe BUFFER_SIZE) auf und sendet sie über UDP. Zuvor wird ein Header gesendet, der den Namen und die exakte Größe des Bildes enthält. Diese kann verwendet werden, als Empfänger nachzuschauen, ob das Bild vollständig empfangen wurde.
def send_image(image_path, target_ip, target_port):
    if not os.path.isfile(image_path):
        print(f"[Error] File not found: {image_path}")
        return

    with open(image_path, "rb") as f:
        image_data = f.read()

    # Zusammenstellen des Headers mit Bildname und Größe
    image_size = len(image_data)
    image_name = os.path.basename(image_path)
    header_msg = f"IMG {image_name} {image_size}"

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(header_msg.encode("utf-8"), (target_ip, target_port))

    # Senden des Bildes in kleineren Paketen
    for i in range(0, image_size, BUFFER_SIZE):
        chunk = image_data[i:i + BUFFER_SIZE]
        sock.sendto(chunk, (target_ip, target_port))

    sock.close()

    print(f"[Image sent] {image_name} ({image_size} Bytes)")

## @brief Empfängt Bilder über UDP und speichert sie im angegebenen Verzeichnis.
# @param port Der Port, auf dem der Client auf eingehende Bildübertragungen wartet.
# @param save_dir Das Verzeichnis, in dem die empfangenen Bilder gespeichert werden sollen. Standardmäßig ist dies der in der Konfigurationsdatei festgelegte IMAGEPATH. 
# Wenn ein Bild empfangen wird, wird es im angegebenen Verzeichnis gespeichert und versucht, es automatisch zu öffnen. Die Funktion wird in CLI-Chat durch die Funktion `threading.Thread(target=chat.receive_images, daemon=True).start()` als Daemon aufgerufen.
# @note Diese Funktion enthält eine Endlosschleife, die auf eingehende UDP-Pakete wartet.
def receive_image(callback=None, port=6000, save_dir=IMAGEPATH):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", port))
    print(f"[Image-Handler] Listening on port: {port}...")

    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            message = data.decode("utf-8", errors="ignore")

            if message.startswith("IMG"):
                _, image_name, image_size = message.split()
                image_size = int(image_size)
                image_path = os.path.join(save_dir, image_name)

                # Da die Datei ein Bild ist, wird hier "wb" verwendet. Dies steht für "write binary" und stellt sicher, dass die Datei im Binärformat geschrieben wird.
                with open(image_path, "wb") as f:
                    bytes_received = 0
                    while bytes_received < image_size:
                        chunk, _ = sock.recvfrom(BUFFER_SIZE)
                        f.write(chunk)
                        bytes_received += len(chunk)

                print(f"[Bild empfangen] Gespeichert als {image_path}")
                if callback:
                    callback(f"[Bild gespeichert unter: {image_path}]")
                
                # Bild wird automatisch geöffnet. Abhängig vom Betriebssystem wird das entsprechende Kommando verwendet.
                try:
                    if platform.system() == "Windows":
                        os.startfile(image_path)
                    elif platform.system() == "Darwin":
                        subprocess.run(["open", image_path])
                    else:
                        subprocess.run(["xdg-open", image_path])
                except Exception as e:
                    print(f"[Bildanzeige fehlgeschlagen]: {e}")

        except Exception as e:
            print(f"[Fehler beim Empfang]: {e}")
