## @file discovery.py
#  @brief Discovery-Modul für den BSRN-Chat
#  @details Verwaltung von Chat-Teilnehmern, Nachrichten und Bildempfang via IPC.

import time
from multiprocessing import current_process
from core.image_handler import save_and_open_image
import base64
import json

## @class Discovery
#  @brief Verarbeitet JOIN/LEAVE/WHO/MSG/IMG Kommandos von Teilnehmern.
#  @details Verwaltet Teilnehmerliste und leitet Nachrichten an CLI weiter.
class Discovery:
    ## @brief Konstruktor
    #  @param in_queue Queue für eingehende Nachrichten
    #  @param out_queue Queue für Ausgaben an CLI
    #  @param imagepath Pfad zum Speichern empfangener Bilder
    def __init__(self, in_queue, out_queue, imagepath):
        ## @var self.in_q
        #  @brief Eingangs-Queue vom Network-Prozess
        self.in_q = in_queue

        ## @var self.out_q
        #  @brief Ausgangs-Queue zur CLI
        self.out_q = out_queue

        ## @var self.participants
        #  @brief Bekannte Teilnehmer (handle → (IP, Port))
        self.participants = {}

        ## @var self.imagepath
        #  @brief Speicherort für empfangene Bilder
        self.imagepath = imagepath

        ## @var self._incoming_chunks
        #  @brief Zwischenspeicher für Bilddaten-Chunks
        self._incoming_chunks = {}

    ## @brief Hauptschleife zur Verarbeitung von Nachrichten
    def run(self):
        print(f"[{current_process().name}] Discovery gestartet")
        while True:
            if not self.in_q.empty():
                msg = self.in_q.get()

                if not isinstance(msg, list) or len(msg) < 2:
                    self.out_q.put("[Discovery] Ungültiges Format.")
                    continue

                command = msg[0]
                handle = msg[1]

                if command == "JOIN" and len(msg) >= 4:
                    handle, ip, port = msg[1], msg[2], msg[3]
                    already_known = handle in self.participants and self.participants[handle] == (ip, port)
                    self.participants[handle] = (ip, port)
                    if not already_known:
                        self.out_q.put(f"[System] {handle} ist dem Chat beigetreten.")

                elif command == "LEAVE":
                    if handle in self.participants:
                        del self.participants[handle]
                        self.out_q.put(f"[System] {handle} hat den Chat verlassen.")

                elif command == "WHO":
                    pass
                
                elif command == "MSG" and len(msg) >= 4:
                    sender, target, text = msg[1], msg[2], msg[3]
                
                    self.out_q.put(f"[{sender}] {text}")

                elif command == "IMG" and len(msg) >= 4:
                    sender, target, img_b64 = msg[1], msg[2], msg[3]
                    try:
                        image_data = base64.b64decode(img_b64)
                    except Exception as e:
                        self.out_q.put(f"[⚠️ Fehler beim Dekodieren des Bildes] {e}")
                        continue
                    path = save_and_open_image(sender, image_data, self.imagepath)
                    self.out_q.put(f"[{sender}] Bild erhalten: {path}")
                    self.out_q.put(f"[Hinweis] Bild gespeichert unter: {path}")

                elif command == "GET_QUEUE":
                    target = msg[2]
                    if target in self.participants:
                        ip, port = self.participants[target]
                        self.out_q.put(["FOUND", target, ip, port])
                    else:
                        self.out_q.put(["NOT_FOUND", target, None])

            time.sleep(0.05)



