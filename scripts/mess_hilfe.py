"""Overlay a labeled pixel ruler on a source photo and estimate the 5 mm grid pitch.

Usage: python scripts/mess_hilfe.py <image> [crop_left crop_top crop_right crop_bottom]
Writes <image stem>_ruler.png into model-sources/analyse/.
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance


def grid_pitch_px(gray: np.ndarray) -> float:
    """Estimate grid pitch from the dominant FFT frequency of row/column means."""
    pitches = []
    for axis in (0, 1):
        signal = gray.mean(axis=axis)
        signal = signal - signal.mean()
        spectrum = np.abs(np.fft.rfft(signal))
        freqs = np.fft.rfftfreq(signal.size)
        mask = (freqs > 1 / 150.0) & (freqs < 1 / 25.0)
        peak = freqs[mask][np.argmax(spectrum[mask])]
        pitches.append(1.0 / peak)
    print("pitch_x_px:", round(pitches[0], 2), "pitch_y_px:", round(pitches[1], 2))
    return float(np.mean(pitches))


def main() -> None:
    src = Path(sys.argv[1])
    img = Image.open(src)
    if len(sys.argv) == 6:
        box = tuple(int(v) for v in sys.argv[2:6])
        img = img.crop(box)
    img = img.convert("RGB")
    img = ImageEnhance.Brightness(img).enhance(1.6)
    img = ImageEnhance.Contrast(img).enhance(1.3)

    gray = np.asarray(img.convert("L"), dtype=float)
    pitch = grid_pitch_px(gray)

    draw = ImageDraw.Draw(img)
    step = 100
    for x in range(0, img.width, step):
        major = x % 500 == 0
        draw.line([(x, 0), (x, 40 if major else 20)], fill="red", width=5)
        if major:
            draw.text((x + 6, 44), str(x), fill="red", font_size=48)
    for y in range(0, img.height, step):
        major = y % 500 == 0
        draw.line([(0, y), (40 if major else 20, y)], fill="red", width=5)
        if major:
            draw.text((46, y + 6), str(y), fill="red", font_size=48)

    out_dir = src.parent / "analyse"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{src.stem}_ruler.png"
    scale = 1600 / img.width
    img.resize((1600, int(img.height * scale))).save(out)
    print("out:", out)
    print("grid_pitch_px:", pitch, "-> px_per_mm:", pitch / 5.0)


if __name__ == "__main__":
    main()
