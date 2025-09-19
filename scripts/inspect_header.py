import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from machine.stega_spec import unpack_header


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect STGA header bytes")
    parser.add_argument("file", help="File to read (reads first 1KB)")
    args = parser.parse_args()

    data = Path(args.file).read_bytes()[:1024]
    try:
        header = unpack_header(data)
    except Exception as exc:
        raise SystemExit(f"Failed to parse header: {exc}")

    print("Header:")
    for key, value in header.items():
        if key == "nonce" and isinstance(value, (bytes, bytearray)):
            printable = value.hex()
        else:
            printable = value
        print(f"  {key}: {printable}")


if __name__ == "__main__":
    main()
