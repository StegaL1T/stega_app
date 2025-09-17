"""
StegaEncodeMachine (Encoder core)
=================================

Shared encoder/decoder contract (LOCKED):
 - Header layout (big-endian):
   Magic: 4 bytes = b"STGA"
   Version: 1 byte = 0x01
   LSB bits used: 1 byte = 1–8
   Start bit offset: 8 bytes (uint64) — index into the flattened LSB stream of the cover
   Payload length: 4 bytes (uint32)
   Filename length: 1 byte (0–100), then Filename bytes (UTF-8)
   CRC32 of payload: 4 bytes (uint32)

PRNG & seeding rules:
 - User key must be numeric (string of digits in GUI). Encoder/decoder derive the same seed:
   seed = int.from_bytes(SHA256(str(key).encode('utf-8') + filename_bytes).digest()[:8], 'big')
 - PRNG = Python random.Random(seed)
 - Start offset is chosen as rng.randrange(0, total_lsb_bits - required_bits) and written to the header
 - Per-byte bit order permutation is generated via Fisher–Yates on [0..(lsb_bits-1)] using the same PRNG

Traversal and flattening choices (decoder must mirror):
 - Images: convert to 24-bit RGB if not already. Flatten bytes row-major with per-pixel channel order RGB.
 - Audio (future): interleaved frames as stored; sample width 8/16/24/32 supported; only LSBs touched.

Capacity math:
 - capacity_bits_image = width * height * channels * lsb_bits (channels=3 for RGB)
 - available_payload_bytes = floor((capacity_bits - header_bits_from_start)/8)
   Note: when embedding from a start offset, only bits from start..end are usable.

This file focuses on image encoding to meet the acceptance goal quickly; audio helpers are stubbed with
clear exceptions and can be wired similarly.
"""

# machine/stega_encode_machine.py
import os
import struct
import zlib
import hashlib
import random
import wave
import io
import cv2
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any
from PIL import Image
import numpy as np


# Typed exceptions for GUI to catch
class StegaError(Exception):
    pass


class ValidationError(StegaError):
    pass


class CapacityError(StegaError):
    pass


class UnsupportedFormatError(StegaError):
    pass


@dataclass
class HeaderMeta:
    lsb_bits: int
    start_bit_offset: int
    payload_len: int
    filename: str
    crc32: int


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
        self.payload_file_path = None
        self.lsb_bits = 1
        # Numeric key (string of digits enforced at GUI); stored as string
        self.encryption_key = None
        self.output_path = None

        # Internal state
        self.cover_image = None
        self.image_array = None
        self.last_embed_info: Optional[Dict[str, Any]] = None

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
                    print(f"Error: Unsupported WAV sample width: {sampwidth} bytes")
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
        if not text.strip():
            print("Error: Payload text cannot be empty")
            return False

        self.payload_data = text.strip().encode('utf-8')
        self.payload_file_path = None  # Clear file path if text is set

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

        # Calculate maximum payload capacity (image only at the moment)
        max_capacity = (self.image_array.size * self.lsb_bits) // 8
        payload_size = len(self.payload_data)

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

        try:
            if not self.encryption_key:
                raise ValidationError("Numeric key is required")

            if self.cover_image is None or self.image_array is None:
                raise ValidationError("Cover image not loaded")

            filename = os.path.basename(self.payload_file_path) if self.payload_file_path else "payload.txt"
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
            print(f"Error during steganography encoding: {e}")
            return False
        except Exception as e:
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

    def cleanup(self):
        """Clean up resources when machine is destroyed"""
        self.cover_image = None
        self.image_array = None
        print("StegaEncodeMachine cleaned up")

    # ====================
    # Spec helpers
    # ====================

    @staticmethod
    def _crc32(data: bytes) -> int:
        return zlib.crc32(data) & 0xFFFFFFFF

    @staticmethod
    def _rng_from_key_and_filename(key: str, filename_bytes: bytes) -> random.Random:
        digest = hashlib.sha256(key.encode('utf-8') + filename_bytes).digest()
        seed_int = int.from_bytes(digest[:8], 'big')
        return random.Random(seed_int)

    @staticmethod
    def _perm_for_lsb_bits(rng: random.Random, lsb_bits: int) -> List[int]:
        perm = list(range(lsb_bits))
        # Fisher–Yates shuffle
        for i in range(lsb_bits - 1, 0, -1):
            j = rng.randrange(0, i + 1)
            perm[i], perm[j] = perm[j], perm[i]
        return perm

    # ====================
    # Header pack/unpack
    # ====================

    @staticmethod
    def pack_header(meta: HeaderMeta) -> bytes:
        if not (1 <= meta.lsb_bits <= 8):
            raise ValidationError(f"LSB bits must be 1..8, got {meta.lsb_bits}")
        fname_bytes = meta.filename.encode('utf-8')[:100]
        if len(fname_bytes) > 100:
            raise ValidationError("Filename too long after UTF-8 encoding")
        magic = b'STGA'
        version = 1
        header = [
            magic,
            struct.pack('>B', version),
            struct.pack('>B', meta.lsb_bits),
            struct.pack('>Q', meta.start_bit_offset),
            struct.pack('>I', meta.payload_len),
            struct.pack('>B', len(fname_bytes)),
            fname_bytes,
            struct.pack('>I', meta.crc32),
        ]
        return b''.join(header)

    @staticmethod
    def unpack_header(b: bytes) -> Dict[str, Any]:
        if len(b) < 4 + 1 + 1 + 8 + 4 + 1 + 4:
            raise ValidationError("Header too short")
        off = 0
        magic = b[off:off+4]; off += 4
        if magic != b'STGA':
            raise ValidationError("Invalid magic")
        version = b[off]; off += 1
        if version != 1:
            raise ValidationError(f"Unsupported version {version}")
        lsb_bits = b[off]; off += 1
        start_bit_offset = struct.unpack('>Q', b[off:off+8])[0]; off += 8
        payload_len = struct.unpack('>I', b[off:off+4])[0]; off += 4
        fname_len = b[off]; off += 1
        if fname_len > 100:
            raise ValidationError("Filename length invalid")
        fname = b[off:off+fname_len].decode('utf-8', errors='replace'); off += fname_len
        crc32_val = struct.unpack('>I', b[off:off+4])[0]
        return {
            'version': version,
            'lsb_bits': lsb_bits,
            'start_bit_offset': start_bit_offset,
            'payload_len': payload_len,
            'filename': fname,
            'crc32': crc32_val,
        }

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
            cap = cv2.VideoCapture(cover_path)
            if not cap.isOpened():
                raise UnsupportedFormatError(f"Cannot open video: {cover_path}")
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
            raise UnsupportedFormatError(f"Unsupported cover type: {cover_type}")

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

        fname_bytes = filename.encode('utf-8')[:100]
        rng = self._rng_from_key_and_filename(key, fname_bytes)
        perm = self._perm_for_lsb_bits(rng, lsb_bits)

        # Build header to know size, but start_bit_offset to be filled after choosing
        crc = self._crc32(payload_bytes)
        header_placeholder = HeaderMeta(lsb_bits=lsb_bits, start_bit_offset=0, payload_len=len(payload_bytes), filename=filename, crc32=crc)
        header_bytes = self.pack_header(header_placeholder)
        header_bits = len(header_bytes) * 8
        required_bits = header_bits + len(payload_bytes) * 8
        if required_bits > total_lsb_bits:
            raise CapacityError(f"Not enough capacity: need {required_bits} bits, have {total_lsb_bits} bits")

        # Compute start offset
        if start_xy is not None:
            x, y = start_xy
            if not (0 <= x < w and 0 <= y < h):
                raise ValidationError(f"Start (x,y) out of bounds: ({x},{y}) for image {w}x{h}")
            pixel_index = y * w + x
            start_bit = pixel_index * c * lsb_bits
            if start_bit + required_bits > total_lsb_bits:
                raise CapacityError("Selected start position too late for payload+header")
        else:
            # Choose via PRNG ensuring room from start to end
            start_bit = rng.randrange(0, total_lsb_bits - required_bits)

        # Rebuild header with actual start_bit_offset
        header = HeaderMeta(lsb_bits=lsb_bits, start_bit_offset=start_bit, payload_len=len(payload_bytes), filename=filename, crc32=crc)
        header_bytes = self.pack_header(header)
        assert len(header_bytes) * 8 == header_bits, "Header size changed unexpectedly"

        # Embed: header then payload
        next_bit = self._embed_bits(flat, lsb_bits, start_bit, perm, header_bytes)
        self._embed_bits(flat, lsb_bits, next_bit, perm, payload_bytes)

        # Reassemble image
        stego_arr = flat.reshape((h, w, c))
        stego_img = Image.fromarray(stego_arr, mode='RGB')

        # Quick header round-trip check
        parsed = self.unpack_header(header_bytes)
        if parsed['crc32'] != crc:
            raise StegaError("Header CRC mismatch after pack/unpack")

        # Store last embed info for GUI proof panel
        self.last_embed_info = {
            'perm': perm,
            'start_bit': start_bit,
            'header': parsed,
            'lsb_bits': lsb_bits,
            'filename': filename,
            'image_shape': (h, w, c),
        }

        return stego_img, parsed

    def encode_audio(self, cover_wav_path: str, payload_bytes: bytes, filename: str, lsb_bits: int, key: str, start_sample: Optional[int] = None) -> bytes:
        # Validate
        if not (1 <= lsb_bits <= 8):
            raise ValidationError(f"LSB bits must be 1..8, got {lsb_bits}")
        if not key or not key.isdigit():
            raise ValidationError("Key must be numeric and non-empty")
        if not os.path.exists(cover_wav_path):
            raise ValidationError(f"Cover WAV not found: {cover_wav_path}")

        # Read WAV
        with wave.open(cover_wav_path, 'rb') as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()  # bytes per sample: 1,2,3,4
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            comptype = wf.getcomptype()
            compname = wf.getcompname()
            if comptype not in ('NONE', 'not compressed'):
                raise UnsupportedFormatError(f"Unsupported WAV compression: {comptype} ({compname})")
            if sampwidth not in (1, 2, 3, 4):
                raise UnsupportedFormatError(f"Unsupported sample width: {sampwidth} bytes")
            frames = wf.readframes(n_frames)
            params = wf.getparams()

        flat = np.frombuffer(frames, dtype=np.uint8).copy()  # mutable
        total_lsb_bits = flat.size * lsb_bits

        # Build header placeholder for size
        fname_bytes = filename.encode('utf-8')[:100]
        rng = self._rng_from_key_and_filename(key, fname_bytes)
        perm = self._perm_for_lsb_bits(rng, lsb_bits)
        crc = self._crc32(payload_bytes)
        header_placeholder = HeaderMeta(lsb_bits=lsb_bits, start_bit_offset=0, payload_len=len(payload_bytes), filename=filename, crc32=crc)
        header_bytes = self.pack_header(header_placeholder)
        header_bits = len(header_bytes) * 8
        required_bits = header_bits + len(payload_bytes) * 8
        if required_bits > total_lsb_bits:
            raise CapacityError(f"Not enough capacity: need {required_bits} bits, have {total_lsb_bits} bits")

        # Compute start offset
        bytes_per_frame = n_channels * sampwidth
        if start_sample is not None:
            if start_sample < 0:
                start_sample = 0
            start_byte = start_sample * bytes_per_frame
            if start_byte >= flat.size:
                raise CapacityError("Selected start sample beyond audio length")
            start_bit = start_byte * lsb_bits
            if start_bit + required_bits > total_lsb_bits:
                raise CapacityError("Selected start position too late for payload+header")
        else:
            # Choose via PRNG ensuring room from start to end
            start_bit = rng.randrange(0, total_lsb_bits - required_bits)

        # Rebuild header with actual start
        header = HeaderMeta(lsb_bits=lsb_bits, start_bit_offset=start_bit, payload_len=len(payload_bytes), filename=filename, crc32=crc)
        header_bytes = self.pack_header(header)
        assert len(header_bytes) * 8 == header_bits, "Header size changed unexpectedly"

        # Embed header then payload into flat uint8 bytes
        next_bit = self._embed_bits(flat, lsb_bits, start_bit, perm, header_bytes)
        self._embed_bits(flat, lsb_bits, next_bit, perm, payload_bytes)

        # Write a new WAV to bytes
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as ww:
            ww.setparams(params)
            ww.writeframes(flat.tobytes())
        audio_bytes = buf.getvalue()

        # Store last embed info
        self.last_embed_info = {
            'perm': perm,
            'start_bit': start_bit,
            'header': self.unpack_header(header_bytes),
            'lsb_bits': lsb_bits,
            'filename': filename,
            'audio_info': {
                'channels': n_channels,
                'sample_rate': framerate,
                'sampwidth_bytes': sampwidth,
                'frames': n_frames,
            },
        }

        return audio_bytes

    # ====================
    # Video helpers
    # ====================

    @staticmethod
    def _iter_video_frames_rgb24(path: str) -> Tuple[List[np.ndarray], float]:
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            raise UnsupportedFormatError(f"Cannot open video: {path}")
        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        frames: List[np.ndarray] = []
        while True:
            ret, frame_bgr = cap.read()
            if not ret:
                break
            # Convert BGR->RGB
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            frames.append(frame_rgb)
        cap.release()
        if not frames:
            raise UnsupportedFormatError("Video has no frames")
        return frames, float(fps)

    @staticmethod
    def _write_video_rgb24(frames_rgb: List[np.ndarray], fps: float, out_path: str) -> None:
        h, w, _ = frames_rgb[0].shape
        # Try uncompressed AVI via DIB 'DIB '
        fourcc = cv2.VideoWriter_fourcc('D', 'I', 'B', ' ')
        writer = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
        if not writer.isOpened():
            writer.release()
            raise UnsupportedFormatError("Failed to open video writer for uncompressed AVI. Ensure a lossless RGB24 codec is available or use ffmpeg.")
        for fr in frames_rgb:
            if fr.shape[0] != h or fr.shape[1] != w:
                raise ValidationError("All frames must have identical dimensions")
            # Convert back to BGR for OpenCV writer
            bgr = cv2.cvtColor(fr, cv2.COLOR_RGB2BGR)
            writer.write(bgr)
        writer.release()

    # ====================
    # Video encoder
    # ====================

    def encode_video(self, cover_video_path: str, payload_bytes: bytes, filename: str, lsb_bits: int, key: str, start_fxy: Optional[Tuple[int, int, int]] = None, out_path: Optional[str] = None) -> str:
        if not (1 <= lsb_bits <= 8):
            raise ValidationError(f"LSB bits must be 1..8, got {lsb_bits}")
        if not key or not key.isdigit():
            raise ValidationError("Key must be numeric and non-empty")
        if not os.path.exists(cover_video_path):
            raise ValidationError(f"Cover video not found: {cover_video_path}")

        frames_rgb, fps = self._iter_video_frames_rgb24(cover_video_path)
        h, w, c = frames_rgb[0].shape
        if c != 3:
            raise UnsupportedFormatError("Expected RGB24 frames (3 channels)")

        # Flatten frames to 1D
        stacked = np.concatenate([fr.reshape(-1) for fr in frames_rgb], axis=0)
        total_lsb_bits = stacked.size * lsb_bits

        # PRNG/perm
        fname_bytes = filename.encode('utf-8')[:100]
        rng = self._rng_from_key_and_filename(key, fname_bytes)
        perm = self._perm_for_lsb_bits(rng, lsb_bits)

        # Header placeholder
        crc = self._crc32(payload_bytes)
        header_placeholder = HeaderMeta(lsb_bits=lsb_bits, start_bit_offset=0, payload_len=len(payload_bytes), filename=filename, crc32=crc)
        header_bytes = self.pack_header(header_placeholder)
        header_bits = len(header_bytes) * 8
        required_bits = header_bits + len(payload_bytes) * 8
        if required_bits > total_lsb_bits:
            raise CapacityError(f"Not enough capacity: need {required_bits} bits, have {total_lsb_bits} bits")

        # Start offset
        if start_fxy is not None:
            f, x, y = start_fxy
            if not (0 <= x < w and 0 <= y < h and 0 <= f < len(frames_rgb)):
                raise ValidationError(f"Start (frame,x,y) out of bounds: ({f},{x},{y})")
            pixel_index_across = f * (w * h) + y * w + x
            start_bit = pixel_index_across * c * lsb_bits
            if start_bit + required_bits > total_lsb_bits:
                raise CapacityError("Selected start position too late for payload+header")
        else:
            start_bit = rng.randrange(0, total_lsb_bits - required_bits)

        # Header with actual start
        header = HeaderMeta(lsb_bits=lsb_bits, start_bit_offset=start_bit, payload_len=len(payload_bytes), filename=filename, crc32=crc)
        header_bytes = self.pack_header(header)
        assert len(header_bytes) * 8 == header_bits, "Header size changed unexpectedly"

        # Embed into stacked bytes
        next_bit = self._embed_bits(stacked, lsb_bits, start_bit, perm, header_bytes)
        self._embed_bits(stacked, lsb_bits, next_bit, perm, payload_bytes)

        # Unstack back to frames
        frame_pixels = w * h * c
        new_frames = []
        for i in range(len(frames_rgb)):
            seg = stacked[i * frame_pixels:(i + 1) * frame_pixels]
            new_frames.append(seg.reshape((h, w, c)))

        # Write output
        out_path = out_path or os.path.splitext(cover_video_path)[0] + "_stego.avi"
        self._write_video_rgb24(new_frames, fps, out_path)

        # Verify header pack/unpack
        parsed = self.unpack_header(header_bytes)
        if parsed['crc32'] != crc:
            raise StegaError("Header CRC mismatch after pack/unpack")

        # Store last embed info
        self.last_embed_info = {
            'perm': perm,
            'start_bit': start_bit,
            'header': parsed,
            'lsb_bits': lsb_bits,
            'filename': filename,
            'video_shape': (len(frames_rgb), h, w, c),
            'fps': fps,
            'output': out_path,
        }

        return out_path

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
