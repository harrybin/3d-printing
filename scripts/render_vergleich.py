"""Render an STL to PNG views and extract video frames for visual comparison.

Usage:
  python scripts/render_vergleich.py stl <path.stl>
  python scripts/render_vergleich.py video <path.mp4> [n_frames]
Outputs go to model-sources/analyse/.
"""

import sys
from pathlib import Path

import numpy as np

OUT_DIR = Path(__file__).resolve().parents[1] / "model-sources" / "analyse"


def render_stl(path: Path) -> None:
    from vedo import Mesh, Plotter

    views = [("top", (0, 0, 1)), ("bottom", (0, 0, -1)), ("front", (0, -1, 0.3)), ("iso", (0.7, -0.7, 0.6)), ("side", (1, 0, 0.1))]
    for name, direction in views:
        mesh = Mesh(str(path)).color("lightsteelblue").lighting("default")
        plotter = Plotter(offscreen=True, size=(1100, 1100), bg="white")
        plotter.show(mesh, viewup="y" if name in ("top", "bottom") else "z")
        plotter.camera.SetPosition([c * 220 for c in direction])
        plotter.camera.SetFocalPoint(mesh.center_of_mass().tolist())
        plotter.reset_camera()
        out = OUT_DIR / f"stl_{name}.png"
        plotter.screenshot(str(out))
        plotter.close()
        print("out:", out)


def extract_frames(path: Path, count: int) -> None:
    import cv2

    capture = cv2.VideoCapture(str(path))
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    for index, frame_no in enumerate(np.linspace(0, total - 1, count).astype(int)):
        capture.set(cv2.CAP_PROP_POS_FRAMES, int(frame_no))
        ok, frame = capture.read()
        if not ok:
            continue
        height, width = frame.shape[:2]
        scale = 1280 / max(width, height)
        frame = cv2.resize(frame, (int(width * scale), int(height * scale)))
        out = OUT_DIR / f"video_{index:02d}.png"
        cv2.imwrite(str(out), frame)
        print("out:", out)
    capture.release()


if __name__ == "__main__":
    OUT_DIR.mkdir(exist_ok=True)
    mode = sys.argv[1]
    target = Path(sys.argv[2])
    if mode == "stl":
        render_stl(target)
    else:
        extract_frames(target, int(sys.argv[3]) if len(sys.argv) > 3 else 10)
