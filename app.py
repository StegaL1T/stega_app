# app.py
import sys
import logging
from PyQt6.QtWidgets import QApplication
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
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    logging.info("StegoLab application is now running!")
    logging.info("Application window has been maximized to full screen")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
