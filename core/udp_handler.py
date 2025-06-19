import socket
import threading

class UDPHandler:
    def __init__(self, listen_port, on_receive_callback):
        self.listen_port = listen_port
        self.on_receive_callback = on_receive_callback
        self.running = False

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def send_message(self, message, peers):
        for ip, port in peers:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(message.encode("utf-8"), (ip, port))

    def _receive_loop(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(("", self.listen_port))
            sock.settimeout(1.0)
            while self.running:
                try:
                    data, addr = sock.recvfrom(4096)
                    message = data.decode("utf-8")
                    self.on_receive_callback(message)
                except socket.timeout:
                    continue
