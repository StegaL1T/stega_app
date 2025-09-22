import os
from typing import Optional, Tuple
import hashlib
import random
import struct
import zlib
from PIL import Image
from datetime import datetime
from PyPDF2 import PdfReader
import numpy as np
import wave

class StegaDecodeMachine:
    """
    Handles all steganography decoding operations and business logic.
    Separated from GUI to maintain clean architecture.
    """

    def __init__(self):
        """Initialize the steganography decoding machine"""
        self.stego_image_path: Optional[str] = None
        self.stego_audio_path: Optional[str] = None
        self.lsb_bits: int = 1
        self.encryption_key: Optional[str] = None
        self.output_path: Optional[str] = None

        # Internal state for media
        self.stego_image: Optional[Image.Image] = None
        self.image_array: Optional[np.ndarray] = None
        self.audio_data: Optional[np.ndarray] = None
        
        # Internal state for results
        self.extracted_data: Optional[str] = None
        self.last_error: Optional[str] = None
        self.header_info: Optional[dict] = None

        print("StegaDecodeMachine initialized")

    def set_stego_image(self, image_path: str) -> bool:
        """
        Set the steganographic image and validate it.
        """
        try:
            self._reset_media()
            if not os.path.exists(image_path):
                self.last_error = f"Steganographic image not found: {image_path}"
                print(f"Error: {self.last_error}")
                return False

            self.stego_image = Image.open(image_path)
            self.stego_image_path = image_path
            
            if self.stego_image.mode != 'RGB':
                self.stego_image = self.stego_image.convert('RGB')
                
            self.image_array = np.array(self.stego_image)
            self.last_error = None
            
            print(f"Steganographic image loaded: {image_path}")
            print(f"Image dimensions: {self.image_array.shape}")
            return True

        except Exception as e:
            self.last_error = f"Error loading steganographic image: {e}"
            print(f"Error: {self.last_error}")
            return False

    def set_stego_audio(self, audio_path: str) -> bool:
        """
        Set the steganographic audio file and validate it.
        """
        try:
            self._reset_media()
            if not os.path.exists(audio_path):
                self.last_error = f"Steganographic audio not found: {audio_path}"
                print(f"Error: {self.last_error}")
                return False
                
            with wave.open(audio_path, 'rb') as audio_file:
                n_frames = audio_file.getnframes()
                samp_width = audio_file.getsampwidth()
                
                raw_data = audio_file.readframes(n_frames)
                
                # Using float32 for wider compatibility with audio samples
                if samp_width == 1:
                    dtype = np.uint8
                elif samp_width == 2:
                    dtype = np.int16
                elif samp_width == 4:
                    dtype = np.int32
                else:
                    self.last_error = f"Unsupported sample width: {samp_width} bytes"
                    print(f"Error: {self.last_error}")
                    return False
                    
                self.audio_data = np.frombuffer(raw_data, dtype=dtype)
                self.stego_audio_path = audio_path
                self.last_error = None
                
            print(f"Steganographic audio loaded: {audio_path}")
            print(f"Audio samples: {len(self.audio_data)}")
            return True

        except Exception as e:
            self.last_error = f"Error loading steganographic audio: {e}"
            print(f"Error: {self.last_error}")
            return False

    def _reset_media(self):
        """Clears all loaded media data."""
        self.stego_image = None
        self.image_array = None
        self.stego_image_path = None
        self.audio_data = None
        self.stego_audio_path = None

    def set_lsb_bits(self, bits: int) -> bool:
        # ... (existing code, no changes needed)
        self.lsb_bits = bits
        print(f"LSB bits set to: {bits}")
        return True

    def set_encryption_key(self, key: str) -> None:
        # ... (existing code, no changes needed)
        self.encryption_key = key if key.strip() else None
        if self.encryption_key:
            print(f"Decryption key set: {len(self.encryption_key)} characters")
        else:
            print("Decryption key cleared")

    def set_output_path(self, output_path: str) -> bool:
        # ... (existing code, no changes needed)
        self.output_path = output_path
        print(f"Output path set: {output_path}")
        return True

    def validate_inputs(self) -> Tuple[bool, str]:
        """
        Validate all inputs before processing.
        """
        if not self.stego_image_path and not self.stego_audio_path:
            return False, "Steganographic media not selected"
            
        if self.stego_image_path and self.image_array is None:
            return False, "Steganographic image not loaded properly"
            
        if self.stego_audio_path and self.audio_data is None:
            return False, "Steganographic audio not loaded properly"

        if not self.output_path:
            return False, "Output path not specified"

        return True, "All inputs valid"

    def extract_message(self) -> bool:
        """
        Perform the steganography decoding operation.
        """
        is_valid, error_msg = self.validate_inputs()
        if not is_valid:
            self.last_error = error_msg
            print(f"Validation failed: {error_msg}")
            return False
            
        # Determine which media to decode from
        if self.stego_image_path:
            media_array = self.image_array
        elif self.stego_audio_path:
            media_array = self.audio_data
        else:
            self.last_error = "No steganographic media loaded."
            return False

        return self._extract_from_media(media_array)
        
    def _extract_from_media(self, media_array: np.ndarray) -> bool:
        """
        Performs the core decoding logic on a NumPy array,
        abstracting image vs. audio.
        """
        try:
            print("Starting steganography decoding process...")

            if not self.encryption_key or not self.encryption_key.strip():
                self.last_error = "Decryption key is required for decoding"
                print(f"Error: {self.last_error}")
                return False

            flat_bytes = media_array.astype(np.uint8).reshape(-1)
            total_bytes = flat_bytes.size
            lsb_bits = self.lsb_bits
            total_lsb_bits = total_bytes * lsb_bits

            # Seed PRNG from key
            rng = self._rng_from_key(self.encryption_key)

            # Choose start offset within LSB bitstream with safety margin
            safety_margin = 4096  # bits reserved to ensure header fits
            if total_lsb_bits <= safety_margin:
                self.last_error = "Cover media is too small for header"
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
                    if byte_index >= len(flat_bytes):
                        break
                    within_byte = current_bit_index % lsb_bits
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

            # Read and parse header
            # Header: magic(4), ver(1), lsb(1), ...
            fixed = read_bytes_exact(4 + 1 + 1)
            
            if fixed[:4] != b'STGA':
                self.last_error = "Magic bytes mismatch. Wrong key or not a stego file."
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
                rest = read_bytes_exact(8 + 4 + 1)
                header_start_offset = struct.unpack('>Q', rest[:8])[0]
                payload_length = struct.unpack('>I', rest[8:12])[0]
                filename_len = rest[12]
            elif version == 1:
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

            # Decide output path and save payload
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # ... (the rest of your original save-file logic) ...
            
            def build_final_name(suggested: str) -> str:
                if suggested:
                    return f"{timestamp}.{suggested}"
                return f"{timestamp}_extracted.bin"

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
                stego_dir = os.path.dirname(self.stego_image_path if self.stego_image_path else self.stego_audio_path) or ''
                final_name = build_final_name(suggested_filename)
                output_path = os.path.join(stego_dir, final_name)
            else:
                output_path = os.path.join(os.getcwd(), f"{timestamp}_extracted_payload.bin")


            with open(output_path, 'wb') as f:
                f.write(payload)

            self.output_path = output_path
            
            try:
                self.extracted_data = payload.decode('utf-8')
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
                    self.extracted_data = f"Binary payload extracted ({len(payload)} bytes) -> {output_path}"

            print(f"Steganography decoding completed successfully!")
            print(f"Extracted data saved to: {output_path}")

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
        # ... (existing code, no changes needed)
        key_bytes = key.encode('utf-8')
        digest = hashlib.sha256(key_bytes).digest()
        seed_int = int.from_bytes(digest[:8], 'big')
        return random.Random(seed_int)

    def get_image_info(self) -> dict:
        # ... (existing code, no changes needed)
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
        # ... (existing code, no changes needed)
        return self.extracted_data

    def cleanup(self):
        # ... (existing code, no changes needed)
        self.stego_image = None
        self.image_array = None
        self.audio_data = None
        self.stego_image_path = None
        self.stego_audio_path = None
        self.extracted_data = None
        self.last_error = None
        self.header_info = None
        print("StegaDecodeMachine cleaned up")

    def get_last_error(self) -> Optional[str]:
        # ... (existing code, no changes needed)
        return self.last_error

    def get_header_info(self) -> Optional[dict]:
        # ... (existing code, no changes needed)
        return self.header_info