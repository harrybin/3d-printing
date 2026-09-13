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
WHITE = "#e8f7f9"
TRANSPARENT = "#b9e9f5"
BACKGROUND = "#24211f"
BED = "#5c5c5c"


def _top_polygons(mesh, z):
    triangles = mesh.vertices[mesh.faces]
    mask = np.all(np.isclose(triangles[:, :, 2], z), axis=1)
    return triangles[mask, :, :2]


def _style_2d(ax):
    ax.set_aspect("equal")
    ax.autoscale_view()
    ax.axis("off")
    ax.margins(0.035)


def render_panel_bed(panel_layout):
    figure, axis = plt.subplots(figsize=(9, 9), facecolor=BACKGROUND)
    axis.set_facecolor(BACKGROUND)
    axis.add_patch(
        plt.Rectangle(
            (-125, -125),
            250,
            250,
            facecolor=BED,
            edgecolor="white",
            linewidth=1.5,
        )
    )
    axis.add_collection(
        PolyCollection(
            _top_polygons(panel_layout, 2),
            facecolor=WHITE,
            edgecolor="#25464d",
            linewidth=0.35,
        )
    )
    axis.set_xlim(-130, 130)
    axis.set_ylim(-130, 130)
    axis.set_aspect("equal")
    axis.axis("off")
    axis.set_title(
        "Datei 2 · Vier Leuchtflächen auf 250 × 250 mm Druckbett",
        color="white",
        fontsize=17,
        pad=12,
    )
    path = OUT_DIR / "lampe-5-leuchtflaechen-druckbett.png"
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


def render_frame(transparent, black):
    figure = plt.figure(figsize=(9, 11), facecolor=BACKGROUND)
    axis = figure.add_subplot(111, projection="3d")
    axis.set_facecolor(BACKGROUND)
    _add_mesh(axis, transparent, TRANSPARENT, alpha=0.42)
    _add_mesh(axis, black, BLACK)
    _style_3d(axis)
    axis.set_title(
        "Datei 1 · Rahmen\n20 mm transparent + 20 mm schwarz",
        color="white",
        fontsize=16,
        pad=4,
    )
    path = OUT_DIR / "lampe-5-rahmen.png"
    figure.savefig(path, dpi=200, bbox_inches="tight", facecolor=figure.get_facecolor())
    plt.close(figure)
    return path


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    transparent, black, panels = lampe_5.build_parts()
    panel_layout = lampe_5.arrange_panels(panels)
    for path in (
        render_frame(transparent, black),
        render_panel_bed(panel_layout),
    ):
        print("out:", path)


if __name__ == "__main__":
    main()
