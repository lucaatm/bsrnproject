##
# @file udp_handler.py
# @brief Implementierung eines einfachen UDP-Kommunikationshandlers.
#
# Diese Datei definiert die Klasse `UDPHandler`, die für das Empfangen und Senden
# von Nachrichten über das UDP-Protokoll zuständig ist. Sie unterstützt den Empfang 
# von Textnachrichten und erkennt spezielle Header wie `IMG ` zur Bildverarbeitung.

import socket
import threading

class UDPHandler:
    # @brief Konstruktor für den UDP-Handler.
    #  @param listen_port UDP-Port, auf dem eingehende Pakete empfangen werden.
    #  @param on_receive_callback Callback-Funktion, die bei einer lesbaren Nachricht oder Bild-Header ausgeführt wird.
    def __init__(self, listen_port, on_receive_callback):
        self.listen_port = listen_port
        self.on_receive_callback = on_receive_callback
        self.running = False

    # @brief Startet den Empfangsthread.
    #  @details Setzt `running = True` und startet einen Daemon-Thread, der `_receive_loop` ausführt.
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.thread.start()

    # @brief Stoppt den Empfangsthread.
    #  @details Setzt `running = False`, sodass `_receive_loop` beendet wird.
    def stop(self):
        self.running = False

    # @brief Sendet eine Nachricht an mehrere Peers.
    #  @param message Textnachricht, die als UTF-8 kodiert versendet wird.
    #  @param peers Liste von `(ip, port)`-Tupeln der Empfänger.
    def send_message(self, message, peers):
        for ip, port in peers:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(message.encode("utf-8"), (ip, port))

    # @brief Empfangsschleife für UDP-Pakete.
    #  @details Bindet an `listen_port`, setzt Timeout und dekodiert eingehende Bytes als UTF-8.
    #           Ruft das Callback nur für Textnachrichten oder Nachrichten mit Bild-Header `IMG ` auf.
    def _receive_loop(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(("", self.listen_port))
            sock.settimeout(1.0)
            while self.running:
                try:
                    data, addr = sock.recvfrom(4096)

                    try:
                        message = data.decode("utf-8")
                        if message.startswith("IMG "):
                            self.on_receive_callback(message)
                        elif message.strip() != "":
                            self.on_receive_callback(message)
                    except UnicodeDecodeError:
                        pass

                except socket.timeout:
                    continue
