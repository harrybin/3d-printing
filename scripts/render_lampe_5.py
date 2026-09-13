"""Render documented construction and final views of the number-5 lamp."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import lampe_5


OUT_DIR = Path(__file__).resolve().parents[1] / "docs" / "images"
BLACK = "#171717"
WHITE = "#f5f5ef"
TRANSPARENT = "#b9e9f5"
BACKGROUND = "#24211f"


def _top_polygons(mesh, z):
    triangles = mesh.vertices[mesh.faces]
    mask = np.all(np.isclose(triangles[:, :, 2], z), axis=1)
    return triangles[mask, :, :2]


def _style_2d(ax):
    ax.set_aspect("equal")
    ax.autoscale_view()
    ax.axis("off")
    ax.margins(0.035)


def render_construction(transparent, black, panels):
    figure, axes = plt.subplots(1, 3, figsize=(15, 7), facecolor=BACKGROUND)
    stages = [
        ("1 · Transparenter Rückrahmen", [(transparent, TRANSPARENT, 20)]),
        ("2 · Schwarzer Frontrahmen", [(black, BLACK, 40)]),
        ("3 · Vier separate Leuchtflächen", [(panel, WHITE, 40) for panel in panels]),
    ]

    for axis, (title, entries) in zip(axes, stages):
        axis.set_facecolor(BACKGROUND)
        for mesh, color, z in entries:
            axis.add_collection(
                PolyCollection(
                    _top_polygons(mesh, z),
                    facecolor=color,
                    edgecolor="#111111",
                    linewidth=0.18,
                )
            )
        _style_2d(axis)
        axis.set_title(title, color="white", fontsize=14, pad=12)

    figure.suptitle(
        "Lampe „5“ · Aufbau der getrennten Materialkörper",
        color="white",
        fontsize=19,
        y=0.97,
    )
    figure.tight_layout()
    path = OUT_DIR / "lampe-5-aufbau.png"
    figure.savefig(path, dpi=180, bbox_inches="tight", facecolor=figure.get_facecolor())
    plt.close(figure)
    return path


def render_front(black, panels):
    figure, axis = plt.subplots(figsize=(8, 10), facecolor=BACKGROUND)
    axis.set_facecolor(BACKGROUND)

    # A soft halo indicates the transparent rear half without obscuring the model.
    outline = np.vstack([polygon for polygon in _top_polygons(black, 40)])
    for width, alpha in ((18, 0.035), (10, 0.06), (5, 0.09)):
        axis.scatter(
            outline[:, 0],
            outline[:, 1],
            s=width * width,
            color="#ffe6a4",
            alpha=alpha,
            linewidths=0,
        )

    axis.add_collection(
        PolyCollection(
            _top_polygons(black, 40),
            facecolor=BLACK,
            edgecolor="#050505",
            linewidth=0.25,
        )
    )
    for panel in panels:
        axis.add_collection(
            PolyCollection(
                _top_polygons(panel, 40),
                facecolor=WHITE,
                edgecolor="#cfcfc7",
                linewidth=0.2,
            )
        )

    _style_2d(axis)
    axis.set_title(
        "Fertiges Modell · Frontansicht · 240 mm hoch",
        color="white",
        fontsize=17,
        pad=12,
    )
    path = OUT_DIR / "lampe-5-frontansicht.png"
    figure.savefig(path, dpi=200, bbox_inches="tight", facecolor=figure.get_facecolor())
    plt.close(figure)
    return path


def _add_mesh(axis, mesh, color, alpha=1.0):
    # Display axes are X (width), Z (depth), Y (height).
    triangles = mesh.vertices[mesh.faces][:, :, [0, 2, 1]]
    collection = Poly3DCollection(
        triangles,
        facecolor=color,
        edgecolor="#090909",
        linewidth=0.04,
        alpha=alpha,
    )
    axis.add_collection3d(collection)


def _style_3d(axis):
    axis.set_xlim(-105, 105)
    axis.set_ylim(-5, 48)
    axis.set_zlim(-130, 130)
    axis.set_box_aspect((210, 75, 260))
    axis.view_init(elev=11, azim=-56)
    axis.set_axis_off()


def render_perspective(transparent, black, panels):
    figure = plt.figure(figsize=(9, 11), facecolor=BACKGROUND)
    axis = figure.add_subplot(111, projection="3d")
    axis.set_facecolor(BACKGROUND)
    _add_mesh(axis, transparent, TRANSPARENT, alpha=0.42)
    _add_mesh(axis, black, BLACK)
    for panel in panels:
        _add_mesh(axis, panel, WHITE)
    _style_3d(axis)
    axis.set_title(
        "Fertiges Modell · Perspektive\n"
        "20 mm transparent + 20 mm schwarz · separate Leuchtflächen",
        color="white",
        fontsize=16,
        pad=4,
    )
    path = OUT_DIR / "lampe-5-perspektive.png"
    figure.savefig(path, dpi=200, bbox_inches="tight", facecolor=figure.get_facecolor())
    plt.close(figure)
    return path


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    transparent, black, panels = lampe_5.build_parts()
    for path in (
        render_construction(transparent, black, panels),
        render_front(black, panels),
        render_perspective(transparent, black, panels),
    ):
        print("out:", path)


if __name__ == "__main__":
    main()
