# app.py
import sys
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from gui.main_window import MainWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


def main():
    logging.info("Starting StegoLab application...")
    # Enable High DPI scaling for sharper UI
    try:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    logging.info("StegoLab application is now running!")
    logging.info("Application window has been maximized to full screen")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
