# machine/image_steganalysis_machine.py
import os
from typing import Optional, Dict, List, Tuple
from PIL import Image
import numpy as np
import statistics
import scipy.fft
from scipy import stats


class ImageSteganalysisMachine:
    """
    Handles image steganalysis operations and business logic.
    Specialized for image-based steganographic detection.
    """

    def __init__(self):
        """Initialize the image steganalysis machine"""
        self.image_path: Optional[str] = None
        self.analysis_method: str = "LSB Analysis"
        self.image: Optional[Image.Image] = None
        self.image_array: Optional[np.ndarray] = None
        
        # Analysis results
        self.results: Dict = {}
        self.statistics: Dict = {}
        self.confidence_level: float = 0.0

        print("ImageSteganalysisMachine initialized")

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

        avg_lsb_ratio = (r_lsb_ratio + g_lsb_ratio + b_lsb_ratio) / 3
        # More conservative threshold: only flag if significantly deviant from 0.5
        # Also check if multiple channels show similar deviation (stronger indicator)
        channel_deviations = [abs(r_lsb_ratio - 0.5), abs(g_lsb_ratio - 0.5), abs(b_lsb_ratio - 0.5)]
        max_deviation = max(channel_deviations)
        avg_deviation = np.mean(channel_deviations)
        
        # Suspicious if: high average deviation OR multiple channels show significant deviation
        suspicious = (abs(avg_lsb_ratio - 0.5) > 0.15) or (max_deviation > 0.2 and avg_deviation > 0.1)
        
        self.results = {
            'method': 'LSB Analysis',
            'r_lsb_ratio': r_lsb_ratio,
            'g_lsb_ratio': g_lsb_ratio,
            'b_lsb_ratio': b_lsb_ratio,
            'avg_lsb_ratio': avg_lsb_ratio,
            'max_deviation': max_deviation,
            'avg_deviation': avg_deviation,
            'suspicious': suspicious
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

        avg_chi2 = (r_chi2 + g_chi2 + b_chi2) / 3
        # More conservative threshold for chi-square test
        # Also consider if multiple channels show high chi-square values
        chi2_values = [r_chi2, g_chi2, b_chi2]
        max_chi2 = max(chi2_values)
        
        # Suspicious if: high average chi-square OR multiple channels show high values
        suspicious = (avg_chi2 > 0.3) or (max_chi2 > 0.5 and avg_chi2 > 0.2)
        
        self.results = {
            'method': 'Chi-Square Test',
            'r_chi2': r_chi2,
            'g_chi2': g_chi2,
            'b_chi2': b_chi2,
            'avg_chi2': avg_chi2,
            'max_chi2': max_chi2,
            'suspicious': suspicious
        }

    def _calculate_chi_square(self, channel: np.ndarray) -> float:
        """Calculate chi-square statistic for a channel with proper statistical analysis"""
        # Count pixel value frequencies
        hist, _ = np.histogram(channel, bins=256, range=(0, 256))
        
        # Calculate expected frequency (uniform distribution)
        total_pixels = len(channel.flatten())
        expected = total_pixels / 256
        
        # Only use bins with sufficient expected frequency (avoid division by zero)
        valid_bins = expected >= 5  # Chi-square assumption
        if np.sum(valid_bins) < 10:  # Need at least 10 valid bins
            return 0.0
            
        observed = hist[valid_bins]
        expected_valid = expected
        
        # Calculate chi-square statistic
        chi2 = np.sum((observed - expected_valid) ** 2 / expected_valid)
        
        # Calculate degrees of freedom
        df = np.sum(valid_bins) - 1
        
        # Normalize by degrees of freedom and scale for display
        normalized_chi2 = chi2 / max(df, 1) / 100.0
        
        return float(normalized_chi2)

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

        # Weighted voting system for comprehensive analysis
        method_weights = {
            'lsb_analysis': 0.4,      # High weight - most reliable
            'chi_square_test': 0.3,   # Medium weight
            'rs_analysis': 0.2,       # Medium weight
            'sample_pairs_analysis': 0.1  # Lower weight - more prone to false positives
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for method, results in all_results.items():
            if method in method_weights:
                weight = method_weights[method]
                if results.get('suspicious', False):
                    weighted_score += weight
                total_weight += weight
        
        # Require weighted score > 0.3 to flag as suspicious
        suspicious_flag = (weighted_score / max(total_weight, 0.1)) > 0.3

        self.results = {
            'method': 'Comprehensive Analysis',
            'analyses': all_results,
            'weighted_score': weighted_score,
            'total_weight': total_weight,
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
        
        # Weighted voting system for advanced comprehensive analysis
        method_weights = {
            'lsb_analysis': 0.35,      # High weight - most reliable
            'chi_square_test': 0.25,   # Medium weight
            'dct_analysis': 0.2,       # Medium weight
            'wavelet_analysis': 0.15,  # Lower weight
            'histogram_analysis': 0.05  # Lowest weight - most prone to false positives
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        all_results = {
            'lsb_analysis': lsb_results,
            'chi_square_test': chi2_results,
            'dct_analysis': dct_results,
            'wavelet_analysis': wavelet_results,
            'histogram_analysis': hist_results
        }
        
        for method, results in all_results.items():
            if method in method_weights:
                weight = method_weights[method]
                if results.get('suspicious', False):
                    weighted_score += weight
                total_weight += weight
        
        # Require weighted score > 0.25 to flag as suspicious
        overall_suspicious = (weighted_score / max(total_weight, 0.1)) > 0.25
        
        self.results = {
            'method': 'Advanced Comprehensive Analysis',
            'lsb_analysis': lsb_results,
            'chi_square_test': chi2_results,
            'dct_analysis': dct_results,
            'wavelet_analysis': wavelet_results,
            'histogram_analysis': hist_results,
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
        if "Comprehensive" not in self.analysis_method:
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
        if "Comprehensive" in self.analysis_method:
            self.confidence_level += 0.05
        elif self.analysis_method in ["DCT Analysis", "Wavelet Analysis", "Histogram Analysis"]:
            self.confidence_level += 0.02

        # Clamp final value
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

    def get_confidence_level(self) -> float:
        """
        Get confidence level in the analysis

        Returns:
            float: Confidence level (0.0 to 1.0)
        """
        return self.confidence_level

    def cleanup(self):
        """Clean up resources when machine is destroyed"""
        self.image = None
        self.image_array = None
        print("ImageSteganalysisMachine cleaned up")
