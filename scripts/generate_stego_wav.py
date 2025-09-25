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

    # Debug: Show CRC32 and first 32 bytes of payload before embedding
    import zlib
    payload_crc32 = zlib.crc32(payload_bytes) & 0xFFFFFFFF
    print(f"[DEBUG] Payload CRC32 before embedding: 0x{payload_crc32:08X}")
    print(f"[DEBUG] First 32 bytes of payload before embedding: {list(payload_bytes[:32])}")

    # If encryption is enabled, print first 32 bytes of encrypted payload
    if not args.no_encrypt:
        from machine.stega_spec import encrypt_payload
        context_bytes = filename.encode('utf-8')
        # Use the same nonce as in the actual encoding (after encode_audio)
        stego_bytes = machine.encode_audio(args.cover, payload_bytes, filename, args.lsb, args.key, start_sample=args.start)
        info = getattr(machine, 'last_embed_info', None) or {}
        header = info.get('header', {})
        nonce = header.get('nonce', b'') if isinstance(header.get('nonce'), (bytes, bytearray)) else b''
        if nonce:
            encrypted_payload = encrypt_payload(args.key, nonce, payload_bytes, context_bytes)
            print(f"[DEBUG] First 32 bytes of encrypted payload: {list(encrypted_payload[:32])}")
        else:
            print(f"[DEBUG] First 32 bytes of encrypted payload: MISSING nonce after encoding")
        # stego_bytes already written below
    else:
        stego_bytes = machine.encode_audio(args.cover, payload_bytes, filename, args.lsb, args.key, start_sample=args.start)

    # Debug: Show first 32 bytes of raw audio and np.uint8 array before encoding
    import wave
    import numpy as np
    with wave.open(args.cover, 'rb') as wf:
        n_frames = wf.getnframes()
        raw_data = wf.readframes(n_frames)
        print(f"[DEBUG] First 32 bytes of raw audio: {raw_data[:32].hex()}")
        flat = np.frombuffer(raw_data, dtype=np.uint8)
        print(f"[DEBUG] np.uint8 flat shape: {flat.shape}, first 32 bytes: {flat[:32].tolist()}")



    stego_bytes = machine.encode_audio(args.cover, payload_bytes, filename, args.lsb, args.key, start_sample=args.start)

    # If encryption is enabled, print context for encryption (after encoding, so nonce is available)
    if not args.no_encrypt:
        info = getattr(machine, 'last_embed_info', None) or {}
        header = info.get('header', {})
        nonce = header.get('nonce', b'') if isinstance(header.get('nonce'), (bytes, bytearray)) else b''
        context_bytes = filename.encode('utf-8')
        if nonce:
            print(f"[DEBUG] Encrypt context: key='{args.key}', nonce={nonce.hex()}, context_bytes={context_bytes}")
        else:
            print(f"[DEBUG] Encrypt context: key='{args.key}', nonce=MISSING, context_bytes={context_bytes}  [ERROR: nonce not found after encoding]")

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
