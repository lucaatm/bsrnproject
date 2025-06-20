## @file discovery.py
# @brief Einfacher UDP-Discovery-Service für das Chat-Projekt.
# @details Dieses Modul hört auf einem bekannten Broadcast-Port und verwaltet alle Chat-Teilnehmer im lokalen Netzwerk.
# Teilnehmer melden sich über **JOIN** an, verabschieden sich über **LEAVE** und können alle bekannten Nutzer mit **WHO** abfragen.
# Die Datenstruktur `participants` ist unser In-Memory-Verzeichnis.

import socket
import threading
import toml
import time
from typing import Dict, Tuple


## Konfiguration laden (Fehlende oder fehlerhafte Konfig wird abgefangen)
try:
    config = toml.load("resources/config.toml")
except FileNotFoundError:
    print("[Fehler] Konfigurationsdatei nicht gefunden. Nutze Standardwerte.")
    config = {
        "user": {"handle": "Unbekannt", "ports": [5001]},
        "network": {"whoisport": 4000}
    }
except toml.TomlDecodeError:
    print("[Fehler] Fehlerhafte Konfigurationsdatei. Nutze Standardwerte.")
    config = {
        "user": {"handle": "Unbekannt", "ports": [5001]},
        "network": {"whoisport": 4000}
    }

## @brief Der eigene Handle aus der Konfiguration.
HANDLE: str = config.get("user", {}).get("handle", "Unbekannt")
## @brief Der Port für eingehende Discovery-Nachrichten.
PORT: int = config.get("user", {}).get("ports", [5001])[0]
## @brief Der Port, auf dem Discovery-Anfragen empfangen werden.
WHOIS_PORT: int = config.get("network", {}).get("whoisport", 4000)
## @brief Maximale Puffergröße für UDP-Pakete.
BUFFER_SIZE: int = 512

## @brief In-Memory-Verzeichnis: {handle: (ip, port)}
participants: Dict[str, Tuple[str, int]] = {}


## @brief Sendet `message` als UDP-Broadcast an WHOIS_PORT.
## @param message Nachricht, die als UTF-8 gesendet wird.
def broadcast(message: str) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(message.encode("utf-8"), ("255.255.255.255", WHOIS_PORT))
    sock.close()

## @brief Sendet eine UDP-Nachricht direkt an ip:port.
## @param ip Ziel-IP-Adresse (String)
## @param port Ziel-Port (int)
## @param message Inhalt der Nachricht (UTF-8 String)
def send_direct(ip: str, port: int, message: str) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message.encode("utf-8"), (ip, port))
    sock.close()


## @brief Verarbeitet ein eingehendes JOIN-Kommando.
## @details Erwartetes Format: `JOIN <handle> <port>`
## @param tokens Tokenisierte Nachricht als Liste von Strings.
## @param addr Absenderadresse (IP, Port) des Sockets.
def handle_join(tokens: list[str], addr: Tuple[str, int]) -> None:
    if len(tokens) != 3:
        return
    handle = tokens[1]
    try:
        port = int(tokens[2])
        participants[handle] = (addr[0], port)
        print(f"[Discovery] {handle} ist beigetreten!")
    except ValueError:
        print("[Discovery] Ungültiger Port in JOIN")

## @brief Verarbeitet ein eingehendes LEAVE-Kommando.
## @details Erwartetes Format: `LEAVE <handle>`
## @param tokens Tokenisierte Nachricht als Liste von Strings.
## @param addr Absenderadresse (IP, Port).
def handle_leave(tokens: list[str], addr: Tuple[str, int]) -> None:
    if len(tokens) != 2:
        return
    handle = tokens[1]
    if handle in participants:
        del participants[handle]
        print(f"[Discovery] {handle} hat den Chat verlassen.")

## @brief Beantwortet ein WHO-Kommando mit allen bekannten Nutzern.
## @details Sendet eine `KNOWNUSERS`-Antwort direkt (Unicast) zurück.
## @param addr Absenderadresse (IP, Port) für die Antwort.
def handle_who(addr: Tuple[str, int]) -> None:
    if not participants:
        return
    entries = [f"{h} {ip} {p}" for h, (ip, p) in participants.items()]
    response = "KNOWNUSERS " + " ".join(entries)
    send_direct(addr[0], addr[1], response)
    print(f"[Discovery] KNOWNUSERS an {addr[0]}:{addr[1]} gesendet")




## @brief Lauscht auf WHOIS_PORT auf Discovery-Kommandos (JOIN, LEAVE, WHO) in Endlosschleife.
def listen() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", WHOIS_PORT))
    print(f"[Discovery] Lausche auf Port {WHOIS_PORT}")
    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            message = data.decode("utf-8").strip()
            tokens = message.split()
            if not tokens:
                continue
            cmd = tokens[0].upper()
            if cmd == "JOIN":
                handle_join(tokens, addr)
            elif cmd == "LEAVE":
                handle_leave(tokens, addr)
            elif cmd == "WHO":
                handle_who(addr)
        except Exception as e:
            print(f"[Discovery-Error] {e}")



## @brief Startet den Discovery-Dienst in einem Hintergrundthread.
def start_discovery_service() -> None:
    thread = threading.Thread(target=listen, daemon=True)
    thread.start()

## @brief Kündigt die eigene Anwesenheit im Netzwerk an.
## @param handle Benutzername, unter dem man im Netzwerk bekannt sein will.
## @param port Port, auf dem das eigene Programm Chatdaten empfängt.
def send_join(handle: str, port: int) -> None:
    message = f"JOIN {handle} {port}"
    broadcast(message)
