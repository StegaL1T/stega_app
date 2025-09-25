# machine/audio_steganalysis_machine.py
import os
import time
from typing import Optional, Dict, List, Tuple
import numpy as np
import wave
import contextlib
import scipy.fft
from scipy import stats
from scipy.signal import welch
import math


class AudioSteganalysisMachine:
    """
    Handles audio steganalysis operations and business logic.
    Specialized for audio-based steganographic detection.
    """

    def __init__(self):
        """Initialize the audio steganalysis machine"""
        # Audio related state
        self.audio_path: Optional[str] = None
        self.audio_sample_rate: Optional[int] = None
        self.audio_num_channels: Optional[int] = None
        self.audio_sample_width: Optional[int] = None  # bytes per sample
        self.audio_num_frames: Optional[int] = None
        self.audio_samples: Optional[np.ndarray] = None  # int16/int8 numpy array, shape (n,) or (n, channels)

        # Analysis results
        self.results: Dict = {}
        self.statistics: Dict = {}
        self.confidence_level: float = 0.0

        print("AudioSteganalysisMachine initialized")

    def set_audio(self, audio_path: str) -> bool:
        """
        Set the audio file (WAV PCM) to analyze.

        Args:
            audio_path: Path to the audio file (.wav)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(audio_path):
                print(f"Error: Audio not found: {audio_path}")
                return False

            # Only support uncompressed PCM WAV using stdlib
            if not audio_path.lower().endswith('.wav'):
                print("Error: Only .wav PCM files are supported for audio steganalysis")
                return False

            with contextlib.closing(wave.open(audio_path, 'rb')) as wf:
                self.audio_num_channels = wf.getnchannels()
                self.audio_sample_width = wf.getsampwidth()  # bytes
                self.audio_sample_rate = wf.getframerate()
                self.audio_num_frames = wf.getnframes()
                frames = wf.readframes(self.audio_num_frames)

            # Convert bytes to numpy array depending on sample width
            if self.audio_sample_width == 1:
                # 8-bit PCM is unsigned in WAV; convert to int16 centered
                raw = np.frombuffer(frames, dtype=np.uint8)
                raw = raw.astype(np.int16) - 128
            elif self.audio_sample_width == 2:
                raw = np.frombuffer(frames, dtype=np.int16)
            else:
                print(f"Error: Unsupported sample width: {self.audio_sample_width} bytes")
                return False

            # Reshape for channels
            if self.audio_num_channels and self.audio_num_channels > 1:
                raw = raw.reshape(-1, self.audio_num_channels)

            self.audio_samples = raw
            self.audio_path = audio_path

            print(f"Audio loaded for analysis: {audio_path}")
            print(f"Sample rate: {self.audio_sample_rate} Hz, Channels: {self.audio_num_channels}, Sample width: {self.audio_sample_width} bytes, Frames: {self.audio_num_frames}")

            return True

        except wave.Error as e:
            print(f"Error reading WAV: {e}")
            return False
        except Exception as e:
            print(f"Error loading audio: {e}")
            return False

    def validate_audio_inputs(self) -> Tuple[bool, str]:
        """
        Validate audio inputs before analysis

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not self.audio_path:
            return False, "No audio selected for analysis"

        if self.audio_samples is None:
            return False, "Audio not loaded properly"

        return True, "Inputs valid"

    def analyze_audio(self, method: str = "Audio LSB Analysis") -> bool:
        """
        Perform steganalysis on the audio

        Args:
            method: Analysis method name for audio

        Returns:
            bool: True if successful, False otherwise
        """
        is_valid, error_msg = self.validate_audio_inputs()
        if not is_valid:
            print(f"Validation failed: {error_msg}")
            return False

        try:
            overall_start_time = time.time()
            print(f"Starting {method}...")

            # Clear previous results
            self.results = {}
            self.statistics = {}

            # Perform analysis based on selected method
            if method == "Audio LSB Analysis":
                self._perform_audio_lsb_analysis()
            elif method == "Audio Chi-Square Test":
                self._perform_audio_chi_square_test()
            elif method == "Audio Comprehensive Analysis":
                self._perform_audio_comprehensive_analysis()
            elif method == "Audio Spectral Analysis":
                self._perform_audio_spectral_analysis()
            elif method == "Audio Autocorrelation Analysis":
                self._perform_audio_autocorrelation_analysis()
            elif method == "Audio Entropy Analysis":
                self._perform_audio_entropy_analysis()
            elif method == "Audio Advanced Comprehensive":
                self._perform_audio_advanced_comprehensive_analysis()
            else:
                print(f"Unknown audio analysis method: {method}")
                return False

            # Calculate overall confidence
            self._calculate_confidence()

            overall_end_time = time.time()
            overall_execution_time = overall_end_time - overall_start_time
            print(f"Audio Analysis completed successfully in {overall_execution_time*1000:.2f}ms total!")
            return True

        except Exception as e:
            print(f"Error during audio analysis: {e}")
            return False

    def _perform_audio_lsb_analysis(self):
        """Perform LSB analysis on audio samples"""
        start_time = time.time()
        print("Performing Audio LSB analysis...")

        samples = self.audio_samples
        if samples.ndim == 2:
            # For stereo, analyze each channel and overall
            channel_lsbs = []
            for ch in range(samples.shape[1]):
                ch_data = samples[:, ch]
                lsb_ratio = np.mean((ch_data & 1) != 0)
                channel_lsbs.append(float(lsb_ratio))
            avg_lsb = float(np.mean(channel_lsbs))
            # More conservative threshold for audio LSB analysis
            channel_deviations = [abs(ratio - 0.5) for ratio in channel_lsbs]
            max_deviation = max(channel_deviations)
            avg_deviation = np.mean(channel_deviations)
            
            # Suspicious if: high average deviation OR multiple channels show significant deviation
            suspicious = (abs(avg_lsb - 0.5) > 0.15) or (max_deviation > 0.2 and avg_deviation > 0.1)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            self.results = {
                'method': 'Audio LSB Analysis',
                'channel_lsb_ratios': channel_lsbs,
                'avg_lsb_ratio': avg_lsb,
                'max_deviation': max_deviation,
                'avg_deviation': avg_deviation,
                'suspicious': suspicious,
                'execution_time_ms': round(execution_time * 1000, 2)
            }
            
            print(f"Audio LSB Analysis completed in {execution_time*1000:.2f}ms")
        else:
            lsb_ratio = float(np.mean((samples & 1) != 0))
            deviation = abs(lsb_ratio - 0.5)
            # More conservative threshold for mono audio
            suspicious = deviation > 0.15
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            self.results = {
                'method': 'Audio LSB Analysis',
                'lsb_ratio': lsb_ratio,
                'deviation': deviation,
                'suspicious': suspicious,
                'execution_time_ms': round(execution_time * 1000, 2)
            }
            
            print(f"Audio LSB Analysis completed in {execution_time*1000:.2f}ms")

    def _perform_audio_chi_square_test(self):
        """Perform Chi-Square test on audio sample histogram (simplified)"""
        print("Performing Audio Chi-Square test...")

        samples = self.audio_samples
        def chi2_for(data: np.ndarray) -> float:
            # Normalize to 16-bit signed range if needed
            if data.dtype != np.int16:
                data = data.astype(np.int16)
            # Shift to non-negative index range [0, 65535]
            shifted = (data.astype(np.int32) + 32768)
            # Use histogram with 256 bins over full range to keep it light
            hist, _ = np.histogram(shifted, bins=256, range=(0, 65536))
            expected = np.mean(hist)
            expected = expected if expected > 0 else 1.0
            chi2 = np.sum((hist - expected) ** 2 / expected)
            return float(chi2) / 1000.0

        if samples.ndim == 2:
            ch_chi2 = []
            for ch in range(samples.shape[1]):
                ch_chi2.append(float(chi2_for(samples[:, ch])))
            avg = float(np.mean(ch_chi2))
            self.results = {
                'method': 'Audio Chi-Square Test',
                'channel_chi2': ch_chi2,
                'avg_chi2': avg,
                'suspicious': avg > 0.5
            }
        else:
            chi2 = chi2_for(samples)
            self.results = {
                'method': 'Audio Chi-Square Test',
                'chi2': chi2,
                'suspicious': chi2 > 0.5
            }

    def _perform_audio_comprehensive_analysis(self):
        """Perform comprehensive analysis on audio using multiple methods"""
        start_time = time.time()
        print("Performing audio comprehensive analysis...")

        self._perform_audio_lsb_analysis()
        lsb_results = self.results.copy()

        self._perform_audio_chi_square_test()
        chi2_results = self.results.copy()

        end_time = time.time()
        execution_time = end_time - start_time
        
        self.results = {
            'method': 'Audio Comprehensive Analysis',
            'audio_lsb_analysis': lsb_results,
            'audio_chi_square_test': chi2_results,
            'suspicious': lsb_results.get('suspicious', False) or chi2_results.get('suspicious', False),
            'execution_time_ms': round(execution_time * 1000, 2)
        }
        
        print(f"Audio Comprehensive Analysis completed in {execution_time*1000:.2f}ms")

    def _perform_audio_spectral_analysis(self):
        """Perform spectral analysis on audio"""
        print("Performing Audio Spectral analysis...")
        
        samples = self.audio_samples
        if samples.ndim == 2:
            # Use first channel for analysis
            samples = samples[:, 0]
        
        # Compute power spectral density
        freqs, psd = welch(samples, fs=self.audio_sample_rate, nperseg=1024)
        
        # Analyze spectral characteristics
        # High-frequency energy ratio
        hf_freqs = freqs > (self.audio_sample_rate / 4)  # Above quarter sampling rate
        hf_energy = np.sum(psd[hf_freqs])
        total_energy = np.sum(psd)
        hf_ratio = hf_energy / (total_energy + 1e-10)
        
        # Spectral flatness (measure of noise-like vs tonal content)
        geometric_mean = np.exp(np.mean(np.log(psd + 1e-10)))
        arithmetic_mean = np.mean(psd)
        spectral_flatness = geometric_mean / (arithmetic_mean + 1e-10)
        
        # More conservative thresholds for spectral analysis
        # Consider both high-frequency content and spectral characteristics
        suspicious = (hf_ratio > 0.4) or (spectral_flatness < 0.05) or (hf_ratio > 0.25 and spectral_flatness < 0.15)
        
        self.results = {
            'method': 'Audio Spectral Analysis',
            'hf_energy_ratio': float(hf_ratio),
            'spectral_flatness': float(spectral_flatness),
            'total_energy': float(total_energy),
            'suspicious': suspicious
        }

    def _perform_audio_autocorrelation_analysis(self):
        """Perform autocorrelation analysis on audio"""
        print("Performing Audio Autocorrelation analysis...")
        
        samples = self.audio_samples
        if samples.ndim == 2:
            samples = samples[:, 0]
        
        # Compute autocorrelation
        autocorr = np.correlate(samples, samples, mode='full')
        autocorr = autocorr[autocorr.size // 2:]
        
        # Normalize
        autocorr = autocorr / autocorr[0]
        
        # Find peaks in autocorrelation (periodic patterns)
        # Look for significant peaks beyond lag 0
        peaks = []
        for i in range(1, min(len(autocorr), 1000)):  # Check first 1000 lags
            if (autocorr[i] > autocorr[i-1] and 
                autocorr[i] > autocorr[i+1] and 
                autocorr[i] > 0.1):  # Significant peak threshold
                peaks.append((i, autocorr[i]))
        
        # Analyze peak distribution
        num_significant_peaks = len(peaks)
        avg_peak_strength = np.mean([p[1] for p in peaks]) if peaks else 0
        
        # Check for unusual periodic patterns
        suspicious = num_significant_peaks > 10 or avg_peak_strength > 0.5
        
        self.results = {
            'method': 'Audio Autocorrelation Analysis',
            'num_significant_peaks': num_significant_peaks,
            'avg_peak_strength': float(avg_peak_strength),
            'max_autocorr_lag1': float(autocorr[1]) if len(autocorr) > 1 else 0,
            'suspicious': suspicious
        }

    def _perform_audio_entropy_analysis(self):
        """Perform entropy analysis on audio"""
        print("Performing Audio Entropy analysis...")
        
        samples = self.audio_samples
        if samples.ndim == 2:
            samples = samples[:, 0]
        
        # Convert to 8-bit for entropy calculation
        samples_8bit = ((samples - samples.min()) / (samples.max() - samples.min() + 1e-10) * 255).astype(np.uint8)
        
        # Calculate histogram
        hist, _ = np.histogram(samples_8bit, bins=256, range=(0, 256))
        
        # Calculate entropy
        hist = hist / np.sum(hist)  # Normalize to probabilities
        hist = hist[hist > 0]  # Remove zero probabilities
        entropy = -np.sum(hist * np.log2(hist))
        
        # Calculate maximum possible entropy (uniform distribution)
        max_entropy = np.log2(256)
        entropy_ratio = entropy / max_entropy
        
        # More conservative entropy analysis
        # Very low entropy (highly structured) or very high entropy (random-like) can indicate steganography
        # But need to be more conservative to avoid false positives
        suspicious = entropy_ratio < 0.6 or entropy_ratio > 0.995
        
        self.results = {
            'method': 'Audio Entropy Analysis',
            'entropy': float(entropy),
            'max_entropy': float(max_entropy),
            'entropy_ratio': float(entropy_ratio),
            'suspicious': suspicious
        }

    def _perform_audio_advanced_comprehensive_analysis(self):
        """Perform advanced comprehensive analysis on audio using multiple methods"""
        print("Performing audio advanced comprehensive analysis...")
        
        # Run all audio analysis methods
        self._perform_audio_lsb_analysis()
        lsb_results = self.results.copy()
        
        self._perform_audio_chi_square_test()
        chi2_results = self.results.copy()
        
        self._perform_audio_spectral_analysis()
        spectral_results = self.results.copy()
        
        self._perform_audio_autocorrelation_analysis()
        autocorr_results = self.results.copy()
        
        self._perform_audio_entropy_analysis()
        entropy_results = self.results.copy()
        
        # Weighted voting system for audio advanced comprehensive analysis
        method_weights = {
            'audio_lsb_analysis': 0.4,      # High weight - most reliable
            'audio_chi_square_test': 0.25,   # Medium weight
            'audio_spectral_analysis': 0.2,  # Medium weight
            'audio_entropy_analysis': 0.1,   # Lower weight
            'audio_autocorrelation_analysis': 0.05  # Lowest weight - most prone to false positives
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        all_results = {
            'audio_lsb_analysis': lsb_results,
            'audio_chi_square_test': chi2_results,
            'audio_spectral_analysis': spectral_results,
            'audio_autocorrelation_analysis': autocorr_results,
            'audio_entropy_analysis': entropy_results
        }
        
        for method, results in all_results.items():
            if method in method_weights:
                weight = method_weights[method]
                if results.get('suspicious', False):
                    weighted_score += weight
                total_weight += weight
        
        # Require weighted score > 0.3 to flag as suspicious
        overall_suspicious = (weighted_score / max(total_weight, 0.1)) > 0.3
        
        self.results = {
            'method': 'Audio Advanced Comprehensive Analysis',
            'audio_lsb_analysis': lsb_results,
            'audio_chi_square_test': chi2_results,
            'audio_spectral_analysis': spectral_results,
            'audio_autocorrelation_analysis': autocorr_results,
            'audio_entropy_analysis': entropy_results,
            'weighted_score': weighted_score,
            'total_weight': total_weight,
            'suspicious': overall_suspicious
        }

    def _calculate_confidence(self):
        """Calculate confidence level in the analysis."""
        if not self.results:
            self.confidence_level = 0.0
            return

        # Single-method default
        if "Comprehensive" not in self.results.get('method', ''):
            self.confidence_level = 0.85 if self.results.get('suspicious', False) else 0.95
            return

        # For comprehensive / advanced analyses
        analyses = self.results.get('analyses', {})

        # Fallback: check nested dicts for advanced comprehensive
        if not analyses:
            analyses = {
                k: v for k, v in self.results.items()
                if isinstance(v, dict) and 'method' in v
            }

        total_methods = len(analyses)
        suspicious_count = sum(
            1 for res in analyses.values()
            if isinstance(res, dict) and res.get('suspicious', False)
        )

        if suspicious_count == 0:
            self.confidence_level = 0.95
        else:
            agreement_ratio = suspicious_count / max(total_methods, 1)
            self.confidence_level = 0.7 + (0.3 * agreement_ratio)
            # Range: 0.7 (1/total flagged) → 1.0 (all flagged)

        # Method-specific adjustments
        if "Comprehensive" in self.results.get('method', ''):
            self.confidence_level += 0.05

        # Clamp final value
        self.confidence_level = min(max(self.confidence_level, 0.0), 1.0)

    def get_results(self) -> Dict:
        """
        Get analysis results

        Returns:
            Dict: Analysis results
        """
        return self.results.copy()

    def get_audio_statistics(self) -> Dict:
        """
        Get audio statistics

        Returns:
            Dict: Audio statistics
        """
        if self.audio_samples is None:
            return {}

        num_samples = int(self.audio_samples.shape[0]) if self.audio_samples.ndim >= 1 else 0
        duration_seconds = (self.audio_num_frames / self.audio_sample_rate) if (self.audio_num_frames and self.audio_sample_rate) else 0
        file_size_mb = os.path.getsize(self.audio_path) / (1024 * 1024) if self.audio_path else 0

        return {
            'file_path': self.audio_path,
            'sample_rate_hz': self.audio_sample_rate,
            'channels': self.audio_num_channels,
            'sample_width_bytes': self.audio_sample_width,
            'num_frames': self.audio_num_frames,
            'num_samples_per_channel': num_samples,
            'duration_seconds': duration_seconds,
            'file_size_mb': file_size_mb
        }

    def get_confidence_level(self) -> float:
        """
        Get confidence level in the analysis

        Returns:
            float: Confidence level (0.0 to 1.0)
        """
        return self.confidence_level

    def cleanup(self):
        """Clean up resources when machine is destroyed"""
        self.audio_samples = None
        self.audio_path = None
        self.audio_sample_rate = None
        self.audio_num_channels = None
        self.audio_sample_width = None
        self.audio_num_frames = None
        print("AudioSteganalysisMachine cleaned up")
