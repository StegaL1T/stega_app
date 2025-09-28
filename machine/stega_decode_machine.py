import os
import json
import base64
import tempfile
import subprocess
import shutil
from typing import List, Optional, Tuple
from datetime import datetime

import numpy as np
from PIL import Image
from PyPDF2 import PdfReader
import wave
from pathlib import Path

try:
    from stegano import lsb
except Exception:
    lsb = None

from crypto_honey import HoneyFormatError, he_decrypt

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
        self.stego_video_path: Optional[str] = None
        self.lsb_bits: int = 1
        self.encryption_key: Optional[str] = None
        self.output_path: Optional[str] = None

        # Internal state for media
        self.stego_image: Optional[Image.Image] = None
        self.image_array: Optional[np.ndarray] = None
        self.audio_data: Optional[np.ndarray] = None
        self.video_data: Optional[np.ndarray] = None
        self.video_shape: Optional[Tuple[int, int, int, int]] = None
        self.video_fps: Optional[float] = None
        self.video_metadata: Optional[dict] = None
        
        # Internal state for results
        self.extracted_data: Optional[str] = None
        self.last_error: Optional[str] = None
        self.header_info: Optional[dict] = None
        self.last_output_path: Optional[str] = None
        self.last_payload_raw: Optional[bytes] = None
        self.honey_detected: bool = False
        self.honey_info: Optional[dict] = None
        self.honey_error: Optional[str] = None

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
                print(f"[DEBUG] First 32 bytes of raw audio: {raw_data[:32].hex()}")
                self.audio_data = np.frombuffer(raw_data, dtype=np.uint8)
                print(f"[DEBUG] np.uint8 audio_data shape: {self.audio_data.shape}, first 32 bytes: {self.audio_data[:32].tolist()}")
                self.stego_audio_path = audio_path
                self.last_error = None

            print(f"Steganographic audio loaded: {audio_path}")
            print(f"Audio samples: {len(self.audio_data)}")
            return True

        except Exception as e:
            self.last_error = f"Error loading steganographic audio: {e}"
            print(f"Error: {self.last_error}")
            return False

    def set_stego_video(self, video_path: str) -> bool:
        """Register a steganographic video path. Frame extraction will be done at decode time.

        We avoid relying on OpenCV's container/codec support here because PNG-in-AVI
        may not be readable by default on some Windows OpenCV builds. Instead, we
        defer to ffmpeg during the actual decode to extract frames reliably.
        """
        try:
            self._reset_media()
            if not os.path.exists(video_path):
                self.last_error = f"Steganographic video not found: {video_path}"
                print(f"Error: {self.last_error}")
                return False

            # We don't pre-parse frames here. Store path and proceed.
            self.stego_video_path = video_path
            self.video_data = None
            self.video_shape = None
            self.video_fps = None
            self.video_metadata = None
            self.last_error = None
            print(f"Steganographic video selected: {video_path}")
            return True

        except Exception as e:
            self.last_error = f"Error loading steganographic video: {e}"
            print(f"Error: {self.last_error}")
            return False

    def _reset_media(self):
        """Clears all loaded media data."""
        self.stego_image = None
        self.image_array = None
        self.stego_image_path = None
        self.audio_data = None
        self.stego_audio_path = None
        self.video_data = None
        self.stego_video_path = None
        self.video_shape = None
        self.video_fps = None
        self.video_metadata = None

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
        if not self.stego_image_path and not self.stego_audio_path and not self.stego_video_path:
            return False, "Steganographic media not selected"
            
        if self.stego_image_path and self.image_array is None:
            return False, "Steganographic image not loaded properly"
            
        if self.stego_audio_path and self.audio_data is None:
            return False, "Steganographic audio not loaded properly"

        # For videos, we defer frame extraction to decode time using ffmpeg.

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

        # If video is provided, use frame-based stegano decode (no header)
        if self.stego_video_path:
            ok = self._extract_from_video_frames(self.stego_video_path)
            return ok

        # Determine which media to decode from for image/audio (header-based)
        if self.stego_image_path:
            media_array = self.image_array
        elif self.stego_audio_path:
            media_array = self.audio_data
        else:
            self.last_error = "No steganographic media loaded."
            return False

        return self._extract_from_media(media_array)

    def _extract_from_video_frames(self, video_path: str) -> bool:
        """Decode message segments embedded per-frame using stegano.lsb and reconstruct payload.

        This matches the simple LSB per-frame method: each frame may contain a chunk of
        text embedded via stegano.lsb.hide. We concatenate all non-empty reveals
        (in frame order) until we hit the first None, then attempt to parse JSON
        metadata {filename, kind, payload} where payload is base64 of the original bytes.
        If parsing fails, we save the concatenated text as a .txt file.
        """
        if lsb is None:
            self.last_error = "Python package 'stegano' is required for video decoding."
            print(f"Error: {self.last_error}")
            return False

        # Extract frames to a temporary directory as PNGs using ffmpeg for robust support
        ffmpeg = shutil.which('ffmpeg')
        if not ffmpeg:
            self.last_error = "ffmpeg is required to extract video frames for decoding."
            print(f"Error: {self.last_error}")
            return False

        temp_dir = Path(tempfile.mkdtemp(prefix="stego_video_decode_"))
        frames_dir = temp_dir / "frames"
        try:
            frames_dir.mkdir(parents=True, exist_ok=True)
            pattern = f"{frames_dir.as_posix()}/%06d.png"
            cmd = [
                ffmpeg, '-y', '-hide_banner', '-loglevel', 'error',
                '-i', video_path,
                '-vsync', '0',
                pattern,
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            if result.returncode != 0:
                detail = result.stderr.decode(errors='ignore').strip()
                self.last_error = f"Failed to extract frames with ffmpeg: {detail}"
                print(f"Error: {self.last_error}")
                return False
            count = len(list(frames_dir.glob('*.png')))
            if count == 0:
                self.last_error = "Video has no frames after extraction"
                print(f"Error: {self.last_error}")
                return False

            # Reveal segments across all frames (skip frames without hidden text)
            segments: List[tuple[int, str]] = []
            for idx in range(count):
                fpath = frames_dir / f"{idx:06d}.png"
                try:
                    dec = lsb.reveal(str(fpath))
                except Exception:
                    dec = None
                if dec:
                    segments.append((idx, dec))

            if not segments:
                self.last_error = "No hidden data found in video frames"
                print(f"Error: {self.last_error}")
                return False

            # Concatenate segments in frame order
            joined = "".join(seg for _, seg in segments)
            first_idxs = [i for i, _ in segments][:8]
            print(f"[VIDEO DECODE] segments_found={len(segments)}, first_frames={first_idxs}")

            # Determine output path base
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_dir = self.output_path if (self.output_path and os.path.isdir(self.output_path)) else os.path.dirname(video_path)
            if not base_dir:
                base_dir = os.getcwd()

            out_path: Optional[str] = None
            saved_bytes = False
            preview_text: Optional[str] = None

            # Try JSON envelope first (supports encrypted or plaintext inner JSON)
            try:
                env = json.loads(joined)
                inner_json_bytes: Optional[bytes] = None
                if isinstance(env, dict) and env.get('v') == 1:
                    # Enforce LSB bits match if present
                    env_bits = env.get('b')
                    if isinstance(env_bits, int) and 1 <= env_bits <= 8:
                        if env_bits != self.lsb_bits:
                            raise ValueError(f"LSB bits mismatch for video envelope (stego {env_bits} != selected {self.lsb_bits})")
                    if env.get('enc') is True:
                        # Encrypted envelope requires a key
                        if not self.encryption_key or not self.encryption_key.strip():
                            raise ValueError('Encrypted video payload requires a decryption key')
                        nonce_b64 = env.get('nonce')
                        ct_b64 = env.get('ct')
                        if not nonce_b64 or not ct_b64:
                            raise ValueError('Missing nonce or ciphertext in envelope')
                        nonce = base64.b64decode(nonce_b64)
                        ct = base64.b64decode(ct_b64)
                        inner_json_bytes = decrypt_payload(self.encryption_key, nonce, ct, context=b'video-json')
                    else:
                        # Plaintext envelope carries base64 of inner JSON in 'pt'
                        pt_b64 = env.get('pt')
                        if not pt_b64:
                            raise ValueError('Missing plaintext payload in envelope')
                        inner_json_bytes = base64.b64decode(pt_b64)
                else:
                    # Legacy direct metadata structure
                    if isinstance(env, dict) and 'payload' in env:
                        inner_json_bytes = json.dumps(env, ensure_ascii=True).encode('utf-8')

                if inner_json_bytes is not None:
                    inner = json.loads(inner_json_bytes.decode('utf-8'))
                    b64 = inner.get('payload')
                    fname = inner.get('filename') or 'payload.bin'
                    raw = base64.b64decode(b64)
                    # If user specified an explicit file (with extension) in output_path, honor it
                    if self.output_path and os.path.splitext(self.output_path)[1]:
                        out_path = self.output_path
                    else:
                        out_path = os.path.join(base_dir, f"{ts}.{fname}")
                    os.makedirs(os.path.dirname(out_path), exist_ok=True)
                    with open(out_path, 'wb') as f:
                        f.write(raw)
                    saved_bytes = True
                    try:
                        preview_text = raw.decode('utf-8')
                    except Exception:
                        preview_text = None
            except Exception:
                pass

            # Fallback: treat as plain text and save
            if not saved_bytes:
                if self.output_path and os.path.splitext(self.output_path)[1]:
                    out_path = self.output_path
                else:
                    out_path = os.path.join(base_dir, f"{ts}_extracted.txt")
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(joined)
                preview_text = joined

            self.last_output_path = out_path
            self.extracted_data = preview_text or f"Binary payload extracted -> {out_path}"
            self.header_info = {
                'video_frames_scanned': count,
                'segments_found': len(segments),
                'segment_frames': [i for (i, _) in segments][:16],
                'saved_to': out_path,
                'mode': 'per-frame-lsb',
            }
            print("Steganography decoding (video frames) completed successfully!")
            print(f"Extracted data saved to: {out_path}")
            return True
        except Exception as e:
            self.last_error = f"Video frame decode failed: {e}"
            print(f"Error: {self.last_error}")
            return False
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
        
    def _extract_from_media(self, media_array: np.ndarray) -> bool:
        """
        Performs the core decoding logic on a NumPy array,
        abstracting image vs. audio. Always outputs a file, even if header/CRC fails.
        """
        self.last_output_path = None
        print("Starting steganography decoding process...")

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
        print(f"[DEBUG] First 16 bytes from LSB stream: {preview_bytes.hex()}")

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

        header_valid = False
        header_info = None
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
            print(f"[DEBUG] Raw header bytes extracted: {list(header_bytes)}")
            try:
                header_info = unpack_header(bytes(header_bytes))
                header_valid = True
            except Exception as exc:
                print(f"[WARN] Invalid header: {exc} (proceeding with raw extraction)")
        except Exception as exc:
            print(f"[WARN] Could not parse header: {exc} (proceeding with raw extraction)")

        # Set defaults if header is invalid
        if header_valid:
            version = header_info["version"]
            flags = header_info["flags"]
            header_lsb_bits = header_info["lsb_bits"]
            start_bit = header_info["start_bit_offset"]
            payload_length = header_info["payload_len"]
            nonce = header_info["nonce"]
            filename = header_info["filename"]
            expected_crc32 = header_info["crc32"]
            header_bits_consumed = header_cursor.pos
        else:
            version = 0
            flags = 0
            header_lsb_bits = self.lsb_bits
            start_bit = header_cursor.pos
            payload_length = min(32, (total_lsb_bits - start_bit) // 8)  # Try to extract something
            nonce = b''
            filename = 'unknown.bin'
            expected_crc32 = 0
            header_bits_consumed = header_cursor.pos

        # LSB bits mismatch: warn but continue
        if header_valid and header_lsb_bits != self.lsb_bits:
            print(f"[WARN] LSB bits mismatch (header {header_lsb_bits} != selected {self.lsb_bits}) (proceeding)")

        # Start offset check: warn but continue
        if header_valid and start_bit < header_bits_consumed:
            print(f"[WARN] Header reports start offset within header region (proceeding)")

        payload_bits = payload_length * 8
        if payload_bits == 0:
            print(f"[WARN] Payload length from header is zero (proceeding with 32 bytes)")
            payload_length = min(32, (total_lsb_bits - start_bit) // 8)
            payload_bits = payload_length * 8

        if start_bit + payload_bits > total_lsb_bits:
            print(f"[WARN] Payload length from header exceeds media capacity (truncating)")
            payload_length = max(0, (total_lsb_bits - start_bit) // 8)
            payload_bits = payload_length * 8

        filename_bytes = filename.encode('utf-8')[:MAX_FILENAME_LEN]
        rng = rng_from_key_and_filename(self.encryption_key or '', b"")
        perm = perm_for_lsb_bits(rng, header_lsb_bits)
        payload_cursor = BitCursor(start_bit, perm)

        try:
            payload_encrypted = payload_cursor.read_bytes(payload_length)
        except Exception as exc:
            print(f"[WARN] Unexpected end of bitstream while reading payload: {exc} (proceeding with partial)")
            payload_encrypted = b''

        is_encrypted = bool(flags & FLAG_PAYLOAD_ENCRYPTED)
        if is_encrypted and nonce:
            try:
                payload_plain = decrypt_payload(self.encryption_key or '', nonce, payload_encrypted, filename_bytes)
            except Exception as exc:
                print(f"[WARN] Decryption failed: {exc} (proceeding with raw bytes)")
                payload_plain = payload_encrypted
        else:
            payload_plain = payload_encrypted

        self.last_payload_raw = payload_plain

        # CRC32 check: warn but continue
        if header_valid:
            actual_crc32 = crc32(payload_plain)
            print(f"[DEBUG] CRC32 expected: 0x{expected_crc32:08X}, actual: 0x{actual_crc32:08X}")
            if actual_crc32 != expected_crc32:
                print(f"[WARN] CRC32 mismatch. Wrong key or corrupted stego. (proceeding with output)")

        self.honey_detected = False
        self.honey_info = None
        self.honey_error = None
        payload_to_save = payload_plain
        honey_display_text = None

        if payload_plain.startswith(b'HONEY1'):
            self.honey_detected = True
            try:
                meta = self._parse_honey_blob_meta(payload_plain)
            except HoneyFormatError as exc:
                self.honey_error = str(exc)
                self.last_error = f"Honey payload parse error: {exc}"
                return False
            meta['key'] = None
            try:
                key_int = int(self.encryption_key or '0')
            except (TypeError, ValueError):
                self.honey_error = "Honey payload detected but numeric key is required."
                self.honey_info = meta
            else:
                try:
                    honey_message = he_decrypt(payload_plain, key_int)
                except HoneyFormatError as exc:
                    self.honey_error = str(exc)
                    self.last_error = f"Honey payload parse error: {exc}"
                    return False
                meta['key'] = key_int
                meta['message'] = honey_message
                self.honey_info = meta
                honey_display_text = honey_message
                payload_to_save = honey_message.encode('utf-8')

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

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
                    base_dir = os.path.join(candidate_dir, base_name) if base_name else candidate_dir
                    if base_dir and not os.path.exists(base_dir):
                        os.makedirs(base_dir, exist_ok=True)

        if explicit_file:
            output_path = explicit_file
        else:
            if not base_dir:
                stego_source = (self.stego_image_path or self.stego_audio_path or self.stego_video_path)
                base_dir = os.path.dirname(stego_source) if stego_source else ''
                if not base_dir:
                    base_dir = os.path.join(os.getcwd(), 'extracted_payloads')
                if not os.path.exists(base_dir):
                    os.makedirs(base_dir, exist_ok=True)
            final_name = build_final_name(suggested_filename)
            output_path = os.path.join(base_dir, final_name)

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, 'wb') as f:
            f.write(payload_to_save)

        self.last_output_path = output_path

        if requested_path:
            if os.path.isdir(requested_path):
                self.output_path = requested_path
            else:
                preferred_dir = os.path.dirname(requested_path) or os.path.dirname(output_path)
                self.output_path = preferred_dir
        else:
            self.output_path = os.path.dirname(output_path)

        if honey_display_text is not None:
            self.extracted_data = honey_display_text
        else:
            try:
                self.extracted_data = payload_to_save.decode('utf-8')
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
                    self.extracted_data = f"Binary payload extracted ({len(payload_to_save)} bytes) -> {output_path}"

        print("Steganography decoding completed (output may be incorrect if LSB/key is wrong)")
        print(f"Extracted data saved to: {output_path}")

        self.header_info = {
            'version': int(version),
            'lsb_bits': int(header_lsb_bits),
            'start_offset': int(start_bit),
            'header_bits': int(header_bits_consumed),
            'payload_length': int(payload_length),
            'filename': suggested_filename,
            'crc32_ok': not header_valid or (header_valid and (not expected_crc32 or crc32(payload_plain) == expected_crc32)),
            'encrypted': is_encrypted,
            'flags': int(flags),
            'nonce': nonce.hex() if nonce else '',
            'computed_start': int(start_bit),
        }
        return True

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

    def get_video_info(self) -> dict:
        """Return metadata about the loaded steganographic video."""
        if not self.stego_video_path or self.video_data is None or self.video_metadata is None:
            return {}

        info = dict(self.video_metadata)
        info['path'] = self.stego_video_path
        info['dimensions'] = (info.get('height'), info.get('width'), info.get('channels'))
        info['flattened_length'] = int(self.video_data.size)
        frames = info.get('frames') or 0
        width = info.get('width') or 0
        height = info.get('height') or 0
        channels = info.get('channels') or 0
        fps = info.get('fps') or 0.0
        max_capacity_bits = frames * width * height * channels * self.lsb_bits
        info['max_capacity_bytes'] = max_capacity_bits // 8 if max_capacity_bits else 0
        info['duration'] = (frames / fps) if fps else None
        return info

    def get_extracted_data(self) -> Optional[str]:
        # ... (existing code, no changes needed)
        return self.extracted_data

    def get_last_output_path(self) -> Optional[str]:
        """Return the full path of the most recent decode output."""
        return self.last_output_path

    def get_honey_context(self) -> Optional[dict]:
        """Return details about the last Honey payload, if any."""
        if not self.honey_detected:
            return None
        return {
            'info': self.honey_info,
            'error': self.honey_error,
        }

    def simulate_honey_with_key(self, key_int: int) -> str:
        """Decrypt the last Honey payload with an alternate key."""
        if not self.last_payload_raw or not self.last_payload_raw.startswith(b'HONEY1'):
            raise HoneyFormatError('No Honey payload available for simulation')
        return he_decrypt(self.last_payload_raw, int(key_int))

    @staticmethod
    def _parse_honey_blob_meta(blob: bytes) -> dict:
        if not isinstance(blob, (bytes, bytearray, memoryview)):
            raise HoneyFormatError('Honey payload must be bytes-like')
        data = memoryview(bytes(blob))
        if len(data) < 6 + 4 + 8 + 1 + 4:
            raise HoneyFormatError('Honey payload is too short')
        if bytes(data[:6]) != b'HONEY1':
            raise HoneyFormatError('Missing HONEY1 magic header')
        offset = 6
        resolution = int.from_bytes(data[offset:offset + 4], 'big')
        offset += 4
        nonce = bytes(data[offset:offset + 8])
        offset += 8
        univ_len = data[offset]
        offset += 1
        if len(data) < offset + univ_len + 4:
            raise HoneyFormatError('Honey payload truncated while reading universe')
        universe = bytes(data[offset:offset + univ_len]).decode('ascii', errors='strict')
        return {
            'universe': universe,
            'resolution': resolution,
            'nonce': nonce.hex(),
        }

    def cleanup(self):
        # ... (existing code, no changes needed)
        self.stego_image = None
        self.image_array = None
        self.audio_data = None
        self.video_data = None
        self.stego_image_path = None
        self.stego_audio_path = None
        self.stego_video_path = None
        self.video_shape = None
        self.video_fps = None
        self.video_metadata = None
        self.extracted_data = None
        self.last_error = None
        self.header_info = None
        self.last_output_path = None
        self.last_payload_raw = None
        self.honey_detected = False
        self.honey_info = None
        self.honey_error = None
        print("StegaDecodeMachine cleaned up")

    def get_last_error(self) -> Optional[str]:
        # ... (existing code, no changes needed)
        return self.last_error

    def get_header_info(self) -> Optional[dict]:
        # ... (existing code, no changes needed)
        return self.header_info

