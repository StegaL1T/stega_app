# gui/steganalysis_window.py
import datetime
from pathlib import Path
import numpy as np
from PIL import Image
import io
import wave
import matplotlib.pyplot as plt
import cv2
import math
import random
import os


# gui/steganalysis_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QFileDialog, QTextEdit,
                             QGroupBox, QGridLayout, QLineEdit, QComboBox, QProgressBar, QApplication,
                             QStackedWidget, QHBoxLayout, QSizePolicy, QTabWidget, QSpacerItem, QScrollArea)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QLinearGradient, QBrush
import numpy as np
import cv2

# Matplotlib for charts (QtAgg backend for PyQt6)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_pdf import PdfPages

# Import individual window modules
from gui.image_steganalysis_window import ImageSteganalysisWindow
from gui.audio_steganalysis_window import AudioSteganalysisWindow
from gui.video_steganalysis_window import VideoSteganalysisWindow


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
            painter.drawLine(i, self.height(), i + grid_size,
                             self.height() - grid_size)

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
        painter.drawLine(self.width() - 20, corner_size,
                         self.width() - corner_size, corner_size)

        # Bottom corners
        painter.drawLine(20, self.height() - 20,
                         corner_size, self.height() - 20)
        painter.drawLine(20, self.height() - 20, 20,
                         self.height() - corner_size)
        painter.drawLine(20, self.height() - corner_size,
                         corner_size, self.height() - corner_size)

        painter.drawLine(self.width() - 20, self.height() - 20,
                         self.width() - corner_size, self.height() - 20)
        painter.drawLine(self.width() - 20, self.height() - 20,
                         self.width() - 20, self.height() - corner_size)
        painter.drawLine(self.width() - 20, self.height() - corner_size,
                         self.width() - corner_size, self.height() - corner_size)

    def draw_scan_lines(self, painter):
        """Draw cybersecurity scan lines effect - maximum 4 lines"""
        # Two horizontal scan lines
        painter.setPen(QPen(QColor(69, 237, 242, 45), 2))
        scan_y = int((self.height() * 0.3 + math.sin(self.time * 2)
                     * self.height() * 0.4) % self.height())
        painter.drawLine(0, scan_y, self.width(), scan_y)

        painter.setPen(QPen(QColor(69, 237, 242, 30), 1))
        scan_y2 = int((self.height() * 0.7 + math.cos(self.time * 1.8)
                      * self.height() * 0.35) % self.height())
        painter.drawLine(0, scan_y2, self.width(), scan_y2)

        # Two vertical scan lines
        painter.setPen(QPen(QColor(69, 237, 242, 40), 2))
        scan_x = int((self.width() * 0.2 + math.cos(self.time * 1.5)
                     * self.width() * 0.5) % self.width())
        painter.drawLine(scan_x, 0, scan_x, self.height())

        painter.setPen(QPen(QColor(69, 237, 242, 25), 1))
        scan_x2 = int((self.width() * 0.8 + math.sin(self.time * 1.2)
                      * self.width() * 0.4) % self.width())
        painter.drawLine(scan_x2, 0, scan_x2, self.height())


class SteganalysisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steganalysis - Detect Hidden Messages")

        # Setup responsive sizing
        self.setup_responsive_sizing()

        # Initialize the steganalysis machine
        from machine.steganalysis_machine import SteganalysisMachine
        self.machine = SteganalysisMachine()
        
        # Initialize individual window modules
        self.image_window = ImageSteganalysisWindow(self.machine)
        self.audio_window = AudioSteganalysisWindow(self.machine)
        self.video_window = VideoSteganalysisWindow(self.machine)
        
        # Set main GUI references
        self.image_window.set_main_gui(self)
        self.audio_window.set_main_gui(self)
        self.video_window.set_main_gui(self)

        # Method descriptions
        self.method_descriptions = {
            # Image analysis methods
            "LSB Analysis": "Analyzes the least significant bits of each pixel to detect hidden data. LSB steganography is the most common method of hiding information in images.",
            "Chi-Square Test": "Performs statistical analysis on pixel value distributions to detect anomalies that may indicate steganographic content.",
            "RS Analysis": "Regular-Singular analysis examines how flipping LSBs affects image smoothness to detect LSB steganography with high accuracy.",
            "Sample Pairs Analysis": "Analyzes adjacent pixel pairs to detect statistical anomalies that may indicate hidden data in the image.",
            "DCT Analysis": "Discrete Cosine Transform analysis examines frequency domain characteristics to detect steganography in JPEG images.",
            "Wavelet Analysis": "Analyzes image using wavelet transforms to detect steganographic artifacts in different frequency bands.",
            "Histogram Analysis": "Examines pixel value histograms for unusual patterns that may indicate hidden information.",
            "Advanced Comprehensive": "Uses all available detection methods with advanced algorithms for the most thorough steganalysis possible.",

            # Audio analysis methods
            "Audio LSB Analysis": "Analyzes least significant bits in audio samples to detect hidden data embedded in audio files.",
            "Audio Chi-Square Test": "Statistical analysis of audio sample distributions to identify anomalies that may indicate steganographic content.",
            "Audio Spectral Analysis": "Examines frequency domain characteristics and power spectral density to detect audio steganography.",
            "Audio Autocorrelation Analysis": "Analyzes temporal patterns and periodic structures in audio to detect hidden information.",
            "Audio Entropy Analysis": "Measures randomness and information content in audio samples to identify steganographic artifacts.",
            "Audio Comprehensive Analysis": "Combines multiple audio detection methods for thorough analysis of potential hidden content.",
            "Audio Advanced Comprehensive": "Uses all available audio analysis techniques for the most comprehensive steganalysis possible.",

            # Video analysis methods
            "Video LSB Analysis": "Analyzes least significant bits in video frames to detect hidden data embedded in video files.",
            "Video Frame Analysis": "Examines individual video frames for anomalies and statistical irregularities that may indicate steganography.",
            "Video Motion Analysis": "Analyzes motion vectors and temporal patterns between frames to detect hidden information.",
            "Video Advanced Comprehensive": "Uses all available video analysis techniques for the most comprehensive steganalysis possible."
        }

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

        # Create background widget
        self.background_widget = CyberBackgroundWidget()
        self.background_widget.setParent(central_widget)
        self.background_widget.lower()  # Put it behind other widgets

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Title section
        self.create_title_section(main_layout)

        # Main content area (tabs)
        self.create_tabs(main_layout)

        # Set window size and position
        self.setGeometry(self.window_x, self.window_y,
                         self.window_width, self.window_height)
        self.show()

        # Initialize background widget size
        self.background_widget.setGeometry(0, 0, self.width(), self.height())

    def resizeEvent(self, event):
        """Handle window resize to update background"""
        super().resizeEvent(event)
        if hasattr(self, 'background_widget'):
            self.background_widget.setGeometry(
                0, 0, self.width(), self.height())

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

    def create_title_section(self, layout):
        """Create the title and back button section"""
        title_layout = QHBoxLayout()

        # Back button with cyber theme
        back_button = QPushButton("← Back to Main")
        back_button.setStyleSheet("""
            QPushButton {
                background: rgba(69,237,242,0.1);
                color: #e8e8fc;
                border: 2px solid rgba(69,237,242,0.6);
                padding: 10px 20px;
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(69,237,242,0.3);
                border: 3px solid rgba(69,237,242,1.0);
            }
            QPushButton:pressed {
                background: rgba(69,237,242,0.3);
            }
        """)
        back_button.clicked.connect(self.go_back)

        # Title with cyber theme
        title_label = QLabel("Steganalysis - Detect Hidden Messages")
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #45edf2; margin: 10px 0;")

        title_layout.addWidget(back_button)
        title_layout.addStretch()
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        layout.addLayout(title_layout)

    def create_tabs(self, layout):
        """Create Image/Audio/Video steganalysis tabs"""
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.setTabPosition(QTabWidget.TabPosition.North)
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 15px;
                background-color: rgba(14,22,37,0.8);
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background: rgba(69,237,242,0.1);
                color: #e8e8fc;
                border: 2px solid rgba(69,237,242,0.6);
                padding: 10px 20px;
                margin: 5px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background: rgba(69,237,242,0.3);
                border: 3px solid rgba(69,237,242,1.0);
            }
            QTabBar::tab:hover {
                background: rgba(69,237,242,0.2);
            }
        """)

        image_tab = QWidget()
        audio_tab = QWidget()
        video_tab = QWidget()

        # Build image tab
        img_split = QHBoxLayout(image_tab)
        img_split.setSpacing(30)

        img_controls = self._build_image_controls()
        img_results = self._build_image_results()
        img_split.addWidget(img_controls)
        img_split.addWidget(img_results)

        # Build audio tab
        aud_split = QHBoxLayout(audio_tab)
        aud_split.setSpacing(30)

        aud_controls = self._build_audio_controls()
        aud_results = self._build_audio_results()
        aud_split.addWidget(aud_controls)
        aud_split.addWidget(aud_results)

        # Build video tab
        vid_split = QHBoxLayout(video_tab)
        vid_split.setSpacing(30)

        vid_controls = self._build_video_controls()
        vid_results = self._build_video_results()
        vid_split.addWidget(vid_controls)
        vid_split.addWidget(vid_results)

        tabs.addTab(image_tab, "Image Steganalysis")
        tabs.addTab(audio_tab, "Audio Steganalysis")
        tabs.addTab(video_tab, "Video Steganalysis")

        layout.addWidget(tabs)

    def _styled_panel(self) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame { 
                background-color: #0e1625;
                border-radius: 15px; 
                border: 2px solid rgba(69,237,242,0.6);
            }
        """)
        return panel


    def _build_image_controls(self) -> QWidget:
        panel = self._styled_panel()
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Image Analysis Input")
        f = QFont()
        f.setPointSize(20)
        f.setBold(True)
        title.setFont(f)
        title.setStyleSheet(
            "color: #e8e8fc; margin-bottom: 10px; border: none;")

        image_group = QGroupBox("Suspicious Image")
        image_group.setStyleSheet("""
            QGroupBox {
                color: #e8e8fc;
                font-weight: bold;
                font-size: 16px;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        image_layout = QVBoxLayout(image_group)
        self.image_path = QLineEdit()
        self.image_path.setPlaceholderText("Select image to analyze...")
        self.image_path.setReadOnly(True)
        self.image_path.setStyleSheet("""
            QLineEdit {
                background-color: #0e1625;
                color: #e8e8fc;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                padding: 8px;
            }
            QLineEdit:focus {
                border: 3px solid rgba(69,237,242,1.0);
            }
        """)
        browse_button = QPushButton("Browse Image")
        browse_button.setStyleSheet("""
            QPushButton { 
                background: rgba(34,139,34,0.2);
                color: #22c55e;
                border: 2px solid #22c55e;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { 
                background: rgba(34,139,34,0.4);
                border: 3px solid #22c55e;
                color: #ffffff;
            }
        """)
        browse_button.clicked.connect(self.image_window.browse_image)
        image_layout.addWidget(self.image_path)
        image_layout.addWidget(browse_button)

        # Image preview
        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setStyleSheet("""
            QLabel {
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                background-color: #0e1625;
                color: #e8e8fc;
                min-height: 150px;
                max-height: 200px;
            }
        """)
        self.image_preview.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.image_preview.setText("No image selected")
        self.image_preview.setScaledContents(False)
        self.image_preview.setAcceptDrops(True)  # Enable drag and drop directly on the preview
        # Connect drag and drop events
        self.image_preview.dragEnterEvent = self.image_preview_drag_enter_event
        self.image_preview.dragLeaveEvent = self.image_preview_drag_leave_event
        self.image_preview.dropEvent = self.image_preview_drop_event
        image_layout.addWidget(self.image_preview)

        method_group = QGroupBox("Image Analysis Method")
        method_group.setStyleSheet("""
            QGroupBox {
                color: #e8e8fc;
                font-weight: bold;
                font-size: 16px;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        method_layout = QVBoxLayout(method_group)
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "LSB Analysis", "Chi-Square Test", "RS Analysis", "Sample Pairs Analysis",
            "DCT Analysis", "Wavelet Analysis", "Histogram Analysis", "Advanced Comprehensive"
        ])
        self.method_combo.setStyleSheet("""
            QComboBox { 
                padding: 8px 12px 8px 12px; 
                border: 2px solid #45edf2; 
                border-radius: 8px; 
                background-color: #0e1625;
                color: #e8e8fc;
                font-weight: bold;
            }
            QComboBox:focus { 
                border: 3px solid #45edf2;
                background-color: rgba(69,237,242,0.1);
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 2px solid #45edf2;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                background-color: #45edf2;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #0e1625;
                margin: 0 8px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #45edf2;
                border-radius: 8px;
                background-color: #0e1625;
                color: #e8e8fc;
                selection-background-color: rgba(69,237,242,0.3);
            }
        """)
        self.method_combo.currentTextChanged.connect(
            self.image_window.on_image_method_changed)
        method_layout.addWidget(self.method_combo)

        self.img_analyze_btn = QPushButton("Analyze Image")
        self.img_analyze_btn.setStyleSheet("""
            QPushButton { 
                background: rgba(255,140,0,0.2);
                color: #ff8c00;
                border: 2px solid #ff8c00;
                padding: 12px 24px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { 
                background: rgba(255,140,0,0.4);
                border: 3px solid #ff8c00;
                color: #ffffff;
            }
            QPushButton:pressed {
                background: rgba(255,140,0,0.4);
            }
        """)
        self.img_analyze_btn.clicked.connect(self.image_window.analyze_image)

        # Method description
        self.image_method_description = QLabel()
        self.image_method_description.setWordWrap(True)
        self.image_method_description.setStyleSheet("""
            QLabel {
                background-color: #0e1625;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                color: #e8e8fc;
                min-height: 60px;
            }
        """)
        # Initialize with LSB Analysis description
        self.image_window.update_method_description(
            "LSB Analysis", self.image_method_description)


        layout.addWidget(title)
        layout.addWidget(image_group)
        layout.addWidget(method_group)
        layout.addWidget(self.image_method_description)
        layout.addWidget(self.img_analyze_btn)
        layout.addStretch()
        return panel

    def _build_image_results(self) -> QWidget:
        panel = self._styled_panel()
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Create header row with title and sensitivity level
        header_layout = QHBoxLayout()
        
        title = QLabel("Image Analysis Results")
        f = QFont()
        f.setPointSize(20)
        f.setBold(True)
        title.setFont(f)
        title.setStyleSheet(
            "color: #e8e8fc; margin-bottom: 10px; border: none;")
        
        # Add spacer to push sensitivity to the right
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Create narrow sensitivity level control with border and label
        sensitivity_group = QGroupBox("Sensitivity")
        sensitivity_group.setStyleSheet("""
            QGroupBox {
                color: #e8e8fc;
                font-weight: bold;
                font-size: 12px;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px 0 3px;
            }
        """)
        sensitivity_layout = QVBoxLayout(sensitivity_group)
        sensitivity_layout.setContentsMargins(8, 5, 8, 8)
        
        self.image_sensitivity_combo = QComboBox()
        self.image_sensitivity_combo.addItems([
            "🔴 Ultra",
            "🟡 Medium", 
            "🟢 Low"
        ])
        self.image_sensitivity_combo.setCurrentIndex(0)  # Default to Ultra
        self.image_sensitivity_combo.setMaximumWidth(140)  # Make it narrow
        self.image_sensitivity_combo.setStyleSheet("""
            QComboBox {
                background-color: #0e1625;
                color: #e8e8fc;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 6px;
                padding: 4px;
                font-size: 11px;
            }
            QComboBox:focus {
                border: 3px solid rgba(69,237,242,1.0);
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 3px solid #45edf2;
                margin-right: 6px;
            }
            QComboBox QAbstractItemView {
                background-color: #0e1625;
                color: #e8e8fc;
                border: 2px solid rgba(69,237,242,0.6);
                selection-background-color: rgba(69,237,242,0.3);
            }
        """)
        sensitivity_layout.addWidget(self.image_sensitivity_combo)
        
        header_layout.addWidget(sensitivity_group)

        self.img_progress_bar = QProgressBar()
        self.img_progress_bar.setVisible(False)
        self.img_progress_bar.setStyleSheet("""
            QProgressBar { 
                border: 2px solid rgba(69,237,242,0.6); 
                border-radius: 8px; 
                text-align: center; 
                background-color: #0e1625;
                color: #e8e8fc;
            }
            QProgressBar::chunk { 
                background-color: #45edf2; 
                border-radius: 6px; 
            }
        """)

        img_results_group = QGroupBox("Detection Results")
        img_results_group.setStyleSheet("""
            QGroupBox {
                color: #e8e8fc;
                font-weight: bold;
                font-size: 16px;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        img_results_layout = QVBoxLayout(img_results_group)
        self.img_results_text = QTextEdit()
        self.img_results_text.setReadOnly(True)
        self.img_results_text.setStyleSheet("""
            QTextEdit {
                background-color: #0e1625;
                color: #e8e8fc;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                padding: 8px;
            }
        """)
        self.img_results_text.setPlaceholderText(
            "Analysis results will appear here...")
        img_results_layout.addWidget(self.img_results_text)

        # Image charts with scrollable area
        image_charts_group = QGroupBox("Image Charts")
        image_charts_group.setStyleSheet("""
            QGroupBox {
                color: #e8e8fc;
                font-weight: bold;
                font-size: 16px;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        # Create scrollable area for charts
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: rgba(69,237,242,0.2);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(69,237,242,0.6);
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(69,237,242,0.8);
            }
            QScrollBar:horizontal {
                background-color: rgba(69,237,242,0.2);
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: rgba(69,237,242,0.6);
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: rgba(69,237,242,0.8);
            }
        """)
        

        img_stats_group = QGroupBox("Statistics")
        img_stats_group.setStyleSheet("""
            QGroupBox {
                color: #e8e8fc;
                font-weight: bold;
                font-size: 16px;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        img_stats_layout = QVBoxLayout(img_stats_group)
        self.img_stats_text = QTextEdit()
        self.img_stats_text.setReadOnly(True)
        self.img_stats_text.setMaximumHeight(150)
        self.img_stats_text.setStyleSheet("""
            QTextEdit {
                background-color: #0e1625;
                color: #e8e8fc;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                padding: 8px;
            }
        """)
        self.img_stats_text.setPlaceholderText(
            "Image statistics will appear here...")
        img_stats_layout.addWidget(self.img_stats_text)

        # Create single scrollable area for all charts
        charts_scroll = QScrollArea()
        charts_scroll.setWidgetResizable(True)
        charts_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        charts_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        charts_scroll.setStyleSheet("""
            QScrollArea {
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                background-color: white;
            }
            QScrollBar:vertical {
                background-color: rgba(69,237,242,0.2);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(69,237,242,0.6);
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(69,237,242,0.8);
            }
            QScrollBar:horizontal {
                background-color: rgba(69,237,242,0.2);
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: rgba(69,237,242,0.6);
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: rgba(69,237,242,0.8);
            }
        """)
        
        # Create container for vertical chart layout
        charts_widget = QWidget()
        charts_widget_layout = QVBoxLayout(charts_widget)
        charts_widget_layout.setSpacing(20)
        charts_widget_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create canvases that fit container width
        self.img_canvas_lsb = FigureCanvas(Figure(figsize=(10, 4), dpi=100))
        self.img_canvas_diff = FigureCanvas(Figure(figsize=(10, 4), dpi=100))
        self.img_canvas_hist = FigureCanvas(Figure(figsize=(10, 4), dpi=100))
        
        # Set size policy to fit container width
        self.img_canvas_lsb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.img_canvas_diff.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.img_canvas_hist.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Set fixed height but let width expand
        self.img_canvas_lsb.setFixedHeight(400)
        self.img_canvas_diff.setFixedHeight(400)
        self.img_canvas_hist.setFixedHeight(400)
        
        # Add charts vertically to the container
        charts_widget_layout.addWidget(self.img_canvas_lsb)
        charts_widget_layout.addWidget(self.img_canvas_diff)
        charts_widget_layout.addWidget(self.img_canvas_hist)
        charts_widget_layout.addStretch()  # Add stretch to push charts to top
        
        # Set the charts widget as the scroll area's widget
        charts_scroll.setWidget(charts_widget)
        
        # Add scroll area to the image charts group
        image_charts_layout = QVBoxLayout(image_charts_group)
        image_charts_layout.addWidget(charts_scroll)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.img_progress_bar)
        
        # Create side-by-side layout for detection results and statistics (50:50)
        results_stats_layout = QHBoxLayout()
        results_stats_layout.setSpacing(20)
        
        # Left side: Detection Results (50%)
        results_container = QWidget()
        results_container.setMaximumWidth(400)  # Limit width for results
        results_vertical_layout = QVBoxLayout(results_container)
        results_vertical_layout.setSpacing(15)
        results_vertical_layout.setContentsMargins(10, 10, 10, 10)
        results_vertical_layout.addWidget(img_results_group)
        results_vertical_layout.addStretch()  # Add stretch to push results to top
        
        # Right side: Statistics (50%)
        stats_container = QWidget()
        stats_container.setMaximumWidth(400)  # Limit width for statistics
        stats_vertical_layout = QVBoxLayout(stats_container)
        stats_vertical_layout.setSpacing(15)
        stats_vertical_layout.setContentsMargins(10, 10, 10, 10)
        stats_vertical_layout.addWidget(img_stats_group)
        stats_vertical_layout.addStretch()  # Add stretch to push stats to top
        
        # Add both containers to results-stats layout
        results_stats_layout.addWidget(results_container)
        results_stats_layout.addWidget(stats_container)
        
        # Add results-stats layout to main layout
        layout.addLayout(results_stats_layout)
        
        # Add charts section with proper header and border
        layout.addWidget(image_charts_group)
        # Export buttons in horizontal layout
        export_buttons_layout = QHBoxLayout()
        export_buttons_layout.setSpacing(10)
        
        export_img_pdf_btn = QPushButton("Export Charts to PDF")
        export_img_pdf_btn.setStyleSheet("""
            QPushButton { 
                background: rgba(147,51,234,0.2);
                color: #9333ea;
                border: 2px solid #9333ea;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { 
                background: rgba(147,51,234,0.4);
                border: 3px solid #9333ea;
                color: #ffffff;
            }
        """)
        export_img_pdf_btn.clicked.connect(self.export_charts_pdf)

        export_img_report_btn = QPushButton("Export Report")
        export_img_report_btn.setStyleSheet("""
            QPushButton { 
                background: rgba(147,51,234,0.2);
                color: #9333ea;
                border: 2px solid #9333ea;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { 
                background: rgba(147,51,234,0.4);
                border: 3px solid #9333ea;
                color: #ffffff;
            }
        """)
        export_img_report_btn.clicked.connect(self.export_report)
        
        export_buttons_layout.addWidget(export_img_pdf_btn)
        export_buttons_layout.addWidget(export_img_report_btn)
        layout.addLayout(export_buttons_layout)
        layout.addStretch()
        return panel

    def _build_audio_controls(self) -> QWidget:
        panel = self._styled_panel()
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Audio Analysis Input")
        f = QFont()
        f.setPointSize(20)
        f.setBold(True)
        title.setFont(f)
        title.setStyleSheet(
            "color: #e8e8fc; margin-bottom: 10px; border: none;")

        audio_group = QGroupBox("Suspicious Audio")
        audio_group.setStyleSheet("""
            QGroupBox {
                color: #e8e8fc;
                font-weight: bold;
                font-size: 16px;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        audio_layout = QVBoxLayout(audio_group)
        self.audio_path = QLineEdit()
        self.audio_path.setPlaceholderText("Select WAV audio to analyze...")
        self.audio_path.setReadOnly(True)
        self.audio_path.setStyleSheet("""
            QLineEdit {
                background-color: #0e1625;
                color: #e8e8fc;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                padding: 8px;
            }
            QLineEdit:focus {
                border: 3px solid rgba(69,237,242,1.0);
            }
        """)
        browse_audio_button = QPushButton("Browse Audio")
        browse_audio_button.setStyleSheet("""
            QPushButton { 
                background: rgba(34,139,34,0.2);
                color: #22c55e;
                border: 2px solid #22c55e;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { 
                background: rgba(34,139,34,0.4);
                border: 3px solid #22c55e;
                color: #ffffff;
            }
        """)
        browse_audio_button.clicked.connect(self.audio_window.browse_audio)
        audio_layout.addWidget(self.audio_path)
        audio_layout.addWidget(browse_audio_button)

        # Audio preview (waveform)
        self.audio_preview = QLabel()
        self.audio_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.audio_preview.setStyleSheet("""
            QLabel {
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                background-color: #0e1625;
                color: #e8e8fc;
                min-height: 100px;
                max-height: 150px;
            }
        """)
        self.audio_preview.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.audio_preview.setText("No audio selected")
        self.audio_preview.setAcceptDrops(True)  # Enable drag and drop directly on the preview
        # Connect drag and drop events
        self.audio_preview.dragEnterEvent = self.audio_preview_drag_enter_event
        self.audio_preview.dragLeaveEvent = self.audio_preview_drag_leave_event
        self.audio_preview.dropEvent = self.audio_preview_drop_event
        audio_layout.addWidget(self.audio_preview)

        audio_method_group = QGroupBox("Audio Analysis Method")
        audio_method_group.setStyleSheet("""
            QGroupBox {
                color: #e8e8fc;
                font-weight: bold;
                font-size: 16px;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        audio_method_layout = QVBoxLayout(audio_method_group)
        self.audio_method_combo = QComboBox()
        self.audio_method_combo.addItems([
            "Audio LSB Analysis", "Audio Chi-Square Test", "Audio Spectral Analysis",
            "Audio Autocorrelation Analysis", "Audio Entropy Analysis", "Audio Comprehensive Analysis", "Audio Advanced Comprehensive"
        ])
        self.audio_method_combo.setStyleSheet("""
            QComboBox { 
                padding: 8px 12px 8px 12px; 
                border: 2px solid #45edf2; 
                border-radius: 8px; 
                background-color: #0e1625;
                color: #e8e8fc;
                font-weight: bold;
            }
            QComboBox:focus { 
                border: 3px solid #45edf2;
                background-color: rgba(69,237,242,0.1);
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 2px solid #45edf2;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                background-color: #45edf2;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #0e1625;
                margin: 0 8px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #45edf2;
                border-radius: 8px;
                background-color: #0e1625;
                color: #e8e8fc;
                selection-background-color: rgba(69,237,242,0.3);
            }
        """)
        self.audio_method_combo.currentTextChanged.connect(
            self.audio_window.on_audio_method_changed)
        audio_method_layout.addWidget(self.audio_method_combo)

        self.aud_analyze_btn = QPushButton("Analyze Audio")
        self.aud_analyze_btn.setStyleSheet("""
            QPushButton { 
                background: rgba(255,140,0,0.2);
                color: #ff8c00;
                border: 2px solid #ff8c00;
                padding: 12px 24px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { 
                background: rgba(255,140,0,0.4);
                border: 3px solid #ff8c00;
                color: #ffffff;
            }
            QPushButton:pressed {
                background: rgba(255,140,0,0.4);
            }
        """)
        self.aud_analyze_btn.clicked.connect(self.audio_window.analyze_audio)

        # Method description
        self.audio_method_description = QLabel()
        self.audio_method_description.setWordWrap(True)
        self.audio_method_description.setStyleSheet("""
            QLabel {
                background-color: #0e1625;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                color: #e8e8fc;
                min-height: 60px;
            }
        """)
        # Initialize with Audio LSB Analysis description
        self.audio_window.update_method_description(
            "Audio LSB Analysis", self.audio_method_description)


        layout.addWidget(title)
        layout.addWidget(audio_group)
        layout.addWidget(audio_method_group)
        layout.addWidget(self.audio_method_description)
        layout.addWidget(self.aud_analyze_btn)
        layout.addStretch()
        return panel

    def _build_audio_results(self) -> QWidget:
        panel = self._styled_panel()
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Create header row with title and sensitivity level
        header_layout = QHBoxLayout()
        
        title = QLabel("Audio Analysis Results")
        f = QFont()
        f.setPointSize(20)
        f.setBold(True)
        title.setFont(f)
        title.setStyleSheet(
            "color: #e8e8fc; margin-bottom: 10px; border: none;")
        
        # Add spacer to push sensitivity to the right
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Create narrow sensitivity level control with border and label
        sensitivity_group = QGroupBox("Sensitivity")
        sensitivity_group.setStyleSheet("""
            QGroupBox {
                color: #e8e8fc;
                font-weight: bold;
                font-size: 12px;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px 0 3px;
            }
        """)
        sensitivity_layout = QVBoxLayout(sensitivity_group)
        sensitivity_layout.setContentsMargins(8, 5, 8, 8)
        
        self.audio_sensitivity_combo = QComboBox()
        self.audio_sensitivity_combo.addItems([
            "🔴 Ultra",
            "🟡 Medium", 
            "🟢 Low"
        ])
        self.audio_sensitivity_combo.setCurrentIndex(0)  # Default to Ultra
        self.audio_sensitivity_combo.setMaximumWidth(140)  # Make it narrow
        self.audio_sensitivity_combo.setStyleSheet("""
            QComboBox {
                background-color: #0e1625;
                color: #e8e8fc;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 6px;
                padding: 4px;
                font-size: 11px;
            }
            QComboBox:focus {
                border: 3px solid rgba(69,237,242,1.0);
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 3px solid #45edf2;
                margin-right: 6px;
            }
            QComboBox QAbstractItemView {
                background-color: #0e1625;
                color: #e8e8fc;
                border: 2px solid rgba(69,237,242,0.6);
                selection-background-color: rgba(69,237,242,0.3);
            }
        """)
        sensitivity_layout.addWidget(self.audio_sensitivity_combo)
        
        header_layout.addWidget(sensitivity_group)

        self.aud_progress_bar = QProgressBar()
        self.aud_progress_bar.setVisible(False)
        self.aud_progress_bar.setStyleSheet("""
            QProgressBar { 
                border: 2px solid rgba(69,237,242,0.6); 
                border-radius: 8px; 
                text-align: center; 
                background-color: #0e1625;
                color: #e8e8fc;
            }
            QProgressBar::chunk { 
                background-color: #45edf2; 
                border-radius: 6px; 
            }
        """)

        aud_results_group = QGroupBox("Detection Results")
        aud_results_group.setStyleSheet("""
            QGroupBox {
                color: #e8e8fc;
                font-weight: bold;
                font-size: 16px;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        aud_results_layout = QVBoxLayout(aud_results_group)
        self.aud_results_text = QTextEdit()
        self.aud_results_text.setReadOnly(True)
        self.aud_results_text.setStyleSheet("""
            QTextEdit {
                background-color: #0e1625;
                color: #e8e8fc;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                padding: 8px;
            }
        """)
        self.aud_results_text.setPlaceholderText(
            "Analysis results will appear here...")
        aud_results_layout.addWidget(self.aud_results_text)

        audio_charts_group = QGroupBox("Audio Charts")
        audio_charts_group.setStyleSheet("""
            QGroupBox {
                color: #e8e8fc;
                font-weight: bold;
                font-size: 16px;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        # Create single scrollable area for all audio charts
        audio_charts_scroll = QScrollArea()
        audio_charts_scroll.setWidgetResizable(True)
        audio_charts_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        audio_charts_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        audio_charts_scroll.setStyleSheet("""
            QScrollArea {
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                background-color: white;
            }
            QScrollBar:vertical {
                background-color: rgba(69,237,242,0.2);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(69,237,242,0.6);
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(69,237,242,0.8);
            }
            QScrollBar:horizontal {
                background-color: rgba(69,237,242,0.2);
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: rgba(69,237,242,0.6);
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: rgba(69,237,242,0.8);
            }
        """)
        
        # Create container for vertical chart layout
        audio_charts_widget = QWidget()
        audio_charts_widget_layout = QVBoxLayout(audio_charts_widget)
        audio_charts_widget_layout.setSpacing(20)
        audio_charts_widget_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create canvases that fit container width (reduced width to prevent cutoff)
        self.aud_canvas_wave = FigureCanvas(Figure(figsize=(8, 4), dpi=100))
        self.aud_canvas_spec = FigureCanvas(Figure(figsize=(8, 4), dpi=100))
        self.aud_canvas_entropy = FigureCanvas(Figure(figsize=(8, 4), dpi=100))
        
        # Set size policy to fit container width
        self.aud_canvas_wave.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.aud_canvas_spec.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.aud_canvas_entropy.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Set fixed height but let width expand
        self.aud_canvas_wave.setFixedHeight(400)
        self.aud_canvas_spec.setFixedHeight(400)
        self.aud_canvas_entropy.setFixedHeight(400)
        
        # Add charts vertically to the container
        audio_charts_widget_layout.addWidget(self.aud_canvas_wave)
        audio_charts_widget_layout.addWidget(self.aud_canvas_spec)
        audio_charts_widget_layout.addWidget(self.aud_canvas_entropy)
        audio_charts_widget_layout.addStretch()  # Add stretch to push charts to top
        
        # Set the charts widget as the scroll area's widget
        audio_charts_scroll.setWidget(audio_charts_widget)
        
        # Add scroll area to the audio charts group
        audio_charts_layout = QVBoxLayout(audio_charts_group)
        audio_charts_layout.addWidget(audio_charts_scroll)

        aud_stats_group = QGroupBox("Statistics")
        aud_stats_group.setStyleSheet("""
            QGroupBox {
                color: #e8e8fc;
                font-weight: bold;
                font-size: 16px;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        aud_stats_layout = QVBoxLayout(aud_stats_group)
        self.aud_stats_text = QTextEdit()
        self.aud_stats_text.setReadOnly(True)
        self.aud_stats_text.setMaximumHeight(150)
        self.aud_stats_text.setStyleSheet("""
            QTextEdit {
                background-color: #0e1625;
                color: #e8e8fc;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                padding: 8px;
            }
        """)
        self.aud_stats_text.setPlaceholderText(
            "Audio statistics will appear here...")
        aud_stats_layout.addWidget(self.aud_stats_text)

        # Export buttons in horizontal layout
        export_buttons_layout = QHBoxLayout()
        export_buttons_layout.setSpacing(10)
        
        export_aud_pdf_btn = QPushButton("Export Charts to PDF")
        export_aud_pdf_btn.setStyleSheet("""
            QPushButton { 
                background: rgba(147,51,234,0.2);
                color: #9333ea;
                border: 2px solid #9333ea;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { 
                background: rgba(147,51,234,0.4);
                border: 3px solid #9333ea;
                color: #ffffff;
            }
        """)
        export_aud_pdf_btn.clicked.connect(self.export_charts_pdf)

        export_button = QPushButton("Export Report")
        export_button.setStyleSheet("""
            QPushButton { 
                background: rgba(147,51,234,0.2);
                color: #9333ea;
                border: 2px solid #9333ea;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { 
                background: rgba(147,51,234,0.4);
                border: 3px solid #9333ea;
                color: #ffffff;
            }
        """)
        export_button.clicked.connect(self.export_report)
        
        export_buttons_layout.addWidget(export_aud_pdf_btn)
        export_buttons_layout.addWidget(export_button)

        layout.addLayout(header_layout)
        layout.addWidget(self.aud_progress_bar)
        
        # Create side-by-side layout for detection results and statistics (50:50)
        results_stats_layout = QHBoxLayout()
        results_stats_layout.setSpacing(20)
        
        # Left side: Detection Results (50%)
        results_container = QWidget()
        results_container.setMaximumWidth(400)  # Limit width for results
        results_vertical_layout = QVBoxLayout(results_container)
        results_vertical_layout.setSpacing(15)
        results_vertical_layout.setContentsMargins(10, 10, 10, 10)
        results_vertical_layout.addWidget(aud_results_group)
        results_vertical_layout.addStretch()  # Add stretch to push results to top
        
        # Right side: Statistics (50%)
        stats_container = QWidget()
        stats_container.setMaximumWidth(400)  # Limit width for statistics
        stats_vertical_layout = QVBoxLayout(stats_container)
        stats_vertical_layout.setSpacing(15)
        stats_vertical_layout.setContentsMargins(10, 10, 10, 10)
        stats_vertical_layout.addWidget(aud_stats_group)
        stats_vertical_layout.addStretch()  # Add stretch to push stats to top
        
        # Add both containers to results-stats layout
        results_stats_layout.addWidget(results_container)
        results_stats_layout.addWidget(stats_container)
        
        # Add results-stats layout to main layout
        layout.addLayout(results_stats_layout)
        
        # Add charts section with proper header and border
        layout.addWidget(audio_charts_group)
        layout.addLayout(export_buttons_layout)
        layout.addStretch()
        return panel

    def _build_video_controls(self) -> QWidget:
        panel = self._styled_panel()
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Video Analysis Input")
        f = QFont()
        f.setPointSize(20)
        f.setBold(True)
        title.setFont(f)
        title.setStyleSheet(
            "color: #e8e8fc; margin-bottom: 10px; border: none;")

        video_group = QGroupBox("Suspicious Video")
        video_group.setStyleSheet("""
            QGroupBox {
                color: #e8e8fc;
                font-weight: bold;
                font-size: 16px;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        video_layout = QVBoxLayout(video_group)
        self.video_path = QLineEdit()
        self.video_path.setPlaceholderText("Select video to analyze...")
        self.video_path.setReadOnly(True)
        self.video_path.setStyleSheet("""
            QLineEdit {
                background-color: #0e1625;
                color: #e8e8fc;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                padding: 8px;
            }
            QLineEdit:focus {
                border: 3px solid rgba(69,237,242,1.0);
            }
        """)
        browse_video_button = QPushButton("Browse Video")
        browse_video_button.setStyleSheet("""
            QPushButton { 
                background: rgba(34,139,34,0.2);
                color: #22c55e;
                border: 2px solid #22c55e;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { 
                background: rgba(34,139,34,0.4);
                border: 3px solid #22c55e;
                color: #ffffff;
            }
        """)
        browse_video_button.clicked.connect(self.video_window.browse_video)
        video_layout.addWidget(self.video_path)
        video_layout.addWidget(browse_video_button)

        # Video preview
        self.video_preview = QLabel()
        self.video_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_preview.setStyleSheet("""
            QLabel {
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                background-color: #0e1625;
                color: #e8e8fc;
                min-height: 120px;
                max-height: 180px;
            }
        """)
        self.video_preview.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.video_preview.setText("No video selected")
        self.video_preview.setScaledContents(False)
        self.video_preview.setAcceptDrops(True)  # Enable drag and drop directly on the preview
        # Connect drag and drop events
        self.video_preview.dragEnterEvent = self.video_preview_drag_enter_event
        self.video_preview.dragLeaveEvent = self.video_preview_drag_leave_event
        self.video_preview.dropEvent = self.video_preview_drop_event
        video_layout.addWidget(self.video_preview)

        video_method_group = QGroupBox("Video Analysis Method")
        video_method_group.setStyleSheet("""
            QGroupBox {
                color: #e8e8fc;
                font-weight: bold;
                font-size: 16px;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        video_method_group = QGroupBox("Video Analysis Method")
        video_method_group.setStyleSheet("""
            QGroupBox {
                color: #e8e8fc;
                font-weight: bold;
                font-size: 16px;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        video_method_layout = QVBoxLayout(video_method_group)
        self.video_method_combo = QComboBox()
        self.video_method_combo.addItems([
            "Video LSB Analysis", "Video Frame Analysis", "Video Motion Analysis",
            "Video Advanced Comprehensive"
        ])
        self.video_method_combo.setStyleSheet("""
            QComboBox { 
                padding: 8px 12px 8px 12px; 
                border: 2px solid #45edf2; 
                border-radius: 8px; 
                background-color: #0e1625;
                color: #e8e8fc;
                font-weight: bold;
            }
            QComboBox:focus { 
                border: 3px solid #45edf2;
                background-color: rgba(69,237,242,0.1);
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 2px solid #45edf2;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                background-color: #45edf2;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #0e1625;
                margin: 0 8px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #45edf2;
                border-radius: 8px;
                background-color: #0e1625;
                color: #e8e8fc;
                selection-background-color: rgba(69,237,242,0.3);
            }
        """)
        self.video_method_combo.currentTextChanged.connect(
            self.video_window.on_video_method_changed)
        video_method_layout.addWidget(self.video_method_combo)

        # Method description
        self.video_method_description = QLabel()
        self.video_method_description.setWordWrap(True)
        self.video_method_description.setStyleSheet("""
            QLabel {
                background-color: #0e1625;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                color: #e8e8fc;
                min-height: 60px;
            }
        """)
        # Initialize with Video LSB Analysis description
        self.video_window.update_method_description(
            "Video LSB Analysis", self.video_method_description)


        self.vid_analyze_btn = QPushButton("Analyze Video")
        self.vid_analyze_btn.setStyleSheet("""
            QPushButton { 
                background: rgba(255,140,0,0.2);
                color: #ff8c00;
                border: 2px solid #ff8c00;
                padding: 12px 24px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { 
                background: rgba(255,140,0,0.4);
                border: 3px solid #ff8c00;
                color: #ffffff;
            }
            QPushButton:pressed {
                background: rgba(255,140,0,0.4);
            }
        """)
        self.vid_analyze_btn.clicked.connect(self.video_window.analyze_video)

        layout.addWidget(title)
        layout.addWidget(video_group)
        layout.addWidget(video_method_group)
        layout.addWidget(self.video_method_description)
        layout.addWidget(self.vid_analyze_btn)
        layout.addStretch()
        return panel

    def _build_video_results(self) -> QWidget:
        panel = self._styled_panel()
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Create header row with title and sensitivity level
        header_layout = QHBoxLayout()
        
        title = QLabel("Video Analysis Results")
        f = QFont()
        f.setPointSize(20)
        f.setBold(True)
        title.setFont(f)
        title.setStyleSheet(
            "color: #e8e8fc; margin-bottom: 10px; border: none;")
        
        # Add spacer to push sensitivity to the right
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Create narrow sensitivity level control with border and label
        sensitivity_group = QGroupBox("Sensitivity")
        sensitivity_group.setStyleSheet("""
            QGroupBox {
                color: #e8e8fc;
                font-weight: bold;
                font-size: 12px;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px 0 3px;
            }
        """)
        sensitivity_layout = QVBoxLayout(sensitivity_group)
        sensitivity_layout.setContentsMargins(8, 5, 8, 8)
        
        self.video_sensitivity_combo = QComboBox()
        self.video_sensitivity_combo.addItems([
            "🔴 Ultra",
            "🟡 Medium", 
            "🟢 Low"
        ])
        self.video_sensitivity_combo.setCurrentIndex(0)  # Default to Ultra
        self.video_sensitivity_combo.setMaximumWidth(140)  # Make it narrow
        self.video_sensitivity_combo.setStyleSheet("""
            QComboBox {
                background-color: #0e1625;
                color: #e8e8fc;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 6px;
                padding: 4px;
                font-size: 11px;
            }
            QComboBox:focus {
                border: 3px solid rgba(69,237,242,1.0);
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 3px solid #45edf2;
                margin-right: 6px;
            }
            QComboBox QAbstractItemView {
                background-color: #0e1625;
                color: #e8e8fc;
                border: 2px solid rgba(69,237,242,0.6);
                selection-background-color: rgba(69,237,242,0.3);
            }
        """)
        sensitivity_layout.addWidget(self.video_sensitivity_combo)
        
        header_layout.addWidget(sensitivity_group)

        self.vid_progress_bar = QProgressBar()
        self.vid_progress_bar.setVisible(False)
        self.vid_progress_bar.setStyleSheet("""
            QProgressBar { 
                border: 2px solid rgba(69,237,242,0.6); 
                border-radius: 8px; 
                text-align: center; 
                background-color: #0e1625;
                color: #e8e8fc;
            }
            QProgressBar::chunk { 
                background-color: #45edf2; 
                border-radius: 6px; 
            }
        """)

        vid_results_group = QGroupBox("Detection Results")
        vid_results_group.setStyleSheet("""
            QGroupBox {
                color: #e8e8fc;
                font-weight: bold;
                font-size: 16px;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        vid_results_layout = QVBoxLayout(vid_results_group)
        self.vid_results_text = QTextEdit()
        self.vid_results_text.setReadOnly(True)
        self.vid_results_text.setStyleSheet("""
            QTextEdit {
                background-color: #0e1625;
                color: #e8e8fc;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                padding: 8px;
            }
        """)
        self.vid_results_text.setPlaceholderText(
            "Analysis results will appear here...")
        vid_results_layout.addWidget(self.vid_results_text)

        # Video charts
        video_charts_group = QGroupBox("Video Charts")
        video_charts_group.setStyleSheet("""
            QGroupBox {
                color: #e8e8fc;
                font-weight: bold;
                font-size: 16px;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        # Create single scrollable area for all video charts
        video_charts_scroll = QScrollArea()
        video_charts_scroll.setWidgetResizable(True)
        video_charts_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        video_charts_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        video_charts_scroll.setStyleSheet("""
            QScrollArea {
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                background-color: white;
            }
            QScrollBar:vertical {
                background-color: rgba(69,237,242,0.2);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(69,237,242,0.6);
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(69,237,242,0.8);
            }
            QScrollBar:horizontal {
                background-color: rgba(69,237,242,0.2);
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: rgba(69,237,242,0.6);
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: rgba(69,237,242,0.8);
            }
        """)
        
        # Create container for vertical chart layout
        video_charts_widget = QWidget()
        video_charts_widget_layout = QVBoxLayout(video_charts_widget)
        video_charts_widget_layout.setSpacing(20)
        video_charts_widget_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create canvases that fit container width
        self.vid_canvas_frame = FigureCanvas(Figure(figsize=(10, 4), dpi=100))
        self.vid_canvas_motion = FigureCanvas(Figure(figsize=(10, 4), dpi=100))
        self.vid_canvas_lsb = FigureCanvas(Figure(figsize=(10, 4), dpi=100))
        
        # Set size policy to fit container width
        self.vid_canvas_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.vid_canvas_motion.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.vid_canvas_lsb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Set fixed height but let width expand
        self.vid_canvas_frame.setFixedHeight(400)
        self.vid_canvas_motion.setFixedHeight(400)
        self.vid_canvas_lsb.setFixedHeight(400)
        
        # Add charts vertically to the container
        video_charts_widget_layout.addWidget(self.vid_canvas_frame)
        video_charts_widget_layout.addWidget(self.vid_canvas_motion)
        video_charts_widget_layout.addWidget(self.vid_canvas_lsb)
        video_charts_widget_layout.addStretch()  # Add stretch to push charts to top
        
        # Set the charts widget as the scroll area's widget
        video_charts_scroll.setWidget(video_charts_widget)
        
        # Add scroll area to the video charts group
        video_charts_layout = QVBoxLayout(video_charts_group)
        video_charts_layout.addWidget(video_charts_scroll)

        vid_stats_group = QGroupBox("Statistics")
        vid_stats_group.setStyleSheet("""
            QGroupBox {
                color: #e8e8fc;
                font-weight: bold;
                font-size: 16px;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        vid_stats_layout = QVBoxLayout(vid_stats_group)
        self.vid_stats_text = QTextEdit()
        self.vid_stats_text.setReadOnly(True)
        self.vid_stats_text.setMaximumHeight(150)
        self.vid_stats_text.setStyleSheet("""
            QTextEdit {
                background-color: #0e1625;
                color: #e8e8fc;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                padding: 8px;
            }
        """)
        self.vid_stats_text.setPlaceholderText(
            "Video statistics will appear here...")
        vid_stats_layout.addWidget(self.vid_stats_text)

        # Export buttons in horizontal layout
        export_buttons_layout = QHBoxLayout()
        export_buttons_layout.setSpacing(10)
        
        export_vid_pdf_btn = QPushButton("Export Charts to PDF")
        export_vid_pdf_btn.setStyleSheet("""
            QPushButton { 
                background: rgba(147,51,234,0.2);
                color: #9333ea;
                border: 2px solid #9333ea;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { 
                background: rgba(147,51,234,0.4);
                border: 3px solid #9333ea;
                color: #ffffff;
            }
        """)
        export_vid_pdf_btn.clicked.connect(self.export_charts_pdf)

        export_vid_report_btn = QPushButton("Export Report")
        export_vid_report_btn.setStyleSheet("""
            QPushButton { 
                background: rgba(147,51,234,0.2);
                color: #9333ea;
                border: 2px solid #9333ea;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { 
                background: rgba(147,51,234,0.4);
                border: 3px solid #9333ea;
                color: #ffffff;
            }
        """)
        export_vid_report_btn.clicked.connect(self.export_report)
        
        export_buttons_layout.addWidget(export_vid_pdf_btn)
        export_buttons_layout.addWidget(export_vid_report_btn)

        layout.addLayout(header_layout)
        layout.addWidget(self.vid_progress_bar)
        
        # Create side-by-side layout for detection results and statistics (50:50)
        results_stats_layout = QHBoxLayout()
        results_stats_layout.setSpacing(20)
        
        # Left side: Detection Results (50%)
        results_container = QWidget()
        results_container.setMaximumWidth(400)  # Limit width for results
        results_vertical_layout = QVBoxLayout(results_container)
        results_vertical_layout.setSpacing(15)
        results_vertical_layout.setContentsMargins(10, 10, 10, 10)
        results_vertical_layout.addWidget(vid_results_group)
        results_vertical_layout.addStretch()  # Add stretch to push results to top
        
        # Right side: Statistics (50%)
        stats_container = QWidget()
        stats_container.setMaximumWidth(400)  # Limit width for statistics
        stats_vertical_layout = QVBoxLayout(stats_container)
        stats_vertical_layout.setSpacing(15)
        stats_vertical_layout.setContentsMargins(10, 10, 10, 10)
        stats_vertical_layout.addWidget(vid_stats_group)
        stats_vertical_layout.addStretch()  # Add stretch to push stats to top
        
        # Add both containers to results-stats layout
        results_stats_layout.addWidget(results_container)
        results_stats_layout.addWidget(stats_container)
        
        # Add results-stats layout to main layout
        layout.addLayout(results_stats_layout)
        
        # Add charts section with proper header and border
        layout.addWidget(video_charts_group)
        layout.addLayout(export_buttons_layout)
        layout.addStretch()
        
        # Drag and drop is now handled directly by preview widgets
        
        return panel


    def create_shadow_effect(self):
        """Create an enhanced shadow effect for panels"""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(35)  # Increased blur for stronger glow
        shadow.setXOffset(0)
        shadow.setYOffset(8)  # Increased offset for more depth
        # Enhanced cyan glow with higher opacity
        # Doubled opacity for stronger effect
        shadow.setColor(QColor(69, 237, 242, 80))
        return shadow

    def update_method_description(self, method_name: str, description_widget: QLabel):
        """Update the method description based on selected method"""
        description = self.method_descriptions.get(
            method_name, "No description available for this method.")
        description_widget.setText(description)

    def get_sensitivity_level(self, media_type: str) -> str:
        """Get the selected sensitivity level for the specified media type"""
        if media_type == "image":
            combo = self.image_sensitivity_combo
        elif media_type == "audio":
            combo = self.audio_sensitivity_combo
        elif media_type == "video":
            combo = self.video_sensitivity_combo
        else:
            return "ultra"  # Default fallback
        
        current_text = combo.currentText()
        if "Ultra" in current_text:
            return "ultra"
        elif "Medium" in current_text:
            return "medium"
        elif "Low" in current_text:
            return "low"
        else:
            return "ultra"  # Default fallback

    def export_report(self):
        """Export analysis report"""
        # Generate timestamp string
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"steganalysis_report_{timestamp}.txt"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Analysis Report", default_name,
            "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            success = self.machine.export_report(file_path)
            if success:
                # Report exported successfully - could show message in appropriate tab
                pass
            else:
                # Export failed - could show error message in appropriate tab
                pass

    def on_image_files_dropped(self, file_paths):
        """Handle dropped image files"""
        if file_paths:
            file_path = file_paths[0]  # Take the first file
            self.image_path.setText(file_path)  # Set the path for compatibility
            if self.machine.set_image(file_path):
                self.image_window.create_image_preview(file_path)
                if hasattr(self, 'img_results_text'):
                    self.img_results_text.append(f"Image selected: {file_path}")
            else:
                if hasattr(self, 'img_results_text'):
                    self.img_results_text.append(f"Error loading image: {file_path}")

    def image_preview_drag_enter_event(self, event):
        """Handle drag enter event for image preview"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp']:
                        event.acceptProposedAction()
                        # Change text and add visual feedback
                        self.image_preview.setText("Drop here!")
                        self.image_preview.setStyleSheet("""
                            QLabel {
                                border: 4px dashed #45edf2;
                                border-radius: 8px;
                                background-color: rgba(69,237,242,0.4);
                                color: #e8e8fc;
                                min-height: 150px;
                                max-height: 200px;
                            }
                        """)
                        return
        event.ignore()

    def image_preview_drag_leave_event(self, event):
        """Handle drag leave event for image preview"""
        # Restore original text and remove visual feedback
        self.image_preview.setText("No image selected")
        self.image_preview.setStyleSheet("""
            QLabel {
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                background-color: #0e1625;
                color: #e8e8fc;
                min-height: 150px;
                max-height: 200px;
            }
        """)
        event.accept()

    def image_preview_drop_event(self, event):
        """Handle drop event for image preview"""
        # Remove visual feedback
        self.image_preview.setStyleSheet("""
            QLabel {
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                background-color: #0e1625;
                color: #e8e8fc;
                min-height: 150px;
                max-height: 200px;
            }
        """)
        
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            valid_files = []
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp']:
                        valid_files.append(file_path)
            
            if valid_files:
                event.acceptProposedAction()
                self.on_image_files_dropped(valid_files)
            else:
                event.ignore()
        else:
            event.ignore()

    def on_audio_files_dropped(self, file_paths):
        """Handle dropped audio files"""
        if file_paths:
            file_path = file_paths[0]  # Take the first file
            self.audio_path.setText(file_path)  # Set the path for compatibility
            if self.machine.set_audio(file_path):
                self.audio_window.create_audio_preview(file_path)
                if hasattr(self, 'aud_results_text'):
                    self.aud_results_text.append(f"Audio selected: {file_path}")
            else:
                if hasattr(self, 'aud_results_text'):
                    self.aud_results_text.append(f"Error loading audio: {file_path}")

    def audio_preview_drag_enter_event(self, event):
        """Handle drag enter event for audio preview"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext in ['.wav', '.mp3', '.flac', '.aac', '.ogg', '.m4a']:
                        event.acceptProposedAction()
                        # Change text and add visual feedback
                        self.audio_preview.setText("Drop here!")
                        self.audio_preview.setStyleSheet("""
                            QLabel {
                                border: 4px dashed #45edf2;
                                border-radius: 8px;
                                background-color: rgba(69,237,242,0.4);
                                color: #e8e8fc;
                                min-height: 100px;
                                max-height: 150px;
                            }
                        """)
                        return
        event.ignore()

    def audio_preview_drag_leave_event(self, event):
        """Handle drag leave event for audio preview"""
        # Restore original text and remove visual feedback
        self.audio_preview.setText("No audio selected")
        self.audio_preview.setStyleSheet("""
            QLabel {
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                background-color: #0e1625;
                color: #e8e8fc;
                min-height: 100px;
                max-height: 150px;
            }
        """)
        event.accept()

    def audio_preview_drop_event(self, event):
        """Handle drop event for audio preview"""
        # Remove visual feedback
        self.audio_preview.setStyleSheet("""
            QLabel {
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                background-color: #0e1625;
                color: #e8e8fc;
                min-height: 100px;
                max-height: 150px;
            }
        """)
        
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            valid_files = []
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext in ['.wav', '.mp3', '.flac', '.aac', '.ogg', '.m4a']:
                        valid_files.append(file_path)
            
            if valid_files:
                event.acceptProposedAction()
                self.on_audio_files_dropped(valid_files)
            else:
                event.ignore()
        else:
            event.ignore()

    def on_video_files_dropped(self, file_paths):
        """Handle dropped video files"""
        if file_paths:
            file_path = file_paths[0]  # Take the first file
            self.video_path.setText(file_path)  # Set the path for compatibility
            if self.machine.set_video(file_path):
                self.video_window.create_video_preview(file_path)
                if hasattr(self, 'vid_results_text'):
                    self.vid_results_text.append(f"Video selected: {file_path}")
            else:
                if hasattr(self, 'vid_results_text'):
                    self.vid_results_text.append(f"Error loading video: {file_path}")

    def video_preview_drag_enter_event(self, event):
        """Handle drag enter event for video preview"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']:
                        event.acceptProposedAction()
                        # Change text and add visual feedback
                        self.video_preview.setText("Drop here!")
                        self.video_preview.setStyleSheet("""
                            QLabel {
                                border: 4px dashed #45edf2;
                                border-radius: 8px;
                                background-color: rgba(69,237,242,0.4);
                                color: #e8e8fc;
                                min-height: 120px;
                                max-height: 180px;
                            }
                        """)
                        return
        event.ignore()

    def video_preview_drag_leave_event(self, event):
        """Handle drag leave event for video preview"""
        # Restore original text and remove visual feedback
        self.video_preview.setText("No video selected")
        self.video_preview.setStyleSheet("""
            QLabel {
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                background-color: #0e1625;
                color: #e8e8fc;
                min-height: 120px;
                max-height: 180px;
            }
        """)
        event.accept()

    def video_preview_drop_event(self, event):
        """Handle drop event for video preview"""
        # Remove visual feedback
        self.video_preview.setStyleSheet("""
            QLabel {
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 8px;
                background-color: #0e1625;
                color: #e8e8fc;
                min-height: 120px;
                max-height: 180px;
            }
        """)
        
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            valid_files = []
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']:
                        valid_files.append(file_path)
            
            if valid_files:
                event.acceptProposedAction()
                self.on_video_files_dropped(valid_files)
            else:
                event.ignore()
        else:
            event.ignore()

    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        # Drag and drop is now handled directly by preview widgets, no positioning needed

    def go_back(self):
        """Go back to main window"""
        # Clean up machine resources
        self.machine.cleanup()

        from gui.main_window import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()

    # ======== Export charts to PDF ========

    def export_charts_pdf(self):
        """Export currently displayed charts (image and/or audio) to a multi-page high-res PDF."""
        # Ask user where to save
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"steganalysis_charts_{timestamp}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Charts to PDF", default_name, "PDF Files (*.pdf)")
        if not file_path:
            return

        try:
            with PdfPages(file_path) as pdf:
                # Cover page with summary text
                fig_cover = Figure(figsize=(8.27, 11.69),
                                   dpi=200)  # A4 portrait
                axc = fig_cover.subplots(1, 1)
                axc.axis('off')
                lines = []
                # Basic summary details - show only the last analyzed file
                if hasattr(self.machine, 'last_analyzed_path') and self.machine.last_analyzed_path:
                    file_path = self.machine.last_analyzed_path
                    file_ext = file_path.lower().split('.')[-1] if '.' in file_path else ''
                    file_type = file_ext.upper()
                    lines.append(f"{file_type}: {file_path}")
                # Get confidence from the main machine (which delegates to specialized machines)
                confidence = self.machine.get_confidence_level()
                lines.append(f"Confidence: {confidence:.2%}")
                y = 0.95
                axc.text(0.05, y, "Steganalysis Charts", fontsize=16,
                         weight='bold', transform=axc.transAxes)
                y -= 0.05
                for s in lines:
                    axc.text(0.05, y, s, fontsize=10, transform=axc.transAxes)
                    y -= 0.035
                pdf.savefig(fig_cover, bbox_inches='tight')

                # Image page: LSB + Diff side-by-side
                if hasattr(self, 'img_canvas_lsb') and hasattr(self, 'img_canvas_diff'):
                    fig_img = Figure(figsize=(11.69, 8.27),
                                     dpi=200)  # A4 landscape
                    ax1, ax2 = fig_img.subplots(1, 2)
                    # Recompute from machine to ensure high-res
                    img = self.machine.image_machine.image_array
                    if img is not None:
                        if img.dtype != np.uint8:
                            img = img.astype(np.uint8)
                        lsb = (img & 1)
                        if lsb.ndim == 3:
                            lsb_vis = (np.mean(lsb, axis=2)
                                       * 255).astype(np.uint8)
                        else:
                            lsb_vis = (lsb * 255).astype(np.uint8)
                        ax1.imshow(lsb_vis, cmap='gray')
                        ax1.set_title('LSB Plane', fontsize=14)
                        ax1.axis('off')
                        blurred = cv2.GaussianBlur(img, (5, 5), 0)
                        residual = cv2.absdiff(img, blurred)
                        residual_gray = cv2.cvtColor(
                            residual, cv2.COLOR_BGR2GRAY) if residual.ndim == 3 else residual
                        ax2.imshow(residual_gray, cmap='inferno')
                        ax2.set_title('Difference Map', fontsize=14)
                        ax2.axis('off')
                        pdf.savefig(fig_img, bbox_inches='tight')

                    # Histogram page full width
                    fig_hist = Figure(figsize=(11.69, 8.27), dpi=200)
                    axh = fig_hist.subplots(1, 1)
                    if img is not None:
                        colors = ('r', 'g', 'b') if (
                            img.ndim == 3 and img.shape[2] == 3) else ('k',)
                        if len(colors) == 3:
                            for i, c in enumerate(colors):
                                hist = cv2.calcHist([img], [i], None, [
                                                    256], [0, 256]).flatten()
                                axh.plot(hist, color=c,
                                         label=f'Channel {c.upper()}')
                        else:
                            hist, _ = np.histogram(
                                img.flatten(), bins=256, range=(0, 256))
                            axh.plot(hist, color='k', label='Gray')
                        axh.set_title('Histogram', fontsize=16)
                        axh.set_xlabel('Pixel value', fontsize=12)
                        axh.set_ylabel('Count', fontsize=12)
                        axh.set_xlim(0, 255)
                        axh.legend(loc='upper right', fontsize=10)
                        axh.grid(True, alpha=0.2)
                        pdf.savefig(fig_hist, bbox_inches='tight')

                # Audio page(s): waveform + spectrogram + entropy
                samples = getattr(self.machine.audio_machine, 'audio_samples', None)
                sr = getattr(self.machine.audio_machine, 'audio_sample_rate', None)
                if samples is not None and sr:
                    if samples.ndim == 2:
                        data = samples[:, 0].astype(np.float32)
                    else:
                        data = samples.astype(np.float32)

                    # Waveform page
                    fig_wave = Figure(figsize=(11.69, 8.27), dpi=200)
                    axw = fig_wave.subplots(1, 1)
                    t = np.arange(len(data)) / float(sr)
                    axw.plot(t, data, color='#34495e', linewidth=0.7)
                    axw.set_title('Waveform', fontsize=16)
                    axw.set_xlabel('Time (s)', fontsize=12)
                    axw.set_ylabel('Amplitude', fontsize=12)
                    axw.grid(True, alpha=0.2)
                    pdf.savefig(fig_wave, bbox_inches='tight')

                    # Spectrogram page
                    fig_spec = Figure(figsize=(11.69, 8.27), dpi=200)
                    axs = fig_spec.subplots(1, 1)
                    nfft = 1024
                    noverlap = 512
                    axs.specgram(data, NFFT=nfft, Fs=sr,
                                 noverlap=noverlap, cmap='magma')
                    axs.set_title('Spectrogram', fontsize=16)
                    axs.set_xlabel('Time (s)', fontsize=12)
                    axs.set_ylabel('Frequency (Hz)', fontsize=12)
                    pdf.savefig(fig_spec, bbox_inches='tight')

                    # Entropy page
                    fig_ent = Figure(figsize=(11.69, 8.27), dpi=200)
                    axe = fig_ent.subplots(1, 1)
                    x = data - np.min(data)
                    denom = (np.max(x) - np.min(x) + 1e-9)
                    x = (x / denom * 255.0).astype(np.uint8)
                    win = max(int(sr * 0.05), 256)
                    hop = max(win // 2, 128)
                    ent_values = []
                    times = []
                    for start in range(0, len(x) - win + 1, hop):
                        seg = x[start:start + win]
                        hist, _ = np.histogram(seg, bins=256, range=(0, 256))
                        p = hist.astype(np.float32)
                        p = p / max(np.sum(p), 1.0)
                        p = p[p > 0]
                        ent = float(-np.sum(p * np.log2(p)))
                        ent_values.append(ent)
                        times.append(start / float(sr))
                    axe.plot(times, ent_values, color='#8e44ad', linewidth=1.0)
                    axe.set_title('Short-time Entropy', fontsize=16)
                    axe.set_xlabel('Time (s)', fontsize=12)
                    axe.set_ylabel('Entropy (bits)', fontsize=12)
                    axe.grid(True, alpha=0.2)
                    pdf.savefig(fig_ent, bbox_inches='tight')

                # Video page(s): frame analysis + motion analysis + LSB analysis
                frames = getattr(self.machine.video_machine, 'video_frames', None)
                if frames is not None and len(frames) > 0:
                    # Sample frames for analysis (max 20 frames)
                    sample_frames = frames[::max(1, len(frames)//20)]

                    # Frame Statistics page
                    fig_frame = Figure(figsize=(11.69, 8.27), dpi=200)
                    ax_frame = fig_frame.subplots(1, 1)

                    frame_stats = []
                    for i, frame in enumerate(sample_frames):
                        if frame.ndim == 3:
                            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                        else:
                            gray = frame
                        mean_val = np.mean(gray)
                        std_val = np.std(gray)
                        frame_stats.append((i, mean_val, std_val))

                    frame_nums, means, stds = zip(*frame_stats)
                    ax_frame.plot(frame_nums, means, 'b-',
                                  label='Mean', linewidth=2)
                    ax_frame.plot(frame_nums, stds, 'r-',
                                  label='Std Dev', linewidth=2)
                    ax_frame.set_title('Video Frame Statistics', fontsize=16)
                    ax_frame.set_xlabel('Frame Number', fontsize=12)
                    ax_frame.set_ylabel('Pixel Value', fontsize=12)
                    ax_frame.legend()
                    ax_frame.grid(True, alpha=0.2)
                    pdf.savefig(fig_frame, bbox_inches='tight')

                    # Motion Analysis page
                    fig_motion = Figure(figsize=(11.69, 8.27), dpi=200)
                    ax_motion = fig_motion.subplots(1, 1)

                    motion_diffs = []
                    for i in range(1, len(sample_frames)):
                        diff = np.mean(np.abs(sample_frames[i].astype(np.float32) -
                                              sample_frames[i-1].astype(np.float32)))
                        motion_diffs.append((i, diff))

                    if motion_diffs:
                        frame_nums, diffs = zip(*motion_diffs)
                        ax_motion.plot(frame_nums, diffs, 'g-', linewidth=2)
                        ax_motion.set_title(
                            'Video Motion Analysis', fontsize=16)
                        ax_motion.set_xlabel('Frame Number', fontsize=12)
                        ax_motion.set_ylabel('Motion Difference', fontsize=12)
                        ax_motion.grid(True, alpha=0.2)
                        pdf.savefig(fig_motion, bbox_inches='tight')

                    # LSB Analysis page
                    fig_lsb = Figure(figsize=(11.69, 8.27), dpi=200)
                    ax_lsb = fig_lsb.subplots(1, 1)

                    lsb_ratios = []
                    for i, frame in enumerate(sample_frames):
                        if frame.ndim == 3:
                            r = frame[:, :, 0]
                        else:
                            r = frame
                        lsb_ratio = np.mean(r & 1)
                        lsb_ratios.append((i, lsb_ratio))

                    frame_nums, ratios = zip(*lsb_ratios)
                    ax_lsb.plot(frame_nums, ratios, 'm-', linewidth=2)
                    ax_lsb.axhline(y=0.5, color='r',
                                   linestyle='--', label='Expected (0.5)')
                    ax_lsb.set_title('Video LSB Analysis', fontsize=16)
                    ax_lsb.set_xlabel('Frame Number', fontsize=12)
                    ax_lsb.set_ylabel('LSB Ratio', fontsize=12)
                    ax_lsb.legend()
                    ax_lsb.grid(True, alpha=0.2)
                    pdf.savefig(fig_lsb, bbox_inches='tight')

            # Notify success
            if hasattr(self, 'img_results_text'):
                self.img_results_text.append(
                    f"Charts exported to PDF: {file_path}")
            if hasattr(self, 'aud_results_text'):
                self.aud_results_text.append(
                    f"Charts exported to PDF: {file_path}")
            if hasattr(self, 'vid_results_text'):
                self.vid_results_text.append(
                    f"Charts exported to PDF: {file_path}")
        except Exception as e:
            if hasattr(self, 'img_results_text'):
                self.img_results_text.append(f"Error exporting charts: {e}")
            if hasattr(self, 'aud_results_text'):
                self.aud_results_text.append(f"Error exporting charts: {e}")
            if hasattr(self, 'vid_results_text'):
                self.vid_results_text.append(f"Error exporting charts: {e}")
