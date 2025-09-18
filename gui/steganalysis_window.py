import datetime
from pathlib import Path

# gui/steganalysis_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QFileDialog, QTextEdit,
                             QGroupBox, QGridLayout, QLineEdit, QComboBox, QProgressBar, QApplication,
                             QTabWidget)
from PyQt6.QtCore import Qt
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
        """Create Image/Audio steganalysis tabs"""
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.setTabPosition(QTabWidget.TabPosition.North)

        image_tab = QWidget()
        audio_tab = QWidget()

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

        tabs.addTab(image_tab, "Image Steganalysis")
        tabs.addTab(audio_tab, "Audio Steganalysis")

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
        method_layout.addWidget(self.method_combo)

        self.img_analyze_btn = QPushButton("Analyze Image")
        self.img_analyze_btn.setStyleSheet("""
            QPushButton { background-color: #e74c3c; color: white; border: none; padding: 12px 24px; border-radius: 5px; font-size: 16px; font-weight: bold; }
            QPushButton:hover { background-color: #c0392b; }
        """)
        self.img_analyze_btn.clicked.connect(self.analyze_image)

        layout.addWidget(title)
        layout.addWidget(image_group)
        layout.addWidget(method_group)
        layout.addWidget(self.img_analyze_btn)
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
        audio_method_layout.addWidget(self.audio_method_combo)

        self.aud_analyze_btn = QPushButton("Analyze Audio")
        self.aud_analyze_btn.setStyleSheet("""
            QPushButton { background-color: #16a085; color: white; border: none; padding: 12px 24px; border-radius: 5px; font-size: 16px; font-weight: bold; }
            QPushButton:hover { background-color: #138d75; }
        """)
        self.aud_analyze_btn.clicked.connect(self.analyze_audio)

        layout.addWidget(title)
        layout.addWidget(audio_group)
        layout.addWidget(audio_method_group)
        layout.addWidget(self.aud_analyze_btn)
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

    def create_input_panel(self):
        """Create the input panel"""
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
        title = QLabel("Analysis Input")
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

        # Analysis method selection
        method_group = QGroupBox("Image Analysis Method")
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

        # Audio method selection
        audio_method_group = QGroupBox("Audio Analysis Method")
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

        layout.addWidget(title)
        layout.addWidget(image_group)
        layout.addWidget(method_group)
        layout.addWidget(analyze_button)
        layout.addWidget(audio_group)
        layout.addWidget(audio_method_group)
        layout.addWidget(analyze_audio_button)
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

        # Image charts
        image_charts_group = QGroupBox("Image Charts")
        image_charts_layout = QGridLayout(image_charts_group)

        self.img_canvas_lsb = FigureCanvas(Figure(figsize=(3, 2)))
        self.img_canvas_diff = FigureCanvas(Figure(figsize=(3, 2)))
        self.img_canvas_hist = FigureCanvas(Figure(figsize=(3, 2)))

        image_charts_layout.addWidget(self.img_canvas_lsb, 0, 0)
        image_charts_layout.addWidget(self.img_canvas_diff, 0, 1)
        image_charts_layout.addWidget(self.img_canvas_hist, 1, 0, 1, 2)

        # Audio charts
        audio_charts_group = QGroupBox("Audio Charts")
        audio_charts_layout = QGridLayout(audio_charts_group)

        self.aud_canvas_wave = FigureCanvas(Figure(figsize=(3, 2)))
        self.aud_canvas_spec = FigureCanvas(Figure(figsize=(3, 2)))
        self.aud_canvas_entropy = FigureCanvas(Figure(figsize=(3, 2)))

        audio_charts_layout.addWidget(self.aud_canvas_wave, 0, 0)
        audio_charts_layout.addWidget(self.aud_canvas_spec, 0, 1)
        audio_charts_layout.addWidget(self.aud_canvas_entropy, 1, 0, 1, 2)

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
        layout.addWidget(image_charts_group)
        layout.addWidget(audio_charts_group)
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
                if hasattr(self, 'aud_results_text'):
                    self.aud_results_text.append(f"Audio selected: {file_path}")
            else:
                if hasattr(self, 'aud_results_text'):
                    self.aud_results_text.append(f"Error loading audio: {file_path}")

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
