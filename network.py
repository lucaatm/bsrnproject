import socket
import threading

PORT = 5001
BUFFER_SIZE = 512

def receive_messages(callback, port=PORT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', port))
    print(f"[Netzwerk] Lausche auf UDP-Port {port}")
    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            message = data.decode('utf-8', errors='ignore')
            print(f"[Empfangen] {addr}: {message}")

            if message.startswith("IMG "):
                try:
                    _, handle, size_str = message.split()
                    size = int(size_str)
                    print(f"[Bild] Empfange Bild ({size} Bytes) von {handle}...")
                    image_data, _ = sock.recvfrom(size)
                    with open(f"received_{handle}.jpg", "wb") as f:
                        f.write(image_data)
                    print(f"[Bild] Bild gespeichert als received_{handle}.jpg")
                    callback(f"[Bild empfangen von {handle}]")
                except Exception as img_err:
                    print(f"[Bildfehler] {img_err}")
            else:
                callback(f"{addr[0]}: {message}")

        except Exception as e:
                print(f"[Fehler] {e}")
                break

def send_message(target_ip, target_port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message.encode('utf-8'), (target_ip, target_port))
    sock.close()
