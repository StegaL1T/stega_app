# gui/stega_encode_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QFileDialog, QTextEdit,
                             QGroupBox, QGridLayout, QLineEdit, QComboBox, QSlider,
                             QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                             QScrollArea, QSlider as QTimeSlider, QToolTip, QProgressBar,
                             QCheckBox, QToolButton, QSizePolicy, QApplication)
from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QDragEnterEvent, QDropEvent, QImage, QCursor
import os
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from PIL.ImageQt import ImageQt
import soundfile as sf
import cv2
from datetime import datetime
from machine.stega_spec import (HeaderMeta, FLAG_PAYLOAD_ENCRYPTED, pack_header, HEADER_MAGIC, HEADER_VERSION)
from crypto_honey import list_universes
import math
import random


def _human_size(num: int) -> str:
    """Return human readable file size."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"


class CustomCheckBox(QCheckBox):
    """Custom checkbox with visible checkmark"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QCheckBox {
                color: #e8e8fc;
                font-weight: 500;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 4px;
                background-color: #0e1625;
            }
            QCheckBox::indicator:checked {
                background-color: #45edf2;
                border: 2px solid #45edf2;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #45edf2;
                background-color: rgba(69,237,242,0.1);
            }
            QCheckBox::indicator:checked:hover {
                background-color: #45edf2;
                border: 2px solid #45edf2;
            }
        """)
    
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.isChecked():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Calculate indicator rect manually (18x18px checkbox)
            checkbox_size = 18
            spacing = 8  # spacing between checkbox and text
            checkbox_x = 0
            checkbox_y = (self.height() - checkbox_size) // 2
            
            # Draw checkmark
            painter.setPen(QPen(QColor("#0d1625"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            
            # Draw checkmark path - bigger and centered
            center_x = checkbox_x + checkbox_size // 2
            center_y = checkbox_y + checkbox_size // 2
            scale = checkbox_size * 0.6  # Increased from 0.4 to 0.6 for bigger checkmark
            
            # Checkmark coordinates (convert to integers) - better centered
            painter.drawLine(
                int(center_x - scale*0.4), int(center_y + scale*0.1),
                int(center_x - scale*0.1), int(center_y + scale*0.4)
            )
            painter.drawLine(
                int(center_x - scale*0.1), int(center_y + scale*0.4),
                int(center_x + scale*0.4), int(center_y - scale*0.3)
            )
            
            painter.end()


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


class NotificationBanner(QFrame):
    """Persistent, dismissible banner for inline notifications."""
    closed = pyqtSignal()

    def __init__(self, message: str, severity: str = 'info', parent: QWidget | None = None, show_close_button: bool = True):
        super().__init__(parent)
        self._message_label = QLabel()
        self._close_btn = None
        if show_close_button:
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
            bg = "rgba(14,22,37,0.8)"; fg = "#e8e8fc"; border = "#45edf2"
        self.setStyleSheet(
            f"#notificationBanner {{ background-color:{bg}; border:1px solid {border}; border-radius:8px; }}"
            f"QLabel {{ color:{fg}; font-weight:bold; }}"
            "QPushButton { background: transparent; color: #e8e8fc; border: none; font-size: 16px; }"
            "QPushButton:hover { color: #45edf2; }"
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 8, 8, 8)
        lay.setSpacing(8)
        self._message_label.setWordWrap(True)
        self._message_label.setText(message)
        lay.addWidget(self._message_label)
        lay.addStretch()
        if self._close_btn:
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



class CollapsibleSection(QFrame):
    "Collapsible container with a disclosure arrow to hide or show content."

    def __init__(self, title: str, parent: QWidget | None = None, *, start_collapsed: bool = False, info_tooltip: str | None = None):
        super().__init__(parent)
        self.setObjectName('collapsibleSection')
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            QFrame#collapsibleSection {
                border: none;
            }
        """)

        self._toggle = QToolButton()
        self._toggle.setObjectName('collapsibleToggle')
        self._toggle.setCheckable(True)
        self._toggle.setChecked(not start_collapsed)
        self._toggle.setArrowType(Qt.ArrowType.DownArrow if not start_collapsed else Qt.ArrowType.RightArrow)
        self._toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self._toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle.setStyleSheet("QToolButton#collapsibleToggle { border: none; color: #e8e8fc; padding: 0 4px; } QToolButton#collapsibleToggle:hover { color: #45edf2; }")

        self._title = QLabel(title)
        self._title.setStyleSheet('color:#e8e8fc;font-weight:600;border:none;background:transparent;')

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)
        header_layout.addWidget(self._toggle)
        header_layout.addWidget(self._title)
        header_layout.addStretch()

        self._info_btn = None
        if info_tooltip:
            self._info_btn = QToolButton()
            self._info_btn.setText('i')
            self._info_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._info_btn.setToolTip(info_tooltip)
            self._info_btn.setAutoRaise(True)
            self._info_btn.setFixedSize(22, 22)
            self._info_btn.setStyleSheet(
                "QToolButton { background: rgba(69,237,242,0.1); color: #45edf2; border: 2px solid rgba(69,237,242,0.6); border-radius: 11px; font-weight: bold; }"
                "QToolButton:hover { background: rgba(69,237,242,0.3); border: 3px solid rgba(69,237,242,1.0); }"
            )
            self._info_btn.clicked.connect(lambda: QToolTip.showText(QCursor.pos(), info_tooltip, self._info_btn))
            header_layout.addWidget(self._info_btn)

        self._content_area = QFrame()
        self._content_area.setFrameShape(QFrame.Shape.NoFrame)
        self._content_layout = QVBoxLayout(self._content_area)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(12)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self._content_area)

        self._toggle.toggled.connect(self._on_toggled)
        self._on_toggled(not start_collapsed)

    def _on_toggled(self, checked: bool) -> None:
        self._content_area.setVisible(checked)
        self._toggle.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)

    def addWidget(self, widget: QWidget) -> None:
        self._content_layout.addWidget(widget)

    def addLayout(self, layout: QVBoxLayout | QHBoxLayout | QGridLayout) -> None:
        self._content_layout.addLayout(layout)

    def clear(self) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)


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
                border: 3px dashed #45edf2;
                border-radius: 15px;
                background-color: #0e1625;
                color: #e8e8fc;
                font-size: 16px;
            }
            QLabel:hover {
                border-color: #45edf2;
                background-color: rgba(69,237,242,0.1);
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
                background: rgba(69,237,242,0.1);
                color: #45edf2;
                border: 2px solid rgba(69,237,242,0.6);
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(69,237,242,0.3);
                border: 3px solid rgba(69,237,242,1.0);
            }
        """)
        self.remove_btn.clicked.connect(self.remove_media)
        self.remove_btn.hide()

        # Browse button
        self.browse_btn = QPushButton("Browse Files")
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background: rgba(69,237,242,0.1);
                color: #45edf2;
                border: 2px solid rgba(69,237,242,0.6);
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(69,237,242,0.3);
                border: 3px solid rgba(69,237,242,1.0);
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
            self.drop_zone.setText("Drop Media Here!")

    def dragLeaveEvent(self, event):
        """Handle drag leave event"""
        self.drop_zone.setStyleSheet("""
            QLabel {
                border: 3px dashed rgba(69,237,242,0.6);
                border-radius: 15px;
                background-color: #0e1625;
                color: #e8e8fc;
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
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 10px;
                background-color: #0e1625;
            }
        """)

        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)

        # Info label
        self.info_label = QLabel("Click on image to select starting pixel")
        self.info_label.setStyleSheet("""
            QLabel {
                color: #e8e8fc;
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
                background-color: #0e1625;
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
                background: rgba(14,22,37,0.8);
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
                color: #e8e8fc;
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
                background-color: #0e1625;
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
                background-color: rgba(69,237,242,0.1);
                color: #e8e8fc;
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
                background: rgba(69,237,242,0.1);
                color: #45edf2;
                border: 2px solid rgba(69,237,242,0.6);
                padding: 6px 10px;
                border-radius: 6px;
            }
            QPushButton:hover { background: rgba(69,237,242,0.3); border: 3px solid rgba(69,237,242,1.0); }
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
                background: rgba(14,22,37,0.8);
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
                background: rgba(69,237,242,0.1);
                color: #45edf2;
                border: 2px solid rgba(69,237,242,0.6);
                padding: 5px 10px;
                border-radius: 3px;
            }
        """)
        self.prev_frame_btn.clicked.connect(self.prev_frame)

        self.next_frame_btn = QPushButton("â–¶")
        self.next_frame_btn.setStyleSheet("""
            QPushButton {
                background: rgba(69,237,242,0.1);
                color: #45edf2;
                border: 2px solid rgba(69,237,242,0.6);
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
                color: #e8e8fc;
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
                border: 3px dashed #45edf2;
                border-radius: 15px;
                background-color: #0e1625;
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
            "Drag & Drop File Here\n\nSupported: .txt, .pdf, .exe, .wav, .mp3, .mov, .mp4")

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
        self.remove_btn = QPushButton("Remove File")
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background: rgba(69,237,242,0.1);
                color: #45edf2;
                border: 2px solid rgba(69,237,242,0.6);
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(69,237,242,0.3);
                border: 3px solid rgba(69,237,242,1.0);
            }
        """)
        self.remove_btn.clicked.connect(self.remove_file)
        self.remove_btn.hide()

        # Browse button
        self.browse_btn = QPushButton("Browse File")
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background: rgba(69,237,242,0.1);
                color: #45edf2;
                border: 2px solid rgba(69,237,242,0.6);
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(69,237,242,0.3);
                border: 3px solid rgba(69,237,242,1.0);
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
                border: 3px dashed #45edf2;
                border-radius: 15px;
                background-color: #0e1625;
                color: #e8e8fc;
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
        self.setObjectName('StegaEncodeWindow')
        self.setWindowTitle("Steganography - Hide Messages")
        
        # Setup responsive sizing to match main window
        self.setup_responsive_sizing()

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

        # Live preview machinery
        self._live_preview_timer = QTimer(self)
        self._live_preview_timer.setSingleShot(True)
        self._live_preview_timer.setInterval(200)
        self._live_preview_timer.timeout.connect(self._launch_live_preview_job)
        self._live_preview_poll_timer = QTimer(self)
        self._live_preview_poll_timer.setSingleShot(False)
        self._live_preview_poll_timer.setInterval(40)
        self._live_preview_poll_timer.timeout.connect(self._check_live_preview_future)
        self._live_preview_executor = ThreadPoolExecutor(max_workers=1)
        self._live_preview_future = None
        self._live_preview_dirty = False
        self._live_preview_buffer = None
        self._live_preview_image = None
        self._live_preview_qimage = None
        self._live_preview_expected_job = None
        self._live_preview_job_id = 0
        self._live_preview_cancelled_jobs = set()

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

        # Persistent notification area at the top
        self.notice_container = QVBoxLayout()
        self.notice_container.setSpacing(8)
        self.notice_container.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(self.notice_container)
        # Track overflow banner to avoid duplicates
        self._overflow_banner = None
        # Track guided tour banner for toggle functionality
        self._tour_banner = None
        self._tour_visible = False
        self._tour_button = None
        self.step_boxes = []
        self.helper_hint_label = None
        self.status_label = None
        self.current_step = 1
        self.step_hints = [
            "Step 1: Select a cover file.",
            "Step 2: Add a payload file or type a secret message.",
            "Step 3: Enter your numeric key and adjust embedding settings.",
            "Step 4: Adjust LSB bits and choose the start location.",
            "Step 5: Review the proof & diagnostics panel before sharing.",
        ]
        self._active_step_index = 0
        self.step_ready_flags = [False, False, False]

        # Quick-start guidance row
        self.create_quickstart_panel(main_layout)

        # Title section
        self.create_title_section(main_layout)

        # Main content area
        self.create_content_area(main_layout)

        # Set window size and position to match main window
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
        """Setup responsive sizing based on screen dimensions to match main window"""
        from PyQt6.QtWidgets import QApplication
        
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

    def create_quickstart_panel(self, layout):
        """Create the top quick-start guidance panel."""
        frame = QFrame()
        frame.setObjectName("quickStartFrame")
        frame.setStyleSheet("""
            QFrame#quickStartFrame {
                background-color: #0e1625;
                border-radius: 18px;
                border: 2px solid rgba(69,237,242,0.6);
                padding: 12px 18px;
            }
            QFrame[class="stepCard"] {
                background-color: #0e1625;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 15px;
            }
            QFrame[class="stepCard"][completed="true"] {
                border: 2px solid #22c55e;
                background-color: rgba(34,197,94,0.1);
            }
            QFrame[class="stepCard"][active="true"] {
                border: 2px solid #45edf2;
                background-color: rgba(69,237,242,0.1);
            }
            QLabel[class="stepNumber"] {
                color: #45edf2;
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QLabel[class="stepTitle"] {
                color: #e8e8fc;
                font-size: 15px;
                font-weight: 600;
            }
            QLabel[class="stepDetail"] {
                color: #e8e8fc;
                font-size: 12px;
            }
        """)

        wrapper_layout = QVBoxLayout(frame)
        wrapper_layout.setContentsMargins(4, 4, 4, 4)
        wrapper_layout.setSpacing(6)

        steps_layout = QHBoxLayout()
        steps_layout.setSpacing(6)

        steps = [
            ("Select Cover", "Drag & drop or browse for the image / audio / video cover.", "Pick the carrier file that will hide your payload."),
            ("Add Payload", "Type a secret message or attach any file to embed.", "You can embed text, documents, executables or other binaries."),
            ("Secure with Key", "Enter the numeric key and choose whether to encrypt.", "This key drives the PRNG, start offset and optional payload cipher."),
            ("Tune Settings", "Set LSB bits and choose the start location for embedding.", "Higher LSB count increases capacity; pick a start pixel/sample."),
            ("Review & Encode", "Check capacity + proof, then hide the payload.", "Use the proof & diagnostics panel to verify before sharing.")
        ]

        self.step_boxes = []
        for idx, (title, detail, tip) in enumerate(steps, start=1):
            card = QFrame()
            card.setProperty("class", "stepCard")
            card.setProperty("active", idx == 1)
            card.setProperty("completed", False)
            card.setToolTip(tip)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(6, 4, 6, 4)
            card_layout.setSpacing(1)

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

            steps_layout.addWidget(card)
            self.step_boxes.append(card)

        helper_layout = QHBoxLayout()
        helper_layout.setContentsMargins(4, 0, 4, 0)
        helper_layout.setSpacing(8)

        self.helper_hint_label = QLabel("Step 1: Start by selecting a cover file.")
        self.helper_hint_label.setStyleSheet("color:#e8e8fc;font-weight:600;")
        self.helper_hint_label.setWordWrap(True)

        tour_btn = QPushButton("Show Guided Tour")
        tour_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        tour_btn.setStyleSheet("""
            QPushButton {
                background: rgba(69,237,242,0.1);
                color: #45edf2;
                border: 2px solid rgba(69,237,242,0.6);
                padding: 6px 16px;
                border-radius: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(69,237,242,0.3);
                border: 3px solid rgba(69,237,242,1.0);
            }
        """)
        tour_btn.setToolTip("Walk through the encoding workflow and learn where each feature lives.")
        tour_btn.clicked.connect(self.show_onboarding_tour)
        self._tour_button = tour_btn

        helper_layout.addWidget(self.helper_hint_label)
        helper_layout.addStretch()
        helper_layout.addWidget(tour_btn)

        steps_container = QWidget()
        steps_container_layout = QVBoxLayout(steps_container)
        steps_container_layout.setContentsMargins(0, 0, 0, 0)
        steps_container_layout.setSpacing(8)
        steps_container_layout.addLayout(steps_layout)
        steps_container_layout.addLayout(helper_layout)

        steps_section = CollapsibleSection("Workflow overview", start_collapsed=True)
        steps_section.setStyleSheet("""
            QFrame#collapsibleSection {
                background: rgba(14,22,37,0.8);
                border: none;
                border-radius: 10px;
            }
        """)
        steps_section.addWidget(steps_container)

        wrapper_layout.addWidget(steps_section)

        layout.addWidget(frame)
        self.reset_workflow_steps()

    def reset_workflow_steps(self):
        """Reset workflow guidance to the first step."""
        self.update_helper_step(1, "Step 1: Start by selecting a cover file.")
        self.set_status('Waiting for cover selection.', 'info')
        self.step_ready_flags = [False, False, False]
        if hasattr(self, 'cover_info_label'):
            self.cover_info_label.setText('Drop a cover file to begin. Supported: PNG/BMP/GIF images, WAV audio, MOV/MP4 video.')
        self.update_step_progress()

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
        """Toggle guided tour banner with workflow tips."""
        if self._tour_visible and self._tour_banner is not None:
            # Hide the tour
            try:
                self._tour_banner._on_close()
            except Exception:
                pass
            self._tour_banner = None
            self._tour_visible = False
            if self._tour_button:
                self._tour_button.setText("Show Guided Tour")
            self.set_status("Guided tour hidden.", 'info')
        else:
            # Show the tour
            tour_text = (
                "1. Select your cover image/audio/video.\n"
                "2. Add a payload (type a message or attach a file).\n"
                "3. Enter a numeric key and pick encryption preferences.\n"
                "4. Adjust LSB bits and choose a start location.\n"
                "5. Press 'Hide Message' and review the proof & diagnostics panel."
            )
            banner = NotificationBanner(f"Guided tour\n{tour_text}", 'info', self, show_close_button=False)
            self.notice_container.addWidget(banner)
            banner.show()
            self._tour_banner = banner
            self._tour_visible = True
            if self._tour_button:
                self._tour_button.setText("Hide Guided Tour")
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
                background: rgba(69,237,242,0.1);
                color: #45edf2;
                border: 2px solid rgba(69,237,242,0.6);
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(69,237,242,0.3);
                border: 3px solid rgba(69,237,242,1.0);
            }
            """
        )
        return btn



    def create_title_section(self, layout):
        """Create the title and back button section"""
        title_layout = QHBoxLayout()

        # Back button
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

        # Title
        title_label = QLabel("Steganography - Hide Messages")
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
        """Create the main content area as a unified workflow."""
        content_scroll = QScrollArea()
        content_scroll.setWidgetResizable(True)
        content_scroll.setFrameShape(QFrame.Shape.NoFrame)
        content_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Make scroll area transparent to show page background
        content_scroll.setStyleSheet("QScrollArea { background-color: transparent; }")

        content_container = QWidget()
        # Make container transparent to show page background
        content_container.setStyleSheet("QWidget { background-color: transparent; }")
        columns_layout = QHBoxLayout(content_container)
        columns_layout.setContentsMargins(0, 0, 0, 0)
        columns_layout.setSpacing(16)

        panels = [
            self.create_cover_panel(),
            self.create_payload_panel(),
            self.create_controls_panel(),
        ]

        for panel in panels:
            panel.setMinimumWidth(280)
            columns_layout.addWidget(panel, stretch=1)

        content_scroll.setWidget(content_container)
        layout.addWidget(content_scroll)

    def create_cover_panel(self):
        """Create the cover item panel (left column)"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #0e1625;
                border-radius: 15px;
                border: 2px solid rgba(69,237,242,0.6);
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Panel header with title and info button
        header_layout = QHBoxLayout()

        # Panel title
        title = QLabel("Cover Item")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #e8e8fc; margin-bottom: 15px; border: none; background: transparent;")

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
        self.cover_info_label = QLabel('Drop a cover file to begin. Supported: PNG/BMP/GIF images, WAV audio, MOV/MP4 video.')
        self.cover_info_label.setStyleSheet('color:#e8e8fc;border:none;background:transparent;')
        self.cover_info_label.setWordWrap(True)
        layout.addWidget(self.cover_info_label)
        layout.addStretch()

        return panel

    def create_payload_panel(self):
        """Create the payload panel (middle column)"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #0e1625;
                border-radius: 15px;
                border: 2px solid rgba(69,237,242,0.6);
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Panel header with title and info button
        header_layout = QHBoxLayout()

        # Panel title
        title = QLabel("Payload")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #e8e8fc; margin-bottom: 15px; border: none; background: transparent;")

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
                border: 3px dashed #45edf2;
                border-radius: 15px;
                background-color: #0e1625;
                color: #e8e8fc;
                font-size: 14px;
                padding: 15px;
                font-family: 'Segoe UI', sans-serif;
            }
            QTextEdit:focus {
                border-color: #45edf2;
                background-color: rgba(69,237,242,0.1);
            }
            QTextEdit:hover {
                border-color: #45edf2;
                background-color: rgba(69,237,242,0.1);
            }
        """)
        self.message_text.textChanged.connect(self.on_payload_text_changed)

        # Or separator
        or_separator = QLabel("------- or -------")
        or_separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        or_separator.setStyleSheet("""
            QLabel {
                color: #e8e8fc;
                font-size: 14px;
                font-weight: bold;
                margin: 5px 0;
                border: none;
                background: transparent;
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
                background-color: #0e1625;
                border-radius: 15px;
                border: 2px solid rgba(69,237,242,0.6);
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Panel header with title and info button
        header_layout = QHBoxLayout()

        # Panel title
        title = QLabel("Controls")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #e8e8fc; margin-bottom: 15px; border: none; background: transparent;")

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
                background-color: #0e1625;
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
        self.lsb_slider.setToolTip('Step 4: Choose how many least-significant bits to use for embedding. Higher values increase capacity but change more data.')
        self.lsb_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.lsb_slider.setTickInterval(1)
        self.lsb_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bdc3c7;
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
            }
        """)
        self.lsb_slider.valueChanged.connect(self.update_lsb_value)
        self.lsb_slider.valueChanged.connect(self._schedule_live_preview)

        lsb_layout.addWidget(self.lsb_value_label)
        lsb_layout.addWidget(self.lsb_slider)

        # Key input
        key_group = QGroupBox("Key (numeric, required)")
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
            QCheckBox {
                color: #e8e8fc;
                font-weight: 500;
            }
            QComboBox {
                color: #e8e8fc;
                background-color: #0e1625;
                border: 1px solid #45edf2;
                border-radius: 6px;
                padding: 4px 6px;
            }
            QComboBox QAbstractItemView {
                background-color: #0e1625;
                color: #e8e8fc;
            }
        """)
        key_layout = QVBoxLayout(key_group)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Enter numeric key, e.g. 123456")
        self.key_input.setToolTip('Step 3: This numeric key is required for both encoding and decoding.')
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                border: 3px dashed rgba(69,237,242,0.6);
                border-radius: 15px;
                background-color: #0e1625;
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

        self.key_input.textChanged.connect(self._handle_key_changed)
        key_layout.addWidget(self.key_input)


        self.encrypt_checkbox = CustomCheckBox("Encrypt payload before embedding (recommended)")
        self.encrypt_checkbox.setToolTip('Use the numeric key to derive an XOR keystream before embedding the payload.')
        self.encrypt_checkbox.setChecked(True)
        self.encrypt_checkbox.toggled.connect(self.on_encrypt_toggle)
        key_layout.addWidget(self.encrypt_checkbox)

        self.honey_checkbox = CustomCheckBox("Honey Encryption (Demo)")
        self.honey_checkbox.setToolTip('Enable the Honey Encryption demo (text payloads only).')
        self.honey_checkbox.toggled.connect(self.on_honey_toggle)
        key_layout.addWidget(self.honey_checkbox)

        self.honey_universe_combo = QComboBox()
        self.honey_universe_combo.addItems(list_universes())
        default_universe = 'office_msgs'
        idx = self.honey_universe_combo.findText(default_universe)
        if idx >= 0:
            self.honey_universe_combo.setCurrentIndex(idx)
        self.honey_universe_combo.setEnabled(False)
        self.honey_universe_combo.setStyleSheet("color:#e8e8fc;background-color:#0e1625;border:1px solid #45edf2;border-radius:6px;padding:4px 6px;")
        self.honey_universe_combo.currentTextChanged.connect(self.on_honey_universe_changed)
        key_layout.addWidget(self.honey_universe_combo)

        self._sync_honey_availability()

        # Capacity group
        capacity_group = QGroupBox("Capacity")
        capacity_group.setStyleSheet("""
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
        cap_layout = QGridLayout(capacity_group)
        cap_layout.setHorizontalSpacing(12)
        cap_layout.setVerticalSpacing(6)
        capacity_fields = [
            ("Cover", "dims"),
            ("Payload", "payload"),
            ("LSB bits", "lsb"),
            ("Header bytes", "header"),
            ("Start bit offset", "startbits"),
            ("Capacity (bytes)", "max"),
            ("Available bytes", "avail"),
        ]
        self.cap_detail_labels = {}
        for row, (label, key) in enumerate(capacity_fields):
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet("color:#e8e8fc;font-weight:600;background:rgba(14,22,37,0.8);border:none;")
            value_lbl = QLabel("-")
            value_lbl.setStyleSheet("color:#e8e8fc;background:transparent;border:none;")
            value_lbl.setWordWrap(True)
            cap_layout.addWidget(lbl, row, 0)
            cap_layout.addWidget(value_lbl, row, 1)
            self.cap_detail_labels[key] = value_lbl
        
        # Store references for backward compatibility
        self.cap_dims = self.cap_detail_labels["dims"]
        self.cap_payload = self.cap_detail_labels["payload"]
        self.cap_lsb = self.cap_detail_labels["lsb"]
        self.cap_header = self.cap_detail_labels["header"]
        self.cap_startbits = self.cap_detail_labels["startbits"]
        self.cap_max = self.cap_detail_labels["max"]
        self.cap_avail = self.cap_detail_labels["avail"]
        # Capacity usage bar
        self.cap_usage_bar = QProgressBar()
        self.cap_usage_bar.setRange(0, 100)
        self.cap_usage_bar.setValue(0)
        self.cap_usage_bar.setTextVisible(True)
        self.cap_usage_bar.setFormat("Payload: %v / %m bytes")
        self.cap_usage_bar.setStyleSheet(
            "QProgressBar{border:1px solid #45edf2;border-radius:6px;background:#0e1625;text-align:center;color:#e8e8fc;}"
            "QProgressBar::chunk{background-color:#45edf2;border-radius:6px;}"
        )
        cap_layout.addWidget(self.cap_usage_bar, len(capacity_fields), 0, 1, 2)
        # Capacity status pill
        self.cap_status = QLabel("OK")
        self.cap_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cap_status.setStyleSheet(
            "QLabel{background:rgba(69,237,242,0.2);color:#45edf2;border-radius:10px;padding:4px 8px;font-weight:bold;}" 
        )
        cap_layout.addWidget(self.cap_status, len(capacity_fields) + 1, 0, 1, 2)
        capacity_group.setLayout(cap_layout)

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
                background-color: #0e1625;
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

        layout.addLayout(header_layout)
        layout.addWidget(lsb_group)
        layout.addWidget(key_group)
        layout.addWidget(output_group)
        layout.addWidget(capacity_group)
        # Proof panel (How embedded)
        proof_group = QGroupBox("How embedded")
        proof_group.setStyleSheet("""
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
        proof_layout = QGridLayout(proof_group)
        proof_layout.setHorizontalSpacing(12)
        proof_layout.setVerticalSpacing(6)
        proof_fields = [
            ("LSB bits", "lsb"),
            ("Start bit", "start"),
            ("Perm [0:8]", "perm"),
            ("Header", "header"),
            ("LSB stats", "stats"),
        ]
        self.proof_detail_labels = {}
        for row, (label, key) in enumerate(proof_fields):
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet("color:#e8e8fc;font-weight:600;")
            value_lbl = QLabel("-")
            value_lbl.setStyleSheet("color:#e8e8fc;")
            value_lbl.setWordWrap(True)
            proof_layout.addWidget(lbl, row, 0)
            proof_layout.addWidget(value_lbl, row, 1)
            self.proof_detail_labels[key] = value_lbl
        
        # Store references for backward compatibility
        self.proof_lsb = self.proof_detail_labels["lsb"]
        self.proof_start = self.proof_detail_labels["start"]
        self.proof_perm = self.proof_detail_labels["perm"]
        self.proof_header = self.proof_detail_labels["header"]
        self.proof_stats = self.proof_detail_labels["stats"]
        # Mini visualization for permutation (8-wide max)
        self.perm_vis = QLabel()
        self.perm_vis.setFixedHeight(20)
        self.perm_vis.setToolTip('Permutation visual: colours map the bit positions (0-7) in the embedding order.')
        self.perm_vis.setStyleSheet("QLabel{background:#0e1625;border:1px dashed #45edf2;border-radius:8px;}")
        proof_layout.addWidget(self.perm_vis, len(proof_fields), 0, 1, 2)

        legend = QLabel('Legend: coloured squares show the per-byte LSB permutation order; LSB stats compare the percentage of ones in cover vs stego for each bit.')
        legend.setStyleSheet('color:#e8e8fc;font-size:12px;')
        legend.setWordWrap(True)
        proof_layout.addWidget(legend, len(proof_fields) + 1, 0, 1, 2)

        # Header diagnostics panel
        header_group = QGroupBox("Header Details")
        header_group.setStyleSheet("""
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
        header_layout = QGridLayout(header_group)
        header_layout.setHorizontalSpacing(12)
        header_layout.setVerticalSpacing(6)
        header_fields = [
            ("Magic", "magic"),
            ("Version", "version"),
            ("Flags", "flags"),
            ("LSB bits", "lsb_bits"),
            ("Start offset", "start_offset"),
            ("Payload bytes", "payload_bytes"),
            ("Filename", "filename"),
            ("CRC32", "crc32"),
            ("Nonce length", "nonce_len"),
        ]
        self.header_detail_labels = {}
        for row, (label, key) in enumerate(header_fields):
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet("color:#e8e8fc;font-weight:600;")
            value_lbl = QLabel("-")
            value_lbl.setStyleSheet("color:#e8e8fc;")
            value_lbl.setWordWrap(True)
            header_layout.addWidget(lbl, row, 0, Qt.AlignmentFlag.AlignTop)
            header_layout.addWidget(value_lbl, row, 1)
            self.header_detail_labels[key] = value_lbl
        self.header_warning_label = QLabel("")
        self.header_warning_label.setStyleSheet("color:#45edf2;font-weight:bold;")
        self.header_warning_label.setWordWrap(True)
        self.header_warning_label.hide()
        header_layout.addWidget(self.header_warning_label, len(header_fields), 0, 1, 2)

        # Encryption diagnostics panel
        encryption_group = QGroupBox("Encryption Diagnostics")
        encryption_group.setStyleSheet("""
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
        encryption_layout = QGridLayout(encryption_group)
        encryption_layout.setHorizontalSpacing(12)
        encryption_layout.setVerticalSpacing(6)
        encryption_fields = [
            ("Encrypted", "status"),
            ("Nonce", "nonce"),
            ("CRC32 match", "crc"),
            ("Payload storage", "note"),
        ]
        self.enc_detail_labels = {}
        for row, (label, key) in enumerate(encryption_fields):
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet("color:#e8e8fc;font-weight:600;")
            value_lbl = QLabel("-")
            value_lbl.setStyleSheet("color:#e8e8fc;")
            value_lbl.setWordWrap(True)
            encryption_layout.addWidget(lbl, row, 0)
            encryption_layout.addWidget(value_lbl, row, 1)
            self.enc_detail_labels[key] = value_lbl

        # Post-encode capacity summary
        summary_group = QGroupBox("Post-Encode Capacity Summary")
        summary_group.setStyleSheet("""
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
        summary_layout = QVBoxLayout(summary_group)
        summary_grid = QGridLayout()
        summary_grid.setHorizontalSpacing(12)
        summary_grid.setVerticalSpacing(6)
        self.cap_summary_labels = {}
        summary_fields = [
            ("Total cover bits", "cover_bits"),
            ("Header bits", "header_bits"),
            ("Payload bits", "payload_bits"),
            ("Payload start", "payload_start"),
            ("Gap bits", "gap_bits"),
            ("Utilisation", "utilisation"),
        ]
        for row, (label, key) in enumerate(summary_fields):
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet("color:#e8e8fc;font-weight:600;")
            value_lbl = QLabel("-")
            value_lbl.setStyleSheet("color:#e8e8fc;")
            value_lbl.setWordWrap(True)
            summary_grid.addWidget(lbl, row, 0, Qt.AlignmentFlag.AlignTop)
            summary_grid.addWidget(value_lbl, row, 1)
            self.cap_summary_labels[key] = value_lbl
        summary_layout.addLayout(summary_grid)
        self.result_util_bar = QProgressBar()
        self.result_util_bar.setRange(0, 100)
        self.result_util_bar.setValue(0)
        self.result_util_bar.setFormat("No encode yet")
        self.result_util_bar.setStyleSheet(
            "QProgressBar{border:1px solid #45edf2;border-radius:6px;background:#0e1625;text-align:center;color:#e8e8fc;}"
            "QProgressBar::chunk{background-color:#45edf2;border-radius:6px;}"
        )
        summary_layout.addWidget(self.result_util_bar)

        diagnostics_section = CollapsibleSection(
            "Proof & diagnostics",
            start_collapsed=True,
            info_tooltip=(
                "After encoding, review this panel to confirm header metadata, encryption status, and capacity utilisation before sharing."
            ),
        )
        diagnostics_section.setStyleSheet("""
            QFrame#collapsibleSection {
                border: none !important;
                background: transparent !important;
                outline: none;
            }
            QFrame {
                border: none !important;
            }
        """)
        diagnostics_section.addWidget(proof_group)
        diagnostics_section.addWidget(header_group)
        diagnostics_section.addWidget(encryption_group)
        diagnostics_section.addWidget(summary_group)
        layout.addWidget(diagnostics_section)

        # Video start controls
        video_group = QGroupBox("Video Start")
        video_group.setStyleSheet("""
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
        video_vlayout = QVBoxLayout(video_group)
        self.video_frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.video_frame_slider.setMinimum(0)
        self.video_frame_slider.setMaximum(0)
        self.video_frame_slider.valueChanged.connect(self.on_video_frame_changed)
        self.video_pos_label = QLabel("Frame: 0, X: 0, Y: 0")
        video_vlayout.addWidget(self.video_frame_slider)
        video_vlayout.addWidget(self.video_pos_label)

        # Audio playback controls (enabled only for audio)
        audio_play_group = QGroupBox("Audio Playback")
        audio_play_group.setStyleSheet("""
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
        audio_play_layout = QHBoxLayout(audio_play_group)
        self.play_cover_btn = QPushButton("Play Cover")
        self.play_stego_btn = QPushButton("Play Stego")
        for btn in (self.play_cover_btn, self.play_stego_btn):
            btn.setEnabled(False)
            btn.setStyleSheet("QPushButton { background: rgba(69,237,242,0.1); color: #45edf2; border: 2px solid rgba(69,237,242,0.6); padding: 8px 12px; border-radius: 5px; }")
        self.play_cover_btn.clicked.connect(self.play_cover_audio)
        self.play_stego_btn.clicked.connect(self.play_stego_audio)
        audio_play_layout.addWidget(self.play_cover_btn)
        audio_play_layout.addWidget(self.play_stego_btn)

        tools_container = QWidget()
        tools_layout = QVBoxLayout(tools_container)
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.setSpacing(12)
        tools_layout.addWidget(video_group)
        tools_layout.addWidget(audio_play_group)

        tools_section = CollapsibleSection(
            "Media helpers",
            start_collapsed=True,
            info_tooltip=(
                "Use these helpers to scrub videos for start frames or audition audio covers before and after encoding."
            ),
        )
        tools_section.setStyleSheet("""
            QFrame#collapsibleSection {
                border: none !important;
                background: transparent !important;
                outline: none;
            }
            QFrame {
                border: none !important;
            }
        """)
        tools_section.addWidget(tools_container)
        layout.addWidget(tools_section)

        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(10)

        self.hide_button = QPushButton("Hide Message")
        self.hide_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hide_button.setMinimumHeight(52)
        self.hide_button.setStyleSheet(
            "QPushButton {"
            "    background: rgba(69,237,242,0.1);"
            "    color: #45edf2;"
            "    border: 2px solid rgba(69,237,242,0.6);"
            "    padding: 16px 32px;"
            "    border-radius: 10px;"
            "    font-size: 16px;"
            "    font-weight: bold;"
            "    min-width: 180px;"
            "}"
            "QPushButton:hover { background: rgba(69,237,242,0.3); border: 3px solid rgba(69,237,242,1.0); }"
            "QPushButton:pressed { background: rgba(69,237,242,0.3); }"
            "QPushButton:disabled {"
            "    background: rgba(128,128,128,0.1);"
            "    color: #808080;"
            "    border: 2px solid rgba(128,128,128,0.3);"
            "}"
        )
        self.hide_button.clicked.connect(self.hide_message)

        action_row.addStretch()
        action_row.addWidget(self.hide_button)
        action_row.addStretch()
        layout.addLayout(action_row)

        if not self.status_label:
            self.status_label = QLabel('Status: Waiting for inputs.')
            self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.status_label.setWordWrap(True)
            self.status_label.setStyleSheet("QLabel { color:#45edf2; background-color:rgba(69,237,242,0.1); border:1px solid #45edf2; border-radius:10px; padding:8px 16px; font-weight:600; }")
        layout.addWidget(self.status_label)
        self.set_status('Waiting for inputs.', 'info')
        layout.addStretch()

        self.reset_post_encode_panels()
        return panel

    def is_cover_ready(self) -> bool:
        return bool(getattr(getattr(self, 'media_drop_widget', None), 'media_path', None))

    def has_payload_input(self) -> bool:
        text_ready = bool(getattr(self, 'message_text', None) and self.message_text.toPlainText().strip())
        file_ready = bool(getattr(self.machine, 'payload_file_path', None))
        return text_ready or file_ready

    def is_key_ready(self) -> bool:
        return bool(getattr(self, 'key_input', None) and self.key_input.text().strip().isdigit())

    def update_step_progress(self) -> None:
        states = [
            self.is_cover_ready(),
            self.has_payload_input(),
            self.is_key_ready(),
        ]
        self.step_ready_flags = states
        if not self.step_boxes:
            return
        for idx, card in enumerate(self.step_boxes, start=1):
            completed = idx <= len(states) and states[idx - 1]
            card.setProperty('completed', completed)
            card.style().unpolish(card)
            card.style().polish(card)

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
                "QProgressBar{border:1px solid rgba(69,237,242,0.6);border-radius:6px;background:rgba(14,22,37,0.8);text-align:center;color:#e8e8fc;}"
                f"QProgressBar::chunk{{background-color:{chunk};border-radius:6px;}}"
            )
            self.cap_status.setStyleSheet(status_css)
            self.cap_status.setText(status_txt)
        except Exception:
            pass

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
        # Recompute capacity when LSB changes
        try:
            self.update_capacity_panel()
        except Exception:
            pass
        self._schedule_live_preview('lsb-slider')

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
        def _set_cover_info(message: str) -> None:
            if hasattr(self, 'cover_info_label') and self.cover_info_label:
                self.cover_info_label.setText(message)

        def _format_duration(seconds: float) -> str:
            try:
                seconds = float(seconds)
            except (TypeError, ValueError):
                return '?'
            if seconds < 0:
                seconds = 0.0
            minutes = int(seconds // 60)
            secs = int(round(seconds - minutes * 60))
            if secs == 60:
                minutes += 1
                secs = 0
            return f"{minutes:d}:{secs:02d}"

        if hasattr(self, 'reset_lsb_stats'):
            self.reset_lsb_stats()
        self.reset_post_encode_panels()
        if hasattr(self, '_clear_live_preview'):
            self._clear_live_preview()

        default_cover_message = 'Drop a cover file to begin. Supported: PNG/BMP/GIF images, WAV audio, MOV/MP4 video.'
        cover_message = None

        if not file_path:
            self.set_status('Cover cleared. Select a cover to begin.', 'info')
            self.reset_workflow_steps()
            self.media_type = None
            cover_message = default_cover_message
            self.update_step_progress()
            if cover_message:
                _set_cover_info(cover_message)
            return

        print(f"Media loaded: {file_path} ({media_type})")
        self.media_type = media_type
        self.start_xy = None
        self.start_sample = None
        self.update_helper_step(2, 'Step 2: Add a payload (type a message or attach a file).')
        self.set_status(f'Cover ready: {os.path.basename(file_path)}', 'success')

        if media_type == 'image':
            convert_path = None
            converted_note = None
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.jpg', '.jpeg']:
                from PyQt6.QtWidgets import QMessageBox
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Icon.Question)
                msg_box.setWindowTitle('Convert JPEG to PNG?')
                msg_box.setText('JPEG is lossy and will not preserve LSBs reliably. Convert to PNG for lossless embedding?')
                msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
                
                # Apply dark theme styling for better text visibility
                self._style_message_box(msg_box, 'info')
                
                resp = msg_box.exec()
                if resp == QMessageBox.StandardButton.Yes:
                    try:
                        img = Image.open(file_path)
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        base, _ = os.path.splitext(file_path)
                        convert_path = base + '_lossless.png'
                        img.save(convert_path, format='PNG')
                        file_path = convert_path
                        converted_note = 'Converted to lossless PNG for reliable embedding.'
                    except Exception as exc:
                        print(f"JPEG->PNG conversion failed: {exc}")
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
                    convert_path = base + '_frame0.png'
                    img.save(convert_path, format='PNG')
                    file_path = convert_path
                    converted_note = 'GIF frame 0 saved as PNG for embedding.'
                except Exception as exc:
                    print(f"GIF frame0 conversion failed: {exc}")

            if self.machine.set_cover_image(file_path):
                info = self.machine.get_image_info()
                print(f"[Image] Loaded: {os.path.basename(file_path)}")
                print(f"Size: {info.get('dimensions', 'Unknown')}")
                print(f"Capacity: {info.get('max_capacity_bytes', 0)} bytes")
                if self.media_drop_widget.preview_widget and hasattr(self.media_drop_widget.preview_widget, 'pixel_selected'):
                    try:
                        self.media_drop_widget.preview_widget.pixel_selected.connect(self.on_start_pixel_selected)
                    except Exception:
                        pass
                self.update_capacity_panel()

                details = []
                dims = info.get('dimensions')
                if isinstance(dims, tuple) and len(dims) == 3:
                    h, w, c = dims
                    details.append(f"{w}x{h}px")
                    details.append(f"{c} channel(s)")
                mode = info.get('mode')
                if mode:
                    details.append(f"mode {mode}")

                summary = f"Detected cover: Image - {os.path.basename(file_path)}"
                if details:
                    summary += " (" + ", ".join(details) + ")"
                summary += "."

                extras = []
                try:
                    size_text = _human_size(os.path.getsize(file_path))
                    extras.append(f"File size {size_text}.")
                except Exception:
                    pass
                capacity_bytes = info.get('max_capacity_bytes')
                if capacity_bytes:
                    try:
                        extras.append(f"Estimated capacity {_human_size(int(capacity_bytes))}.")
                    except Exception:
                        pass
                if converted_note:
                    extras.append(converted_note)

                cover_message = " ".join([summary] + extras) if extras else summary
            else:
                print('[Image] Error loading image')
                cover_message = 'Image cover could not be loaded. Try a different file.'
        elif media_type == 'audio':
            if self.machine.set_cover_audio(file_path):
                try:
                    self.audio_info = self.machine.get_audio_info(file_path)
                    print(f"[Audio] Loaded: {os.path.basename(file_path)} {self.audio_info}")
                except Exception as exc:
                    print(f"Error reading audio info: {exc}")
                    self.audio_info = None
                if self.media_drop_widget.preview_widget and hasattr(self.media_drop_widget.preview_widget, 'time_selected'):
                    try:
                        self.media_drop_widget.preview_widget.time_selected.connect(self.on_audio_time_selected)
                    except Exception:
                        pass
                if hasattr(self, 'play_cover_btn'):
                    self.play_cover_btn.setEnabled(True)
                self.update_capacity_panel()

                details = []
                if isinstance(self.audio_info, dict):
                    channels = self.audio_info.get('channels')
                    sample_rate = self.audio_info.get('sample_rate')
                    sampwidth_bits = self.audio_info.get('sampwidth_bits')
                    duration = self.audio_info.get('duration')
                    if channels and sample_rate:
                        details.append(f"{int(channels)} channel(s) @ {int(sample_rate)} Hz")
                    elif channels:
                        details.append(f"{int(channels)} channel(s)")
                    if sampwidth_bits:
                        details.append(f"{int(sampwidth_bits)}-bit samples")
                    if duration:
                        details.append(f"~{_format_duration(duration)}")

                summary = f"Detected cover: Audio - {os.path.basename(file_path)}"
                if details:
                    summary += " (" + ", ".join(details) + ")"
                summary += "."

                extras = []
                try:
                    size_text = _human_size(os.path.getsize(file_path))
                    extras.append(f"File size {size_text}.")
                except Exception:
                    pass

                cover_message = " ".join([summary] + extras) if extras else summary
            else:
                print('[Audio] Error loading audio')
                cover_message = 'Audio cover could not be loaded. Try a different file.'
        elif media_type == 'video':
            try:
                cap = cv2.VideoCapture(file_path)
                if not cap.isOpened():
                    raise RuntimeError('Cannot open video')
                frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS) or 24
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()
                self.video_meta = {'frames': frames, 'w': w, 'h': h, 'fps': float(fps)}
                self.cap_dims.setText(f"Video: {frames}f, {w}x{h}, {int(fps)}fps")
                if hasattr(self, 'video_frame_slider'):
                    self.video_frame_slider.setMaximum(max(0, frames - 1))
                    self.video_frame_slider.setValue(0)
                self.video_start = (0, 0, 0)
                if hasattr(self, 'video_pos_label'):
                    self.video_pos_label.setText('Frame: 0, X: 0, Y: 0')
                if self.media_drop_widget.preview_widget and hasattr(self.media_drop_widget.preview_widget, 'frame_selected'):
                    try:
                        self.media_drop_widget.preview_widget.frame_selected.connect(self.on_video_frame_changed)
                    except Exception:
                        pass
                if self.media_drop_widget.preview_widget and hasattr(self.media_drop_widget.preview_widget, 'xy_selected'):
                    try:
                        self.media_drop_widget.preview_widget.xy_selected.connect(self.on_video_xy_selected)
                    except Exception:
                        pass
                if hasattr(self, 'hide_button'):
                    self.hide_button.setEnabled(True)

                duration_text = _format_duration(frames / fps) if fps else '?'
                summary = f"Detected cover: Video - {os.path.basename(file_path)}"
                details = [f"{frames} frame(s)", f"{w}x{h}px"]
                if fps:
                    details.append(f"{fps:.1f} fps (~{duration_text})")
                if details:
                    summary += " (" + ", ".join(details) + ")"
                summary += "."

                extras = []
                try:
                    size_text = _human_size(os.path.getsize(file_path))
                    extras.append(f"File size {size_text}.")
                except Exception:
                    pass
                extras.append('Output will be saved as a lossless AVI for embedding.')

                cover_message = " ".join([summary] + extras)
            except Exception as exc:
                print(f"Video probe failed: {exc}")
                self.set_status('Could not read video metadata. Try a different file.', 'error')
                self.reset_workflow_steps()
                if hasattr(self, 'hide_button'):
                    self.hide_button.setEnabled(False)
                cover_message = 'Video metadata unavailable. Try a different file.'
            self.update_capacity_panel()
        else:
            cover_message = f"Detected cover: {media_type}. Ensure this cover type is supported."

        if cover_message:
            _set_cover_info(cover_message)
        self.update_step_progress()

    def on_honey_toggle(self, checked: bool):
        if not hasattr(self, 'honey_checkbox'):
            return
        checked = bool(checked)
        if checked and getattr(self.machine, 'payload_file_path', None):
            QToolTip.showText(QCursor.pos(), 'Honey mode supports short text payloads for demo.', self.honey_checkbox)
            self.honey_checkbox.blockSignals(True)
            self.honey_checkbox.setChecked(False)
            self.honey_checkbox.blockSignals(False)
            checked = False
        try:
            self.machine.set_honey_enabled(checked)
        except Exception as exc:
            print(f'Failed to toggle honey mode: {exc}')
            checked = False
            self.honey_checkbox.blockSignals(True)
            self.honey_checkbox.setChecked(False)
            self.honey_checkbox.blockSignals(False)
        if checked and hasattr(self, 'encrypt_checkbox'):
            self.encrypt_checkbox.blockSignals(True)
            self.encrypt_checkbox.setChecked(False)
            self.encrypt_checkbox.blockSignals(False)
            try:
                self.machine.set_encrypt_payload(False)
            except Exception as exc:
                print(f'Failed to disable encryption when enabling honey: {exc}')
        if hasattr(self, 'honey_universe_combo'):
            self.honey_universe_combo.setEnabled(checked and self.honey_checkbox.isEnabled())
            if checked:
                try:
                    self.machine.set_honey_universe(self.honey_universe_combo.currentText())
                except Exception as exc:
                    print(f'Failed to set honey universe: {exc}')
        self._sync_honey_availability()
        try:
            self.update_capacity_panel()
        except Exception:
            pass
        self._schedule_live_preview('honey-toggle')

    def on_honey_universe_changed(self, universe: str):
        try:
            self.machine.set_honey_universe(universe)
        except Exception as exc:
            print(f'Failed to set honey universe: {exc}')
        try:
            self.update_capacity_panel()
        except Exception:
            pass
        self._schedule_live_preview('honey-universe')

    def _sync_honey_availability(self):
        if not hasattr(self, 'honey_checkbox'):
            return
        text_only = not bool(getattr(self.machine, 'payload_file_path', None))
        tooltip = 'Honey mode supports short text payloads for demo.' if not text_only else 'Enable the Honey Encryption demo (text payloads only).'
        self.honey_checkbox.setToolTip(tooltip)
        self.honey_checkbox.setEnabled(text_only or self.honey_checkbox.isChecked())
        if not text_only and self.honey_checkbox.isChecked():
            self.honey_checkbox.blockSignals(True)
            self.honey_checkbox.setChecked(False)
            self.honey_checkbox.blockSignals(False)
            try:
                self.machine.set_honey_enabled(False)
            except Exception as exc:
                print(f'Failed to disable honey mode: {exc}')
        if hasattr(self, 'honey_universe_combo'):
            self.honey_universe_combo.setEnabled(text_only and self.honey_checkbox.isChecked())

    def on_payload_text_changed(self):
        text_value = self.message_text.toPlainText() if hasattr(self, 'message_text') else ''
        trimmed = text_value.strip()
        has_file_payload = bool(getattr(self.machine, 'payload_file_path', None))
        if trimmed and not has_file_payload:
            try:
                if self.machine.set_payload_text(text_value):
                    self.update_helper_step(3, "Step 3: Enter your numeric key to secure the payload.")
                    self.set_status('Payload text ready. Enter your numeric key next.', 'success')
                    self._sync_honey_availability()
                    try:
                        self.update_capacity_panel()
                    except Exception:
                        pass
                    self._schedule_live_preview('payload-text')
                else:
                    self._clear_live_preview()
            except Exception as exc:
                print(f"Failed to set payload text: {exc}")
                self._clear_live_preview()
        elif not trimmed and not has_file_payload:
            self.machine.payload_data = None
            self.update_helper_step(2, "Step 2: Add a payload file or type a message.")
            self.set_status('Add a payload file or type a secret message.', 'info')
            self._sync_honey_availability()
            try:
                self.update_capacity_panel()
            except Exception:
                pass
            self._clear_live_preview()
        self.update_step_progress()

    def _handle_key_changed(self, value: str):
        self.on_key_changed(value)

    def on_key_changed(self, value: str):
        trimmed = value.strip() if isinstance(value, str) else ''
        try:
            self.machine.set_encryption_key(value or '')
        except Exception as exc:
            print(f"Failed to set encryption key: {exc}")
        if trimmed.isdigit():
            self.update_helper_step(4, "Step 4: Adjust LSB bits and choose the start location.")
            self.set_status('Key ready. Adjust LSB bits and pick a start location.', 'success')
            self.show_step_hint('Tweak the embedding settings and mark a start location on the cover.')
            self._schedule_live_preview('key-change')
        else:
            if not trimmed:
                self.update_helper_step(3, "Step 3: Enter your numeric key to secure the payload.")
                self.set_status('Enter your numeric key to continue.', 'info')
            self._clear_live_preview()
        self.update_step_progress()

    def on_payload_file_loaded(self, file_path):
        """Handle payload file loaded from drag and drop or browse"""
        if hasattr(self, 'reset_lsb_stats'):
            self.reset_lsb_stats()
        if not file_path:
            print("Payload file removed")
            self.machine.payload_file_path = None
            self.machine.payload_data = None
            self._sync_honey_availability()
            if not (hasattr(self, 'message_text') and self.message_text.toPlainText().strip()):
                self.update_helper_step(2, 'Step 2: Add a payload file or type a message.')
            self.set_status('Payload removed. Add a new payload to continue.', 'info')
            try:
                self.update_capacity_panel()
            except Exception:
                pass
            self._clear_live_preview()
            self.update_step_progress()
            return

        print(f"Payload file loaded: {file_path}")

        if self.machine.set_payload_file(file_path):
            print(f"Payload file ready: {os.path.basename(file_path)}")
            self.update_helper_step(3, 'Step 3: Enter your numeric key to secure the payload.')
            self.set_status(f'Payload ready: {os.path.basename(file_path)}', 'success')
            self._sync_honey_availability()
            try:
                self.update_capacity_panel()
            except Exception:
                pass
            self._schedule_live_preview('payload-file')
        else:
            print("Error loading payload file")
            self.set_status('Could not load the selected payload.', 'error')
            self._clear_live_preview()

        self.update_step_progress()

    def browse_cover_image(self):
        """Browse for cover image (legacy method - now handled by media drop widget)"""
        # This method is now handled by the MediaDropWidget
        pass

    def _default_output_filename(self) -> str:
        """Return a media-aware default file name for the stego output."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.media_type == 'audio':
            return f"stego_output_{timestamp}.wav"
        if self.media_type == 'video':
            return f"stego_output_{timestamp}.avi"
        return f"stego_output_{timestamp}.png"

    def choose_output_path(self):
        """Choose output path"""
        if self.media_type == 'audio':
            title = "Save Steganographic Audio"
            filt = "WAV Files (*.wav);;All Files (*)"
            default_name = "stego_output.wav"
        elif self.media_type == 'video':
            title = "Save Steganographic Video"
            filt = "AVI Files (*.avi);;MP4 Files (*.mp4);;All Files (*)"
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

        if hasattr(self, 'honey_checkbox'):
            try:
                self.machine.set_honey_enabled(self.honey_checkbox.isChecked())
                if self.honey_checkbox.isChecked() and hasattr(self, 'honey_universe_combo'):
                    self.machine.set_honey_universe(self.honey_universe_combo.currentText())
            except Exception as exc:
                print(f"Failed to sync honey toggle: {exc}")

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
            default_path = self._default_output_filename()
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
                default_path = self._default_output_filename()
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
                default_path = self._default_output_filename()
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
            self.update_helper_step(5, "Step 5: Review the proof & diagnostics panel.")
            
            # Show success popup matching decoding style
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle('Encode Successful')
            out_path_display = self.machine.output_path or 'saved file'
            msg.setText(f"Message hidden successfully.\nSaved to: {out_path_display}")
            open_btn = msg.addButton('Open file', QMessageBox.ButtonRole.AcceptRole)
            msg.addButton('Close', QMessageBox.ButtonRole.RejectRole)
            
            # Apply dark theme styling for better text visibility
            self._style_message_box(msg, 'info')
            
            msg.exec()
            if msg.clickedButton() == open_btn and self.machine.output_path:
                from PyQt6.QtGui import QDesktopServices
                from PyQt6.QtCore import QUrl
                QDesktopServices.openUrl(QUrl.fromLocalFile(self.machine.output_path))
            info = getattr(self.machine, 'last_embed_info', None)
            if info:
                encrypted_flag = info.get('encrypted')
                self.proof_lsb.setText(f"{info.get('lsb_bits')} | encrypted: {'yes' if encrypted_flag else 'no'}")
                self.proof_start.setText(f"{info.get('start_bit')}")
                perm = info.get('perm', [])
                self.proof_perm.setText(f"{perm[:8]}")
                hdr = info.get('header', {}) or {}
                flags_val = hdr.get('flags', info.get('flags'))
                try:
                    flags_display = f"0x{int(flags_val) & 0xFF:02X}" if flags_val is not None else 'n/a'
                except Exception:
                    flags_display = str(flags_val)
                version = hdr.get('version', 'n/a')
                start_val = info.get('start_bit', hdr.get('start_bit_offset'))
                if start_val is None:
                    start_display = 'n/a'
                else:
                    try:
                        start_display = f"{int(start_val):,}"
                    except Exception:
                        start_display = str(start_val)
                payload_len_val = hdr.get('payload_len')
                if payload_len_val is None:
                    payload_display = 'n/a'
                else:
                    try:
                        payload_display = f"{int(payload_len_val):,}"
                    except Exception:
                        payload_display = str(payload_len_val)
                self.proof_header.setText(
                    f"Header summary: version={version} start_bit={start_display} payload_len={payload_display} bytes flags={flags_display}"
                )
                self.update_post_encode_panels(info)
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
                self.reset_post_encode_panels()
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
            if self.media_type == 'audio' and hasattr(self, 'play_stego_btn'):
                self.play_stego_btn.setEnabled(True)
            self.show_step_hint('Encoding complete. Review the proof & diagnostics panel or share the stego file.')
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
        self._schedule_live_preview('start-pixel')

    def on_encrypt_toggle(self, checked: bool):
        try:
            self.machine.set_encrypt_payload(bool(checked))
        except Exception as e:
            print(f"Failed to toggle encryption: {e}")

        if checked and hasattr(self, 'honey_checkbox'):
            if self.honey_checkbox.isChecked():
                self.honey_checkbox.blockSignals(True)
                self.honey_checkbox.setChecked(False)
                self.honey_checkbox.blockSignals(False)
                try:
                    self.machine.set_honey_enabled(False)
                except Exception as exc:
                    print(f"Failed to disable honey mode: {exc}")
            if hasattr(self, 'honey_universe_combo'):
                self.honey_universe_combo.setEnabled(False)
        self._sync_honey_availability()

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
        if hasattr(self, '_schedule_live_preview'):
            self._schedule_live_preview('encrypt-toggle')

    def _live_preview_prereqs_met(self) -> bool:
        if getattr(self, 'media_type', None) != 'image':
            return False
        drop_widget = getattr(self, 'media_drop_widget', None)
        cover_path = getattr(drop_widget, 'media_path', None) if drop_widget else None
        if not cover_path or not os.path.exists(cover_path):
            return False
        if self.start_xy is None:
            return False
        key_input = getattr(self, 'key_input', None)
        key_text = key_input.text().strip() if key_input else ''
        if not key_text.isdigit():
            return False
        payload = getattr(self.machine, 'payload_data', None)
        if payload is None:
            return False
        try:
            if len(payload) == 0:
                return False
        except TypeError:
            return False
        return True

    def _collect_live_preview_inputs(self) -> dict | None:
        if not self._live_preview_prereqs_met():
            return None
        drop_widget = getattr(self, 'media_drop_widget', None)
        cover_path = getattr(drop_widget, 'media_path', None) if drop_widget else None
        if not cover_path:
            return None
        payload = getattr(self.machine, 'payload_data', None)
        if payload is None:
            return None
        try:
            payload_bytes = bytes(payload)
        except Exception:
            try:
                payload_bytes = bytes(bytearray(payload))
            except Exception:
                return None
        payload_file_path = getattr(self.machine, 'payload_file_path', None)
        payload_filename = os.path.basename(payload_file_path) if payload_file_path else 'payload.txt'
        lsb_bits = max(1, int(self.lsb_slider.value())) if hasattr(self, 'lsb_slider') else 1
        key_text = self.key_input.text().strip() if hasattr(self, 'key_input') else ''
        return {
            'cover_path': cover_path,
            'start_xy': tuple(self.start_xy) if self.start_xy is not None else None,
            'lsb_bits': lsb_bits,
            'key': key_text,
            'payload_bytes': payload_bytes,
            'payload_file_path': payload_file_path,
            'payload_filename': payload_filename,
            'encrypt_payload': bool(getattr(self.machine, 'encrypt_payload', False)),
        }

    def _schedule_live_preview(self, reason=None):
        if isinstance(reason, (int, float)):
            reason = 'signal'
        if not self._live_preview_prereqs_met():
            if self._live_preview_image is not None:
                self._clear_live_preview()
            return
        self._live_preview_dirty = True
        if self._live_preview_future is not None and not self._live_preview_future.done():
            return
        if self._live_preview_timer.isActive():
            self._live_preview_timer.stop()
        self._live_preview_timer.start()

    def _launch_live_preview_job(self):
        if not self._live_preview_dirty:
            return
        if not self._live_preview_prereqs_met():
            if self._live_preview_image is not None:
                self._clear_live_preview()
            self._live_preview_dirty = False
            return
        if self._live_preview_future is not None and not self._live_preview_future.done():
            return
        params = self._collect_live_preview_inputs()
        if not params:
            self._clear_live_preview()
            self._live_preview_dirty = False
            return
        self._live_preview_timer.stop()
        self._live_preview_job_id += 1
        job_id = self._live_preview_job_id
        params['job_id'] = job_id
        self._live_preview_expected_job = job_id
        self._live_preview_dirty = False
        future = self._live_preview_executor.submit(StegaEncodeWindow._compute_live_preview_payload, params)
        self._live_preview_future = future
        if not self._live_preview_poll_timer.isActive():
            self._live_preview_poll_timer.start()

    def _check_live_preview_future(self):
        future = self._live_preview_future
        if future is None:
            if self._live_preview_poll_timer.isActive():
                self._live_preview_poll_timer.stop()
            return
        if not future.done():
            return
        if self._live_preview_poll_timer.isActive():
            self._live_preview_poll_timer.stop()
        self._live_preview_future = None
        try:
            result = future.result()
        except Exception as exc:
            print(f"Live preview worker failed: {exc}")
            self._clear_live_preview()
            return
        self._handle_live_preview_result(result)

    @staticmethod
    def _compute_live_preview_payload(params: dict) -> dict:
        result = {'job_id': params.get('job_id')}
        try:
            from machine.stega_encode_machine import StegaEncodeMachine
            clone = StegaEncodeMachine()
            clone.set_encrypt_payload(bool(params.get('encrypt_payload')))
            cover_path = params['cover_path']
            if not clone.set_cover_image(cover_path):
                raise ValueError('Failed to load cover image')
            lsb_bits = max(1, int(params.get('lsb_bits', 1)))
            clone.set_lsb_bits(lsb_bits)
            clone.set_encryption_key(params.get('key', '') or '')
            payload_bytes = params.get('payload_bytes', b'')
            if not payload_bytes:
                raise ValueError('No payload data available')
            clone.payload_data = payload_bytes
            clone.payload_file_path = params.get('payload_file_path')
            filename = params.get('payload_filename') or 'payload.txt'
            start_xy = params.get('start_xy')
            stego_img, _ = clone.encode_image(
                cover_path,
                payload_bytes,
                filename,
                lsb_bits,
                params.get('key', '') or '',
                start_xy=start_xy
            )
            cover_img = clone.cover_image.convert('RGB')
            stego_rgb = stego_img.convert('RGB')
            cover_arr = np.array(cover_img, dtype=np.uint8)
            stego_arr = np.array(stego_rgb, dtype=np.uint8)
            height, width, _ = cover_arr.shape
            change_counts = np.zeros((height, width), dtype=np.uint16)
            for bit in range(lsb_bits):
                cover_bit = (cover_arr >> bit) & 1
                stego_bit = (stego_arr >> bit) & 1
                diff = cover_bit != stego_bit
                change_counts += diff.sum(axis=2, dtype=np.uint16)
            max_change = int(change_counts.max())
            if max_change > 0:
                scaled = (change_counts.astype(np.float32) * (255.0 / max_change)).astype(np.uint8)
            else:
                scaled = np.zeros_like(change_counts, dtype=np.uint8)
            heatmap = np.zeros((height, width, 3), dtype=np.uint8)
            heatmap[..., 1] = scaled
            heatmap[..., 2] = np.where(change_counts > 0, 255, 0).astype(np.uint8)
            heat_bytes = heatmap.tobytes()
            stats_lines = []
            for bit in range(lsb_bits):
                mask = 1 << bit
                cover_ratio = float(((cover_arr & mask) != 0).mean() * 100.0)
                stego_ratio = float(((stego_arr & mask) != 0).mean() * 100.0)
                stats_lines.append(f"bit{bit}: cover {cover_ratio:.2f}% / stego {stego_ratio:.2f}% ones")
            result.update({
                'heatmap_bytes': heat_bytes,
                'width': width,
                'height': height,
                'stats_text': '\n'.join(stats_lines),
            })
        except Exception as exc:
            result['error'] = str(exc)
        return result

    def _handle_live_preview_result(self, result: dict | None):
        if not isinstance(result, dict):
            return
        job_id = result.get('job_id')
        if job_id in self._live_preview_cancelled_jobs:
            self._live_preview_cancelled_jobs.discard(job_id)
            return
        if self._live_preview_expected_job is not None and job_id != self._live_preview_expected_job:
            return
        self._live_preview_expected_job = None
        error = result.get('error')
        if error:
            print(f"Live preview error: {error}")
            self._clear_live_preview()
            return
        heat_bytes = result.get('heatmap_bytes')
        width = result.get('width')
        height = result.get('height')
        stats_text = result.get('stats_text')
        if heat_bytes and width and height:
            try:
                heat_image = Image.frombytes('RGB', (int(width), int(height)), heat_bytes)
            except Exception as exc:
                print(f"Failed to build heatmap image: {exc}")
                self._clear_live_preview()
            else:
                self._live_preview_buffer = heat_bytes
                self._live_preview_image = heat_image
                self._live_preview_qimage = ImageQt(heat_image)
                pixmap = QPixmap.fromImage(self._live_preview_qimage)
                preview_widget = getattr(self.media_drop_widget, 'preview_widget', None) if hasattr(self, 'media_drop_widget') else None
                pixmap_item = getattr(preview_widget, 'pixmap_item', None)
                if pixmap_item:
                    pixmap_item.setPixmap(pixmap)
                    try:
                        preview_widget.graphics_view.fitInView(pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
                    except Exception:
                        pass
        if stats_text and hasattr(self, 'proof_stats'):
            self.proof_stats.setText(stats_text)
        if self._live_preview_dirty and self._live_preview_prereqs_met():
            if self._live_preview_timer.isActive():
                self._live_preview_timer.stop()
            self._live_preview_timer.start()
        else:
            self._live_preview_dirty = False

    def _restore_cover_preview(self):
        if getattr(self, 'media_type', None) != 'image':
            return
        drop_widget = getattr(self, 'media_drop_widget', None)
        preview = getattr(drop_widget, 'preview_widget', None) if drop_widget else None
        pixmap_item = getattr(preview, 'pixmap_item', None)
        cover_path = getattr(drop_widget, 'media_path', None) if drop_widget else None
        if not pixmap_item or not cover_path or not os.path.exists(cover_path):
            return
        pm = QPixmap(cover_path)
        if pm.isNull():
            return
        pixmap_item.setPixmap(pm)
        try:
            preview.graphics_view.fitInView(pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        except Exception:
            pass

    def _clear_live_preview(self):
        try:
            if self._live_preview_timer.isActive():
                self._live_preview_timer.stop()
        except Exception:
            pass
        if self._live_preview_poll_timer.isActive():
            self._live_preview_poll_timer.stop()
        if self._live_preview_future is not None:
            self._live_preview_future = None
        if self._live_preview_expected_job is not None:
            self._live_preview_cancelled_jobs.add(self._live_preview_expected_job)
        self._live_preview_expected_job = None
        self._live_preview_dirty = False
        self._live_preview_buffer = None
        self._live_preview_image = None
        self._live_preview_qimage = None
        self._restore_cover_preview()
        if hasattr(self, 'reset_lsb_stats'):
            self.reset_lsb_stats()

    def current_payload_len(self) -> int:
        if hasattr(self.machine, 'get_effective_payload_length'):
            try:
                return int(self.machine.get_effective_payload_length())
            except Exception:
                pass
        if self.machine.payload_data:
            return len(self.machine.payload_data)
        txt = self.message_text.toPlainText().encode('utf-8') if self.message_text.toPlainText() else b""
        return len(txt)

    def _format_payload_summary(self, raw_len: int, effective_len: int) -> str:
        if raw_len <= 0 and effective_len <= 0:
            return '-'
        if getattr(self.machine, 'honey_enabled', False) and raw_len != effective_len:
            return f'Raw {raw_len} B -> Honey blob {effective_len} B'
        if raw_len != effective_len:
            return f'Raw {raw_len} B -> Effective {effective_len} B'
        return f'{effective_len} B'

    def update_capacity_panel(self):
        raw_payload = 0
        effective_payload = self.current_payload_len()
        if hasattr(self.machine, 'get_payload_lengths'):
            try:
                raw_payload, effective_payload = self.machine.get_payload_lengths()
            except Exception:
                raw_payload = effective_payload
        elif self.machine.payload_data:
            raw_payload = len(self.machine.payload_data)
        if hasattr(self, 'cap_payload'):
            try:
                self.cap_payload.setText(self._format_payload_summary(int(raw_payload), int(effective_payload)))
            except Exception:
                self.cap_payload.setText(self._format_payload_summary(0, int(effective_payload)))

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
                        self.cap_startbits.setText(f"{header_bits} (header reserved)")
                    else:
                        self.cap_startbits.setText(f"{start_bit}")
                self.cap_lsb.setText(f"{lsb}")
                self.cap_header.setText(f"{len(header_bytes)}")
                self.cap_max.setText(f"{max_bytes}")
                self.cap_avail.setText(f"{self.available_bytes}")
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
                        self.cap_avail.setStyleSheet("color:#e74c3c;background:transparent;border:none;")
                        self.cap_avail.setText(f"{self.available_bytes}  (Too large)")
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
                        self.cap_avail.setStyleSheet("color:#e8e8fc;background:transparent;border:none;")
                        self.cap_avail.setText(f"{self.available_bytes}")
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
        self.cap_lsb.setText(f"{self.lsb_slider.value()}")
        self.cap_header.setText("-")
        self.cap_max.setText("-")
        self.cap_avail.setText("-")
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
                    self.cap_startbits.setText(f"{header_bits} (header reserved)")
                else:
                    self.cap_startbits.setText(f"{start_bit_offset}")
                total_bits = self.machine.estimate_capacity_bits(self.media_drop_widget.media_path, 'audio', lsb, start_sample)
                max_bytes = total_bits // 8
                available_bits = max(0, total_bits - header_bits) if start_sample == 0 else max(0, total_bits)
                self.available_bytes = available_bits // 8
                self.cap_lsb.setText(f"{lsb}")
                self.cap_header.setText(f"{len(header_bytes)}")
                self.cap_max.setText(f"{max_bytes}")
                self.cap_avail.setText(f"{self.available_bytes}")
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
                        self.cap_avail.setStyleSheet("color:#e74c3c;background:transparent;border:none;")
                        self.cap_avail.setText(f"{self.available_bytes}  (Too large)")
                    except Exception:
                        pass
                    try:
                        self._set_overflow_banner(msg)
                    except Exception:
                        pass
                else:
                    try:
                        self.cap_avail.setToolTip("")
                        self.cap_avail.setStyleSheet("color:#e8e8fc;background:transparent;border:none;")
                        self.cap_avail.setText(f"{self.available_bytes}")
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
                self.cap_startbits.setText(f"{start_bit} (overlaps header)")
            else:
                self.cap_startbits.setText(f"{start_bit}")
        else:
            start_bit = header_bits
            self.cap_startbits.setText(f"{header_bits}")

        payload_start = max(start_bit, header_bits)
        usable_bits = max(0, total_bits - payload_start)
        max_bytes = usable_bits // 8
        self.available_bytes = max_bytes

        self.cap_dims.setText(f"Cover: {w}x{h}x{channels}")
        self.cap_lsb.setText(f"{lsb}")
        self.cap_header.setText(f"{len(header_bytes)}")
        self.cap_max.setText(f"{max_bytes}")
        self.cap_avail.setText(f"{self.available_bytes}")
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
                self.cap_avail.setStyleSheet("color:#e74c3c;background:transparent;border:none;")
                self.cap_avail.setText(f"{self.available_bytes}  (Too large)")
            except Exception:
                pass
            try:
                self._set_overflow_banner(msg)
            except Exception:
                pass
        else:
            try:
                self.cap_avail.setToolTip("")
                self.cap_avail.setStyleSheet("color:#e8e8fc;background:transparent;border:none;")
                self.cap_avail.setText(f"{self.available_bytes}")
            except Exception:
                pass
            try:
                self._set_overflow_banner(None)
            except Exception:
                pass


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

    def reset_lsb_stats(self, message: str = "-") -> None:
        if hasattr(self, 'proof_stats'):
            self.proof_stats.setText(message)

    def reset_post_encode_panels(self) -> None:
        if hasattr(self, '_clear_live_preview'):
            self._clear_live_preview()
        if hasattr(self, 'header_detail_labels'):
            for label in self.header_detail_labels.values():
                label.setText('-')
        if hasattr(self, 'header_warning_label'):
            self.header_warning_label.hide()
            self.header_warning_label.setText('')
        if hasattr(self, 'enc_detail_labels'):
            for label in self.enc_detail_labels.values():
                label.setText('-')
        if hasattr(self, 'cap_summary_labels'):
            for label in self.cap_summary_labels.values():
                label.setText('-')
        if hasattr(self, 'result_util_bar'):
            try:
                self.result_util_bar.setValue(0)
                self.result_util_bar.setFormat('No encode yet')
            except Exception:
                pass

    def update_post_encode_panels(self, info: dict) -> None:
        if not info:
            self.reset_post_encode_panels()
            return
        header = info.get('header') if isinstance(info, dict) else {}
        if not isinstance(header, dict):
            header = {}
        try:
            expected_magic = HEADER_MAGIC.decode('ascii')
        except Exception:
            expected_magic = str(HEADER_MAGIC)
        magic_value = header.get('magic')
        if isinstance(magic_value, (bytes, bytearray)):
            try:
                magic_value = magic_value.decode('ascii', errors='replace')
            except Exception:
                magic_value = magic_value.hex()
        magic_text = str(magic_value) if magic_value else expected_magic
        try:
            header_size_bytes = int(header.get('header_size', 0))
        except Exception:
            header_size_bytes = 0
        header_bits = max(0, header_size_bytes * 8)
        try:
            payload_bytes = int(header.get('payload_len', 0))
        except Exception:
            payload_bytes = 0
        payload_bits = max(0, payload_bytes * 8)
        try:
            lsb_bits = int(info.get('lsb_bits', header.get('lsb_bits', 1)))
            if lsb_bits <= 0:
                lsb_bits = 1
        except Exception:
            lsb_bits = 1
        try:
            start_bit = int(info.get('start_bit', header.get('start_bit_offset', 0)))
        except Exception:
            start_bit = 0
        total_bits = self._compute_total_bits_from_info(info, lsb_bits)
        gap_bits = max(0, start_bit - header_bits)
        utilised_bits = header_bits + payload_bits
        util_pct = (utilised_bits / total_bits * 100.0) if total_bits else 0.0

        if hasattr(self, 'header_detail_labels'):
            labels = self.header_detail_labels
            if 'magic' in labels:
                labels['magic'].setText(magic_text or '-')
            version = header.get('version')
            if 'version' in labels:
                labels['version'].setText(str(version) if version is not None else '-')
            flags_val = header.get('flags')
            if flags_val is None:
                flags_val = info.get('flags')
            if 'flags' in labels:
                if flags_val is None:
                    labels['flags'].setText('-')
                else:
                    try:
                        labels['flags'].setText(f"0x{int(flags_val) & 0xFF:02X}")
                    except Exception:
                        labels['flags'].setText(str(flags_val))
            if 'lsb_bits' in labels:
                labels['lsb_bits'].setText(str(header.get('lsb_bits', lsb_bits)))
            if 'start_offset' in labels:
                try:
                    start_display = int(header.get('start_bit_offset', start_bit))
                except Exception:
                    start_display = start_bit
                labels['start_offset'].setText(f"{start_display} bits")
            if 'payload_bytes' in labels:
                labels['payload_bytes'].setText(f"{payload_bytes} bytes")
            if 'filename' in labels:
                labels['filename'].setText(header.get('filename') or '-')
            crc_val = header.get('crc32')
            crc_display = '-'
            if crc_val is not None:
                try:
                    crc_display = f"0x{int(crc_val) & 0xFFFFFFFF:08X}"
                except Exception:
                    crc_display = str(crc_val)
            if 'crc32' in labels:
                labels['crc32'].setText(crc_display)
            nonce_bytes = header.get('nonce')
            nonce_len = len(nonce_bytes) if isinstance(nonce_bytes, (bytes, bytearray)) else 0
            if 'nonce_len' in labels:
                labels['nonce_len'].setText(str(nonce_len))
        warnings = []
        if not magic_value:
            if expected_magic:
                warnings.append(f"Magic missing; expected {expected_magic}")
        elif expected_magic and magic_text != expected_magic:
            warnings.append(f"Magic {magic_text} != expected {expected_magic}")
        version = header.get('version')
        if version is not None and version != HEADER_VERSION:
            warnings.append(f"Header version {version} != expected {HEADER_VERSION}")
        if header_bits == 0:
            warnings.append('Header length is zero; decoder cannot locate payload.')
        header_lsb = header.get('lsb_bits')
        if header_lsb is not None:
            try:
                if int(header_lsb) != int(lsb_bits):
                    warnings.append('Header LSB bits do not match encoder settings.')
            except Exception:
                pass
        header_flags = header.get('flags')
        info_flags = info.get('flags')
        if header_flags is not None and info_flags is not None:
            try:
                if int(header_flags) != int(info_flags):
                    warnings.append('Flags differ between header and session metadata.')
            except Exception:
                pass
        if hasattr(self, 'header_warning_label'):
            if warnings:
                self.header_warning_label.setText(' | '.join(warnings))
                self.header_warning_label.show()
            else:
                self.header_warning_label.hide()
                self.header_warning_label.setText('')

        if hasattr(self, 'enc_detail_labels'):
            labels = self.enc_detail_labels
            flags_val = header_flags if header_flags is not None else info_flags
            try:
                flags_text = f"0x{int(flags_val) & 0xFF:02X}" if flags_val is not None else 'n/a'
            except Exception:
                flags_text = str(flags_val)
            enc_enabled = bool(info.get('encrypted'))
            try:
                if flags_val is not None:
                    enc_enabled = bool(int(flags_val) & FLAG_PAYLOAD_ENCRYPTED)
            except Exception:
                pass
            status_text = f"{'yes' if enc_enabled else 'no'} (flags {flags_text})"
            if 'status' in labels:
                labels['status'].setText(status_text)
            nonce_bytes = header.get('nonce')
            if isinstance(nonce_bytes, (bytes, bytearray)):
                nonce_hex = nonce_bytes.hex()
            else:
                nonce_hex = info.get('nonce') if isinstance(info.get('nonce'), str) else ''
            if not nonce_hex:
                nonce_hex = 'none'
            if 'nonce' in labels:
                labels['nonce'].setText(f"{nonce_hex}")
            crc_val_info = info.get('crc32')
            match_text = '-'
            if header.get('crc32') is not None:
                try:
                    header_crc = int(header.get('crc32')) & 0xFFFFFFFF
                    info_crc = int(crc_val_info) & 0xFFFFFFFF if crc_val_info is not None else None
                    match_ok = info_crc is None or header_crc == info_crc
                    match_text = f"{'ok' if match_ok else 'mismatch'} (0x{header_crc:08X})"
                except Exception:
                    match_text = f"{header.get('crc32')}"
            if 'crc' in labels:
                labels['crc'].setText(match_text)
            if 'note' in labels:
                if enc_enabled:
                    labels['note'].setText('Payload stored as ciphertext; CRC tracked on plaintext bytes.')
                else:
                    labels['note'].setText('Payload stored as plaintext; CRC guards integrity.')

        if hasattr(self, 'cap_summary_labels'):
            labels = self.cap_summary_labels
            if 'cover_bits' in labels:
                if total_bits:
                    labels['cover_bits'].setText(f"{total_bits:,} bits ({total_bits / 8:.1f} bytes)")
                else:
                    labels['cover_bits'].setText('-')
            if 'header_bits' in labels:
                labels['header_bits'].setText(f"{header_bits:,} bits ({header_bits / 8:.1f} bytes)")
            if 'payload_bits' in labels:
                labels['payload_bits'].setText(f"{payload_bits:,} bits ({payload_bytes:,} bytes)")
            if 'payload_start' in labels:
                labels['payload_start'].setText(f"{start_bit:,} bits")
            if 'gap_bits' in labels:
                labels['gap_bits'].setText(f"{gap_bits:,} bits")
            if 'utilisation' in labels:
                if total_bits:
                    labels['utilisation'].setText(f"{utilised_bits:,} bits ({util_pct:.1f}% of capacity)")
                else:
                    labels['utilisation'].setText('Unknown (no capacity metadata)')
        if hasattr(self, 'result_util_bar'):
            try:
                if total_bits:
                    value = int(min(100, max(0, round(util_pct))))
                    self.result_util_bar.setValue(value)
                    self.result_util_bar.setFormat(f"{util_pct:.1f}% utilised")
                else:
                    self.result_util_bar.setValue(0)
                    self.result_util_bar.setFormat('No capacity metadata')
            except Exception:
                pass

    def _compute_total_bits_from_info(self, info: dict, lsb_bits: int) -> int:
        try:
            lsb_bits = max(1, int(lsb_bits))
        except Exception:
            lsb_bits = 1
        if not isinstance(info, dict):
            return 0
        image_shape = info.get('image_shape')
        if isinstance(image_shape, tuple) and len(image_shape) == 3:
            h, w, c = image_shape
            try:
                return int(h) * int(w) * int(c) * lsb_bits
            except Exception:
                return 0
        audio_info = info.get('audio_info') or {}
        if isinstance(audio_info, dict) and audio_info:
            frames = audio_info.get('frames', 0)
            channels = audio_info.get('channels', 1)
            sampwidth = audio_info.get('sampwidth_bytes', audio_info.get('sampwidth'))
            if sampwidth is None:
                bits = audio_info.get('sampwidth_bits')
                try:
                    sampwidth = max(1, int(bits) // 8)
                except Exception:
                    sampwidth = 1
            try:
                return int(frames) * max(1, int(channels)) * max(1, int(sampwidth)) * lsb_bits
            except Exception:
                return 0
        video_shape = info.get('video_shape')
        if isinstance(video_shape, tuple) and len(video_shape) == 4:
            frames, h, w, c = video_shape
            try:
                return int(frames) * int(h) * int(w) * int(c) * lsb_bits
            except Exception:
                return 0
        return 0

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

    def closeEvent(self, event):
        try:
            if self._live_preview_timer.isActive():
                self._live_preview_timer.stop()
        except Exception:
            pass
        try:
            if self._live_preview_poll_timer.isActive():
                self._live_preview_poll_timer.stop()
        except Exception:
            pass
        future = getattr(self, '_live_preview_future', None)
        if future is not None and not future.done():
            if self._live_preview_expected_job is not None:
                self._live_preview_cancelled_jobs.add(self._live_preview_expected_job)
            self._live_preview_expected_job = None
        executor = getattr(self, '_live_preview_executor', None)
        if executor is not None:
            try:
                executor.shutdown(wait=False, cancel_futures=True)
            except TypeError:
                executor.shutdown(wait=False)
            except Exception:
                pass
            self._live_preview_executor = None
        super().closeEvent(event)

    def go_back(self):
        """Go back to main window"""
        # Clean up machine resources
        self.machine.cleanup()

        from gui.main_window import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()





