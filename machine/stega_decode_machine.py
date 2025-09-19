# machine/stega_decode_machine.py
import os
from typing import Optional, Tuple
from datetime import datetime

import numpy as np
from PIL import Image
from PyPDF2 import PdfReader

from machine.stega_spec import (
    FLAG_PAYLOAD_ENCRYPTED,
    HEADER_MAGIC,
    MAX_FILENAME_LEN,
    crc32,
    decrypt_payload,
    perm_for_lsb_bits,
    rng_from_key_and_filename,
    unpack_header,
)


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
        self.last_error = None
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
            # Ensure directory exists, create if needed
            output_dir = os.path.dirname(output_path)
            if output_dir:
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)

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
        is_valid, error_msg = self.validate_inputs()
        if not is_valid:
            print(f"Validation failed: {error_msg}")
            return False

        try:
            if not self.encryption_key or not self.encryption_key.strip():
                self.last_error = "Decryption key is required for decoding"
                print(f"Error: {self.last_error}")
                return False

            flat_bytes = self.image_array.astype(np.uint8).reshape(-1)
            if flat_bytes.size == 0:
                self.last_error = "Stego image is empty"
                print(f"Error: {self.last_error}")
                return False

            key = self.encryption_key.strip()

            class BitReader:
                def __init__(self, data: np.ndarray, lsb_bits: int, start_bit: int, bit_order: list[int]):
                    self.data = data
                    self.lsb_bits = lsb_bits
                    self.total_bits = data.size * lsb_bits
                    self.index = start_bit
                    self.order = bit_order

                def read_bit(self) -> int:
                    if self.index >= self.total_bits:
                        raise ValueError("Ran out of LSB bits while reading stream")
                    byte_index = self.index // self.lsb_bits
                    within_byte = self.index % self.lsb_bits
                    bit_pos = self.order[within_byte]
                    byte_value = int(self.data[byte_index])
                    bit = (byte_value >> bit_pos) & 1
                    self.index += 1
                    return bit

                def read_bits(self, count: int) -> int:
                    value = 0
                    for _ in range(count):
                        value = (value << 1) | self.read_bit()
                    return value

                def read_bytes(self, count: int) -> bytes:
                    return bytes(self.read_bits(8) for _ in range(count))

                @property
                def position(self) -> int:
                    return self.index

            header_bytes = None
            header_info = None
            header_bits_consumed = 0
            for candidate_bits in range(1, 9):
                identity = list(range(candidate_bits))
                reader = BitReader(flat_bytes, candidate_bits, 0, identity)
                buf = bytearray()
                try:
                    buf.extend(reader.read_bytes(4))
                    if bytes(buf[:4]) != HEADER_MAGIC:
                        continue
                    buf.append(reader.read_bits(8))
                    buf.append(reader.read_bits(8))
                    buf.append(reader.read_bits(8))
                    buf.extend(reader.read_bytes(8))
                    buf.extend(reader.read_bytes(4))
                    nonce_len = reader.read_bits(8)
                    buf.append(nonce_len)
                    buf.extend(reader.read_bytes(nonce_len))
                    fname_len = reader.read_bits(8)
                    buf.append(fname_len)
                    buf.extend(reader.read_bytes(fname_len))
                    buf.extend(reader.read_bytes(4))
                    candidate_header = unpack_header(bytes(buf))
                    if candidate_header['lsb_bits'] != candidate_bits:
                        continue
                    header_bytes = bytes(buf)
                    header_info = candidate_header
                    header_bits_consumed = reader.position
                    break
                except ValueError:
                    continue
                except Exception:
                    continue

            if header_info is None or header_bytes is None:
                self.last_error = "Failed to locate STGA header. Wrong key or unsupported format."
                print(f"Error: {self.last_error}")
                return False

            lsb_bits = header_info['lsb_bits']
            self.lsb_bits = lsb_bits
            total_lsb_bits = flat_bytes.size * lsb_bits

            start_bit = header_info['start_bit_offset']
            payload_length = header_info['payload_len']
            if start_bit < header_bits_consumed:
                self.last_error = "Header indicates payload overlaps reserved header region"
                print(f"Error: {self.last_error}")
                return False
            if start_bit + payload_length * 8 > total_lsb_bits:
                self.last_error = "Payload length exceeds cover capacity"
                print(f"Error: {self.last_error}")
                return False

            rng = rng_from_key_and_filename(key, b'')
            perm = perm_for_lsb_bits(rng, lsb_bits)

            payload_reader = BitReader(flat_bytes, lsb_bits, start_bit, perm)
            payload_cipher = payload_reader.read_bytes(payload_length)

            filename = header_info.get('filename', '')
            fname_bytes = filename.encode('utf-8')[:MAX_FILENAME_LEN]
            flags = header_info.get('flags', 0)
            nonce = header_info.get('nonce', b'')

            if flags & FLAG_PAYLOAD_ENCRYPTED:
                if not nonce:
                    self.last_error = "Encrypted payload missing nonce"
                    print(f"Error: {self.last_error}")
                    return False
                payload_plain = decrypt_payload(key, nonce, payload_cipher, fname_bytes)
            else:
                payload_plain = payload_cipher

            expected_crc = header_info.get('crc32', 0)
            actual_crc = crc32(payload_plain)
            if actual_crc != expected_crc:
                self.last_error = "CRC32 mismatch. Wrong key or corrupted stego."
                print(f"Error: {self.last_error}")
                return False

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            def build_final_name(suggested: str) -> str:
                if suggested:
                    return f"{timestamp}.{suggested}"
                return f"{timestamp}_extracted.bin"

            suggested_filename = filename
            if self.output_path and self.output_path.strip():
                if os.path.isdir(self.output_path):
                    base_dir = self.output_path
                    final_name = build_final_name(suggested_filename)
                    output_path = os.path.join(base_dir, final_name)
                else:
                    chosen_dir = os.path.dirname(self.output_path)
                    chosen_base = os.path.basename(self.output_path)
                    name, ext = os.path.splitext(chosen_base)
                    if not ext:
                        candidate_dir = os.path.join(chosen_dir, chosen_base) if chosen_dir else chosen_base
                        base_dir = candidate_dir if candidate_dir else os.getcwd()
                        if not os.path.exists(base_dir):
                            os.makedirs(base_dir, exist_ok=True)
                        final_name = build_final_name(suggested_filename)
                        output_path = os.path.join(base_dir, final_name)
                    else:
                        output_path = self.output_path
            elif suggested_filename:
                stego_dir = os.path.dirname(self.stego_image_path) or ''
                final_name = build_final_name(suggested_filename)
                output_path = os.path.join(stego_dir, final_name)
            else:
                output_path = os.path.join(os.getcwd(), f"{timestamp}_extracted_payload.bin")

            with open(output_path, 'wb') as f:
                f.write(payload_plain)

            self.output_path = output_path

            try:
                self.extracted_data = payload_plain.decode('utf-8')
            except Exception:
                self.extracted_data = None
                try:
                    if output_path.lower().endswith('.pdf'):
                        with open(output_path, 'rb') as pf:
                            reader = PdfReader(pf)
                            texts = []
                            for page in reader.pages:
                                try:
                                    t = page.extract_text() or ''
                                except Exception:
                                    t = ''
                                if t:
                                    texts.append(t)
                            preview = "\n".join(texts).strip()
                            if preview:
                                self.extracted_data = preview
                except Exception:
                    pass
                if self.extracted_data is None:
                    self.extracted_data = f"Binary payload extracted ({len(payload_plain)} bytes) -> {output_path}"

            print("Steganography decoding completed successfully!")
            print(f"Extracted data saved to: {output_path}")
            self.header_info = {
                'version': int(header_info.get('version', 0)),
                'lsb_bits': int(lsb_bits),
                'start_offset': int(start_bit),
                'payload_length': int(payload_length),
                'filename': suggested_filename,
                'crc32_ok': True,
                'encrypted': bool(flags & FLAG_PAYLOAD_ENCRYPTED),
                'flags': int(flags),
                'nonce': nonce.hex() if nonce else '',
                'header_bits': header_bits_consumed,
            }
            return True

        except Exception as e:
            self.last_error = f"Decoding failed: {e}"
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
        self.last_error = None
        self.header_info = None
        print("StegaDecodeMachine cleaned up")

    def get_last_error(self) -> Optional[str]:
        return self.last_error

    def get_header_info(self) -> Optional[dict]:
        return self.header_info
