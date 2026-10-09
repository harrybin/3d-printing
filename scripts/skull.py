"""A printable skull, used for the trigger button and the lid cartouche.

The soft masses - braincase, face, jaw - are a blended capsule field, because a
boolean union of spheres leaves hard creases exactly where a skull is smooth.
The features that make a shape *read* as a skull are the opposite: orbits, the
nasal aperture and the tooth row all have crisp rims, so they are cut as proper
booleans afterwards instead of as smooth-maximum voids.

Local frame: +X to the viewer's right, +Y up, +Z out of the face.
"""

from __future__ import annotations

import numpy as np
import trimesh

from mesh_kit import (box, clean, cylinder, difference, intersection,
                      rounded_box, simplify, union)
from sdf_bones import chain, segment_mesh, sphere


def _masses():
    """Braincase, face block and mandible as round cones. About 44 x 56 mm."""
    cranium = [
        sphere((0.0, 12.0, -2.0), 17.0),
        ((0.0, 3.0, 1.0), (0.0, -5.0, 4.0), 15.5, 12.5),
        ((0.0, -5.0, 4.0), (0.0, -13.0, 5.0), 12.5, 9.0),
    ]
    jaw = chain(
        [(-11.5, -9.0, -3.0), (-11.0, -18.0, 1.0), (0.0, -21.5, 5.0),
         (11.0, -18.0, 1.0), (11.5, -9.0, -3.0)],
        [3.2, 3.6, 4.0, 3.6, 3.2],
    )
    return cranium + jaw


def _cutters():
    """Orbits, nasal aperture, tooth row and the flats on the temples."""
    cuts = []
    for side in (-1.0, 1.0):
        centre = (side * 8.2, 2.0, 14.0)
        orbit = rounded_box((13.5, 13.0, 26.0), 2.6, centre)
        orbit.apply_transform(trimesh.transformations.rotation_matrix(
            np.deg2rad(side * -9.0), [0.0, 0.0, 1.0], centre))
        cuts.append(orbit)
        # Temple flats keep the braincase from reading as a ball.
        cuts.append(box((14.0, 44.0, 30.0), (side * 27.0, 8.0, 2.0)))

    # Piriform aperture: a box on its corner gives the inverted-heart opening.
    nose = box((7.2, 11.0, 24.0), (0.0, -6.5, 14.0))
    nose.apply_transform(trimesh.transformations.rotation_matrix(
        np.deg2rad(45.0), [0.0, 0.0, 1.0], [0.0, -6.5, 14.0]))
    cuts.append(nose)
    cuts.append(box((4.6, 5.0, 24.0), (0.0, -3.0, 14.0)))

    # Bite line plus the gaps between the teeth. The cutters run clear through
    # the jaw - stopping them inside it leaves tangential knife edges.
    cuts.append(box((23.0, 1.4, 34.0), (0.0, -15.4, 10.0)))
    for i in range(-4, 5):
        cuts.append(box((1.0, 5.0, 34.0), (i * 2.6, -15.4, 10.0)))

    cuts.append(box((44.0, 14.0, 30.0), (0.0, -29.0, 6.0)))
    return cuts


def build_skull(scale: float = 1.0, pitch: float = 0.45) -> trimesh.Trimesh:
    mesh = simplify(segment_mesh(_masses(), pitch=pitch, blend=2.6), 30000)
    mesh = difference(mesh, [union(_cutters())])
    # The capsule field builds a tall egg; a cranium is wider than it is long.
    mesh.apply_scale([1.24, 0.94, 1.0])
    mesh = clean(simplify(mesh, 18000))
    if scale != 1.0:
        mesh.apply_scale(scale)
    return mesh


def skull_relief(scale: float = 1.0, depth: float = 5.0) -> trimesh.Trimesh:
    """Front slice of the skull, sitting on z = 0 and rising to z = ``depth``.

    The skull is squashed along its depth axis first. Slicing the unsquashed
    dome would only yield the crown; compressing it keeps the whole face -
    orbits, nasal aperture and tooth row - inside the relief height.
    """
    full = build_skull(scale)
    full.apply_scale([1.0, 1.0, depth * 2.4 / full.extents[2]])
    hi = full.bounds[1]
    span = full.extents
    slab = box((span[0] + 10.0, span[1] + 10.0, depth * 2.0),
               (full.centroid[0], full.centroid[1], hi[2] - depth))
    relief = intersection([full, slab])
    relief.apply_translation([0.0, 0.0, depth - hi[2]])
    return clean(relief)


def build_drive_knob(scale: float = 1.15, shaft_d: float = 8.0) -> trimesh.Trimesh:
    """Large skull knob with a blind press-fit socket for the drive shaft."""
    knob = build_trigger(scale=scale, stem_d=14.0, stem_len=9.0,
                         flange_d=34.0)
    socket = cylinder((shaft_d - 0.2) / 2.0, 10.0, (0.0, 0.0, -7.0))
    return clean(difference(knob, [socket]))


def build_trigger(scale: float = 1.0, stem_d: float = 4.0,
                  stem_len: float = 5.5,
                  flange_d: float = 30.0) -> trimesh.Trimesh:
    """Skull push button with a short plunger for the internal latch cam.

    The button is modelled face-up from z = 0 so it prints without support.
    Its stem and shallow rear rib run down the -Z axis and stop before the cam,
    leaving the button's operating travel instead of intersecting the latch.
    """
    head = skull_relief(scale, depth=13.0 * scale)
    head.apply_scale([1.0, 1.0, 0.5])
    head.apply_translation([0.0, 0.0, -head.bounds[0][2]])
    flange = cylinder(flange_d * scale / 2.0, 3.0, (0.0, 0.0, -1.5))
    stem = cylinder(stem_d / 2.0, stem_len, (0.0, 0.0, -3.0 - stem_len / 2.0))
    rib = box((3.0, flange_d * scale - 6.0, 3.0), (0.0, 0.0, -4.5))
    return clean(union([head, flange, stem, rib]))
