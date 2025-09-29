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
        self.sensitivity_level: str = "ultra"  # Default to ultra-sensitive for maximum detection

        # Analysis results
        self.results: Dict = {}
        self.statistics: Dict = {}
        self.confidence_level: float = 0.0

        print("VideoSteganalysisMachine initialized")

    def set_sensitivity_level(self, level: str):
        """Set the sensitivity level for analysis"""
        self.sensitivity_level = level.lower()
        self.current_sensitivity = level  # Store for report generation
        print(f"Video sensitivity level set to: {self.sensitivity_level}")

    def get_sensitivity_thresholds(self) -> Dict[str, float]:
        """Get sensitivity thresholds based on current level
        
        Sensitivity levels explained:
        - ultra: Detects even subtle LSB modifications (high false positive rate expected)
        - medium: Balanced detection with reasonable false positive rate
        - low: Conservative detection, only flags obvious steganography
        """
        thresholds = {
            "ultra": {
                "lsb_frame": 0.3,        # 30% combined score threshold - catches subtle LSB anomalies
                "lsb_ratio": 0.15,       # 15% suspicious frame ratio - very sensitive
                "comprehensive": 0.2      # 20% weighted voting - flags almost everything
            },
            "medium": {
                "lsb_frame": 0.65,       # 65% combined score threshold - more conservative for practical use
                "lsb_ratio": 0.4,        # 40% suspicious frame ratio
                "comprehensive": 0.6      # 60% weighted voting - requires stronger evidence
            },
            "low": {
                "lsb_frame": 0.7,        # 70% combined score threshold - conservative
                "lsb_ratio": 0.5,        # 50% suspicious frame ratio
                "comprehensive": 0.6      # 60% weighted voting
            }
        }
        return thresholds.get(self.sensitivity_level, thresholds["medium"])

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
        """Perform LSB analysis on video frames using Chi-square test and LSB distribution analysis."""
        start_time = time.time()
        print("Performing Video LSB analysis...")

        suspicious_frames = 0
        frame_scores = []
        
        for frame in self.video_frames[::max(1, len(self.video_frames)//50)]:  # sample frames
            # Convert to grayscale for LSB analysis
            if len(frame.shape) == 3:
                gray_frame = np.mean(frame, axis=2).astype(np.uint8)
            else:
                gray_frame = frame
            
            # Extract LSBs
            lsbs = gray_frame & 1
            
            # Chi-square test for LSB randomness
            # Count LSB=0 and LSB=1
            lsb_0_count = np.sum(lsbs == 0)
            lsb_1_count = np.sum(lsbs == 1)
            total_pixels = lsb_0_count + lsb_1_count
            
            if total_pixels > 0:
                # Expected counts for random distribution
                expected = total_pixels / 2
                
                # Chi-square statistic
                chi_square = ((lsb_0_count - expected) ** 2 + (lsb_1_count - expected) ** 2) / expected
                
                # Normalize chi-square to 0-1 range (higher = more suspicious)
                # Chi-square > 3.84 indicates significant deviation from randomness (p < 0.05)
                chi_square_normalized = min(chi_square / 10.0, 1.0)  # Cap at 1.0
                
                # LSB ratio analysis
                lsb_ratio = lsb_1_count / total_pixels
                # Extreme ratios are suspicious (too far from 0.5)
                ratio_deviation = abs(lsb_ratio - 0.5) * 2  # Scale to 0-1
                
                # Combine chi-square and ratio analysis
                combined_score = (chi_square_normalized + ratio_deviation) / 2
                frame_scores.append(combined_score)
                
                # Determine if frame is suspicious based on sensitivity
                thresholds = self.get_sensitivity_thresholds()
                is_suspicious = combined_score > thresholds["lsb_frame"]
                
                if is_suspicious:
                    suspicious_frames += 1
            else:
                frame_scores.append(0)

        # Configurable frame analysis based on sensitivity level
        total_sampled_frames = len(frame_scores)
        suspicious_ratio = suspicious_frames / max(total_sampled_frames, 1)
        thresholds = self.get_sensitivity_thresholds()
        suspicious = suspicious_ratio > thresholds["lsb_ratio"]
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.results = {
            'method': 'Video LSB Analysis',
            'frames_analyzed': len(self.video_frames),
            'suspicious_frames': suspicious_frames,
            'suspicious_ratio': suspicious_ratio,
            'avg_deviation': np.mean(frame_scores) if frame_scores else 0,
            'max_deviation': max(frame_scores) if frame_scores else 0,
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
        # Adjust thresholds based on sensitivity level
        thresholds = self.get_sensitivity_thresholds()
        
        if self.sensitivity_level == "ultra":
            # Ultra-sensitive: catch subtle motion anomalies
            unusual_motion = sum(1 for d in diffs if abs(d - avg_diff) > avg_diff * 0.8)
            extreme_motion = sum(1 for d in diffs if abs(d - avg_diff) > 1.5 * std_diff)
            suspicious = unusual_motion > len(diffs) * 0.05 and extreme_motion > len(diffs) * 0.02
        elif self.sensitivity_level == "medium":
            # Medium: balanced approach
            unusual_motion = sum(1 for d in diffs if abs(d - avg_diff) > avg_diff * 1.5)
            extreme_motion = sum(1 for d in diffs if abs(d - avg_diff) > 2.5 * std_diff)
            suspicious = unusual_motion > len(diffs) * 0.08 and extreme_motion > len(diffs) * 0.03
        else:  # low
            # Low: conservative approach
            unusual_motion = sum(1 for d in diffs if abs(d - avg_diff) > avg_diff * 2.0)
            extreme_motion = sum(1 for d in diffs if abs(d - avg_diff) > 3.0 * std_diff)
            suspicious = unusual_motion > len(diffs) * 0.1 and extreme_motion > len(diffs) * 0.05

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
        # Adjust weights based on sensitivity level
        if self.sensitivity_level == "ultra":
            # Ultra-sensitive: emphasize LSB analysis for subtle detection
            method_weights = {
                'video_lsb_analysis': 0.6,      # Higher weight for subtle LSB detection
                'video_frame_analysis': 0.3,    # Medium weight
                'video_motion_analysis': 0.1    # Lower weight but still considered
            }
        elif self.sensitivity_level == "medium":
            # Medium: balanced approach
            method_weights = {
                'video_lsb_analysis': 0.4,      # Balanced weight
                'video_frame_analysis': 0.4,    # Balanced weight
                'video_motion_analysis': 0.2    # Lower weight
            }
        else:  # low
            # Low: emphasize frame analysis for obvious steganography
            method_weights = {
                'video_lsb_analysis': 0.3,      # Lower weight
                'video_frame_analysis': 0.5,    # Higher weight for obvious changes
                'video_motion_analysis': 0.2    # Lower weight
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
        
        # Configurable video comprehensive thresholds based on sensitivity level
        thresholds = self.get_sensitivity_thresholds()
        overall_suspicious = (weighted_score / max(total_weight, 0.1)) > thresholds["comprehensive"]

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
