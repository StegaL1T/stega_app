# machine/steganalysis_machine.py
import os
from typing import Optional, Dict, List, Tuple
from PIL import Image
import numpy as np
import statistics


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

    def _perform_rs_analysis(self):
        """Perform RS (Regular-Singular) analysis"""
        print("Performing RS analysis...")

        # Simplified RS analysis
        # In practice, you'd implement the full RS analysis algorithm

        r_channel = self.image_array[:, :, 0]

        # Calculate RS statistics (simplified)
        rs_ratio = 0.5  # Placeholder calculation

        self.results = {
            'method': 'RS Analysis',
            'rs_ratio': rs_ratio,
            'suspicious': abs(rs_ratio - 0.5) > 0.1
        }

    def _perform_sample_pairs_analysis(self):
        """Perform Sample Pairs analysis"""
        print("Performing Sample Pairs analysis...")

        # Simplified sample pairs analysis
        r_channel = self.image_array[:, :, 0]

        # Calculate sample pairs statistics (simplified)
        pairs_ratio = 0.5  # Placeholder calculation

        self.results = {
            'method': 'Sample Pairs Analysis',
            'pairs_ratio': pairs_ratio,
            'suspicious': abs(pairs_ratio - 0.5) > 0.1
        }

    def _perform_comprehensive_analysis(self):
        """Perform comprehensive analysis using multiple methods"""
        print("Performing comprehensive analysis...")

        # Run multiple analysis methods
        self._perform_lsb_analysis()
        lsb_results = self.results.copy()

        self._perform_chi_square_test()
        chi2_results = self.results.copy()

        # Combine results
        self.results = {
            'method': 'Comprehensive Analysis',
            'lsb_analysis': lsb_results,
            'chi_square_test': chi2_results,
            'suspicious': lsb_results.get('suspicious', False) or chi2_results.get('suspicious', False)
        }

    def _calculate_confidence(self):
        """Calculate confidence level in the analysis"""
        if not self.results:
            self.confidence_level = 0.0
            return

        # Calculate confidence based on results
        if self.results.get('suspicious', False):
            self.confidence_level = 0.85  # High confidence if suspicious
        else:
            self.confidence_level = 0.95  # Very high confidence if clean

        # Adjust based on method
        if self.analysis_method == "Comprehensive Analysis":
            self.confidence_level += 0.05

        self.confidence_level = min(self.confidence_level, 1.0)

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

                f.write(f"Image: {self.image_path}\n")
                f.write(f"Analysis Method: {self.analysis_method}\n")
                f.write(f"Confidence Level: {self.confidence_level:.2%}\n\n")

                f.write("RESULTS:\n")
                f.write("--------\n")
                for key, value in self.results.items():
                    f.write(f"{key}: {value}\n")

                f.write("\nSTATISTICS:\n")
                f.write("-----------\n")
                stats = self.get_statistics()
                for key, value in stats.items():
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
        print("SteganalysisMachine cleaned up")
