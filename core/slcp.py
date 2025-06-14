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

    ## SLCPChat is used by cli_chat.py to handle the chat functionality and is used in cli_chat.py in input_loop

    ## Sends a JOIN message to the discovery service
    def send_join(self):
        discovery.send_join(self.handle, self.port)

    ## Sends a LEAVE message to the discovery service
    def leave(self):
        discovery.broadcast(f"LEAVE {self.handle}")

    ## Sends a broadcast WHO request to the discovery service to get a list of known users
    def request_who(self):
        discovery.broadcast("WHO")

    ## Sends a message to a specific user
    def send_message(self, recipient, message):
        if recipient not in self.known_users:
            return False, f"Unknown user: {recipient}"
        ip, port = self.known_users[recipient]
        self.sock.sendto(f"{self.handle}: {message}".encode(), (ip, port))
        return True, None

    ## Sends an image to a specific user
    def send_image(self, recipient, image_path):
        if recipient not in self.known_users:
            return False, f"Unknown user: {recipient}"
        ip, _ = self.known_users[recipient]
        image_handler.send_image(image_path, ip, self.image_port)
        return True, None

    ## Parses the KNOWNUSERS message to update the list of known users
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

    ## Listens for incoming messages and calls the provided callback function on_message
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

    ## Starts listening for incoming images on the specified image port
    def receive_images(self):
        image_handler.receive_image(self.image_port)