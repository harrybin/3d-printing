"""Hill-shaded previews of the cached gothic chest relief height maps.

Grayscale height alone is a poor judge of a bas relief - a flat ribbon and a
rounded carved stem look identical.  A Lambert hill shade with a low light
exposes exactly the thing the user complained about: whether the motif reads
as a sculpted creature or as a stamped outline.

    .\\.venv\\Scripts\\python.exe scripts\\preview_chest_reliefs.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "assets" / "gothic-chest-reliefs"
OUT = ROOT / "build" / "ornament-audit"
LIGHT = np.array([-0.55, 0.62, 0.56])


def hillshade(heights: np.ndarray, pitch: float, depth: float) -> np.ndarray:
    z = heights * depth
    gy, gx = np.gradient(z, pitch)
    normals = np.dstack([-gx, -gy, np.ones_like(z)])
    normals /= np.linalg.norm(normals, axis=2, keepdims=True)
    light = LIGHT / np.linalg.norm(LIGHT)
    shade = np.clip(normals @ light, 0.0, 1.0) ** 1.4
    ambient = 0.18 + 0.30 * np.clip(heights, 0.0, 1.0)
    return np.clip(0.26 * ambient + 0.82 * shade, 0.0, 1.0)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for npz in sorted(CACHE.glob("*.npz")):
        data = np.load(npz)
        heights = data["heights"].astype(np.float64)
        pitch = float(data["pitch"])
        grey = (np.flipud(heights) * 255).astype(np.uint8)
        Image.fromarray(grey).resize(
            (grey.shape[1] * 3, grey.shape[0] * 3), Image.LANCZOS
        ).save(OUT / f"height-{npz.stem}.png")
        shade = hillshade(heights, pitch, 2.6)
        img = (np.flipud(shade) * 255).astype(np.uint8)
        Image.fromarray(img).resize(
            (img.shape[1] * 3, img.shape[0] * 3), Image.LANCZOS
        ).save(OUT / f"shade-{npz.stem}.png")
        print(f"{npz.stem:5s} {heights.shape} -> shade-{npz.stem}.png")


if __name__ == "__main__":
    main()
