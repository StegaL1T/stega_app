"""StegaEncodeMachine (Encoder core)
=================================

Shared encoder/decoder contract (LOCKED):
 - Header layout (big-endian):
   Magic: 4 bytes = b"STGA"
   Version: 1 byte = 0x02
   Flags: 1 byte (bit 0 = payload encrypted)
   LSB bits used: 1 byte in range 1..8
   Start bit offset: 8 bytes (uint64) identifying the LSB bit index within the flattened cover stream
   Payload length: 4 bytes (uint32)
   Nonce length: 1 byte (0..32), then nonce bytes (used when encryption flag is set)
   Header bits occupy the leading portion of the flattened LSB stream; payload start offsets are always >= header size.
   Filename length: 1 byte (0..100), then filename bytes (UTF-8)
   CRC32 of plaintext payload: 4 bytes (uint32)

PRNG & seeding rules:
 - User key must be numeric (string of digits in GUI). Encoder/decoder derive the same seed:
   seed = int.from_bytes(SHA256(str(key).encode('utf-8')).digest()[:8], 'big')
 - PRNG = Python random.Random(seed)
 - Start offset is chosen deterministically via rng.randrange(0, total_lsb_bits - required_bits + 1) when not user-selected
 - Per-byte bit order permutation is generated via Fisher-Yates on [0..(lsb_bits-1)] using the same PRNG
 - Encryption derives an independent XOR keystream using the filename and nonce for context

Traversal and flattening choices (decoder must mirror):
 - Images: convert to 24-bit RGB if not already. Flatten bytes row-major with per-pixel channel order RGB.
 - Audio: interleaved frames as stored; sample width 8/16/24/32 supported; only LSBs touched.
 - Video: decoded to RGB24 frames; flattened in frame order.

Capacity math:
 - capacity_bits_image = width * height * channels * lsb_bits (channels=3 for RGB)
 - available_payload_bytes = floor((capacity_bits - header_bits_from_start)/8)
   Note: when embedding from a start offset, only bits from start..end are usable.
"""

# machine/stega_encode_machine.py
import os
import io
import math
import wave
import tempfile
import base64
import json
import subprocess
import shutil
from typing import Optional, Tuple, List, Dict, Any

try:
    import cv2
except ImportError:  # pragma: no cover - optional dependency for video handling
    cv2 = None
from PIL import Image
import numpy as np
from pathlib import Path

from crypto_honey import HoneyFormatError, he_encrypt
from machine.stega_spec import (
    FLAG_PAYLOAD_ENCRYPTED,
    HeaderMeta,
    MAX_FILENAME_LEN,
    crc32,
    encrypt_payload,
    generate_nonce,
    pack_header,
    perm_for_lsb_bits,
    rng_from_key_and_filename,
    unpack_header,
)


# Typed exceptions for GUI to catch
class StegaError(Exception):
    pass


class ValidationError(StegaError):
    pass


class CapacityError(StegaError):
    pass


class UnsupportedFormatError(StegaError):
    pass


class StegaEncodeMachine:
    """
    Handles all steganography encoding operations and business logic.
    Separated from GUI to maintain clean architecture.
    """

    def __init__(self):
        """Initialize the steganography encoding machine"""
        self.cover_image_path = None
        self.cover_audio_path = None
        # Payload (bytes). If text was provided, this is UTF-8 bytes of that text.
        self.payload_data = None
        self.payload_text: Optional[str] = None
        self.payload_file_path = None
        self.lsb_bits = 1
        # Numeric key (string of digits enforced at GUI); stored as string
        self.encryption_key = None
        self.encrypt_payload = True
        self.output_path = None

        # Honey / transformation state
        self.honey_enabled = False
        self.honey_universe = 'office_msgs'
        self._encrypt_preference = True
        self._last_transform_info: Optional[Dict[str, Any]] = None

        # Internal state
        self.cover_image = None
        self.image_array = None
        self.last_embed_info: Optional[Dict[str, Any]] = None
        self.last_error: Optional[str] = None

        print("StegaEncodeMachine initialized")

    def set_cover_audio(self, wav_path: str) -> bool:
        """Set the cover audio (WAV PCM) and validate it."""
        try:
            if not os.path.exists(wav_path):
                print(f"Error: Cover WAV not found: {wav_path}")
                return False
            with wave.open(wav_path, 'rb') as wf:
                comptype = wf.getcomptype()
                sampwidth = wf.getsampwidth()
                if comptype not in ('NONE', 'not compressed'):
                    print(f"Error: Unsupported WAV compression: {comptype}")
                    return False
                if sampwidth not in (1, 2, 3, 4):
                    print(
                        f"Error: Unsupported WAV sample width: {sampwidth} bytes")
                    return False
            self.cover_audio_path = wav_path
            print(f"Cover audio loaded: {wav_path}")
            return True
        except Exception as e:
            print(f"Error loading cover audio: {e}")
            return False

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
        trimmed = text.strip()
        if not trimmed:
            print("Error: Payload text cannot be empty")
            return False

        self.payload_text = trimmed
        self.payload_data = trimmed.encode('utf-8')
        self.payload_file_path = None  # Clear file path if text is set
        self._invalidate_transform_cache()

        print(f"Payload text set: {len(self.payload_data)} bytes")
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

            # Store raw bytes
            self.payload_data = file_data
            self.payload_file_path = file_path
            self.payload_text = None
            self._invalidate_transform_cache()

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
        # Only accept digits; GUI should validate but we enforce here too
        key = key.strip()
        self.encryption_key = key if key and key.isdigit() else None
        if self.encryption_key:
            print(f"Key set: {self.encryption_key}")
        else:
            print("Key cleared or invalid (numeric required)")

    def set_encrypt_payload(self, enabled: bool) -> None:
        """Toggle XOR payload encryption."""
        self._encrypt_preference = bool(enabled)
        if self.honey_enabled:
            self.encrypt_payload = False
        else:
            self.encrypt_payload = self._encrypt_preference
        state = 'enabled' if self.encrypt_payload else 'disabled'
        print(f"Payload encryption {state}")
        self._invalidate_transform_cache()

    def _invalidate_transform_cache(self) -> None:
        """Reset cached payload transform metadata."""
        self._last_transform_info = None

    def set_honey_enabled(self, enabled: bool) -> None:
        """Enable or disable the Honey Encryption demo mode."""
        self.honey_enabled = bool(enabled)
        if self.honey_enabled:
            self.encrypt_payload = False
        else:
            self.encrypt_payload = bool(self._encrypt_preference)
        state = 'enabled' if self.honey_enabled else 'disabled'
        print(f"Honey encryption {state}")
        self._invalidate_transform_cache()

    def set_honey_universe(self, universe: str) -> None:
        """Record the active Honey Encryption universe."""
        name = (universe or '').strip()
        if not name:
            raise ValidationError("Honey universe cannot be empty")
        self.honey_universe = name
        self._invalidate_transform_cache()

    def get_payload_lengths(self) -> Tuple[int, int]:
        """Return (raw_len, effective_len) for the current payload."""
        raw_len = len(self.payload_data) if self.payload_data else 0
        effective_len = self.get_effective_payload_length()
        return raw_len, effective_len

    def get_effective_payload_length(self) -> int:
        """Return the number of bytes that will actually be embedded."""
        if not self.payload_data:
            return 0
        if self.honey_enabled:
            try:
                universe_bytes = self.honey_universe.encode('ascii')
            except UnicodeEncodeError:
                return 0
            return 6 + 4 + 8 + 1 + len(universe_bytes) + 4
        return len(self.payload_data)

    def get_transform_summary(self) -> Dict[str, Any]:
        """Expose a summary of the most recent payload transform."""
        if self._last_transform_info is not None:
            return dict(self._last_transform_info)
        raw_len, effective_len = self.get_payload_lengths()
        if self.honey_enabled:
            return {
                'mode': 'honey',
                'raw_len': raw_len,
                'embed_len': effective_len,
                'universe': self.honey_universe,
            }
        mode = 'xor' if self.encrypt_payload else 'plain'
        return {'mode': mode, 'raw_len': raw_len, 'embed_len': effective_len}

    def _prepare_payload_for_embedding(self, payload_bytes: bytes, key: str, fname_bytes: bytes) -> Dict[str, Any]:
        """Apply the configured transform (plain/xor/honey) to the payload."""
        summary = {
            'mode': 'plain',
            'raw_len': len(payload_bytes),
            'embed_len': len(payload_bytes),
        }
        flags = 0
        nonce = b''
        payload_for_embed = payload_bytes
        crc_source = payload_bytes

        if self.honey_enabled:
            if self.payload_file_path:
                raise ValidationError("Honey mode supports short text payloads only.")
            if self.payload_text is not None:
                text_value = self.payload_text
            else:
                try:
                    text_value = payload_bytes.decode('utf-8')
                except UnicodeDecodeError as exc:
                    raise ValidationError("Honey mode requires UTF-8 text payloads.") from exc
            try:
                honey_blob = he_encrypt(text_value, int(key), self.honey_universe)
            except (ValueError, HoneyFormatError) as exc:
                raise ValidationError(f"Honey encryption failed: {exc}") from exc
            payload_for_embed = honey_blob
            crc_source = honey_blob
            summary.update({
                'mode': 'honey',
                'embed_len': len(honey_blob),
                'universe': self.honey_universe,
            })
        elif self.encrypt_payload:
            nonce = generate_nonce()
            payload_for_embed = encrypt_payload(key, nonce, payload_bytes, fname_bytes)
            flags = FLAG_PAYLOAD_ENCRYPTED
            summary['mode'] = 'xor'

        self._last_transform_info = dict(summary)
        return {
            'payload': payload_for_embed,
            'flags': flags,
            'nonce': nonce,
            'crc_payload': crc_source,
            'summary': summary,
        }

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

        if self.honey_enabled and self.payload_file_path:
            return False, "Honey mode supports text payloads only"

        max_capacity = (self.image_array.size * self.lsb_bits) // 8
        payload_size = self.get_effective_payload_length()

        if payload_size > max_capacity:
            return False, f"Payload too large. Max capacity: {max_capacity} bytes, Payload: {payload_size} bytes"

        return True, "All inputs valid"

    # ====================
    # Public operations
    # ====================

    def hide_message(self, start_xy: Optional[Tuple[int, int]] = None) -> bool:
        """
        Perform the steganography encoding operation

        Returns:
            bool: True if successful, False otherwise
        """
        # Validate inputs
        is_valid, error_msg = self.validate_inputs()
        if not is_valid:
            print(f"Validation failed: {error_msg}")
            return False

        self.last_error = None
        try:
            if not self.encryption_key:
                raise ValidationError("Numeric key is required")

            if self.cover_image is None or self.image_array is None:
                raise ValidationError("Cover image not loaded")

            filename = os.path.basename(
                self.payload_file_path) if self.payload_file_path else "payload.txt"
            stego_img, header = self.encode_image(
                self.cover_image_path, self.payload_data, filename, self.lsb_bits, self.encryption_key, start_xy=start_xy
            )

            # Save result
            if not self.output_path:
                raise ValidationError("Output path not specified")
            stego_img.save(self.output_path)

            print("Steganography encoding completed successfully!")
            print(f"Output saved to: {self.output_path}")
            print(f"Header: {header}")

            return True

        except StegaError as e:
            self.last_error = str(e)
            print(f"Error during steganography encoding: {e}")
            return False
        except Exception as e:
            self.last_error = str(e)
            print(f"Unexpected error during encoding: {e}")
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

    def get_last_error(self) -> Optional[str]:
        return self.last_error

    def cleanup(self):
        """Clean up resources when machine is destroyed"""
        self.cover_image = None
        self.image_array = None
        self.last_error = None
        print("StegaEncodeMachine cleaned up")

    # ====================
    # Flatteners & capacity
    # ====================

    @staticmethod
    def _flatten_image_bytes(img: Image.Image) -> Tuple[np.ndarray, Tuple[int, int, int]]:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        arr = np.array(img, dtype=np.uint8)
        h, w, c = arr.shape
        flat = arr.reshape(-1)
        return flat, (h, w, c)

    @staticmethod
    def estimate_capacity_bits_for_image(img: Image.Image, lsb_bits: int) -> int:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        arr = np.array(img, dtype=np.uint8)
        return arr.size * lsb_bits

    def estimate_capacity_bits(self, cover_path: str, cover_type: str, lsb_bits: int, start_pixel_or_sample: Optional[Tuple[int, int] | int] = None) -> int:
        if cover_type == 'image':
            img = Image.open(cover_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            total_bits = self.estimate_capacity_bits_for_image(img, lsb_bits)
            if start_pixel_or_sample is None:
                return total_bits
            # start_pixel_or_sample = (x,y)
            x, y = start_pixel_or_sample  # type: ignore
            w, h = img.size
            channels = 3
            pixel_index = y * w + x
            start_bit = pixel_index * channels * lsb_bits
            return max(0, total_bits - start_bit)
        elif cover_type == 'audio':
            # WAV PCM only
            with wave.open(cover_path, 'rb') as wf:
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()  # bytes per sample (1,2,3,4)
                n_frames = wf.getnframes()
                total_bytes = n_frames * n_channels * sampwidth
                total_bits = total_bytes * lsb_bits
                if start_pixel_or_sample is None:
                    return total_bits
                # start_pixel_or_sample is int: start_sample index
                start_sample = int(start_pixel_or_sample)  # type: ignore
                if start_sample < 0:
                    start_sample = 0
                bytes_per_frame = n_channels * sampwidth
                start_byte = min(start_sample * bytes_per_frame, total_bytes)
                return max(0, total_bits - start_byte * lsb_bits)
        elif cover_type == 'video':
            if cv2 is None:
                raise UnsupportedFormatError(
                    "OpenCV is required for video support")
            cap = cv2.VideoCapture(cover_path)
            if not cap.isOpened():
                raise UnsupportedFormatError(
                    f"Cannot open video: {cover_path}")
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            channels = 3
            total_bits = frame_count * width * height * channels * lsb_bits
            if start_pixel_or_sample is None:
                return total_bits
            # start_pixel_or_sample is (frame_idx, x, y)
            f, x, y = start_pixel_or_sample  # type: ignore
            if f < 0:
                f = 0
            if x < 0:
                x = 0
            if y < 0:
                y = 0
            pixel_index_across = f * (width * height) + y * width + x
            start_bit = pixel_index_across * channels * lsb_bits
            return max(0, total_bits - start_bit)
        else:
            raise UnsupportedFormatError(
                f"Unsupported cover type: {cover_type}")

    # ====================
    # Embedding core
    # ====================

    @staticmethod
    def _embed_bits(flat_bytes: np.ndarray, lsb_bits: int, start_bit: int, bit_order: List[int], data_bytes: bytes) -> int:
        """Embed data_bytes starting at start_bit. Returns next bit index after embedding."""
        total_lsb_bits = flat_bytes.size * lsb_bits

        def bit_stream():
            for byte in data_bytes:
                for i in range(7, -1, -1):
                    yield (byte >> i) & 1

        idx = start_bit
        for bit in bit_stream():
            if idx >= total_lsb_bits:
                raise CapacityError('Insufficient capacity while embedding')
            byte_index = idx // lsb_bits
            within_byte = idx % lsb_bits
            bit_pos = bit_order[within_byte]
            value = int(flat_bytes[byte_index])
            value = (value & ~(1 << bit_pos)) | ((bit & 1) << bit_pos)
            flat_bytes[byte_index] = value
            idx += 1
        return idx

    # ====================
    # Encoders
    # ====================

    def encode_image(self, cover_image_path: str, payload_bytes: bytes, filename: str, lsb_bits: int, key: str, start_xy: Optional[Tuple[int, int]] = None) -> Tuple[Image.Image, Dict[str, Any]]:
        if not (1 <= lsb_bits <= 8):
            raise ValidationError(f"LSB bits must be 1..8, got {lsb_bits}")
        if not key or not key.isdigit():
            raise ValidationError("Key must be numeric and non-empty")
        if not os.path.exists(cover_image_path):
            raise ValidationError(f"Cover image not found: {cover_image_path}")

        img = Image.open(cover_image_path)
        flat, (h, w, c) = self._flatten_image_bytes(img)
        total_lsb_bits = flat.size * lsb_bits

        fname_bytes = filename.encode('utf-8')[:MAX_FILENAME_LEN]
        rng = rng_from_key_and_filename(key, b'')
        perm = perm_for_lsb_bits(rng, lsb_bits)
        transform = self._prepare_payload_for_embedding(payload_bytes, key, fname_bytes)
        payload_for_embed = transform['payload']
        flags = transform['flags']
        nonce = transform['nonce']
        payload_crc = crc32(transform['crc_payload'])
        payload_len = len(payload_for_embed)
        header_placeholder = HeaderMeta(
            lsb_bits=lsb_bits,
            start_bit_offset=0,
            payload_len=payload_len,
            filename=filename,
            crc32=payload_crc,
            flags=flags,
            nonce=nonce,
        )
        header_bytes = pack_header(header_placeholder)
        header_bits = len(header_bytes) * 8
        payload_bits = len(payload_for_embed) * 8
        required_bits = header_bits + payload_bits
        if required_bits > total_lsb_bits:
            raise CapacityError(
                f"Not enough capacity: need {required_bits} bits, have {total_lsb_bits} bits")

        if start_xy is not None:
            x, y = start_xy
            if not (0 <= x < w and 0 <= y < h):
                raise ValidationError(
                    f"Start (x,y) out of bounds: ({x},{y}) for image {w}x{h}")
            pixel_index = y * w + x
            start_bit = pixel_index * c * lsb_bits
            if start_bit < header_bits:
                raise CapacityError(
                    "Selected start position overlaps header region")
            if start_bit + payload_bits > total_lsb_bits:
                raise CapacityError(
                    "Selected start position too late for payload")
        else:
            start_bit = rng.randrange(
                header_bits, total_lsb_bits - payload_bits + 1)

        header_actual = HeaderMeta(
            lsb_bits=lsb_bits,
            start_bit_offset=start_bit,
            payload_len=payload_len,
            filename=filename,
            crc32=payload_crc,
            flags=flags,
            nonce=nonce,
        )
        header_bytes = pack_header(header_actual)
        assert len(header_bytes) * \
            8 == header_bits, "Header size changed unexpectedly"

        identity_order = list(range(lsb_bits))
        self._embed_bits(flat, lsb_bits, 0, identity_order, header_bytes)
        self._embed_bits(flat, lsb_bits, start_bit, perm, payload_for_embed)

        stego_arr = flat.reshape((h, w, c))
        stego_img = Image.fromarray(stego_arr, mode='RGB')

        parsed = unpack_header(header_bytes)
        if parsed['crc32'] != payload_crc:
            raise StegaError("Header CRC mismatch after pack/unpack")

        self.last_embed_info = {
            'perm': perm,
            'start_bit': start_bit,
            'header': parsed,
            'lsb_bits': lsb_bits,
            'filename': filename,
            'image_shape': (h, w, c),
            'flags': flags,
            'nonce': nonce.hex() if nonce else '',
            'encrypted': bool(flags & FLAG_PAYLOAD_ENCRYPTED),
            'crc32': payload_crc,
            'transform': self.get_transform_summary(),
            'honey_enabled': self.honey_enabled,
        }

        return stego_img, parsed

    def encode_audio(self, cover_wav_path: str, payload_bytes: bytes, filename: str, lsb_bits: int, key: str, start_sample: Optional[int] = None) -> bytes:
        if not (1 <= lsb_bits <= 8):
            raise ValidationError(f"LSB bits must be 1..8, got {lsb_bits}")
        if not key or not key.isdigit():
            raise ValidationError("Key must be numeric and non-empty")
        if not os.path.exists(cover_wav_path):
            raise ValidationError(f"Cover WAV not found: {cover_wav_path}")

        with wave.open(cover_wav_path, 'rb') as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            comptype = wf.getcomptype()
            compname = wf.getcompname()
            if comptype not in ('NONE', 'not compressed'):
                raise UnsupportedFormatError(
                    f"Unsupported WAV compression: {comptype} ({compname})")
            if sampwidth not in (1, 2, 3, 4):
                raise UnsupportedFormatError(
                    f"Unsupported sample width: {sampwidth} bytes")
            frames = wf.readframes(n_frames)
            params = wf.getparams()

        print(f"[DEBUG] First 32 bytes of raw audio: {frames[:32].hex()}")
        flat = np.frombuffer(frames, dtype=np.uint8).copy()
        print(
            f"[DEBUG] np.uint8 flat shape: {flat.shape}, first 32 bytes: {flat[:32].tolist()}")
        total_lsb_bits = flat.size * lsb_bits

        fname_bytes = filename.encode('utf-8')[:MAX_FILENAME_LEN]
        rng = rng_from_key_and_filename(key, b'')
        perm = perm_for_lsb_bits(rng, lsb_bits)

        flags = 0
        nonce = b''
        payload_for_embed = payload_bytes
        if self.encrypt_payload:
            nonce = generate_nonce()
            payload_for_embed = encrypt_payload(
                key, nonce, payload_bytes, fname_bytes)
            flags |= FLAG_PAYLOAD_ENCRYPTED

        payload_crc = crc32(payload_bytes)
        header_placeholder = HeaderMeta(
            lsb_bits=lsb_bits,
            start_bit_offset=0,
            payload_len=len(payload_bytes),
            filename=filename,
            crc32=payload_crc,
            flags=flags,
            nonce=nonce,
        )
        header_bytes = pack_header(header_placeholder)
        header_bits = len(header_bytes) * 8
        payload_bits = len(payload_for_embed) * 8
        required_bits = header_bits + payload_bits
        if required_bits > total_lsb_bits:
            raise CapacityError(
                f"Not enough capacity: need {required_bits} bits, have {total_lsb_bits} bits")

        bytes_per_frame = n_channels * sampwidth
        if start_sample is not None:
            if start_sample < 0:
                start_sample = 0
            start_byte = start_sample * bytes_per_frame
            if start_byte >= flat.size:
                raise CapacityError(
                    "Selected start sample beyond audio length")
            start_bit = start_byte * lsb_bits
            if start_bit < header_bits:
                raise CapacityError(
                    "Selected start sample overlaps header region")
            if start_bit + payload_bits > total_lsb_bits:
                raise CapacityError(
                    "Selected start position too late for payload")
        else:
            start_bit = rng.randrange(
                header_bits, total_lsb_bits - payload_bits + 1)

        header_actual = HeaderMeta(
            lsb_bits=lsb_bits,
            start_bit_offset=start_bit,
            payload_len=len(payload_bytes),
            filename=filename,
            crc32=payload_crc,
            flags=flags,
            nonce=nonce,
        )
        header_bytes = pack_header(header_actual)
        assert len(header_bytes) * \
            8 == header_bits, "Header size changed unexpectedly"

        identity_order = list(range(lsb_bits))
        self._embed_bits(flat, lsb_bits, 0, identity_order, header_bytes)
        self._embed_bits(flat, lsb_bits, start_bit, perm, payload_for_embed)

        buf = io.BytesIO()
        with wave.open(buf, 'wb') as ww:
            ww.setparams(params)
            ww.writeframes(flat.tobytes())
        audio_bytes = buf.getvalue()

        self.last_embed_info = {
            'perm': perm,
            'start_bit': start_bit,
            'header': unpack_header(header_bytes),
            'lsb_bits': lsb_bits,
            'filename': filename,
            'audio_info': {
                'channels': n_channels,
                'sample_rate': framerate,
                'sampwidth_bytes': sampwidth,
                'frames': n_frames,
            },
            'flags': flags,
            'nonce': nonce.hex() if nonce else '',
            'encrypted': bool(flags & FLAG_PAYLOAD_ENCRYPTED),
            'crc32': payload_crc,
            'transform': self.get_transform_summary(),
            'honey_enabled': self.honey_enabled,
        }

        return audio_bytes

    # ====================
    # ====================
    # Video helpers
    # ====================

    @staticmethod
    def _split_message_for_frames(message: str, frame_count: int) -> List[str]:
        if frame_count <= 0:
            raise ValueError("Frame count must be positive")
        chunk_size = math.ceil(len(message) / frame_count)
        if chunk_size <= 0:
            chunk_size = len(message)
        return [message[i:i + chunk_size] for i in range(0, len(message), chunk_size)]

    @staticmethod
    def _extract_frames_to_directory(video_path: str, target_dir: Path) -> float:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise UnsupportedFormatError(f"Cannot open video: {video_path}")
        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        index = 0
        while True:
            success, frame = cap.read()
            if not success:
                break
            frame_path = target_dir / f"{index:06d}.png"
            cv2.imwrite(str(frame_path), frame)
            index += 1
        cap.release()
        if index == 0:
            raise UnsupportedFormatError("Video has no frames")
        return float(fps)

    @staticmethod
    def _extract_audio_track(video_path: str, temp_dir: Path) -> Optional[Path]:
        ffmpeg = shutil.which('ffmpeg')
        if not ffmpeg:
            return None
        audio_path = temp_dir / "audio.wav"
        cmd = [
            ffmpeg, '-y', '-hide_banner', '-loglevel', 'error',
            '-i', video_path,
            '-vn',
            '-acodec', 'pcm_s16le',
            str(audio_path),
        ]
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if result.returncode != 0:
            return None
        return audio_path if audio_path.exists() else None

    @staticmethod
    def _assemble_frames_with_ffmpeg(frames_dir: Path, fps: float, audio_path: Optional[Path], output_path: str) -> str:
        ffmpeg = shutil.which('ffmpeg')
        if not ffmpeg:
            raise UnsupportedFormatError(
                "ffmpeg is required to assemble video frames")
        pattern = f"{frames_dir.as_posix()}/%06d.png"
        # Important: place encoding options AFTER all inputs to avoid ffmpeg
        # interpreting them as input options for the following input (audio).
        cmd = [
            ffmpeg, '-y', '-hide_banner', '-loglevel', 'error',
            # Image sequence input (controls input framerate for the image2 demuxer)
            '-framerate', f"{fps:.6f}",
            '-i', pattern,
        ]
        if audio_path and audio_path.exists():
            cmd.extend(['-i', str(audio_path)])
        # Output encoding options
        cmd.extend([
            '-c:v', 'png',
            '-pix_fmt', 'rgb24',
        ])
        if audio_path and audio_path.exists():
            cmd.extend(['-c:a', 'pcm_s16le', '-shortest'])
        cmd.append(output_path)
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if result.returncode != 0:
            detail = result.stderr.decode(errors='ignore').strip()
            raise UnsupportedFormatError(
                f"ffmpeg failed to assemble video: {detail}")
        return output_path

    def encode_video(self, cover_video_path: str, payload_bytes: bytes, filename: str, lsb_bits: int, key: str, start_fxy: Optional[Tuple[int, int, int]] = None, out_path: Optional[str] = None) -> str:
        if not os.path.exists(cover_video_path):
            raise ValidationError(f"Cover video not found: {cover_video_path}")
        if self.honey_enabled:
            raise ValidationError("Honey Encryption demo is available for image and audio payloads only right now.")

        temp_dir = Path(tempfile.mkdtemp(prefix="stego_video_"))
        frames_dir = temp_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        try:
            fps = self._extract_frames_to_directory(
                cover_video_path, frames_dir)
            audio_path = self._extract_audio_track(cover_video_path, temp_dir)

            payload_kind = 'file' if self.payload_file_path else 'text'
            safe_filename = filename or (
                Path(self.payload_file_path).name if self.payload_file_path else 'payload.bin')
            # Build inner JSON that describes the payload
            inner = {
                'filename': safe_filename,
                'kind': payload_kind,
                'payload': base64.b64encode(payload_bytes).decode('ascii'),
            }
            inner_json = json.dumps(inner, ensure_ascii=True).encode('utf-8')

            envelope: dict
            nonce: bytes | None = None
            if self.encrypt_payload and key and key.isdigit():
                # Encrypt the inner JSON and wrap with nonce + ciphertext
                nonce = generate_nonce()
                ct = encrypt_payload(
                    key, nonce, inner_json, context=b'video-json')
                envelope = {
                    'v': 1,
                    'enc': True,
                    'alg': 'xor-s256',
                    'b': int(lsb_bits),
                    'nonce': base64.b64encode(nonce).decode('ascii'),
                    'ct': base64.b64encode(ct).decode('ascii'),
                }
            else:
                # No encryption: store base64 of the inner JSON as plaintext
                envelope = {
                    'v': 1,
                    'enc': False,
                    'b': int(lsb_bits),
                    'pt': base64.b64encode(inner_json).decode('ascii'),
                }
            message = json.dumps(envelope, ensure_ascii=True)

            frame_files = sorted(frames_dir.glob('*.png'))
            total_frames = len(frame_files)
            # If a start frame is provided, embed the whole message into that one frame for robustness
            start_frame = 0
            if start_fxy is not None:
                sf, _, _ = start_fxy
                if 0 <= sf < total_frames:
                    start_frame = sf
            if start_fxy is not None:
                segments = [message]
                if start_frame >= total_frames:
                    raise CapacityError(
                        'Selected start frame is beyond the end of the video')
                frame_index = start_frame
                frame_path = frames_dir / f"{frame_index:06d}.png"
                secret = lsb.hide(str(frame_path), segments[0])
                secret.save(str(frame_path))
            else:
                segments = self._split_message_for_frames(
                    message, total_frames)
                if len(segments) > total_frames:
                    raise CapacityError(
                        'Video does not have enough frames to store the payload')
                # Embed sequentially from frame 0
                for idx, segment in enumerate(segments):
                    frame_index = idx
                    frame_path = frames_dir / f"{frame_index:06d}.png"
                    secret = lsb.hide(str(frame_path), segment)
                    secret.save(str(frame_path))

            cover_root = os.path.splitext(cover_video_path)[0]
            target_path = out_path or f"{cover_root}_stego.avi"
            assembled = self._assemble_frames_with_ffmpeg(
                frames_dir, fps, audio_path, target_path)

            self.last_embed_info = {
                'filename': safe_filename,
                'payload_kind': payload_kind,
                'payload_length': len(payload_bytes),
                'frames': total_frames,
                'start_frame': start_frame,
                'segments': len(segments),
                'output': assembled,
                'encrypted': bool(self.encrypt_payload and key and key.isdigit()),
                'nonce': (nonce.hex() if (nonce is not None) else ''),
            }
            self.output_path = os.path.dirname(assembled)
            return assembled
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # Helper for GUI

    def get_audio_info(self, wav_path: str) -> Dict[str, Any]:
        with wave.open(wav_path, 'rb') as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            duration = n_frames / framerate if framerate else 0.0
            return {
                'channels': n_channels,
                'sample_rate': framerate,
                'sampwidth_bits': sampwidth * 8,
                'frames': n_frames,
                'duration': duration,
            }

    # ====================
    # Visualization helpers
    # ====================

    @staticmethod
    def lsb_plane_image_from_path(image_path: str, bit_index: int = 0) -> Image.Image:
        """Return an RGB image visualizing the selected bit plane (default LSB) as white/black."""
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        arr = np.array(img, dtype=np.uint8)
        # Extract bit plane across all channels
        plane = ((arr >> bit_index) & 1) * 255
        plane = plane.astype(np.uint8)
        return Image.fromarray(plane, mode='RGB')
