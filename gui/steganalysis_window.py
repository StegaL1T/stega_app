# gui/steganalysis_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QFileDialog, QTextEdit,
                             QGroupBox, QGridLayout, QLineEdit, QComboBox, QProgressBar)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QPen


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

    def create_content_area(self, layout):
        """Create the main content area with analysis tools"""
        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)

        # Left panel - Input
        input_panel = self.create_input_panel()
        content_layout.addWidget(input_panel)

        # Right panel - Results
        results_panel = self.create_results_panel()
        content_layout.addWidget(results_panel)

        layout.addLayout(content_layout)

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
            else:
                self.results_text.append(f"Error loading audio: {file_path}")

    def analyze_image(self):
        """Analyze the selected image"""
        if not self.image_path.text():
            self.results_text.append(
                "Error: Please select an image to analyze")
            return

        # Run analysis via machine
        method = self.method_combo.currentText()
        self.machine.set_analysis_method(method)
        ok = self.machine.analyze_image()

        self.results_text.append("\n=== IMAGE ANALYSIS ===")
        if not ok:
            self.results_text.append("Error during image analysis.")
            return

        results = self.machine.get_results()
        confidence = self.machine.get_confidence_level()
        stats = self.machine.get_statistics()

        self.results_text.append(f"Method: {results.get('method', method)}")
        self.results_text.append(f"Suspicious: {results.get('suspicious', False)}")
        for k, v in results.items():
            if k in ("method", "suspicious"):
                continue
            self.results_text.append(f"{k}: {v}")

        self.results_text.append(f"Confidence level: {confidence*100:.2f}%")

        self.stats_text.append("Image Statistics:")
        for k, v in stats.items():
            self.stats_text.append(f"- {k}: {v}")

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

    def export_report(self):
        """Export analysis report"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Analysis Report", "",
            "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            if self.machine.export_report(file_path):
                self.results_text.append(f"Report exported to: {file_path}")
            else:
                self.results_text.append("Error exporting report.")

    def go_back(self):
        """Go back to main window"""
        # Clean up machine resources
        self.machine.cleanup()

        from gui.main_window import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()
