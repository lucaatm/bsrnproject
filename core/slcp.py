import socket
import threading


class SLCPChat:
    def __init__(self, username, listen_port, peers):
        self.username = username
        self.listen_port = listen_port
        self.peers = peers  # Liste von (IP, Port)
        self.running = False
        self.callback = None  # Wird gesetzt durch register_callback()

        # UDP-Socket einrichten
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", self.listen_port))

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.listen_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except Exception:
            pass

    def register_callback(self, callback):
        """Setzt die Methode, die auf empfangene Nachrichten reagieren soll."""
        self.callback = callback

    def send_message(self, message):
        """Sendet die Nachricht an alle eingetragenen Peers."""
        if not message:
            return

        full_message = f"{self.username}:{message}"
        data = full_message.encode("utf-8")

        for ip, port in self.peers:
            try:
                self.sock.sendto(data, (ip, port))
            except Exception as e:
                print(f"[Fehler beim Senden an {ip}:{port}] {e}")

    def listen_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                text = data.decode("utf-8")

                # Erwartetes Format: "Username:Nachricht"
                if ":" in text:
                    sender, message = text.split(":", 1)
                else:
                    sender, message = "Unbekannt", text

                if self.callback:
                    self.callback(sender.strip(), message.strip())

            except Exception as e:
                if self.running:
                    print(f"[Empfangsfehler] {e}")
