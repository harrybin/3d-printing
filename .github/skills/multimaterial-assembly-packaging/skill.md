---
name: multimaterial-assembly-packaging
description: Package complex models as an assembled master 3MF and printable plate 3MFs, preferring separately printed keyed color parts to reduce purge waste.
---

# Multimaterial assembly packaging

Use this skill for complex assemblies, multiple materials, multiple colors, or models
that need different print orientations.

## Required deliverables

For new complex models or substantial revisions, produce:

- `models/<model>-master.3mf`: the complete assembled object with named, separate
  bodies and intended material/color semantics
- `models/<model>-print-<plate-or-material>.3mf`: one or more project files arranged
  for actual printing
- `models/<model>-part-<name>.stl`: optional per-body interchange or validation
  meshes

The master file is the overview and assembly source. Print files optimize
orientation, plate use, supports, material, and print order. A collection of STL
files does not replace the master 3MF.

Create exactly one printable OrcaSlicer project 3MF for each actual
material/color/spool combination. Put every part using that spool in this project;
do not split one spool into separate 3MF files merely because parts need different
orientations, supports, or process overrides. Use multiple plates inside the same
project when the bed, support clearance, or print-risk isolation requires it.
Parts sharing both material and color should share a plate when they fit safely;
for example, bone-colored fingers and bone parts belong on one plate rather than
in separate files.

## Purge-minimizing color strategy

Before assigning ACE Pro color changes within one printed object, evaluate whether
each visible color can become a separately printed body.

Prefer separate color bodies when they can be assembled without unacceptable:

- visible gaps
- loss of strength
- excessive part count
- inaccessible assembly
- loss of the intended surface

Use in-place multicolor only when separation is impractical or explicitly preferred
by the user. Avoid small isolated color islands and repeated layer-by-layer tool
changes.

## Assembly design

Separately printed bodies must be positively located. Choose a connection suited to
the load and assembly direction:

- keyed pin and socket
- tongue and groove
- registration step
- dovetail
- snap feature
- screw or insert where serviceability is required

Make joints asymmetric or keyed when incorrect orientation is possible. Keep
clearance as a named parameter and follow the material/fit rules from
`stl-create-edit-interview` and `optimize-stl-for-print`. Create a test coupon when a
joint controls an expensive print.

Do not use glue as an undocumented substitute for missing alignment geometry.

Material/color separation is not complete until the separated bodies can be
physically assembled in the real mechanism. For every interface between print
projects:

- define an unobstructed insertion direction and a feasible assembly order;
- keep fasteners, pins, keys, retaining clips and tool access reachable after the
  surrounding parts are installed;
- prove the insertion sweep against already-installed bodies, not only the final
  static pose;
- verify zero unintended intersection between the assembled bodies; gear contact,
  coaxial bearings and press fits must be represented by explicit clearances rather
  than overlapping solids;
- split an integral cross-material shaft/gear into a keyed coupling when the
  integral part cannot pass through its bearings or enclosure;
- document which material project contains every half of the joint and how it is
  retained against axial withdrawal.

A render showing parts in the right final location is not assembly proof. Reject a
design when a part can reach its final pose only by passing through another solid.

## Packaging checks

- Names and transforms are stable across master and print files.
- Master assembly has the correct final relative positions.
- Print plates contain every required body exactly once unless duplicates are
  intentional.
- Every material/color/spool combination has one and only one printable project
  3MF; plate boundaries must not create duplicate project files.
- Material and color assignments match the documentation.
- Every body passes mesh validation independently.
- Mating pairs preserve their measured clearance after export.
- Every cross-project joint has a collision-free insertion path, reachable
  retention feature and documented assembly sequence.
- The final assembly has no unintended material/material intersections.
- A bill of parts maps master objects to print plates and optional STL files.

## OrcaSlicer handoff

Run `orcaslicer-print-validation` for every print 3MF. Compare separate-part plates
with the in-place multicolor alternative when purge waste or print time drives the
decision. Record the chosen strategy and evidence.

## Final evidence

Provide:

- a rendered assembled view of the master 3MF
- a slicer preview of every print plate
- the bill of parts and assembly order
- any required hardware, adhesive, or post-processing
- remaining fit or color-alignment risk
