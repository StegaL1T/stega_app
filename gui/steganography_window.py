# gui/steganography_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QFileDialog, QTextEdit,
                             QGroupBox, QGridLayout, QLineEdit, QComboBox, QSlider,
                             QSpinBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QPen


class SteganographyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steganography - Hide Messages")
        self.setMinimumSize(1200, 800)

        # Initialize the steganography machine
        from machine.steganography_machine import SteganographyMachine
        self.machine = SteganographyMachine()

        # Set gradient background
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e3f2fd, stop:1 #ffffff);
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

        # Make the window fullscreen
        self.showMaximized()

    def create_title_section(self, layout):
        """Create the title and back button section"""
        title_layout = QHBoxLayout()

        # Back button
        back_button = QPushButton("← Back to Main")
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        back_button.clicked.connect(self.go_back)

        # Title
        title_label = QLabel("Steganography - Hide Messages")
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
        """Create the main content area with three columns"""
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Left column - Cover Item
        cover_panel = self.create_cover_panel()
        content_layout.addWidget(cover_panel)

        # Middle column - Payload
        payload_panel = self.create_payload_panel()
        content_layout.addWidget(payload_panel)

        # Right column - Controls
        controls_panel = self.create_controls_panel()
        content_layout.addWidget(controls_panel)

        layout.addLayout(content_layout)

    def create_cover_panel(self):
        """Create the cover item panel (left column)"""
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

        # Panel title
        title = QLabel("Cover Item")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 15px;")

        # Cover image selection
        cover_group = QGroupBox("Select Cover Image")
        cover_layout = QVBoxLayout(cover_group)

        self.cover_path = QLineEdit()
        self.cover_path.setPlaceholderText("No image selected...")
        self.cover_path.setReadOnly(True)
        self.cover_path.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: #f8f9fa;
            }
        """)

        cover_button = QPushButton("Browse Image")
        cover_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        cover_button.clicked.connect(self.browse_cover_image)

        # Image preview area
        self.image_preview = QLabel()
        self.image_preview.setMinimumHeight(200)
        self.image_preview.setStyleSheet("""
            QLabel {
                border: 2px dashed #bdc3c7;
                border-radius: 10px;
                background-color: #f8f9fa;
            }
        """)
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setText(
            "Image Preview\n\nSelect an image to see preview")

        cover_layout.addWidget(self.cover_path)
        cover_layout.addWidget(cover_button)
        cover_layout.addWidget(self.image_preview)

        layout.addWidget(title)
        layout.addWidget(cover_group)
        layout.addStretch()

        return panel

    def create_payload_panel(self):
        """Create the payload panel (middle column)"""
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

        # Panel title
        title = QLabel("Payload")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 15px;")

        # Message input
        message_group = QGroupBox("Secret Message")
        message_layout = QVBoxLayout(message_group)

        self.message_text = QTextEdit()
        self.message_text.setPlaceholderText(
            "Enter your secret message here...")
        self.message_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                background-color: #f8f9fa;
                font-family: 'Consolas', 'Monaco', monospace;
            }
            QTextEdit:focus {
                border-color: #3498db;
            }
        """)

        message_layout.addWidget(self.message_text)

        # File input option
        file_group = QGroupBox("Or Load from File")
        file_layout = QVBoxLayout(file_group)

        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("No file selected...")
        self.file_path.setReadOnly(True)
        self.file_path.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: #f8f9fa;
            }
        """)

        file_button = QPushButton("Browse File")
        file_button.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        file_button.clicked.connect(self.browse_payload_file)

        file_layout.addWidget(self.file_path)
        file_layout.addWidget(file_button)

        layout.addWidget(title)
        layout.addWidget(message_group)
        layout.addWidget(file_group)
        layout.addStretch()

        return panel

    def create_controls_panel(self):
        """Create the controls panel (right column)"""
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

        # Panel title
        title = QLabel("Controls")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 15px;")

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
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 5px;
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
                background: #3498db;
                border: 1px solid #2980b9;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #2980b9;
            }
        """)
        self.lsb_slider.valueChanged.connect(self.update_lsb_value)

        lsb_layout.addWidget(self.lsb_value_label)
        lsb_layout.addWidget(self.lsb_slider)

        # Key input
        key_group = QGroupBox("Encryption Key")
        key_layout = QVBoxLayout(key_group)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Enter encryption key (optional)...")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: #f8f9fa;
            }
            QLineEdit:focus {
                border-color: #e67e22;
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
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: #f8f9fa;
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

        # Hide button
        hide_button = QPushButton("Hide Message")
        hide_button.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        hide_button.clicked.connect(self.hide_message)

        layout.addWidget(title)
        layout.addWidget(lsb_group)
        layout.addWidget(key_group)
        layout.addWidget(output_group)
        layout.addWidget(hide_button)
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

    def browse_cover_image(self):
        """Browse for cover image"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Cover Image", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        if file_path:
            self.cover_path.setText(file_path)

            # Load image into machine
            if self.machine.set_cover_image(file_path):
                # Get image info and display preview
                info = self.machine.get_image_info()
                self.image_preview.setText(
                    f"Image loaded:\n{file_path.split('/')[-1]}\n"
                    f"Size: {info.get('dimensions', 'Unknown')}\n"
                    f"Capacity: {info.get('max_capacity_bytes', 0)} bytes"
                )
            else:
                self.image_preview.setText("Error loading image")

    def browse_payload_file(self):
        """Browse for payload file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Payload File", "",
            "All Files (*)"
        )
        if file_path:
            self.file_path.setText(file_path)

            # Load file into machine
            if self.machine.set_payload_file(file_path):
                print(f"Payload file loaded successfully")
            else:
                print("Error loading payload file")

    def choose_output_path(self):
        """Choose output path"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Steganographic Image", "",
            "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
        )
        if file_path:
            self.output_path.setText(file_path)
            self.machine.set_output_path(file_path)

    def hide_message(self):
        """Hide message in the cover image"""
        # Update machine with current GUI values
        self.machine.set_lsb_bits(self.lsb_slider.value())
        self.machine.set_encryption_key(self.key_input.text())

        # Set payload from text if provided
        if self.message_text.toPlainText().strip():
            self.machine.set_payload_text(self.message_text.toPlainText())

        # Perform steganography
        if self.machine.hide_message():
            print("✅ Steganography completed successfully!")
            # TODO: Show success message in GUI
        else:
            print("❌ Steganography failed!")
            # TODO: Show error message in GUI

    def go_back(self):
        """Go back to main window"""
        # Clean up machine resources
        self.machine.cleanup()

        from gui.main_window import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()
