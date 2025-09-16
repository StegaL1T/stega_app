import argparse
import os
import hashlib
import random
import struct
import zlib
from typing import Optional

import numpy as np
from PIL import Image


def rng_from_key(key: str) -> random.Random:
    key_bytes = key.encode('utf-8')
    digest = hashlib.sha256(key_bytes).digest()
    seed_int = int.from_bytes(digest[:8], 'big')
    return random.Random(seed_int)


def build_header_v1(lsb_bits: int, payload: bytes, suggested_filename: Optional[str]) -> bytes:
    magic = b'STGA'
    version = bytes([1])
    lsb = bytes([lsb_bits])
    length = struct.pack('>I', len(payload))
    fname_bytes = (suggested_filename or '').encode('utf-8')[:100]
    fname_len = bytes([len(fname_bytes)])
    crc32 = struct.pack('>I', zlib.crc32(payload) & 0xFFFFFFFF)
    return b''.join([magic, version, lsb, length, fname_len, fname_bytes, crc32])


def write_bits_into_image(flat_bytes: np.ndarray, lsb_bits: int, start_bit: int, bit_order: list[int], bits: bytes) -> None:
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
    parser = argparse.ArgumentParser(description='Generate a stego PNG for decoder testing (header v1).')
    parser.add_argument('--cover', required=True, help='Path to cover image (PNG, BMP, etc.).')
    parser.add_argument('--payload', required=True, help='Path to payload file (any binary).')
    parser.add_argument('--key', required=True, help='Numeric or string key used for PRNG.')
    parser.add_argument('--lsb', type=int, default=1, help='Number of LSBs to use (1-8).')
    parser.add_argument('--out', required=True, help='Output stego PNG path.')
    args = parser.parse_args()

    if not (1 <= args.lsb <= 8):
        raise SystemExit('lsb must be between 1 and 8')

    if not os.path.exists(args.cover):
        raise SystemExit(f'Cover image not found: {args.cover}')
    if not os.path.exists(args.payload):
        raise SystemExit(f'Payload file not found: {args.payload}')

    # Load inputs
    with open(args.payload, 'rb') as f:
        payload = f.read()
    suggested_filename = os.path.basename(args.payload)

    img = Image.open(args.cover)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    arr = np.array(img, dtype=np.uint8)
    flat = arr.reshape(-1)

    # Build header
    header = build_header_v1(args.lsb, payload, suggested_filename)

    # Compute capacity and choose start
    total_lsb_bits = flat.size * args.lsb
    required_bits = len(header) * 8 + len(payload) * 8
    if required_bits > total_lsb_bits:
        raise SystemExit(f'Not enough capacity: need {required_bits} bits, have {total_lsb_bits} bits')

    rng = rng_from_key(args.key)
    safety_margin = 0
    start_bit = rng.randrange(0, total_lsb_bits - required_bits - safety_margin)

    # Bit order permutation
    bit_order = list(range(args.lsb))
    rng.shuffle(bit_order)

    # Embed header then payload
    write_bits_into_image(flat, args.lsb, start_bit, bit_order, header)
    write_bits_into_image(flat, args.lsb, start_bit + len(header) * 8, bit_order, payload)

    # Save stego image (PNG)
    stego = flat.reshape(arr.shape)
    out_img = Image.fromarray(stego, mode='RGB')
    out_dir = os.path.dirname(args.out)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    out_img.save(args.out, format='PNG')
    print(f'Wrote stego PNG to {args.out}')
    print(f'Header bytes: {len(header)}  Payload bytes: {len(payload)}  Start bit: {start_bit}')


if __name__ == '__main__':
    main()


