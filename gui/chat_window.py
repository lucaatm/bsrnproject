import sys
import os
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QListWidgetItem, QLabel, QWidget, QVBoxLayout, QInputDialog, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStatusTipEvent
import subprocess
import platform

# Pfad zur Projektwurzel ergänzen, damit "core" gefunden wird
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.udp_handler import UDPHandler  # Für Textnachrichten
from core.image_handler import send_image, IMAGEPATH  # Für Bildversand

class ChatWindow(QtWidgets.QMainWindow):
    def __init__(self, listen_port, peers):
        super().__init__()

        # Benutzername beim Start abfragen
        name, ok = QInputDialog.getText(self, "Benutzername", "Wie heißt du?")
        if ok and name.strip():
            self.username = name.strip()
        else:
            self.username = "Unbekannt"

        self.listen_port = listen_port
        self.peers = peers

        # Lade die .ui-Datei
        ui_datei = os.path.join(os.path.dirname(__file__), "guidesign_bsrn.ui")
        uic.loadUi(ui_datei, self)

        self.setWindowTitle(f"BSRN Chat – {self.username}")

        # Button-Verbindungen
        self.pushButton.clicked.connect(self.send_message)
        self.pushButtonImage.clicked.connect(self.send_image_dialog)
        self.lineEdit.returnPressed.connect(self.send_message)

        # UDP-Empfänger starten
        self.udp = UDPHandler(self.listen_port, self.receive_message)
        self.udp.start()

        self.show()

    ## Text senden
    def send_message(self):
        text = self.lineEdit.text().strip()
        if text:
            self.add_chat_bubble(f"{self.username}: {text}", align="right", color="#ccffcc")
            self.lineEdit.clear()
            self.udp.send_message(f"{self.username}: {text}", self.peers)

    ## Eingehende Nachricht anzeigen
    def receive_message(self, text):
        if text.startswith("IMG "):
            try:
                _, image_name, image_size = text.split()
                QtWidgets.QApplication.instance().postEvent(
                    self, QStatusTipEvent(f"[IMAGE_RECEIVED]::{image_name}")
                )
            except Exception:
                pass  
        elif text.strip() and not text.startswith("[IMAGE_RECEIVED]"):
            QtWidgets.QApplication.instance().postEvent(self, QStatusTipEvent(text))

    def event(self, event):
        if isinstance(event, QStatusTipEvent):
            tip = event.tip()
            if tip.startswith("[IMAGE_RECEIVED]::"):
                image_name = tip.split("::", 1)[1]
                self.add_image_bubble(image_name)
            else:
                self.add_foreign_message(tip)
            return True
        return super().event(event)

    def add_foreign_message(self, text):
        self.add_chat_bubble(text, align="left", color="#eeeeee")

    def add_chat_bubble(self, text, align="left", color="#e6f2ff"):
        bubble_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(
            f"""
            QLabel {{
                border: 1px solid #99ff99;
                border-radius: 12px;
                padding: 8px;
                background-color: {color};
                max-width: 400px;
            }}
            """
        )
        label.setAlignment(Qt.AlignLeft if align == "left" else Qt.AlignRight)
        layout.addWidget(label, alignment=Qt.AlignLeft if align == "left" else Qt.AlignRight)

        bubble_widget.setLayout(layout)

        item = QListWidgetItem()
        item.setSizeHint(bubble_widget.sizeHint())
        self.listWidget.addItem(item)
        self.listWidget.setItemWidget(item, bubble_widget)
        self.listWidget.scrollToBottom()

    def add_image_bubble(self, image_name):
        image_path = os.path.abspath(os.path.join(IMAGEPATH, image_name))
        if not os.path.exists(image_path):
            print(f"[WARN] Bild nicht gefunden: {image_path}")
            return  

        bubble_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        label = QLabel(f"[Bild empfangen: {image_name}]")
        label.setWordWrap(True)
        label.setStyleSheet(
            """
            QLabel {
                border: 1px solid #99ff99;
                border-radius: 12px;
                padding: 8px;
                background-color: #eeeeee;
                max-width: 400px;
            }
            """
        )
        label.setAlignment(Qt.AlignLeft)
        layout.addWidget(label, alignment=Qt.AlignLeft)

        button = QtWidgets.QPushButton("Bild öffnen")
        button.setStyleSheet("padding: 4px; font-size: 12px;")
        button.clicked.connect(lambda: self.open_image(image_path))
        layout.addWidget(button, alignment=Qt.AlignLeft)

        bubble_widget.setLayout(layout)

        item = QListWidgetItem()
        item.setSizeHint(bubble_widget.sizeHint())
        self.listWidget.addItem(item)
        self.listWidget.setItemWidget(item, bubble_widget)
        self.listWidget.scrollToBottom()

    def open_image(self, image_path):
        try:
            if platform.system() == "Windows":
                os.startfile(image_path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", image_path])
            else:
                subprocess.run(["xdg-open", image_path])
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Fehler", f"Bild konnte nicht geöffnet werden:\n{e}")

   
    def send_image_dialog(self):
        dateipfad, _ = QFileDialog.getOpenFileName(self, "Bild auswählen", "", "Bilder (*.png *.jpg *.jpeg *.bmp)")
        if dateipfad:
            for ip, port in self.peers:
                send_image(dateipfad, ip, port)
            self.add_chat_bubble(f"[Bild versendet: {os.path.basename(dateipfad)}]", align="right", color="#ccffcc")

# Nur zum Testen direkt
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    fenster = ChatWindow(listen_port=4567, peers=[("127.0.0.1", 4568)])
    sys.exit(app.exec_())
