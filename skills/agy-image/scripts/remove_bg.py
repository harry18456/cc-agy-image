#!/usr/bin/env python3
"""Remove an image's background with rembg (u2net) -> a real transparent-alpha PNG.

Used by the agy-image skill for transparent-background requests, because neither
`agy` (Nano Banana) nor the `codex` CLI produce genuine alpha — they fake it (white
key / painted checkerboard). rembg segments the subject from ANY background, so it
does not need a clean solid-colour plate.

Usage:
    python remove_bg.py <input-image> <output.png>

Fully local: no API key, no cloud. Auto-installs rembg if missing; first run
downloads a ~176MB model to ~/.u2net/.
"""
import subprocess
import sys
from pathlib import Path


def ensure_rembg() -> None:
    try:
        import rembg  # noqa: F401
    except ImportError:
        print("rembg not installed - installing once (rembg + onnxruntime)...", file=sys.stderr)
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", "rembg", "onnxruntime", "pillow"],
            check=True,
        )


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: python remove_bg.py <input-image> <output.png>", file=sys.stderr)
        sys.exit(2)
    inp, out = sys.argv[1], sys.argv[2]
    if not Path(inp).exists():
        print(f"input not found: {inp}", file=sys.stderr)
        sys.exit(1)

    ensure_rembg()
    from rembg import remove
    from PIL import Image

    img = Image.open(inp).convert("RGBA")
    result = remove(img)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    result.save(out)

    lo, hi = result.getchannel("A").getextrema()
    print(f"OK {out} mode=RGBA size={result.size} alpha={lo}-{hi}")
    if hi == 0:
        print("WARNING: output is fully transparent - segmentation likely failed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
