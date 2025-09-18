# gui/main_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QApplication, QSizePolicy)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QLinearGradient, QBrush, QPen, QPainterPath
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
        
        # Enhanced grid pattern
        self.draw_enhanced_grid(painter)
        
        # Floating data packets with trails
        self.draw_enhanced_particles(painter)
        
        # Circuit patterns with connections
        self.draw_enhanced_circuit_patterns(painter)
        
        # Cybersecurity scan lines
        self.draw_enhanced_scan_lines(painter)
        
        # Data flow streams
        self.draw_data_streams(painter)
        
        # Security indicators
        self.draw_security_indicators(painter)
        
        self.time += 0.02
        
    def draw_enhanced_grid(self, painter):
        """Draw an enhanced grid pattern with cybersecurity elements"""
        # Main grid lines with pulsing effect
        pulse_intensity = 8 + 4 * math.sin(self.time * 3)
        painter.setPen(QPen(QColor(69, 237, 242, int(pulse_intensity)), 1))
        grid_size = 40
        
        for x in range(0, self.width(), grid_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), grid_size):
            painter.drawLine(0, y, self.width(), y)
        
        # Animated grid intersections with pulsing dots
        pulse_dots = 15 + 10 * math.sin(self.time * 2)
        painter.setPen(QPen(QColor(69, 237, 242, int(pulse_dots)), 2))
        for x in range(grid_size, self.width(), grid_size * 2):
            for y in range(grid_size, self.height(), grid_size * 2):
                painter.drawPoint(x, y)
        
        # Animated diagonal accent lines
        diagonal_intensity = 6 + 3 * math.cos(self.time * 1.5)
        painter.setPen(QPen(QColor(73, 41, 154, int(diagonal_intensity)), 1))
        for i in range(0, self.width(), grid_size * 3):
            offset = 5 * math.sin(self.time + i * 0.1)
            painter.drawLine(i, int(0 + offset), i + grid_size, int(grid_size + offset))
            painter.drawLine(i, int(self.height() - offset), i + grid_size, int(self.height() - grid_size - offset))
    
    def draw_enhanced_particles(self, painter):
        """Draw enhanced floating cybersecurity data packets with trails"""
        # Main data packets with pulsing intensity
        for i in range(8):
            x = (self.width() * 0.1 + i * self.width() * 0.1 + 
                 math.sin(self.time + i * 0.5) * 20) % self.width()
            y = (self.height() * 0.2 + i * self.height() * 0.1 + 
                 math.cos(self.time * 0.7 + i * 0.3) * 15) % self.height()
            
            # Pulsing intensity
            intensity = 20 + 15 * math.sin(self.time * 2 + i)
            painter.setPen(QPen(QColor(69, 237, 242, int(intensity)), 2))
            
            # Draw data packet with trail effect
            trail_length = 3
            for j in range(trail_length):
                alpha = intensity * (1 - j / trail_length) * 0.3
                painter.setPen(QPen(QColor(69, 237, 242, int(alpha)), 1))
                offset_x = -j * 2
                offset_y = -j * 2
                painter.drawRect(int(x + offset_x), int(y + offset_y), 4 - j, 4 - j)
        
        # Security indicators with different patterns
        painter.setPen(QPen(QColor(73, 41, 154, 25), 1))
        for i in range(6):
            x = (self.width() * 0.15 + i * self.width() * 0.15 + 
                 math.sin(self.time * 1.3 + i) * 30) % self.width()
            y = (self.height() * 0.3 + i * self.height() * 0.12 + 
                 math.cos(self.time * 0.8 + i) * 20) % self.height()
            
            # Draw security indicators with different shapes
            if i % 2 == 0:
                painter.drawEllipse(int(x), int(y), 3, 3)
            else:
                painter.drawRect(int(x), int(y), 3, 3)
    
    def draw_enhanced_circuit_patterns(self, painter):
        """Draw enhanced circuit-like patterns with connections"""
        # Animated circuit intensity
        circuit_intensity = 12 + 8 * math.sin(self.time * 1.5)
        painter.setPen(QPen(QColor(73, 41, 154, int(circuit_intensity)), 1))
        
        # Draw animated circuit-like lines in corners
        corner_size = 120
        offset = 3 * math.sin(self.time * 2)
        
        # Top-left corner with animation
        painter.drawLine(int(20 + offset), 20, int(corner_size + offset), 20)
        painter.drawLine(20, int(20 + offset), 20, int(corner_size + offset))
        painter.drawLine(int(20 + offset), corner_size, int(corner_size + offset), corner_size)
        
        # Top-right corner
        painter.drawLine(int(self.width() - 20 - offset), 20, int(self.width() - corner_size - offset), 20)
        painter.drawLine(self.width() - 20, int(20 + offset), self.width() - 20, int(corner_size + offset))
        painter.drawLine(int(self.width() - 20 - offset), corner_size, int(self.width() - corner_size - offset), corner_size)
        
        # Bottom corners
        painter.drawLine(int(20 + offset), self.height() - 20, int(corner_size + offset), self.height() - 20)
        painter.drawLine(20, int(self.height() - 20 - offset), 20, int(self.height() - corner_size - offset))
        painter.drawLine(int(20 + offset), self.height() - corner_size, int(corner_size + offset), self.height() - corner_size)
        
        painter.drawLine(int(self.width() - 20 - offset), self.height() - 20, int(self.width() - corner_size - offset), self.height() - 20)
        painter.drawLine(self.width() - 20, int(self.height() - 20 - offset), self.width() - 20, int(self.height() - corner_size - offset))
        painter.drawLine(int(self.width() - 20 - offset), self.height() - corner_size, int(self.width() - corner_size - offset), self.height() - corner_size)
        
        # Add connecting lines between corners
        painter.setPen(QPen(QColor(69, 237, 242, 8), 1))
        painter.drawLine(corner_size, 20, self.width() - corner_size, 20)
        painter.drawLine(corner_size, self.height() - 20, self.width() - corner_size, self.height() - 20)
    
    def draw_enhanced_scan_lines(self, painter):
        """Draw enhanced cybersecurity scan lines effect"""
        # Multiple horizontal scan lines with different speeds
        for i in range(3):
            speed = 1.5 + i * 0.5
            intensity = 12 + 8 * math.sin(self.time * speed)
            painter.setPen(QPen(QColor(69, 237, 242, int(intensity)), 1))
            scan_y = int((self.height() * (0.2 + i * 0.3) + math.sin(self.time * speed) * self.height() * 0.15) % self.height())
            painter.drawLine(0, scan_y, self.width(), scan_y)
        
        # Multiple vertical scan lines
        for i in range(2):
            speed = 1.2 + i * 0.3
            intensity = 10 + 6 * math.cos(self.time * speed)
            painter.setPen(QPen(QColor(69, 237, 242, int(intensity)), 1))
            scan_x = int((self.width() * (0.15 + i * 0.4) + math.cos(self.time * speed) * self.width() * 0.2) % self.width())
            painter.drawLine(scan_x, 0, scan_x, self.height())
        
        # Animated binary code patterns
        painter.setPen(QPen(QColor(73, 41, 154, 15), 1))
        binary_patterns = ["1010", "1101", "0110", "1001", "1110", "0001"]
        for i, pattern in enumerate(binary_patterns):
            x = 30 + (i % 3) * (self.width() - 150)
            y = 30 + (i // 3) * (self.height() - 150)
            # Add slight animation to binary text
            offset = 2 * math.sin(self.time * 3 + i)
            painter.drawText(int(x + offset), int(y + offset), pattern)

    def draw_data_streams(self, painter):
        """Draw flowing data streams"""
        # Flowing data streams with wave patterns
        painter.setPen(QPen(QColor(69, 237, 242, 12), 2))
        for i in range(4):
            wave_amplitude = 20 + 10 * math.sin(self.time + i)
            wave_frequency = 0.02 + i * 0.005
            
            # Draw flowing stream
            for x in range(0, self.width(), 5):
                y = self.height() * (0.3 + i * 0.15) + wave_amplitude * math.sin(x * wave_frequency + self.time * 2)
                if 0 <= y <= self.height():
                    painter.drawPoint(x, int(y))
    
    def draw_security_indicators(self, painter):
        """Draw security status indicators"""
        # Security status lights
        for i in range(5):
            x = self.width() * 0.1 + i * self.width() * 0.2
            y = self.height() * 0.1
            
            # Pulsing security indicators
            pulse = 15 + 10 * math.sin(self.time * 4 + i)
            painter.setPen(QPen(QColor(69, 237, 242, int(pulse)), 3))
            painter.drawEllipse(int(x), int(y), 6, 6)
            
            # Add status text
            painter.setPen(QPen(QColor(73, 41, 154, 20), 1))
            status_texts = ["SEC", "AUTH", "ENCR", "MON", "LOG"]
            painter.drawText(int(x - 10), int(y + 20), status_texts[i])


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
        main_layout.setSpacing(50)  # Increased spacing for better balance
        main_layout.setContentsMargins(50, 80, 50, 50)  # More top margin to push content down

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
        """Create the title and subtitle section with enhanced typography"""
        # Main title with gradient effect using custom painting
        title_label = GradientLabel("LSB Steganography & Steganalysis Tool")
        title_font = QFont()
        title_font.setPointSize(38)  # Slightly larger for better hierarchy
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("margin-bottom: 20px;")  # Increased spacing

        subtitle_label = QLabel(
            "Advanced steganography and steganalysis platform for secure data hiding and detection.")
        subtitle_font = QFont()
        subtitle_font.setPointSize(17)  # Slightly larger for better readability
        subtitle_font.setWeight(QFont.Weight.Light)  # Lighter font weight
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #D9D9D9; margin-bottom: 40px; line-height: 1.4;")  # More spacing before cards

        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)

    def create_cards_section(self, layout):
        """Create the three main cards with enhanced spacing"""
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(50)  # Increased spacing between cards for better visual balance
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Steganography Encoding card
        encode_card = self.create_card(
            "Steganography Encoding",
            "Hide sensitive data within images using advanced LSB and DCT algorithms. Supports multiple file formats with military-grade encryption.",
            "Start Encoding",
            "#45edf2",
            self.load_icon("asset/icons/encoding.png")
        )

        # Steganography Decoding card
        decode_card = self.create_card(
            "Steganography Decoding",
            "Extract hidden data from steganographic images. Advanced detection algorithms can reveal concealed information with high accuracy.",
            "Start Decoding",
            "#45edf2",
            self.load_icon("asset/icons/decoding.png")
        )

        # Steganalysis card
        analysis_card = self.create_card(
            "Steganalysis",
            "Detect and analyze potential steganographic content using AI-powered statistical analysis and machine learning techniques.",
            "Start Analyzing",
            "#45edf2",
            self.load_icon("asset/icons/steganalysis.png")
        )

        cards_layout.addWidget(encode_card)
        cards_layout.addWidget(decode_card)
        cards_layout.addWidget(analysis_card)

        # Add some top spacing to the cards section
        cards_widget = QWidget()
        cards_widget.setLayout(cards_layout)
        cards_widget.setStyleSheet("margin-top: 20px;")
        
        layout.addWidget(cards_widget)

    def create_card(self, title, description, button_text, button_color, icon):
        """Create an enhanced responsive card widget with better UX"""
        card = QFrame()
        card.setMinimumSize(360, 400)  # Slightly larger for better breathing room
        card.setMaximumSize(440, 480)  # Increased maximum size
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        card.setStyleSheet("""
            QFrame {
                background-color: #0e1625;
                border-radius: 18px;
                border: 1px solid rgba(73,41,154,0.45);
                padding: 5px;
            }
        """)

        # Add shadow effect
        card.setGraphicsEffect(self.create_shadow_effect())

        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)  # Better spacing for readability
        layout.setContentsMargins(20, 20, 20, 20)  # More breathing room

        # Icon with proper centering - no borders
        icon_container = QWidget()
        icon_container.setFixedHeight(80)  # Larger icons for better visibility
        icon_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        icon_container.setStyleSheet("""
            QWidget {
                border: none;
                background: transparent;
            }
        """)
        icon_layout = QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel()
        icon_label.setPixmap(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(80, 80)  # Larger icon size
        # Remove icon border styling - explicitly no borders
        icon_label.setStyleSheet("""
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        
        icon_layout.addWidget(icon_label)

        # Title with gradient effect
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(22)  # Larger for better hierarchy
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("""
            color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #45edf2, stop:0.5 #45edf2, stop:0.6 #7B2CBF, stop:1 #7B2CBF);
            margin: 8px 0;
            padding: 4px 0;
            border: none;
            background: transparent;
        """)
        title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Description with improved readability
        desc_label = QLabel(description)
        desc_font = QFont()
        desc_font.setPointSize(12)  # Larger for better readability
        desc_font.setWeight(QFont.Weight.Normal)
        desc_label.setFont(desc_font)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center-align for consistency
        desc_label.setWordWrap(True)
        desc_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        desc_label.setStyleSheet("""
            color: #D9D9D9;
            line-height: 1.5;
            padding: 8px 4px 4px 4px;
            text-align: center;
            border: none;
            background: transparent;
        """)

        # Enhanced button with gradient and hover effects
        button = QPushButton(button_text)
        button_font = QFont()
        button_font.setPointSize(14)  # Slightly larger
        button_font.setBold(True)
        button.setFont(button_font)
        button.setMinimumHeight(45)  # Taller for better touch targets
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(69,237,242,0.1), stop:1 rgba(69,237,242,0.05));
                color: {button_color};
                border: 2px solid rgba(69,237,242,0.6);
                padding: 10px 20px;
                text-align: center;
                border-radius: 12px;
                min-height: 45px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(69,237,242,0.2), stop:1 rgba(73,41,154,0.1));
                border: 2px solid rgba(69,237,242,0.8);
                transform: scale(1.02);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(69,237,242,0.3), stop:1 rgba(73,41,154,0.2));
            }}
        """)

        # Connect button click
        if "Start Encoding" in button_text:
            button.clicked.connect(self.start_steganography_encoding)
        elif "Start Decoding" in button_text:
            button.clicked.connect(self.start_steganography_decoding)
        elif "Start Analyzing" in button_text:
            button.clicked.connect(self.start_steganalysis)

        layout.addWidget(icon_container)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        # Add minimal spacing for compact cards
        layout.addSpacing(6)
        layout.addWidget(button)

        return card

    def load_icon(self, icon_path):
        """Load an icon from a PNG file and resize it to 80x80"""
        try:
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                # Scale the icon to 80x80 while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                return scaled_pixmap
            else:
                print(f"Warning: Could not load icon from {icon_path}")
                # Return a default icon if loading fails
                return self.create_default_icon()
        except Exception as e:
            print(f"Error loading icon {icon_path}: {e}")
            return self.create_default_icon()

    def create_default_icon(self):
        """Create a simple default icon if PNG loading fails"""
        pixmap = QPixmap(80, 80)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#45edf2"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(10, 10, 60, 60)
        painter.end()
        return pixmap


    def create_shadow_effect(self):
        """Create an enhanced shadow effect for cards"""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        # Enhanced cyan glow
        shadow.setColor(QColor(69, 237, 242, 40))
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
