# machine/steganalysis_machine.py
import os
from typing import Optional, Dict, List, Tuple
from PIL import Image
import numpy as np
import statistics
import wave
import contextlib
import scipy.fft
from scipy import stats
from scipy.signal import welch
import math


class SteganalysisMachine:
    """
    Handles all steganalysis operations and business logic.
    Separated from GUI to maintain clean architecture.
    """

    def __init__(self):
        """Initialize the steganalysis machine"""
        self.image_path: Optional[str] = None
        self.analysis_method: str = "LSB Analysis"
        self.image: Optional[Image.Image] = None
        self.image_array: Optional[np.ndarray] = None
        
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

        print("SteganalysisMachine initialized")

    def set_image(self, image_path: str) -> bool:
        """
        Set the image to analyze

        Args:
            image_path: Path to the image

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(image_path):
                print(f"Error: Image not found: {image_path}")
                return False

            # Load and validate image
            self.image = Image.open(image_path)
            self.image_path = image_path

            # Convert to RGB if necessary
            if self.image.mode != 'RGB':
                self.image = self.image.convert('RGB')

            # Convert to numpy array for processing
            self.image_array = np.array(self.image)

            print(f"Image loaded for analysis: {image_path}")
            print(f"Image dimensions: {self.image_array.shape}")

            return True

        except Exception as e:
            print(f"Error loading image: {e}")
            return False

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

    def set_analysis_method(self, method: str) -> None:
        """
        Set the analysis method to use

        Args:
            method: Analysis method name
        """
        self.analysis_method = method
        print(f"Analysis method set to: {method}")

    def validate_inputs(self) -> Tuple[bool, str]:
        """
        Validate inputs before analysis

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not self.image_path:
            return False, "No image selected for analysis"

        if not self.image:
            return False, "Image not loaded properly"

        return True, "Inputs valid"

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

    def analyze_image(self) -> bool:
        """
        Perform steganalysis on the image

        Returns:
            bool: True if successful, False otherwise
        """
        # Validate inputs
        is_valid, error_msg = self.validate_inputs()
        if not is_valid:
            print(f"Validation failed: {error_msg}")
            return False

        try:
            print(f"Starting {self.analysis_method}...")

            # Clear previous results
            self.results = {}
            self.statistics = {}

            # Perform analysis based on selected method
            if self.analysis_method == "LSB Analysis":
                self._perform_lsb_analysis()
            elif self.analysis_method == "Chi-Square Test":
                self._perform_chi_square_test()
            elif self.analysis_method == "RS Analysis":
                self._perform_rs_analysis()
            elif self.analysis_method == "Sample Pairs Analysis":
                self._perform_sample_pairs_analysis()
            elif self.analysis_method == "Comprehensive Analysis":
                self._perform_comprehensive_analysis()
            elif self.analysis_method == "DCT Analysis":
                self._perform_dct_analysis()
            elif self.analysis_method == "Wavelet Analysis":
                self._perform_wavelet_analysis()
            elif self.analysis_method == "Histogram Analysis":
                self._perform_histogram_analysis()
            elif self.analysis_method == "Advanced Comprehensive":
                self._perform_advanced_comprehensive_analysis()
            else:
                print(f"Unknown analysis method: {self.analysis_method}")
                return False

            # Calculate overall confidence
            self._calculate_confidence()

            print("Analysis completed successfully!")
            return True

        except Exception as e:
            print(f"Error during analysis: {e}")
            return False

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

            print("Audio analysis completed successfully!")
            return True

        except Exception as e:
            print(f"Error during audio analysis: {e}")
            return False

    def _perform_lsb_analysis(self):
        """Perform LSB analysis"""
        print("Performing LSB analysis...")

        # Extract LSBs from each color channel
        r_channel = self.image_array[:, :, 0]
        g_channel = self.image_array[:, :, 1]
        b_channel = self.image_array[:, :, 2]

        # Calculate LSB statistics
        r_lsb = r_channel & 1
        g_lsb = g_channel & 1
        b_lsb = b_channel & 1

        # Calculate LSB distribution
        r_lsb_ratio = np.mean(r_lsb)
        g_lsb_ratio = np.mean(g_lsb)
        b_lsb_ratio = np.mean(b_lsb)

        self.results = {
            'method': 'LSB Analysis',
            'r_lsb_ratio': r_lsb_ratio,
            'g_lsb_ratio': g_lsb_ratio,
            'b_lsb_ratio': b_lsb_ratio,
            'avg_lsb_ratio': (r_lsb_ratio + g_lsb_ratio + b_lsb_ratio) / 3,
            'suspicious': abs((r_lsb_ratio + g_lsb_ratio + b_lsb_ratio) / 3 - 0.5) > 0.1
        }

    def _perform_chi_square_test(self):
        """Perform Chi-Square test"""
        print("Performing Chi-Square test...")

        # This is a simplified implementation
        # In practice, you'd implement the full chi-square test

        r_channel = self.image_array[:, :, 0]
        g_channel = self.image_array[:, :, 1]
        b_channel = self.image_array[:, :, 2]

        # Calculate chi-square statistic for each channel
        r_chi2 = self._calculate_chi_square(r_channel)
        g_chi2 = self._calculate_chi_square(g_channel)
        b_chi2 = self._calculate_chi_square(b_channel)

        self.results = {
            'method': 'Chi-Square Test',
            'r_chi2': r_chi2,
            'g_chi2': g_chi2,
            'b_chi2': b_chi2,
            'avg_chi2': (r_chi2 + g_chi2 + b_chi2) / 3,
            'suspicious': (r_chi2 + g_chi2 + b_chi2) / 3 > 0.5
        }

    def _calculate_chi_square(self, channel: np.ndarray) -> float:
        """Calculate chi-square statistic for a channel"""
        # Simplified chi-square calculation
        # In practice, you'd implement the full statistical test

        # Count pixel value frequencies
        unique, counts = np.unique(channel, return_counts=True)

        # Calculate expected frequency (uniform distribution)
        expected = len(channel.flatten()) / 256

        # Calculate chi-square statistic
        chi2 = np.sum((counts - expected) ** 2 / expected)

        return chi2 / 1000  # Normalize for display

    def _perform_audio_lsb_analysis(self):
        """Perform LSB analysis on audio samples"""
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
            self.results = {
                'method': 'Audio LSB Analysis',
                'channel_lsb_ratios': channel_lsbs,
                'avg_lsb_ratio': avg_lsb,
                'suspicious': abs(avg_lsb - 0.5) > 0.1
            }
        else:
            lsb_ratio = float(np.mean((samples & 1) != 0))
            self.results = {
                'method': 'Audio LSB Analysis',
                'lsb_ratio': lsb_ratio,
                'suspicious': abs(lsb_ratio - 0.5) > 0.1
            }

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
        print("Performing audio comprehensive analysis...")

        self._perform_audio_lsb_analysis()
        lsb_results = self.results.copy()

        self._perform_audio_chi_square_test()
        chi2_results = self.results.copy()

        self.results = {
            'method': 'Audio Comprehensive Analysis',
            'audio_lsb_analysis': lsb_results,
            'audio_chi_square_test': chi2_results,
            'suspicious': lsb_results.get('suspicious', False) or chi2_results.get('suspicious', False)
        }

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
        
        # Check for unusual spectral patterns
        suspicious = hf_ratio > 0.3 or spectral_flatness < 0.1
        
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
        
        # Check for unusual entropy patterns
        # Low entropy might indicate steganographic content
        suspicious = entropy_ratio < 0.7 or entropy_ratio > 0.99
        
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
        
        # Combine results with weighted scoring
        suspicious_count = sum([
            lsb_results.get('suspicious', False),
            chi2_results.get('suspicious', False),
            spectral_results.get('suspicious', False),
            autocorr_results.get('suspicious', False),
            entropy_results.get('suspicious', False)
        ])
        
        # Consider suspicious if 2 or more methods flag it
        overall_suspicious = suspicious_count >= 2
        
        self.results = {
            'method': 'Audio Advanced Comprehensive Analysis',
            'audio_lsb_analysis': lsb_results,
            'audio_chi_square_test': chi2_results,
            'audio_spectral_analysis': spectral_results,
            'audio_autocorrelation_analysis': autocorr_results,
            'audio_entropy_analysis': entropy_results,
            'suspicious_methods_count': suspicious_count,
            'suspicious': overall_suspicious
        }

    def _perform_rs_analysis(self):
        """Perform RS (Regular-Singular) analysis across all color channels"""
        print("Performing RS analysis...")

        results_per_channel = {}
        suspicious_flag = False

        # Go through R, G, B channels
        for idx, color in enumerate(['R', 'G', 'B']):
            channel = self.image_array[:, :, idx].astype(np.int32)

            # Helper: flip LSBs
            def flip_lsb(block):
                return block ^ 1

            # Helper: discriminant (smoothness measure)
            def discriminant(block):
                return np.sum(np.abs(np.diff(block)))

            regular, singular = 0, 0

            # Iterate over rows in 2-pixel groups
            for row in channel:
                for i in range(0, len(row) - 1, 2):
                    block = row[i:i+2]
                    if len(block) < 2:
                        continue

                    d_original = discriminant(block)
                    block_flipped = flip_lsb(block)
                    d_flipped = discriminant(block_flipped)

                    if d_flipped > d_original:
                        regular += 1
                    elif d_flipped < d_original:
                        singular += 1

            total = max(regular + singular, 1)
            rs_ratio = regular / total

            # Store channel results
            results_per_channel[color] = {
                'regular_groups': regular,
                'singular_groups': singular,
                'rs_ratio': rs_ratio
            }

            # If RS ratio deviates from ~0.5, flag as suspicious
            if abs(rs_ratio - 0.5) > 0.05:
                suspicious_flag = True

        # Save combined results
        self.results = {
            'method': 'RS Analysis',
            'channels': results_per_channel,
            'suspicious': suspicious_flag
        }

    def _perform_sample_pairs_analysis(self):
        """Perform Sample Pairs analysis across all color channels"""
        print("Performing Sample Pairs analysis...")

        results_per_channel = {}
        suspicious_flag = False

        for idx, color in enumerate(['R', 'G', 'B']):
            channel = self.image_array[:, :, idx].astype(np.int32)

            total_pairs = 0
            equal_pairs = 0
            different_pairs = 0

            # Iterate over rows and check adjacent pixel pairs
            for row in channel:
                for i in range(0, len(row) - 1):
                    p1, p2 = row[i], row[i + 1]
                    total_pairs += 1
                    if p1 == p2:
                        equal_pairs += 1
                    else:
                        different_pairs += 1

            # Calculate ratio (normalized)
            equal_ratio = equal_pairs / max(total_pairs, 1)
            diff_ratio = different_pairs / max(total_pairs, 1)

            # Store per-channel results
            results_per_channel[color] = {
                'total_pairs': total_pairs,
                'equal_pairs': equal_pairs,
                'different_pairs': different_pairs,
                'equal_ratio': equal_ratio,
                'diff_ratio': diff_ratio
            }

            # Suspicion check: if equal/diff balance looks skewed
            if abs(equal_ratio - diff_ratio) > 0.2:  
                suspicious_flag = True

        # Save combined results
        self.results = {
            'method': 'Sample Pairs Analysis',
            'channels': results_per_channel,
            'suspicious': suspicious_flag
        }


    def _perform_rs_analysis(self):
        """Perform RS (Regular-Singular) analysis across all color channels"""
        print("Performing RS analysis...")

        results_per_channel = {}
        suspicious_flag = False

        # Go through R, G, B channels
        for idx, color in enumerate(['R', 'G', 'B']):
            channel = self.image_array[:, :, idx].astype(np.int32)

            # Helper: flip LSBs
            def flip_lsb(block):
                return block ^ 1

            # Helper: discriminant (smoothness measure)
            def discriminant(block):
                return np.sum(np.abs(np.diff(block)))

            regular, singular = 0, 0

            # Iterate over rows in 2-pixel groups
            for row in channel:
                for i in range(0, len(row) - 1, 2):
                    block = row[i:i+2]
                    if len(block) < 2:
                        continue

                    d_original = discriminant(block)
                    block_flipped = flip_lsb(block)
                    d_flipped = discriminant(block_flipped)

                    if d_flipped > d_original:
                        regular += 1
                    elif d_flipped < d_original:
                        singular += 1

            total = max(regular + singular, 1)
            rs_ratio = regular / total

            # Store channel results
            results_per_channel[color] = {
                'regular_groups': regular,
                'singular_groups': singular,
                'rs_ratio': rs_ratio
            }

            # If RS ratio deviates from ~0.5, flag as suspicious
            if abs(rs_ratio - 0.5) > 0.05:
                suspicious_flag = True

        # Save combined results
        self.results = {
            'method': 'RS Analysis',
            'channels': results_per_channel,
            'suspicious': suspicious_flag
        }


    def _perform_comprehensive_analysis(self):
        """Perform comprehensive analysis using multiple methods"""
        print("Performing comprehensive analysis...")

        # Run all methods and store their results
        all_results = {}

        # LSB Analysis
        self._perform_lsb_analysis()
        all_results['lsb_analysis'] = self.results.copy()

        # Chi-Square Test
        self._perform_chi_square_test()
        all_results['chi_square_test'] = self.results.copy()

        # RS Analysis
        self._perform_rs_analysis()
        all_results['rs_analysis'] = self.results.copy()

        # Sample Pairs Analysis
        self._perform_sample_pairs_analysis()
        all_results['sample_pairs_analysis'] = self.results.copy()

        # Combine into final results
        suspicious_flag = any(
            res.get('suspicious', False) for res in all_results.values()
        )

        self.results = {
            'method': 'Comprehensive Analysis',
            'analyses': all_results,
            'suspicious': suspicious_flag
        }

    def _perform_dct_analysis(self):
        """Perform DCT (Discrete Cosine Transform) analysis"""
        print("Performing DCT analysis...")
        
        # Convert to grayscale for DCT analysis
        if len(self.image_array.shape) == 3:
            gray = np.mean(self.image_array, axis=2)
        else:
            gray = self.image_array
            
        # Apply DCT to 8x8 blocks
        dct_coeffs = []
        for i in range(0, gray.shape[0] - 8, 8):
            for j in range(0, gray.shape[1] - 8, 8):
                block = gray[i:i+8, j:j+8].astype(np.float32)
                dct_block = scipy.fft.dctn(block, norm='ortho')
                dct_coeffs.append(dct_block.flatten())
        
        dct_coeffs = np.array(dct_coeffs)
        
        # Analyze high-frequency coefficients (potential stego indicators)
        hf_coeffs = dct_coeffs[:, 1:]  # Exclude DC component
        hf_variance = np.var(hf_coeffs, axis=1)
        avg_hf_variance = np.mean(hf_variance)
        
        # Check for unusual patterns in DCT coefficients
        suspicious = avg_hf_variance > np.percentile(hf_variance, 90)
        
        self.results = {
            'method': 'DCT Analysis',
            'avg_hf_variance': float(avg_hf_variance),
            'dct_blocks_analyzed': len(dct_coeffs),
            'suspicious': suspicious
        }

    def _perform_wavelet_analysis(self):
        """Perform Wavelet analysis (simplified)"""
        print("Performing Wavelet analysis...")
        
        # Convert to grayscale
        if len(self.image_array.shape) == 3:
            gray = np.mean(self.image_array, axis=2)
        else:
            gray = self.image_array
            
        # Simple wavelet-like analysis using differences
        # Horizontal differences
        h_diff = np.diff(gray, axis=1)
        # Vertical differences  
        v_diff = np.diff(gray, axis=0)
        
        # Calculate energy in high-frequency components
        h_energy = np.mean(h_diff ** 2)
        v_energy = np.mean(v_diff ** 2)
        total_energy = h_energy + v_energy
        
        # Check for unusual energy distribution
        energy_ratio = h_energy / (v_energy + 1e-10)
        suspicious = abs(energy_ratio - 1.0) > 0.3 or total_energy > np.percentile(gray.flatten(), 95)
        
        self.results = {
            'method': 'Wavelet Analysis',
            'horizontal_energy': float(h_energy),
            'vertical_energy': float(v_energy),
            'energy_ratio': float(energy_ratio),
            'suspicious': suspicious
        }

    def _perform_histogram_analysis(self):
        """Perform detailed histogram analysis"""
        print("Performing Histogram analysis...")
        
        r_channel = self.image_array[:, :, 0]
        g_channel = self.image_array[:, :, 1]
        b_channel = self.image_array[:, :, 2]
        
        # Calculate histogram smoothness
        def histogram_smoothness(channel):
            hist, _ = np.histogram(channel, bins=256, range=(0, 256))
            # Calculate second derivative (smoothness measure)
            diff1 = np.diff(hist)
            diff2 = np.diff(diff1)
            smoothness = np.sum(np.abs(diff2))
            return smoothness
        
        r_smooth = histogram_smoothness(r_channel)
        g_smooth = histogram_smoothness(g_channel)
        b_smooth = histogram_smoothness(b_channel)
        
        # Check for unusual histogram patterns
        avg_smoothness = (r_smooth + g_smooth + b_smooth) / 3
        suspicious = avg_smoothness > 1000  # Threshold for suspicious smoothness
        
        self.results = {
            'method': 'Histogram Analysis',
            'r_smoothness': float(r_smooth),
            'g_smoothness': float(g_smooth),
            'b_smoothness': float(b_smooth),
            'avg_smoothness': float(avg_smoothness),
            'suspicious': suspicious
        }

    def _perform_advanced_comprehensive_analysis(self):
        """Perform advanced comprehensive analysis using multiple methods"""
        print("Performing advanced comprehensive analysis...")
        
        # Run all basic methods
        self._perform_lsb_analysis()
        lsb_results = self.results.copy()
        
        self._perform_chi_square_test()
        chi2_results = self.results.copy()
        
        self._perform_dct_analysis()
        dct_results = self.results.copy()
        
        self._perform_wavelet_analysis()
        wavelet_results = self.results.copy()
        
        self._perform_histogram_analysis()
        hist_results = self.results.copy()
        
        # Combine results with weighted scoring
        suspicious_count = sum([
            lsb_results.get('suspicious', False),
            chi2_results.get('suspicious', False),
            dct_results.get('suspicious', False),
            wavelet_results.get('suspicious', False),
            hist_results.get('suspicious', False)
        ])
        
        # Consider suspicious if 2 or more methods flag it
        overall_suspicious = suspicious_count >= 2
        
        self.results = {
            'method': 'Advanced Comprehensive Analysis',
            'lsb_analysis': lsb_results,
            'chi_square_test': chi2_results,
            'dct_analysis': dct_results,
            'wavelet_analysis': wavelet_results,
            'histogram_analysis': hist_results,
            'suspicious_methods_count': suspicious_count,
            'suspicious': overall_suspicious
        }
    def _calculate_confidence(self):
        """Calculate confidence level in the analysis"""
        if not self.results:
            self.confidence_level = 0.0
            return

        # Default: for single methods
        if self.analysis_method != "Comprehensive Analysis":
            if self.results.get('suspicious', False):
                self.confidence_level = 0.85  # suspicious
            else:
                self.confidence_level = 0.95  # clean
            return

        # For comprehensive analysis
        analyses = self.results.get('analyses', {})
        total_methods = len(analyses)
        suspicious_count = sum(
            1 for res in analyses.values() if res.get('suspicious', False)
        )

        if suspicious_count == 0:
            self.confidence_level = 0.95  # very confident it's clean
        else:
            # Confidence increases with agreement across methods
            agreement_ratio = suspicious_count / total_methods
            self.confidence_level = 0.7 + (0.3 * agreement_ratio)
            # Range: 0.7 (1 method flagged) → 1.0 (all flagged)

        # Adjust based on method
        if self.analysis_method in ["Comprehensive Analysis", "Advanced Comprehensive"]:
            self.confidence_level += 0.05
        elif self.analysis_method in ["DCT Analysis", "Wavelet Analysis", "Histogram Analysis"]:
            self.confidence_level += 0.02

        # Ensure stays between 0.0 and 1.0
        self.confidence_level = min(max(self.confidence_level, 0.0), 1.0)


    def get_results(self) -> Dict:
        """
        Get analysis results

        Returns:
            Dict: Analysis results
        """
        return self.results.copy()

    def get_statistics(self) -> Dict:
        """
        Get image statistics

        Returns:
            Dict: Image statistics
        """
        if self.image is None:
            return {}

        return {
            'file_path': self.image_path,
            'dimensions': self.image_array.shape,
            'size_pixels': self.image_array.size,
            'file_size_mb': os.path.getsize(self.image_path) / (1024 * 1024) if self.image_path else 0,
            'color_channels': self.image_array.shape[2] if len(self.image_array.shape) > 2 else 1,
            'compression': self.image.format,
            'mode': self.image.mode
        }

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

    def export_report(self, file_path: str) -> bool:
        """
        Export analysis report to file

        Args:
            file_path: Path to save the report

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(file_path, 'w') as f:
                f.write("STEGANALYSIS REPORT\n")
                f.write("==================\n\n")

                if self.image_path:
                    f.write(f"Image: {self.image_path}\n")
                if self.audio_path:
                    f.write(f"Audio: {self.audio_path}\n")
                f.write(f"Confidence Level: {self.confidence_level:.2%}\n\n")

                f.write("RESULTS:\n")
                f.write("--------\n")
                for key, value in self.results.items():
                    f.write(f"{key}: {value}\n")

                if self.image_path:
                    f.write("\nIMAGE STATISTICS:\n")
                    f.write("------------------\n")
                    stats = self.get_statistics()
                    for key, value in stats.items():
                        f.write(f"{key}: {value}\n")

                if self.audio_path:
                    f.write("\nAUDIO STATISTICS:\n")
                    f.write("------------------\n")
                    astats = self.get_audio_statistics()
                    for key, value in astats.items():
                        f.write(f"{key}: {value}\n")

            print(f"Report exported to: {file_path}")
            return True

        except Exception as e:
            print(f"Error exporting report: {e}")
            return False

    def cleanup(self):
        """Clean up resources when machine is destroyed"""
        self.image = None
        self.image_array = None
        self.audio_samples = None
        self.audio_path = None
        self.audio_sample_rate = None
        self.audio_num_channels = None
        self.audio_sample_width = None
        self.audio_num_frames = None
        print("SteganalysisMachine cleaned up")
