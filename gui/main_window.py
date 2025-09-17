# gui/main_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QApplication)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QLinearGradient, QBrush, QPen


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steganography Tool")
        self.setMinimumSize(1000, 700)

        # Cybersecurity theme: fonts & background
        # Colors:
        #   Background: #0e1625 (very dark navy)
        #   Headings/accents: #49299a (purple)
        #   Highlights/buttons: #45edf2 (aqua/cyan)
        #   Light contrast: #e8e8fc (very light lavender)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0e1625;
                font-family: 'Syne', 'Segoe UI', 'Arial', sans-serif;
                color: #e8e8fc;
            }
            QWidget {
                font-family: 'Syne', 'Segoe UI', 'Arial', sans-serif;
                color: #e8e8fc;
            }
        """)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout with gradient background
        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setSpacing(40)
        main_layout.setContentsMargins(50, 50, 50, 50)

        # Title section
        self.create_title_section(main_layout)

        # Cards section
        self.create_cards_section(main_layout)

        # Make the window fullscreen
        self.showMaximized()

    def create_title_section(self, layout):
        """Create the title and subtitle section"""
        title_label = QLabel("Steganography Tool")
        title_font = QFont()
        title_font.setPointSize(36)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #49299a; margin-bottom: 10px;")

        subtitle_label = QLabel(
            "Hide and detect hidden information in digital media.")
        subtitle_font = QFont()
        subtitle_font.setPointSize(16)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: rgba(232,232,252,0.8); margin-bottom: 20px;")

        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)

    def create_cards_section(self, layout):
        """Create the three main cards"""
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(30)
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Steganography Encoding card
        encode_card = self.create_card(
            "Steganography - Encoding",
            "Hide secret messages within images, audio, or other media files using LSB techniques.",
            "Start Encoding →",
            "#45edf2",
            self.create_padlock_icon()
        )

        # Steganography Decoding card
        decode_card = self.create_card(
            "Steganography - Decoding",
            "Extract hidden messages from steganographic media files using LSB techniques.",
            "Start Decoding →",
            "#45edf2",
            self.create_unlock_icon()
        )

        # Steganalysis card
        analysis_card = self.create_card(
            "Steganalysis",
            "Detect and analyze hidden information in digital media files.",
            "Start Analyzing →",
            "#45edf2",
            self.create_magnifying_glass_icon()
        )

        cards_layout.addWidget(encode_card)
        cards_layout.addWidget(decode_card)
        cards_layout.addWidget(analysis_card)

        layout.addLayout(cards_layout)

    def create_card(self, title, description, button_text, button_color, icon):
        """Create a card widget"""
        card = QFrame()
        card.setFixedSize(400, 350)
        card.setStyleSheet("""
            QFrame {
                background-color: #0e1625;
                border-radius: 16px;
                border: 1px solid rgba(73,41,154,0.45);
            }
        """)

        # Add shadow effect
        card.setGraphicsEffect(self.create_shadow_effect())

        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(80, 80)

        # Title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #49299a; margin: 10px 0;")

        # Description
        desc_label = QLabel(description)
        desc_font = QFont()
        desc_font.setPointSize(12)
        desc_label.setFont(desc_font)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: rgba(232,232,252,0.85); line-height: 1.4;")

        # Button
        button = QPushButton(button_text)
        button_font = QFont()
        button_font.setPointSize(14)
        button_font.setBold(True)
        button.setFont(button_font)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(69,237,242,0.08);
                color: {button_color};
                border: 1px solid rgba(69,237,242,0.5);
                padding: 10px 16px;
                text-align: center;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: rgba(69,237,242,0.15);
                color: {self.darken_color(button_color)};
            }}
        """)

        # Connect button click
        if "Encoding" in button_text:
            button.clicked.connect(self.start_steganography_encoding)
        elif "Decoding" in button_text:
            button.clicked.connect(self.start_steganography_decoding)
        elif "Analyzing" in button_text:
            button.clicked.connect(self.start_steganalysis)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        layout.addWidget(button)

        return card

    def create_padlock_icon(self):
        """Create a padlock icon"""
        pixmap = QPixmap(80, 80)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Lock body (purple)
        painter.setBrush(QColor("#49299a"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(20, 35, 40, 30, 5, 5)

        # Keyhole (light lavender)
        painter.setBrush(QColor("#e8e8fc"))
        painter.drawEllipse(35, 45, 10, 10)
        painter.drawRect(38, 50, 4, 8)

        # Lock shackle (cyan)
        painter.setPen(Qt.PenStyle.SolidLine)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#45edf2"), 4))
        painter.drawArc(25, 20, 30, 30, 0, 180 * 16)

        painter.end()
        return pixmap

    def create_unlock_icon(self):
        """Create an unlock icon"""
        pixmap = QPixmap(80, 80)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Lock body (purple)
        painter.setBrush(QColor("#49299a"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(20, 35, 40, 30, 5, 5)

        # Keyhole (light lavender)
        painter.setBrush(QColor("#e8e8fc"))
        painter.drawEllipse(35, 45, 10, 10)
        painter.drawRect(38, 50, 4, 8)

        # Lock shackle (open - cyan)
        painter.setPen(Qt.PenStyle.SolidLine)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#45edf2"), 4))
        # Draw open shackle (arc from top-left to top-right)
        painter.drawArc(25, 20, 30, 30, 0, 90 * 16)  # Top arc
        painter.drawLine(40, 20, 40, 15)  # Vertical line up
        painter.drawLine(40, 15, 35, 15)  # Horizontal line left

        painter.end()
        return pixmap

    def create_magnifying_glass_icon(self):
        """Create a magnifying glass icon"""
        pixmap = QPixmap(80, 80)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Glass circle (cyan)
        painter.setBrush(QColor("#45edf2"))
        painter.setPen(QPen(QColor("#49299a"), 3))
        painter.drawEllipse(15, 15, 35, 35)

        # Handle (purple)
        painter.setPen(QPen(QColor("#49299a"), 6))
        painter.drawLine(45, 45, 60, 60)

        painter.end()
        return pixmap

    def create_shadow_effect(self):
        """Create a shadow effect for cards"""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(28)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        # Subtle cyan glow
        shadow.setColor(QColor(69, 237, 242, 50))
        return shadow

    def darken_color(self, color_hex):
        """Darken a hex color for hover effects"""
        color = QColor(color_hex)
        return color.darker(120).name()

    def start_steganography_encoding(self):
        """Handle steganography encoding button click"""
        from gui.stega_encode_window import StegaEncodeWindow
        self.encode_window = StegaEncodeWindow()
        self.encode_window.show()
        self.close()

    def start_steganography_decoding(self):
        """Handle steganography decoding button click"""
        from gui.stega_decode_window import StegaDecodeWindow
        self.decode_window = StegaDecodeWindow()
        self.decode_window.show()
        self.close()

    def start_steganalysis(self):
        """Handle steganalysis button click"""
        from gui.steganalysis_window import SteganalysisWindow
        self.steganalysis_window = SteganalysisWindow()
        self.steganalysis_window.show()
        self.close()
