# machine/steganography_machine.py
import os
from typing import Optional, Tuple
from PIL import Image
import numpy as np


class SteganographyMachine:
    """
    Handles all steganography operations and business logic.
    Separated from GUI to maintain clean architecture.
    """

    def __init__(self):
        """Initialize the steganography machine"""
        self.cover_image_path: Optional[str] = None
        self.payload_data: Optional[str] = None
        self.payload_file_path: Optional[str] = None
        self.lsb_bits: int = 1
        self.encryption_key: Optional[str] = None
        self.output_path: Optional[str] = None

        # Internal state
        self.cover_image: Optional[Image.Image] = None
        self.image_array: Optional[np.ndarray] = None

        print("SteganographyMachine initialized")

    def set_cover_image(self, image_path: str) -> bool:
        """
        Set the cover image and validate it

        Args:
            image_path: Path to the cover image

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(image_path):
                print(f"Error: Cover image not found: {image_path}")
                return False

            # Load and validate image
            self.cover_image = Image.open(image_path)
            self.cover_image_path = image_path

            # Convert to RGB if necessary
            if self.cover_image.mode != 'RGB':
                self.cover_image = self.cover_image.convert('RGB')

            # Convert to numpy array for processing
            self.image_array = np.array(self.cover_image)

            print(f"Cover image loaded: {image_path}")
            print(f"Image dimensions: {self.image_array.shape}")
            print(f"Image size: {self.image_array.size} pixels")

            return True

        except Exception as e:
            print(f"Error loading cover image: {e}")
            return False

    def set_payload_text(self, text: str) -> bool:
        """
        Set the payload text message

        Args:
            text: The secret message to hide

        Returns:
            bool: True if successful, False otherwise
        """
        if not text.strip():
            print("Error: Payload text cannot be empty")
            return False

        self.payload_data = text.strip()
        self.payload_file_path = None  # Clear file path if text is set

        print(f"Payload text set: {len(self.payload_data)} characters")
        return True

    def set_payload_file(self, file_path: str) -> bool:
        """
        Set the payload from a file

        Args:
            file_path: Path to the payload file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                print(f"Error: Payload file not found: {file_path}")
                return False

            with open(file_path, 'rb') as f:
                file_data = f.read()

            # Convert binary data to string representation
            self.payload_data = file_data.hex()  # or use base64 encoding
            self.payload_file_path = file_path

            print(f"Payload file loaded: {file_path}")
            print(f"File size: {len(file_data)} bytes")

            return True

        except Exception as e:
            print(f"Error loading payload file: {e}")
            return False

    def set_lsb_bits(self, bits: int) -> bool:
        """
        Set the number of LSB bits to use

        Args:
            bits: Number of bits (1-8)

        Returns:
            bool: True if successful, False otherwise
        """
        if not 1 <= bits <= 8:
            print(f"Error: LSB bits must be between 1 and 8, got {bits}")
            return False

        self.lsb_bits = bits
        print(f"LSB bits set to: {bits}")
        return True

    def set_encryption_key(self, key: str) -> None:
        """
        Set the encryption key (optional)

        Args:
            key: Encryption key string
        """
        self.encryption_key = key if key.strip() else None
        if self.encryption_key:
            print(f"Encryption key set: {len(self.encryption_key)} characters")
        else:
            print("Encryption key cleared")

    def set_output_path(self, output_path: str) -> bool:
        """
        Set the output path for the steganographic image

        Args:
            output_path: Path where to save the result

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                print(f"Error: Output directory does not exist: {output_dir}")
                return False

            self.output_path = output_path
            print(f"Output path set: {output_path}")
            return True

        except Exception as e:
            print(f"Error setting output path: {e}")
            return False

    def validate_inputs(self) -> Tuple[bool, str]:
        """
        Validate all inputs before processing

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not self.cover_image_path:
            return False, "Cover image not selected"

        if not self.payload_data:
            return False, "No payload data provided"

        if not self.output_path:
            return False, "Output path not specified"

        # Check if payload fits in image
        if self.cover_image is None:
            return False, "Cover image not loaded properly"

        # Calculate maximum payload capacity
        max_capacity = (self.image_array.size * self.lsb_bits) // 8
        payload_size = len(self.payload_data.encode('utf-8'))

        if payload_size > max_capacity:
            return False, f"Payload too large. Max capacity: {max_capacity} bytes, Payload: {payload_size} bytes"

        return True, "All inputs valid"

    def hide_message(self) -> bool:
        """
        Perform the steganography operation

        Returns:
            bool: True if successful, False otherwise
        """
        # Validate inputs
        is_valid, error_msg = self.validate_inputs()
        if not is_valid:
            print(f"Validation failed: {error_msg}")
            return False

        try:
            print("Starting steganography process...")

            # TODO: Implement actual LSB steganography algorithm
            # This is where you would implement the core steganography logic

            # For now, just copy the image as a placeholder
            result_image = self.cover_image.copy()

            # Save the result
            result_image.save(self.output_path)

            print(f"Steganography completed successfully!")
            print(f"Output saved to: {self.output_path}")

            return True

        except Exception as e:
            print(f"Error during steganography: {e}")
            return False

    def get_image_info(self) -> dict:
        """
        Get information about the loaded cover image

        Returns:
            dict: Image information
        """
        if self.cover_image is None:
            return {}

        return {
            'path': self.cover_image_path,
            'dimensions': self.image_array.shape,
            'size_pixels': self.image_array.size,
            'mode': self.cover_image.mode,
            'format': self.cover_image.format,
            'max_capacity_bytes': (self.image_array.size * self.lsb_bits) // 8
        }

    def cleanup(self):
        """Clean up resources when machine is destroyed"""
        self.cover_image = None
        self.image_array = None
        print("SteganographyMachine cleaned up")
