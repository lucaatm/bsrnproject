## @file cli_chat.py
# @brief Diese Datei implementiert die Kommandozeilen-Schnittstelle (CLI) für den SLCP-Chat.
# Sie ermöglicht es Benutzern, Nachrichten zu senden, Bilder zu teilen und die Chat-Konfiguration zu ändern. 

import threading
import toml
import atexit
from core.slcp import SLCPChat
import core.discovery as discovery
import time
from prettytable import PrettyTable
from config.config_loader import save_config

## Die Konfigurationsdatei wird eingelesen, um alle wichtigen Benutzereinstellungen zu laden.
# @details Diese Einstellungen umfassen den Benutzernamen, die Ports für Nachrichten und Bilder sowie die Whois-Portnummer.
## @note Für den Image-Port wird ein Standardwert von 6000 verwendet, falls nicht anders konfiguriert.
config = toml.load("resources/config.toml")

HANDLE = config["user"]["handle"]
PORT = config["user"]["port"][0]
IMAGE_PORT = config["user"].get("imageport", 6000)
WHOIS_PORT = config["network"]["whoisport"]
INACTIVE = config["user"]["inactive"]
AUTOREPLYMSG = config["user"]["autoreply"]

## Initialisierung des SLCPChat-Objekts mit den geladenen Konfigurationen.
# Dieses Objekt wird letztendlich verwendet, um Nachrichten zu senden, Bilder zu teilen und die Chat-Funktionalität zu verwalten.
chat = SLCPChat(HANDLE, PORT, IMAGE_PORT, WHOIS_PORT)

## @brief Diese Funktion wird aufgerufen, wenn der Benutzer den Chat verlässt.
# @details Sie sendet eine LEAVE-Nachricht an den Discovery-Service und gibt eine Bestätigung aus. Im Falle eines Fehlers wird eine Fehlermeldung ausgegeben.
# @note Sie wird durch die `atexit`-Bibliothek ausgeführt, um sicherzustellen, dass sie beim Beenden des Programms aufgerufen wird.

def leave_chat():
    try:
        chat.leave()
        print(f"[{HANDLE}] You just left!")
    except Exception as e:
        print(f"[Error] Could not leave. {e}")

atexit.register(leave_chat)

## @brief Diese Funktion verarbeitet eingehende Nachrichten und führt dann individuelle Aktionen aus.
# @details Sie überprüft, ob die Nachricht mit "KNOWNUSERS" beginnt, um die Liste der bekannten Benutzer zu aktualisieren. Hierzu wird dann eine Tabelle mithilfe der PrettyTable-Bibliothek erstellt und ausgegeben.
# @details Wenn die Nachricht nicht mit "KNOWNUSERS" beginnt, wird sie als normale Chat-Nachricht behandelt und ausgegeben. Dazu wird überprüft, ob der Nutzer inaktiv ist und somit eine automatische Antwort gesendet werden soll. Falls ja, wird die Abwesenheitsnachricht an den Absender zurück gesendet.
# @param message: Die empfangene Nachricht.
# @param addr: Die Adresse des Absenders der Nachricht.

def on_message(message, addr):
    if message.startswith("KNOWNUSERS"):
        users = chat.parse_knownusers(message)
        print("Known users:")
        t = PrettyTable(['Name', 'IP', "Port"])
        for user in users:
            t.add_row([user, users[user][0], users[user][1]])
        print(t)
    elif message.startswith(HANDLE):
        print(f"{message}")
    else:
        print(f"{message}")

        # Ruft außerdem die aktuelle Konfiguration ab, um zu überprüfen, ob der Benutzer inaktiv ist und eine automatische Antwort gesendet werden soll.
        config = toml.load("resources/config.toml")
        inactive = config["user"].get("inactive", False)
        autoreplymsg = config["user"].get("autoreply", "")

        if inactive:
            sender_handle = message.split()[0].replace(":", "")
            if sender_handle != HANDLE:
                success, error = chat.send_message(sender_handle, autoreplymsg)
                
                if not success:
                    try:
                        chat.sock.sendto(f"{HANDLE}: {autoreplymsg}".encode(), addr)
                        print(f"[AutoReply] Nachricht an {sender_handle} gesendet: {autoreplymsg}")
                    except Exception as e:
                        print(f"[AutoReply-Error] {e}")

## @brief Diese Funktion führt eine Endlosschleife aus, in der der Benutzer Eingaben tätigen kann.
# @details Sie verarbeitet die Eingaben des Benutzers, um verschiedene Chat-Kommandos auszuführen, wie JOIN, LEAVE, WHO, MSG und IMG und das Ändern der Konfiguration. Außerdem gibt es die Möglichkeit, per "HELP" eine Übersicht der verfügbaren Befehle zu erhalten.
def input_loop():
    print("\nYou already joined the chat as '" + HANDLE + "'. Enter 'WHO' to see other online users.")
    print("Use 'MSG <Handle> <Message>' to send a message, or 'IMG <Handle> <ImagePath>' to send an image.")
    print("Enter 'LEAVE' to leave, 'JOIN' to join the chat.")

    while True:
        user_input = input().strip()
        if not user_input:
            continue

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

            # Wenn die Nutzereingabe nicht den Anforderungen entsprichtm, wird eine Fehlermeldung angezeigt.
            # @note Der Befehl muss mindestens drei Teile haben, z. B.: "CONFIG HANDLE MeinNutzername", niemals nur "CONFIG HANDLE".
            if len(parts) < 3:
                print('[Configuration] Invalid command. Try HELP for a list of commands.')
                continue
            subcommand = parts[1].upper()

            # Konfiguration der verschiedenen Subcommands

            ## Handle-Konfiguration
            if subcommand == "HANDLE":
                new_handle = parts[2].strip()
                if new_handle:
                    config["user"]["handle"] = new_handle
                    save_config(config)
                else:
                    print("[Configuration] Invalid command. Use 'CONFIG Handle <Handle>'.")
            
            ## Port-Konfiguration
            elif subcommand == "PORT":
                try:
                    new_port = int(parts[2].strip())
                    config["user"]["port"] = [new_port]

                    
                    save_config(config)
                    print(f"[Configuration] Port changed to {new_port}")
                except ValueError:
                    print("[Configuration] Invalid command. Use 'CONFIG Port <Port>'.")

            ## ImagePort-Konfiguration
            elif subcommand == "IMAGEPORT":
                try:
                    new_port = int(parts[2].strip())
                    config["user"]["imageport"] = [new_port]
                    save_config(config)
                    print(f"[Configuration] Port changed to: {new_port}")
                except ValueError:
                    print("[Configuration] Invalid command. Use 'CONFIG Port <Port>'.")
            
            ## Inactive-Konfiguration
            elif subcommand == "INACTIVE":

                # wenn der Befehl "CONFIG Inactive ON" eingegeben wird, wird die automatische Antwort aktiviert.
                if parts[2].upper() == "ON":
                    config["user"]["inactive"] = True

                # wenn der Befehl "CONFIG Inactive OFF" eingegeben wird, wird die automatische Antwort deaktiviert.
                elif parts[2].upper() == "OFF":
                    config["user"]["inactive"] = False

                else:
                    print("[Configuration] Invalid command. Use 'CONFIG Inactive ON' or 'CONFIG Inactive OFF'.")
                    return

                save_config(config)

                status = "activated" if config["user"]["inactive"] else "deactivated"
                print(f"[Configuration] Autoreply {status}.")

            ## Autoreply-Konfiguration
            elif subcommand == "AUTOREPLY":
                new_message = parts[2].strip()
                config["user"]["autoreply"] = new_message
                
                save_config(config)

                print(f"[Configuration] Autoreply changed to: {new_message}")

            else:
                print("[Configuration] Invalid command. Try 'HELP' for a list of commands.")

        ## HELP-Befehl
        elif command == "HELP":
            print("—————————————————————")
            print("Commands available:")
            print("—————————————————————")
            print("JOIN\t\t\t\tJoin the chat.")
            print("LEAVE\t\t\t\tLeave the chat.")
            print("WHO\t\t\t\tShow all known users.")
            print("MSG <Handle> <Message>\t\tSend a message to a specific user.")
            print("IMG <Handle> <ImagePath>\tSend an image to a specific user.")
            print("CONFIG Handle <Handle>\t\tChange your handle.")
            print("CONFIG Port <Port>\t\tChange your port.")
            print("CONFIG ImagePort <ImagePort>\tChange your image-port.")
            print("CONFIG Inactive <ON/OFF>\tActivate/deactivate autoreply.")
            print("CONFIG Autoreply <Message>\tChange the autoreply message.")
            print("HELP\t\t\t\tShow this help page.")

        else:
            print("Unknown command.")

## @brief Die main-Funktion startet den Discovery-Service und die Chat-Funktionalität.
# @details Sie startet Threads im "daemon"-Modus, um Nachrichten zu empfangen und Bilder zu senden, und wartet auf Benutzereingaben in einer Endlosschleife.
def main():
    discovery.start_discovery_service()
    threading.Thread(target=chat.listen_for_messages, args=(on_message,), daemon=True).start()
    threading.Thread(target=chat.receive_images, daemon=True).start()
    time.sleep(0.5)
    chat.send_join()
    input_loop()

if __name__ == "__main__":
    main()