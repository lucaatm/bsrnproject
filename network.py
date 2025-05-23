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
            message = data.decode('utf-8')
            print(f"[Empfangen] {addr}: {message}")
            callback(f"{addr[0]}: {message}")
           
        
        except Exception as e:
            print(f"[Fehler] {e}")
            break

def send_message(target_ip, target_port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message.encode('utf-8'), (target_ip, target_port))
    sock.close()
