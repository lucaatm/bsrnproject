import os
import sys

# Pfad zur Projektwurzel hinzufügen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QListWidgetItem, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QMetaObject, Q_ARG, pyqtSlot
from core.slcp import SLCPChat


class ChatWindow(QtWidgets.QMainWindow):
    def __init__(self, username, listen_port, peers):
        super().__init__()

        # Lade das UI-Layout
        ui_datei = os.path.join(os.path.dirname(__file__), "gui_design.ui")
        uic.loadUi(ui_datei, self)

        # SLCP-Chat starten
        self.chat = SLCPChat(username=username, listen_port=listen_port, peers=peers)
        self.chat.register_callback(self.on_message_received)
        self.chat.start()

        # Kontakte hinzufügen
        self.chatList.addItems(["Sohal", "Sumaya", "Luca", "Ani"])
        self.pushButton.clicked.connect(self.nachricht_senden)
        self.lineEdit.returnPressed.connect(self.nachricht_senden)

        # Begrüßung anzeigen
        self.add_fremde_nachricht(f"Willkommen, {username}!")
        self.show()

    def nachricht_senden(self):
        text = self.lineEdit.text().strip()
        if text:
            self.add_chat_bubble(text, align="right", color="#ccffcc")
            self.chat.send_message(text)
            self.lineEdit.clear()

    def on_message_received(self, sender, message):
        # Thread-sicheres Update im GUI-Thread
        def update_ui():
            self.add_chat_bubble(f"{sender}: {message}", align="left", color="#eeeeee")

        QMetaObject.invokeMethod(
            self,
            "invoke_ui_update",
            Qt.QueuedConnection,
            Q_ARG(object, update_ui)
        )

    @pyqtSlot(object)
    def invoke_ui_update(self, func):
        func()

    def add_fremde_nachricht(self, text):
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

    def closeEvent(self, event):
        self.chat.stop()
        event.accept()

