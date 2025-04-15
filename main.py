import socket
import threading

# Server Code
def handle_client(client_socket, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            print(f"[{addr}] {message}")
            client_socket.send("Message received".encode('utf-8'))
        except ConnectionResetError:
            break
    print(f"[DISCONNECT] {addr} disconnected.")
    client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 5555))
    server.listen()
    print("[SERVER STARTED] Waiting for connections...")
    while True:
        client_socket, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

# Client Code
def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", 5555))
    print("[CONNECTED TO SERVER]")
    while True:
        message = input("You: ")
        if message.lower() == "exit":
            break
        client.send(message.encode('utf-8'))
        response = client.recv(1024).decode('utf-8')
        print(f"Server: {response}")
    client.close()

# Main
if __name__ == "__main__":
    mode = input("Start as server or client? (server/client): ").strip().lower()
    if mode == "server":
        start_server()
    elif mode == "client":
        start_client()
    else:
        print("Invalid mode. Please choose 'server' or 'client'.")