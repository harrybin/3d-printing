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

    # The maxillary process follows the dental arch rather than bridging the
    # face as one straight bar. The smaller intermediate nodes keep the
    # alveolar rim visible around the roots after the oral cavity is opened.
    face.extend(chain(
        [(-10.5, -9.8, 4.8), (-6.0, -12.0, 6.0),
         (0.0, -13.0, 7.0), (6.0, -12.0, 6.0),
         (10.5, -9.8, 4.8)],
        [4.5, 4.6, 4.9, 4.6, 4.5],
    ))
    # A flared angle, narrower tooth-bearing body and central mental eminence
    # read more like a mandible than the former uniform U-shaped tube.
    jaw = chain(
        [(-11.8, -12.5, 0.0), (-11.0, -18.0, 1.8),
         (-7.0, -21.0, 3.4), (0.0, -22.0, 5.4),
         (7.0, -21.0, 3.4), (11.0, -18.0, 1.8),
         (11.8, -12.5, 0.0)],
        [4.1, 4.0, 3.8, 4.8, 3.8, 4.0, 4.1],
    )
    return cranium + face + jaw


def _cutters():
    """Orbits, nasal aperture, oral cavity and the flats on the temples."""
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

    # Open a shallow oval oral cavity. The remaining back wall joins every
    # tooth root to the skull, while the crowns stand free at the surface.
    mouth = solid_sphere(1.0, subdivisions=3)
    mouth.apply_scale([11.8, 6.2, 8.0])
    mouth.apply_translation((0.0, -16.1, 17.0))
    cuts.append(mouth)

    cuts.append(box((44.0, 14.0, 30.0), (0.0, -29.0, 6.0)))
    return cuts


def _dental_arcade() -> list[trimesh.Trimesh]:
    """Upper and lower permanent teeth sized for a 0.4 mm nozzle.

    Each side has a central and lateral incisor, canine, premolar and visible
    first molar. Crowns remain at least 1.45 mm wide before the final X scale,
    and their roots overlap the alveolar backing below the opened mouth.
    """
    x_positions = (0.95, 2.85, 4.75, 6.75, 8.85)
    widths = (1.55, 1.45, 1.50, 1.65, 1.90)
    upper_heights = (3.45, 3.20, 3.80, 2.85, 2.60)
    lower_heights = (3.05, 2.85, 3.35, 2.65, 2.45)
    upper_y = (-13.55, -13.65, -13.90, -14.35, -14.90)
    lower_y = (-17.65, -17.55, -17.35, -17.05, -16.80)
    projection = (11.35, 11.20, 11.45, 10.95, 10.65)

    teeth = []
    for side in (-1.0, 1.0):
        for index, x in enumerate(x_positions):
            for y, height, lower in (
                (upper_y[index], upper_heights[index], False),
                (lower_y[index], lower_heights[index], True),
            ):
                tooth = solid_sphere(1.0, subdivisions=2)
                depth = 2.75 if index < 3 else 2.55
                tooth.apply_scale([widths[index] / 2.0, height / 2.0, depth])
                tooth.apply_translation(
                    (side * x, y, projection[index] - (0.15 if lower else 0.0))
                )
                # Canines lean slightly toward the corners of the mouth;
                # posterior crowns follow the turn of the dental arcade.
                angle = side * (2.0 + index * 1.6)
                tooth.apply_transform(trimesh.transformations.rotation_matrix(
                    np.deg2rad(angle), [0.0, 0.0, 1.0], tooth.centroid))
                teeth.append(tooth)
    return teeth


def build_skull(scale: float = 1.0, pitch: float = 0.45) -> trimesh.Trimesh:
    mesh = simplify(segment_mesh(_masses(), pitch=pitch, blend=2.6), 30000)
    mesh = difference(mesh, [union(_cutters())])
    mesh = union([mesh, *_dental_arcade()])
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


def build_drive_knob(scale: float = 1.15, shaft_d: float = 8.0,
                     flat_depth: float = 1.0, flat_angle: float = 32.0,
                     cross_pin_z: float = -7.4) -> trimesh.Trimesh:
    """Large skull knob with a keyed D-socket for the drive shaft.

    The blind socket (z -12..-2) takes the pinion's D-flat with 0.15 mm
    per-side clearance.  ``flat_angle`` turns the flat so the skull faces
    forward at the stowed stop (mechanism.KNOB_STOW_ANGLE).  A 1.75 mm
    filament cross pin through stem and shaft at ``cross_pin_z`` holds the
    knob axially.
    """
    import fdm_joints

    knob = build_trigger(scale=scale, stem_d=14.0, stem_len=9.0,
                         flange_d=34.0)
    socket = fdm_joints.d_bore_cutter(
        shaft_d, 10.0, flat_depth,
        clearance=fdm_joints.CLEARANCE_CLOSE_PER_SIDE,
        center=(0.0, 0.0, -7.0))
    socket.apply_transform(trimesh.transformations.rotation_matrix(
        np.deg2rad(flat_angle), (0.0, 0.0, 1.0)))
    angle = np.deg2rad(flat_angle)
    cross = fdm_joints.cross_pin_hole(
        14.0, axis=(-np.sin(angle), np.cos(angle), 0.0),
        center=(0.0, 0.0, cross_pin_z))
    return clean(difference(knob, [socket, cross]))


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
