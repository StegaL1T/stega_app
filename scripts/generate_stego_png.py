import argparse
import os
import hashlib
import random
import struct
import zlib
from typing import Optional

import numpy as np
from PIL import Image


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


def parse_header_v1(h: bytes) -> dict:
    off = 0
    magic = h[off:off+4]; off += 4
    if magic != b'STGA':
        raise ValueError('Bad magic')
    ver = h[off]; off += 1
    lsb = h[off]; off += 1
    start = struct.unpack('>Q', h[off:off+8])[0]; off += 8
    length = struct.unpack('>I', h[off:off+4])[0]; off += 4
    flen = h[off]; off += 1
    fname = h[off:off+flen].decode('utf-8', errors='replace'); off += flen
    crc32 = struct.unpack('>I', h[off:off+4])[0]
    return {
        'version': ver,
        'lsb_bits': lsb,
        'start_bit_offset': start,
        'payload_len': length,
        'filename': fname,
        'crc32': crc32,
    }


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
    parser = argparse.ArgumentParser(description='Generate a stego PNG for decoder testing (header v1, with start offset).')
    parser.add_argument('--cover', required=True, help='Path to cover image (PNG, BMP, etc.).')
    parser.add_argument('--payload', required=True, help='Path to payload file (any binary).')
    parser.add_argument('--key', required=True, help='Numeric key used for PRNG.')
    parser.add_argument('--lsb', type=int, default=1, help='Number of LSBs to use (1-8).')
    parser.add_argument('--out', required=True, help='Output stego PNG path.')
    parser.add_argument('--diff', action='store_true', help='Also save a difference map PNG next to output.')
    args = parser.parse_args()

    if not (1 <= args.lsb <= 8):
        raise SystemExit('lsb must be between 1 and 8')

    # Create fixtures if needed
    if not os.path.exists(args.cover):
        base_dir = os.path.dirname(args.cover)
        if base_dir and not os.path.isdir(base_dir):
            os.makedirs(base_dir, exist_ok=True)
        # Create a simple RGB gradient fixture
        w = 256
        h = 256
        x = np.linspace(0, 255, w, dtype=np.uint8)
        y = np.linspace(0, 255, h, dtype=np.uint8)
        xv, yv = np.meshgrid(x, y)
        fixture = np.stack([xv, yv, ((xv.astype(int)+yv.astype(int))//2).astype(np.uint8)], axis=2)
        Image.fromarray(fixture, mode='RGB').save(args.cover, format='PNG')
        print(f'Created fixture cover image at {args.cover}')
    if not os.path.exists(args.payload):
        raise SystemExit(f'Payload file not found: {args.payload}')

    # Load inputs
    if not os.path.exists(args.payload):
        # Create a small text payload fixture
        base_dir = os.path.dirname(args.payload)
        if base_dir and not os.path.isdir(base_dir):
            os.makedirs(base_dir, exist_ok=True)
        with open(args.payload, 'wb') as f:
            f.write(b'This is a small payload for stego demo.\n' * 64)
        print(f'Created fixture payload at {args.payload}')
    with open(args.payload, 'rb') as f:
        payload = f.read()
    suggested_filename = os.path.basename(args.payload)

    img = Image.open(args.cover)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    arr = np.array(img, dtype=np.uint8)
    flat = arr.reshape(-1)

    # Build header
    # We need header length to pick start, but header includes start; so we build a placeholder with 0 then recompute
    tmp_header = build_header_v1(args.lsb, payload, suggested_filename, 0)
    header_bits = len(tmp_header) * 8

    # Compute capacity and choose start
    total_lsb_bits = flat.size * args.lsb
    required_bits = header_bits + len(payload) * 8
    if required_bits > total_lsb_bits:
        raise SystemExit(f'Not enough capacity: need {required_bits} bits, have {total_lsb_bits} bits')

    fname_bytes = suggested_filename.encode('utf-8')[:100]
    rng = rng_from_key_and_filename(args.key, fname_bytes)
    safety_margin = 0
    start_bit = rng.randrange(0, total_lsb_bits - required_bits - safety_margin)

    # Bit order permutation
    bit_order = list(range(args.lsb))
    rng.shuffle(bit_order)

    # Embed header then payload
    header = build_header_v1(args.lsb, payload, suggested_filename, start_bit)
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
    # Print parsed header fields from the bytes we embedded
    parsed = parse_header_v1(header)
    print('Parsed header:', parsed)

    if args.diff:
        # Create a visual diff map of changed LSBs
        stego_arr = np.array(out_img, dtype=np.uint8)
        diff = (arr ^ stego_arr) & ((1 << max(1, args.lsb)) - 1)
        # Amplify for visibility
        scale = 255 // ((1 << max(1, args.lsb)) - 1)
        diff_vis = (diff * scale).astype(np.uint8)
        diff_img = Image.fromarray(diff_vis, mode='RGB')
        diff_path = os.path.splitext(args.out)[0] + '_diff.png'
        diff_img.save(diff_path)
        print(f'Saved difference map to {diff_path}')


if __name__ == '__main__':
    main()


