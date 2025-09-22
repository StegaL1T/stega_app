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
                             QStackedWidget, QHBoxLayout, QSizePolicy, QTabWidget)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QPen
import numpy as np
import cv2

# Matplotlib for charts (QtAgg backend for PyQt6)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_pdf import PdfPages


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
                background: #e3f2fd;
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

        # Main content area (tabs)
        self.create_tabs(main_layout)

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



    def create_tabs(self, layout):
        """Create Image/Audio/Video steganalysis tabs"""
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.setTabPosition(QTabWidget.TabPosition.North)

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
            QFrame { background-color: white; border-radius: 15px; border: none; }
        """)
        panel.setGraphicsEffect(self.create_shadow_effect())
        return panel

    def _build_image_controls(self) -> QWidget:
        panel = self._styled_panel()
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Image Analysis Input")
        f = QFont(); f.setPointSize(20); f.setBold(True)
        title.setFont(f)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")

        image_group = QGroupBox("Suspicious Image")
        image_layout = QVBoxLayout(image_group)
        self.image_path = QLineEdit(); self.image_path.setPlaceholderText("Select image to analyze..."); self.image_path.setReadOnly(True)
        browse_button = QPushButton("Browse Image")
        browse_button.setStyleSheet("""
            QPushButton { background-color: #9b59b6; color: white; border: none; padding: 8px 16px; border-radius: 5px; }
            QPushButton:hover { background-color: #8e44ad; }
        """)
        browse_button.clicked.connect(self.browse_image)
        image_layout.addWidget(self.image_path)
        image_layout.addWidget(browse_button)

        method_group = QGroupBox("Image Analysis Method")
        method_layout = QVBoxLayout(method_group)
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "LSB Analysis","Chi-Square Test","RS Analysis","Sample Pairs Analysis",
            "DCT Analysis","Wavelet Analysis","Histogram Analysis","Comprehensive Analysis","Advanced Comprehensive"
        ])
        self.method_combo.setStyleSheet("""
            QComboBox { padding: 8px; border: 2px solid #bdc3c7; border-radius: 5px; background-color: white; }
            QComboBox:focus { border-color: #9b59b6; }
        """)
        self.method_combo.currentTextChanged.connect(self.on_image_method_changed)
        method_layout.addWidget(self.method_combo)

        self.img_analyze_btn = QPushButton("Analyze Image")
        self.img_analyze_btn.setStyleSheet("""
            QPushButton { background-color: #e74c3c; color: white; border: none; padding: 12px 24px; border-radius: 5px; font-size: 16px; font-weight: bold; }
            QPushButton:hover { background-color: #c0392b; }
        """)
        self.img_analyze_btn.clicked.connect(self.analyze_image)

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
        layout.addWidget(self.img_analyze_btn)
        layout.addWidget(self.image_method_description)
        layout.addStretch()
        return panel

    def _build_image_results(self) -> QWidget:
        panel = self._styled_panel()
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Image Analysis Results")
        f = QFont(); f.setPointSize(20); f.setBold(True)
        title.setFont(f)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")

        self.img_progress_bar = QProgressBar(); self.img_progress_bar.setVisible(False)
        self.img_progress_bar.setStyleSheet("""
            QProgressBar { border: 2px solid #bdc3c7; border-radius: 5px; text-align: center; background-color: #ecf0f1; }
            QProgressBar::chunk { background-color: #9b59b6; border-radius: 3px; }
        """)

        img_results_group = QGroupBox("Detection Results")
        img_results_layout = QVBoxLayout(img_results_group)
        self.img_results_text = QTextEdit(); self.img_results_text.setReadOnly(True)
        self.img_results_text.setPlaceholderText("Analysis results will appear here...")
        img_results_layout.addWidget(self.img_results_text)

        # Image charts
        image_charts_group = QGroupBox("Image Charts")
        image_charts_layout = QGridLayout(image_charts_group)
        # Larger canvases for readability
        self.img_canvas_lsb = FigureCanvas(Figure(figsize=(4, 4), dpi=100))
        self.img_canvas_diff = FigureCanvas(Figure(figsize=(4, 4), dpi=100))
        self.img_canvas_hist = FigureCanvas(Figure(figsize=(8, 3), dpi=100))
        # Ensure minimum display size ~400x400 for image plots
        self.img_canvas_lsb.setMinimumSize(400, 400)
        self.img_canvas_diff.setMinimumSize(400, 400)
        # Histogram full-width and taller
        self.img_canvas_hist.setMinimumHeight(300)
        image_charts_layout.addWidget(self.img_canvas_lsb, 0, 0)
        image_charts_layout.addWidget(self.img_canvas_diff, 0, 1)
        image_charts_layout.addWidget(self.img_canvas_hist, 1, 0, 1, 2)

        img_stats_group = QGroupBox("Statistics")
        img_stats_layout = QVBoxLayout(img_stats_group)
        self.img_stats_text = QTextEdit(); self.img_stats_text.setReadOnly(True); self.img_stats_text.setMaximumHeight(150)
        self.img_stats_text.setPlaceholderText("Image statistics will appear here...")
        img_stats_layout.addWidget(self.img_stats_text)

        layout.addWidget(title)
        layout.addWidget(self.img_progress_bar)
        layout.addWidget(img_results_group)
        layout.addWidget(image_charts_group)
        layout.addWidget(img_stats_group)
        # Export charts to PDF button
        export_img_pdf_btn = QPushButton("Export Charts to PDF")
        export_img_pdf_btn.setStyleSheet("""
            QPushButton { background-color: #2ecc71; color: white; border: none; padding: 10px 20px; border-radius: 5px; font-weight: bold; }
            QPushButton:hover { background-color: #27ae60; }
        """)
        export_img_pdf_btn.clicked.connect(self.export_charts_pdf)
        layout.addWidget(export_img_pdf_btn)
        layout.addStretch()
        return panel

    def _build_audio_controls(self) -> QWidget:
        panel = self._styled_panel()
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Audio Analysis Input")
        f = QFont(); f.setPointSize(20); f.setBold(True)
        title.setFont(f)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")

        audio_group = QGroupBox("Suspicious Audio")
        audio_layout = QVBoxLayout(audio_group)
        self.audio_path = QLineEdit(); self.audio_path.setPlaceholderText("Select WAV audio to analyze..."); self.audio_path.setReadOnly(True)
        browse_audio_button = QPushButton("Browse Audio")
        browse_audio_button.setStyleSheet("""
            QPushButton { background-color: #3498db; color: white; border: none; padding: 8px 16px; border-radius: 5px; }
            QPushButton:hover { background-color: #2980b9; }
        """)
        browse_audio_button.clicked.connect(self.browse_audio)
        audio_layout.addWidget(self.audio_path)
        audio_layout.addWidget(browse_audio_button)

        audio_method_group = QGroupBox("Audio Analysis Method")
        audio_method_layout = QVBoxLayout(audio_method_group)
        self.audio_method_combo = QComboBox()
        self.audio_method_combo.addItems([
            "Audio LSB Analysis","Audio Chi-Square Test","Audio Spectral Analysis",
            "Audio Autocorrelation Analysis","Audio Entropy Analysis","Audio Comprehensive Analysis","Audio Advanced Comprehensive"
        ])
        self.audio_method_combo.setStyleSheet("""
            QComboBox { padding: 8px; border: 2px solid #bdc3c7; border-radius: 5px; background-color: white; }
            QComboBox:focus { border-color: #3498db; }
        """)
        self.audio_method_combo.currentTextChanged.connect(self.on_audio_method_changed)
        audio_method_layout.addWidget(self.audio_method_combo)

        self.aud_analyze_btn = QPushButton("Analyze Audio")
        self.aud_analyze_btn.setStyleSheet("""
            QPushButton { background-color: #16a085; color: white; border: none; padding: 12px 24px; border-radius: 5px; font-size: 16px; font-weight: bold; }
            QPushButton:hover { background-color: #138d75; }
        """)
        self.aud_analyze_btn.clicked.connect(self.analyze_audio)

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
        layout.addWidget(self.aud_analyze_btn)
        layout.addWidget(self.audio_method_description)
        layout.addStretch()
        return panel

    def _build_audio_results(self) -> QWidget:
        panel = self._styled_panel()
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Audio Analysis Results")
        f = QFont(); f.setPointSize(20); f.setBold(True)
        title.setFont(f)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")

        aud_results_group = QGroupBox("Detection Results")
        aud_results_layout = QVBoxLayout(aud_results_group)
        self.aud_results_text = QTextEdit(); self.aud_results_text.setReadOnly(True)
        self.aud_results_text.setPlaceholderText("Analysis results will appear here...")
        aud_results_layout.addWidget(self.aud_results_text)

        audio_charts_group = QGroupBox("Audio Charts")
        audio_charts_layout = QGridLayout(audio_charts_group)
        self.aud_canvas_wave = FigureCanvas(Figure(figsize=(3, 2)))
        self.aud_canvas_spec = FigureCanvas(Figure(figsize=(3, 2)))
        self.aud_canvas_entropy = FigureCanvas(Figure(figsize=(3, 2)))
        audio_charts_layout.addWidget(self.aud_canvas_wave, 0, 0)
        audio_charts_layout.addWidget(self.aud_canvas_spec, 0, 1)
        audio_charts_layout.addWidget(self.aud_canvas_entropy, 1, 0, 1, 2)

        aud_stats_group = QGroupBox("Statistics")
        aud_stats_layout = QVBoxLayout(aud_stats_group)
        self.aud_stats_text = QTextEdit(); self.aud_stats_text.setReadOnly(True); self.aud_stats_text.setMaximumHeight(150)
        self.aud_stats_text.setPlaceholderText("Audio statistics will appear here...")
        aud_stats_layout.addWidget(self.aud_stats_text)

        export_button = QPushButton("Export Report")
        export_button.setStyleSheet("""
            QPushButton { background-color: #f39c12; color: white; border: none; padding: 10px 20px; border-radius: 5px; font-weight: bold; }
            QPushButton:hover { background-color: #e67e22; }
        """)
        export_button.clicked.connect(self.export_report)

        # Export charts to PDF button
        export_aud_pdf_btn = QPushButton("Export Charts to PDF")
        export_aud_pdf_btn.setStyleSheet("""
            QPushButton { background-color: #2ecc71; color: white; border: none; padding: 10px 20px; border-radius: 5px; font-weight: bold; }
            QPushButton:hover { background-color: #27ae60; }
        """)
        export_aud_pdf_btn.clicked.connect(self.export_charts_pdf)

        layout.addWidget(title)
        layout.addWidget(aud_results_group)
        layout.addWidget(audio_charts_group)
        layout.addWidget(aud_stats_group)
        layout.addWidget(export_aud_pdf_btn)
        layout.addWidget(export_button)
        layout.addStretch()
        return panel

    def _build_video_controls(self) -> QWidget:
        panel = self._styled_panel()
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Video Analysis Input")
        f = QFont(); f.setPointSize(20); f.setBold(True)
        title.setFont(f)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")

        video_group = QGroupBox("Suspicious Video")
        video_layout = QVBoxLayout(video_group)
        self.video_path = QLineEdit(); self.video_path.setPlaceholderText("Select video to analyze..."); self.video_path.setReadOnly(True)
        browse_video_button = QPushButton("Browse Video")
        browse_video_button.setStyleSheet("""
            QPushButton { background-color: #e67e22; color: white; border: none; padding: 8px 16px; border-radius: 5px; }
            QPushButton:hover { background-color: #d35400; }
        """)
        browse_video_button.clicked.connect(self.browse_video)
        video_layout.addWidget(self.video_path)
        video_layout.addWidget(browse_video_button)

        # Video preview
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
        self.video_preview.setScaledContents(False)
        video_layout.addWidget(self.video_preview)

        video_method_group = QGroupBox("Video Analysis Method")
        video_method_layout = QVBoxLayout(video_method_group)
        self.video_method_combo = QComboBox()
        self.video_method_combo.addItems([
            "Video LSB Analysis","Video Frame Analysis","Video Motion Analysis",
            "Video Comprehensive Analysis","Video Advanced Comprehensive"
        ])
        self.video_method_combo.setStyleSheet("""
            QComboBox { padding: 8px; border: 2px solid #bdc3c7; border-radius: 5px; background-color: white; }
            QComboBox:focus { border-color: #e67e22; }
        """)
        self.video_method_combo.currentTextChanged.connect(self.on_video_method_changed)
        video_method_layout.addWidget(self.video_method_combo)

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

        self.vid_analyze_btn = QPushButton("Analyze Video")
        self.vid_analyze_btn.setStyleSheet("""
            QPushButton { background-color: #8e44ad; color: white; border: none; padding: 12px 24px; border-radius: 5px; font-size: 16px; font-weight: bold; }
            QPushButton:hover { background-color: #7d3c98; }
        """)
        self.vid_analyze_btn.clicked.connect(self.analyze_video)

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

        title = QLabel("Video Analysis Results")
        f = QFont(); f.setPointSize(20); f.setBold(True)
        title.setFont(f)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")

        self.vid_progress_bar = QProgressBar(); self.vid_progress_bar.setVisible(False)
        self.vid_progress_bar.setStyleSheet("""
            QProgressBar { border: 2px solid #bdc3c7; border-radius: 5px; text-align: center; background-color: #ecf0f1; }
            QProgressBar::chunk { background-color: #8e44ad; border-radius: 3px; }
        """)

        vid_results_group = QGroupBox("Detection Results")
        vid_results_layout = QVBoxLayout(vid_results_group)
        self.vid_results_text = QTextEdit(); self.vid_results_text.setReadOnly(True)
        self.vid_results_text.setPlaceholderText("Analysis results will appear here...")
        vid_results_layout.addWidget(self.vid_results_text)

        # Video charts
        video_charts_group = QGroupBox("Video Charts")
        video_charts_layout = QGridLayout(video_charts_group)
        self.vid_canvas_frame = FigureCanvas(Figure(figsize=(4, 3), dpi=100))
        self.vid_canvas_motion = FigureCanvas(Figure(figsize=(4, 3), dpi=100))
        self.vid_canvas_lsb = FigureCanvas(Figure(figsize=(8, 3), dpi=100))
        self.vid_canvas_frame.setMinimumSize(400, 300)
        self.vid_canvas_motion.setMinimumSize(400, 300)
        self.vid_canvas_lsb.setMinimumHeight(300)
        video_charts_layout.addWidget(self.vid_canvas_frame, 0, 0)
        video_charts_layout.addWidget(self.vid_canvas_motion, 0, 1)
        video_charts_layout.addWidget(self.vid_canvas_lsb, 1, 0, 1, 2)

        vid_stats_group = QGroupBox("Statistics")
        vid_stats_layout = QVBoxLayout(vid_stats_group)
        self.vid_stats_text = QTextEdit(); self.vid_stats_text.setReadOnly(True); self.vid_stats_text.setMaximumHeight(150)
        self.vid_stats_text.setPlaceholderText("Video statistics will appear here...")
        vid_stats_layout.addWidget(self.vid_stats_text)

        # Export charts to PDF button
        export_vid_pdf_btn = QPushButton("Export Charts to PDF")
        export_vid_pdf_btn.setStyleSheet("""
            QPushButton { background-color: #2ecc71; color: white; border: none; padding: 10px 20px; border-radius: 5px; font-weight: bold; }
            QPushButton:hover { background-color: #27ae60; }
        """)
        export_vid_pdf_btn.clicked.connect(self.export_charts_pdf)

        layout.addWidget(title)
        layout.addWidget(self.vid_progress_bar)
        layout.addWidget(vid_results_group)
        layout.addWidget(video_charts_group)
        layout.addWidget(vid_stats_group)
        layout.addWidget(export_vid_pdf_btn)
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
                # Create preview
                self.create_image_preview(file_path)
                if hasattr(self, 'img_results_text'):
                    self.img_results_text.append(f"Image selected: {file_path}")
            else:
                if hasattr(self, 'img_results_text'):
                    self.img_results_text.append(f"Error loading image: {file_path}")

    def browse_audio(self):
        """Browse for audio to analyze"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio to Analyze", "",
            "WAV Files (*.wav)"
        )
        if file_path:
            self.audio_path.setText(file_path)
            if self.machine.set_audio(file_path):
                # Create preview
                self.create_audio_preview(file_path)
                if hasattr(self, 'aud_results_text'):
                    self.aud_results_text.append(f"Audio selected: {file_path}")
            else:
                if hasattr(self, 'aud_results_text'):
                    self.aud_results_text.append(f"Error loading audio: {file_path}")

    def browse_video(self):
        """Browse for video to analyze"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video to Analyze", "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv)"
        )
        if file_path:
            self.video_path.setText(file_path)
            if self.machine.set_video(file_path):
                # Create preview
                self.create_video_preview(file_path)
                if hasattr(self, 'vid_results_text'):
                    self.vid_results_text.append(f"Video selected: {file_path}")
            else:
                if hasattr(self, 'vid_results_text'):
                    self.vid_results_text.append(f"Error loading video: {file_path}")

    def analyze_image(self):
        """Analyze the selected image"""
        if not self.image_path.text():
            self.img_results_text.append("Error: Please select an image to analyze")
            return

        # Clear old outputs
        self.img_results_text.clear()
        self.img_stats_text.clear()

        # Show progress bar
        self.img_progress_bar.setVisible(True)
        self.img_progress_bar.setValue(0)
        QApplication.processEvents()

        # Load image into the machine
        success = self.machine.set_image(self.image_path.text())
        if not success:
            self.img_results_text.append("Error: Failed to load image for analysis")
            self.img_progress_bar.setVisible(False)
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
            self.img_results_text.append("\n=== ANALYSIS COMPLETE ===")
            self.img_results_text.append(f"Method: {results.get('method')}")
            self.img_results_text.append(f"Suspicious: {results.get('suspicious')}")
            self.img_results_text.append(f"Confidence level: {confidence:.2%}\n")

            # Helper function to pretty print nested dicts
            def print_dict(d: dict, indent: int = 0):
                for key, value in d.items():
                    if isinstance(value, dict):
                        self.img_results_text.append(" " * indent + f"{key}:")
                        print_dict(value, indent + 4)
                    else:
                        self.img_results_text.append(" " * indent + f"- {key}: {value}")

            # Print details (skip redundant top-level keys)
            for key, value in results.items():
                if key in ['method', 'suspicious']:
                    continue
                if isinstance(value, dict):
                    self.img_results_text.append(f"{key}:")
                    print_dict(value, 4)
                else:
                    self.img_results_text.append(f"{key}: {value}")

            # === Stats section ===
            self.img_stats_text.append("Image Statistics:")
            for key, value in stats.items():
                self.img_stats_text.append(f"- {key}: {value}")

            # === Charts ===
            try:
                self._plot_image_charts()
            except Exception as e:
                self.img_results_text.append(f"Chart error: {e}")

        else:
            self.img_results_text.append("Error: Analysis failed")

        # Hide progress bar
        self.img_progress_bar.setVisible(False)

    def analyze_audio(self):
        """Analyze the selected audio"""
        if not self.audio_path.text():
            self.aud_results_text.append(
                "Error: Please select an audio file to analyze")
            return

        method = self.audio_method_combo.currentText()
        ok = self.machine.analyze_audio(method)

        self.aud_results_text.append("\n=== AUDIO ANALYSIS ===")
        if not ok:
            self.aud_results_text.append("Error during audio analysis.")
            return

        results = self.machine.get_results()
        confidence = self.machine.get_confidence_level()
        stats = self.machine.get_audio_statistics()

        self.aud_results_text.append(f"Method: {results.get('method', method)}")
        self.aud_results_text.append(f"Suspicious: {results.get('suspicious', False)}")
        for k, v in results.items():
            if k in ("method", "suspicious"):
                continue
            self.aud_results_text.append(f"{k}: {v}")

        self.aud_results_text.append(f"Confidence level: {confidence*100:.2f}%")

        self.aud_stats_text.append("Audio Statistics:")
        for k, v in stats.items():
            self.aud_stats_text.append(f"- {k}: {v}")

        # === Charts ===
        try:
            self._plot_audio_charts()
        except Exception as e:
            self.aud_results_text.append(f"Audio chart error: {e}")

    def analyze_video(self):
        """Analyze the selected video"""
        if not self.video_path.text():
            self.vid_results_text.append("Error: Please select a video file to analyze")
            return

        # Clear old outputs
        self.vid_results_text.clear()
        self.vid_stats_text.clear()

        # Show progress bar
        self.vid_progress_bar.setVisible(True)
        self.vid_progress_bar.setValue(0)
        QApplication.processEvents()

        # Load video into the machine
        success = self.machine.set_video(self.video_path.text())
        if not success:
            self.vid_results_text.append("Error: Failed to load video for analysis")
            self.vid_progress_bar.setVisible(False)
            return

        # Set selected analysis method
        method = self.video_method_combo.currentText()
        
        # Run analysis
        if self.machine.analyze_video(method):
            results = self.machine.get_results()
            stats = self.machine.get_video_statistics()
            confidence = self.machine.get_confidence_level()

            # === Results section ===
            self.vid_results_text.append("\n=== VIDEO ANALYSIS COMPLETE ===")
            self.vid_results_text.append(f"Method: {results.get('method')}")
            self.vid_results_text.append(f"Suspicious: {results.get('suspicious')}")
            self.vid_results_text.append(f"Confidence level: {confidence:.2%}\n")

            # Helper function to pretty print nested dicts
            def print_dict(d: dict, indent: int = 0):
                for key, value in d.items():
                    if isinstance(value, dict):
                        self.vid_results_text.append(" " * indent + f"{key}:")
                        print_dict(value, indent + 4)
                    else:
                        self.vid_results_text.append(" " * indent + f"- {key}: {value}")

            # Print details (skip redundant top-level keys)
            for key, value in results.items():
                if key in ['method', 'suspicious']:
                    continue
                if isinstance(value, dict):
                    self.vid_results_text.append(f"{key}:")
                    print_dict(value, 4)
                else:
                    self.vid_results_text.append(f"{key}: {value}")

            # === Stats section ===
            self.vid_stats_text.append("Video Statistics:")
            for key, value in stats.items():
                self.vid_stats_text.append(f"- {key}: {value}")

            # === Charts ===
            try:
                self._plot_video_charts()
            except Exception as e:
                self.vid_results_text.append(f"Chart error: {e}")

        else:
            self.vid_results_text.append("Error: Analysis failed")

        # Hide progress bar
        self.vid_progress_bar.setVisible(False)

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

    def go_back(self):
        """Go back to main window"""
        # Clean up machine resources
        self.machine.cleanup()

        from gui.main_window import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()

    # ======== Chart helpers ========
    def _plot_image_charts(self):
        """Render LSB Plane, Difference Map, and Histogram for the current image."""
        img = self.machine.image_array
        if img is None:
            return

        # Ensure RGB uint8
        if img.dtype != np.uint8:
            img = img.astype(np.uint8)

        # LSB Plane (combined across channels as mean of LSBs)
        ax_lsb = self.img_canvas_lsb.figure.subplots(1, 1)
        self.img_canvas_lsb.figure.tight_layout()
        ax_lsb.clear()
        lsb = (img & 1)
        if lsb.ndim == 3:
            lsb_vis = (np.mean(lsb, axis=2) * 255).astype(np.uint8)
        else:
            lsb_vis = (lsb * 255).astype(np.uint8)
        ax_lsb.imshow(lsb_vis, cmap='gray')
        ax_lsb.set_title('LSB Plane', fontsize=11)
        ax_lsb.axis('off')
        self.img_canvas_lsb.draw()

        # Difference Map (residual to blurred image)
        ax_diff = self.img_canvas_diff.figure.subplots(1, 1)
        self.img_canvas_diff.figure.tight_layout()
        ax_diff.clear()
        blurred = cv2.GaussianBlur(img, (5, 5), 0)
        residual = cv2.absdiff(img, blurred)
        residual_gray = cv2.cvtColor(residual, cv2.COLOR_BGR2GRAY) if residual.ndim == 3 else residual
        ax_diff.imshow(residual_gray, cmap='inferno')
        ax_diff.set_title('Difference Map', fontsize=11)
        ax_diff.axis('off')
        self.img_canvas_diff.draw()

        # Histogram (all channels)
        ax_hist = self.img_canvas_hist.figure.subplots(1, 1)
        self.img_canvas_hist.figure.tight_layout()
        ax_hist.clear()
        colors = ('r', 'g', 'b') if (img.ndim == 3 and img.shape[2] == 3) else ('k',)
        if len(colors) == 3:
            for i, c in enumerate(colors):
                hist = cv2.calcHist([img], [i], None, [256], [0, 256]).flatten()
                ax_hist.plot(hist, color=c, label=f'Channel {c.upper()}')
        else:
            hist, _ = np.histogram(img.flatten(), bins=256, range=(0, 256))
            ax_hist.plot(hist, color='k', label='Gray')
        ax_hist.set_title('Histogram', fontsize=12)
        ax_hist.set_xlabel('Pixel value', fontsize=10)
        ax_hist.set_ylabel('Count', fontsize=10)
        ax_hist.set_xlim(0, 255)
        ax_hist.legend(loc='upper right', fontsize=9)
        ax_hist.grid(True, alpha=0.2)
        self.img_canvas_hist.draw()

    def _plot_audio_charts(self):
        """Render Waveform, Spectrogram, and Entropy for the current audio."""
        samples = self.machine.audio_samples
        sr = self.machine.audio_sample_rate
        if samples is None or not sr:
            return

        # Use first channel if stereo
        if samples.ndim == 2:
            data = samples[:, 0]
        else:
            data = samples

        data = data.astype(np.float32)

        # Waveform
        ax_wave = self.aud_canvas_wave.figure.subplots(1, 1)
        self.aud_canvas_wave.figure.tight_layout()
        ax_wave.clear()
        t = np.arange(len(data)) / float(sr)
        ax_wave.plot(t, data, color='#34495e', linewidth=0.8)
        ax_wave.set_title('Waveform')
        ax_wave.set_xlabel('Time (s)')
        ax_wave.set_ylabel('Amplitude')
        ax_wave.grid(True, alpha=0.2)
        self.aud_canvas_wave.draw()

        # Spectrogram (log-magnitude)
        ax_spec = self.aud_canvas_spec.figure.subplots(1, 1)
        self.aud_canvas_spec.figure.tight_layout()
        ax_spec.clear()
        nfft = 1024
        noverlap = 512
        Pxx, freqs, bins, im = ax_spec.specgram(data, NFFT=nfft, Fs=sr, noverlap=noverlap, cmap='magma')
        ax_spec.set_title('Spectrogram')
        ax_spec.set_xlabel('Time (s)')
        ax_spec.set_ylabel('Frequency (Hz)')
        self.aud_canvas_spec.draw()

        # Entropy over time (short-time 8-bit entropy)
        ax_ent = self.aud_canvas_entropy.figure.subplots(1, 1)
        self.aud_canvas_entropy.figure.tight_layout()
        ax_ent.clear()
        # Normalize to 8-bit range
        x = data - np.min(data)
        denom = (np.max(x) - np.min(x) + 1e-9)
        x = (x / denom * 255.0).astype(np.uint8)
        win = max(int(sr * 0.05), 256)  # 50 ms window
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
        ax_ent.plot(times, ent_values, color='#8e44ad', linewidth=1.2)
        ax_ent.set_title('Short-time Entropy')
        ax_ent.set_xlabel('Time (s)')
        ax_ent.set_ylabel('Entropy (bits)')
        ax_ent.grid(True, alpha=0.2)
        self.aud_canvas_entropy.draw()

    def _plot_video_charts(self):
        """Render Frame Analysis, Motion Analysis, and LSB Analysis for the current video."""
        frames = self.machine.video_frames
        if frames is None or len(frames) == 0:
            return

        # Sample frames for analysis (max 20 frames)
        sample_frames = frames[::max(1, len(frames)//20)]
        
        # Frame Analysis Chart
        ax_frame = self.vid_canvas_frame.figure.subplots(1, 1)
        self.vid_canvas_frame.figure.tight_layout()
        ax_frame.clear()
        
        # Calculate frame statistics
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
        ax_frame.plot(frame_nums, means, 'b-', label='Mean', linewidth=2)
        ax_frame.plot(frame_nums, stds, 'r-', label='Std Dev', linewidth=2)
        ax_frame.set_title('Frame Statistics', fontsize=12)
        ax_frame.set_xlabel('Frame Number')
        ax_frame.set_ylabel('Pixel Value')
        ax_frame.legend()
        ax_frame.grid(True, alpha=0.2)
        self.vid_canvas_frame.draw()

        # Motion Analysis Chart
        ax_motion = self.vid_canvas_motion.figure.subplots(1, 1)
        self.vid_canvas_motion.figure.tight_layout()
        ax_motion.clear()
        
        # Calculate motion between consecutive frames
        motion_values = []
        for i in range(1, len(sample_frames)):
            prev_frame = sample_frames[i-1]
            curr_frame = sample_frames[i]
            
            if prev_frame.ndim == 3:
                prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_RGB2GRAY)
                curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_RGB2GRAY)
            else:
                prev_gray = prev_frame
                curr_gray = curr_frame
            
            # Calculate frame difference
            diff = cv2.absdiff(prev_gray, curr_gray)
            motion = np.mean(diff)
            motion_values.append(motion)
        
        ax_motion.plot(range(1, len(sample_frames)), motion_values, 'g-', linewidth=2)
        ax_motion.set_title('Motion Analysis', fontsize=12)
        ax_motion.set_xlabel('Frame Number')
        ax_motion.set_ylabel('Motion Intensity')
        ax_motion.grid(True, alpha=0.2)
        self.vid_canvas_motion.draw()

        # LSB Analysis Chart
        ax_lsb = self.vid_canvas_lsb.figure.subplots(1, 1)
        self.vid_canvas_lsb.figure.tight_layout()
        ax_lsb.clear()
        
        # Calculate LSB ratios for each frame
        lsb_ratios = []
        for i, frame in enumerate(sample_frames):
            if frame.ndim == 3:
                # Use red channel for LSB analysis
                r_channel = frame[:, :, 0]
            else:
                r_channel = frame
            
            lsb_ratio = np.mean(r_channel & 1)
            lsb_ratios.append(lsb_ratio)
        
        ax_lsb.plot(range(len(sample_frames)), lsb_ratios, 'purple', linewidth=2, marker='o', markersize=4)
        ax_lsb.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='Expected (0.5)')
        ax_lsb.set_title('LSB Analysis Across Frames', fontsize=12)
        ax_lsb.set_xlabel('Frame Number')
        ax_lsb.set_ylabel('LSB Ratio')
        ax_lsb.set_ylim(0, 1)
        ax_lsb.legend()
        ax_lsb.grid(True, alpha=0.2)
        self.vid_canvas_lsb.draw()

    # ======== Export charts to PDF ========
    def export_charts_pdf(self):
        """Export currently displayed charts (image and/or audio) to a multi-page high-res PDF."""
        # Ask user where to save
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"steganalysis_charts_{timestamp}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Charts to PDF", default_name, "PDF Files (*.pdf)")
        if not file_path:
            return

        try:
            with PdfPages(file_path) as pdf:
                # Cover page with summary text
                fig_cover = Figure(figsize=(8.27, 11.69), dpi=200)  # A4 portrait
                axc = fig_cover.subplots(1, 1)
                axc.axis('off')
                lines = []
                # Basic summary details
                if getattr(self.machine, 'image_path', None):
                    lines.append(f"Image: {self.machine.image_path}")
                if getattr(self.machine, 'audio_path', None):
                    lines.append(f"Audio: {self.machine.audio_path}")
                lines.append(f"Confidence: {self.machine.get_confidence_level():.2%}")
                y = 0.95
                axc.text(0.05, y, "Steganalysis Charts", fontsize=16, weight='bold', transform=axc.transAxes)
                y -= 0.05
                for s in lines:
                    axc.text(0.05, y, s, fontsize=10, transform=axc.transAxes)
                    y -= 0.035
                pdf.savefig(fig_cover, bbox_inches='tight')
                
                # Image page: LSB + Diff side-by-side
                if hasattr(self, 'img_canvas_lsb') and hasattr(self, 'img_canvas_diff'):
                    fig_img = Figure(figsize=(11.69, 8.27), dpi=200)  # A4 landscape
                    ax1, ax2 = fig_img.subplots(1, 2)
                    # Recompute from machine to ensure high-res
                    img = self.machine.image_array
                    if img is not None:
                        if img.dtype != np.uint8:
                            img = img.astype(np.uint8)
                        lsb = (img & 1)
                        if lsb.ndim == 3:
                            lsb_vis = (np.mean(lsb, axis=2) * 255).astype(np.uint8)
                        else:
                            lsb_vis = (lsb * 255).astype(np.uint8)
                        ax1.imshow(lsb_vis, cmap='gray')
                        ax1.set_title('LSB Plane', fontsize=14)
                        ax1.axis('off')
                        blurred = cv2.GaussianBlur(img, (5, 5), 0)
                        residual = cv2.absdiff(img, blurred)
                        residual_gray = cv2.cvtColor(residual, cv2.COLOR_BGR2GRAY) if residual.ndim == 3 else residual
                        ax2.imshow(residual_gray, cmap='inferno')
                        ax2.set_title('Difference Map', fontsize=14)
                        ax2.axis('off')
                        pdf.savefig(fig_img, bbox_inches='tight')

                    # Histogram page full width
                    fig_hist = Figure(figsize=(11.69, 8.27), dpi=200)
                    axh = fig_hist.subplots(1, 1)
                    if img is not None:
                        colors = ('r', 'g', 'b') if (img.ndim == 3 and img.shape[2] == 3) else ('k',)
                        if len(colors) == 3:
                            for i, c in enumerate(colors):
                                hist = cv2.calcHist([img], [i], None, [256], [0, 256]).flatten()
                                axh.plot(hist, color=c, label=f'Channel {c.upper()}')
                        else:
                            hist, _ = np.histogram(img.flatten(), bins=256, range=(0, 256))
                            axh.plot(hist, color='k', label='Gray')
                        axh.set_title('Histogram', fontsize=16)
                        axh.set_xlabel('Pixel value', fontsize=12)
                        axh.set_ylabel('Count', fontsize=12)
                        axh.set_xlim(0, 255)
                        axh.legend(loc='upper right', fontsize=10)
                        axh.grid(True, alpha=0.2)
                        pdf.savefig(fig_hist, bbox_inches='tight')

                # Audio page(s): waveform + spectrogram + entropy
                samples = getattr(self.machine, 'audio_samples', None)
                sr = getattr(self.machine, 'audio_sample_rate', None)
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
                    axs.specgram(data, NFFT=nfft, Fs=sr, noverlap=noverlap, cmap='magma')
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

            # Notify success
            if hasattr(self, 'img_results_text'):
                self.img_results_text.append(f"Charts exported to PDF: {file_path}")
            if hasattr(self, 'aud_results_text'):
                self.aud_results_text.append(f"Charts exported to PDF: {file_path}")
        except Exception as e:
            if hasattr(self, 'img_results_text'):
                self.img_results_text.append(f"Error exporting charts: {e}")
            if hasattr(self, 'aud_results_text'):
                self.aud_results_text.append(f"Error exporting charts: {e}")
