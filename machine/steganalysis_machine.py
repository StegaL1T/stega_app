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
            with open(file_path, 'w') as f:
                f.write("STEGANALYSIS REPORT\n")
                f.write("==================\n\n")

                # Get confidence and results from the appropriate specialized machine
                if self.image_path:
                    f.write(f"Image: {self.image_path}\n")
                if self.audio_path:
                    f.write(f"Audio: {self.audio_path}\n")
                if self.video_path:
                    f.write(f"Video: {self.video_path}\n")
                
                confidence = self.get_confidence_level()
                results = self.get_results()
                
                f.write(f"Confidence Level: {confidence:.2%}\n\n")

                f.write("RESULTS:\n")
                f.write("--------\n")
                if results:
                    for key, value in results.items():
                        f.write(f"{key}: {value}\n")
                else:
                    f.write("No analysis results available.\n")

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
                        
                if self.video_path:
                    f.write("\nVIDEO STATISTICS:\n")
                    f.write("------------------\n")
                    vstats = self.get_video_statistics()
                    for key, value in vstats.items():
                        f.write(f"{key}: {value}\n")

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
