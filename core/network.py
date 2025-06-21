## @file network.py 
#  @brief Netzwerkmodul für den BSRN-Chat
#  @details Verwaltet UDP-Broadcasts, TCP-Bildempfang und leitet Befehle weiter zwischen CLI und Discovery.

import socket, select, json
import time
from multiprocessing import current_process
import uuid
import math
import threading

## @class Network
#  @brief Netzwerk-Komponente des BSRN-Chatprogramms.
#  @details Startet TCP-Server für Bilder, verarbeitet UDP-Broadcasts und synchronisiert Teilnehmerdaten.
class Network:
    def __init__(self, username, port, in_q, out_q, to_disc, from_disc, config):
        ## @var self.username
        #  @brief Benutzername dieses Clients
        self.username   = username

        ## @var self.port
        #  @brief Lokaler Port für UDP-Kommunikation
        self.port       = port

        ## @var self.in_q
        #  @brief Eingangs-Queue von CLI
        self.in_q       = in_q

        ## @var self.out_q
        #  @brief Ausgangs-Queue zur CLI
        self.out_q      = out_q

        ## @var self.to_disc
        #  @brief Nachrichten an Discovery-Prozess
        self.to_disc    = to_disc

        ## @var self.from_disc
        #  @brief Nachrichten vom Discovery-Prozess
        self.from_disc  = from_disc

        ## @var self.config
        #  @brief Konfigurationsdaten (z. B. imagepath, whoisport)
        self.config     = config

        # Lokale IP-Adresse beim Start ermitteln
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            self.local_ip = s.getsockname()[0]
        except:
            self.local_ip = "127.0.0.1"
        finally:
            s.close()

        ## @var self.udp
        #  @brief UDP-Socket für Broadcast und Empfang
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp.bind(('', self.port))
        self.udp.setblocking(False)

        # Zusätzlicher UDP-Socket für Broadcast-Empfang auf WHOIS-Port
        self.broadcast_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.broadcast_udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_udp.bind(('', self.config['whoisport']))
        self.broadcast_udp.setblocking(False)

    ## @brief Startet den TCP-Server zum Bildempfang (Port+100)
    def start_tcp_image_server(self):
        def handler():
            tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            tcp_sock.bind(('', self.port + 100))  # z. B. TCP auf Port+100
            tcp_sock.listen(5)
            print(f"[TCP-ImageServer] Lauscht auf Port {self.port + 100}")
            while True:
                conn, addr = tcp_sock.accept()
                print(f"[TCP-Server] Verbindung angenommen von {addr}")
                with conn:
                    data = b""
                    while True:
                        part = conn.recv(4096)
                        if not part:
                            break
                        data += part
                    if data:
                        try:
                            import json, base64
                            from core.image_handler import save_and_open_image
                            decoded = json.loads(data.decode())
                            sender, filename, img_b64 = decoded
                            image_data = base64.b64decode(img_b64)
                            path = save_and_open_image(sender, image_data, self.config['imagepath'])
                            self.out_q.put(f"[{sender}] Bild erhalten: {path}")
                        except Exception as e:
                            self.out_q.put(f"[Fehler beim Empfangen über TCP] {e}")
        threading.Thread(target=handler, daemon=True).start()


    def _send_unicast(self, cmd, ip, port):
        packet = json.dumps(cmd).encode()
        self.udp.sendto(packet, (ip, port))

    def _send_broadcast(self, cmd):
        packet = json.dumps(cmd).encode()
        self.udp.sendto(packet, ('<broadcast>', self.config['whoisport']))

    ## @brief Hauptschleife: Verarbeitet CLI-Befehle, sendet/empfängt über UDP/TCP.
    def run(self):
        print(f"[{current_process().name}] Network gestartet")
        self.start_tcp_image_server()
        while True:
            # 1) Lokale Queue von CLI
            try:
                cmd = self.in_q.get_nowait()
            except:
                cmd = None

            if cmd:
                if not (isinstance(cmd, list) and cmd and cmd[0] in ("IMG_HEADER", "IMG_CHUNK") and isinstance(cmd[-2], str) and isinstance(cmd[-1], int)):
                    self.to_disc.put(cmd)

                if isinstance(cmd, list) and cmd[0] == "KNOWNUSERS" and len(cmd) >= 3:
                    target_ip = cmd[-2]
                    target_port = cmd[-1]
                    net_cmd = cmd[:-2]
                    self._send_unicast(net_cmd, target_ip, target_port)
                    continue

                # Unicast für Nachrichten mit Ziel-IP/Port
                if isinstance(cmd, list) and cmd and cmd[0] in ("IMG", "IMG_CHUNK", "IMG_HEADER") and len(cmd) >= 5 and isinstance(cmd[-2], str) and isinstance(cmd[-1], int):
                    # ["IMG", sender, target, img_b64, ip, port]
                    ip = cmd[-2]
                    port = cmd[-1]
                    net_cmd = cmd[:-2]
                    
                    if cmd[0] == "IMG":
                        import base64
                        from core.image_handler import chunk_image_data
                        img_b64 = cmd[3]
                        chunks = chunk_image_data(img_b64, 512)
                        msg_id = uuid.uuid4().hex
                        for idx, chunk in enumerate(chunks):
                            self.in_q.put(["IMG_CHUNK", msg_id, idx, len(chunks), chunk, ip, port])
                        break  # exit after enqueuing all chunks once
                    else:
                        self._send_unicast(net_cmd, ip, port)
                elif isinstance(cmd, list) and cmd[0] == "IMG_CHUNK" and len(cmd) >= 7 and isinstance(cmd[-2], str) and isinstance(cmd[-1], int):
                    # Already handled above, but keep for clarity
                    ip = cmd[-2]
                    port = cmd[-1]
                    net_cmd = cmd[:-2]
                    self._send_unicast(net_cmd, ip, port)
                elif isinstance(cmd, list) and cmd[0] == "MSG" and len(cmd) >= 6 and isinstance(cmd[-2], str) and isinstance(cmd[-1], int):
                    ip = cmd[-2]
                    port = cmd[-1]
                    msg_cmd = cmd[:-2]
                    
                    self._send_unicast(msg_cmd, ip, port)
                    continue
                else:
                    packet = json.dumps(cmd).encode()
                    # Maximale Chunk-Größe für Bilddaten (512 Bytes pro Chunk)
                    max_size = 512
                    if len(packet) <= max_size:
                        # Direkt senden, für JOIN, LEAVE, WHO immer Broadcast
                        if isinstance(cmd, list) and cmd and cmd[0] in ("JOIN", "LEAVE", "WHO"):
                            self._send_broadcast(cmd)
                    else:
                        # Nachricht in Chunks aufteilen
                        msg_id = uuid.uuid4().hex
                        chunks = [packet[i:i+max_size] for i in range(0, len(packet), max_size)]
                        total = len(chunks)
                        for idx, chunk in enumerate(chunks):

                            wrapper = ["IMG_CHUNK", msg_id, idx, total, chunk.decode('latin1')]
                            data = json.dumps(wrapper).encode()

                            sent = False
                            while not sent:
                                try:
                                    self.udp.sendto(data, ('<broadcast>', self.config['whoisport']))
                                    sent = True
                                except OSError as e:
                                    if getattr(e, 'errno', None) == 55:
                                        time.sleep(0.05)
                                    else:
                                        raise
                            time.sleep(0.01)

            # 2) Remotes empfangen
            ready, _, _ = select.select([self.udp, self.broadcast_udp], [], [], 0.05)
            for sock in ready:
                data, addr = sock.recvfrom(4096)
                try:
                    msg = json.loads(data.decode())
                    sender_ip, sender_port = addr[0], addr[1]
                    if isinstance(msg, list) and msg and msg[0] == "WHO":
                        if not (sender_ip == "127.0.0.1" or (self.username == msg[1] and self.port == sender_port)):
                            user_string = f"{self.username} {self.local_ip} {self.port}"
                            known_msg = ["KNOWNUSERS", user_string]
                            pkt = json.dumps(known_msg).encode()
                            self.udp.sendto(pkt, (sender_ip, sender_port))
                        continue
                    if isinstance(msg, list) and msg[0] == "MSG" and len(msg) >= 3:
                        if msg[1] == self.username:
                            continue
                        # Autoreply-Logik bei Inaktivität
                        if self.config.get("inactive", False):
                            autoreply = self.config.get("autoreply", "")
                            sender = msg[1]
                            self.to_disc.put(["GET_QUEUE", self.username, sender])
                            found = None
                            while True:
                                try:
                                    resp = self.from_disc.get(timeout=1)
                                    if isinstance(resp, list) and resp and resp[0] == "FOUND" and resp[1] == sender:
                                        found = resp
                                        break
                                    elif isinstance(resp, list) and resp and resp[0] == "NOT_FOUND" and resp[1] == sender:
                                        break
                                except:
                                    break

                            if found:
                                ip = found[2]
                                port = found[3]
                                reply_cmd = ["MSG", self.username, sender, autoreply, ip, port]
                                self._send_unicast(reply_cmd, ip, port)
                    
                    if isinstance(msg, list) and msg and msg[0] == "KNOWNUSERS" and len(msg) >= 2:
                        user_entries = msg[1].split(", ")
                        if not hasattr(self, "participants"):
                            self.participants = {}
                        for entry in user_entries:
                            parts = entry.strip().split(" ")
                            if len(parts) == 3:
                                h, ip, p = parts[0], parts[1], int(parts[2])
                                if h not in self.participants:
                                    self.participants[h] = (ip, p)
                        final_list = [
                            f"{h} {ip} {port}" for h, (ip, port) in self.participants.items()
                        ]
                        output = "KNOWNUSERS " + ", ".join(final_list)
                        self.out_q.put(output)
                        for h, (ip, port) in self.participants.items():
                            self.to_disc.put(["JOIN", h, ip, port])
                        continue

                    if len(msg) >= 4 and msg[0] == "JOIN":
                        handle = msg[1]
                        ip     = msg[2]
                        port   = int(msg[3])
                        if handle == self.username and port == self.port:
                            continue
                        self.to_disc.put(["JOIN", handle, ip, port])
                    else:

                        self.to_disc.put(msg)
                except json.JSONDecodeError:
                    continue

            # 3) Antworten von Discovery an CLI shutteln
            try:
                resp = self.from_disc.get_nowait()
                self.out_q.put(resp)
            except:
                pass