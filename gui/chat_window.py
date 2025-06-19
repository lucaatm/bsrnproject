import sys
import os
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QListWidgetItem, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStatusTipEvent  # ✅ Richtiger Import

# ✅ Pfad zur Projektwurzel ergänzen, damit "core" gefunden wird
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.udp_handler import UDPHandler  # UDP-Modul einbinden

class ChatWindow(QtWidgets.QMainWindow):
    def __init__(self, username, listen_port, peers):
        super().__init__()

        # Übergabeparameter speichern
        self.username = username
        self.listen_port = listen_port
        self.peers = peers

        # Lade die .ui-Datei, die mit Qt Designer erstellt wurde
        ui_datei = os.path.join(os.path.dirname(__file__), "guidesign_bsrn.ui")
        uic.loadUi(ui_datei, self)

        # Setze das Fenster-Title basierend auf dem Username
        self.setWindowTitle(f"BSRN Chat – {self.username}")

        # Beispielhafte Namen zur Chatliste hinzufügen
        self.chatList.addItems([
            "Support",
            "Anna",
            "Ben",
            "Lisa",
            "Projektgruppe",
            "Admin"
        ])

        # Verbindung zum Senden-Button
        self.pushButton.clicked.connect(self.nachricht_senden)

        # Verbindung zur Enter-Taste im Eingabefeld
        self.lineEdit.returnPressed.connect(self.nachricht_senden)

        # Begrüßung
        self.add_fremde_nachricht("Willkommen im Chat!")
        self.add_fremde_nachricht("Support: Wie kann ich helfen?")

        # UDP-Empfang starten (läuft im Hintergrund)
        self.udp = UDPHandler(self.listen_port, self.nachricht_empfangen)
        self.udp.start()

        # GUI anzeigen
        self.show()

    # ✅ Methode zum Senden einer Nachricht – war vorher vermutlich gelöscht
    def nachricht_senden(self):
        text = self.lineEdit.text().strip()
        if text:
            self.add_chat_bubble(f"{self.username}: {text}", align="right", color="#ccffcc")
            self.lineEdit.clear()
            self.udp.send_message(f"{self.username}: {text}", self.peers)

    # Methode, die von UDP-Handler aufgerufen wird
    def nachricht_empfangen(self, text):
        QtWidgets.QApplication.instance().postEvent(self, QStatusTipEvent(text))  # ✅ korrekt aufgerufen

    # ✅ Event-Handler für empfangene UDP-Nachrichten
    def event(self, event):
        if isinstance(event, QStatusTipEvent):
            self.add_fremde_nachricht(event.tip())
            return True
        return super().event(event)

    # Methode zum Hinzufügen einer fremden Nachricht
    def add_fremde_nachricht(self, text):
        self.add_chat_bubble(text, align="left", color="#eeeeee")

    # Methode zum Erstellen und Anzeigen einer Chat-Bubble
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

# Nur zu Testzwecken – im echten Start per start_sohal.py oder start_sumaya.py
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    fenster = ChatWindow(username="Sohal", listen_port=4567, peers=[("127.0.0.1", 4568)])
    sys.exit(app.exec_())
