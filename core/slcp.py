import socket
import core.discovery as discovery
import core.image_handler as image_handler

BUFFER_SIZE = 512

class SLCPChat:
    def __init__(self, handle, port, image_port, whois_port):
        self.handle = handle
        self.port = port
        self.image_port = image_port
        self.whois_port = whois_port
        self.known_users = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_join(self):
        discovery.send_join(self.handle, self.port)

    def leave(self):
        discovery.broadcast(f"LEAVE {self.handle}")

    def request_who(self):
        discovery.broadcast("WHO")

    def send_message(self, recipient, message):
        if recipient not in self.known_users:
            return False, f"Unbekannter Benutzer: {recipient}"
        ip, port = self.known_users[recipient]
        self.sock.sendto(f"{self.handle}: {message}".encode(), (ip, port))
        return True, None

    def send_image(self, recipient, image_path):
        if recipient not in self.known_users:
            return False, f"Unbekannter Benutzer: {recipient}"
        ip, _ = self.known_users[recipient]
        image_handler.send_image(image_path, ip, self.image_port)
        return True, None

    def parse_knownusers(self, message):
        self.known_users.clear()
        parts = message.split()[1:]
        for i in range(0, len(parts), 3):
            try:
                handle, ip, port = parts[i], parts[i + 1], int(parts[i + 2])
                self.known_users[handle] = (ip, port)
            except (IndexError, ValueError):
                continue
            
        return self.known_users

    def listen_for_messages(self, on_message):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", self.port))
        while True:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            try:
                message = data.decode(errors="ignore")
            except UnicodeDecodeError:
                continue
            on_message(message, addr)

    def receive_images(self):
        image_handler.receive_image(None, self.image_port)