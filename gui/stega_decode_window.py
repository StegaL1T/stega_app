# gui/stega_decode_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QFileDialog, QTextEdit,
                             QGroupBox, QGridLayout, QLineEdit, QComboBox, QSlider,
                             QSpinBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                             QScrollArea, QSlider as QTimeSlider, QToolTip, QApplication)
from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QDragEnterEvent, QDropEvent, QImage
import os
import numpy as np
from PIL import Image
import soundfile as sf
import cv2
from datetime import datetime


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
                border: 3px dashed #bdc3c7;
                border-radius: 15px;
                background-color: #f8f9fa;
                color: #7f8c8d;
                font-size: 16px;
            }
            QLabel:hover {
                border-color: #e67e22;
                background-color: #fdf2e9;
            }
        """)
        self.drop_zone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_zone.setText(
            "Drag & Drop Steganographic Media Here\n\nSupported: Images, Audio, Video")

        # File info
        self.file_info = QLabel()
        self.file_info.setStyleSheet("""
            QLabel {
                color: #2c3e50;
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
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.remove_btn.clicked.connect(self.remove_media)
        self.remove_btn.hide()

        # Browse button
        self.browse_btn = QPushButton("Browse Files")
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d35400;
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
                    border: 3px dashed #27ae60;
                    border-radius: 15px;
                    background-color: #d5f4e6;
                    color: #27ae60;
                    font-size: 16px;
                    font-weight: bold;
                }
            """)
            self.drop_zone.setText("Drop Steganographic Media Here!")

    def dragLeaveEvent(self, event):
        """Handle drag leave event"""
        self.drop_zone.setStyleSheet("""
            QLabel {
                border: 3px dashed #bdc3c7;
                border-radius: 15px;
                background-color: #f8f9fa;
                color: #7f8c8d;
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

        # Set gradient background
        self.setStyleSheet("""
            QMainWindow {
                background: #fdf2e9;
            }
        """)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

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
        """Create an orange info button with tooltip"""
        info_btn = QPushButton("ℹ")
        info_btn.setFixedSize(25, 25)
        info_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        info_btn.setToolTip(tooltip_text)
        return info_btn

    def create_title_section(self, layout):
        """Create the title and back button section"""
        title_layout = QHBoxLayout()

        # Back button
        back_button = QPushButton("← Back to Main")
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        back_button.clicked.connect(self.go_back)

        # Title
        title_label = QLabel("Steganography - Extract Messages")
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50;")

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
                background-color: #e67e22;
                color: white;
                border: none;
                padding: 20px 40px;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
            QPushButton:pressed {
                background-color: #c0392b;
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
                background-color: white;
                border-radius: 15px;
                border: none;
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
        title.setStyleSheet("color: #2c3e50; margin-bottom: 15px;")

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
                background-color: white;
                border-radius: 15px;
                border: none;
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
        title.setStyleSheet("color: #2c3e50; margin-bottom: 15px;")

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
        lsb_layout = QVBoxLayout(lsb_group)

        # LSB value display
        self.lsb_value_label = QLabel("LSB Bits: 1")
        self.lsb_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lsb_value_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 15px;
                background-color: #f8f9fa;
                border: 3px dashed #bdc3c7;
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
                border: 1px solid #bdc3c7;
                height: 8px;
                background: #ecf0f1;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #e67e22;
                border: 1px solid #d35400;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #d35400;
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
            lab.setStyleSheet("color: #7f8c8d;")
            self.lsb_markers.append(lab)
            markers_row.addWidget(lab)

        lsb_layout.addWidget(self.lsb_value_label)
        lsb_layout.addWidget(self.lsb_slider)
        lsb_layout.addLayout(markers_row)

        # Key input
        key_group = QGroupBox("Decryption Key")
        key_layout = QVBoxLayout(key_group)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText(
            "Enter decryption key (if used during encoding)...")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                border: 3px dashed #bdc3c7;
                border-radius: 15px;
                background-color: #f8f9fa;
                color: #7f8c8d;
                font-size: 14px;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit:focus {
                border-color: #e67e22;
                background-color: #fdf2e9;
            }
            QLineEdit:hover {
                border-color: #e67e22;
                background-color: #fdf2e9;
            }
        """)

        key_layout.addWidget(self.key_input)

        # Output path
        output_group = QGroupBox("Output Path")
        output_layout = QVBoxLayout(output_group)

        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Output will be saved here...")
        self.output_path.setReadOnly(True)
        self.output_path.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                border: 3px dashed #bdc3c7;
                border-radius: 15px;
                background-color: #f8f9fa;
                color: #7f8c8d;
                font-size: 14px;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        output_button = QPushButton("Choose Output")
        output_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        output_button.clicked.connect(self.choose_output_path)

        output_layout.addWidget(self.output_path)
        output_layout.addWidget(output_button)

        # Results display
        results_group = QGroupBox("Extracted Data")
        results_layout = QVBoxLayout(results_group)

        self.results_text = QTextEdit()
        self.results_text.setPlaceholderText(
            "Extracted data will appear here...")
        self.results_text.setMaximumHeight(150)
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet("""
            QTextEdit {
                border: 3px dashed #bdc3c7;
                border-radius: 15px;
                background-color: #f8f9fa;
                color: #7f8c8d;
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

    def create_shadow_effect(self):
        """Create a shadow effect for panels"""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 30))
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
                    lab.setStyleSheet("color: #e67e22; font-weight: bold;")
                else:
                    lab.setStyleSheet("color: #7f8c8d;")

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
            print("✅ Steganography extraction completed successfully!")
            # Display extracted data and header info in results text area
            extracted_data = self.machine.get_extracted_data()
            header_info = self.machine.get_header_info() or {}
            out_path = self.machine.get_last_output_path() or "(unknown)"

            lines = []
            lines.append("=== Decode Success ===")
            if header_info:
                lines.append(f"Version: {header_info.get('version')}")
                lines.append(f"LSB bits: {header_info.get('lsb_bits')}")
                if header_info.get('start_offset') is not None:
                    lines.append(f"Header start offset: {header_info.get('start_offset')}")
                lines.append(f"Computed start: {header_info.get('computed_start')}")
                lines.append(f"Payload length: {header_info.get('payload_length')} bytes")
                if header_info.get('filename'):
                    lines.append(f"Filename: {header_info.get('filename')}")
            lines.append(f"Saved to: {out_path}")

            # Always show some message in results pane
            if extracted_data and isinstance(extracted_data, str):
                # Limit overly long text previews
                preview = extracted_data
                if len(preview) > 5000:
                    preview = preview[:5000] + "\n...[truncated]"
                lines.append("")
                lines.append(preview)

            self.results_text.setPlainText("\n".join(lines))

            # Show success dialog with option to open file
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Decode Successful")
            out_path = self.machine.get_last_output_path() or "saved file"
            msg.setText(f"Payload extracted successfully.\nSaved to: {out_path}")
            open_btn = msg.addButton("Open file", QMessageBox.ButtonRole.AcceptRole)
            msg.addButton("Close", QMessageBox.ButtonRole.RejectRole)
            msg.exec()
            if msg.clickedButton() == open_btn and self.machine.get_last_output_path():
                from PyQt6.QtGui import QDesktopServices
                from PyQt6.QtCore import QUrl
                QDesktopServices.openUrl(QUrl.fromLocalFile(self.machine.get_last_output_path()))
        else:
            print("❌ Steganography extraction failed!")
            error_msg = self.machine.get_last_error() or "Extraction failed. Please check your settings and try again."
            self.results_text.setPlainText(error_msg)

            # Show error popup
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Decode Failed", error_msg)

    def go_back(self):
        """Go back to main window"""
        # Clean up machine resources
        self.machine.cleanup()

        from gui.main_window import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()
