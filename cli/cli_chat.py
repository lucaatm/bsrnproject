# cli/cli_chat.py

import threading
import toml
import atexit
from core.slcp import SLCPChat
import core.discovery as discovery
import time

config = toml.load("resources/config.toml")
HANDLE = config["user"]["handle"]
PORT = config["user"]["port"][0]
IMAGE_PORT = config["user"].get("imageport", 6000)
WHOIS_PORT = config["network"]["whoisport"]
INACTIVE = config["user"]["inactive"]
AUTOREPLYMSG = config["user"]["autoreply"]

chat = SLCPChat(HANDLE, PORT, IMAGE_PORT, WHOIS_PORT)

def leave_chat():
    try:
        chat.leave()
        print(f"[{HANDLE}] just left!")
    except Exception as e:
        print(f"[Error] Could not leave. {e}")

atexit.register(leave_chat)

def on_message(message, addr):
    if message.startswith("KNOWNUSERS"):
        users = chat.parse_knownusers(message)
        print("Known users:")
        for user in users:
            print(f"User: {user},\t\t IP: {users[user][0]},\t\t Port: {users[user][1]}")
    elif message.startswith(HANDLE):
        print(f"[{addr[0]}]: {message}")
    else:
        print(f"[{addr[0]}]: {message}")



        # Automatische Antwort, wenn INACTIVE aktiv ist
        if INACTIVE:
            sender_handle = message.split()[0].replace(":", "")
            if sender_handle != HANDLE:
                # Versuche über known_users, sonst direkt an Absenderadresse
                success, error = chat.send_message(sender_handle, AUTOREPLYMSG)
                if not success:
                    # Fallback: direkt an Absender-IP und Port antworten
                    try:
                        chat.sock.sendto(f"{HANDLE}: {AUTOREPLYMSG}".encode(), addr)
                        print(f"[AutoReply] Nachricht an {sender_handle} gesendet: {AUTOREPLYMSG}")
                    except Exception as e:
                        print(f"[AutoReply-Error] {e}")




def input_loop():
    print("You already Joined the chat as:", HANDLE, ". Enter 'WHO' to see other online users.")
    print("Use 'MSG <Handle> <Message>' to send a message, or 'IMG <Handle> <ImagePath>' to send an image.")
    print("\nEnter 'LEAVE' to leave, 'JOIN' to join the chat.")
    while True:
        user_input = input(f"{HANDLE}: ").strip()
        if not user_input:
            return

        parts = user_input.split(" ", 2)
        command = parts[0].upper()

        ## JOIN-Command
        if command == "JOIN":
            chat.send_join()
        
        ## LEAVE-Command
        elif command == "LEAVE":
            leave_chat()

        ## WHO-Command
        elif command == "WHO":
            chat.request_who()

        ## MSG-Command
        elif command == "MSG" and len(parts) == 3:
            _, recipient, message = parts
            success, error = chat.send_message(recipient, message)
            if not success:
                print(error)

        ## IMG-Command
        elif command == "IMG" and len(parts) == 3:
            _, recipient, image_path = parts
            success, error = chat.send_image(recipient, image_path)
            if not success:
                print(error)

        ## CONFIG-Commands
        elif command == "CONFIG":
            if len(parts) < 2:
                print('[Configuration] Invalid command. Try HELP for a list of commands.')
                continue
            subcommand = parts[1].upper()
            ## Handle-Konfiguration
            if subcommand == "HANDLE":
                if len(parts) < 3:
                    print("[Configuration] Invalid command. Use 'CONFIG Handle <Handle>'.")
                    continue
                new_handle = parts[2].strip()
                if new_handle:
                    config["user"]["handle"] = new_handle
                    with open("resources/config.toml", "w") as f:
                        toml.dump(config, f)
                    print(f"[Configuration] Handle changed to: {new_handle}")
                else:
                    print("[Configuration] Invalid command. Use 'CONFIG Handle <Handle>'.")
            
            ## Port-Konfiguration
            elif subcommand == "PORT":
                if len(parts) < 3 or not parts[2].strip():
                    print("[Configuration] Invalid command. Use 'CONFIG Port <Port>'.")
                    continue
                try:
                    new_port = int(parts[2].strip())
                    config["user"]["port"] = [new_port]
                    with open("resources/config.toml", "w") as f:
                        toml.dump(config, f)
                    print(f"[Configuration] Port changed to {new_port}")
                except ValueError:
                    print("[Configuration] Invalid command. Use 'CONFIG Port <Port>'.")

            ## ImagePort-Konfiguration
            elif subcommand == "IMAGEPORT":
                if len(parts) < 3 or not parts[2].strip():
                    print("[Configuration] Invalid command. Use 'CONFIG Imageport <Imageport>'.")
                    continue
                try:
                    new_port = int(parts[2].strip())
                    config["user"]["imageport"] = [new_port]
                    with open("resources/config.toml", "w") as f:
                        toml.dump(config, f)
                    print(f"[Configuration] Port changed to: {new_port}")
                except ValueError:
                    print("[Configuration] Invalid command. Use 'CONFIG Port <Port>'.")
            
            ## Inactive-Konfiguration
            elif subcommand == "INACTIVE":
                if parts[2].upper() == "ON":
                    config["user"]["inactive"] = True
                    with open("resources/config.toml", "w") as f:
                        toml.dump(config, f)
                        status = "activated" if config["user"]["inactive"] else "deactivated"
                        print(f"[Configuration] Automatische Antwort {status}.")
                elif parts[2].upper() == "OFF":
                    config["user"]["inactive"] = False
                    with open("resources/config.toml", "w") as f:
                        toml.dump(config, f)
                        status = "activated" if config["user"]["inactive"] else "deactivated"
                        print(f"[Configuration] Autoreply {status}.")
                else:
                    print("[Configuration] Invalid command. Use 'CONFIG Inactive ON' or 'CONFIG Inactive OFF'.")
                    return

            ## Autoreply-Konfiguration
            elif subcommand == "AUTOREPLY":
                if len(parts) < 3 or not parts[2].strip():
                    print("[Configuration] Invalid command. Use 'CONFIG Autoreply <Message>'.")
                    continue
                new_message = parts[2].strip()
                config["user"]["autoreply"] = new_message
                with open("resources/config.toml", "w") as f:
                    toml.dump(config, f)
                print(f"[Configuration] Autoreply changed to: {new_message}")

            else:
                print("[Configuration] Invalid command. Try 'HELP' for a list of commands.")

        ## HELP-Command
        elif command == "HELP":
            print("Commands available:")
            print("JOIN - Join the chat.")
            print("LEAVE - Leave the chat.")
            print("WHO - Show all known users.")
            print("MSG <Handle> <Message> - Send a message to a specific user.")
            print("IMG <Handle> <ImagePath> - Send an image to a specific user.")
            print("CONFIG Handle <Handle> - Change your handle.")
            print("CONFIG Port <Port> - Change your port.")
            print("CONFIG ImagePort <ImagePort> - Change your image-port.")
            print("CONFIG Inactive <ON/OFF> - Activate/deactivate autoreply.")
            print("CONFIG Autoreply <Message> - Change the autoreply message.")
            print("HELP - Show this help page.")

        else:
            print("Unknown command.")

def main():
    discovery.start_discovery_service()
    chat.send_join()
    threading.Thread(target=chat.listen_for_messages, args=(on_message,), daemon=True).start()
    threading.Thread(target=chat.receive_images, daemon=True).start()
    time.sleep(0.5)
    input_loop()

if __name__ == "__main__":
    main()