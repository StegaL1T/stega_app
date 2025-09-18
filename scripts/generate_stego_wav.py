import argparse
import os
import hashlib
import random
import struct
import zlib
import wave
import io
from typing import Optional

import numpy as np


def rng_from_key_and_filename(key: str, filename_bytes: bytes) -> random.Random:
    digest = hashlib.sha256(key.encode('utf-8') + filename_bytes).digest()
    seed_int = int.from_bytes(digest[:8], 'big')
    return random.Random(seed_int)


def build_header_v1(lsb_bits: int, payload: bytes, suggested_filename: Optional[str], start_bit_offset: int) -> bytes:
    magic = b'STGA'
    version = bytes([1])
    lsb = bytes([lsb_bits])
    start = struct.pack('>Q', start_bit_offset)
    length = struct.pack('>I', len(payload))
    fname_bytes = (suggested_filename or '').encode('utf-8')[:100]
    fname_len = bytes([len(fname_bytes)])
    crc32 = struct.pack('>I', zlib.crc32(payload) & 0xFFFFFFFF)
    return b''.join([magic, version, lsb, start, length, fname_len, fname_bytes, crc32])


def write_bits_into_bytes(flat_bytes: np.ndarray, lsb_bits: int, start_bit: int, bit_order: list[int], bits: bytes) -> None:
    total_lsb_bits = flat_bytes.size * lsb_bits

    def bit_stream():
        for byte in bits:
            for i in range(7, -1, -1):
                yield (byte >> i) & 1

    idx = start_bit
    for bit in bit_stream():
        if idx >= total_lsb_bits:
            raise ValueError('Insufficient capacity while embedding')
        byte_index = idx // lsb_bits
        within_byte = idx % lsb_bits
        bit_pos = bit_order[within_byte]
        value = int(flat_bytes[byte_index])
        value = (value & ~(1 << bit_pos)) | ((bit & 1) << bit_pos)
        flat_bytes[byte_index] = value
        idx += 1


def main():
    parser = argparse.ArgumentParser(description='Generate a stego WAV for decoder testing (header v1, with start offset).')
    parser.add_argument('--cover', required=True, help='Path to cover WAV (PCM, uncompressed).')
    parser.add_argument('--payload', required=True, help='Path to payload file (any binary).')
    parser.add_argument('--key', required=True, help='Numeric key used for PRNG.')
    parser.add_argument('--lsb', type=int, default=1, help='Number of LSBs to use (1-8).')
    parser.add_argument('--out', required=True, help='Output stego WAV path.')
    args = parser.parse_args()

    if not (1 <= args.lsb <= 8):
        raise SystemExit('lsb must be between 1 and 8')

    if not os.path.exists(args.cover):
        raise SystemExit(f'Cover WAV not found: {args.cover}')
    if not os.path.exists(args.payload):
        raise SystemExit(f'Payload file not found: {args.payload}')

    # Load payload
    with open(args.payload, 'rb') as f:
        payload = f.read()
    suggested_filename = os.path.basename(args.payload)

    # Open WAV
    with wave.open(args.cover, 'rb') as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        comptype = wf.getcomptype()
        if comptype not in ('NONE', 'not compressed'):
            raise SystemExit(f'Unsupported WAV compression: {comptype}')
        frames = wf.readframes(n_frames)
        params = wf.getparams()

    flat = np.frombuffer(frames, dtype=np.uint8).copy()

    # Build header placeholder
    tmp_header = build_header_v1(args.lsb, payload, suggested_filename, 0)
    header_bits = len(tmp_header) * 8

    # Compute capacity and choose start
    total_lsb_bits = flat.size * args.lsb
    required_bits = header_bits + len(payload) * 8
    if required_bits > total_lsb_bits:
        raise SystemExit(f'Not enough capacity: need {required_bits} bits, have {total_lsb_bits} bits')

    fname_bytes = suggested_filename.encode('utf-8')[:100]
    rng = rng_from_key_and_filename(args.key, fname_bytes)
    start_bit = rng.randrange(0, total_lsb_bits - required_bits)

    # Bit order permutation
    bit_order = list(range(args.lsb))
    rng.shuffle(bit_order)

    # Embed header then payload
    header = build_header_v1(args.lsb, payload, suggested_filename, start_bit)
    write_bits_into_bytes(flat, args.lsb, start_bit, bit_order, header)
    write_bits_into_bytes(flat, args.lsb, start_bit + len(header) * 8, bit_order, payload)

    # Save WAV
    out_buf = io.BytesIO()
    with wave.open(out_buf, 'wb') as ww:
        ww.setparams(params)
        ww.writeframes(flat.tobytes())
    out_bytes = out_buf.getvalue()
    out_dir = os.path.dirname(args.out)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, 'wb') as f:
        f.write(out_bytes)
    print(f'Wrote stego WAV to {args.out}')
    print(f'Header bytes: {len(header)}  Payload bytes: {len(payload)}  Start bit: {start_bit}')


if __name__ == '__main__':
    main()
