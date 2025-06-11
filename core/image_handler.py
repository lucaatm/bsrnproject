import socket
import os
import platform
import subprocess

BUFFER_SIZE = 512


def send_image(image_path, target_ip, target_port):
    if not os.path.isfile(image_path):
        print(f"[Error] File not found: {image_path}")
        return

    with open(image_path, "rb") as f:
        image_data = f.read()

    image_size = len(image_data)
    image_name = os.path.basename(image_path)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    
    header_msg = f"IMG {image_name} {image_size}"
    sock.sendto(header_msg.encode("utf-8"), (target_ip, target_port))

    
    for i in range(0, image_size, BUFFER_SIZE):
        chunk = image_data[i:i + BUFFER_SIZE]
        sock.sendto(chunk, (target_ip, target_port))

    sock.close()
    print(f"[Bild gesendet] {image_name} ({image_size} Bytes)")


def receive_image(callback=None, port=5002, save_dir="./received_images"):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", port))
    print(f"[Image-Handler] Listening on port: {port}...")

    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            message = data.decode("utf-8", errors="ignore")

            if message.startswith("IMG"):
                _, image_name, image_size = message.split()
                image_size = int(image_size)
                image_path = os.path.join(save_dir, image_name)

                with open(image_path, "wb") as f:
                    bytes_received = 0
                    while bytes_received < image_size:
                        chunk, _ = sock.recvfrom(BUFFER_SIZE)
                        f.write(chunk)
                        bytes_received += len(chunk)

                print(f"[Bild empfangen] Gespeichert als {image_path}")
                if callback:
                    callback(f"[Bild gespeichert unter: {image_path}]")

                
                try:
                    if platform.system() == "Windows":
                        os.startfile(image_path)
                    elif platform.system() == "Darwin":
                        subprocess.run(["open", image_path])
                    else:
                        subprocess.run(["xdg-open", image_path])
                except Exception as e:
                    print(f"[Bildanzeige fehlgeschlagen]: {e}")

        except Exception as e:
            print(f"[Fehler beim Empfang]: {e}")
