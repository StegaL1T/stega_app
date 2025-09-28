# gui/stega_decode_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QFileDialog, QTextEdit,
                             QGroupBox, QLineEdit, QSlider, QToolTip, QApplication)
from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QDragEnterEvent, QDropEvent, QCursor
import os
import math
import random


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


class MediaDropWidget(QFrame):
    """Custom widget for drag and drop media upload with interactive previews"""

    media_loaded = pyqtSignal(str, str)  # file_path, media_type

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(300)
        self.media_type = None
        self.media_path = None
        self.preview_widget = None

        self.setup_ui()

    def setup_ui(self):
        """Setup the drag and drop interface"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # Drop zone
        self.drop_zone = QLabel()
        self.drop_zone.setMinimumHeight(200)
        self.drop_zone.setStyleSheet("""
            QLabel {
                border: 3px dashed rgba(69,237,242,0.6);
                border-radius: 15px;
                background-color: rgba(14,22,37,0.8);
                color: #e8e8fc;
                font-size: 16px;
            }
            QLabel:hover {
                border-color: #45edf2;
                background-color: rgba(69,237,242,0.1);
            }
        """)
        self.drop_zone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_zone.setText(
            "Drag & Drop Steganographic Media Here\n\nSupported: Images, Audio, Video")

        # File info
        self.file_info = QLabel()
        self.file_info.setStyleSheet("""
            QLabel {
                color: #e8e8fc;
                font-weight: bold;
                padding: 5px;
            }
        """)
        self.file_info.setWordWrap(True)
        self.file_info.hide()

        # Remove button (initially hidden)
        self.remove_btn = QPushButton("Remove Media")
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background: rgba(231,76,60,0.2);
                color: #e74c3c;
                border: 2px solid #e74c3c;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(231,76,60,0.4);
                border: 3px solid #e74c3c;
            }
        """)
        self.remove_btn.clicked.connect(self.remove_media)
        self.remove_btn.hide()

        # Browse button
        self.browse_btn = QPushButton("Browse Files")
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background: rgba(34,139,34,0.2);
                color: #22c55e;
                border: 2px solid #22c55e;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(34,139,34,0.4);
                border: 3px solid #22c55e;
            }
        """)
        self.browse_btn.clicked.connect(self.browse_files)

        # Add widgets to main layout
        main_layout.addWidget(self.drop_zone)
        main_layout.addWidget(self.file_info)
        main_layout.addWidget(self.remove_btn)
        main_layout.addWidget(self.browse_btn)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_zone.setStyleSheet("""
                QLabel {
                    border: 3px dashed #45edf2;
                    border-radius: 15px;
                    background-color: rgba(69,237,242,0.2);
                    color: #45edf2;
                    font-size: 16px;
                    font-weight: bold;
                }
            """)
            self.drop_zone.setText("Drop Steganographic Media Here!")

    def dragLeaveEvent(self, event):
        """Handle drag leave event"""
        self.drop_zone.setStyleSheet("""
            QLabel {
                border: 3px dashed rgba(69,237,242,0.6);
                border-radius: 15px;
                background-color: rgba(14,22,37,0.8);
                color: #e8e8fc;
                font-size: 16px;
            }
        """)
        self.drop_zone.setText(
            "Drag & Drop Steganographic Media Here\n\nSupported: Images, Audio, Video")

    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        self.dragLeaveEvent(event)

        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                self.load_media(file_path)

    def browse_files(self):
        """Browse for media files"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Steganographic Media File", "",
            "Media Files (*.png *.jpg *.jpeg *.bmp *.tiff *.mp3 *.wav *.mp4 *.avi *.mov);;"
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff);;"
            "Audio (*.mp3 *.wav);;"
            "Video (*.mp4 *.avi *.mov);;"
            "All Files (*)"
        )
        if file_path:
            self.load_media(file_path)

    def load_media(self, file_path):
        """Load and display media file"""
        if not os.path.exists(file_path):
            return

        # Determine media type
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
            media_type = 'image'
        elif ext in ['.mp3', '.wav']:
            media_type = 'audio'
        elif ext in ['.mp4', '.avi', '.mov']:
            media_type = 'video'
        else:
            return

        self.media_path = file_path
        self.media_type = media_type

        # Hide drop zone and browse button, show remove button
        self.drop_zone.hide()
        self.browse_btn.hide()
        self.remove_btn.show()

        # Update UI with proper file path formatting
        self.file_info.setText(f"<b>File Path</b><br>{file_path}")
        self.file_info.show()

        # Emit signal
        self.media_loaded.emit(file_path, media_type)

    def remove_media(self):
        """Remove the loaded media and reset to initial state"""
        # Clear media data
        self.media_path = None
        self.media_type = None

        # Hide file info and remove button
        self.file_info.hide()
        self.remove_btn.hide()

        # Show drop zone and browse button
        self.drop_zone.show()
        self.browse_btn.show()

        # Emit signal to notify parent
        self.media_loaded.emit("", "")


class StegaDecodeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steganography - Extract Messages")
        
        # Setup responsive sizing
        self.setup_responsive_sizing()

        # Initialize the steganography decoding machine
        from machine.stega_decode_machine import StegaDecodeMachine
        self.machine = StegaDecodeMachine()

        self.status_label = None
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

        # Main content area
        self.create_content_area(main_layout)

        # Set window size and position
        self.setGeometry(self.window_x, self.window_y, self.window_width, self.window_height)
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

    def create_info_button(self, tooltip_text):
        """Create a cyan info button with tooltip"""
        info_btn = QPushButton("ℹ")
        info_btn.setFixedSize(25, 25)
        info_btn.setStyleSheet("""
            QPushButton {
                background: rgba(69,237,242,0.2);
                color: #45edf2;
                border: 2px solid #45edf2;
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(69,237,242,0.4);
                border: 3px solid #45edf2;
            }
        """)
        info_btn.setToolTip(tooltip_text)
        return info_btn

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
        title_label = QLabel("Steganography - Extract Messages")
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

    def create_content_area(self, layout):
        """Create the main content area with two columns"""
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Left column - Steganographic Media (fixed width)
        media_panel = self.create_media_panel()
        media_panel.setFixedWidth(500)
        content_layout.addWidget(media_panel)

        # Right column - Controls and Results (fixed width)
        controls_panel = self.create_controls_panel()
        controls_panel.setFixedWidth(500)
        content_layout.addWidget(controls_panel)

        layout.addLayout(content_layout)

        # Add Extract Message button below all columns
        self.create_extract_button(layout)

    def create_extract_button(self, layout):
        """Create the Extract Message button below all columns"""
        # Add some spacing above the button
        layout.addSpacing(30)

        # Create button container with centered alignment
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)

        # Extract Message button
        extract_button = QPushButton("Extract Message")
        extract_button.setMinimumHeight(60)
        extract_button.setStyleSheet("""
            QPushButton {
                background: rgba(255,140,0,0.2);
                color: #ff8c00;
                border: 2px solid #ff8c00;
                padding: 20px 40px;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
                min-width: 200px;
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
        extract_button.clicked.connect(self.extract_message)

        # Center the button
        button_layout.addStretch()
        button_layout.addWidget(extract_button)
        button_layout.addStretch()

        layout.addWidget(button_container)

    def create_media_panel(self):
        """Create the steganographic media panel (left column)"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #0e1625;
                border-radius: 15px;
                border: 2px solid rgba(69,237,242,0.6);
            }
        """)
        panel.setGraphicsEffect(self.create_shadow_effect())

        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Panel header with title and info button
        header_layout = QHBoxLayout()

        # Panel title
        title = QLabel("Steganographic Media")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #e8e8fc; margin-bottom: 15px; border: none;")

        # Info button
        info_btn = self.create_info_button(
            "For Steganographic Media, we support:\n"
            "• Image (.png, .bmp, .gif, .jpg)\n"
            "• Audio (.wav, .mp3)\n"
            "• Video (.mov, .mp4)")

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(info_btn)

        # Media drop widget
        self.media_drop_widget = MediaDropWidget()
        self.media_drop_widget.media_loaded.connect(self.on_media_loaded)

        layout.addLayout(header_layout)
        layout.addWidget(self.media_drop_widget)
        layout.addStretch()

        return panel

    def create_controls_panel(self):
        """Create the controls and results panel (right column)"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #0e1625;
                border-radius: 15px;
                border: 2px solid rgba(69,237,242,0.6);
            }
        """)
        panel.setGraphicsEffect(self.create_shadow_effect())

        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Panel header with title and info button
        header_layout = QHBoxLayout()

        # Panel title
        title = QLabel("Controls & Results")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #e8e8fc; margin-bottom: 15px; border: none;")

        # Info button
        info_btn = self.create_info_button(
            "For Controls:\n"
            "• LSB: Number of bits used for encoding\n"
            "• Decryption Key: Key used for encoding (if any)\n"
            "• Output Path: Where to save extracted data")

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(info_btn)

        # LSB slider
        lsb_group = QGroupBox("LSB Settings")
        lsb_group.setStyleSheet("""
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
        lsb_layout = QVBoxLayout(lsb_group)

        # LSB value display
        self.lsb_value_label = QLabel("LSB Bits: 1")
        self.lsb_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lsb_value_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #e8e8fc;
                padding: 15px;
                background-color: rgba(14,22,37,0.8);
                border: 3px dashed rgba(69,237,242,0.6);
                border-radius: 15px;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        # LSB slider
        self.lsb_slider = QSlider(Qt.Orientation.Horizontal)
        self.lsb_slider.setMinimum(1)
        self.lsb_slider.setMaximum(8)
        self.lsb_slider.setValue(1)
        self.lsb_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.lsb_slider.setTickInterval(1)
        self.lsb_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid rgba(69,237,242,0.6);
                height: 8px;
                background: rgba(14,22,37,0.8);
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #45edf2;
                border: 1px solid #45edf2;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #45edf2;
                border: 2px solid #45edf2;
            }
        """)
        self.lsb_slider.valueChanged.connect(self.update_lsb_value)

        # LSB markers 1..8 with highlight for selected value
        markers_row = QHBoxLayout()
        markers_row.setSpacing(8)
        self.lsb_markers = []
        for i in range(1, 9):
            lab = QLabel(str(i))
            lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lab.setStyleSheet("""
                QLabel {
                    color: #45edf2;
                    border: 2px solid #49299a;
                    border-radius: 8px;
                    padding: 5px 10px;
                    background-color: rgba(14,22,37,0.8);
                    font-weight: bold;
                }
            """)
            self.lsb_markers.append(lab)
            markers_row.addWidget(lab)

        lsb_layout.addWidget(self.lsb_value_label)
        lsb_layout.addWidget(self.lsb_slider)
        lsb_layout.addLayout(markers_row)

        # Key input
        key_group = QGroupBox("Decryption Key")
        key_group.setStyleSheet("""
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
        key_layout = QVBoxLayout(key_group)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText(
            "Enter decryption key (if used during encoding)...")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                border: 3px dashed rgba(69,237,242,0.6);
                border-radius: 15px;
                background-color: rgba(14,22,37,0.8);
                color: #e8e8fc;
                font-size: 14px;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit:focus {
                border: 3px dashed #45edf2;
                background-color: rgba(69,237,242,0.1);
            }
            QLineEdit:hover {
                border: 3px dashed #45edf2;
                background-color: rgba(69,237,242,0.1);
            }
        """)

        key_layout.addWidget(self.key_input)

        self.honey_random_button = QPushButton('Honey: Try random key')
        self.honey_random_button.setEnabled(False)
        self.honey_random_button.clicked.connect(self.on_honey_random_key)
        key_layout.addWidget(self.honey_random_button)

        # Output path
        output_group = QGroupBox("Output Path")
        output_group.setStyleSheet("""
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
        output_layout = QVBoxLayout(output_group)

        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Output will be saved here...")
        self.output_path.setReadOnly(True)
        self.output_path.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                border: 3px dashed rgba(69,237,242,0.6);
                border-radius: 15px;
                background-color: rgba(14,22,37,0.8);
                color: #e8e8fc;
                font-size: 14px;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        output_button = QPushButton("Choose Output")
        output_button.setStyleSheet("""
            QPushButton {
                background: rgba(34,139,34,0.2);
                color: #22c55e;
                border: 2px solid #22c55e;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(34,139,34,0.4);
                border: 3px solid #22c55e;
            }
        """)
        output_button.clicked.connect(self.choose_output_path)

        output_layout.addWidget(self.output_path)
        output_layout.addWidget(output_button)

        # Results display
        results_group = QGroupBox("Extracted Data")
        results_group.setStyleSheet("""
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
        results_layout = QVBoxLayout(results_group)

        self.status_label = QLabel('Status: Ready')
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("QLabel { background: rgba(69,237,242,0.12); color: #45edf2; border: 1px solid rgba(69,237,242,0.5); border-radius: 10px; padding: 8px 14px; font-weight: 600; }")
        results_layout.addWidget(self.status_label)

        self.set_status('Ready to decode.', 'info')

        self.results_text = QTextEdit()
        self.results_text.setPlaceholderText(
            "Extracted data will appear here...")
        self.results_text.setMaximumHeight(150)
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet("""
            QTextEdit {
                border: 3px dashed rgba(69,237,242,0.6);
                border-radius: 15px;
                background-color: rgba(14,22,37,0.8);
                color: #e8e8fc;
                font-size: 14px;
                padding: 15px;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        results_layout.addWidget(self.results_text)

        layout.addLayout(header_layout)
        layout.addWidget(lsb_group)
        layout.addWidget(key_group)
        layout.addWidget(output_group)
        layout.addWidget(results_group)
        layout.addStretch()

        return panel


    def set_status(self, message: str, severity: str = 'info'):

        """Update the status badge with contextual colours."""

        if self.status_label is None:

            print(f'[STATUS:{severity}] {message}')

            return

        styles = {

            'info': "QLabel { background: rgba(69,237,242,0.12); color: #45edf2; border: 1px solid rgba(69,237,242,0.5); border-radius: 10px; padding: 8px 14px; font-weight: 600; }",

            'success': "QLabel { background: rgba(34,197,94,0.18); color: #4ade80; border: 1px solid rgba(34,197,94,0.5); border-radius: 10px; padding: 8px 14px; font-weight: 600; }",

            'warning': "QLabel { background: rgba(234,179,8,0.2); color: #facc15; border: 1px solid rgba(234,179,8,0.5); border-radius: 10px; padding: 8px 14px; font-weight: 600; }",

            'error': "QLabel { background: rgba(239,68,68,0.2); color: #f87171; border: 1px solid rgba(239,68,68,0.6); border-radius: 10px; padding: 8px 14px; font-weight: 600; }",

        }

        style = styles.get(severity, styles['info'])

        self.status_label.setText(message)

        self.status_label.setStyleSheet(style)



    def create_shadow_effect(self):
        """Create an enhanced shadow effect for panels"""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(35)  # Increased blur for stronger glow
        shadow.setXOffset(0)
        shadow.setYOffset(8)  # Increased offset for more depth
        # Enhanced cyan glow with higher opacity
        shadow.setColor(QColor(69, 237, 242, 80))
        return shadow

    def update_lsb_value(self, value):
        """Update LSB value display"""
        self.lsb_value_label.setText(f"LSB Bits: {value}")
        # Update machine with new LSB value
        self.machine.set_lsb_bits(value)

        # Update marker highlight
        if hasattr(self, 'lsb_markers'):
            for i, lab in enumerate(self.lsb_markers, start=1):
                if i == value:
                    lab.setStyleSheet("""
                        QLabel {
                            color: #45edf2;
                            border: 2px solid #49299a;
                            border-radius: 8px;
                            padding: 5px 10px;
                            background-color: rgba(69,237,242,0.2);
                            font-weight: bold;
                        }
                    """)
                else:
                    lab.setStyleSheet("""
                        QLabel {
                            color: #45edf2;
                            border: 2px solid #49299a;
                            border-radius: 8px;
                            padding: 5px 10px;
                            background-color: rgba(14,22,37,0.8);
                            font-weight: bold;
                        }
                    """)

    def on_media_loaded(self, file_path, media_type):
        """Handle media loaded from drag and drop or browse"""
        if not file_path:  # Media was removed
            return

        print(f"Steganographic media loaded: {file_path} ({media_type})")

        # Update machine with media
        if media_type == 'image':
            if self.machine.set_stego_image(file_path):
                info = self.machine.get_image_info()
                print(
                    f"✅ Steganographic image loaded: {os.path.basename(file_path)}")
                print(f"Size: {info.get('dimensions', 'Unknown')}")
                print(f"Capacity: {info.get('max_capacity_bytes', 0)} bytes")
            else:
                print("❌ Error loading steganographic image")
        elif media_type == 'audio':
            if self.machine.set_stego_audio(file_path):
                print(f"✅ AUDIO loaded: {os.path.basename(file_path)}")
            else:
                print(f"❌ Error loading steganographic audio: {file_path}")
        elif media_type == 'video':
            if self.machine.set_stego_video(file_path):
                info = self.machine.get_video_info() or {}
                frames = info.get('frames', 'n/a')
                dims = info.get('dimensions') or ('n/a', 'n/a', 'n/a')
                fps = info.get('fps', 0.0) or 0.0
                capacity = info.get('max_capacity_bytes', 0)
                print(f"✅ VIDEO loaded: {os.path.basename(file_path)}")
                if isinstance(dims, tuple) and len(dims) == 3:
                    height, width, _ = dims
                else:
                    height = width = 'n/a'
                print(f"Frames: {frames}, resolution: {width}x{height}, fps: {fps:.2f}")
                print(f"Capacity (approx.): {capacity} bytes at {self.machine.lsb_bits} LSBs")
            else:
                print(f"❌ Error loading steganographic video: {file_path}")
        else:
            print(f"❌ Unsupported media type: {media_type}")

    def choose_output_path(self):
        """Choose output folder; file will be auto-named (datetime.<header_filename>)."""
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", "")
        if folder:
            self.output_path.setText(folder)
            self.machine.set_output_path(folder)

    def extract_message(self):
        """Extract message from the steganographic media"""
        # Update machine with current GUI values
        self.machine.set_lsb_bits(self.lsb_slider.value())
        self.machine.set_encryption_key(self.key_input.text())

        # Require non-empty key
        if not self.key_input.text().strip():
            self.results_text.setPlainText("Error: A key is required to decode.")
            return

        # Set default output path if none specified
        if not self.output_path.text().strip():
            stego_source = (self.machine.stego_image_path or
                            self.machine.stego_audio_path or
                            self.machine.stego_video_path)
            base_dir = os.path.dirname(stego_source) if stego_source else os.path.join(os.getcwd(), 'extracted_payloads')
            if not os.path.exists(base_dir):
                os.makedirs(base_dir, exist_ok=True)
            self.output_path.setText(base_dir)
            self.machine.set_output_path(base_dir)
        # Perform steganography extraction
        if self.machine.extract_message():
            print('[OK] Steganography extraction completed successfully!')
            extracted_data = self.machine.get_extracted_data()
            header_info = self.machine.get_header_info() or {}
            out_path = self.machine.get_last_output_path() or '(unknown)'

            honey_context = None
            if hasattr(self.machine, 'get_honey_context'):
                try:
                    honey_context = self.machine.get_honey_context()
                except Exception as exc:
                    print(f"[WARN] Honey context unavailable: {exc}")
                    honey_context = None
            honey_info = None
            honey_error = None
            if isinstance(honey_context, dict):
                honey_info = honey_context.get('info')
                honey_error = honey_context.get('error')

            lines = []
            lines.append('=== Decode Success ===')
            if header_info:
                lines.append(f"Version: {header_info.get('version')}")
                lines.append(f"LSB bits: {header_info.get('lsb_bits')}")
                if header_info.get('start_offset') is not None:
                    lines.append(f"Header start offset: {header_info.get('start_offset')}")
                lines.append(f"Computed start: {header_info.get('computed_start')}")
                payload_length = header_info.get('payload_length')
                if payload_length is not None:
                    lines.append(f"Payload length: {payload_length} bytes")
                if header_info.get('filename'):
                    lines.append(f"Filename: {header_info.get('filename')}")
                if 'crc32_ok' in header_info:
                    lines.append(f"CRC OK: {header_info.get('crc32_ok')}")
            lines.append(f"Saved to: {out_path}")

            if honey_error:
                lines.append('')
                lines.append(f"Honey warning: {honey_error}")
            if honey_info and honey_info.get('message'):
                universe = honey_info.get('universe', 'unknown')
                key_used = honey_info.get('key')
                lines.append('')
                lines.append(f"Honey mode: message consistent with universe '{universe}'.")
                if key_used is not None:
                    lines.append(f"Key used: {key_used}")
                lines.append('Try a different key to see another plausible decoy.')

            if extracted_data and isinstance(extracted_data, str):
                preview = extracted_data
                if len(preview) > 5000:
                    preview = preview[:5000] + "\n...[truncated]"
                lines.append('')
                lines.append(preview)

            self.results_text.setPlainText("\n".join(lines))

            if hasattr(self, 'honey_random_button'):
                self.honey_random_button.setEnabled(bool(honey_info and honey_info.get('message')))
            if honey_error:
                self.set_status(f"Honey warning: {honey_error}", 'warning')
            elif honey_info and honey_info.get('message'):
                self.set_status('Honey mode: integrity verified.', 'success')
            elif header_info.get('crc32_ok'):
                self.set_status('Decryption OK (integrity verified).', 'success')
            else:
                self.set_status('Decode succeeded (checksum mismatch).', 'warning')

            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle('Decode Successful')
            out_path_display = self.machine.get_last_output_path() or 'saved file'
            msg.setText(f"Payload extracted successfully.\nSaved to: {out_path_display}")
            open_btn = msg.addButton('Open file', QMessageBox.ButtonRole.AcceptRole)
            msg.addButton('Close', QMessageBox.ButtonRole.RejectRole)
            
            # Apply dark theme styling for better text visibility
            self._style_message_box(msg, 'info')
            
            msg.exec()
            if msg.clickedButton() == open_btn and self.machine.get_last_output_path():
                from PyQt6.QtGui import QDesktopServices
                from PyQt6.QtCore import QUrl
                QDesktopServices.openUrl(QUrl.fromLocalFile(self.machine.get_last_output_path()))
        else:
            print('[ERR] Steganography extraction failed!')
            error_msg = self.machine.get_last_error() or "Extraction failed. Please check your settings and try again."
            self.results_text.setPlainText(error_msg)
            if hasattr(self, 'honey_random_button'):
                self.honey_random_button.setEnabled(False)
            self.set_status(error_msg, 'error')

            # Show error popup
            from PyQt6.QtWidgets import QMessageBox
            error_msg_box = QMessageBox.critical(self, "Decode Failed", error_msg)
            self._style_message_box(error_msg_box, 'error')

    def _style_message_box(self, msg_box, button_style='default'):
        """Apply dark theme styling to QMessageBox for better text visibility"""
        if button_style == 'error':
            button_bg = "rgba(231,76,60,0.1)"
            button_color = "#e74c3c"
            button_border = "rgba(231,76,60,0.6)"
            button_hover_bg = "rgba(231,76,60,0.3)"
            button_pressed_bg = "rgba(231,76,60,0.5)"
        else:  # default/info
            button_bg = "rgba(69,237,242,0.1)"
            button_color = "#45edf2"
            button_border = "rgba(69,237,242,0.6)"
            button_hover_bg = "rgba(69,237,242,0.3)"
            button_pressed_bg = "rgba(69,237,242,0.5)"
            
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: #0e1625;
                color: #e8e8fc;
            }}
            QMessageBox QLabel {{
                color: #e8e8fc;
                background-color: transparent;
            }}
            QMessageBox QPushButton {{
                background-color: {button_bg};
                color: {button_color};
                border: 2px solid {button_border};
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {button_hover_bg};
                border: 2px solid {button_color};
            }}
            QMessageBox QPushButton:pressed {{
                background-color: {button_pressed_bg};
            }}
        """)

    def on_honey_random_key(self):
        if not hasattr(self.machine, 'simulate_honey_with_key'):
            QToolTip.showText(QCursor.pos(), 'Honey simulation unavailable.', self.honey_random_button)
            return
        try:
            honey_context = self.machine.get_honey_context() if hasattr(self.machine, 'get_honey_context') else None
        except Exception as exc:
            print(f'Honey context unavailable: {exc}')
            honey_context = None
        honey_info = honey_context.get('info') if isinstance(honey_context, dict) else None
        if not honey_info or not honey_info.get('message'):
            QToolTip.showText(QCursor.pos(), 'No Honey payload available to simulate.', self.honey_random_button)
            return
        current_key = None
        current_text = self.key_input.text().strip() if hasattr(self, 'key_input') else ''
        try:
            current_key = int(current_text) if current_text else None
        except ValueError:
            current_key = None
        attempts = 0
        random_key = current_key
        while random_key == current_key:
            random_key = random.randint(0, 999999)
            attempts += 1
            if attempts > 1000:
                break
        try:
            decoy_message = self.machine.simulate_honey_with_key(random_key)
        except Exception as exc:
            QToolTip.showText(QCursor.pos(), f'Honey simulation failed: {exc}', self.honey_random_button)
            return
        if hasattr(self, 'results_text'):
            self.results_text.append(f"\n[Honey demo] Key {random_key}: {decoy_message}")
        self.set_status(f'Honey demo: key {random_key} produced a plausible decoy.', 'info')

    def go_back(self):
        """Go back to main window"""
        # Clean up machine resources
        self.machine.cleanup()

        from gui.main_window import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()
