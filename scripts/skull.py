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
                      simplify, sphere as solid_sphere, union)
from sdf_bones import chain, segment_mesh, sphere


def _masses():
    """Anatomical masses for the braincase, face, cheekbones and mandible."""
    cranium = [
        sphere((0.0, 12.0, -2.0), 17.0),
        # The forehead rolls into the nasal bridge instead of ending in a
        # spherical overhang above two holes.
        ((0.0, 10.0, 5.0), (0.0, -3.0, 8.0), 9.0, 5.2),
        ((0.0, 3.0, 1.0), (0.0, -5.0, 4.0), 15.5, 12.5),
        ((0.0, -5.0, 4.0), (0.0, -13.0, 5.0), 12.5, 9.0),
    ]

    face = []
    for side in (-1.0, 1.0):
        # Supraorbital ridge and zygomatic buttress are the landmarks missing
        # from the old egg-shaped face. They stay inside the cranium envelope.
        face.extend([
            ((side * 2.0, 7.0, 8.5), (side * 12.5, 5.2, 7.2), 2.5, 3.0),
            ((side * 13.0, 3.0, 3.0), (side * 13.5, -6.5, 7.0), 2.8, 3.3),
            sphere((side * 13.5, -6.5, 7.0), 3.3),
            # Ascending ramus gives the mandible a recognisable rear corner.
            ((side * 11.3, -7.0, -2.5),
             (side * 12.0, -16.0, 0.5), 3.4, 4.0),
        ])

    # Maxillary/alveolar bow plus a U-shaped mandible and a modest chin.
    face.extend(chain(
        [(-10.0, -9.5, 5.2), (0.0, -12.0, 7.2), (10.0, -9.5, 5.2)],
        [4.8, 5.3, 4.8],
    ))
    jaw = chain(
        [(-11.8, -13.0, 0.0), (-10.5, -19.0, 2.5),
         (0.0, -22.0, 5.5), (10.5, -19.0, 2.5), (11.8, -13.0, 0.0)],
        [4.0, 4.2, 4.7, 4.2, 4.0],
    )
    return cranium + face + jaw


def _cutters():
    """Orbits, nasal aperture, tooth row and the flats on the temples."""
    cuts = []
    for side in (-1.0, 1.0):
        centre = (side * 8.2, 2.0, 14.0)
        # A tilted ellipsoid produces the rounded orbit and stronger lateral
        # rim seen in the licensed CT reference; the previous rounded box made
        # the eyes look machined.
        orbit = solid_sphere(1.0, subdivisions=3)
        orbit.apply_scale([6.2, 5.6, 14.0])
        orbit.apply_translation(centre)
        orbit.apply_transform(trimesh.transformations.rotation_matrix(
            np.deg2rad(side * -9.0), [0.0, 0.0, 1.0], centre))
        cuts.append(orbit)
        # Temple flats keep the braincase from reading as a ball.
        cuts.append(box((14.0, 44.0, 30.0), (side * 27.0, 8.0, 2.0)))

    # Overlapping ellipsoids form a piriform nasal aperture: narrow at the
    # bridge and broad at the lower maxilla, without a diamond-shaped rim.
    nose_upper = solid_sphere(1.0, subdivisions=2)
    nose_upper.apply_scale([2.5, 5.0, 14.0])
    nose_upper.apply_translation((0.0, -4.2, 14.0))
    nose_lower = solid_sphere(1.0, subdivisions=2)
    nose_lower.apply_scale([4.0, 4.2, 14.0])
    nose_lower.apply_translation((0.0, -8.2, 14.0))
    cuts.extend([nose_upper, nose_lower])

    # Bite line plus the gaps between the teeth. The cutters run clear through
    # the jaw - stopping them inside it leaves tangential knife edges.
    cuts.append(box((23.0, 1.0, 34.0), (0.0, -15.4, 10.0)))
    tooth_gaps = (-8.8, -6.4, -4.2, -2.2, 0.0, 2.2, 4.2, 6.4, 8.8)
    for x in tooth_gaps:
        width = 0.65 if abs(x) <= 4.2 else 0.8
        cuts.append(box((width, 4.2, 34.0), (x, -15.4, 10.0)))

    cuts.append(box((44.0, 14.0, 30.0), (0.0, -29.0, 6.0)))
    return cuts


def build_skull(scale: float = 1.0, pitch: float = 0.45) -> trimesh.Trimesh:
    mesh = simplify(segment_mesh(_masses(), pitch=pitch, blend=2.6), 30000)
    mesh = difference(mesh, [union(_cutters())])
    # Keep the established control envelope after adding the lateral cheekbone
    # masses; the old cranium needed more X stretch because it had no zygoma.
    mesh.apply_scale([1.208, 0.94, 1.0])
    mesh = clean(simplify(mesh, 30000))
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
