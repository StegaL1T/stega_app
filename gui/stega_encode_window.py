# gui/stega_encode_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QFileDialog, QTextEdit,
                             QGroupBox, QGridLayout, QLineEdit, QComboBox, QSlider,
                             QSpinBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                             QScrollArea, QSlider as QTimeSlider, QToolTip)
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
        cover_panel.setFixedWidth(400)
        content_layout.addWidget(cover_panel)

        # Middle column - Payload (fixed width)
        payload_panel = self.create_payload_panel()
        payload_panel.setFixedWidth(400)
        content_layout.addWidget(payload_panel)

        # Right column - Controls (fixed width)
        controls_panel = self.create_controls_panel()
        controls_panel.setFixedWidth(400)
        content_layout.addWidget(controls_panel)

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
        hide_button = QPushButton("Hide Message")
        hide_button.setMinimumHeight(60)
        hide_button.setStyleSheet("""
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
        hide_button.clicked.connect(self.hide_message)

        # Center the button
        button_layout.addStretch()
        button_layout.addWidget(hide_button)
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
            "• Encryption Key: Any string\n"
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
        key_group = QGroupBox("Encryption Key")
        key_layout = QVBoxLayout(key_group)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Enter encryption key (optional)...")
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
                border-color: #3498db;
                background-color: #e3f2fd;
            }
            QLineEdit:hover {
                border-color: #3498db;
                background-color: #e3f2fd;
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

        layout.addLayout(header_layout)
        layout.addWidget(lsb_group)
        layout.addWidget(key_group)
        layout.addWidget(output_group)
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

    def on_media_loaded(self, file_path, media_type):
        """Handle media loaded from drag and drop or browse"""
        if not file_path:  # Media was removed
            return

        print(f"Media loaded: {file_path} ({media_type})")

        # Update machine with media
        if media_type == 'image':
            if self.machine.set_cover_image(file_path):
                info = self.machine.get_image_info()
                print(f"✅ Image loaded: {os.path.basename(file_path)}")
                print(f"Size: {info.get('dimensions', 'Unknown')}")
                print(f"Capacity: {info.get('max_capacity_bytes', 0)} bytes")
            else:
                print("❌ Error loading image")
        else:
            # For audio and video, we'll need to extend the machine
            print(f"✅ {media_type.upper()} loaded: {os.path.basename(file_path)}")

    def on_payload_file_loaded(self, file_path):
        """Handle payload file loaded from drag and drop or browse"""
        if not file_path:  # File was removed
            print("Payload file removed")
            return

        print(f"Payload file loaded: {file_path}")

        # Update machine with payload file
        if self.machine.set_payload_file(file_path):
            print(f"✅ Payload file loaded: {os.path.basename(file_path)}")
        else:
            print("❌ Error loading payload file")

    def browse_cover_image(self):
        """Browse for cover image (legacy method - now handled by media drop widget)"""
        # This method is now handled by the MediaDropWidget
        pass

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

        # Set default output path if none specified
        if not self.output_path.text().strip():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_path = f"stego_output_{timestamp}.png"
            self.output_path.setText(default_path)
            self.machine.set_output_path(default_path)

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
