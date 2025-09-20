# gui/stega_encode_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QFileDialog, QTextEdit,
                             QGroupBox, QGridLayout, QLineEdit, QComboBox, QSlider,
                             QSpinBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                             QScrollArea, QSlider as QTimeSlider, QToolTip, QProgressBar,
                             QCheckBox)
from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSignal, QRegularExpression
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QDragEnterEvent, QDropEvent, QImage, QIntValidator, QRegularExpressionValidator, QCursor
import os
import numpy as np
from PIL import Image
import soundfile as sf
import cv2
from datetime import datetime
from machine.stega_spec import HeaderMeta, FLAG_PAYLOAD_ENCRYPTED, pack_header


def _human_size(num: int) -> str:
    """Return human readable file size."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"


class NotificationBanner(QFrame):
    """Persistent, dismissible banner for inline notifications."""
    closed = pyqtSignal()

    def __init__(self, message: str, severity: str = 'info', parent: QWidget | None = None):
        super().__init__(parent)
        self._message_label = QLabel()
        self._close_btn = QPushButton("Ã—")
        self._close_btn.setFixedWidth(24)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.clicked.connect(self._on_close)

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setObjectName("notificationBanner")

        # Colors by severity
        if severity == 'error':
            bg = "#fdecea"; fg = "#c0392b"; border = "#e6b0aa"
        elif severity == 'warning':
            bg = "#fff4e5"; fg = "#8e5b00"; border = "#f5c16c"
        else:
            bg = "#eef5ff"; fg = "#2c3e50"; border = "#a9c8ff"
        self.setStyleSheet(
            f"#notificationBanner {{ background-color:{bg}; border:1px solid {border}; border-radius:8px; }}"
            f"QLabel {{ color:{fg}; font-weight:bold; }}"
            "QPushButton { background: transparent; color: #7f8c8d; border: none; font-size: 16px; }"
            "QPushButton:hover { color: #2c3e50; }"
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 8, 8, 8)
        lay.setSpacing(8)
        self._message_label.setWordWrap(True)
        self._message_label.setText(message)
        lay.addWidget(self._message_label)
        lay.addStretch()
        lay.addWidget(self._close_btn)

    def setText(self, message: str):
        self._message_label.setText(message)

    def _on_close(self):
        try:
            self.closed.emit()
        except Exception:
            pass
        self.hide()
        self.deleteLater()


class MediaDropWidget(QFrame):
    """Custom widget for drag and drop media upload with interactive previews"""

    media_loaded = pyqtSignal(str, str)  # file_path, media_type
    notify = pyqtSignal(str, str)  # message, severity

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
        self.drop_zone.setToolTip('Step 1: Add a cover file. Drag & drop or click browse to pick an image, WAV, or video container.')
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
            # Notify parent via signal for persistent banner
            try:
                self.notify.emit(f"Unsupported media type: {ext}", 'warning')
            except Exception:
                pass
            # Brief inline hint
            self.drop_zone.setText("Unsupported media type")
            QTimer.singleShot(1500, lambda: self.drop_zone.setText("Drag & Drop Media Here\n\nSupported: Images, Audio, Video"))
            return

        self.media_path = file_path
        self.media_type = media_type

        # Hide drop zone and browse button, show remove button
        self.drop_zone.hide()
        self.browse_btn.hide()
        self.remove_btn.show()

        # Update UI with proper file path formatting
        self.file_info.setText(f"<b>File Path</b><br>{file_path}")
        # Tooltip with size info
        try:
            size = os.path.getsize(file_path)
            self.file_info.setToolTip(f"{os.path.basename(file_path)}\nSize: {_human_size(size)} ({size} bytes)")
        except Exception:
            self.file_info.setToolTip(os.path.basename(file_path))
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
    xy_selected = pyqtSignal(int, int, int)  # frame, x, y

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.cap = None
        self.total_frames = 0
        self.fps = 0
        self.duration = 0
        self.selected_frame = 0
        self.current_frame = 0
        self._last_scaled_size = None  # (w,h) of pixmap displayed
        self._last_offset = (0, 0)     # (offset_x, offset_y) inside label
        self._frame_size = None        # (w,h) original frame size
        self._last_click = None        # (frame, x, y) in frame coords

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
        # Enable click selection on the video label
        self.video_label.mousePressEvent = self.on_video_click

        # Status pill and clear control
        status_layout = QHBoxLayout()
        self.status_pill = QLabel("Click video to set start")
        self.status_pill.setStyleSheet(
            """
            QLabel {
                background-color: #eef5ff;
                color: #2c3e50;
                border-radius: 12px;
                padding: 4px 10px;
                font-weight: bold;
            }
            """
        )
        self.clear_marker_btn = QPushButton("Clear Marker")
        self.clear_marker_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #bdc3c7;
                color: #2c3e50;
                border: none;
                padding: 6px 10px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #aeb6bf; }
            """
        )
        self.clear_marker_btn.clicked.connect(self.on_clear_marker)
        status_layout.addWidget(self.status_pill)
        status_layout.addStretch()
        status_layout.addWidget(self.clear_marker_btn)

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

        self.prev_frame_btn = QPushButton("â—€")
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

        self.next_frame_btn = QPushButton("â–¶")
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
        layout.addLayout(status_layout)
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
            # If there's a click marker for this frame, draw it
            if self._last_click and self._last_click[0] == frame_number:
                try:
                    _, cx, cy = self._last_click
                    # Map frame coords -> scaled pixmap coords
                    sx = int(cx * scaled_pixmap.width() / max(1, w))
                    sy = int(cy * scaled_pixmap.height() / max(1, h))
                    pm_to_draw = QPixmap(scaled_pixmap)
                    painter = QPainter(pm_to_draw)
                    painter.setPen(QPen(QColor(231, 76, 60), 2))  # red
                    painter.drawLine(max(0, sx-10), sy, min(pm_to_draw.width()-1, sx+10), sy)
                    painter.drawLine(sx, max(0, sy-10), sx, min(pm_to_draw.height()-1, sy+10))
                    painter.end()
                    self.video_label.setPixmap(pm_to_draw)
                except Exception as _e:
                    # Fallback to plain pixmap
                    self.video_label.setPixmap(scaled_pixmap)
            else:
                self.video_label.setPixmap(scaled_pixmap)
            # Store mapping state
            self._last_scaled_size = (scaled_pixmap.width(), scaled_pixmap.height())
            self._frame_size = (w, h)
            off_x = max(0, (label_size.width() - scaled_pixmap.width()) // 2)
            off_y = max(0, (label_size.height() - scaled_pixmap.height()) // 2)
            # account for the -20 margin used in scaling
            # ensure offsets are not negative
            self._last_offset = (max(0, off_x), max(0, off_y))

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

    def on_video_click(self, event):
        """Map click on label back to frame pixel coordinates and emit xy_selected"""
        try:
            if event.button() != Qt.MouseButton.LeftButton:
                return
            if not self._frame_size or not self._last_scaled_size:
                return
            lx = event.position().x() if hasattr(event, 'position') else event.pos().x()
            ly = event.position().y() if hasattr(event, 'position') else event.pos().y()
            off_x, off_y = self._last_offset
            disp_w, disp_h = self._last_scaled_size
            # Check inside displayed pixmap area
            if lx < off_x or ly < off_y or lx > off_x + disp_w or ly > off_y + disp_h:
                return
            fx, fy = self._frame_size
            x = int((lx - off_x) * fx / max(1, disp_w))
            y = int((ly - off_y) * fy / max(1, disp_h))
            # Clamp to bounds
            x = max(0, min(fx - 1, x))
            y = max(0, min(fy - 1, y))
            # Remember selected frame
            self.selected_frame = self.current_frame
            self._last_click = (self.current_frame, x, y)
            # Redraw current frame with marker
            self.show_frame(self.current_frame)
            try:
                self.status_pill.setText(f"Start: frame {self.current_frame}, x:{x}, y:{y}")
            except Exception:
                pass
            print(f"[VideoPreview] label=({lx:.1f},{ly:.1f}) -> frame=({x},{y}), frame#={self.current_frame}")
            self.xy_selected.emit(self.current_frame, x, y)
        except Exception as e:
            # Fallback: ignore click errors silently
            print(f"Video click mapping failed: {e}")

    def __del__(self):
        """Cleanup video capture"""
        if self.cap:
            self.cap.release()

    def on_clear_marker(self):
        """Clear the click marker overlay and reset status pill"""
        self._last_click = None
        try:
            self.status_pill.setText("Click video to set start")
        except Exception:
            pass
        # Redraw current frame without marker
        try:
            self.show_frame(self.current_frame)
        except Exception:
            pass


class PayloadDropWidget(QFrame):
    """Custom widget for drag and drop payload file upload"""

    file_loaded = pyqtSignal(str)  # file_path
    notify = pyqtSignal(str, str)  # message, severity

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
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
            # Highlight drop zone
            self.drop_zone.setStyleSheet(
                """
                QLabel {
                    border: 3px dashed #27ae60;
                    border-radius: 15px;
                    background-color: #d5f4e6;
                    color: #27ae60;
                    font-size: 16px;
                    font-weight: bold;
                }
                """
            )
            self.drop_zone.setText("Drop File Here!")

    def dragLeaveEvent(self, event):
        """Reset styles on drag leave"""
        self.drop_zone.setStyleSheet(
            """
            QLabel {
                border: 3px dashed #bdc3c7;
                border-radius: 15px;
                background-color: #f8f9fa;
                color: #7f8c8d;
                font-size: 16px;
            }
            """
        )
        self.drop_zone.setText("Drag & Drop File Here\n\nSupported: .txt, .pdf, .exe, .wav, .mp3, .mov, .mp4")

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
            # Persistent banner notification via parent
            try:
                self.notify.emit(f"Unsupported payload type: {ext}", 'warning')
            except Exception:
                pass
            # Brief inline hint
            self.drop_zone.setText("Unsupported file type")
            QTimer.singleShot(1500, lambda: self.drop_zone.setText("Drag & Drop File Here\n\nSupported: .txt, .pdf, .exe, .wav, .mp3, .mov, .mp4"))
            return

        self.file_path = file_path

        # Hide drop zone and browse button, show remove button
        self.drop_zone.hide()
        self.browse_btn.hide()
        self.remove_btn.show()

        # Update UI with proper file path formatting
        self.file_info.setText(f"<b>File Path</b><br>{file_path}")
        # Tooltip with size info
        try:
            size = os.path.getsize(file_path)
            self.file_info.setToolTip(f"{os.path.basename(file_path)}\nSize: {_human_size(size)} ({size} bytes)")
        except Exception:
            self.file_info.setToolTip(os.path.basename(file_path))
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
        try:
            self.machine.set_encrypt_payload(True)
        except Exception:
            pass
        self.media_type = None
        self.start_xy = None  # (x,y) for image start
        self.start_sample = None  # for audio
        self.audio_info = None  # dict from machine.get_audio_info
        self.video_start = (0, 0, 0)  # (frame,x,y)
        self.video_meta = None  # {'frames':int,'w':int,'h':int,'fps':float}
        self.available_bytes = 0

        # Set gradient background
        self.setStyleSheet("""
            QMainWindow {
                background: #e3f2fd;
            }
        """)

        # Create central widget and main layout
        central_widget = QWidget()
        # Transparent background so the window gradient shows cleanly (avoids dark corners)
        central_widget.setStyleSheet("background: transparent;")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Persistent notification area at the top
        self.notice_container = QVBoxLayout()
        self.notice_container.setSpacing(8)
        self.notice_container.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(self.notice_container)
        # Track overflow banner to avoid duplicates
        self._overflow_banner = None
        self.step_boxes = []
        self.helper_hint_label = None
        self.status_label = None
        self.current_step = 1

        # Quick-start guidance row
        self.create_quickstart_panel(main_layout)

        # Title section
        self.create_title_section(main_layout)

        # Main content area
        self.create_content_area(main_layout)

        # Make the window fullscreen
        self.showMaximized()

    def create_quickstart_panel(self, layout):
        """Create the top quick-start guidance panel."""
        frame = QFrame()
        frame.setObjectName("quickStartFrame")
        frame.setStyleSheet("""
            QFrame#quickStartFrame {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 18px;
                border: 1px solid #d6e4f3;
                padding: 12px 18px;
            }
            QFrame[class="stepCard"] {
                background-color: #f4f9ff;
                border: 1px dashed #c9d6eb;
                border-radius: 14px;
            }
            QFrame[class="stepCard"][active="true"] {
                border: 2px solid #3498db;
                background-color: #e6f2ff;
            }
            QLabel[class="stepNumber"] {
                color: #3498db;
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QLabel[class="stepTitle"] {
                color: #2c3e50;
                font-size: 15px;
                font-weight: 600;
            }
            QLabel[class="stepDetail"] {
                color: #5d6d7e;
                font-size: 12px;
            }
        """)

        wrapper_layout = QVBoxLayout(frame)
        wrapper_layout.setContentsMargins(8, 8, 8, 8)
        wrapper_layout.setSpacing(10)

        steps_layout = QHBoxLayout()
        steps_layout.setSpacing(12)

        steps = [
            ("Select Cover", "Drag & drop or browse for the image / audio / video cover.", "Pick the carrier file that will hide your payload."),
            ("Add Payload", "Type a secret message or attach any file to embed.", "You can embed text, documents, executables or other binaries."),
            ("Secure with Key", "Enter the numeric key and choose whether to encrypt.", "This key drives the PRNG, start offset and optional payload cipher."),
            ("Tune Settings", "Set LSB bits and choose the start location for embedding.", "Higher LSB count increases capacity; pick a start pixel/sample."),
            ("Review & Encode", "Check capacity + proof, then hide the payload.", "Use visual tools to compare cover vs stego before sharing.")
        ]

        self.step_boxes = []
        for idx, (title, detail, tip) in enumerate(steps, start=1):
            card = QFrame()
            card.setProperty("class", "stepCard")
            card.setProperty("active", idx == 1)
            card.setToolTip(tip)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 10, 12, 10)
            card_layout.setSpacing(4)

            number_lbl = QLabel(f"Step {idx}")
            number_lbl.setProperty("class", "stepNumber")
            title_lbl = QLabel(title)
            title_lbl.setProperty("class", "stepTitle")
            title_lbl.setWordWrap(True)
            detail_lbl = QLabel(detail)
            detail_lbl.setProperty("class", "stepDetail")
            detail_lbl.setWordWrap(True)

            card_layout.addWidget(number_lbl)
            card_layout.addWidget(title_lbl)
            card_layout.addWidget(detail_lbl)
            card_layout.addStretch()

            steps_layout.addWidget(card)
            self.step_boxes.append(card)

        wrapper_layout.addLayout(steps_layout)

        helper_layout = QHBoxLayout()
        helper_layout.setContentsMargins(4, 0, 4, 0)
        helper_layout.setSpacing(12)

        self.helper_hint_label = QLabel("Step 1: Start by selecting a cover file.")
        self.helper_hint_label.setStyleSheet("color:#2c3e50;font-weight:600;")
        self.helper_hint_label.setWordWrap(True)

        tour_btn = QPushButton("Show Guided Tour")
        tour_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        tour_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1f8a4c;
            }
        """)
        tour_btn.setToolTip("Walk through the encoding workflow and learn where each feature lives.")
        tour_btn.clicked.connect(self.show_onboarding_tour)

        helper_layout.addWidget(self.helper_hint_label)
        helper_layout.addStretch()
        helper_layout.addWidget(tour_btn)
        wrapper_layout.addLayout(helper_layout)

        layout.addWidget(frame)
        self.reset_workflow_steps()

    def reset_workflow_steps(self):
        """Reset workflow guidance to the first step."""
        self.update_helper_step(1, "Step 1: Start by selecting a cover file.")
        self.set_status('Waiting for cover selection.', 'info')

    def update_helper_step(self, step_index: int, hint: str | None = None):
        """Highlight the active workflow step and update helper text."""
        self.current_step = max(1, min(step_index, len(self.step_boxes) or 1))
        if self.step_boxes:
            for idx, card in enumerate(self.step_boxes, start=1):
                active = idx == self.current_step
                card.setProperty("active", active)
                card.style().unpolish(card)
                card.style().polish(card)
        if hint and self.helper_hint_label:
            self.helper_hint_label.setText(hint)

    def show_step_hint(self, message: str):
        """Convenience helper to refresh the helper hint label."""
        if self.helper_hint_label:
            self.helper_hint_label.setText(message)

    def set_status(self, message: str, severity: str = 'info'):
        """Update the inline status label with colour coding."""
        if not self.status_label:
            return
        colours = {
            'info': ('#2980b9', '#e8f4ff'),
            'success': ('#1e8449', '#e6f8ed'),
            'warning': ('#b9770e', '#fff6e0'),
            'error': ('#c0392b', '#fdecea')
        }
        fg, bg = colours.get(severity, colours['info'])
        self.status_label.setText(f"Status: {message}")
        self.status_label.setStyleSheet(
            f"QLabel {{ color:{fg}; background-color:{bg}; border:1px solid {fg}; "
            "border-radius:10px; padding:8px 16px; font-weight:600; }}"
        )

    def show_onboarding_tour(self):
        """Display a guided tour banner with workflow tips."""
        tour_text = (
            "1. Select your cover image/audio/video.\n"
            "2. Add a payload (type a message or attach a file).\n"
            "3. Enter a numeric key and pick encryption preferences.\n"
            "4. Adjust LSB bits and choose a start location.\n"
            "5. Press 'Hide Message' and review the proof panel/visual tools."
        )
        banner = NotificationBanner(f"Guided tour\n{tour_text}", 'info', self)
        self.notice_container.addWidget(banner)
        banner.show()
        self.set_status("Guided tour: follow the numbered steps above.", 'info')
        self.show_step_hint("Start at Step 1 and work your way across.")

    def create_info_button(self, tooltip_text: str) -> QPushButton:
        """Create a styled info button with tooltip text."""
        btn = QPushButton('i')
        btn.setFixedSize(24, 24)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tooltip_text)
        btn.setStyleSheet(
            """
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
            """
        )
        return btn



    def create_title_section(self, layout):
        """Create the title and back button section"""
        title_layout = QHBoxLayout()

        # Back button
        back_button = QPushButton("â† Back to Main")
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
        cover_scroll.setStyleSheet("QScrollArea{background:transparent;border:none;} QScrollArea>Viewport{background:transparent;}")
        content_layout.addWidget(cover_scroll)

        # Middle column - Payload (fixed width)
        payload_panel = self.create_payload_panel()
        payload_scroll = QScrollArea()
        payload_scroll.setWidget(payload_panel)
        payload_scroll.setWidgetResizable(True)
        payload_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        payload_scroll.setFrameShape(QFrame.Shape.NoFrame)
        payload_scroll.setFixedWidth(400)
        payload_scroll.setStyleSheet("QScrollArea{background:transparent;border:none;} QScrollArea>Viewport{background:transparent;}")
        content_layout.addWidget(payload_scroll)

        # Right column - Controls (fixed width)
        controls_panel = self.create_controls_panel()
        controls_scroll = QScrollArea()
        controls_scroll.setWidget(controls_panel)
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        controls_scroll.setFrameShape(QFrame.Shape.NoFrame)
        controls_scroll.setFixedWidth(400)
        controls_scroll.setStyleSheet("QScrollArea{background:transparent;border:none;} QScrollArea>Viewport{background:transparent;}")
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

        # Inline status banner
        if not self.status_label:
            self.status_label = QLabel('Status: Waiting for inputs.')
            self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.status_label.setWordWrap(True)
            self.status_label.setStyleSheet("QLabel { color:#2980b9; background-color:#e8f4ff; border:1px solid #2980b9; border-radius:10px; padding:8px 16px; font-weight:600; }")
        layout.addWidget(self.status_label)
        self.set_status('Waiting for inputs.', 'info')

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
            "â€¢ Image (.png, .bmp, .gif, .jpg)\n"
            "â€¢ Audio (.wav, .mp3)\n"
            "â€¢ Video (.mov, .mp4)")

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(info_btn)

        # Media drop widget
        self.media_drop_widget = MediaDropWidget()
        self.media_drop_widget.media_loaded.connect(self.on_media_loaded)

        layout.addLayout(header_layout)
        # Connect notify signal for persistent messages
        try:
            self.media_drop_widget.notify.connect(self.show_persistent_notice)
        except Exception:
            pass
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
            "â€¢ Text Input\n"
            "â€¢ Text File (.txt)\n"
            "â€¢ .pdf\n"
            "â€¢ .exe\n"
            "â€¢ Audio (.wav, .mp3)\n"
            "â€¢ Video (.mov, .mp4)")

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(info_btn)

        # Text input (first row)
        self.message_text = QTextEdit()
        self.message_text.setPlaceholderText(
            "Enter your secret message here...")
        self.message_text.setToolTip('Step 2: Type a short secret message to embed (optional).')
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
        self.message_text.textChanged.connect(self.on_payload_text_changed)

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
        self.payload_drop_widget.setToolTip('Upload a payload file (any binary). Drag & drop or browse to continue Step 2.')
        self.payload_drop_widget.file_loaded.connect(self.on_payload_file_loaded)
        try:
            self.payload_drop_widget.notify.connect(self.show_persistent_notice)
        except Exception:
            pass

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
            "â€¢ LSB: Higher -> more capacity, lower quality\n"
            "â€¢ Key: Numeric, required for reproducibility\n"
            "â€¢ Output Path: Default to datetime")

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
        self.lsb_slider.setToolTip('Step 4: Choose how many least-significant bits to use for embedding. Higher values increase capacity but change more data.')
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
        self.key_input.setToolTip('Step 3: This numeric key is required for both encoding and decoding.')
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

        self.key_input.textChanged.connect(self.on_key_changed)
        key_layout.addWidget(self.key_input)

        self.encrypt_checkbox = QCheckBox("Encrypt payload before embedding (recommended)")
        self.encrypt_checkbox.setToolTip('Use the numeric key to derive an XOR keystream before embedding the payload.')
        self.encrypt_checkbox.setChecked(True)
        self.encrypt_checkbox.toggled.connect(self.on_encrypt_toggle)
        key_layout.addWidget(self.encrypt_checkbox)

        # Capacity group
        capacity_group = QGroupBox("Capacity")
        cap_layout = QVBoxLayout(capacity_group)
        self.cap_dims = QLabel("Cover: -")
        self.cap_lsb = QLabel("LSB bits: 1")
        self.cap_header = QLabel("Header bytes: -")
        self.cap_startbits = QLabel("Start bit offset: 0")
        self.cap_max = QLabel("Capacity (bytes): -")
        self.cap_avail = QLabel("Available bytes: -")
        for lbl in [self.cap_dims, self.cap_lsb, self.cap_header, self.cap_startbits, self.cap_max, self.cap_avail]:
            lbl.setStyleSheet("color:#2c3e50;")
            cap_layout.addWidget(lbl)
        # Capacity usage bar
        self.cap_usage_bar = QProgressBar()
        self.cap_usage_bar.setRange(0, 100)
        self.cap_usage_bar.setValue(0)
        self.cap_usage_bar.setTextVisible(True)
        self.cap_usage_bar.setFormat("Payload: %v / %m bytes")
        self.cap_usage_bar.setStyleSheet(
            "QProgressBar{border:1px solid #bdc3c7;border-radius:6px;background:#ecf0f1;text-align:center;}"
            "QProgressBar::chunk{background-color:#2ecc71;border-radius:6px;}"
        )
        cap_layout.addWidget(self.cap_usage_bar)
        # Capacity status pill
        self.cap_status = QLabel("OK")
        self.cap_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cap_status.setStyleSheet(
            "QLabel{background:#eafaf1;color:#2e7d32;border-radius:10px;padding:4px 8px;font-weight:bold;}" 
        )
        cap_layout.addWidget(self.cap_status)
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
        self.proof_stats = QLabel("LSB stats: -")
        for lbl in [self.proof_lsb, self.proof_start, self.proof_perm, self.proof_header, self.proof_stats]:
            lbl.setStyleSheet("color:#2c3e50;")
            lbl.setWordWrap(True)
            proof_layout.addWidget(lbl)
        # Mini visualization for permutation (8-wide max)
        self.perm_vis = QLabel()
        self.perm_vis.setFixedHeight(20)
        self.perm_vis.setToolTip('Permutation visual: colours map the bit positions (0-7) in the embedding order.')
        self.perm_vis.setStyleSheet("QLabel{background:#f8f9fa;border:1px dashed #bdc3c7;border-radius:8px;}")
        proof_layout.addWidget(self.perm_vis)

        legend = QLabel('Legend: coloured squares show the per-byte LSB permutation order; LSB stats compare the percentage of ones in cover vs stego for each bit.')
        legend.setStyleSheet('color:#5d6d7e;font-size:12px;')
        legend.setWordWrap(True)
        proof_layout.addWidget(legend)

        # Visualization toggles
        vis_group = QGroupBox("Visualization")
        vis_layout = QVBoxLayout(vis_group)
        self.lsb_toggle_btn = QPushButton("Show LSB plane")
        self.lsb_toggle_btn.setToolTip('Visualise the least significant bit plane of the cover image/audio preview.')
        self.lsb_toggle_btn.setCheckable(True)
        self.lsb_toggle_btn.setStyleSheet("""
            QPushButton { background-color: #95a5a6; color: white; border: none; padding: 8px 12px; border-radius: 5px; }
            QPushButton:checked { background-color: #2ecc71; }
        """)
        self.lsb_toggle_btn.toggled.connect(self.on_lsb_toggle)
        vis_layout.addWidget(self.lsb_toggle_btn)
        # Diff map toggle (enabled after stego exists)
        self.diff_toggle_btn = QPushButton("Show Difference Map")
        self.diff_toggle_btn.setToolTip('Toggle to highlight which pixels changed between cover and stego outputs.')
        self.diff_toggle_btn.setCheckable(True)
        self.diff_toggle_btn.setEnabled(False)
        self.diff_toggle_btn.setStyleSheet("""
            QPushButton { background-color: #95a5a6; color: white; border: none; padding: 8px 12px; border-radius: 5px; }
            QPushButton:checked { background-color: #e67e22; }
        """)
        self.diff_toggle_btn.toggled.connect(self.on_diff_toggle)
        vis_layout.addWidget(self.diff_toggle_btn)

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

    def _update_capacity_visuals(self, max_bytes: int, available_bytes: int):
        """Update progress bar and status pill for capacity usage."""
        try:
            need = self.current_payload_len()
            # Progress proportion: show portion of available used; clamp to show overflow as 100%
            denom = max(available_bytes, need, 1)
            self.cap_usage_bar.setRange(0, denom)
            self.cap_usage_bar.setValue(need)
            # Text shows exact numbers
            self.cap_usage_bar.setFormat(f"Need: {need} bytes  |  Available: {available_bytes} bytes")
            # Style/state
            if available_bytes <= 0:
                chunk = "#bdc3c7"  # gray
                status_css = "QLabel{background:#eceff1;color:#546e7a;border-radius:10px;padding:4px 8px;font-weight:bold;}"
                status_txt = "No capacity"
            else:
                ratio = need / available_bytes if available_bytes else 1.0
                if need > available_bytes:
                    chunk = "#e74c3c"  # red
                    status_css = "QLabel{background:#fdecea;color:#c62828;border-radius:10px;padding:4px 8px;font-weight:bold;}"
                    status_txt = "Too large"
                elif ratio >= 0.9:
                    chunk = "#f1c40f"  # yellow
                    status_css = "QLabel{background:#fff8e1;color:#ff8f00;border-radius:10px;padding:4px 8px;font-weight:bold;}"
                    status_txt = "Near limit"
                else:
                    chunk = "#2ecc71"  # green
                    status_css = "QLabel{background:#eafaf1;color:#2e7d32;border-radius:10px;padding:4px 8px;font-weight:bold;}"
                    status_txt = "Fits"
            self.cap_usage_bar.setStyleSheet(
                "QProgressBar{border:1px solid #bdc3c7;border-radius:6px;background:#ecf0f1;text-align:center;}"
                f"QProgressBar::chunk{{background-color:{chunk};border-radius:6px;}}"
            )
            self.cap_status.setStyleSheet(status_css)
            self.cap_status.setText(status_txt)
        except Exception:
            pass

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

    def show_persistent_notice(self, message: str, severity: str = 'info'):
        """Display a persistent banner at the top of the window."""
        try:
            banner = NotificationBanner(message, severity, self)
            # Auto-remove when closed
            try:
                banner.closed.connect(lambda: None)
            except Exception:
                pass
            self.notice_container.addWidget(banner)
            banner.show()
        except Exception as e:
            print(f"Failed to show banner: {e}")

    def _set_overflow_banner(self, message: str | None):
        """Create/update/clear the capacity overflow persistent banner."""
        try:
            # Create/update
            if message:
                if self._overflow_banner is None:
                    banner = NotificationBanner(message, 'error', self)
                    def _on_closed():
                        try:
                            self._overflow_banner = None
                        except Exception:
                            pass
                    try:
                        banner.closed.connect(_on_closed)
                    except Exception:
                        pass
                    self.notice_container.addWidget(banner)
                    banner.show()
                    self._overflow_banner = banner
                else:
                    self._overflow_banner.setText(message)
            else:
                # Clear existing
                if self._overflow_banner is not None:
                    try:
                        self._overflow_banner._on_close()
                    except Exception:
                        pass
                    self._overflow_banner = None
        except Exception as e:
            print(f"Failed to manage overflow banner: {e}")

    def on_media_loaded(self, file_path, media_type):
        """Handle media loaded from drag and drop or browse"""
        if hasattr(self, 'reset_lsb_stats'):
            self.reset_lsb_stats()
        if not file_path:  # Media was removed
            self.set_status('Cover cleared. Select a cover to begin.', 'info')
            self.reset_workflow_steps()
            self.media_type = None
            return

        print(f"Media loaded: {file_path} ({media_type})")
        self.media_type = media_type
        self.start_xy = None
        self.update_helper_step(2, 'Step 2: Add a payload (type a message or attach a file).')
        self.set_status(f'Cover ready: {os.path.basename(file_path)}', 'success')

        # Update machine with media
        if media_type == 'image':
            # Handle JPEG prompt and GIF frame 0 conversion
            ext = os.path.splitext(file_path)[1].lower()
            convert_path = None
            if ext in ['.jpg', '.jpeg']:
                from PyQt6.QtWidgets import QMessageBox
                resp = QMessageBox.question(self, "Convert JPEG to PNG?",
                                            "JPEG is lossy and will not preserve LSBs reliably. Convert to PNG for lossless embedding?",
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                            QMessageBox.StandardButton.Yes)
                if resp == QMessageBox.StandardButton.Yes:
                    try:
                        img = Image.open(file_path)
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        base, _ = os.path.splitext(file_path)
                        convert_path = base + "_lossless.png"
                        img.save(convert_path, format='PNG')
                        file_path = convert_path
                    except Exception as e:
                        print(f"JPEG->PNG conversion failed: {e}")
            elif ext == '.gif':
                try:
                    img = Image.open(file_path)
                    try:
                        img.seek(0)
                    except Exception:
                        pass
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    base, _ = os.path.splitext(file_path)
                    convert_path = base + "_frame0.png"
                    img.save(convert_path, format='PNG')
                    file_path = convert_path
                except Exception as e:
                    print(f"GIF frame0 conversion failed: {e}")

            if self.machine.set_cover_image(file_path):
                info = self.machine.get_image_info()
                print(f"âœ… Image loaded: {os.path.basename(file_path)}")
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
                if hasattr(self, 'diff_toggle_btn'):
                    self.diff_toggle_btn.setChecked(False)
                    self.diff_toggle_btn.setEnabled(False)
            else:
                print("âŒ Error loading image")
        elif media_type == 'audio':
            # WAV PCM
            if self.machine.set_cover_audio(file_path):
                try:
                    self.audio_info = self.machine.get_audio_info(file_path)
                    print(f"âœ… WAV loaded: {os.path.basename(file_path)}  {self.audio_info}")
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
                print("âŒ Error loading audio")
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
                self.video_meta = {'frames': frames, 'w': w, 'h': h, 'fps': float(fps)}
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
                # connect XY selection from preview if available
                if self.media_drop_widget.preview_widget and hasattr(self.media_drop_widget.preview_widget, 'xy_selected'):
                    try:
                        self.media_drop_widget.preview_widget.xy_selected.connect(self.on_video_xy_selected)
                    except Exception:
                        pass
                # Allow embedding now that we will write lossless AVI
                if hasattr(self, 'hide_button'):
                    self.hide_button.setEnabled(True)
            except Exception as e:
                print(f"Video probe failed: {e}")
                self.set_status('Could not read video metadata. Try a different file.', 'error')
                self.reset_workflow_steps()
                if hasattr(self, 'hide_button'):
                    self.hide_button.setEnabled(False)
            self.update_capacity_panel()

    def on_payload_text_changed(self):
        text_value = self.message_text.toPlainText() if hasattr(self, 'message_text') else ''
        has_text = bool(text_value.strip())
        if has_text and not self.machine.payload_file_path:
            self.update_helper_step(3, "Step 3: Enter your numeric key to secure the payload.")
            self.set_status('Payload text ready. Enter your numeric key next.', 'success')
        elif not has_text and not self.machine.payload_file_path:
            self.update_helper_step(2, "Step 2: Add a payload file or type a message.")
            self.set_status('Add a payload file or type a secret message.', 'info')

    def on_key_changed(self, value: str):
        if value and value.strip().isdigit():
            self.update_helper_step(4, "Step 4: Adjust LSB bits and choose the start location.")
            self.set_status('Key ready. Adjust LSB bits and pick a start location.', 'success')
            self.show_step_hint('Tweak the embedding settings and mark a start location on the cover.')
        else:
            if not value.strip():
                self.update_helper_step(3, "Step 3: Enter your numeric key to secure the payload.")
                self.set_status('Enter your numeric key to continue.', 'info')

    def on_payload_file_loaded(self, file_path):
        """Handle payload file loaded from drag and drop or browse"""
        if hasattr(self, 'reset_lsb_stats'):
            self.reset_lsb_stats()
        if not file_path:  # File was removed
            print("Payload file removed")
            if not (hasattr(self, 'message_text') and self.message_text.toPlainText().strip()):
                self.update_helper_step(2, 'Step 2: Add a payload file or type a message.')
            self.set_status('Payload removed. Add a new payload to continue.', 'info')
            return

        print(f"Payload file loaded: {file_path}")

        # Update machine with payload file
        if self.machine.set_payload_file(file_path):
            print(f"�o. Payload file loaded: {os.path.basename(file_path)}")
            self.update_helper_step(3, 'Step 3: Enter your numeric key to secure the payload.')
            self.set_status(f'Payload ready: {os.path.basename(file_path)}', 'success')
            self.update_capacity_panel()
        else:
            print("Error loading payload file")
            self.set_status('Could not load the selected payload.', 'error')

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
        self.set_status("Validating inputs...", 'info')
        self.machine.set_lsb_bits(self.lsb_slider.value())
        self.machine.set_encryption_key(self.key_input.text())
        if hasattr(self, 'encrypt_checkbox'):
            try:
                self.machine.set_encrypt_payload(self.encrypt_checkbox.isChecked())
            except Exception as exc:
                print(f"Failed to sync encryption toggle: {exc}")

        key_value = self.key_input.text().strip()
        if not key_value.isdigit():
            self.set_status("Numeric key required before encoding.", 'warning')
            self.update_helper_step(3, "Step 3: Enter your numeric key to secure the payload.")
            self.show_step_hint("Enter a numeric key to continue.")
            return

        if hasattr(self, 'reset_lsb_stats'):
            self.reset_lsb_stats("LSB stats: computing...")

        if self.message_text.toPlainText().strip():
            self.machine.set_payload_text(self.message_text.toPlainText())

        if not self.output_path.text().strip():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_path = f"stego_output_{timestamp}.png"
            if self.media_type == 'audio':
                default_path = f"stego_output_{timestamp}.wav"
            elif self.media_type == 'video':
                default_path = f"stego_output_{timestamp}.avi"
            self.output_path.setText(default_path)
            self.machine.set_output_path(default_path)

        ok = False
        if self.media_type == 'image':
            if self.start_xy is None:
                self.set_status("Pick a start pixel on the cover image before encoding.", 'warning')
                self.update_helper_step(4, "Step 4: Click the cover preview to choose a start location.")
                self.show_step_hint("Click on the cover preview to set the embed start pixel.")
                return
            ok = self.machine.hide_message(start_xy=self.start_xy)
        elif self.media_type == 'audio':
            if not self.output_path.text().strip():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_path = f"stego_output_{timestamp}.wav"
                self.output_path.setText(default_path)
                self.machine.set_output_path(default_path)
            start_sample = self.start_sample if self.start_sample is not None else 0
            try:
                filename = os.path.basename(self.machine.payload_file_path) if self.machine.payload_file_path else "payload.bin"
                audio_bytes = self.machine.encode_audio(
                    self.media_drop_widget.media_path,
                    self.machine.payload_data or b"",
                    filename,
                    self.lsb_slider.value(),
                    self.key_input.text(),
                    start_sample=start_sample,
                )
                with open(self.output_path.text(), 'wb') as handle:
                    handle.write(audio_bytes)
                ok = True
            except Exception as exc:
                self.machine.last_error = str(exc)
                print(f"Audio encode failed: {exc}")
                ok = False
        elif self.media_type == 'video':
            if not self.output_path.text().strip():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_path = f"stego_output_{timestamp}.avi"
                self.output_path.setText(default_path)
                self.machine.set_output_path(default_path)
            try:
                filename = os.path.basename(self.machine.payload_file_path) if self.machine.payload_file_path else "payload.bin"
                f, x, y = self.video_start
                outp = self.machine.encode_video(
                    self.media_drop_widget.media_path,
                    self.machine.payload_data or b"",
                    filename,
                    self.lsb_slider.value(),
                    self.key_input.text(),
                    start_fxy=(f, x, y),
                    out_path=self.output_path.text(),
                )
                ok = bool(outp)
            except Exception as exc:
                self.machine.last_error = str(exc)
                print(f"Video encode failed: {exc}")
                ok = False
        else:
            self.set_status('Embedding into this media type is not supported. Use an image, WAV, or RGB video cover.', 'warning')
            return

        if ok:
            print("Steganography completed successfully!")
            self.set_status(f"Stego saved: {self.machine.output_path}", 'success')
            self.update_helper_step(5, "Step 5: Review the proof panel and visualisations.")
            info = getattr(self.machine, 'last_embed_info', None)
            if info:
                encrypted_flag = info.get('encrypted')
                self.proof_lsb.setText(f"LSB bits: {info.get('lsb_bits')} | encrypted: {'yes' if encrypted_flag else 'no'}")
                self.proof_start.setText(f"Start bit: {info.get('start_bit')}")
                perm = info.get('perm', [])
                self.proof_perm.setText(f"Perm [0:8]: {perm[:8]}")
                hdr = info.get('header', {})
                flags = hdr.get('flags', 0)
                nonce_bytes = hdr.get('nonce') if isinstance(hdr.get('nonce'), (bytes, bytearray)) else b''
                nonce_hex = nonce_bytes.hex() if nonce_bytes else '-'
                enc_status = 'yes' if flags & FLAG_PAYLOAD_ENCRYPTED else 'no'
                self.proof_header.setText(
                    f"Header: ver={hdr.get('version')} lsb={hdr.get('lsb_bits')} start={hdr.get('start_bit_offset')} len={hdr.get('payload_len')} flags=0x{flags:02X} enc={enc_status} fname='{hdr.get('filename')}' crc=0x{hdr.get('crc32'):08X} nonce={nonce_hex}"
                )
                try:
                    n = min(8, len(perm))
                    if n > 0:
                        w, h = 8 * 18, 18
                        pm = QPixmap(w, h)
                        pm.fill(Qt.GlobalColor.transparent)
                        painter = QPainter(pm)
                        for i in range(n):
                            val = int(perm[i]) if isinstance(perm[i], (int, float)) else 0
                            hue = (val % 8) / 8.0
                            color = QColor.fromHsvF(hue, 0.7, 0.9)
                            painter.fillRect(i * 18 + 1, 1, 16, 16, color)
                            painter.setPen(QPen(QColor(255, 255, 255)))
                            painter.drawText(i * 18 + 1, 1, 16, 16, Qt.AlignmentFlag.AlignCenter, str(val))
                        painter.end()
                        self.perm_vis.setPixmap(pm)
                except Exception:
                    pass
            else:
                if hasattr(self, 'reset_lsb_stats'):
                    self.reset_lsb_stats()
            if self.media_type == 'image':
                out_path = self.output_path.text().strip()
                if out_path and os.path.exists(out_path):
                    self.update_lsb_stats_image(self.media_drop_widget.media_path, out_path, self.lsb_slider.value())
            elif self.media_type == 'audio':
                out_path = self.output_path.text().strip()
                if out_path and os.path.exists(out_path):
                    self.update_lsb_stats_audio(self.media_drop_widget.media_path, out_path, self.lsb_slider.value())
            else:
                if hasattr(self, 'reset_lsb_stats'):
                    self.reset_lsb_stats('LSB stats: (video analysis coming soon)')
            if self.media_type == 'image' and hasattr(self, 'diff_toggle_btn'):
                out = self.output_path.text().strip()
                self.diff_toggle_btn.setEnabled(bool(out and os.path.exists(out)))
            if self.media_type == 'audio' and hasattr(self, 'play_stego_btn'):
                self.play_stego_btn.setEnabled(True)
            self.show_step_hint('Encoding complete. Review the proof panel or share the stego file.')
        else:
            print("Steganography failed!")
            detail = getattr(self.machine, 'last_error', 'Steganography failed. See console for details.')
            self.set_status(detail, 'error')
            self.show_step_hint("Resolve the issue above, then try encoding again.")
            if hasattr(self, 'reset_lsb_stats'):
                self.reset_lsb_stats()


    def on_start_pixel_selected(self, x, y):
        self.start_xy = (x, y)
        self.update_helper_step(5, 'Step 5: Press Hide Message to embed and review the proof panel.')
        self.show_step_hint('Start location locked. Ready to encode when you are.')
        try:
            self.update_capacity_panel()
        except Exception:
            pass

    def on_encrypt_toggle(self, checked: bool):
        try:
            self.machine.set_encrypt_payload(bool(checked))
        except Exception as e:
            print(f"Failed to toggle encryption: {e}")

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
                    header_bytes = pack_header(header_meta)
                except Exception:
                    header_bytes = b""
                header_bits = len(header_bytes) * 8
                f, x, y = self.video_start
                total_bits = self.machine.estimate_capacity_bits(self.media_drop_widget.media_path, 'video', lsb, (f, x, y))
                max_bytes = total_bits // 8
                zero_start = (f == 0 and x == 0 and y == 0)
                available_bits = max(0, total_bits - header_bits) if zero_start else max(0, total_bits)
                self.available_bytes = available_bits // 8
                # Compute start bit offset if we know video dimensions
                if self.video_meta:
                    w = self.video_meta.get('w', 0)
                    h = self.video_meta.get('h', 0)
                    start_bit = ((f * (w * h) + y * w + x) * 3 * max(1, lsb)) if (w and h) else 0
                    if f == 0 and x == 0 and y == 0 and header_bits:
                        self.cap_startbits.setText(f"Start bit offset: {header_bits} (header reserved)")
                    else:
                        self.cap_startbits.setText(f"Start bit offset: {start_bit}")
                self.cap_lsb.setText(f"LSB bits: {lsb}")
                self.cap_header.setText(f"Header bytes: {len(header_bytes)}")
                self.cap_max.setText(f"Capacity (bytes): {max_bytes}")
                self.cap_avail.setText(f"Available bytes: {self.available_bytes}")
                try:
                    self._update_capacity_visuals(max_bytes, self.available_bytes)
                except Exception:
                    pass
                too_large = self.current_payload_len() > self.available_bytes if header_bytes else False
                if hasattr(self, 'hide_button'):
                    self.hide_button.setEnabled(not too_large)
                # Notify user if payload is too big
                if too_large:
                    msg = f"Payload too large. Available: {_human_size(self.available_bytes)}, Need: {_human_size(self.current_payload_len())}"
                    try:
                        QToolTip.showText(QCursor.pos(), msg, self)
                    except Exception:
                        pass
                    try:
                        self.cap_avail.setToolTip(msg)
                        self.cap_avail.setStyleSheet("color:#e74c3c;")
                        self.cap_avail.setText(f"Available bytes: {self.available_bytes}  (Too large)")
                    except Exception:
                        pass
                    # Persistent banner
                    try:
                        self._set_overflow_banner(msg)
                    except Exception:
                        pass
                else:
                    try:
                        self.cap_avail.setToolTip("")
                        self.cap_avail.setStyleSheet("color:#2c3e50;")
                        self.cap_avail.setText(f"Available bytes: {self.available_bytes}")
                    except Exception:
                        pass
                    try:
                        self._set_overflow_banner(None)
                    except Exception:
                        pass
            except Exception as e:
                print(f"Video capacity update failed: {e}")
            return
        # Default reset
        self.cap_dims.setText("Cover: -")
        self.cap_lsb.setText(f"LSB bits: {self.lsb_slider.value()}")
        self.cap_header.setText("Header bytes: -")
        self.cap_max.setText("Capacity (bytes): -")
        self.cap_avail.setText("Available bytes: -")
        try:
            self._update_capacity_visuals(0, 0)
        except Exception:
            pass
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
                    header_bytes = pack_header(header_meta)
                except Exception:
                    header_bytes = b""
                header_bits = len(header_bytes) * 8
                start_sample = self.start_sample if self.start_sample is not None else 0
                channels = info.get('channels', 1)
                channels = int(channels) if isinstance(channels, (int, float)) else 1
                samp_bits = info.get('sampwidth_bits', 8)
                samp_bits = int(samp_bits) if isinstance(samp_bits, (int, float)) else 8
                bytes_per_frame = max(1, channels * max(1, samp_bits // 8))
                start_bit_offset = start_sample * bytes_per_frame * max(1, lsb)
                if start_sample == 0 and header_bits:
                    self.cap_startbits.setText(f"Start bit offset: {header_bits} (header reserved)")
                else:
                    self.cap_startbits.setText(f"Start bit offset: {start_bit_offset}")
                total_bits = self.machine.estimate_capacity_bits(self.media_drop_widget.media_path, 'audio', lsb, start_sample)
                max_bytes = total_bits // 8
                available_bits = max(0, total_bits - header_bits) if start_sample == 0 else max(0, total_bits)
                self.available_bytes = available_bits // 8
                self.cap_lsb.setText(f"LSB bits: {lsb}")
                self.cap_header.setText(f"Header bytes: {len(header_bytes)}")
                self.cap_max.setText(f"Capacity (bytes): {max_bytes}")
                self.cap_avail.setText(f"Available bytes: {self.available_bytes}")
                try:
                    self._update_capacity_visuals(max_bytes, self.available_bytes)
                except Exception:
                    pass
                too_large = self.current_payload_len() > self.available_bytes if header_bytes else False
                if hasattr(self, 'hide_button'):
                    self.hide_button.setEnabled(not too_large)
                if too_large:
                    msg = f"Payload too large. Available: {_human_size(self.available_bytes)}, Need: {_human_size(self.current_payload_len())}"
                    try:
                        QToolTip.showText(QCursor.pos(), msg, self)
                    except Exception:
                        pass
                    try:
                        self.cap_avail.setToolTip(msg)
                        self.cap_avail.setStyleSheet("color:#e74c3c;")
                        self.cap_avail.setText(f"Available bytes: {self.available_bytes}  (Too large)")
                    except Exception:
                        pass
                    try:
                        self._set_overflow_banner(msg)
                    except Exception:
                        pass
                else:
                    try:
                        self.cap_avail.setToolTip("")
                        self.cap_avail.setStyleSheet("color:#2c3e50;")
                        self.cap_avail.setText(f"Available bytes: {self.available_bytes}")
                    except Exception:
                        pass
                    try:
                        self._set_overflow_banner(None)
                    except Exception:
                        pass
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
            header_bytes = pack_header(header_meta)
        except Exception:
            header_bytes = b""
        header_bits = len(header_bytes) * 8

        if self.start_xy is not None:
            x, y = self.start_xy
            pixel_index = y * w + x
            start_bit = pixel_index * channels * lsb
            if header_bits and start_bit < header_bits:
                self.cap_startbits.setText(f"Start bit offset: {start_bit} (overlaps header)")
            else:
                self.cap_startbits.setText(f"Start bit offset: {start_bit}")
        else:
            start_bit = header_bits
            self.cap_startbits.setText(f"Start bit offset: {header_bits}")

        payload_start = max(start_bit, header_bits)
        usable_bits = max(0, total_bits - payload_start)
        max_bytes = usable_bits // 8
        self.available_bytes = max_bytes

        self.cap_dims.setText(f"Cover: {w}x{h}x{channels}")
        self.cap_lsb.setText(f"LSB bits: {lsb}")
        self.cap_header.setText(f"Header bytes: {len(header_bytes)}")
        self.cap_max.setText(f"Capacity (bytes): {max_bytes}")
        self.cap_avail.setText(f"Available bytes: {self.available_bytes}")
        try:
            self._update_capacity_visuals(max_bytes, self.available_bytes)
        except Exception:
            pass

        too_large = self.current_payload_len() > self.available_bytes if header_bytes else False
        if hasattr(self, 'hide_button'):
            self.hide_button.setEnabled(not too_large)
        # Notify on overflow
        if too_large:
            msg = f"Payload too large. Available: {_human_size(self.available_bytes)}, Need: {_human_size(self.current_payload_len())}"
            try:
                QToolTip.showText(QCursor.pos(), msg, self)
            except Exception:
                pass
            try:
                self.cap_avail.setToolTip(msg)
                self.cap_avail.setStyleSheet("color:#e74c3c;")
                self.cap_avail.setText(f"Available bytes: {self.available_bytes}  (Too large)")
            except Exception:
                pass
            try:
                self._set_overflow_banner(msg)
            except Exception:
                pass
        else:
            try:
                self.cap_avail.setToolTip("")
                self.cap_avail.setStyleSheet("color:#2c3e50;")
                self.cap_avail.setText(f"Available bytes: {self.available_bytes}")
            except Exception:
                pass
            try:
                self._set_overflow_banner(None)
            except Exception:
                pass

    def on_diff_toggle(self, checked: bool):
        # Only for images with a saved stego output
        if self.media_type != 'image':
            return
        out = self.output_path.text().strip()
        if not (out and os.path.exists(out)):
            self.diff_toggle_btn.setChecked(False)
            return
        # Require an image preview widget
        if not (self.media_drop_widget.preview_widget and hasattr(self.media_drop_widget.preview_widget, 'pixmap_item')):
            return
        try:
            cover_path = self.media_drop_widget.media_path
            stego_path = out
            cov = Image.open(cover_path)
            stg = Image.open(stego_path)
            if cov.mode != 'RGB':
                cov = cov.convert('RGB')
            if stg.mode != 'RGB':
                stg = stg.convert('RGB')
            a = np.array(cov, dtype=np.uint8)
            b = np.array(stg, dtype=np.uint8)
            lsb = max(1, self.lsb_slider.value())
            mask = (1 << lsb) - 1
            diff = (a ^ b) & mask
            scale = 255 // mask if mask else 255
            vis = (diff * scale).astype(np.uint8)
            qimg = QImage(vis.data, vis.shape[1], vis.shape[0], vis.shape[1]*3, QImage.Format.Format_RGB888)
            pm = QPixmap.fromImage(qimg)
            if checked:
                self.media_drop_widget.preview_widget.pixmap_item.setPixmap(pm)
            else:
                # Restore original preview
                orig = QPixmap(cover_path)
                self.media_drop_widget.preview_widget.pixmap_item.setPixmap(orig)
        except Exception as e:
            print(f"Failed to show diff map: {e}")

    def update_lsb_stats_image(self, cover_path: str, stego_path: str, lsb_bits: int) -> None:
        if not hasattr(self, 'proof_stats'):
            return
        try:
            with Image.open(cover_path) as cover_im:
                cover = cover_im.convert('RGB') if cover_im.mode != 'RGB' else cover_im.copy()
            with Image.open(stego_path) as stego_im:
                stego = stego_im.convert('RGB') if stego_im.mode != 'RGB' else stego_im.copy()
            cov_arr = np.array(cover, dtype=np.uint8)
            stg_arr = np.array(stego, dtype=np.uint8)
            stats = []
            for bit in range(max(1, lsb_bits)):
                mask = 1 << bit
                cov_ratio = float(((cov_arr & mask) != 0).mean() * 100.0)
                stg_ratio = float(((stg_arr & mask) != 0).mean() * 100.0)
                stats.append(f"bit{bit}: cover {cov_ratio:.2f}% / stego {stg_ratio:.2f}% ones")
            self.proof_stats.setText("\n".join(stats))
        except Exception as e:
            self.proof_stats.setText(f"LSB stats unavailable: {e}")

    def update_lsb_stats_audio(self, cover_path: str, stego_path: str, lsb_bits: int) -> None:
        if not hasattr(self, 'proof_stats'):
            return
        try:
            import wave
            with wave.open(cover_path, 'rb') as wf_cover:
                cover_bytes = wf_cover.readframes(wf_cover.getnframes())
            with wave.open(stego_path, 'rb') as wf_stego:
                stego_bytes = wf_stego.readframes(wf_stego.getnframes())
            cov_arr = np.frombuffer(cover_bytes, dtype=np.uint8)
            stg_arr = np.frombuffer(stego_bytes, dtype=np.uint8)
            length = min(cov_arr.size, stg_arr.size)
            if length == 0:
                raise ValueError('empty buffers')
            cov_arr = cov_arr[:length]
            stg_arr = stg_arr[:length]
            stats = []
            for bit in range(max(1, lsb_bits)):
                mask = 1 << bit
                cov_ratio = float(((cov_arr & mask) != 0).mean() * 100.0)
                stg_ratio = float(((stg_arr & mask) != 0).mean() * 100.0)
                stats.append(f"bit{bit}: cover {cov_ratio:.2f}% / stego {stg_ratio:.2f}% ones")
            self.proof_stats.setText("\n".join(stats))
        except Exception as e:
            self.proof_stats.setText(f"LSB stats unavailable: {e}")

    def reset_lsb_stats(self, message: str = "LSB stats: -") -> None:
        if hasattr(self, 'proof_stats'):
            self.proof_stats.setText(message)

    def on_audio_time_selected(self, t: float):
        # Convert time to start_sample
        try:
            if self.audio_info and self.audio_info.get('sample_rate'):
                sr = int(self.audio_info['sample_rate'])
                self.start_sample = int(max(0.0, t) * sr)
            else:
                self.start_sample = 0
            self.update_helper_step(5, 'Step 5: Press Hide Message to embed and review the proof panel.')
            self.show_step_hint('Start sample selected. You can encode when ready.')
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

    def on_video_xy_selected(self, frame: int, x: int, y: int):
        # Update start frame and XY from click
        self.video_start = (int(frame), int(x), int(y))
        self.update_helper_step(5, 'Step 5: Press Hide Message to embed and review the proof panel.')
        self.show_step_hint('Start frame selected. Ready to encode when you are.')
        print(f"[Window] video xy selected -> frame={frame}, x={x}, y={y}")
        if hasattr(self, 'video_pos_label'):
            self.video_pos_label.setText(f"Frame: {int(frame)}, X: {int(x)}, Y: {int(y)}")
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





