# gui/image_steganalysis_window.py
import numpy as np
from PIL import Image
import io
import cv2
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFrame, QFileDialog, QTextEdit, QGroupBox, QGridLayout, 
                             QLineEdit, QComboBox, QProgressBar, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ImageSteganalysisWindow(QWidget):
    def __init__(self, machine):
        super().__init__()
        self.machine = machine
        self.main_gui = None  # Will be set by main window
        
    def set_main_gui(self, main_gui):
        """Set reference to main GUI for accessing widgets"""
        self.main_gui = main_gui
        self.method_descriptions = {
            "LSB Analysis": "Analyzes the least significant bits of each pixel to detect hidden data. LSB steganography is the most common method of hiding information in images.",
            "Chi-Square Test": "Performs statistical analysis on pixel value distributions to detect anomalies that may indicate steganographic content.",
            "RS Analysis": "Regular-Singular analysis examines how flipping LSBs affects image smoothness to detect LSB steganography with high accuracy.",
            "Sample Pairs Analysis": "Analyzes adjacent pixel pairs to detect statistical anomalies that may indicate hidden data in the image.",
            "DCT Analysis": "Discrete Cosine Transform analysis examines frequency domain characteristics to detect steganography in JPEG images.",
            "Wavelet Analysis": "Analyzes image using wavelet transforms to detect steganographic artifacts in different frequency bands.",
            "Histogram Analysis": "Examines pixel value histograms for unusual patterns that may indicate hidden information.",
            "Comprehensive Analysis": "Combines multiple basic detection methods for a thorough analysis of potential steganographic content.",
            "Advanced Comprehensive": "Uses all available detection methods with advanced algorithms for the most thorough steganalysis possible."
        }

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
            self.main_gui.image_preview.setPixmap(pixmap)
            self.main_gui.image_preview.setText("")
            
        except Exception as e:
            self.main_gui.image_preview.setText(f"Error loading preview: {str(e)}")

    def browse_image(self):
        """Browse for image to analyze"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_gui, "Select Image to Analyze", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        if file_path:
            self.main_gui.image_path.setText(file_path)
            # Load into machine
            if self.machine.set_image(file_path):
                # Create preview
                self.create_image_preview(file_path)
                if hasattr(self.main_gui, 'img_results_text'):
                    self.main_gui.img_results_text.append(f"Image selected: {file_path}")
            else:
                if hasattr(self.main_gui, 'img_results_text'):
                    self.main_gui.img_results_text.append(f"Error loading image: {file_path}")

    def on_image_method_changed(self):
        """Handle image method dropdown change"""
        method = self.main_gui.method_combo.currentText()
        self.update_method_description(method, self.main_gui.image_method_description)

    def update_method_description(self, method_name: str, description_widget: QLabel):
        """Update the method description based on selected method"""
        description = self.method_descriptions.get(method_name, "No description available for this method.")
        description_widget.setText(description)

    def analyze_image(self):
        """Analyze the selected image"""
        if not self.main_gui.image_path.text():
            self.main_gui.img_results_text.append("Error: Please select an image to analyze")
            return

        # Clear old outputs
        self.main_gui.img_results_text.clear()
        self.main_gui.img_stats_text.clear()

        # Show progress bar
        self.main_gui.img_progress_bar.setVisible(True)
        self.main_gui.img_progress_bar.setValue(0)
        self.main_gui.img_progress_bar.setFormat("Loading")
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        # Load image into the machine
        success = self.machine.set_image(self.main_gui.image_path.text())
        if not success:
            self.main_gui.img_results_text.append("Error: Failed to load image for analysis")
            self.main_gui.img_progress_bar.setVisible(False)
            return

        # Set selected analysis method
        method = self.main_gui.method_combo.currentText()
        self.machine.set_analysis_method(method)

        # Run analysis
        if self.machine.analyze_image():
            results = self.machine.get_results()
            stats = self.machine.get_statistics()
            confidence = self.machine.get_confidence_level()

            # === Results section ===
            self.main_gui.img_results_text.append("\n=== ANALYSIS COMPLETE ===")
            self.main_gui.img_results_text.append(f"Method: {results.get('method')}")
            self.main_gui.img_results_text.append(f"Suspicious: {results.get('suspicious')}")
            self.main_gui.img_results_text.append(f"Confidence level: {confidence:.2%}\n")

            # Helper function to pretty print nested dicts
            def print_dict(d: dict, indent: int = 0):
                for key, value in d.items():
                    if isinstance(value, dict):
                        self.main_gui.img_results_text.append(" " * indent + f"{key}:")
                        print_dict(value, indent + 4)
                    else:
                        self.main_gui.img_results_text.append(" " * indent + f"- {key}: {value}")

            # Print details (skip redundant top-level keys)
            for key, value in results.items():
                if key in ['method', 'suspicious']:
                    continue
                if isinstance(value, dict):
                    self.main_gui.img_results_text.append(f"{key}:")
                    print_dict(value, 4)
                else:
                    self.main_gui.img_results_text.append(f"{key}: {value}")

            # === Stats section ===
            self.main_gui.img_stats_text.append("Image Statistics:")
            for key, value in stats.items():
                self.main_gui.img_stats_text.append(f"- {key}: {value}")

            # === Charts ===
            try:
                self._plot_image_charts()
            except Exception as e:
                self.main_gui.img_results_text.append(f"Chart error: {e}")

        else:
            self.main_gui.img_results_text.append("Error: Analysis failed")

        # Hide progress bar
        self.main_gui.img_progress_bar.setVisible(False)

    def _plot_image_charts(self):
        """Render LSB Plane, Difference Map, and Histogram for the current image."""
        img = self.machine.image_array
        if img is None:
            return

        # Ensure RGB uint8
        if img.dtype != np.uint8:
            img = img.astype(np.uint8)

        # LSB Plane (combined across channels as mean of LSBs)
        ax_lsb = self.main_gui.img_canvas_lsb.figure.subplots(1, 1)
        self.main_gui.img_canvas_lsb.figure.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.05)
        ax_lsb.clear()
        lsb = (img & 1)
        if lsb.ndim == 3:
            lsb_vis = (np.mean(lsb, axis=2) * 255).astype(np.uint8)
        else:
            lsb_vis = (lsb * 255).astype(np.uint8)
        ax_lsb.imshow(lsb_vis, cmap='gray')
        ax_lsb.set_title('LSB Plane', fontsize=11)
        ax_lsb.axis('off')
        self.main_gui.img_canvas_lsb.draw()

        # Difference Map (residual to blurred image)
        ax_diff = self.main_gui.img_canvas_diff.figure.subplots(1, 1)
        self.main_gui.img_canvas_diff.figure.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.05)
        ax_diff.clear()
        blurred = cv2.GaussianBlur(img, (5, 5), 0)
        residual = cv2.absdiff(img, blurred)
        residual_gray = cv2.cvtColor(residual, cv2.COLOR_BGR2GRAY) if residual.ndim == 3 else residual
        ax_diff.imshow(residual_gray, cmap='inferno')
        ax_diff.set_title('Difference Map', fontsize=11)
        ax_diff.axis('off')
        self.main_gui.img_canvas_diff.draw()

        # Histogram (all channels)
        ax_hist = self.main_gui.img_canvas_hist.figure.subplots(1, 1)
        self.main_gui.img_canvas_hist.figure.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.1)
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
        self.main_gui.img_canvas_hist.draw()
