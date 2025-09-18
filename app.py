# app.py
import sys
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
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
    # Enable HiDPI scaling and high-DPI pixmaps
    try:
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass

    app = QApplication(sys.argv)

    # Base font: 10–11 pt, bump by devicePixelRatio
    try:
        screen = app.primaryScreen()
        dpr = screen.devicePixelRatio() if screen else 1.0
        base_pt = 10
        bump = int(dpr)
        font = QFont()
        font.setPointSize(base_pt + bump)
        app.setFont(font)
    except Exception:
        pass
    w = MainWindow()
    w.show()
    logging.info("StegoLab application is now running!")
    logging.info("Application window has been maximized to full screen")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
