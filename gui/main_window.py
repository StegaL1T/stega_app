# gui/main_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QApplication)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QLinearGradient, QBrush, QPen
import math
import random


class GradientLabel(QLabel):
    """Custom QLabel with gradient text effect"""
    def __init__(self, text):
        super().__init__(text)
        self.setMinimumHeight(50)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create gradient
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor("#45edf2"))  # Cyan
        gradient.setColorAt(0.5, QColor("#45edf2"))  # Cyan
        gradient.setColorAt(0.6, QColor("#49299a"))  # Purple
        gradient.setColorAt(1, QColor("#49299a"))    # Purple
        
        # Set the gradient as the brush
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Draw text with gradient
        font = self.font()
        painter.setFont(font)
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(gradient, 1))
        
        # Get text metrics
        metrics = painter.fontMetrics()
        text_rect = metrics.boundingRect(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())
        
        # Draw the text
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.text())


class CyberBackgroundWidget(QWidget):
    """Custom background widget with subtle cybersecurity elements"""
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update)
        self.animation_timer.start(50)  # 20 FPS animation
        self.time = 0
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Base dark background
        painter.fillRect(self.rect(), QColor("#0e1625"))
        
        # Subtle grid pattern
        self.draw_grid(painter)
        
        # Floating particles (data packets)
        self.draw_particles(painter)
        
        # Subtle circuit-like patterns
        self.draw_circuit_patterns(painter)
        
        # Cybersecurity scan lines
        self.draw_scan_lines(painter)
        
        self.time += 0.02
        
    def draw_grid(self, painter):
        """Draw an enhanced grid pattern with cybersecurity elements"""
        # Main grid lines
        painter.setPen(QPen(QColor(69, 237, 242, 12), 1))
        grid_size = 40
        
        for x in range(0, self.width(), grid_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), grid_size):
            painter.drawLine(0, y, self.width(), y)
        
        # Add some grid intersections with small dots
        painter.setPen(QPen(QColor(69, 237, 242, 20), 2))
        for x in range(grid_size, self.width(), grid_size * 2):
            for y in range(grid_size, self.height(), grid_size * 2):
                painter.drawPoint(x, y)
        
        # Add some diagonal accent lines for tech feel
        painter.setPen(QPen(QColor(73, 41, 154, 8), 1))
        for i in range(0, self.width(), grid_size * 3):
            painter.drawLine(i, 0, i + grid_size, grid_size)
            painter.drawLine(i, self.height(), i + grid_size, self.height() - grid_size)
    
    def draw_particles(self, painter):
        """Draw floating data particles"""
        painter.setPen(QPen(QColor(69, 237, 242, 30), 2))
        
        # Create some floating particles
        for i in range(8):
            x = (self.width() * 0.1 + i * self.width() * 0.1 + 
                 math.sin(self.time + i) * 20) % self.width()
            y = (self.height() * 0.2 + i * self.height() * 0.1 + 
                 math.cos(self.time * 0.7 + i) * 15) % self.height()
            
            # Draw small circles
            painter.drawEllipse(int(x), int(y), 3, 3)
    
    def draw_circuit_patterns(self, painter):
        """Draw subtle circuit-like patterns"""
        painter.setPen(QPen(QColor(73, 41, 154, 15), 1))
        
        # Draw some circuit-like lines in corners
        corner_size = 100
        # Top-left corner
        painter.drawLine(20, 20, corner_size, 20)
        painter.drawLine(20, 20, 20, corner_size)
        painter.drawLine(20, corner_size, corner_size, corner_size)
        
        # Top-right corner
        painter.drawLine(self.width() - 20, 20, self.width() - corner_size, 20)
        painter.drawLine(self.width() - 20, 20, self.width() - 20, corner_size)
        painter.drawLine(self.width() - 20, corner_size, self.width() - corner_size, corner_size)
        
        # Bottom corners
        painter.drawLine(20, self.height() - 20, corner_size, self.height() - 20)
        painter.drawLine(20, self.height() - 20, 20, self.height() - corner_size)
        painter.drawLine(20, self.height() - corner_size, corner_size, self.height() - corner_size)
        
        painter.drawLine(self.width() - 20, self.height() - 20, self.width() - corner_size, self.height() - 20)
        painter.drawLine(self.width() - 20, self.height() - 20, self.width() - 20, self.height() - corner_size)
        painter.drawLine(self.width() - 20, self.height() - corner_size, self.width() - corner_size, self.height() - corner_size)
    
    def draw_connection_lines(self, painter):
        """Draw animated connection lines between particles"""
        painter.setPen(QPen(QColor(69, 237, 242, 20), 1))
        
        # Draw some connecting lines
        for i in range(3):
            x1 = self.width() * 0.2 + i * self.width() * 0.2
            y1 = self.height() * 0.3 + math.sin(self.time + i) * 10
            x2 = self.width() * 0.8 - i * self.width() * 0.2
            y2 = self.height() * 0.7 + math.cos(self.time + i) * 10
            
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))


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

        # Create central widget with background
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create background widget
        self.background_widget = CyberBackgroundWidget()
        self.background_widget.setParent(central_widget)
        self.background_widget.lower()  # Put it behind other widgets

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
        
        # Initialize background widget size
        self.background_widget.setGeometry(0, 0, self.width(), self.height())
        
    def resizeEvent(self, event):
        """Handle window resize to update background"""
        super().resizeEvent(event)
        if hasattr(self, 'background_widget'):
            self.background_widget.setGeometry(0, 0, self.width(), self.height())

    def create_title_section(self, layout):
        """Create the title and subtitle section"""
        # Main title with gradient effect using custom painting
        title_label = GradientLabel("LSB Steganography & Steganalysis Tool")
        title_font = QFont()
        title_font.setPointSize(36)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("margin-bottom: 10px;")

        subtitle_label = QLabel(
            "Advanced steganography and steganalysis platform for secure data hiding and detection.")
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
            "Steganography Encoding",
            "Hide sensitive data within images using advanced LSB and DCT algorithms. Supports multiple file formats with military-grade encryption.",
            "Start Encoding",
            "#45edf2",
            self.create_padlock_icon()
        )

        # Steganography Decoding card
        decode_card = self.create_card(
            "Steganography Decoding",
            "Extract hidden data from steganographic images. Advanced detection algorithms can reveal concealed information with high accuracy.",
            "Start Decoding",
            "#45edf2",
            self.create_unlock_icon()
        )

        # Steganalysis card
        analysis_card = self.create_card(
            "Steganalysis",
            "Detect and analyze potential steganographic content using AI-powered statistical analysis and machine learning techniques.",
            "Start Analyzing",
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
        card.setFixedSize(450, 400)  # Increased size to prevent text truncation
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
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

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
        desc_font.setPointSize(11)
        desc_label.setFont(desc_font)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setMaximumWidth(380)  # Ensure proper text wrapping
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
        if "Start Encoding" in button_text:
            button.clicked.connect(self.start_steganography_encoding)
        elif "Start Decoding" in button_text:
            button.clicked.connect(self.start_steganography_decoding)
        elif "Start Analyzing" in button_text:
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
