import sys
import os

# Pfad zur Projektwurzel hinzufügen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt5 import QtWidgets
from chat_window import ChatWindow

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    fenster = ChatWindow(
        username="Sumaya",
        listen_port=4568,  # Sumayas eigener Port
        peers=[("127.0.0.1", 4567)]  # Sohals Port
    )

    sys.exit(app.exec_())

