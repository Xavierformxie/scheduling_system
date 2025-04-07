import sys
from PyQt6.QtWidgets import QApplication 
from ui.main_window import MainWindow 
import qdarkstyle

if __name__ =="__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())