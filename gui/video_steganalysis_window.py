# gui/video_steganalysis_window.py
import numpy as np
import cv2
from PIL import Image
import io
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFrame, QFileDialog, QTextEdit, QGroupBox, QGridLayout, 
                             QLineEdit, QComboBox, QProgressBar, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class VideoSteganalysisWindow(QWidget):
    def __init__(self, machine):
        super().__init__()
        self.machine = machine
        self.main_gui = None  # Will be set by main window
        
    def set_main_gui(self, main_gui):
        """Set reference to main GUI for accessing widgets"""
        self.main_gui = main_gui
        self.method_descriptions = {
            "Video LSB Analysis": "Analyzes least significant bits in video frames to detect hidden data embedded in video files.",
            "Video Frame Analysis": "Examines individual video frames for anomalies and statistical irregularities that may indicate steganography.",
            "Video Motion Analysis": "Analyzes motion vectors and temporal patterns between frames to detect hidden information.",
            "Video Comprehensive Analysis": "Combines multiple video detection methods for thorough analysis of potential steganographic content.",
            "Video Advanced Comprehensive": "Uses all available video analysis techniques for the most comprehensive steganalysis possible."
        }

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
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            pixmap = QPixmap()
            pixmap.loadFromData(img_bytes.getvalue())

            # Set the preview
            self.main_gui.video_preview.setPixmap(pixmap)
            self.main_gui.video_preview.setText("")

        except Exception as e:
            self.main_gui.video_preview.setText(f"Error loading video preview: {str(e)}")

    def browse_video(self):
        """Browse for video to analyze"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_gui, "Select Video to Analyze", "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv)"
        )
        if file_path:
            self.main_gui.video_path.setText(file_path)
            if self.machine.set_video(file_path):
                # Create preview
                self.create_video_preview(file_path)
                if hasattr(self.main_gui, 'vid_results_text'):
                    self.main_gui.vid_results_text.append(f"Video selected: {file_path}")
            else:
                if hasattr(self.main_gui, 'vid_results_text'):
                    self.main_gui.vid_results_text.append(f"Error loading video: {file_path}")

    def on_video_method_changed(self):
        """Handle video method dropdown change"""
        method = self.main_gui.video_method_combo.currentText()
        self.update_method_description(method, self.main_gui.video_method_description)

    def update_method_description(self, method_name: str, description_widget: QLabel):
        """Update the method description based on selected method"""
        description = self.method_descriptions.get(method_name, "No description available for this method.")
        description_widget.setText(description)

    def analyze_video(self):
        """Analyze the selected video"""
        if not self.main_gui.video_path.text():
            self.main_gui.vid_results_text.append("Error: Please select a video file to analyze")
            return

        # Clear old outputs
        self.main_gui.vid_results_text.clear()
        self.main_gui.vid_stats_text.clear()

        # Show progress bar
        self.main_gui.vid_progress_bar.setVisible(True)
        self.main_gui.vid_progress_bar.setValue(0)
        self.main_gui.vid_progress_bar.setFormat("Loading")
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        # Load video into the machine
        success = self.machine.set_video(self.main_gui.video_path.text())
        if not success:
            self.main_gui.vid_results_text.append("Error: Failed to load video for analysis")
            self.main_gui.vid_progress_bar.setVisible(False)
            return

        # Set selected analysis method
        method = self.main_gui.video_method_combo.currentText()
        
        # Set sensitivity level from GUI
        sensitivity_level = self.main_gui.get_sensitivity_level("video")
        self.machine.set_sensitivity_level(sensitivity_level)
        
        # Run analysis
        if self.machine.analyze_video(method):
            results = self.machine.get_results()
            stats = self.machine.get_video_statistics()
            confidence = self.machine.get_confidence_level()

            # === Results section ===
            self.main_gui.vid_results_text.append("\n=== VIDEO ANALYSIS COMPLETE ===")
            self.main_gui.vid_results_text.append(f"Method: {results.get('method')}")
            self.main_gui.vid_results_text.append(f"Suspicious: {results.get('suspicious')}")
            self.main_gui.vid_results_text.append(f"Confidence level: {confidence:.2%}\n")

            # Helper function to pretty print nested dicts
            def print_dict(d: dict, indent: int = 0):
                for key, value in d.items():
                    if isinstance(value, dict):
                        self.main_gui.vid_results_text.append(" " * indent + f"{key}:")
                        print_dict(value, indent + 4)
                    else:
                        self.main_gui.vid_results_text.append(" " * indent + f"- {key}: {value}")

            # Print details (skip redundant top-level keys)
            for key, value in results.items():
                if key in ['method', 'suspicious']:
                    continue
                if isinstance(value, dict):
                    self.main_gui.vid_results_text.append(f"{key}:")
                    print_dict(value, 4)
                else:
                    self.main_gui.vid_results_text.append(f"{key}: {value}")

            # === Stats section ===
            self.main_gui.vid_stats_text.append("Video Statistics:")
            for key, value in stats.items():
                self.main_gui.vid_stats_text.append(f"- {key}: {value}")

            # === Charts ===
            try:
                self._plot_video_charts()
            except Exception as e:
                self.main_gui.vid_results_text.append(f"Chart error: {e}")

        else:
            self.main_gui.vid_results_text.append("Error: Analysis failed")

        # Hide progress bar
        self.main_gui.vid_progress_bar.setVisible(False)

    def _plot_video_charts(self):
        """Render Frame Analysis, Motion Analysis, and LSB Analysis for the current video."""
        frames = self.machine.video_frames
        if frames is None or len(frames) == 0:
            return

        # Sample frames for analysis (max 20 frames)
        sample_frames = frames[::max(1, len(frames)//20)]
        
        # Frame Analysis Chart
        ax_frame = self.main_gui.vid_canvas_frame.figure.subplots(1, 1)
        self.main_gui.vid_canvas_frame.figure.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.1)
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
        self.main_gui.vid_canvas_frame.draw()

        # Motion Analysis Chart
        ax_motion = self.main_gui.vid_canvas_motion.figure.subplots(1, 1)
        self.main_gui.vid_canvas_motion.figure.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.1)
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
        self.main_gui.vid_canvas_motion.draw()

        # LSB Analysis Chart
        ax_lsb = self.main_gui.vid_canvas_lsb.figure.subplots(1, 1)
        self.main_gui.vid_canvas_lsb.figure.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.1)
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
        self.main_gui.vid_canvas_lsb.draw()
