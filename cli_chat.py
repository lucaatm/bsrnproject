
import socket
import threading
import toml
import os
import time
import discovery

config = toml.load("config.toml")
HANDLE = config["user"]["handle"]
PORT = config["user"]["port"][0]

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