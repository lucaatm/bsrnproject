import sys
import os
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QListWidgetItem, QLabel, QWidget, QVBoxLayout, QInputDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStatusTipEvent

# Pfad zur Projektwurzel ergänzen, damit "core" gefunden wird
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.udp_handler import UDPHandler  # UDP-Modul einbinden

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

        # Lade die .ui-Datei, die mit Qt Designer erstellt wurde
        ui_datei = os.path.join(os.path.dirname(__file__), "guidesign_bsrn.ui")
        uic.loadUi(ui_datei, self)

        # Setze das Fenster-Title basierend auf dem Username
        self.setWindowTitle(f"BSRN Chat – {self.username}")

        # Verbindung zum Senden-Button
        self.pushButton.clicked.connect(self.send_message)

        # Verbindung zur Enter-Taste im Eingabefeld
        self.lineEdit.returnPressed.connect(self.send_message)

        # UDP-Empfang starten (läuft im Hintergrund)
        self.udp = UDPHandler(self.listen_port, self.receive_message)
        self.udp.start()

        # GUI anzeigen
        self.show()

    ## @brief Sendet eine eingegebene Nachricht über UDP und zeigt sie lokal an.
    def send_message(self):
        text = self.lineEdit.text().strip()
        if text:
            self.add_chat_bubble(f"{self.username}: {text}", align="right", color="#ccffcc")
            self.lineEdit.clear()
            self.udp.send_message(f"{self.username}: {text}", self.peers)

    ## @brief Wird vom UDP-Thread aufgerufen – leitet empfangene Nachrichten an das GUI weiter.
    def receive_message(self, text):
        QtWidgets.QApplication.instance().postEvent(self, QStatusTipEvent(text))

    ## @brief Event-Handler für StatusTipEvent (UDP-Textnachrichten)
    def event(self, event):
        if isinstance(event, QStatusTipEvent):
            self.add_foreign_message(event.tip())
            return True
        return super().event(event)

    ## @brief Zeigt eine empfangene Nachricht im Chatverlauf an.
    def add_foreign_message(self, text):
        self.add_chat_bubble(text, align="left", color="#eeeeee")

    ## @brief Erstellt und zeigt eine neue Chat-Bubble (Nachricht)
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

# Testzwecke – im echten Start per start_sohal.py oder start_sumaya.py
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    fenster = ChatWindow(listen_port=4567, peers=[("127.0.0.1", 4568)])
    sys.exit(app.exec_())
