import argparse
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import numpy as np
from PIL import Image

from machine.stega_encode_machine import StegaEncodeMachine
from machine.stega_spec import FLAG_PAYLOAD_ENCRYPTED


def human_size(num: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(num)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} PB"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a stego PNG using the core encode machine")
    parser.add_argument("--cover", required=True, help="Path to cover image (PNG, BMP, etc.)")
    parser.add_argument("--payload", required=True, help="Path to payload file")
    parser.add_argument("--key", required=True, help="Numeric key used for PRNG and encryption")
    parser.add_argument("--lsb", type=int, default=2, help="Number of cover LSB bits to use (1-8)")
    parser.add_argument("--out", required=True, help="Output stego PNG path")
    parser.add_argument("--no-encrypt", action="store_true", help="Disable payload encryption (for debugging)")
    parser.add_argument("--diff", action="store_true", help="Also save an LSB difference map next to output")
    args = parser.parse_args()

    machine = StegaEncodeMachine()
    machine.set_encrypt_payload(not args.no_encrypt)
    machine.set_encryption_key(args.key)
    if not machine.encryption_key:
        raise SystemExit("Key must be numeric")
    if not machine.set_lsb_bits(args.lsb):
        raise SystemExit("Invalid LSB bit selection")

    if not machine.set_cover_image(args.cover):
        raise SystemExit(f"Failed to load cover image: {args.cover}")

    payload_path = Path(args.payload)
    if not payload_path.exists():
        raise SystemExit(f"Payload file not found: {payload_path}")
    payload_bytes = payload_path.read_bytes()
    filename = payload_path.name

    stego_img, header = machine.encode_image(args.cover, payload_bytes, filename, args.lsb, args.key)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    stego_img.save(out_path, format="PNG")

    info = machine.last_embed_info or {}
    flags = header.get('flags', 0)
    nonce = header.get('nonce', b'') if isinstance(header.get('nonce'), (bytes, bytearray)) else b''
    print("Stego PNG generated")
    print(f"Output: {out_path}")
    print(f"Cover: {args.cover}")
    print(f"Payload: {payload_path} ({human_size(len(payload_bytes))})")
    print(f"LSB bits: {info.get('lsb_bits')}")
    print(f"Start bit: {info.get('start_bit')}")
    print(f"Flags: 0x{flags:02X}  Encrypted: {'yes' if flags & FLAG_PAYLOAD_ENCRYPTED else 'no'}")
    print(f"Header CRC32: 0x{header.get('crc32', 0):08X}")
    print(f"Nonce: {nonce.hex() if nonce else '-'}")

    if args.diff:
        cover_img = Image.open(args.cover)
        if cover_img.mode != "RGB":
            cover_img = cover_img.convert("RGB")
        cover_arr = np.array(cover_img, dtype=np.uint8)
        stego_arr = np.array(stego_img, dtype=np.uint8)
        mask = (1 << max(1, args.lsb)) - 1
        diff = (cover_arr ^ stego_arr) & mask
        scale = 255 // mask if mask else 255
        diff_vis = (diff * scale).astype(np.uint8)
        diff_img = Image.fromarray(diff_vis, mode="RGB")
        diff_path = out_path.with_name(out_path.stem + "_diff.png")
        diff_img.save(diff_path)
        print(f"Diff map saved to: {diff_path}")


if __name__ == "__main__":
    main()
