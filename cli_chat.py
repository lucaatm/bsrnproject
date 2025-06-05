# cli_chat.py

import threading
import toml
import atexit
from slcp import SLCPChat
import discovery

config = toml.load("config.toml")
HANDLE = config["user"]["handle"]
PORT = config["user"]["port"][0]
IMAGE_PORT = config["user"].get("imageport", 6000)
WHOIS_PORT = config["network"]["whoisport"]

chat = SLCPChat(HANDLE, PORT, IMAGE_PORT, WHOIS_PORT)

def leave_chat():
    try:
        chat.leave()
        print(f"[{HANDLE}] hat den Chat verlassen.")
    except Exception as e:
        print(f"[Fehler beim Verlassen] {e}")

atexit.register(leave_chat)

def on_message(message, addr):
    if message.startswith("KNOWNUSERS"):
        users = chat.parse_knownusers(message)
        print(f"[{HANDLE}] Aktualisierte Benutzerliste: {users}")
    elif message.startswith(HANDLE):
        print(f"[{addr[0]}]: {message}")
    else:
        print(f"[{addr[0]}]: {message}")

def input_loop():
    print("SLCP: JOIN, LEAVE, WHO, MSG <Handle> <Nachricht>, IMG <Handle> <Bilddatei>")
    while True:
        user_input = input(f"{HANDLE}: ").strip()
        if not user_input:
            continue

        parts = user_input.split(" ", 2)
        command = parts[0].upper()

        if command == "JOIN":
            chat.send_join()
        elif command == "LEAVE":
            leave_chat()
        elif command == "WHO":
            chat.request_who()
        elif command == "MSG" and len(parts) == 3:
            _, recipient, message = parts
            success, error = chat.send_message(recipient, message)
            if not success:
                print(error)
        elif command == "IMG" and len(parts) == 3:
            _, recipient, image_path = parts
            success, error = chat.send_image(recipient, image_path)
            if not success:
                print(error)
        else:
            print("Ungültiger Befehl.")

def main():
    discovery.start_discovery_service()
    chat.send_join()
    threading.Thread(target=chat.listen_for_messages, args=(on_message,), daemon=True).start()
    threading.Thread(target=chat.receive_images, daemon=True).start()
    input_loop()

if __name__ == "__main__":
    main()