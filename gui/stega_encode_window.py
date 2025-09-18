# gui/stega_encode_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QFileDialog, QTextEdit,
                             QGroupBox, QGridLayout, QLineEdit, QComboBox, QSlider,
                             QSpinBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                             QScrollArea, QSlider as QTimeSlider, QToolTip)
from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSignal, QRegularExpression
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QDragEnterEvent, QDropEvent, QImage, QIntValidator, QRegularExpressionValidator
import os
import numpy as np
from PIL import Image
import soundfile as sf
import cv2
from datetime import datetime
from machine.stega_encode_machine import HeaderMeta


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
                border-color: #3498db;
                background-color: #e3f2fd;
            }
        """)
        self.drop_zone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_zone.setText(
            "Drag & Drop Media Here\n\nSupported: Images, Audio, Video")

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
            self.drop_zone.setText("Drop Media Here!")

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
            "Drag & Drop Media Here\n\nSupported: Images, Audio, Video")

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
            self, "Select Media File", "",
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

        # Create preview
        self.create_preview()

        # Emit signal
        self.media_loaded.emit(file_path, media_type)

    def create_preview(self):
        """Create interactive preview based on media type"""
        if self.preview_widget:
            self.layout().removeWidget(self.preview_widget)
            self.preview_widget.deleteLater()

        if self.media_type == 'image':
            self.preview_widget = ImagePreviewWidget(self.media_path)
        elif self.media_type == 'audio':
            self.preview_widget = AudioPreviewWidget(self.media_path)
        elif self.media_type == 'video':
            self.preview_widget = VideoPreviewWidget(self.media_path)

        if self.preview_widget:
            # Insert preview after drop zone (index 1), before file info
            self.layout().insertWidget(1, self.preview_widget)

    def remove_media(self):
        """Remove the loaded media and reset to initial state"""
        # Clear media data
        self.media_path = None
        self.media_type = None

        # Remove preview widget
        if self.preview_widget:
            self.layout().removeWidget(self.preview_widget)
            self.preview_widget.deleteLater()
            self.preview_widget = None

        # Hide file info and remove button
        self.file_info.hide()
        self.remove_btn.hide()

        # Show drop zone and browse button
        self.drop_zone.show()
        self.browse_btn.show()

        # Emit signal to notify parent
        self.media_loaded.emit("", "")


class ImagePreviewWidget(QWidget):
    """Interactive image preview with pixel selection"""

    pixel_selected = pyqtSignal(int, int)  # x, y coordinates

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        self.pixmap = None
        self.scaled_pixmap = None
        self.scale_factor = 1.0
        self.selected_pixel = None

        self.setup_ui()
        self.load_image()

    def setup_ui(self):
        """Setup the image preview UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Graphics view for image display
        self.graphics_view = QGraphicsView()
        self.graphics_view.setMinimumHeight(250)
        self.graphics_view.setMaximumHeight(400)
        self.graphics_view.setStyleSheet("""
            QGraphicsView {
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                background-color: #f8f9fa;
            }
        """)

        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)

        # Info label
        self.info_label = QLabel("Click on image to select starting pixel")
        self.info_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-weight: bold;
                padding: 5px;
                text-align: center;
            }
        """)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.graphics_view)
        layout.addWidget(self.info_label)

    def load_image(self):
        """Load and display the image"""
        try:
            self.pixmap = QPixmap(self.image_path)
            if not self.pixmap.isNull():
                # Scale image to fit view
                view_size = self.graphics_view.size()
                self.pixmap_item = QGraphicsPixmapItem(self.pixmap)
                self.scene.addItem(self.pixmap_item)

                # Fit image in view
                self.graphics_view.fitInView(
                    self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

                # Connect mouse click
                self.graphics_view.mousePressEvent = self.on_image_click

                self.info_label.setText(
                    f"Image loaded: {self.pixmap.width()}x{self.pixmap.height()}")
            else:
                self.info_label.setText("Error loading image")
        except Exception as e:
            self.info_label.setText(f"Error: {str(e)}")

    def on_image_click(self, event):
        """Handle mouse click on image"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Get click position in scene coordinates
            scene_pos = self.graphics_view.mapToScene(event.pos())

            # Convert to image coordinates
            if hasattr(self, 'pixmap_item'):
                item_pos = self.pixmap_item.mapFromScene(scene_pos)
                x = int(item_pos.x())
                y = int(item_pos.y())

                # Check if click is within image bounds
                if 0 <= x < self.pixmap.width() and 0 <= y < self.pixmap.height():
                    self.selected_pixel = (x, y)
                    self.pixel_selected.emit(x, y)
                    self.info_label.setText(f"Selected pixel: ({x}, {y})")

                    # Draw selection indicator
                    self.draw_selection(x, y)

    def draw_selection(self, x, y):
        """Draw selection indicator on image"""
        # Create a copy of the original pixmap
        display_pixmap = self.pixmap.copy()
        painter = QPainter(display_pixmap)
        painter.setPen(QPen(QColor(255, 0, 0), 3))

        # Draw crosshair
        painter.drawLine(x - 10, y, x + 10, y)
        painter.drawLine(x, y - 10, x, y + 10)
        painter.end()

        # Update display
        self.pixmap_item.setPixmap(display_pixmap)


class AudioPreviewWidget(QWidget):
    """Interactive audio preview with waveform and time selection"""

    time_selected = pyqtSignal(float)  # time in seconds

    def __init__(self, audio_path):
        super().__init__()
        self.audio_path = audio_path
        self.audio_data = None
        self.sample_rate = None
        self.duration = 0
        self.selected_time = 0

        self.setup_ui()
        self.load_audio()

    def setup_ui(self):
        """Setup the audio preview UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Waveform display
        self.waveform_label = QLabel()
        self.waveform_label.setMinimumHeight(200)
        self.waveform_label.setMaximumHeight(300)
        self.waveform_label.setStyleSheet("""
            QLabel {
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                background-color: #f8f9fa;
            }
        """)
        self.waveform_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.waveform_label.setText("Loading audio...")

        # Time slider
        self.time_slider = QTimeSlider(Qt.Orientation.Horizontal)
        self.time_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bdc3c7;
                height: 8px;
                background: #ecf0f1;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #9b59b6;
                border: 1px solid #8e44ad;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)
        self.time_slider.valueChanged.connect(self.on_time_changed)

        # Info label
        self.info_label = QLabel(
            "Click on waveform or use slider to select start time")
        self.info_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-weight: bold;
                padding: 5px;
                text-align: center;
            }
        """)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.waveform_label)
        layout.addWidget(self.time_slider)
        layout.addWidget(self.info_label)

    def load_audio(self):
        """Load and display audio waveform"""
        try:
            # Load audio file
            self.audio_data, self.sample_rate = sf.read(self.audio_path)
            self.duration = len(self.audio_data) / self.sample_rate

            # Create waveform visualization
            self.create_waveform()

            # Setup slider
            self.time_slider.setMaximum(int(self.duration * 100))
            self.time_slider.setValue(0)

            self.info_label.setText(
                f"Audio loaded: {self.duration:.2f}s, {self.sample_rate}Hz")

        except Exception as e:
            self.waveform_label.setText(f"Error loading audio: {str(e)}")

    def create_waveform(self):
        """Create waveform visualization"""
        if self.audio_data is None:
            return

        # Create waveform pixmap - use full width of the widget
        width = 380  # Full width minus padding
        height = 200
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(248, 249, 250))

        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor(52, 152, 219), 2))

        # Draw waveform
        samples_per_pixel = len(self.audio_data) // width
        for x in range(width):
            start_idx = x * samples_per_pixel
            end_idx = min(start_idx + samples_per_pixel, len(self.audio_data))

            if start_idx < len(self.audio_data):
                chunk = self.audio_data[start_idx:end_idx]
                max_val = np.max(np.abs(chunk))
                y = int(height/2 - max_val * height/2)
                painter.drawLine(x, height//2, x, y)
                painter.drawLine(x, height//2, x, height//2 + (height//2 - y))

        painter.end()
        self.waveform_label.setPixmap(pixmap)

        # Connect click event
        self.waveform_label.mousePressEvent = self.on_waveform_click

    def on_waveform_click(self, event):
        """Handle click on waveform"""
        if event.button() == Qt.MouseButton.LeftButton:
            x = event.pos().x()
            width = self.waveform_label.width()
            time = (x / width) * self.duration
            self.selected_time = time
            self.time_selected.emit(time)
            self.time_slider.setValue(int(time * 100))
            self.info_label.setText(f"Selected time: {time:.2f}s")

    def on_time_changed(self, value):
        """Handle time slider change"""
        time = value / 100.0
        self.selected_time = time
        self.time_selected.emit(time)
        self.info_label.setText(f"Selected time: {time:.2f}s")


class VideoPreviewWidget(QWidget):
    """Interactive video preview with frame selection"""

    frame_selected = pyqtSignal(int)  # frame number

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.cap = None
        self.total_frames = 0
        self.fps = 0
        self.duration = 0
        self.selected_frame = 0
        self.current_frame = 0

        self.setup_ui()
        self.load_video()

    def setup_ui(self):
        """Setup the video preview UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Video display
        self.video_label = QLabel()
        self.video_label.setMinimumHeight(250)
        self.video_label.setMaximumHeight(400)
        self.video_label.setStyleSheet("""
            QLabel {
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                background-color: #f8f9fa;
            }
        """)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setText("Loading video...")

        # Frame slider
        self.frame_slider = QTimeSlider(Qt.Orientation.Horizontal)
        self.frame_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bdc3c7;
                height: 8px;
                background: #ecf0f1;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #e74c3c;
                border: 1px solid #c0392b;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)
        self.frame_slider.valueChanged.connect(self.on_frame_changed)

        # Control buttons
        button_layout = QHBoxLayout()

        self.prev_frame_btn = QPushButton("◀")
        self.prev_frame_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
        """)
        self.prev_frame_btn.clicked.connect(self.prev_frame)

        self.next_frame_btn = QPushButton("▶")
        self.next_frame_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
        """)
        self.next_frame_btn.clicked.connect(self.next_frame)

        button_layout.addWidget(self.prev_frame_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.next_frame_btn)

        # Info label
        self.info_label = QLabel("Use slider or buttons to select start frame")
        self.info_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-weight: bold;
                padding: 5px;
                text-align: center;
            }
        """)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.video_label)
        layout.addWidget(self.frame_slider)
        layout.addLayout(button_layout)
        layout.addWidget(self.info_label)

    def load_video(self):
        """Load video and display first frame"""
        try:
            self.cap = cv2.VideoCapture(self.video_path)
            if self.cap.isOpened():
                self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                self.fps = self.cap.get(cv2.CAP_PROP_FPS)
                self.duration = self.total_frames / self.fps

                # Setup slider
                self.frame_slider.setMaximum(self.total_frames - 1)
                self.frame_slider.setValue(0)

                # Display first frame
                self.show_frame(0)

                self.info_label.setText(
                    f"Video loaded: {self.total_frames} frames, {self.fps:.2f} FPS")
            else:
                self.video_label.setText("Error opening video")
        except Exception as e:
            self.video_label.setText(f"Error loading video: {str(e)}")

    def show_frame(self, frame_number):
        """Display specific frame"""
        if self.cap is None:
            return

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()

        if ret:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w

            # Create QImage
            q_image = QImage(frame_rgb.data, w, h,
                             bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)

            # Scale to fit label with proper aspect ratio
            label_size = self.video_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size.width() - 20, label_size.height() - 20,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.video_label.setPixmap(scaled_pixmap)

            self.current_frame = frame_number
            self.info_label.setText(
                f"Frame: {frame_number}/{self.total_frames-1}")

    def on_frame_changed(self, value):
        """Handle frame slider change"""
        self.selected_frame = value
        self.frame_selected.emit(value)
        self.show_frame(value)

    def prev_frame(self):
        """Go to previous frame"""
        if self.current_frame > 0:
            new_frame = self.current_frame - 1
            self.frame_slider.setValue(new_frame)

    def next_frame(self):
        """Go to next frame"""
        if self.current_frame < self.total_frames - 1:
            new_frame = self.current_frame + 1
            self.frame_slider.setValue(new_frame)

    def __del__(self):
        """Cleanup video capture"""
        if self.cap:
            self.cap.release()


class PayloadDropWidget(QFrame):
    """Custom widget for drag and drop payload file upload"""

    file_loaded = pyqtSignal(str)  # file_path

    def __init__(self):
        super().__init__()
        self.file_path = None
        self.setup_ui()

    def setup_ui(self):
        """Setup the drag and drop interface"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # Drop zone
        self.drop_zone = QLabel()
        self.drop_zone.setMinimumHeight(150)
        self.drop_zone.setStyleSheet("""
            QLabel {
                border: 3px dashed #bdc3c7;
                border-radius: 15px;
                background-color: #f8f9fa;
                color: #7f8c8d;
                font-size: 16px;
            }
            QLabel:hover {
                border-color: #3498db;
                background-color: #e3f2fd;
            }
        """)
        self.drop_zone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_zone.setText(
            "Drag & Drop File Here\n\nSupported: .txt, .pdf, .exe, .wav, .mp3, .mov, .mp4")

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
        self.remove_btn = QPushButton("Remove File")
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
        self.remove_btn.clicked.connect(self.remove_file)
        self.remove_btn.hide()

        # Browse button
        self.browse_btn = QPushButton("Browse File")
        self.browse_btn.setStyleSheet("""
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

    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        if files:
            self.load_file(files[0])

    def browse_files(self):
        """Browse for files"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Payload File", "",
            "All Supported (*.txt *.pdf *.exe *.wav *.mp3 *.mov *.mp4);;"
            "Text Files (*.txt);;PDF Files (*.pdf);;Executable Files (*.exe);;"
            "Audio Files (*.wav *.mp3);;Video Files (*.mov *.mp4);;All Files (*)"
        )
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path):
        """Load a file"""
        if not os.path.exists(file_path):
            return

        # Check file extension
        ext = os.path.splitext(file_path)[1].lower()
        supported_extensions = ['.txt', '.pdf',
                                '.exe', '.wav', '.mp3', '.mov', '.mp4']

        if ext not in supported_extensions:
            print(f"Unsupported file type: {ext}")
            return

        self.file_path = file_path

        # Hide drop zone and browse button, show remove button
        self.drop_zone.hide()
        self.browse_btn.hide()
        self.remove_btn.show()

        # Update UI with proper file path formatting
        self.file_info.setText(f"<b>File Path</b><br>{file_path}")
        self.file_info.show()

        # Emit signal
        self.file_loaded.emit(file_path)

    def remove_file(self):
        """Remove the loaded file and reset to initial state"""
        # Clear file data
        self.file_path = None

        # Hide file info and remove button
        self.file_info.hide()
        self.remove_btn.hide()

        # Show drop zone and browse button
        self.drop_zone.show()
        self.browse_btn.show()

        # Emit signal to notify parent
        self.file_loaded.emit("")


class StegaEncodeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steganography - Hide Messages")
        self.setMinimumSize(1200, 800)

        # Initialize the steganography machine
        from machine.stega_encode_machine import StegaEncodeMachine
        self.machine = StegaEncodeMachine()
        self.media_type = None
        self.start_xy = None  # (x,y) for image start
        self.start_sample = None  # for audio
        self.audio_info = None  # dict from machine.get_audio_info
        self.video_start = (0, 0, 0)  # (frame,x,y)
        self.available_bytes = 0

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

    def create_info_button(self, tooltip_text):
        """Create a blue info button with tooltip"""
        info_btn = QPushButton("ℹ")
        info_btn.setFixedSize(25, 25)
        info_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
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

        # Left column - Cover Item (fixed width)
        cover_panel = self.create_cover_panel()
        cover_scroll = QScrollArea()
        cover_scroll.setWidget(cover_panel)
        cover_scroll.setWidgetResizable(True)
        cover_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        cover_scroll.setFrameShape(QFrame.Shape.NoFrame)
        cover_scroll.setFixedWidth(400)
        content_layout.addWidget(cover_scroll)

        # Middle column - Payload (fixed width)
        payload_panel = self.create_payload_panel()
        payload_scroll = QScrollArea()
        payload_scroll.setWidget(payload_panel)
        payload_scroll.setWidgetResizable(True)
        payload_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        payload_scroll.setFrameShape(QFrame.Shape.NoFrame)
        payload_scroll.setFixedWidth(400)
        content_layout.addWidget(payload_scroll)

        # Right column - Controls (fixed width)
        controls_panel = self.create_controls_panel()
        controls_scroll = QScrollArea()
        controls_scroll.setWidget(controls_panel)
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        controls_scroll.setFrameShape(QFrame.Shape.NoFrame)
        controls_scroll.setFixedWidth(400)
        content_layout.addWidget(controls_scroll)

        layout.addLayout(content_layout)

        # Add Hide Message button below all columns
        self.create_hide_button(layout)

    def create_hide_button(self, layout):
        """Create the Hide Message button below all columns"""
        # Add some spacing above the button
        layout.addSpacing(30)

        # Create button container with centered alignment
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)

        # Hide Message button
        self.hide_button = QPushButton("Hide Message")
        self.hide_button.setMinimumHeight(60)
        self.hide_button.setStyleSheet("""
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
        self.hide_button.clicked.connect(self.hide_message)

        # Center the button
        button_layout.addStretch()
        button_layout.addWidget(self.hide_button)
        button_layout.addStretch()

        layout.addWidget(button_container)

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

        # Panel header with title and info button
        header_layout = QHBoxLayout()

        # Panel title
        title = QLabel("Cover Item")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 15px;")

        # Info button
        info_btn = self.create_info_button(
            "For Cover Item, we support:\n"
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

        # Panel header with title and info button
        header_layout = QHBoxLayout()

        # Panel title
        title = QLabel("Payload")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 15px;")

        # Info button
        info_btn = self.create_info_button(
            "For payload, we support:\n"
            "• Text Input\n"
            "• Text File (.txt)\n"
            "• .pdf\n"
            "• .exe\n"
            "• Audio (.wav, .mp3)\n"
            "• Video (.mov, .mp4)")

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(info_btn)

        # Text input (first row)
        self.message_text = QTextEdit()
        self.message_text.setPlaceholderText(
            "Enter your secret message here...")
        self.message_text.setMaximumHeight(80)
        self.message_text.setStyleSheet("""
            QTextEdit {
                border: 3px dashed #bdc3c7;
                border-radius: 15px;
                background-color: #f8f9fa;
                color: #7f8c8d;
                font-size: 14px;
                padding: 15px;
                font-family: 'Segoe UI', sans-serif;
            }
            QTextEdit:focus {
                border-color: #3498db;
                background-color: #e3f2fd;
            }
            QTextEdit:hover {
                border-color: #3498db;
                background-color: #e3f2fd;
            }
        """)

        # Or separator
        or_separator = QLabel("------- or -------")
        or_separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        or_separator.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 14px;
                font-weight: bold;
                margin: 5px 0;
            }
        """)

        # File drop widget (similar to cover item)
        self.payload_drop_widget = PayloadDropWidget()
        self.payload_drop_widget.file_loaded.connect(
            self.on_payload_file_loaded)

        layout.addLayout(header_layout)
        layout.addWidget(self.message_text)
        layout.addWidget(or_separator)
        layout.addWidget(self.payload_drop_widget)
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

        # Panel header with title and info button
        header_layout = QHBoxLayout()

        # Panel title
        title = QLabel("Controls")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 15px;")

        # Info button
        info_btn = self.create_info_button(
            "For Controls:\n"
            "• LSB: Higher -> more capacity, lower quality\n"
            "• Key: Numeric, required for reproducibility\n"
            "• Output Path: Default to datetime")

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
        key_group = QGroupBox("Key (numeric, required)")
        key_layout = QVBoxLayout(key_group)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Enter numeric key, e.g. 123456")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        # Use regex validator to allow long numeric keys without 32-bit limits
        self.key_input.setValidator(QRegularExpressionValidator(QRegularExpression(r"^\d{1,32}$")))
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
                border-color: #3498db;
                background-color: #e3f2fd;
            }
            QLineEdit:hover {
                border-color: #3498db;
                background-color: #e3f2fd;
            }
        """)

        key_layout.addWidget(self.key_input)

        # Capacity group
        capacity_group = QGroupBox("Capacity")
        cap_layout = QVBoxLayout(capacity_group)
        self.cap_dims = QLabel("Cover: -")
        self.cap_lsb = QLabel("LSB bits: 1")
        self.cap_header = QLabel("Header bytes: -")
        self.cap_max = QLabel("Capacity (bytes): -")
        self.cap_avail = QLabel("Available bytes: -")
        for lbl in [self.cap_dims, self.cap_lsb, self.cap_header, self.cap_max, self.cap_avail]:
            lbl.setStyleSheet("color:#2c3e50;")
            cap_layout.addWidget(lbl)
        capacity_group.setLayout(cap_layout)

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

        layout.addLayout(header_layout)
        layout.addWidget(lsb_group)
        layout.addWidget(key_group)
        # Proof panel (How embedded)
        proof_group = QGroupBox("How embedded")
        proof_layout = QVBoxLayout(proof_group)
        self.proof_lsb = QLabel("LSB bits: -")
        self.proof_start = QLabel("Start bit: -")
        self.proof_perm = QLabel("Perm [0:8]: -")
        self.proof_header = QLabel("Header: -")
        for lbl in [self.proof_lsb, self.proof_start, self.proof_perm, self.proof_header]:
            lbl.setStyleSheet("color:#2c3e50;")
            lbl.setWordWrap(True)
            proof_layout.addWidget(lbl)

        # Visualization toggles
        vis_group = QGroupBox("Visualization")
        vis_layout = QVBoxLayout(vis_group)
        self.lsb_toggle_btn = QPushButton("Show LSB plane")
        self.lsb_toggle_btn.setCheckable(True)
        self.lsb_toggle_btn.setStyleSheet("""
            QPushButton { background-color: #95a5a6; color: white; border: none; padding: 8px 12px; border-radius: 5px; }
            QPushButton:checked { background-color: #2ecc71; }
        """)
        self.lsb_toggle_btn.toggled.connect(self.on_lsb_toggle)
        vis_layout.addWidget(self.lsb_toggle_btn)

        layout.addWidget(output_group)
        layout.addWidget(capacity_group)
        # Video start controls
        video_group = QGroupBox("Video Start")
        video_vlayout = QVBoxLayout(video_group)
        self.video_frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.video_frame_slider.setMinimum(0)
        self.video_frame_slider.setMaximum(0)
        self.video_frame_slider.valueChanged.connect(self.on_video_frame_changed)
        self.video_pos_label = QLabel("Frame: 0, X: 0, Y: 0")
        video_vlayout.addWidget(self.video_frame_slider)
        video_vlayout.addWidget(self.video_pos_label)
        layout.addWidget(video_group)
        layout.addWidget(proof_group)
        layout.addWidget(vis_group)

        # Audio playback controls (enabled only for audio)
        audio_play_group = QGroupBox("Audio Playback")
        audio_play_layout = QHBoxLayout(audio_play_group)
        self.play_cover_btn = QPushButton("Play Cover")
        self.play_stego_btn = QPushButton("Play Stego")
        for btn in (self.play_cover_btn, self.play_stego_btn):
            btn.setEnabled(False)
            btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; border: none; padding: 8px 12px; border-radius: 5px; }")
        self.play_cover_btn.clicked.connect(self.play_cover_audio)
        self.play_stego_btn.clicked.connect(self.play_stego_audio)
        audio_play_layout.addWidget(self.play_cover_btn)
        audio_play_layout.addWidget(self.play_stego_btn)
        layout.addWidget(audio_play_group)
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
        # Recompute capacity when LSB changes
        try:
            self.update_capacity_panel()
        except Exception:
            pass

    def on_media_loaded(self, file_path, media_type):
        """Handle media loaded from drag and drop or browse"""
        if not file_path:  # Media was removed
            return

        print(f"Media loaded: {file_path} ({media_type})")
        self.media_type = media_type
        self.start_xy = None

        # Update machine with media
        if media_type == 'image':
            if self.machine.set_cover_image(file_path):
                info = self.machine.get_image_info()
                print(f"✅ Image loaded: {os.path.basename(file_path)}")
                print(f"Size: {info.get('dimensions', 'Unknown')}")
                print(f"Capacity: {info.get('max_capacity_bytes', 0)} bytes")
                # connect to pixel selection if available
                if self.media_drop_widget.preview_widget and hasattr(self.media_drop_widget.preview_widget, 'pixel_selected'):
                    try:
                        self.media_drop_widget.preview_widget.pixel_selected.connect(self.on_start_pixel_selected)
                    except Exception:
                        pass
                self.update_capacity_panel()
                # Reset visualization toggle
                if hasattr(self, 'lsb_toggle_btn'):
                    self.lsb_toggle_btn.setChecked(False)
            else:
                print("❌ Error loading image")
        elif media_type == 'audio':
            # WAV PCM
            if self.machine.set_cover_audio(file_path):
                try:
                    self.audio_info = self.machine.get_audio_info(file_path)
                    print(f"✅ WAV loaded: {os.path.basename(file_path)}  {self.audio_info}")
                except Exception as e:
                    print(f"Error reading audio info: {e}")
                    self.audio_info = None
                # connect time selection
                if self.media_drop_widget.preview_widget and hasattr(self.media_drop_widget.preview_widget, 'time_selected'):
                    try:
                        self.media_drop_widget.preview_widget.time_selected.connect(self.on_audio_time_selected)
                    except Exception:
                        pass
                # Enable cover play
                if hasattr(self, 'play_cover_btn'):
                    self.play_cover_btn.setEnabled(True)
                self.update_capacity_panel()
            else:
                print("❌ Error loading audio")
        elif media_type == 'video':
            # Probe metadata and enable lossless embed path
            try:
                cap = cv2.VideoCapture(file_path)
                if not cap.isOpened():
                    raise RuntimeError("Cannot open video")
                frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS) or 24
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()
                self.cap_dims.setText(f"Video: {frames}f, {w}x{h}, {int(fps)}fps")
                # init frame slider and start tuple
                if hasattr(self, 'video_frame_slider'):
                    self.video_frame_slider.setMaximum(max(0, frames - 1))
                    self.video_frame_slider.setValue(0)
                self.video_start = (0, 0, 0)
                if hasattr(self, 'video_pos_label'):
                    self.video_pos_label.setText("Frame: 0, X: 0, Y: 0")
                # connect preview frame selection if available
                if self.media_drop_widget.preview_widget and hasattr(self.media_drop_widget.preview_widget, 'frame_selected'):
                    try:
                        self.media_drop_widget.preview_widget.frame_selected.connect(self.on_video_frame_changed)
                    except Exception:
                        pass
                # Allow embedding now that we will write lossless AVI
                if hasattr(self, 'hide_button'):
                    self.hide_button.setEnabled(True)
            except Exception as e:
                print(f"Video probe failed: {e}")
                if hasattr(self, 'hide_button'):
                    self.hide_button.setEnabled(False)
            self.update_capacity_panel()

    def on_payload_file_loaded(self, file_path):
        """Handle payload file loaded from drag and drop or browse"""
        if not file_path:  # File was removed
            print("Payload file removed")
            return

        print(f"Payload file loaded: {file_path}")

        # Update machine with payload file
        if self.machine.set_payload_file(file_path):
            print(f"✅ Payload file loaded: {os.path.basename(file_path)}")
            self.update_capacity_panel()
        else:
            print("❌ Error loading payload file")

    def browse_cover_image(self):
        """Browse for cover image (legacy method - now handled by media drop widget)"""
        # This method is now handled by the MediaDropWidget
        pass

    def choose_output_path(self):
        """Choose output path"""
        if self.media_type == 'audio':
            title = "Save Steganographic Audio"
            filt = "WAV Files (*.wav);;All Files (*)"
            default_name = "stego_output.wav"
        elif self.media_type == 'video':
            title = "Save Steganographic Video"
            filt = "AVI Files (*.avi);;All Files (*)"
            default_name = "stego_output.avi"
        else:
            title = "Save Steganographic Image"
            filt = "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
            default_name = "stego_output.png"
        file_path, _ = QFileDialog.getSaveFileName(self, title, default_name, filt)
        if file_path:
            self.output_path.setText(file_path)
            self.machine.set_output_path(file_path)

    def hide_message(self):
        """Hide message in the cover image"""
        from PyQt6.QtWidgets import QMessageBox
        # Update machine with current GUI values
        self.machine.set_lsb_bits(self.lsb_slider.value())
        self.machine.set_encryption_key(self.key_input.text())

        # Validate key
        if not self.key_input.text().strip().isdigit():
            QMessageBox.warning(self, "Key required", "Please enter a numeric key.")
            return

        # Set payload from text if provided
        if self.message_text.toPlainText().strip():
            self.machine.set_payload_text(self.message_text.toPlainText())

        # Set default output path if none specified
        if not self.output_path.text().strip():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_path = f"stego_output_{timestamp}.png"
            self.output_path.setText(default_path)
            self.machine.set_output_path(default_path)

        # Route by media type
        if self.media_type == 'image':
            if self.start_xy is None:
                QMessageBox.information(self, "Start required", "Click the image to select a start pixel.")
                return
            ok = self.machine.hide_message(start_xy=self.start_xy)
        elif self.media_type == 'audio':
            # Ensure payload set from text if any
            # Default output path
            if not self.output_path.text().strip():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_path = f"stego_output_{timestamp}.wav"
                self.output_path.setText(default_path)
                self.machine.set_output_path(default_path)
            # derive start_sample
            start_sample = self.start_sample if self.start_sample is not None else 0
            try:
                filename = os.path.basename(self.machine.payload_file_path) if self.machine.payload_file_path else "payload.bin"
                audio_bytes = self.machine.encode_audio(self.media_drop_widget.media_path, self.machine.payload_data or b"", filename, self.lsb_slider.value(), self.key_input.text(), start_sample=start_sample)
                # save
                with open(self.output_path.text(), 'wb') as f:
                    f.write(audio_bytes)
                ok = True
            except Exception as e:
                print(f"Audio encode failed: {e}")
                ok = False
        elif self.media_type == 'video':
            # Default output for video if none
            if not self.output_path.text().strip():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_path = f"stego_output_{timestamp}.avi"
                self.output_path.setText(default_path)
                self.machine.set_output_path(default_path)
            try:
                filename = os.path.basename(self.machine.payload_file_path) if self.machine.payload_file_path else "payload.bin"
                f, x, y = self.video_start
                outp = self.machine.encode_video(self.media_drop_widget.media_path, self.machine.payload_data or b"", filename, self.lsb_slider.value(), self.key_input.text(), start_fxy=(f, x, y), out_path=self.output_path.text())
                ok = True if outp else False
            except Exception as e:
                print(f"Video encode failed: {e}")
                ok = False
        else:
            QMessageBox.warning(self, "Unsupported", "Embedding into compressed video is not supported. Please use an image or WAV.")
            return

        # Post-result handling
        if ok:
            print("✅ Steganography completed successfully!")
            QMessageBox.information(self, "Success", f"Saved: {self.machine.output_path}")
            # Update proof panel from machine.last_embed_info
            info = getattr(self.machine, 'last_embed_info', None)
            if info:
                self.proof_lsb.setText(f"LSB bits: {info.get('lsb_bits')}")
                self.proof_start.setText(f"Start bit: {info.get('start_bit')}")
                perm = info.get('perm', [])
                self.proof_perm.setText(f"Perm [0:8]: {perm[:8]}")
                hdr = info.get('header', {})
                self.proof_header.setText(
                    f"Header: ver={hdr.get('version')} lsb={hdr.get('lsb_bits')} start={hdr.get('start_bit_offset')} len={hdr.get('payload_len')} fname='{hdr.get('filename')}' crc=0x{hdr.get('crc32'):08X}"
                )
            # Enable stego playback button for audio
            if self.media_type == 'audio' and hasattr(self, 'play_stego_btn'):
                self.play_stego_btn.setEnabled(True)
        else:
            print("❌ Steganography failed!")
            QMessageBox.critical(self, "Failed", "Steganography failed. See console for details.")

    def on_start_pixel_selected(self, x, y):
        self.start_xy = (x, y)
        try:
            self.update_capacity_panel()
        except Exception:
            pass

    def on_lsb_toggle(self, checked: bool):
        # Only for images/audio with a preview
        if not hasattr(self, 'media_drop_widget') or not self.media_drop_widget.media_path:
            return
        if self.media_type == 'image':
            if not self.media_drop_widget.preview_widget or not hasattr(self.media_drop_widget.preview_widget, 'pixmap_item'):
                return
            if checked:
                # Show image LSB plane
                try:
                    from machine.stega_encode_machine import StegaEncodeMachine
                    lsb_img = StegaEncodeMachine.lsb_plane_image_from_path(self.media_drop_widget.media_path, 0)
                    qimg = QImage(lsb_img.tobytes(), lsb_img.size[0], lsb_img.size[1], lsb_img.width * 3, QImage.Format.Format_RGB888)
                    pm = QPixmap.fromImage(qimg)
                    self.media_drop_widget.preview_widget.pixmap_item.setPixmap(pm)
                except Exception as e:
                    print(f"Failed to show LSB plane: {e}")
            else:
                # Restore original image preview
                try:
                    pm = QPixmap(self.media_drop_widget.media_path)
                    self.media_drop_widget.preview_widget.pixmap_item.setPixmap(pm)
                except Exception as e:
                    print(f"Failed to restore original preview: {e}")
        elif self.media_type == 'audio' and checked:
            # Compute a simple LSB density summary
            try:
                import wave, numpy as np
                with wave.open(self.media_drop_widget.media_path, 'rb') as wf:
                    frames = wf.readframes(min(wf.getnframes(), 200000))
                arr = np.frombuffer(frames, dtype=np.uint8)
                lsb = self.lsb_slider.value()
                mask = (1 << 1) - 1  # LSB only summary
                ones = int(((arr & mask) != 0).sum())
                pct = ones / arr.size * 100 if arr.size else 0
                self.proof_header.setText(f"Audio LSB density (first chunk): {pct:.2f}% ones")
            except Exception as e:
                print(f"Failed to compute audio LSB density: {e}")
            # Restore original image preview
            try:
                pm = QPixmap(self.media_drop_widget.media_path)
                self.media_drop_widget.preview_widget.pixmap_item.setPixmap(pm)
            except Exception as e:
                print(f"Failed to restore original preview: {e}")

    def current_payload_len(self) -> int:
        if self.machine.payload_data:
            return len(self.machine.payload_data)
        txt = self.message_text.toPlainText().encode('utf-8') if self.message_text.toPlainText() else b""
        return len(txt)

    def update_capacity_panel(self):
        if self.media_type == 'video' and hasattr(self.media_drop_widget, 'media_path') and self.media_drop_widget.media_path:
            try:
                lsb = self.lsb_slider.value()
                filename = os.path.basename(self.machine.payload_file_path) if self.machine.payload_file_path else "payload.bin"
                header_meta = HeaderMeta(lsb_bits=lsb, start_bit_offset=0, payload_len=self.current_payload_len(), filename=filename, crc32=0)
                try:
                    header_bytes = self.machine.pack_header(header_meta)
                except Exception:
                    header_bytes = b""
                header_bits = len(header_bytes) * 8
                f, x, y = self.video_start
                total_bits = self.machine.estimate_capacity_bits(self.media_drop_widget.media_path, 'video', lsb, (f, x, y))
                max_bytes = total_bits // 8
                self.available_bytes = max(0, (total_bits - header_bits) // 8)
                self.cap_lsb.setText(f"LSB bits: {lsb}")
                self.cap_header.setText(f"Header bytes: {len(header_bytes)}")
                self.cap_max.setText(f"Capacity (bytes): {max_bytes}")
                self.cap_avail.setText(f"Available bytes: {self.available_bytes}")
                too_large = self.current_payload_len() > self.available_bytes if header_bytes else False
                if hasattr(self, 'hide_button'):
                    self.hide_button.setEnabled(not too_large)
            except Exception as e:
                print(f"Video capacity update failed: {e}")
            return
        # Default reset
        self.cap_dims.setText("Cover: -")
        self.cap_lsb.setText(f"LSB bits: {self.lsb_slider.value()}")
        self.cap_header.setText("Header bytes: -")
        self.cap_max.setText("Capacity (bytes): -")
        self.cap_avail.setText("Available bytes: -")
        if hasattr(self, 'hide_button'):
            self.hide_button.setEnabled(True)

        if self.media_type == 'video':
            self.cap_dims.setText("Video: N/A (compressed stream)")
            self.cap_max.setText("Capacity: N/A")
            if hasattr(self, 'hide_button'):
                self.hide_button.setEnabled(False)
            return

        if self.media_type == 'audio' and self.machine.cover_audio_path:
            # Audio capacity
            try:
                info = self.audio_info or {}
                ch = info.get('channels', '-')
                sr = info.get('sample_rate', '-')
                bits = info.get('sampwidth_bits', '-')
                dur = info.get('duration', 0.0)
                self.cap_dims.setText(f"WAV: {ch}ch, {sr}Hz, {bits}-bit, {dur:.2f}s")
                lsb = self.lsb_slider.value()
                filename = os.path.basename(self.machine.payload_file_path) if self.machine.payload_file_path else "payload.bin"
                header_meta = HeaderMeta(lsb_bits=lsb, start_bit_offset=0, payload_len=self.current_payload_len(), filename=filename, crc32=0)
                try:
                    header_bytes = self.machine.pack_header(header_meta)
                except Exception:
                    header_bytes = b""
                header_bits = len(header_bytes) * 8
                start_sample = self.start_sample if self.start_sample is not None else 0
                total_bits = self.machine.estimate_capacity_bits(self.media_drop_widget.media_path, 'audio', lsb, start_sample)
                max_bytes = total_bits // 8
                self.available_bytes = max(0, (total_bits - header_bits) // 8)
                self.cap_lsb.setText(f"LSB bits: {lsb}")
                self.cap_header.setText(f"Header bytes: {len(header_bytes)}")
                self.cap_max.setText(f"Capacity (bytes): {max_bytes}")
                self.cap_avail.setText(f"Available bytes: {self.available_bytes}")
                too_large = self.current_payload_len() > self.available_bytes if header_bytes else False
                if hasattr(self, 'hide_button'):
                    self.hide_button.setEnabled(not too_large)
            except Exception as e:
                print(f"Audio capacity update failed: {e}")
            return

        if self.media_type != 'image' or not self.machine.cover_image:
            return

        img = self.machine.cover_image
        h, w = img.size[1], img.size[0]
        channels = 3
        lsb = self.lsb_slider.value()
        total_bits = w * h * channels * lsb

        # Header size (depends on filename length)
        filename = os.path.basename(self.machine.payload_file_path) if self.machine.payload_file_path else "payload.txt"
        header_meta = HeaderMeta(lsb_bits=lsb, start_bit_offset=0, payload_len=self.current_payload_len(), filename=filename, crc32=0)
        try:
            header_bytes = self.machine.pack_header(header_meta)
        except Exception:
            header_bytes = b""
        header_bits = len(header_bytes) * 8

        if self.start_xy is not None:
            x, y = self.start_xy
            pixel_index = y * w + x
            start_bit = pixel_index * channels * lsb
        else:
            start_bit = 0

        usable_bits = max(0, total_bits - start_bit)
        max_bytes = usable_bits // 8
        self.available_bytes = max(0, (usable_bits - header_bits) // 8)

        self.cap_dims.setText(f"Cover: {w}x{h}x{channels}")
        self.cap_lsb.setText(f"LSB bits: {lsb}")
        self.cap_header.setText(f"Header bytes: {len(header_bytes)}")
        self.cap_max.setText(f"Capacity (bytes): {max_bytes}")
        self.cap_avail.setText(f"Available bytes: {self.available_bytes}")

        too_large = self.current_payload_len() > self.available_bytes if header_bytes else False
        if hasattr(self, 'hide_button'):
            self.hide_button.setEnabled(not too_large)

    def on_audio_time_selected(self, t: float):
        # Convert time to start_sample
        try:
            if self.audio_info and self.audio_info.get('sample_rate'):
                sr = int(self.audio_info['sample_rate'])
                self.start_sample = int(max(0.0, t) * sr)
            else:
                self.start_sample = 0
            self.update_capacity_panel()
        except Exception:
            pass

    def play_cover_audio(self):
        # Open cover WAV in default player
        try:
            from PyQt6.QtGui import QDesktopServices
            if self.media_drop_widget and self.media_drop_widget.media_path:
                QDesktopServices.openUrl(QUrl.fromLocalFile(self.media_drop_widget.media_path))
        except Exception as e:
            print(f"Failed to open cover audio: {e}")

    def play_stego_audio(self):
        try:
            from PyQt6.QtGui import QDesktopServices
            out = self.output_path.text().strip()
            if out and os.path.exists(out):
                QDesktopServices.openUrl(QUrl.fromLocalFile(out))
        except Exception as e:
            print(f"Failed to open stego audio: {e}")

    def on_video_frame_changed(self, value: int):
        # Update start frame; TODO: add X,Y from clicks on video preview
        try:
            f, x, y = self.video_start
        except Exception:
            f, x, y = 0, 0, 0
        self.video_start = (int(value), x, y)
        if hasattr(self, 'video_pos_label'):
            self.video_pos_label.setText(f"Frame: {int(value)}, X: {x}, Y: {y}")
        try:
            self.update_capacity_panel()
        except Exception:
            pass

    def go_back(self):
        """Go back to main window"""
        # Clean up machine resources
        self.machine.cleanup()

        from gui.main_window import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()
