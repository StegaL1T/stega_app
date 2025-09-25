import os
from typing import List, Optional, Tuple
from datetime import datetime

import numpy as np
from PIL import Image
from datetime import datetime
from PyPDF2 import PdfReader
import wave

from machine.stega_spec import (
    FLAG_PAYLOAD_ENCRYPTED,
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
        self.last_output_path: Optional[str] = None

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
                print(
                    f"[DEBUG] First 32 bytes of raw audio: {raw_data[:32].hex()}")
                self.audio_data = np.frombuffer(raw_data, dtype=np.uint8)
                print(
                    f"[DEBUG] np.uint8 audio_data shape: {self.audio_data.shape}, first 32 bytes: {self.audio_data[:32].tolist()}")
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
            self.last_output_path = None
            print("Starting steganography decoding process...")

            if not self.encryption_key or not self.encryption_key.strip():
                self.last_error = "Decryption key is required for decoding"
                print(f"Error: {self.last_error}")
                return False

            if not (1 <= self.lsb_bits <= 8):
                self.last_error = f"Invalid LSB bits setting: {self.lsb_bits}"
                print(f"Error: {self.last_error}")
                return False

            flat_bytes = media_array.astype(np.uint8).reshape(-1)
            total_bytes = flat_bytes.size
            lsb_bits = self.lsb_bits
            total_lsb_bits = total_bytes * lsb_bits

            if total_lsb_bits == 0:
                self.last_error = "Cover media contains no data to decode"
                print(f"Error: {self.last_error}")
                return False

            identity_order = list(range(lsb_bits))

            class BitCursor:
                def __init__(self, start_bit: int, order: List[int]):
                    self.pos = start_bit
                    self.order = order

                def _read_one(self) -> int:
                    if self.pos >= total_lsb_bits:
                        raise ValueError("Unexpected end of bitstream")
                    byte_index = self.pos // lsb_bits
                    within_byte = self.pos % lsb_bits
                    bit_pos = self.order[within_byte]
                    byte_value = int(flat_bytes[byte_index])
                    self.pos += 1
                    return (byte_value >> bit_pos) & 1

                def read_bits(self, num_bits: int) -> int:
                    value = 0
                    for _ in range(num_bits):
                        value = (value << 1) | self._read_one()
                    return value

                def read_bytes(self, num_bytes: int) -> bytes:
                    return bytes(self.read_bits(8) for _ in range(num_bytes))

            preview_cursor = BitCursor(0, identity_order)
            preview_bits = []
            preview_limit = min(total_lsb_bits, 8 * 16)
            for _ in range(preview_limit):
                try:
                    preview_bits.append(preview_cursor.read_bits(1))
                except ValueError:
                    break
            preview_bytes = bytearray()
            for i in range(0, len(preview_bits), 8):
                byte = 0
                for bit in preview_bits[i:i + 8]:
                    byte = (byte << 1) | (bit & 1)
                preview_bytes.append(byte)
            print(
                f"[DEBUG] First 16 bytes from LSB stream: {preview_bytes.hex()}")

            header_cursor = BitCursor(0, identity_order)
            header_bytes = bytearray()

            def read_header_bytes(count: int) -> bytes:
                data = header_cursor.read_bytes(count)
                header_bytes.extend(data)
                return data

            def read_header_byte() -> int:
                value = header_cursor.read_bits(8)
                header_bytes.append(value)
                return value

            try:
                read_header_bytes(4)  # magic
                read_header_byte()    # version
                read_header_byte()    # flags
                read_header_byte()    # lsb bits
                read_header_bytes(8)  # start offset
                read_header_bytes(4)  # payload length
                nonce_len = read_header_byte()
                read_header_bytes(nonce_len)  # nonce
                filename_len = read_header_byte()
                read_header_bytes(filename_len)  # filename
                read_header_bytes(4)  # crc32
            except ValueError as exc:
                self.last_error = f"Unexpected end of bitstream while reading header: {exc}"
                print(f"Error: {self.last_error}")
                return False

            print(f"[DEBUG] Raw header bytes extracted: {list(header_bytes)}")

            try:
                header_info = unpack_header(bytes(header_bytes))
            except Exception as exc:
                self.last_error = f"Invalid header: {exc}"
                print(f"Error: {self.last_error}")
                return False

            version = header_info["version"]
            flags = header_info["flags"]
            header_lsb_bits = header_info["lsb_bits"]
            start_bit = header_info["start_bit_offset"]
            payload_length = header_info["payload_len"]
            nonce = header_info["nonce"]
            filename = header_info["filename"]
            expected_crc32 = header_info["crc32"]
            header_bits_consumed = header_cursor.pos

            if header_lsb_bits != self.lsb_bits:
                self.last_error = f"LSB bits mismatch (header {header_lsb_bits} != selected {self.lsb_bits})"
                print(f"Error: {self.last_error}")
                return False

            if start_bit < header_bits_consumed:
                self.last_error = "Header reports start offset within header region"
                print(f"Error: {self.last_error}")
                return False

            payload_bits = payload_length * 8
            if payload_bits == 0:
                self.last_error = "Payload length from header is zero"
                print(f"Error: {self.last_error}")
                return False

            if start_bit + payload_bits > total_lsb_bits:
                self.last_error = "Payload length from header exceeds media capacity"
                print(f"Error: {self.last_error}")
                return False

            filename_bytes = filename.encode('utf-8')[:MAX_FILENAME_LEN]
            rng = rng_from_key_and_filename(self.encryption_key, b"")
            perm = perm_for_lsb_bits(rng, header_lsb_bits)
            payload_cursor = BitCursor(start_bit, perm)

            try:
                payload_encrypted = payload_cursor.read_bytes(payload_length)
            except ValueError as exc:
                self.last_error = f"Unexpected end of bitstream while reading payload: {exc}"
                print(f"Error: {self.last_error}")
                return False

            is_encrypted = bool(flags & FLAG_PAYLOAD_ENCRYPTED)
            if is_encrypted:
                if not nonce:
                    self.last_error = "Encrypted payload missing nonce in header"
                    print(f"Error: {self.last_error}")
                    return False
                payload_plain = decrypt_payload(
                    self.encryption_key, nonce, payload_encrypted, filename_bytes)
            else:
                payload_plain = payload_encrypted

            actual_crc32 = crc32(payload_plain)
            print(
                f"[DEBUG] CRC32 expected: 0x{expected_crc32:08X}, actual: 0x{actual_crc32:08X}")
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

            requested_path = (self.output_path or '').strip()
            suggested_filename = filename
            base_dir = ''
            explicit_file = ''

            if requested_path:
                if os.path.isdir(requested_path):
                    base_dir = requested_path
                else:
                    candidate_dir = os.path.dirname(requested_path)
                    base_name = os.path.basename(requested_path)
                    name, ext = os.path.splitext(base_name)
                    if ext:
                        explicit_file = requested_path
                        base_dir = candidate_dir or os.getcwd()
                    else:
                        base_dir = os.path.join(
                            candidate_dir, base_name) if base_name else candidate_dir
                        if base_dir and not os.path.exists(base_dir):
                            os.makedirs(base_dir, exist_ok=True)

            if explicit_file:
                output_path = explicit_file
            else:
                if not base_dir:
                    stego_source = self.stego_image_path if self.stego_image_path else self.stego_audio_path
                    base_dir = os.path.dirname(
                        stego_source) if stego_source else ''
                    if not base_dir:
                        base_dir = os.path.join(
                            os.getcwd(), 'extracted_payloads')
                    if not os.path.exists(base_dir):
                        os.makedirs(base_dir, exist_ok=True)
                final_name = build_final_name(suggested_filename)
                output_path = os.path.join(base_dir, final_name)

            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            with open(output_path, 'wb') as f:
                f.write(payload)

            self.last_output_path = output_path

            if requested_path:
                if os.path.isdir(requested_path):
                    self.output_path = requested_path
                else:
                    preferred_dir = os.path.dirname(
                        requested_path) or os.path.dirname(output_path)
                    self.output_path = preferred_dir
            else:
                self.output_path = os.path.dirname(output_path)

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
                'start_offset': int(start_bit),
                'header_bits': int(header_bits_consumed),
                'payload_length': int(payload_length),
                'filename': suggested_filename,
                'crc32_ok': True,
                'encrypted': is_encrypted,
                'flags': int(flags),
                'nonce': nonce.hex() if nonce else '',
                'computed_start': int(start_bit),
            }
            return True

        except Exception as e:
            self.last_error = f"Decoding failed: {e}"
            print(f"Error during steganography decoding: {e}")
            return False

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

    def get_last_output_path(self) -> Optional[str]:
        """Return the full path of the most recent decode output."""
        return self.last_output_path

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
        self.last_output_path = None
        print("StegaDecodeMachine cleaned up")

    def get_last_error(self) -> Optional[str]:
        # ... (existing code, no changes needed)
        return self.last_error

    def get_header_info(self) -> Optional[dict]:
        # ... (existing code, no changes needed)
        return self.header_info
