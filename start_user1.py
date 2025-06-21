## @file start_user1.py
# @brief Programmstart für die Chat-Anwendung mit PyQt5.
# @details Fügt den Projektpfad zur Module-Suche hinzu, startet die QApplication
#          und öffnet ein ChatWindow mit vordefinierten Parametern.

import sys
import os

# @brief Pfad zur Projektwurzel ergänzen
#  Damit Module aus dem `core`-Verzeichnis gefunden werden.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt5 import QtWidgets
from chat_window import ChatWindow

# @brief Direktaufruf: Initialisiert das Qt-Framework und das Chat-Fenster.
#  Dieser Block wird nur ausgeführt, wenn das Skript direkt gestartet wird.
if __name__ == "__main__":
    # @brief Erzeugt die Qt-Anwendung
    app = QtWidgets.QApplication(sys.argv)

    # @brief Öffnet das Chat-Fenster für zwei Testnutzer
    fenster = ChatWindow(
        listen_port=4567,      # UDP-Port für Nutzer 1
        peers=[("127.0.0.1", 4568)]  # UDP-Port für Nutzer 2
    )

    # @brief Startet die Qt-Event-Schleife und beendet das Skript bei Schließen des Fensters
    sys.exit(app.exec_())
