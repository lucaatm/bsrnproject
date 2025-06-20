import sys
import os

# Pfad zur Projektwurzel hinzufügen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt5 import QtWidgets
from chat_window import ChatWindow

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    fenster = ChatWindow(
        
        listen_port=4567,  # Port für user1
        peers=[("127.0.0.1", 4568)]  # Port für user2 
    )

    sys.exit(app.exec_())

