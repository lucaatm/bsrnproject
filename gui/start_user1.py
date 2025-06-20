import sys
import os

# Pfad zur Projektwurzel hinzufügen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt5 import QtWidgets
from chat_window import ChatWindow

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    fenster = ChatWindow(
        
        listen_port=4567,  # Sohals eigener Port
        peers=[("127.0.0.1", 4568)]  # Sumayas Port
    )

    sys.exit(app.exec_())

