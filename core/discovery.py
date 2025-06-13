import socket
import threading
import toml
import time

try:
    config = toml.load("resources/config.toml")
except FileNotFoundError:
    print("[Error] Configuration file not found. Using default settings.")
    config = {"user": {"handle": "Unknown", "ports": [5001]}, "network": {"whoisport": 4000}}
except toml.TomlDecodeError:
    print("[Error] Malformed configuration file. Using default settings.")
    config = {"user": {"handle": "Unknown", "ports": [5001]}, "network": {"whoisport": 4000}}
handle = config.get("user", {}).get("handle", "Unknown")
PORT = config.get("user", {}).get("ports", [5001])[0]
WHOIS_PORT = config.get("network", {}).get("whoisport", 4000)
BUFFER_SIZE = 512

participants = {}  

## Broadcasts a message to all participants in the network
def broadcast(msg):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(msg.encode('utf-8'), ('255.255.255.255', WHOIS_PORT))
    sock.close()

## Sends a direct message to a specific IP and port
def send_direct(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message.encode('utf-8'), (ip, port))
    sock.close()

## HANDLES
## Handles the JOIN command from a participant
def handle_join(tokens, addr):
    if len(tokens) != 3:
        return
    handle = tokens[1]
    try:
        port = int(tokens[2])
        participants[handle] = (addr[0], port)
        print(f"[Discovery] {handle} just joined!")
    except ValueError:
        print("[Discovery] Invalid port in JOIN")

## Handles the LEAVE command from a participant
def handle_leave(tokens, addr):
    if len(tokens) != 2:
        return
    handle = tokens[1]
    if handle in participants:
        del participants[handle]
        print(f"[Discovery] {handle} just left!")

## Handles the WHO command to list all known participants
def handle_who(addr):
    if not participants:
        return
    
    for h, (ip,p) in participants.items():
        if ip == addr[0]:
            response = "KNOWNUSERS " + " ".join(f"{h} {ip} {p}" for h, (ip, p) in participants.items())
            send_direct(ip, p,response)
            print(f"[Discovery] KNOWNUSERS sent to {ip}:{p}")
            return

## Listens for incoming discovery messages using the WHOIS_PORT such as JOIN, LEAVE, and WHO and handles them
def listen(): 
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', WHOIS_PORT))
    print(f"[Discovery] Listening on port {WHOIS_PORT}")

    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            message = data.decode('utf-8').strip()
            tokens = message.split()
            if not tokens:
                continue

            command = tokens[0].upper()
            if command == "JOIN":
                handle_join(tokens, addr)
            elif command == "LEAVE":
                handle_leave(tokens, addr)
            elif command == "WHO":
                handle_who(addr)
        except Exception as e:
            print(f"[Discovery-Error] {e}")

## Starts the discovery service which is used in cli_chat.py in a separate thread
def start_discovery_service():
    thread = threading.Thread(target=listen, daemon=True)
    thread.start()

# Sends a JOIN message to the network to announce the participant's handle and port, which is used in cli_chat.py
def send_join(handle, port):
    message = f"JOIN {handle} {port}"
    broadcast(message)