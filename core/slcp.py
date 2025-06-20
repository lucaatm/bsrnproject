## @file slcp.py
# @brief Einfache Chat-Klasse (SLCPChat) für das Chat-Projekt.
# @details Diese Klasse kapselt die komplette Chatlogik für einen Nutzer:
# - **JOIN/LEAVE/WHO** werden an den Discovery-Dienst weitergeleitet.
# - Textnachrichten und Bilder können an bekannte Nutzer gesendet werden.
# - Eingehende Datagramme (Text) werden über einen Callback an die CLI weitergereicht.

import socket
import core.discovery as discovery
import core.image_handler as image_handler

BUFFER_SIZE = 512

class SLCPChat:
    # @class SLCPChat
    # @brief Kernklasse, die einen Chat-Client vertritt.
    # @details Die Instanz verwaltet den eigenen Handle, Ports für Text- und Bilddaten
    # sowie eine kleine Tabelle aller bekannten Nutzer (`known_users`).

    def __init__(selbst, Handle: str, Port: int, Bildport: int, whois_port: int):
        # @brief Konstruktor.
        # @param handle Eigener Chat-Name
        # @param port UDP-Port für Textnachrichten
        # @param image_port UDP-Port für Bilddaten
        # @param whois_port Discovery-Port (WHOIS)
        selbst.handle = Handle
        selbst.port = Port
        selbst.image_port = Bildport
        selbst.whois_port = whois_port
        selbst.known_users: dict[str, tuple[str, int]] = {}
        selbst.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_join(self) -> None:
        # @brief Meldet den Client beim Discovery-Service an.
        discovery.send_join(self.handle, self.port)

    def leave(self) -> None:
        # @brief Meldet den Client beim Discovery-Service ab.
        discovery.broadcast(f"LEAVE {self.handle}")

    def request_who(self) -> None:
        # @brief Fragt per Broadcast alle bekannten Nutzer ab.
        discovery.broadcast("WHO")

    def send_message(selbst, Empfänger: str, Nachricht: str) -> tuple[bool, str | None]:
        # @brief Sendet eine Textnachricht an *recipient*.
        # @param Empfänger Ziel-Handle
        # @param Inhalt der Nachricht
         
        if Empfänger not in selbst.known_users:
            return False, f"Unbekannter Nutzer: {Empfänger}"
        IP, Port = selbst.known_users[Empfänger]
        selbst.sock.sendto(f"{selbst.handle}: {Nachricht}".encode(), (IP, Port))
        return True, None

    def send_image(selbst, Empfänger: str, Bildpfad: str) -> tuple[bool, str | None]:
        # @brief Sendet ein Bild an *recipient*.
        # @param Empfänger Ziel-Handle
        # @param Bildpfad Pfad zur Bilddatei
    
        if Empfänger not in selbst.known_users:
            return False, f"Unbekannter Nutzer: {Empfänger}"
        ip, _ = selbst.known_users[Empfänger]
        image_handler.send_image(Bildpfad, ip, selbst.image_port)
        return True, None

    def parse_knownusers(selbst, Nachricht: str) -> dict[str, tuple[str, int]]:
        # @brief Aktualisiert `known_users` basierend auf einer **KNOWNUSERS**-Nachricht.
        # @param Nachricht Komplette KNOWNUSERS-Zeile
        # @return Aktualisiertes dictionary
        selbst.known_users.clear()
        Teile = Nachricht.split()[1:]
        for i in range(0, len(Teile), 3):
            try:
                Handle, IP, Port = Teile[i], Teile[i+1], int(Teile[i+2])
                selbst.known_users[Handle] = (IP, Port)
            except (IndexError, ValueError):
                continue
        return selbst.known_users

    def listen_for_messages(self, on_message) -> None:
        # @brief Blockiert und lauscht auf eingehende Textnachrichten.
        # @param on_message Callback `(message: str, addr: tuple) -> None
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", self.port))
        while True:
            Daten, Adresse = sock.recvfrom(BUFFER_SIZE)
            try:
                Nachricht = Daten.decode(errors="ignore")
            except UnicodeDecodeError:
                continue
            on_message(Nachricht, Adresse)

    def receive_images(self) -> None:
        # @brief Startet den Bildempfang über `image_handler`.
        image_handler.receive_image(self.image_port)
