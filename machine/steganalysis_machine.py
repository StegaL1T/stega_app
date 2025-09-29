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

# Import specialized machines
from machine.image_steganalysis_machine import ImageSteganalysisMachine
from machine.audio_steganalysis_machine import AudioSteganalysisMachine
from machine.video_steganalysis_machine import VideoSteganalysisMachine


class SteganalysisMachine:
    """
    Handles all steganalysis operations and business logic.
    Separated from GUI to maintain clean architecture.
    """

    def __init__(self):
        """Initialize the steganalysis machine"""
        # Initialize specialized machines
        self.image_machine = ImageSteganalysisMachine()
        self.audio_machine = AudioSteganalysisMachine()
        self.video_machine = VideoSteganalysisMachine()
        
        # Legacy properties for backward compatibility
        self.analysis_method: str = "LSB Analysis"
        
        # Unified results and statistics
        self.results: Dict = {}
        self.statistics: Dict = {}
        self.confidence_level: float = 0.0
        
        # Track the last analyzed file path
        self.last_analyzed_path: Optional[str] = None

        print("SteganalysisMachine initialized")

    # Property accessors for backward compatibility with GUI
    @property
    def image_array(self):
        """Get image array from image machine"""
        return self.image_machine.image_array if hasattr(self.image_machine, 'image_array') else None
    
    @property
    def audio_samples(self):
        """Get audio samples from audio machine"""
        return self.audio_machine.audio_samples if hasattr(self.audio_machine, 'audio_samples') else None
    
    @property
    def video_frames(self):
        """Get video frames from video machine"""
        return self.video_machine.video_frames if hasattr(self.video_machine, 'video_frames') else None
    
    @property
    def image_path(self):
        """Get image path from image machine"""
        return self.image_machine.image_path if hasattr(self.image_machine, 'image_path') else None
    
    @property
    def audio_path(self):
        """Get audio path from audio machine"""
        return self.audio_machine.audio_path if hasattr(self.audio_machine, 'audio_path') else None
    
    @property
    def audio_sample_rate(self):
        """Get audio sample rate from audio machine"""
        return self.audio_machine.audio_sample_rate if hasattr(self.audio_machine, 'audio_sample_rate') else None
    
    @property
    def audio_num_channels(self):
        """Get audio number of channels from audio machine"""
        return self.audio_machine.audio_num_channels if hasattr(self.audio_machine, 'audio_num_channels') else None
    
    @property
    def audio_sample_width(self):
        """Get audio sample width from audio machine"""
        return self.audio_machine.audio_sample_width if hasattr(self.audio_machine, 'audio_sample_width') else None
    
    @property
    def audio_num_frames(self):
        """Get audio number of frames from audio machine"""
        return self.audio_machine.audio_num_frames if hasattr(self.audio_machine, 'audio_num_frames') else None
    
    @property
    def video_path(self):
        """Get video path from video machine"""
        return self.video_machine.video_path if hasattr(self.video_machine, 'video_path') else None
    
    @property
    def video_fps(self):
        """Get video FPS from video machine"""
        return self.video_machine.video_fps if hasattr(self.video_machine, 'video_fps') else None
    
    @property
    def video_duration(self):
        """Get video duration from video machine"""
        return self.video_machine.video_duration if hasattr(self.video_machine, 'video_duration') else None
    
    @property
    def video_width(self):
        """Get video width from video machine"""
        return self.video_machine.video_width if hasattr(self.video_machine, 'video_width') else None
    
    @property
    def video_height(self):
        """Get video height from video machine"""
        return self.video_machine.video_height if hasattr(self.video_machine, 'video_height') else None
    
    @property
    def image(self):
        """Get image from image machine"""
        return self.image_machine.image if hasattr(self.image_machine, 'image') else None

    def set_image(self, image_path: str) -> bool:
        """
        Set the image to analyze

        Args:
            image_path: Path to the image

        Returns:
            bool: True if successful, False otherwise
        """
        return self.image_machine.set_image(image_path)

    def set_audio(self, audio_path: str) -> bool:
        """
        Set the audio file (WAV PCM) to analyze.

        Args:
            audio_path: Path to the audio file (.wav)

        Returns:
            bool: True if successful, False otherwise
        """
        return self.audio_machine.set_audio(audio_path)

    def set_analysis_method(self, method: str) -> None:
        """
        Set the analysis method to use

        Args:
            method: Analysis method name
        """
        self.analysis_method = method
        self.image_machine.set_analysis_method(method)
        print(f"Analysis method set to: {method}")

    def validate_inputs(self) -> Tuple[bool, str]:
        """
        Validate inputs before analysis

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        return self.image_machine.validate_inputs()

    def validate_audio_inputs(self) -> Tuple[bool, str]:
        """
        Validate audio inputs before analysis

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        return self.audio_machine.validate_audio_inputs()

    def validate_video_inputs(self) -> Tuple[bool, str]:
        """
        Validate video inputs before analysis

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        return self.video_machine.validate_video_inputs()

    def set_video(self, video_path: str) -> bool:
        """
        Load video frames and metadata using OpenCV.
        """
        return self.video_machine.set_video(video_path)


    def analyze_video(self, method: str = "Video LSB Analysis") -> bool:
        """
        Perform steganalysis on the video

        Args:
            method: Analysis method name for video

        Returns:
            bool: True if successful, False otherwise
        """
        success = self.video_machine.analyze_video(method)
        if success:
            # Store current sensitivity for report generation
            self.current_sensitivity = getattr(self.video_machine, 'current_sensitivity', 'Unknown')
            # Track the last analyzed file
            self.last_analyzed_path = self.video_machine.video_path
            # Copy results from video machine to main machine for backward compatibility
            self.results = self.video_machine.get_results()
            self.confidence_level = self.video_machine.get_confidence_level()
            self._results_set = True
            self._confidence_set = True
        return success

    def get_video_statistics(self) -> Dict:
        """
        Get video statistics

        Returns:
            Dict: Video statistics
        """
        return self.video_machine.get_video_statistics()

    def analyze_image(self) -> bool:
        """
        Perform steganalysis on the image

        Returns:
            bool: True if successful, False otherwise
        """
        success = self.image_machine.analyze_image()
        if success:
            # Store current sensitivity for report generation
            self.current_sensitivity = getattr(self.image_machine, 'current_sensitivity', 'Unknown')
            # Track the last analyzed file
            self.last_analyzed_path = self.image_machine.image_path
            # Copy results from image machine to main machine for backward compatibility
            self.results = self.image_machine.get_results()
            self.confidence_level = self.image_machine.get_confidence_level()
            self._results_set = True
            self._confidence_set = True
        return success

    def analyze_audio(self, method: str = "Audio LSB Analysis") -> bool:
        """
        Perform steganalysis on the audio

        Args:
            method: Analysis method name for audio

        Returns:
            bool: True if successful, False otherwise
        """
        success = self.audio_machine.analyze_audio(method)
        if success:
            # Store current sensitivity for report generation
            self.current_sensitivity = getattr(self.audio_machine, 'current_sensitivity', 'Unknown')
            # Track the last analyzed file
            self.last_analyzed_path = self.audio_machine.audio_path
            # Copy results from audio machine to main machine for backward compatibility
            self.results = self.audio_machine.get_results()
            self.confidence_level = self.audio_machine.get_confidence_level()
            self._results_set = True
            self._confidence_set = True
        return success





    def get_results(self) -> Dict:
        """
        Get analysis results from the appropriate specialized machine

        Returns:
            Dict: Analysis results
        """
        # If results are already copied locally (for backward compatibility), use them
        if hasattr(self, '_results_set') and self._results_set:
            return self.results.copy()
        
        # Otherwise, get results from the specialized machine that was used
        if self.image_path:
            return self.image_machine.get_results()
        elif self.audio_path:
            return self.audio_machine.get_results()
        elif self.video_path:
            return self.video_machine.get_results()
        else:
            return {}

    def get_statistics(self) -> Dict:
        """
        Get image statistics

        Returns:
            Dict: Image statistics
        """
        return self.image_machine.get_statistics()

    def get_audio_statistics(self) -> Dict:
        """
        Get audio statistics

        Returns:
            Dict: Audio statistics
        """
        return self.audio_machine.get_audio_statistics()

    def get_confidence_level(self) -> float:
        """
        Get confidence level from the appropriate specialized machine

        Returns:
            float: Confidence level (0.0 to 1.0)
        """
        # If confidence is already set locally (for backward compatibility), use it
        # Check if it's been set (not just default 0.0)
        if hasattr(self, '_confidence_set') and self._confidence_set:
            return self.confidence_level
        
        # Otherwise, get confidence from the specialized machine that was used
        if self.image_path:
            return self.image_machine.get_confidence_level()
        elif self.audio_path:
            return self.audio_machine.get_confidence_level()
        elif self.video_path:
            return self.video_machine.get_confidence_level()
        else:
            return 0.0

    def set_sensitivity_level(self, level: str):
        """Set the sensitivity level for all analysis machines"""
        self.image_machine.set_sensitivity_level(level)
        self.audio_machine.set_sensitivity_level(level)
        self.video_machine.set_sensitivity_level(level)
        print(f"All machines sensitivity level set to: {level}")

    def export_report(self, file_path: str) -> bool:
        """
        Export analysis report to file

        Args:
            file_path: Path to save the report

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from datetime import datetime
            import os
            
            with open(file_path, 'w') as f:
                # Header
                f.write("STEGANALYSIS ANALYSIS REPORT\n")
                f.write("============================\n\n")

                # File Information
                f.write("FILE INFORMATION\n")
                f.write("----------------\n")
                current_file = self.last_analyzed_path
                if current_file:
                    f.write(f"File Path: {current_file}\n")
                
                if current_file:
                    try:
                        file_size = os.path.getsize(current_file)
                        file_size_mb = file_size / (1024 * 1024)
                        f.write(f"File Size: {file_size_mb:.2f} MB\n")
                    except:
                        f.write(f"File Size: Unable to determine\n")
                    
                    file_ext = os.path.splitext(current_file)[1].upper()
                    if file_ext in ['.PNG', '.JPG', '.JPEG', '.BMP', '.TIFF']:
                        f.write(f"File Type: Image ({file_ext})\n")
                    elif file_ext in ['.WAV', '.MP3', '.FLAC', '.AAC']:
                        f.write(f"File Type: Audio ({file_ext})\n")
                    elif file_ext in ['.MP4', '.AVI', '.MOV', '.WMV']:
                        f.write(f"File Type: Video ({file_ext})\n")
                    else:
                        f.write(f"File Type: {file_ext}\n")
                
                f.write(f"Analysis Date: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}\n\n")

                # Analysis Configuration
                f.write("ANALYSIS CONFIGURATION\n")
                f.write("-----------------------\n")
                results = self.get_results()
                method_name = "Unknown"
                if results and 'method' in results:
                    method_name = results['method']
                f.write(f"Method: {method_name}\n")
                
                # Get sensitivity level from the current analysis
                sensitivity = "Unknown"
                if hasattr(self, 'current_sensitivity'):
                    sensitivity = self.current_sensitivity
                elif results and 'sensitivity' in results:
                    sensitivity = results['sensitivity']
                f.write(f"Sensitivity: {sensitivity}\n")
                # Extract execution time from the results
                execution_time = "Unknown"
                if results:
                    # Look for execution time in individual method results
                    for key, value in results.items():
                        if isinstance(value, dict) and 'execution_time_ms' in value:
                            execution_time = f"{value['execution_time_ms']}"
                            break
                    # If not found in individual methods, check top level
                    if execution_time == "Unknown" and 'execution_time_ms' in results:
                        execution_time = f"{results['execution_time_ms']}"
                
                f.write(f"Analysis Duration: {execution_time} ms\n")
                f.write(f"Processing Status: COMPLETED\n\n")

                # Detection Results
                f.write("DETECTION RESULTS\n")
                f.write("-----------------\n")
                confidence = self.get_confidence_level()
                suspicious = results.get('suspicious', False) if results else False
                
                result_status = "SUSPICIOUS" if suspicious else "CLEAN"
                f.write(f"Overall Result: {result_status}\n")
                f.write(f"Confidence: {confidence:.2%}\n")
                
                # Risk assessment based on confidence AND result
                if suspicious:
                    # For suspicious files, higher confidence = higher risk
                    if confidence >= 0.8:
                        risk_level = "HIGH"
                    elif confidence >= 0.6:
                        risk_level = "MEDIUM"
                    else:
                        risk_level = "LOW"
                else:
                    # For clean files, higher confidence = lower risk (more certain it's clean)
                    if confidence >= 0.8:
                        risk_level = "LOW"
                    elif confidence >= 0.6:
                        risk_level = "MEDIUM"
                    else:
                        risk_level = "HIGH"
                f.write(f"Risk Level: {risk_level}\n\n")

                # Method Breakdown
                f.write("METHOD BREAKDOWN\n")
                f.write("----------------\n")
                if results:
                    # Always try to extract individual methods first (for comprehensive analysis)
                    method_results = []
                    for key, value in results.items():
                        if isinstance(value, dict) and 'method' in value and 'suspicious' in value:
                            method_name = value['method']
                            method_suspicious = value['suspicious']
                            status = "SUSPICIOUS" if method_suspicious else "NOT SUSPICIOUS"
                            method_results.append((method_name, status))
                    
                    
                    if method_results:
                        # Show individual methods (comprehensive analysis)
                        f.write(f"{'Method':<25} {'Status':<10}\n")
                        f.write("-" * 35 + "\n")
                        for method, status in method_results:
                            f.write(f"{method:<25} {status:<10}\n")
                    elif 'method' in results and 'suspicious' in results:
                        # Single method result
                        method_name = results['method']
                        method_suspicious = results['suspicious']
                        status = "SUSPICIOUS" if method_suspicious else "NOT SUSPICIOUS"
                        f.write(f"{'Method':<25} {'Status':<10}\n")
                        f.write("-" * 35 + "\n")
                        f.write(f"{method_name:<25} {status:<10}\n")
                    else:
                        f.write("No detailed method breakdown available.\n")
                else:
                    f.write("No analysis results available.\n")
                f.write("\n")

                # Technical Details
                f.write("TECHNICAL DETAILS\n")
                f.write("-----------------\n")
                if results:
                    for key, value in results.items():
                        if isinstance(value, dict):
                            f.write(f"{key}:\n")
                            for sub_key, sub_value in value.items():
                                if sub_key != 'method':  # Skip method as it's already shown above
                                    f.write(f"  {sub_key}: {sub_value}\n")
                        else:
                            f.write(f"{key}: {value}\n")
                    
                else:
                    f.write("No technical details available.\n")
                f.write("\n")

                # File Statistics - show only for the last analyzed file
                if self.last_analyzed_path:
                    file_ext = self.last_analyzed_path.lower().split('.')[-1] if '.' in self.last_analyzed_path else ''
                    
                    if file_ext in ['png', 'jpg', 'jpeg', 'bmp', 'gif'] and self.image_path:
                        f.write("IMAGE STATISTICS\n")
                        f.write("----------------\n")
                        stats = self.get_statistics()
                        for key, value in stats.items():
                            f.write(f"{key}: {value}\n")
                        f.write("\n")
                    elif file_ext in ['wav', 'mp3'] and self.audio_path:
                        f.write("AUDIO STATISTICS\n")
                        f.write("----------------\n")
                        astats = self.get_audio_statistics()
                        for key, value in astats.items():
                            f.write(f"{key}: {value}\n")
                        f.write("\n")
                    elif file_ext in ['mp4', 'mov', 'avi'] and self.video_path:
                        f.write("VIDEO STATISTICS\n")
                        f.write("----------------\n")
                        vstats = self.get_video_statistics()
                        for key, value in vstats.items():
                            f.write(f"{key}: {value}\n")
                        f.write("\n")

            print(f"Report exported to: {file_path}")
            return True

        except Exception as e:
            print(f"Error exporting report: {e}")
            return False

    def cleanup(self):
        """Clean up resources when machine is destroyed"""
        self.image_machine.cleanup()
        self.audio_machine.cleanup()
        self.video_machine.cleanup()
        print("SteganalysisMachine cleaned up")
