"""Shared steganography specification utilities."""
from __future__ import annotations

import hashlib
import os
import random
import struct
import zlib
from dataclasses import dataclass
from typing import Any, Dict, List

HEADER_MAGIC = b"STGA"
HEADER_VERSION = 2
FLAG_PAYLOAD_ENCRYPTED = 0x01
MAX_FILENAME_LEN = 100
MAX_NONCE_LEN = 32
DEFAULT_NONCE_LEN = 16


@dataclass
class HeaderMeta:
    lsb_bits: int
    start_bit_offset: int
    payload_len: int
    filename: str
    crc32: int
    flags: int = 0
    nonce: bytes = b""

    def normalised(self) -> "HeaderMeta":
        filename_bytes = self.filename.encode("utf-8")[:MAX_FILENAME_LEN]
        filename_normalised = filename_bytes.decode("utf-8", errors="ignore")
        nonce = (self.nonce or b"")[:MAX_NONCE_LEN]
        return HeaderMeta(
            lsb_bits=self.lsb_bits,
            start_bit_offset=int(self.start_bit_offset),
            payload_len=int(self.payload_len),
            filename=filename_normalised,
            crc32=int(self.crc32) & 0xFFFFFFFF,
            flags=int(self.flags) & 0xFF,
            nonce=bytes(nonce),
        )


def crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def rng_from_key_and_filename(key: str, filename_bytes: bytes) -> random.Random:
    digest = hashlib.sha256(key.encode("utf-8") + filename_bytes).digest()
    seed_int = int.from_bytes(digest[:8], "big")
    return random.Random(seed_int)


def perm_for_lsb_bits(rng: random.Random, lsb_bits: int) -> List[int]:
    perm = list(range(lsb_bits))
    for i in range(lsb_bits - 1, 0, -1):
        j = rng.randrange(0, i + 1)
        perm[i], perm[j] = perm[j], perm[i]
    return perm


def _keystream(key: str, nonce: bytes, context: bytes, length: int) -> bytes:
    if not nonce:
        raise ValueError("Nonce required for keystream derivation")
    key_bytes = key.encode("utf-8")
    output = bytearray()
    counter = 0
    while len(output) < length:
        block = hashlib.sha256(key_bytes + nonce + context + counter.to_bytes(8, "big")).digest()
        output.extend(block)
        counter += 1
    return bytes(output[:length])


def encrypt_payload(key: str, nonce: bytes, payload: bytes, context: bytes = b"") -> bytes:
    stream = _keystream(key, nonce, context, len(payload))
    return bytes(p ^ s for p, s in zip(payload, stream))


def decrypt_payload(key: str, nonce: bytes, payload: bytes, context: bytes = b"") -> bytes:
    return encrypt_payload(key, nonce, payload, context)


def generate_nonce(length: int = DEFAULT_NONCE_LEN) -> bytes:
    if length <= 0 or length > MAX_NONCE_LEN:
        raise ValueError("Invalid nonce length")
    return os.urandom(length)


def pack_header(meta: HeaderMeta) -> bytes:
    m = meta.normalised()
    if not (1 <= m.lsb_bits <= 8):
        raise ValueError(f"LSB bits must be 1..8, got {m.lsb_bits}")
    fname_bytes = m.filename.encode("utf-8")[:MAX_FILENAME_LEN]
    nonce = (m.nonce or b"")[:MAX_NONCE_LEN]
    parts = [
        HEADER_MAGIC,
        struct.pack(">B", HEADER_VERSION),
        struct.pack(">B", m.flags & 0xFF),
        struct.pack(">B", m.lsb_bits),
        struct.pack(">Q", m.start_bit_offset),
        struct.pack(">I", m.payload_len),
        struct.pack(">B", len(nonce)),
        nonce,
        struct.pack(">B", len(fname_bytes)),
        fname_bytes,
        struct.pack(">I", m.crc32),
    ]
    return b"".join(parts)


def unpack_header(blob: bytes) -> Dict[str, Any]:
    minimum = 4 + 1 + 1 + 1 + 8 + 4 + 1 + 1 + 4
    if len(blob) < minimum:
        raise ValueError("Header too short")
    offset = 0
    magic = blob[offset:offset + 4]
    offset += 4
    if magic != HEADER_MAGIC:
        raise ValueError("Invalid magic")
    version = blob[offset]
    offset += 1
    if version != HEADER_VERSION:
        raise ValueError(f"Unsupported header version {version}")
    flags = blob[offset]
    offset += 1
    lsb_bits = blob[offset]
    offset += 1
    start_bit_offset = struct.unpack(">Q", blob[offset:offset + 8])[0]
    offset += 8
    payload_len = struct.unpack(">I", blob[offset:offset + 4])[0]
    offset += 4
    nonce_len = blob[offset]
    offset += 1
    if nonce_len > MAX_NONCE_LEN:
        raise ValueError("Nonce length invalid")
    nonce = blob[offset:offset + nonce_len]
    offset += nonce_len
    fname_len = blob[offset]
    offset += 1
    if fname_len > MAX_FILENAME_LEN:
        raise ValueError("Filename length invalid")
    fname = blob[offset:offset + fname_len].decode("utf-8", errors="replace")
    offset += fname_len
    crc32_val = struct.unpack(">I", blob[offset:offset + 4])[0]
    offset += 4
    return {
        "version": version,
        "flags": flags,
        "lsb_bits": lsb_bits,
        "start_bit_offset": start_bit_offset,
        "payload_len": payload_len,
        "nonce": nonce,
        "filename": fname,
        "crc32": crc32_val,
        "header_size": offset,
    }