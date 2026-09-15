---
name: edit-stl-transform
description: Edit STL geometry (scale/rotate/translate/split/merge) while preserving printability constraints.
---

# Edit STL Transform

Use this skill when changing existing STL models.

Perform all edits with the project Python libraries (venv `.venv`): **trimesh** (+ **numpy**) for transforms, merges, splits, and validation, **manifold3d** for boolean operations, **vedo** for post-edit render verification. Never edit STL text or facet data by hand; if a shape change exceeds simple transforms, regenerate from the parametric source script (build123d) instead.

## Supported edits

- Scale (uniform or per-axis)
- Rotate/orient for printability
- Translate/origin alignment
- Merge/split solid groups
- Basic simplification: remove duplicate vertices and degenerate faces only. Do not perform mesh decimation or polygon reduction.

## Tooling shortcut

`scripts/mesh_tool.py` covers the routine transforms with ASCII STL output and the
bed conventions already applied:

```powershell
python scripts\mesh_tool.py transform models\part.stl -o models\part_v2.stl --rotate z,90
python scripts\mesh_tool.py transform models\part.stl -o models\part_v2.stl --fit 250x250x260
python scripts\mesh_tool.py center    models\part.stl --drop
python scripts\mesh_tool.py boolean union models\a.stl models\b.stl -o models\merged.stl
python scripts\mesh_tool.py arrange   models\a.stl models\b.stl -o models\plate.stl --gap 5
```

Print-orientation rotations belong in a new file or the slicer, never overwriting a
generator's output. For anything beyond a transform, change the parametric source
script and regenerate.

## German `wenden` for vertical models

When the user says `nun das objekt wenden (oben <--> unten)` about a vertical
print model, interpret it as a complete top-to-bottom inversion: the face currently
on the print bed becomes the top, and its opposite face becomes the print-bed
contact face. For an upright model, this is normally a 180-degree rotation around
the X axis, followed by dropping the transformed model back to Z=0.

1. Keep the script-generated source STL unchanged. Write the result as a derived
   sibling named `<base>-druckorientiert.stl`; do not overwrite the original.
2. Apply the X-axis 180-degree rotation and align the new lowest Z extent to the
   bed. Recompute and report the bounding box.
3. Verify the intended inversion programmatically before describing it as flipped.
   Intersect the mesh with thin Z slabs at its minimum and maximum Z extents, or
   otherwise measure the bed-contact area, and confirm that the former contact face
   is now at the top and the opposite face is now at the bed.
4. State the physical orientation in feature terms when known. For example, the
   validated pepper-mill insert has its round collar (`Kragen`) on the print bed
   and its smooth shaft facing upward after `wenden`.

## Required behavior

- Preserve manifold/watertight topology.
- Recompute/report bounding box after each transform.
- Maintain intended units (mm).
- Flag if edits create non-printable thin features.
- If a requested transform would create features below the minimum wall thickness, warn the user with the specific offending dimension, propose the maximum safe transform value that preserves printability, and do not apply the transform until the user confirms.
- If the edit is driven by reference photos, build or refresh the numbered contact sheet first (`python scripts/make_contact_sheet.py <image folder>`), read it once, and open only the tiles that show the feature being changed. See `stl-from-image-measurements` step 0.
- If the goal is to make an existing model match photos more closely, do not keep chaining ad-hoc transforms on the latest STL. Freeze trusted dimensions and switch to `photo-anchor-candidate-fit`; if the outer shell itself is under-constrained across several views, switch to `visual-hull-envelope-fit`.
- If a local region is structurally wrong, do not keep patching it with transforms and booleans. Switch to `partial-rebuild-instead-of-mutate`.

## Printability checks after editing

- Wall thickness still meets target (0.8 mm minimum for 0.4 nozzle baseline).
- Overhang risk analyzed (>60 degrees likely needs support).
- Mating/fit surfaces preserve required clearances.
- Normals stay outward and consistent.

## Multi-color (ACE Pro)

- Keep color-part boundaries aligned after transforms.
- If parts are merged, warn user about lost color separability.
- Preserve keyed assembly features for multi-part color prints.

## Mandatory canvas preview after every edit

Every STL that is modified, transformed, merged, split, or re-saved must be shown in the STL canvas immediately after the changed file is written. This step is not optional and must not be skipped, even if the user did not ask for a preview.

- Ensure the edited file lives under the workspace `models/` folder (the canvas only resolves workspace-relative paths).
- Then call `open_canvas` with `canvasId: "stl-canvas"` and `input.stlPath` set to the workspace-relative path, e.g. `models/bracket.stl`.
- If reopening the canvas for the same file, a stable `instanceId` such as
  `stl-preview` can refresh the panel. Before relying on a preview after changing
  the STL path, verify which file the canvas file selector actually shows: an
  existing canvas can retain its original dropdown selection even when reopened
  with a different `stlPath`. Use a new, file-specific `instanceId` to force an
  unambiguous preview of the derived file.
- If the edit produced several output files, preview each one, using a distinct `instanceId` per file.
- Optionally call the `read_stats` action and report the post-edit facets and bounds together with the preview.
- If the canvas fails to open (extension unavailable or `stl_not_found`), report the failure and the file path explicitly instead of silently continuing.

## Source

- Prusa modeling for printability guidelines  
  https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135
