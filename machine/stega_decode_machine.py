# machine/stega_decode_machine.py
import os
from typing import Optional, Tuple
import hashlib
import random
import struct
import zlib
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
        self.last_error: Optional[str] = None
        self.header_info: Optional[dict] = None

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

            if not self.encryption_key or not self.encryption_key.strip():
                self.last_error = "Decryption key is required for decoding"
                print(f"Error: {self.last_error}")
                return False

            # Prepare flattened byte view of image
            flat_bytes = self.image_array.astype(np.uint8).reshape(-1)
            total_bytes = flat_bytes.size
            lsb_bits = self.lsb_bits
            total_lsb_bits = total_bytes * lsb_bits

            # Seed PRNG from key
            rng = self._rng_from_key(self.encryption_key)

            # Choose start offset within LSB bitstream with safety margin
            safety_margin = 4096  # bits reserved to ensure header fits
            if total_lsb_bits <= safety_margin:
                self.last_error = "Cover stego image is too small for header"
                print(f"Error: {self.last_error}")
                return False
            start_bit = rng.randrange(0, total_lsb_bits - safety_margin)

            # Build per-byte LSB permutation using PRNG (length == lsb_bits)
            bit_order = list(range(lsb_bits))
            rng.shuffle(bit_order)

            # Helper to yield LSB bits starting from start_bit
            def lsb_bit_iter():
                current_bit_index = start_bit
                while current_bit_index < total_lsb_bits:
                    byte_index = current_bit_index // lsb_bits
                    within_byte = current_bit_index % lsb_bits
                    # Map within-byte position through permutation
                    bit_pos = bit_order[within_byte]
                    byte_value = int(flat_bytes[byte_index])
                    yield (byte_value >> bit_pos) & 1
                    current_bit_index += 1

            bit_iter = lsb_bit_iter()

            # Utilities to read from bit iterator
            def read_bits(num_bits: int) -> int:
                value = 0
                for _ in range(num_bits):
                    try:
                        b = next(bit_iter)
                    except StopIteration:
                        raise ValueError("Unexpected end of bitstream while reading bits")
                    value = (value << 1) | (b & 1)
                return value

            def read_bytes_exact(num_bytes: int) -> bytes:
                out = bytearray()
                for _ in range(num_bytes):
                    out.append(read_bits(8))
                return bytes(out)

            # Read and parse header (variable length)
            # Header: magic(4), ver(1), lsb(1), length(4), fname_len(1), fname(N), crc32(4)
            # Read fixed portion: magic(4), ver(1), lsb(1)
            fixed = read_bytes_exact(4 + 1 + 1)

            if fixed[:4] != b'STGA':
                self.last_error = "Magic bytes mismatch. Wrong key or not a stego image."
                print(f"Error: {self.last_error}")
                return False

            version = fixed[4]
            header_lsb_bits = fixed[5]

            if header_lsb_bits != lsb_bits:
                self.last_error = f"LSB bits mismatch (header {header_lsb_bits} != selected {lsb_bits})"
                print(f"Error: {self.last_error}")
                return False

            header_start_offset = None
            if version == 2:
                # start_offset(8), length(4), fname_len(1)
                rest = read_bytes_exact(8 + 4 + 1)
                header_start_offset = struct.unpack('>Q', rest[:8])[0]
                payload_length = struct.unpack('>I', rest[8:12])[0]
                filename_len = rest[12]
            elif version == 1:
                # length(4), fname_len(1)
                rest = read_bytes_exact(4 + 1)
                payload_length = struct.unpack('>I', rest[:4])[0]
                filename_len = rest[4]
            else:
                self.last_error = f"Unsupported header version: {version}"
                print(f"Error: {self.last_error}")
                return False

            if filename_len > 100:
                self.last_error = "Unreasonable filename length in header"
                print(f"Error: {self.last_error}")
                return False

            filename_bytes = read_bytes_exact(filename_len) if filename_len else b''
            try:
                suggested_filename = filename_bytes.decode('utf-8') if filename_bytes else ''
            except Exception:
                suggested_filename = ''

            crc32_bytes = read_bytes_exact(4)
            expected_crc32 = struct.unpack('>I', crc32_bytes)[0]

            # Now read payload
            if payload_length > (total_lsb_bits // 8):
                self.last_error = "Payload length from header exceeds plausible capacity"
                print(f"Error: {self.last_error}")
                return False

            payload = read_bytes_exact(payload_length)

            actual_crc32 = zlib.crc32(payload) & 0xFFFFFFFF
            if actual_crc32 != expected_crc32:
                self.last_error = "CRC32 mismatch. Wrong key or corrupted stego."
                print(f"Error: {self.last_error}")
                return False

            # Decide output path
            output_path = self.output_path
            if suggested_filename:
                try:
                    base_dir = os.path.dirname(self.output_path) if self.output_path else ''
                    if base_dir and os.path.isdir(base_dir):
                        output_path = os.path.join(base_dir, suggested_filename)
                    else:
                        output_path = suggested_filename
                except Exception:
                    pass

            with open(output_path, 'wb') as f:
                f.write(payload)

            # Persist the actual output path used so the GUI can reference it
            self.output_path = output_path

            # Try to populate extracted_data as text preview if decodable
            try:
                self.extracted_data = payload.decode('utf-8')
            except Exception:
                self.extracted_data = f"Binary payload extracted ({len(payload)} bytes) -> {output_path}"

            print(f"Steganography decoding completed successfully!")
            print(f"Extracted data saved to: {output_path}")
            # Record header info for UI/reporting
            self.header_info = {
                'version': int(version),
                'lsb_bits': int(header_lsb_bits),
                'start_offset': int(header_start_offset) if header_start_offset is not None else None,
                'computed_start': int(start_bit),
                'payload_length': int(payload_length),
                'filename': suggested_filename,
                'crc32_ok': actual_crc32 == expected_crc32
            }
            return True

        except Exception as e:
            self.last_error = f"Decoding failed: {e}"
            print(f"Error during steganography decoding: {e}")
            return False

    def _rng_from_key(self, key: str) -> random.Random:
        """Create a deterministic RNG from the provided key string."""
        key_bytes = key.encode('utf-8')
        digest = hashlib.sha256(key_bytes).digest()
        seed_int = int.from_bytes(digest[:8], 'big')
        return random.Random(seed_int)

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
        self.last_error = None
        self.header_info = None
        print("StegaDecodeMachine cleaned up")

    def get_last_error(self) -> Optional[str]:
        return self.last_error

    def get_header_info(self) -> Optional[dict]:
        return self.header_info
