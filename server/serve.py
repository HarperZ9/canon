"""Source and frozen Canon client entrypoint; no installation or ambient grants."""
from pathlib import Path
import sys

if not getattr(sys, 'frozen', False):
    vendored = Path(__file__).resolve().parent / 'src'
    source = vendored if vendored.is_dir() else Path(__file__).resolve().parents[2] / 'src'
    sys.path.insert(0, str(source))

from canon.client_mcp import main

if __name__ == '__main__':
    raise SystemExit(main())
