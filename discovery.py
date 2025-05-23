import socket
import threading
import toml


config = toml.load("config.toml")
handle = config.get("user", {}).get("handle", "Unknown")
PORT = config.get("user", {}).get("ports", [5001])[0]
WHOIS_PORT = config.get("network", {}).get("whoisport", 4000)
BUFFER_SIZE = 1024

participants = {}  


def broadcast(msg, port=WHOIS_PORT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(msg.encode('utf-8'), ('255.255.255.255', port))
    sock.close()


def send_direct(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message.encode('utf-8'), (ip, port))
    sock.close()


def handle_join(tokens, addr):
    if len(tokens) != 3:
        return
    handle = tokens[1]
    try:
        port = int(tokens[2])
        participants[handle] = (addr[0], port)
        print(f"[Discovery] {handle} hinzugefügt: {addr[0]}:{port}")
    except ValueError:
        print("[Discovery] Ungültiger Port in JOIN")


def handle_leave(tokens, addr):
    if len(tokens) != 2:
        return
    handle = tokens[1]
    if handle in participants:
        del participants[handle]
        print(f"[Discovery] {handle} entfernt")

def handle_who(addr):
    if not participants:
        return

    for h, (ip, p) in participants.items():
       if ip == addr[0]:  
            response = "KNOWNUSERS " + " ".join(f"{h} {ip} {p}" for h, (ip, p) in participants.items())
            send_direct(ip, p, response)  
            print(f"[Discovery] KNOWNUSERS an {ip}:{p} gesendet")
            return



def listen():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', WHOIS_PORT))
    print(f"[Discovery] Lauscht auf Port {WHOIS_PORT}")

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
            print(f"[Discovery-Fehler] {e}")


def start_discovery_service():
    thread = threading.Thread(target=listen, daemon=True)
    thread.start()


def send_join(handle, port):
    message = f"JOIN {handle} {port}"
    broadcast(message)