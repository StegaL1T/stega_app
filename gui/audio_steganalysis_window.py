# gui/audio_steganalysis_window.py
import numpy as np
import wave
import matplotlib.pyplot as plt
import io
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFrame, QFileDialog, QTextEdit, QGroupBox, QGridLayout, 
                             QLineEdit, QComboBox, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class AudioSteganalysisWindow(QWidget):
    def __init__(self, machine):
        super().__init__()
        self.machine = machine
        self.main_gui = None  # Will be set by main window
        
    def set_main_gui(self, main_gui):
        """Set reference to main GUI for accessing widgets"""
        self.main_gui = main_gui
        self.method_descriptions = {
            "Audio LSB Analysis": "Analyzes least significant bits in audio samples to detect hidden data embedded in audio files.",
            "Audio Chi-Square Test": "Statistical analysis of audio sample distributions to identify anomalies that may indicate steganographic content.",
            "Audio Spectral Analysis": "Examines frequency domain characteristics and power spectral density to detect audio steganography.",
            "Audio Autocorrelation Analysis": "Analyzes temporal patterns and periodic structures in audio to detect hidden information.",
            "Audio Entropy Analysis": "Measures randomness and information content in audio samples to identify steganographic artifacts.",
            "Audio Comprehensive Analysis": "Combines multiple audio detection methods for thorough analysis of potential hidden content.",
            "Audio Advanced Comprehensive": "Uses all available audio analysis techniques for the most comprehensive steganalysis possible."
        }

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
            buf = io.BytesIO()
            plt.savefig(buf, format="png")
            buf.seek(0)
            plt.close()

            pixmap = QPixmap()
            pixmap.loadFromData(buf.getvalue())

            # Set to QLabel
            self.main_gui.audio_preview.setPixmap(pixmap)
            self.main_gui.audio_preview.setText("")

        except Exception as e:
            self.main_gui.audio_preview.setText(f"Error loading audio preview: {str(e)}")

    def browse_audio(self):
        """Browse for audio to analyze"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_gui, "Select Audio to Analyze", "",
            "WAV Files (*.wav)"
        )
        if file_path:
            self.main_gui.audio_path.setText(file_path)
            if self.machine.set_audio(file_path):
                # Create preview
                self.create_audio_preview(file_path)
                if hasattr(self.main_gui, 'aud_results_text'):
                    self.main_gui.aud_results_text.append(f"Audio selected: {file_path}")
            else:
                if hasattr(self.main_gui, 'aud_results_text'):
                    self.main_gui.aud_results_text.append(f"Error loading audio: {file_path}")

    def on_audio_method_changed(self):
        """Handle audio method dropdown change"""
        method = self.main_gui.audio_method_combo.currentText()
        self.update_method_description(method, self.main_gui.audio_method_description)

    def update_method_description(self, method_name: str, description_widget: QLabel):
        """Update the method description based on selected method"""
        description = self.method_descriptions.get(method_name, "No description available for this method.")
        description_widget.setText(description)

    def analyze_audio(self):
        """Analyze the selected audio"""
        if not self.main_gui.audio_path.text():
            self.main_gui.aud_results_text.append(
                "Error: Please select an audio file to analyze")
            return

        # Clear old outputs
        self.main_gui.aud_results_text.clear()
        self.main_gui.aud_stats_text.clear()

        # Show progress bar
        self.main_gui.aud_progress_bar.setVisible(True)
        self.main_gui.aud_progress_bar.setValue(0)
        self.main_gui.aud_progress_bar.setFormat("Loading")
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        method = self.main_gui.audio_method_combo.currentText()
        
        # Set sensitivity level from GUI
        sensitivity_level = self.main_gui.get_sensitivity_level("audio")
        self.machine.set_sensitivity_level(sensitivity_level)
        
        ok = self.machine.analyze_audio(method)

        self.main_gui.aud_results_text.append("\n=== AUDIO ANALYSIS ===")
        if not ok:
            self.main_gui.aud_results_text.append("Error during audio analysis.")
            self.main_gui.aud_progress_bar.setVisible(False)
            return

        results = self.machine.get_results()
        confidence = self.machine.get_confidence_level()
        stats = self.machine.get_audio_statistics()

        self.main_gui.aud_results_text.append(f"Method: {results.get('method', method)}")
        self.main_gui.aud_results_text.append(f"Suspicious: {results.get('suspicious', False)}")
        for k, v in results.items():
            if k in ("method", "suspicious"):
                continue
            self.main_gui.aud_results_text.append(f"{k}: {v}")

        self.main_gui.aud_results_text.append(f"Confidence level: {confidence*100:.2f}%")

        self.main_gui.aud_stats_text.append("Audio Statistics:")
        for k, v in stats.items():
            self.main_gui.aud_stats_text.append(f"- {k}: {v}")

        # === Charts ===
        try:
            self._plot_audio_charts()
        except Exception as e:
            self.main_gui.aud_results_text.append(f"Audio chart error: {e}")

        # Hide progress bar
        self.main_gui.aud_progress_bar.setVisible(False)

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
        ax_wave = self.main_gui.aud_canvas_wave.figure.subplots(1, 1)
        self.main_gui.aud_canvas_wave.figure.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.1)
        ax_wave.clear()
        t = np.arange(len(data)) / float(sr)
        ax_wave.plot(t, data, color='#34495e', linewidth=0.8)
        ax_wave.set_title('Waveform')
        ax_wave.set_xlabel('Time (s)')
        ax_wave.set_ylabel('Amplitude')
        ax_wave.grid(True, alpha=0.2)
        self.main_gui.aud_canvas_wave.draw()

        # Spectrogram (log-magnitude)
        ax_spec = self.main_gui.aud_canvas_spec.figure.subplots(1, 1)
        self.main_gui.aud_canvas_spec.figure.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.1)
        ax_spec.clear()
        nfft = 1024
        noverlap = 512
        Pxx, freqs, bins, im = ax_spec.specgram(data, NFFT=nfft, Fs=sr, noverlap=noverlap, cmap='magma')
        ax_spec.set_title('Spectrogram')
        ax_spec.set_xlabel('Time (s)')
        ax_spec.set_ylabel('Frequency (Hz)')
        self.main_gui.aud_canvas_spec.draw()

        # Entropy over time (short-time 8-bit entropy)
        ax_ent = self.main_gui.aud_canvas_entropy.figure.subplots(1, 1)
        self.main_gui.aud_canvas_entropy.figure.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.1)
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
        self.main_gui.aud_canvas_entropy.draw()
