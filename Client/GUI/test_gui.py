import sys
from PySide6.QtWidgets import QApplication
from Client.GUI.main_gui import MainWindow

app = QApplication(sys.argv)
window = MainWindow(app)
window.show()
sys.exit(app.exec())