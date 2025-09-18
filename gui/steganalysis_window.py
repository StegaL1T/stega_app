import datetime
from pathlib import Path
import numpy as np
from PIL import Image
import io
import wave
import matplotlib.pyplot as plt
import cv2


# gui/steganalysis_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QFileDialog, QTextEdit,
                             QGroupBox, QGridLayout, QLineEdit, QComboBox, QProgressBar, QApplication,
                             QStackedWidget, QHBoxLayout, QSizePolicy)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QPen 


class SteganalysisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steganalysis - Detect Hidden Messages")
        self.setMinimumSize(1000, 700)

        # Initialize the steganalysis machine
        from machine.steganalysis_machine import SteganalysisMachine
        self.machine = SteganalysisMachine()

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
            "Comprehensive Analysis": "Combines multiple basic detection methods for a thorough analysis of potential steganographic content.",
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
            "Video Comprehensive Analysis": "Combines multiple video detection methods for thorough analysis of potential steganographic content.",
            "Video Advanced Comprehensive": "Uses all available video analysis techniques for the most comprehensive steganalysis possible."
        }

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

        # Page navigation section
        self.create_page_navigation(main_layout)

        # Main content area with stacked pages
        self.create_stacked_content_area(main_layout)

        # Make the window fullscreen
        self.showMaximized()

    def create_title_section(self, layout):
        """Create the title and back button section"""
        title_layout = QHBoxLayout()

        # Back button
        back_button = QPushButton("← Back to Main")
        back_button.setStyleSheet("""
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
        back_button.clicked.connect(self.go_back)

        # Title
        title_label = QLabel("Steganalysis - Detect Hidden Messages")
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

    def create_page_navigation(self, layout):
        """Create page navigation with arrow buttons and page indicators"""
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(20)
        
        # Left arrow button
        self.prev_button = QPushButton("← Image Analysis")
        self.prev_button.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.prev_button.clicked.connect(self.go_to_previous_page)
        self.prev_button.setEnabled(False)  # Start on first page
        
        # Page indicator
        self.page_indicator = QLabel("Page 1 of 3")
        self.page_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_indicator.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        
        # Right arrow button
        self.next_button = QPushButton("Next →")
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.next_button.clicked.connect(self.go_to_next_page)
        
        nav_layout.addWidget(self.prev_button)
        nav_layout.addStretch()
        nav_layout.addWidget(self.page_indicator)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_button)
        
        layout.addLayout(nav_layout)

    def create_stacked_content_area(self, layout):
        """Create the main content area with stacked pages"""
        # Create stacked widget for pages
        self.stacked_widget = QStackedWidget()
        
        # Create image analysis page
        image_page = self.create_image_analysis_page()
        self.stacked_widget.addWidget(image_page)
        
        # Create audio analysis page
        audio_page = self.create_audio_analysis_page()
        self.stacked_widget.addWidget(audio_page)
        
        # Create video analysis page
        video_page = self.create_video_analysis_page()
        self.stacked_widget.addWidget(video_page)
        
        # Start on first page (image analysis)
        self.current_page = 0
        self.stacked_widget.setCurrentIndex(0)
        
        layout.addWidget(self.stacked_widget)

    def create_image_analysis_page(self):
        """Create the image analysis page"""
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setSpacing(30)

        # Left panel - Image Input
        input_panel = self.create_image_input_panel()
        layout.addWidget(input_panel)

        # Right panel - Results
        results_panel = self.create_results_panel()
        layout.addWidget(results_panel)

        return page

    def create_audio_analysis_page(self):
        """Create the audio analysis page"""
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setSpacing(30)

        # Left panel - Audio Input
        input_panel = self.create_audio_input_panel()
        layout.addWidget(input_panel)

        # Right panel - Results (shared)
        results_panel = self.create_results_panel()
        layout.addWidget(results_panel)

        return page

    def create_video_analysis_page(self):
        """Create the video analysis page"""
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setSpacing(30)

        # Left panel - Video Input
        input_panel = self.create_video_input_panel()
        layout.addWidget(input_panel)

        # Right panel - Results (shared)
        results_panel = self.create_results_panel()
        layout.addWidget(results_panel)

        return page

    def create_image_input_panel(self):
        """Create the image input panel"""
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
        layout.setContentsMargins(30, 30, 30, 30)

        # Panel title
        title = QLabel("Image Analysis")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")

        # Image selection
        image_group = QGroupBox("Suspicious Image")
        image_layout = QVBoxLayout(image_group)

        self.image_path = QLineEdit()
        self.image_path.setPlaceholderText("Select image to analyze...")
        self.image_path.setReadOnly(True)

        browse_button = QPushButton("Browse Image")
        browse_button.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        browse_button.clicked.connect(self.browse_image)

        image_layout.addWidget(self.image_path)
        image_layout.addWidget(browse_button)

        # Image preview
        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setStyleSheet("""
            QLabel {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: #f8f9fa;
                min-height: 150px;
                max-height: 200px;
            }
        """)
        self.image_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.image_preview.setText("No image selected")
        self.image_preview.setScaledContents(False)  # Don't stretch to fill
        image_layout.addWidget(self.image_preview)

        # Analysis method selection
        method_group = QGroupBox("Analysis Method")
        method_layout = QVBoxLayout(method_group)

        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "LSB Analysis",
            "Chi-Square Test",
            "RS Analysis",
            "Sample Pairs Analysis",
            "DCT Analysis",
            "Wavelet Analysis",
            "Histogram Analysis",
            "Comprehensive Analysis",
            "Advanced Comprehensive"
        ])
        self.method_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
            }
            QComboBox:focus {
                border-color: #9b59b6;
            }
        """)
        self.method_combo.currentTextChanged.connect(self.on_image_method_changed)

        method_layout.addWidget(self.method_combo)

        # Analyze button
        analyze_button = QPushButton("Analyze Image")
        analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        analyze_button.clicked.connect(self.analyze_image)

        # Method description
        self.image_method_description = QLabel()
        self.image_method_description.setWordWrap(True)
        self.image_method_description.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
                color: #495057;
                min-height: 60px;
            }
        """)
        self.image_method_description.setText("Select an analysis method to see its description...")

        layout.addWidget(title)
        layout.addWidget(image_group)
        layout.addWidget(method_group)
        layout.addWidget(analyze_button)
        layout.addWidget(self.image_method_description)
        layout.addStretch()

        return panel

    def create_audio_input_panel(self):
        """Create the audio input panel"""
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
        layout.setContentsMargins(30, 30, 30, 30)

        # Panel title
        title = QLabel("Audio Analysis")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")

        # Audio selection
        audio_group = QGroupBox("Suspicious Audio")
        audio_layout = QVBoxLayout(audio_group)

        self.audio_path = QLineEdit()
        self.audio_path.setPlaceholderText("Select WAV audio to analyze...")
        self.audio_path.setReadOnly(True)

        browse_audio_button = QPushButton("Browse Audio")
        browse_audio_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        browse_audio_button.clicked.connect(self.browse_audio)

        audio_layout.addWidget(self.audio_path)
        audio_layout.addWidget(browse_audio_button)

        # Audio preview (waveform)
        self.audio_preview = QLabel()
        self.audio_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.audio_preview.setStyleSheet("""
            QLabel {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: #f8f9fa;
                min-height: 100px;
                max-height: 150px;
            }
        """)
        self.audio_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.audio_preview.setText("No audio selected")
        audio_layout.addWidget(self.audio_preview)

        # Audio method selection
        audio_method_group = QGroupBox("Analysis Method")
        audio_method_layout = QVBoxLayout(audio_method_group)

        self.audio_method_combo = QComboBox()
        self.audio_method_combo.addItems([
            "Audio LSB Analysis",
            "Audio Chi-Square Test",
            "Audio Spectral Analysis",
            "Audio Autocorrelation Analysis",
            "Audio Entropy Analysis",
            "Audio Comprehensive Analysis",
            "Audio Advanced Comprehensive"
        ])
        self.audio_method_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
        """)
        self.audio_method_combo.currentTextChanged.connect(self.on_audio_method_changed)

        audio_method_layout.addWidget(self.audio_method_combo)

        # Analyze audio button
        analyze_audio_button = QPushButton("Analyze Audio")
        analyze_audio_button.setStyleSheet("""
            QPushButton {
                background-color: #16a085;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138d75;
            }
        """)
        analyze_audio_button.clicked.connect(self.analyze_audio)

        # Method description
        self.audio_method_description = QLabel()
        self.audio_method_description.setWordWrap(True)
        self.audio_method_description.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
                color: #495057;
                min-height: 60px;
            }
        """)
        self.audio_method_description.setText("Select an analysis method to see its description...")

        layout.addWidget(title)
        layout.addWidget(audio_group)
        layout.addWidget(audio_method_group)
        layout.addWidget(analyze_audio_button)
        layout.addWidget(self.audio_method_description)
        layout.addStretch()

        return panel

    def create_video_input_panel(self):
        """Create the video input panel"""
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
        layout.setContentsMargins(30, 30, 30, 30)

        # Panel title
        title = QLabel("Video Analysis")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")

        # Video selection
        video_group = QGroupBox("Suspicious Video")
        video_layout = QVBoxLayout(video_group)

        self.video_path = QLineEdit()
        self.video_path.setPlaceholderText("Select video to analyze...")
        self.video_path.setReadOnly(True)

        browse_video_button = QPushButton("Browse Video")
        browse_video_button.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        browse_video_button.clicked.connect(self.browse_video)

        video_layout.addWidget(self.video_path)
        video_layout.addWidget(browse_video_button)

        # Video preview (frame)
        self.video_preview = QLabel()
        self.video_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_preview.setStyleSheet("""
            QLabel {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: #f8f9fa;
                min-height: 120px;
                max-height: 180px;
            }
        """)
        self.video_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.video_preview.setText("No video selected")
        self.video_preview.setScaledContents(False)  # Don't stretch to fill
        video_layout.addWidget(self.video_preview)

        # Video method selection
        video_method_group = QGroupBox("Analysis Method")
        video_method_layout = QVBoxLayout(video_method_group)

        self.video_method_combo = QComboBox()
        self.video_method_combo.addItems([
            "Video LSB Analysis",
            "Video Frame Analysis",
            "Video Motion Analysis",
            "Video Comprehensive Analysis",
            "Video Advanced Comprehensive"
        ])
        self.video_method_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
            }
            QComboBox:focus {
                border-color: #e67e22;
            }
        """)
        self.video_method_combo.currentTextChanged.connect(self.on_video_method_changed)

        video_method_layout.addWidget(self.video_method_combo)

        # Analyze video button
        analyze_video_button = QPushButton("Analyze Video")
        analyze_video_button.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7d3c98;
            }
        """)
        analyze_video_button.clicked.connect(self.analyze_video)

        # Method description
        self.video_method_description = QLabel()
        self.video_method_description.setWordWrap(True)
        self.video_method_description.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
                color: #495057;
                min-height: 60px;
            }
        """)
        self.video_method_description.setText("Select an analysis method to see its description...")

        layout.addWidget(title)
        layout.addWidget(video_group)
        layout.addWidget(video_method_group)
        layout.addWidget(analyze_video_button)
        layout.addWidget(self.video_method_description)
        layout.addStretch()

        return panel

    def create_results_panel(self):
        """Create the results panel"""
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
        layout.setContentsMargins(30, 30, 30, 30)

        # Panel title
        title = QLabel("Analysis Results")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #9b59b6;
                border-radius: 3px;
            }
        """)

        # Results display
        results_group = QGroupBox("Detection Results")
        results_layout = QVBoxLayout(results_group)

        self.results_text = QTextEdit()
        self.results_text.setPlaceholderText(
            "Analysis results will appear here...")
        self.results_text.setReadOnly(True)

        results_layout.addWidget(self.results_text)

        # Statistics display
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout(stats_group)

        self.stats_text = QTextEdit()
        self.stats_text.setPlaceholderText(
            "Statistical analysis will appear here...")
        self.stats_text.setMaximumHeight(150)
        self.stats_text.setReadOnly(True)

        stats_layout.addWidget(self.stats_text)

        # Export button
        export_button = QPushButton("Export Report")
        export_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        export_button.clicked.connect(self.export_report)

        layout.addWidget(title)
        layout.addWidget(self.progress_bar)
        layout.addWidget(results_group)
        layout.addWidget(stats_group)
        layout.addWidget(export_button)
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

    def update_method_description(self, method_name: str, description_widget: QLabel):
        """Update the method description based on selected method"""
        description = self.method_descriptions.get(method_name, "No description available for this method.")
        description_widget.setText(description)

    def on_image_method_changed(self):
        """Handle image method dropdown change"""
        method = self.method_combo.currentText()
        self.update_method_description(method, self.image_method_description)

    def on_audio_method_changed(self):
        """Handle audio method dropdown change"""
        method = self.audio_method_combo.currentText()
        self.update_method_description(method, self.audio_method_description)

    def on_video_method_changed(self):
        """Handle video method dropdown change"""
        method = self.video_method_combo.currentText()
        self.update_method_description(method, self.video_method_description)

    def create_image_preview(self, image_path: str):
        """Create a preview of the selected image"""
        try:
            # Load and resize image while maintaining aspect ratio
            img = Image.open(image_path)
            
            # Calculate new size maintaining aspect ratio, fitting within max height
            max_width = 300
            max_height = 200
            
            # Get original dimensions
            original_width, original_height = img.size
            
            # Calculate scaling factor to fit within max dimensions
            width_ratio = max_width / original_width
            height_ratio = max_height / original_height
            scale_factor = min(width_ratio, height_ratio)
            
            # Calculate new dimensions
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            
            # Resize image
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to QPixmap
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            pixmap = QPixmap()
            pixmap.loadFromData(img_bytes.getvalue())
            
            # Set the preview
            self.image_preview.setPixmap(pixmap)
            self.image_preview.setText("")
            
        except Exception as e:
            self.image_preview.setText(f"Error loading preview: {str(e)}")

    def create_audio_preview(self, audio_path: str):
        """Create a waveform preview of the selected audio"""
        try:
            
            # Read WAV file
            with wave.open(audio_path, "rb") as wf:
                n_channels = wf.getnchannels()
                n_frames = wf.getnframes()
                sample_width = wf.getsampwidth()
                framerate = wf.getframerate()
                duration = n_frames / float(framerate)

                # Extract raw audio
                frames = wf.readframes(n_frames)
                audio_data = np.frombuffer(frames, dtype=np.int16)

                if n_channels > 1:
                    audio_data = audio_data[::n_channels]  # take left channel if stereo

            # Plot waveform (downsample if too large)
            max_points = 1000
            if len(audio_data) > max_points:
                factor = len(audio_data) // max_points
                audio_data = audio_data[::factor]

            plt.figure(figsize=(4, 2))
            plt.plot(audio_data, color="blue")
            plt.axis("off")
            plt.tight_layout()

            # Save plot to QPixmap
            import io
            buf = io.BytesIO()
            plt.savefig(buf, format="png")
            buf.seek(0)
            plt.close()

            pixmap = QPixmap()
            pixmap.loadFromData(buf.getvalue())

            # Set to QLabel
            self.audio_preview.setPixmap(pixmap)
            self.audio_preview.setText("")

        except Exception as e:
            self.audio_preview.setText(f"Error loading audio preview: {str(e)}")

    def create_video_preview(self, video_path: str):
        """Create a frame preview of the selected video"""
        try:

            # Open video file
            cap = cv2.VideoCapture(video_path)
            success, frame = cap.read()
            cap.release()

            if not success or frame is None:
                self.video_preview.setText("Error: Could not extract frame")
                return

            # Convert BGR (OpenCV) → RGB (Qt/PIL)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Resize frame for preview while maintaining aspect ratio
            from PIL import Image
            img = Image.fromarray(frame_rgb)
            
            # Calculate new size maintaining aspect ratio, fitting within max height
            max_width = 300
            max_height = 180
            
            # Get original dimensions
            original_width, original_height = img.size
            
            # Calculate scaling factor to fit within max dimensions
            width_ratio = max_width / original_width
            height_ratio = max_height / original_height
            scale_factor = min(width_ratio, height_ratio)
            
            # Calculate new dimensions
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            
            # Resize image
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert to QPixmap
            import io
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            pixmap = QPixmap()
            pixmap.loadFromData(img_bytes.getvalue())

            # Set the preview
            self.video_preview.setPixmap(pixmap)
            self.video_preview.setText("")

        except Exception as e:
            self.video_preview.setText(f"Error loading video preview: {str(e)}")

    def go_to_previous_page(self):
        """Navigate to the previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.stacked_widget.setCurrentIndex(self.current_page)
            self.update_navigation_buttons()

    def go_to_next_page(self):
        """Navigate to the next page"""
        if self.current_page < self.stacked_widget.count() - 1:
            self.current_page += 1
            self.stacked_widget.setCurrentIndex(self.current_page)
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        """Update navigation button states and page indicator"""
        total_pages = self.stacked_widget.count()
        
        # Update button states
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)
        
        # Update page indicator
        page_names = ["Image Analysis", "Audio Analysis", "Video Analysis"]
        current_page_name = page_names[self.current_page] if self.current_page < len(page_names) else f"Page {self.current_page + 1}"
        self.page_indicator.setText(f"{current_page_name} ({self.current_page + 1} of {total_pages})")
        
        # Update button text
        if self.current_page == 0:
            self.prev_button.setText("← Image Analysis")
            self.next_button.setText("Next →")
        elif self.current_page == 1:
            self.prev_button.setText("← Previous")
            self.next_button.setText("Next →")
        else:
            self.prev_button.setText("← Previous")
            self.next_button.setText("Video Analysis →")

    def browse_image(self):
        """Browse for image to analyze"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image to Analyze", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        if file_path:
            self.image_path.setText(file_path)
            # Load into machine
            if self.machine.set_image(file_path):
                self.results_text.append(f"Image selected: {file_path}")
                # Create preview
                self.create_image_preview(file_path)
            else:
                self.results_text.append(f"Error loading image: {file_path}")

    def browse_audio(self):
        """Browse for audio to analyze"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio to Analyze", "",
            "WAV Files (*.wav)"
        )
        if file_path:
            self.audio_path.setText(file_path)
            if self.machine.set_audio(file_path):
                self.results_text.append(f"Audio selected: {file_path}")
                # Create preview
                self.create_audio_preview(file_path)
            else:
                self.results_text.append(f"Error loading audio: {file_path}")

    def browse_video(self):
        """Browse for video to analyze"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video to Analyze", "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv)"
        )
        if file_path:
            self.video_path.setText(file_path)
            if self.machine.set_video(file_path):
                self.results_text.append(f"Video selected: {file_path}")
                # Create preview
                self.create_video_preview(file_path)
            else:
                self.results_text.append(f"Error loading video: {file_path}")

    def analyze_image(self):
        """Analyze the selected image"""
        if not self.image_path.text():
            self.results_text.append("Error: Please select an image to analyze")
            return

        # Clear old outputs
        self.results_text.clear()
        self.stats_text.clear()

        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        QApplication.processEvents()

        # Load image into the machine
        success = self.machine.set_image(self.image_path.text())
        if not success:
            self.results_text.append("Error: Failed to load image for analysis")
            self.progress_bar.setVisible(False)
            return

        # Set selected analysis method
        method = self.method_combo.currentText()
        self.machine.set_analysis_method(method)

        # Run analysis
        if self.machine.analyze_image():
            results = self.machine.get_results()
            stats = self.machine.get_statistics()
            confidence = self.machine.get_confidence_level()

            # === Results section ===
            self.results_text.append("\n=== ANALYSIS COMPLETE ===")
            self.results_text.append(f"Method: {results.get('method')}")
            self.results_text.append(f"Suspicious: {results.get('suspicious')}")
            self.results_text.append(f"Confidence level: {confidence:.2%}\n")

            # Helper function to pretty print nested dicts
            def print_dict(d: dict, indent: int = 0):
                for key, value in d.items():
                    if isinstance(value, dict):
                        self.results_text.append(" " * indent + f"{key}:")
                        print_dict(value, indent + 4)
                    else:
                        self.results_text.append(" " * indent + f"- {key}: {value}")

            # Print details (skip redundant top-level keys)
            for key, value in results.items():
                if key in ['method', 'suspicious']:
                    continue
                if isinstance(value, dict):
                    self.results_text.append(f"{key}:")
                    print_dict(value, 4)
                else:
                    self.results_text.append(f"{key}: {value}")

            # === Stats section ===
            self.stats_text.append("Image Statistics:")
            for key, value in stats.items():
                self.stats_text.append(f"- {key}: {value}")

        else:
            self.results_text.append("Error: Analysis failed")

        # Hide progress bar
        self.progress_bar.setVisible(False)

    def analyze_audio(self):
        """Analyze the selected audio"""
        if not self.audio_path.text():
            self.results_text.append(
                "Error: Please select an audio file to analyze")
            return

        method = self.audio_method_combo.currentText()
        ok = self.machine.analyze_audio(method)

        self.results_text.append("\n=== AUDIO ANALYSIS ===")
        if not ok:
            self.results_text.append("Error during audio analysis.")
            return

        results = self.machine.get_results()
        confidence = self.machine.get_confidence_level()
        stats = self.machine.get_audio_statistics()

        self.results_text.append(f"Method: {results.get('method', method)}")
        self.results_text.append(f"Suspicious: {results.get('suspicious', False)}")
        for k, v in results.items():
            if k in ("method", "suspicious"):
                continue
            self.results_text.append(f"{k}: {v}")

        self.results_text.append(f"Confidence level: {confidence*100:.2f}%")

        self.stats_text.append("Audio Statistics:")
        for k, v in stats.items():
            self.stats_text.append(f"- {k}: {v}")

    def analyze_video(self):
        """Analyze the selected video"""
        if not self.video_path.text():
            self.results_text.append("Error: Please select a video file to analyze")
            return

        method = self.video_method_combo.currentText()
        ok = self.machine.analyze_video(method)

        self.results_text.append("\n=== VIDEO ANALYSIS ===")
        if not ok:
            self.results_text.append("Error during video analysis.")
            return

        results = self.machine.get_results()
        confidence = self.machine.get_confidence_level()
        stats = self.machine.get_video_statistics()

        self.results_text.append(f"Method: {results.get('method', method)}")
        self.results_text.append(f"Suspicious: {results.get('suspicious', False)}")
        for k, v in results.items():
            if k in ("method", "suspicious"):
                continue
            self.results_text.append(f"{k}: {v}")

        self.results_text.append(f"Confidence level: {confidence*100:.2f}%")

        self.stats_text.append("Video Statistics:")
        for k, v in stats.items():
            self.stats_text.append(f"- {k}: {v}")

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
                self.results_text.append(f"Report exported to: {file_path}")
            else:
                self.results_text.append("Error: Could not export report.")

    def go_back(self):
        """Go back to main window"""
        # Clean up machine resources
        self.machine.cleanup()

        from gui.main_window import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()
