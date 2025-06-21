## @file gui.py
#  @brief Tkinter-Oberfläche für den BSRN-Chat
#  @details Parallel-Frontend zur CLI. Unterstützt MSG, IMG, WHO.
#           Keine Logikänderungen – nur Benutzerschnittstelle.
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import filedialog, messagebox
import threading
from multiprocessing import current_process
import os
import socket
import json

## @brief Extrahiert den Namen aus einer Systemzeile.
#  @param msg_line Die Zeile, z. B. "[System] Alice ...".
#  @return Der extrahierte Benutzername oder ein leerer String.
def extract_username(msg_line: str) -> str:
    parts = msg_line.split()
    return parts[1] if len(parts) > 1 else ""

## @class GUI
#  @brief Tkinter-basierte grafische Oberfläche für den Chat.
#  @details Stellt eine Benutzeroberfläche zur Verfügung, mit der Nachrichten
#           gesendet und empfangen werden können. Unterstützt auch Bildversand
#           per TCP und WHO-Anfragen.
class GUI:
    def __init__(self, in_q, out_q, username, to_disc=None, from_disc=None):
        self.in_q = in_q        
        self.out_q = out_q      
        self.username = username
        self.to_disc = to_disc      
        self.from_disc = from_disc  
        self.known_users = set()

        self.root = tk.Tk()
        self.root.title(f"BSRN Chat – GUI ({self.username})")

        # Name oben als Label
        tk.Label(self.root, text=f"Du bist: {self.username}", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=5, sticky="w", padx=10, pady=(5,0))

        # Chat-Verlauf
        self.text_area = ScrolledText(self.root, state="disabled", width=75, height=25, wrap=tk.WORD)
        self.text_area.grid(row=1, column=0, columnspan=5, padx=10, pady=10)

        # Empfänger-Label und Dropdown nebeneinander
        tk.Label(self.root, text="Empfänger").grid(row=2, column=0, sticky="w", padx=(10, 0))
        self.recipient_var = tk.StringVar()
        self.recipient_menu = tk.OptionMenu(self.root, self.recipient_var, ())
        self.recipient_menu.config(width=20)
        self.recipient_menu.grid(row=2, column=1, sticky="w", padx=(0, 10))

        # Texteingabe
        self.entry = tk.Entry(self.root, width=40)
        self.entry.grid(row=2, column=2, padx=(0, 10), pady=(0, 10))

        # Buttons
        tk.Button(self.root, text="Text senden", command=self.send_msg).grid(row=2, column=3, pady=(0, 10))
        tk.Button(self.root, text="Bild senden", command=self.send_img).grid(row=2, column=4, pady=(0, 10))
        tk.Button(self.root, text="WHO", command=self.send_who).grid(row=3, column=4, sticky="e", pady=(0, 10))
        tk.Button(self.root, text="Verlassen", command=self.leave_chat, fg="red").grid(row=3, column=0, sticky="w", padx=10, pady=(0, 10))

        self.recipient_menu.config(state="disabled")
        self.entry.config(state="disabled")

        threading.Thread(target=self.listen_for_messages, daemon=True).start()

        self.send_who()

        self.root.protocol("WM_DELETE_WINDOW", self.leave_chat)

        print(f"[{current_process().name}] GUI gestartet")
        self.root.mainloop()

    ## @brief Sendet eine Textnachricht an den ausgewählten Empfänger.
    #  @details Holt sich IP/Port aus der Discovery-Queue und sendet per UDP.
    def send_msg(self):
        target = self.recipient_var.get().strip()
        text = self.entry.get().strip()
        if not target:
            messagebox.showwarning("Kein Empfänger", "Bitte einen Empfänger auswählen.")
            return
        if not text:
            return
        print(f"Sende MSG an {target}: {text}")

        self.to_disc.put(["GET_QUEUE", self.username, target])
        found = None
        while True:
            resp = self.from_disc.get()
            if isinstance(resp, list) and resp and resp[0] == "FOUND" and resp[1] == target:
                found = resp
                break
            elif isinstance(resp, list) and resp and resp[0] == "NOT_FOUND" and resp[1] == target:
                found = None
                break

        if not found:
            messagebox.showerror("Fehler", f"Nutzer '{target}' nicht gefunden.")
            return

        ip = found[2]
        port = found[3]
        self.in_q.put(["MSG", self.username, target, text, ip, port])
        self.append_chat_line(f"[Du → {target}]: {text}")
        self.entry.delete(0, tk.END)

    ## @brief Sendet ein Bild an den ausgewählten Empfänger.
    #  @details Wandelt das Bild in base64 um und sendet es per TCP an den Zielport + 100.
    def send_img(self):
        target = self.recipient_var.get().strip()
        if not target:
            messagebox.showwarning("Kein Empfänger", "Bitte einen Empfänger auswählen.")
            return
        path = filedialog.askopenfilename(title="Bild auswählen",
                                          filetypes=[("Bilddateien", "*.png *.jpg *.jpeg *.gif *.bmp"), ("Alle", "*.*")])
        if not path or not os.path.isfile(path):
            return
        from core.image_handler import load_image_as_bytes
        import base64
        img_bytes = load_image_as_bytes(path)
        if img_bytes is None:
            messagebox.showerror("Fehler", "Bild konnte nicht geladen werden.")
            return
        img_b64 = base64.b64encode(img_bytes).decode()
        filename = os.path.basename(path)
        print(f"Sende IMG an {target}: {path}")

        self.to_disc.put(["GET_QUEUE", self.username, target])
        found = None
        while True:
            resp = self.from_disc.get()
            if isinstance(resp, list) and resp and resp[0] == "FOUND" and resp[1] == target:
                found = resp
                break
            elif isinstance(resp, list) and resp and resp[0] == "NOT_FOUND" and resp[1] == target:
                found = None
                break

        if not found:
            messagebox.showerror("Fehler", f"Nutzer '{target}' nicht gefunden.")
            return

        ip = found[2]
        port = found[3]
        print(f"[DEBUG] Sende Bild an IP: {ip}, Port: {port + 100}, Empfänger: {target}")

        payload = json.dumps([self.username, filename, img_b64]).encode()
        try:
            with socket.create_connection((ip, port + 100), timeout=5) as sock:
                print(f"[TCP-Client] Sende an {ip}:{port + 100}")
                sock.sendall(payload)
                print(f"[TCP] Bild erfolgreich an {target} gesendet.")
                messagebox.showinfo("Bild gesendet", f"Bild erfolgreich an {target} gesendet.")
        except Exception as e:
            print(f"[TCP Fehler] Bildversand an {target} fehlgeschlagen: {e}")
            messagebox.showerror("Fehler", f"Bildversand an {target} fehlgeschlagen:\n{e}")

    ## @brief Fordert mit WHO die aktuelle Teilnehmerliste an.
    def send_who(self):
        print("Sende WHO-Befehl")
        self.in_q.put(["WHO", self.username])

    ## @brief Wartet auf Nachrichten aus der Queue und verarbeitet sie.
    def listen_for_messages(self):
        while True:
            if not self.out_q.empty():
                line = self.out_q.get()
                print("Empfangen:", repr(line))  # Debug-Ausgabe
                # Nur normale Nachrichten anzeigen, keine WHO/KNOWNUSERS
                if not (line.startswith("[WHO]") or line.startswith("KNOWNUSERS ")):
                    self.append_chat_line(line)
                self.update_users_from_line(line)

    ## @brief Fügt eine neue Zeile zum Chat-Verlauf hinzu.
    #  @param text_line Die Textzeile, die angezeigt werden soll.
    def append_chat_line(self, text_line: str):
        self.text_area.config(state="normal")
        self.text_area.insert(tk.END, text_line + "\n")
        self.text_area.config(state="disabled")
        self.text_area.see(tk.END)

    ## @brief Aktualisiert bekannte Nutzer aus einer empfangenen Zeile.
    #  @param line Die eingehende Nachricht (z. B. WHO oder Systemmeldung).
    def update_users_from_line(self, line: str):
        if line.startswith("[System]") and "ist dem Chat beigetreten" in line:
            self.known_users.add(extract_username(line))
            print("User beigetreten:", self.known_users)
            self.refresh_recipient_menu()
        elif line.startswith("[System]") and "hat den Chat verlassen" in line:
            self.known_users.discard(extract_username(line))
            print("User verlassen:", self.known_users)
            self.refresh_recipient_menu()
        elif line.startswith("[WHO]"):
            parts = line.split("]", 1)
            if len(parts) == 2:
                users = [u.strip() for u in parts[1].split(",") if u.strip()]
                print("WHO-User:", users)
                self.known_users = set(users)
                self.refresh_recipient_menu()
        elif line.startswith("KNOWNUSERS "):
            users_str = line[len("KNOWNUSERS "):]
            users = [u.split(" ")[0] for u in users_str.split(",") if u.strip()]
            print("KNOWNUSERS-User:", users)
            self.known_users = set(users)
            self.refresh_recipient_menu()

    ## @brief Aktualisiert das Empfänger-Dropdown-Menü basierend auf bekannten Nutzern.
    def refresh_recipient_menu(self):
        menu = self.recipient_menu["menu"]
        menu.delete(0, "end")
        sorted_users = sorted(self.known_users) 
        for user in sorted_users:
            menu.add_command(label=user, command=lambda u=user: self.recipient_var.set(u))
        if sorted_users:
            self.recipient_var.set(sorted_users[0])
            self.recipient_menu.config(state="normal")
            self.entry.config(state="normal")
        else:
            self.recipient_var.set("")
            self.recipient_menu.config(state="disabled")
            self.entry.config(state="disabled")
            messagebox.showinfo("Keine Nutzer", "Es sind keine anderen Nutzer im Chat.")

    ## @brief Beendet den Chat sauber und schließt das GUI-Fenster.
    def leave_chat(self):
        self.in_q.put(["LEAVE", self.username])
        self.root.destroy()
