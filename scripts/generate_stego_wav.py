import argparse
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

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
    parser = argparse.ArgumentParser(description="Generate a stego WAV using the core encode machine")
    parser.add_argument("--cover", required=True, help="Path to cover WAV (PCM, uncompressed)")
    parser.add_argument("--payload", required=True, help="Path to payload file")
    parser.add_argument("--key", required=True, help="Numeric key used for PRNG and encryption")
    parser.add_argument("--lsb", type=int, default=2, help="Number of cover LSB bits to use (1-8)")
    parser.add_argument("--out", required=True, help="Output stego WAV path")
    parser.add_argument("--start", type=int, default=None, help="Optional start sample index")
    parser.add_argument("--no-encrypt", action="store_true", help="Disable payload encryption (for debugging)")
    args = parser.parse_args()

    machine = StegaEncodeMachine()
    machine.set_encrypt_payload(not args.no_encrypt)
    machine.set_encryption_key(args.key)
    if not machine.encryption_key:
        raise SystemExit("Key must be numeric")
    if not machine.set_lsb_bits(args.lsb):
        raise SystemExit("Invalid LSB bit selection")

    if not machine.set_cover_audio(args.cover):
        raise SystemExit(f"Failed to load cover WAV: {args.cover}")

    payload_path = Path(args.payload)
    if not payload_path.exists():
        raise SystemExit(f"Payload file not found: {payload_path}")
    payload_bytes = payload_path.read_bytes()
    filename = payload_path.name

    stego_bytes = machine.encode_audio(args.cover, payload_bytes, filename, args.lsb, args.key, start_sample=args.start)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(stego_bytes)

    info = machine.last_embed_info or {}
    header = info.get('header', {})
    flags = header.get('flags', 0)
    nonce = header.get('nonce', b'') if isinstance(header.get('nonce'), (bytes, bytearray)) else b''
    print("Stego WAV generated")
    print(f"Output: {out_path}")
    print(f"Cover: {args.cover}")
    print(f"Payload: {payload_path} ({human_size(len(payload_bytes))})")
    print(f"LSB bits: {info.get('lsb_bits')}")
    print(f"Start bit: {info.get('start_bit')}")
    print(f"Flags: 0x{flags:02X}  Encrypted: {'yes' if flags & FLAG_PAYLOAD_ENCRYPTED else 'no'}")
    print(f"Nonce: {nonce.hex() if nonce else '-'}")
    if 'audio_info' in info:
        print(f"Audio info: {info['audio_info']}")


if __name__ == "__main__":
    main()
