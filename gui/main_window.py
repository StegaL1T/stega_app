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
        
        # Create gradient - smooth fade from blue to purple
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor("#45edf2"))    # Cyan blue at start
        gradient.setColorAt(0.3, QColor("#45edf2"))  # Blue continues
        gradient.setColorAt(0.7, QColor("#49299a"))  # Purple starts
        gradient.setColorAt(1, QColor("#49299a"))    # Purple at end
        
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
        # Main grid lines with better visibility
        painter.setPen(QPen(QColor(69, 237, 242, 18), 1))  # Increased opacity
        grid_size = 40
        
        for x in range(0, self.width(), grid_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), grid_size):
            painter.drawLine(0, y, self.width(), y)
        
        # Add some grid intersections with small dots
        painter.setPen(QPen(QColor(69, 237, 242, 25), 2))  # Increased opacity
        for x in range(grid_size, self.width(), grid_size * 2):
            for y in range(grid_size, self.height(), grid_size * 2):
                painter.drawPoint(x, y)
        
        # Add some diagonal accent lines for tech feel
        painter.setPen(QPen(QColor(73, 41, 154, 12), 1))  # Increased opacity
        for i in range(0, self.width(), grid_size * 3):
            painter.drawLine(i, 0, i + grid_size, grid_size)
            painter.drawLine(i, self.height(), i + grid_size, self.height() - grid_size)
        
        # Static grid - no animated highlights to reduce visual clutter
    
    def draw_particles(self, painter):
        """Draw floating cybersecurity data packets"""
        # Main data packets
        painter.setPen(QPen(QColor(69, 237, 242, 25), 2))
        
        for i in range(6):
            x = (self.width() * 0.15 + i * self.width() * 0.12 + 
                 math.sin(self.time + i) * 15) % self.width()
            y = (self.height() * 0.25 + i * self.height() * 0.12 + 
                 math.cos(self.time * 0.8 + i) * 12) % self.height()
            
            # Draw data packet squares
            painter.drawRect(int(x), int(y), 4, 4)
        
        # Add some smaller security indicators
        painter.setPen(QPen(QColor(73, 41, 154, 20), 1))
        for i in range(4):
            x = (self.width() * 0.1 + i * self.width() * 0.2 + 
                 math.sin(self.time * 1.2 + i) * 25) % self.width()
            y = (self.height() * 0.3 + i * self.height() * 0.15 + 
                 math.cos(self.time * 0.6 + i) * 18) % self.height()
            
            # Draw small security dots
            painter.drawPoint(int(x), int(y))
    
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
    
    def draw_scan_lines(self, painter):
        """Draw cybersecurity scan lines effect - maximum 4 lines"""
        # Two horizontal scan lines
        painter.setPen(QPen(QColor(69, 237, 242, 45), 2))
        scan_y = int((self.height() * 0.3 + math.sin(self.time * 2) * self.height() * 0.4) % self.height())
        painter.drawLine(0, scan_y, self.width(), scan_y)
        
        painter.setPen(QPen(QColor(69, 237, 242, 30), 1))
        scan_y2 = int((self.height() * 0.7 + math.cos(self.time * 1.8) * self.height() * 0.35) % self.height())
        painter.drawLine(0, scan_y2, self.width(), scan_y2)
        
        # Two vertical scan lines
        painter.setPen(QPen(QColor(69, 237, 242, 40), 2))
        scan_x = int((self.width() * 0.2 + math.cos(self.time * 1.5) * self.width() * 0.5) % self.width())
        painter.drawLine(scan_x, 0, scan_x, self.height())
        
        painter.setPen(QPen(QColor(69, 237, 242, 25), 1))
        scan_x2 = int((self.width() * 0.8 + math.sin(self.time * 1.2) * self.width() * 0.4) % self.width())
        painter.drawLine(scan_x2, 0, scan_x2, self.height())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steganography Tool")
        
        # Get screen dimensions and calculate responsive sizing
        self.setup_responsive_sizing()

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

        # Main layout with gradient background - centered with equal margins
        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setSpacing(self.spacing)  # Responsive spacing
        main_layout.setContentsMargins(self.margins, self.margins, self.margins, self.margins)  # Responsive margins

        # Title section
        self.create_title_section(main_layout)

        # Cards section
        self.create_cards_section(main_layout)

        # Set window size and position
        self.setGeometry(self.window_x, self.window_y, self.window_width, self.window_height)
        self.show()
        
        # Initialize background widget size
        self.background_widget.setGeometry(0, 0, self.width(), self.height())
    
    def setup_responsive_sizing(self):
        """Setup responsive sizing based on screen dimensions"""
        # Get screen dimensions using modern PyQt6 approach
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        screen = app.primaryScreen().geometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        # Define responsive scaling factors
        # For screens between 1200x1080 and 1920x1200
        if screen_width <= 1366:  # Smaller laptops
            scale_factor = 0.8
        elif screen_width <= 1600:  # Medium laptops
            scale_factor = 0.9
        else:  # Larger screens
            scale_factor = 1.0
        
        # Calculate window dimensions (leave some margin from screen edges)
        margin_percent = 0.05  # 5% margin from screen edges
        self.window_width = int(screen_width * (1 - 2 * margin_percent))
        self.window_height = int(screen_height * (1 - 2 * margin_percent))
        
        # Center the window
        self.window_x = int(screen_width * margin_percent)
        self.window_y = int(screen_height * margin_percent)
        
        # Set minimum size to ensure usability on smaller screens
        min_width = 1000
        min_height = 700
        self.window_width = max(self.window_width, min_width)
        self.window_height = max(self.window_height, min_height)
        
        # Responsive layout parameters
        self.margins = int(40 * scale_factor)  # Responsive margins
        self.spacing = int(30 * scale_factor)  # Responsive spacing
        
        # Responsive font sizes
        self.title_font_size = int(28 * scale_factor)
        self.subtitle_font_size = int(14 * scale_factor)
        self.card_title_font_size = int(18 * scale_factor)
        self.card_desc_font_size = int(10 * scale_factor)
        self.button_font_size = int(12 * scale_factor)
        
        # Responsive card dimensions
        self.card_min_width = int(280 * scale_factor)
        self.card_max_width = int(350 * scale_factor)
        self.card_min_height = int(320 * scale_factor)
        self.card_max_height = int(400 * scale_factor)
        self.card_spacing = int(30 * scale_factor)
        
        # Responsive icon size
        self.icon_size = int(80 * scale_factor)
        
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
        title_font.setPointSize(self.title_font_size)  # Responsive font size
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"margin-top: {int(20 * (self.title_font_size / 28))}px; margin-bottom: {int(10 * (self.title_font_size / 28))}px;")  # Responsive spacing

        subtitle_label = QLabel(
            "Advanced steganography and steganalysis platform for secure data hiding and detection.")
        subtitle_font = QFont()
        subtitle_font.setPointSize(self.subtitle_font_size)  # Responsive font size
        subtitle_font.setWeight(QFont.Weight.Light)  # Lighter font weight
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(f"color: #D9D9D9; margin-bottom: {int(20 * (self.subtitle_font_size / 14))}px; line-height: 1.4;")  # Responsive spacing

        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)

    def create_cards_section(self, layout):
        """Create the three main cards with enhanced spacing"""
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(self.card_spacing)  # Responsive spacing between cards
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cards_layout.setContentsMargins(0, 0, 0, 0)  # No extra margins on cards container

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

        # Create cards widget with centered layout
        cards_widget = QWidget()
        cards_widget.setLayout(cards_layout)
        cards_widget.setStyleSheet("")  # No extra styling for perfect centering
        
        layout.addWidget(cards_widget)

    def create_card(self, title, description, button_text, button_color, icon):
        """Create an enhanced responsive card widget with better UX"""
        card = QFrame()
        card.setMinimumSize(self.card_min_width, self.card_min_height)  # Responsive minimum size
        card.setMaximumSize(self.card_max_width, self.card_max_height)  # Responsive maximum size
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        card.setStyleSheet("""
            QFrame {
                background-color: #0e1625;
                border-radius: 18px;
                border: 3px solid rgba(73,41,154,0.6);
                padding: 5px;
            }
        """)

        # No shadow effect - clean purple border only

        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(int(6 * (self.card_min_width / 280)))  # Responsive spacing
        layout.setContentsMargins(int(15 * (self.card_min_width / 280)), int(15 * (self.card_min_width / 280)), 
                                 int(15 * (self.card_min_width / 280)), int(15 * (self.card_min_width / 280)))  # Responsive margins

        # Icon with proper centering - no borders
        icon_container = QWidget()
        icon_container.setFixedHeight(self.icon_size + 20)  # Responsive icon container height
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
        icon_label.setFixedSize(self.icon_size, self.icon_size)  # Responsive icon size
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
        title_font.setPointSize(self.card_title_font_size)  # Responsive font size
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("""
            color: #45edf2;
            margin: 4px 0;
            padding: 2px 0;
            border: none;
            background: transparent;
        """)
        title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Description with improved readability
        desc_label = QLabel(description)
        desc_font = QFont()
        desc_font.setPointSize(self.card_desc_font_size)  # Responsive font size
        desc_font.setWeight(QFont.Weight.Normal)
        desc_label.setFont(desc_font)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center-align for consistency
        desc_label.setWordWrap(True)
        desc_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        desc_label.setStyleSheet("""
            color: #D9D9D9;
            line-height: 1.5;
            padding: 4px 4px 2px 4px;
            text-align: center;
            border: none;
            background: transparent;
        """)

        # Enhanced button with gradient and hover effects
        button = QPushButton(button_text)
        button_font = QFont()
        button_font.setPointSize(self.button_font_size)  # Responsive font size
        button_font.setBold(True)
        button.setFont(button_font)
        button.setMinimumHeight(int(35 * (self.card_min_width / 280)))  # Responsive button height
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        button.setStyleSheet(f"""
            QPushButton {{
                background: rgba(69,237,242,0.1);
                color: {button_color};
                border: 2px solid rgba(69,237,242,0.6);
                padding: 10px 20px;
                text-align: center;
                border-radius: 12px;
                min-height: 45px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(69,237,242,0.3);
                border: 3px solid rgba(69,237,242,1.0);
            }}
            QPushButton:pressed {{
                background: rgba(69,237,242,0.3);
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
        layout.addSpacing(2)
        layout.addWidget(button)

        return card

    def load_icon(self, icon_path):
        """Load an icon from a PNG file and resize it responsively"""
        try:
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                # Scale the icon responsively while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(self.icon_size, self.icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
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
        icon_size = self.icon_size
        pixmap = QPixmap(icon_size, icon_size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#45edf2"))
        painter.setPen(Qt.PenStyle.NoPen)
        margin = int(icon_size * 0.125)  # 12.5% margin
        painter.drawEllipse(margin, margin, icon_size - 2*margin, icon_size - 2*margin)
        painter.end()
        return pixmap


    def create_shadow_effect(self):
        """Create an enhanced shadow effect for cards"""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(35)  # Increased blur for stronger glow
        shadow.setXOffset(0)
        shadow.setYOffset(8)  # Increased offset for more depth
        # Enhanced cyan glow with higher opacity
        shadow.setColor(QColor(69, 237, 242, 80))  # Doubled opacity for stronger effect
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
