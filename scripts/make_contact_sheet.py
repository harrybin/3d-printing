"""Build a numbered contact sheet (index image) from a folder of reference images.

Reading every reference photo at full resolution burns context and most of them
answer nothing. The contact sheet is looked at once; afterwards only the tiles
that actually show the feature in question are opened at full size.

Usage:
    python scripts/make_contact_sheet.py model-sources
    python scripts/make_contact_sheet.py model-sources --out docs/images/index.png
    python scripts/make_contact_sheet.py model-sources --cols 5 --tile 420 --recursive

The printed legend maps every tile number to its source path, so a later step can
say "open tile 07" and resolve it without re-listing the folder.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
LABEL_H = 34
PAD = 8
BG = (255, 255, 255)
LABEL_BG = (32, 32, 32)
LABEL_FG = (255, 255, 255)


def collect(folder: Path, recursive: bool) -> list[Path]:
    walker = folder.rglob("*") if recursive else folder.glob("*")
    files = [p for p in walker if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES]
    return sorted(files, key=lambda p: str(p).lower())


def make_tile(path: Path, index: int, tile: int) -> np.ndarray:
    canvas = np.full((tile + LABEL_H, tile, 3), BG, dtype=np.uint8)
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        cv2.putText(canvas, "unreadable", (10, tile // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 200), 2)
    else:
        h, w = img.shape[:2]
        scale = tile / max(h, w)
        resized = cv2.resize(img, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
        rh, rw = resized.shape[:2]
        y0, x0 = (tile - rh) // 2, (tile - rw) // 2
        canvas[y0:y0 + rh, x0:x0 + rw] = resized

    cv2.rectangle(canvas, (0, tile), (tile, tile + LABEL_H), LABEL_BG, -1)
    # Keep the tile caption short: the number is the handle, the stem disambiguates.
    stem = path.stem
    caption = f"{index:02d}  {stem if len(stem) <= 22 else '...' + stem[-19:]}"
    cv2.putText(canvas, caption, (6, tile + 23), cv2.FONT_HERSHEY_SIMPLEX, 0.52, LABEL_FG, 1, cv2.LINE_AA)
    return canvas


def build_sheet(paths: list[Path], cols: int, tile: int) -> np.ndarray:
    rows = (len(paths) + cols - 1) // cols
    cell_w, cell_h = tile + PAD, tile + LABEL_H + PAD
    sheet = np.full((rows * cell_h + PAD, cols * cell_w + PAD, 3), BG, dtype=np.uint8)
    for i, path in enumerate(paths):
        r, c = divmod(i, cols)
        y, x = PAD + r * cell_h, PAD + c * cell_w
        sheet[y:y + tile + LABEL_H, x:x + tile] = make_tile(path, i, tile)
    return sheet


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", type=Path, help="folder holding the reference images")
    ap.add_argument("--out", type=Path, default=None, help="output png (default <folder>/_index.png)")
    ap.add_argument("--cols", type=int, default=5)
    ap.add_argument("--tile", type=int, default=360, help="tile edge length in px")
    ap.add_argument("--recursive", action="store_true")
    args = ap.parse_args()

    if not args.folder.is_dir():
        print(f"error: {args.folder} is not a directory", file=sys.stderr)
        return 2

    paths = collect(args.folder, args.recursive)
    if not paths:
        print(f"error: no images found in {args.folder}", file=sys.stderr)
        return 2

    out = args.out or args.folder / "_index.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), build_sheet(paths, args.cols, args.tile))

    print(f"sheet: {out}  ({len(paths)} images, {args.cols} cols, tile {args.tile}px)")
    print("legend:")
    for i, path in enumerate(paths):
        print(f"  {i:02d}  {path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
