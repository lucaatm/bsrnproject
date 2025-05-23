
import socket
import threading
import toml
import os
import time
import discovery
import image_handler

config = toml.load("config.toml")
HANDLE = config["user"]["handle"]
PORT = config["user"]["port"][0]
IMAGE_PORT = config["user"].get("imageport", 6000)
WHOIS_PORT = config["network"]["whoisport"]
BUFFER_SIZE = 512

known_users = {}
buffered_users = {}
last_who_time = 0


def listen_for_messages():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", PORT))
    print(f"[{HANDLE}] Empfang läuft auf Port {PORT}")
    while True:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        try:
            message = data.decode(errors="ignore")
        except UnicodeDecodeError:
            continue
        if message.startswith("KNOWNUSERS"):
            parse_knownusers(message)
        elif message.startswith(HANDLE):
            print(f"[{addr[0]}]: {message}")
        else:
            print(f"[{addr[0]}]: {message}")


def parse_knownusers(message):
    global buffered_users, last_who_time
    parts = message.split()[1:]
    for i in range(0, len(parts), 3):
        try:
            handle, ip, port = parts[i], parts[i + 1], int(parts[i + 2])
            buffered_users[handle] = (ip, port)
        except (IndexError, ValueError):
            continue
    last_who_time = time.time()

def flush_known_users():
    global known_users, buffered_users, last_who_time
    while True:
        time.sleep(1)
        if buffered_users and (time.time() - last_who_time > 0.5):
            known_users = dict(buffered_users)
            buffered_users.clear()
            print(f"[{HANDLE}] Aktualisierte Benutzerliste: {known_users}")


def send_slcp_message():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("SLCP: JOIN <Handle> <Port>, LEAVE <Handle>, WHO, MSG <Handle> <Nachricht>, IMG <Handle> <Bilddatei>")

    while True:
        user_input = input(f"{HANDLE}: ").strip()
        if not user_input:
            continue

        command = user_input.split(" ", 1)[0].upper()

        if command == "JOIN":
            discovery.send_join(HANDLE, PORT)
        elif command == "LEAVE":
            discovery.broadcast(f"LEAVE {HANDLE}")
        elif command == "WHO":
            discovery.broadcast("WHO")
        elif command == "MSG":
            parts = user_input.split(" ", 2)
            if len(parts) != 3:
                print("Falsches Format. Beispiel: MSG Bob Hallo")
                continue
            _, empfaenger, nachricht = parts
            if empfaenger not in known_users:
                print(f"Unbekannter Benutzer: {empfaenger}")
                continue
            ip, port = known_users[empfaenger]
            sock.sendto(f"{HANDLE}: {nachricht}".encode(), (ip, port))
        elif command == "IMG":
            parts = user_input.split(" ", 2)
            if len(parts) != 3:
                print("Falsches Format. Beispiel: IMG Bob bild.png")
                continue
            _, empfaenger, bildpfad = parts
            if empfaenger not in known_users:
                print(f"Unbekannter Benutzer: {empfaenger}")
                continue
            ip, port = known_users[empfaenger]
            image_handler.send_image(bildpfad, ip, IMAGE_PORT)
        else:
            print("Unbekannter Befehl.")


def start_cli():
    threading.Thread(target=listen_for_messages, daemon=True).start()
    threading.Thread(target=image_handler.receive_image, args=(None, IMAGE_PORT), daemon=True).start()
    send_slcp_message()
