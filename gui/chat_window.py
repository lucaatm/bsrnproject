import sys
import os
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QListWidgetItem, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

class ChatWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        ui_datei = os.path.join(os.path.dirname(__file__), "guidesign_bsrn.ui")
        uic.loadUi(ui_datei, self)

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

        self.show()

    def nachricht_senden(self):
        text = self.lineEdit.text().strip()
        if text:
            self.add_chat_bubble(text, align="right", color="#ccffcc")  # Eigene Nachricht
            self.lineEdit.clear()

    def add_fremde_nachricht(self, text):
        self.add_chat_bubble(text, align="left", color="#eeeeee")  # System oder Fremder

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

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    fenster = ChatWindow()
    sys.exit(app.exec_())