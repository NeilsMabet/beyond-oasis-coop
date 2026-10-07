"""Apply the release BPS patch using only the Python 3 standard library."""
import argparse
import hashlib
import json
from pathlib import Path
from bps import apply

ROOT = Path(__file__).resolve().parent.parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=ROOT/'generated/Beyond Oasis Coop.bin')
    args = parser.parse_args()
    try:
        if args.rom.resolve() == args.output.resolve():
            raise ValueError('Output must differ from the original ROM.')
        if not args.rom.is_file():
            raise ValueError('Original ROM file not found: ' + str(args.rom))
        manifest = json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
        source = args.rom.read_bytes()
        if hashlib.sha256(source).hexdigest() != manifest['original_sha256']:
            raise ValueError('Unsupported ROM SHA-256. See README for the required original dump.')
        patch = (ROOT/'beyond-oasis-coop.bps').read_bytes()
        if hashlib.sha256(patch).hexdigest() != manifest['bps_sha256']:
            raise ValueError('BPS checksum mismatch. Download the release again.')
        target = apply(source, patch)
        digest = hashlib.sha256(target).hexdigest()
        if len(target) != manifest['patched_size'] or digest != manifest['patched_sha256']:
            raise ValueError('Patched ROM checksum or size mismatch.')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(target)
    except (OSError, ValueError, AssertionError, IndexError) as exc:
        parser.exit(1, 'Error: ' + (str(exc) or 'Invalid BPS patch.') + '\n')
    print('Ready:', args.output)
    print('SHA-256:', digest)

if __name__ == '__main__':
    main()
