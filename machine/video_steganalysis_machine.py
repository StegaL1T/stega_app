# machine/video_steganalysis_machine.py
import os
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

    def set_video(self, video_path: str, start_sec: float = 0, end_sec: Optional[float] = None) -> bool:
        """
        Load video frames and metadata using OpenCV.
        
        Args:
            video_path: Path to the video file
            start_sec: Start time in seconds (default: 0)
            end_sec: End time in seconds (default: None for full video)
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

            # Validate time parameters
            if start_sec < 0:
                print("Error: Start time cannot be negative")
                cap.release()
                return False
                
            if end_sec is not None:
                if end_sec <= start_sec:
                    print("Error: End time must be greater than start time")
                    cap.release()
                    return False
                if end_sec > self.video_duration:
                    print(f"Error: End time ({end_sec}s) exceeds video duration ({self.video_duration:.2f}s)")
                    cap.release()
                    return False
            else:
                end_sec = self.video_duration

            # Calculate frame ranges
            start_frame = int(start_sec * self.video_fps)
            end_frame = int(end_sec * self.video_fps)
            
            # Ensure we don't exceed total frame count
            end_frame = min(end_frame, total_frame_count)
            
            print(f"Loading frames from {start_sec:.2f}s to {end_sec:.2f}s (frames {start_frame} to {end_frame})")

            # Seek to start frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            frames = []
            current_frame = start_frame
            
            # Read frames in the specified range
            while current_frame < end_frame:
                try:
                    success, frame = cap.read()
                    if not success or frame is None:
                        break
                    
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frames.append(frame_rgb)
                    current_frame += 1
                    
                except Exception as read_error:
                    print(f"Warning: Error reading frame {current_frame}: {read_error}")
                    break

            cap.release()
            
            if len(frames) == 0:
                print("Error: No frames could be read from video")
                return False
                
            self.video_frames = frames

            print(f"Video loaded: {video_path}")
            print(f"Frames loaded: {len(frames)} (from {start_sec:.2f}s to {end_sec:.2f}s), FPS: {self.video_fps}, Total duration: {self.video_duration:.2f}s")
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

            print("Video analysis completed successfully!")
            return True

        except Exception as e:
            print(f"Error during video analysis: {e}")
            return False

    def _perform_video_lsb_analysis(self):
        """Perform LSB analysis on video frames."""
        print("Performing Video LSB analysis...")

        suspicious_frames = 0
        for frame in self.video_frames[::max(1, len(self.video_frames)//50)]:  # sample frames
            r = frame[:, :, 0]
            lsb_ratio = np.mean(r & 1)
            if abs(lsb_ratio - 0.5) > 0.1:
                suspicious_frames += 1

        suspicious = suspicious_frames > 0
        self.results = {
            'method': 'Video LSB Analysis',
            'frames_analyzed': len(self.video_frames),
            'suspicious_frames': suspicious_frames,
            'suspicious_ratio': suspicious_frames / max(len(self.video_frames), 1),
            'suspicious': suspicious
        }

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
        unusual_motion = sum(1 for d in diffs if abs(d - avg_diff) > avg_diff * 0.5)

        self.results = {
            'method': 'Video Motion Analysis',
            'avg_frame_diff': float(avg_diff),
            'unusual_motion_count': unusual_motion,
            'suspicious': unusual_motion > 2
        }

    def _perform_video_comprehensive_analysis(self):
        """Run LSB + Frame Analysis and combine results."""
        print("Performing video comprehensive analysis...")

        self._perform_video_lsb_analysis()
        lsb_results = self.results.copy()

        self._perform_video_frame_analysis()
        frame_results = self.results.copy()

        suspicious = lsb_results.get('suspicious', False) or frame_results.get('suspicious', False)

        self.results = {
            'method': 'Video Comprehensive Analysis',
            'video_lsb_analysis': lsb_results,
            'video_frame_analysis': frame_results,
            'suspicious': suspicious
        }

    def _perform_video_advanced_comprehensive_analysis(self):
        """Run all video methods and weigh results."""
        print("Performing video advanced comprehensive analysis...")

        self._perform_video_lsb_analysis()
        lsb_results = self.results.copy()

        self._perform_video_frame_analysis()
        frame_results = self.results.copy()

        self._perform_video_motion_analysis()
        motion_results = self.results.copy()

        suspicious_count = sum([
            lsb_results.get('suspicious', False),
            frame_results.get('suspicious', False),
            motion_results.get('suspicious', False)
        ])

        overall_suspicious = suspicious_count >= 2

        self.results = {
            'method': 'Video Advanced Comprehensive Analysis',
            'video_lsb_analysis': lsb_results,
            'video_frame_analysis': frame_results,
            'video_motion_analysis': motion_results,
            'suspicious_methods_count': suspicious_count,
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
