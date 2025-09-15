# machine/stega_decode_machine.py
import os
from typing import Optional, Tuple
from PIL import Image
import numpy as np


class StegaDecodeMachine:
    """
    Handles all steganography decoding operations and business logic.
    Separated from GUI to maintain clean architecture.
    """

    def __init__(self):
        """Initialize the steganography decoding machine"""
        self.stego_image_path: Optional[str] = None
        self.lsb_bits: int = 1
        self.encryption_key: Optional[str] = None
        self.output_path: Optional[str] = None

        # Internal state
        self.stego_image: Optional[Image.Image] = None
        self.image_array: Optional[np.ndarray] = None
        self.extracted_data: Optional[str] = None

        print("StegaDecodeMachine initialized")

    def set_stego_image(self, image_path: str) -> bool:
        """
        Set the steganographic image and validate it

        Args:
            image_path: Path to the steganographic image

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(image_path):
                print(f"Error: Steganographic image not found: {image_path}")
                return False

            # Load and validate image
            self.stego_image = Image.open(image_path)
            self.stego_image_path = image_path

            # Convert to RGB if necessary
            if self.stego_image.mode != 'RGB':
                self.stego_image = self.stego_image.convert('RGB')

            # Convert to numpy array for processing
            self.image_array = np.array(self.stego_image)

            print(f"Steganographic image loaded: {image_path}")
            print(f"Image dimensions: {self.image_array.shape}")
            print(f"Image size: {self.image_array.size} pixels")

            return True

        except Exception as e:
            print(f"Error loading steganographic image: {e}")
            return False

    def set_lsb_bits(self, bits: int) -> bool:
        """
        Set the number of LSB bits to use for extraction

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
        Set the decryption key (optional)

        Args:
            key: Decryption key string
        """
        self.encryption_key = key if key.strip() else None
        if self.encryption_key:
            print(f"Decryption key set: {len(self.encryption_key)} characters")
        else:
            print("Decryption key cleared")

    def set_output_path(self, output_path: str) -> bool:
        """
        Set the output path for the extracted data

        Args:
            output_path: Path where to save the extracted data

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
        if not self.stego_image_path:
            return False, "Steganographic image not selected"

        if not self.output_path:
            return False, "Output path not specified"

        # Check if image is loaded properly
        if self.stego_image is None:
            return False, "Steganographic image not loaded properly"

        return True, "All inputs valid"

    def extract_message(self) -> bool:
        """
        Perform the steganography decoding operation

        Returns:
            bool: True if successful, False otherwise
        """
        # Validate inputs
        is_valid, error_msg = self.validate_inputs()
        if not is_valid:
            print(f"Validation failed: {error_msg}")
            return False

        try:
            print("Starting steganography decoding process...")

            # TODO: Implement actual LSB steganography extraction algorithm
            # This is where you would implement the core steganography extraction logic

            # For now, just create a placeholder extracted message
            self.extracted_data = "This is a placeholder for extracted data. The actual LSB extraction algorithm needs to be implemented."

            # Save the extracted data to file
            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write(self.extracted_data)

            print(f"Steganography decoding completed successfully!")
            print(f"Extracted data saved to: {self.output_path}")
            print(f"Extracted data: {self.extracted_data}")

            return True

        except Exception as e:
            print(f"Error during steganography decoding: {e}")
            return False

    def get_image_info(self) -> dict:
        """
        Get information about the loaded steganographic image

        Returns:
            dict: Image information
        """
        if self.stego_image is None:
            return {}

        return {
            'path': self.stego_image_path,
            'dimensions': self.image_array.shape,
            'size_pixels': self.image_array.size,
            'mode': self.stego_image.mode,
            'format': self.stego_image.format,
            'max_capacity_bytes': (self.image_array.size * self.lsb_bits) // 8
        }

    def get_extracted_data(self) -> Optional[str]:
        """
        Get the extracted data

        Returns:
            Optional[str]: The extracted data if available
        """
        return self.extracted_data

    def cleanup(self):
        """Clean up resources when machine is destroyed"""
        self.stego_image = None
        self.image_array = None
        self.extracted_data = None
        print("StegaDecodeMachine cleaned up")
