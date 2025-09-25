# machine/video_steganalysis_machine.py
import os
import time
from typing import Optional, Dict, List, Tuple
import numpy as np


class VideoSteganalysisMachine:
    """
    Handles video steganalysis operations and business logic.
    Specialized for video-based steganographic detection.
    """

    def __init__(self):
        """Initialize the video steganalysis machine"""
        # Video related state
        self.video_path: Optional[str] = None
        self.video_frames: Optional[List[np.ndarray]] = None  # List of video frames as numpy arrays
        self.video_fps: Optional[float] = None
        self.video_duration: Optional[float] = None
        self.video_width: Optional[int] = None
        self.video_height: Optional[int] = None

        # Analysis results
        self.results: Dict = {}
        self.statistics: Dict = {}
        self.confidence_level: float = 0.0

        print("VideoSteganalysisMachine initialized")

    def set_video(self, video_path: str) -> bool:
        """
        Load video frames and metadata using OpenCV.
        
        Args:
            video_path: Path to the video file
        """
        try:
            import cv2
        except ImportError:
            print("Error: OpenCV (cv2) is required for video processing. Please install it with: pip install opencv-python")
            return False

        try:
            if not os.path.exists(video_path):
                print(f"Error: Video not found: {video_path}")
                return False

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print("Error: Could not open video file")
                return False

            self.video_path = video_path
            
            # Get video properties with error handling
            try:
                self.video_fps = cap.get(cv2.CAP_PROP_FPS)
                total_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                self.video_duration = total_frame_count / self.video_fps if self.video_fps > 0 else 0
                self.video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                self.video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                # Validate video properties
                if self.video_fps <= 0 or self.video_width <= 0 or self.video_height <= 0:
                    print("Error: Invalid video properties")
                    cap.release()
                    return False
                    
            except Exception as prop_error:
                print(f"Error reading video properties: {prop_error}")
                cap.release()
                return False

            frames = []
            frames_read = 0
            
            # Read all frames from the video
            while True:
                try:
                    success, frame = cap.read()
                    if not success or frame is None:
                        break
                    
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frames.append(frame_rgb)
                    frames_read += 1
                    
                except Exception as read_error:
                    print(f"Warning: Error reading frame: {read_error}")
                    break

            cap.release()
            
            if len(frames) == 0:
                print("Error: No frames could be read from video")
                return False
                
            self.video_frames = frames

            print(f"Video loaded: {video_path}")
            print(f"Frames: {len(frames)}, FPS: {self.video_fps}, Duration: {self.video_duration:.2f}s")
            return True

        except Exception as e:
            print(f"Error loading video: {e}")
            return False

    def validate_video_inputs(self) -> Tuple[bool, str]:
        """
        Validate video inputs before analysis

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not self.video_path:
            return False, "No video selected for analysis"

        if self.video_frames is None:
            return False, "Video not loaded properly"

        return True, "Inputs valid"

    def analyze_video(self, method: str = "Video LSB Analysis") -> bool:
        """
        Perform steganalysis on the video

        Args:
            method: Analysis method name for video

        Returns:
            bool: True if successful, False otherwise
        """
        is_valid, error_msg = self.validate_video_inputs()
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
            if method == "Video LSB Analysis":
                self._perform_video_lsb_analysis()
            elif method == "Video Frame Analysis":
                self._perform_video_frame_analysis()
            elif method == "Video Motion Analysis":
                self._perform_video_motion_analysis()
            elif method == "Video Comprehensive Analysis":
                self._perform_video_comprehensive_analysis()
            elif method == "Video Advanced Comprehensive":
                self._perform_video_advanced_comprehensive_analysis()
            else:
                print(f"Unknown video analysis method: {method}")
                return False

            # Calculate overall confidence
            self._calculate_confidence()

            overall_end_time = time.time()
            overall_execution_time = overall_end_time - overall_start_time
            print(f"Video Analysis completed successfully in {overall_execution_time*1000:.2f}ms total!")
            return True

        except Exception as e:
            print(f"Error during video analysis: {e}")
            return False

    def _perform_video_lsb_analysis(self):
        """Perform LSB analysis on video frames."""
        start_time = time.time()
        print("Performing Video LSB analysis...")

        suspicious_frames = 0
        frame_deviations = []
        
        for frame in self.video_frames[::max(1, len(self.video_frames)//50)]:  # sample frames
            r = frame[:, :, 0]
            lsb_ratio = np.mean(r & 1)
            deviation = abs(lsb_ratio - 0.5)
            frame_deviations.append(deviation)
            
            # Ultra-sensitive threshold for video frames: catch very subtle steganography
            # Special case: if deviation > 2%, flag as suspicious (like your encoded image)
            if deviation > 0.025:
                suspicious_frames += 1

        # Ultra-sensitive frame analysis: catch very subtle steganography
        total_sampled_frames = len(frame_deviations)
        suspicious_ratio = suspicious_frames / max(total_sampled_frames, 1)
        suspicious = suspicious_ratio > 0.1  # Require only 10% of frames to be suspicious (down from 20%)
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.results = {
            'method': 'Video LSB Analysis',
            'frames_analyzed': len(self.video_frames),
            'suspicious_frames': suspicious_frames,
            'suspicious_ratio': suspicious_ratio,
            'avg_deviation': np.mean(frame_deviations) if frame_deviations else 0,
            'max_deviation': max(frame_deviations) if frame_deviations else 0,
            'suspicious': suspicious,
            'execution_time_ms': round(execution_time * 1000, 2)
        }
        
        print(f"Video LSB Analysis completed in {execution_time*1000:.2f}ms")

    def _perform_video_frame_analysis(self):
        """Detect anomalous frames by variance in pixel intensity."""
        print("Performing Video Frame analysis...")

        variances = [np.var(frame) for frame in self.video_frames[::max(1, len(self.video_frames)//50)]]
        mean_var = np.mean(variances)
        anomalies = sum(1 for v in variances if abs(v - mean_var) > mean_var * 0.3)

        self.results = {
            'method': 'Video Frame Analysis',
            'total_frames': len(self.video_frames),
            'anomalous_frames': anomalies,
            'frame_variance_mean': float(mean_var),
            'suspicious': anomalies > 0
        }

    def _perform_video_motion_analysis(self):
        """Check motion consistency via frame differencing."""
        print("Performing Video Motion analysis...")

        diffs = []
        for i in range(1, len(self.video_frames)):
            diff = np.mean(np.abs(self.video_frames[i].astype(np.float32) - 
                                  self.video_frames[i-1].astype(np.float32)))
            diffs.append(diff)

        avg_diff = np.mean(diffs)
        std_diff = np.std(diffs)
        
        # More sophisticated motion analysis
        # Consider both absolute differences and statistical outliers
        unusual_motion = sum(1 for d in diffs if abs(d - avg_diff) > avg_diff * 0.7)
        extreme_motion = sum(1 for d in diffs if abs(d - avg_diff) > 2 * std_diff)
        
        # Only flag as suspicious if there are both unusual and extreme motion patterns
        suspicious = unusual_motion > 3 and extreme_motion > 1

        self.results = {
            'method': 'Video Motion Analysis',
            'avg_frame_diff': float(avg_diff),
            'std_frame_diff': float(std_diff),
            'unusual_motion_count': unusual_motion,
            'extreme_motion_count': extreme_motion,
            'suspicious': suspicious
        }

    def _perform_video_comprehensive_analysis(self):
        """Run LSB + Frame Analysis and combine results."""
        start_time = time.time()
        print("Performing video comprehensive analysis...")

        self._perform_video_lsb_analysis()
        lsb_results = self.results.copy()

        self._perform_video_frame_analysis()
        frame_results = self.results.copy()

        suspicious = lsb_results.get('suspicious', False) or frame_results.get('suspicious', False)

        end_time = time.time()
        execution_time = end_time - start_time
        
        self.results = {
            'method': 'Video Comprehensive Analysis',
            'video_lsb_analysis': lsb_results,
            'video_frame_analysis': frame_results,
            'suspicious': suspicious,
            'execution_time_ms': round(execution_time * 1000, 2)
        }
        
        print(f"Video Comprehensive Analysis completed in {execution_time*1000:.2f}ms")

    def _perform_video_advanced_comprehensive_analysis(self):
        """Run all video methods and weigh results."""
        print("Performing video advanced comprehensive analysis...")

        self._perform_video_lsb_analysis()
        lsb_results = self.results.copy()

        self._perform_video_frame_analysis()
        frame_results = self.results.copy()

        self._perform_video_motion_analysis()
        motion_results = self.results.copy()

        # Weighted voting system for video advanced comprehensive analysis
        method_weights = {
            'video_lsb_analysis': 0.5,      # Highest weight - most reliable
            'video_frame_analysis': 0.3,    # Medium weight
            'video_motion_analysis': 0.2    # Lower weight - most prone to false positives
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        all_results = {
            'video_lsb_analysis': lsb_results,
            'video_frame_analysis': frame_results,
            'video_motion_analysis': motion_results
        }
        
        for method, results in all_results.items():
            if method in method_weights:
                weight = method_weights[method]
                if results.get('suspicious', False):
                    weighted_score += weight
                total_weight += weight
        
        # Ultra-sensitive video comprehensive: catch very subtle steganography
        # Lower threshold (0.15 instead of 0.3) to match image sensitivity
        overall_suspicious = (weighted_score / max(total_weight, 0.1)) > 0.15

        self.results = {
            'method': 'Video Advanced Comprehensive Analysis',
            'video_lsb_analysis': lsb_results,
            'video_frame_analysis': frame_results,
            'video_motion_analysis': motion_results,
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

    def get_video_statistics(self) -> Dict:
        """
        Get video statistics

        Returns:
            Dict: Video statistics
        """
        if self.video_frames is None:
            return {}

        return {
            'file_path': self.video_path,
            'width': self.video_width,
            'height': self.video_height,
            'fps': self.video_fps,
            'duration_seconds': self.video_duration,
            'total_frames': len(self.video_frames) if self.video_frames else 0,
            'file_size_mb': os.path.getsize(self.video_path) / (1024 * 1024) if self.video_path else 0
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
        self.video_frames = None
        self.video_path = None
        self.video_fps = None
        self.video_duration = None
        self.video_width = None
        self.video_height = None
        print("VideoSteganalysisMachine cleaned up")
