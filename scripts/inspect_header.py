import argparse
import struct


def parse_header(b: bytes):
    if len(b) < 4 + 1 + 1 + 8 + 4 + 1 + 4:
        raise ValueError('Too short for header')
    off = 0
    magic = b[off:off+4]; off += 4
    if magic != b'STGA':
        raise ValueError('Bad magic')
    version = b[off]; off += 1
    lsb = b[off]; off += 1
    start = struct.unpack('>Q', b[off:off+8])[0]; off += 8
    length = struct.unpack('>I', b[off:off+4])[0]; off += 4
    fname_len = b[off]; off += 1
    fname = b[off:off+fname_len].decode('utf-8', 'replace'); off += fname_len
    crc32 = struct.unpack('>I', b[off:off+4])[0]
    return {
        'version': version,
        'lsb_bits': lsb,
        'start_bit_offset': start,
        'payload_len': length,
        'filename': fname,
        'crc32': crc32,
        'header_size': off,
    }


def main():
    p = argparse.ArgumentParser(description='Inspect STGA header at the start of a byte stream (for demo).')
    p.add_argument('file', help='File to read (reads first ~256 bytes)')
    args = p.parse_args()
    with open(args.file, 'rb') as f:
        data = f.read(256)
    try:
        info = parse_header(data)
        print('Header:')
        for k, v in info.items():
            print(f'  {k}: {v}')
    except Exception as e:
        print(f'Failed to parse header: {e}')


if __name__ == '__main__':
    main()
