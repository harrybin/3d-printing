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

## Required behavior

- Preserve manifold/watertight topology.
- Recompute/report bounding box after each transform.
- Maintain intended units (mm).
- Flag if edits create non-printable thin features.
- If a requested transform would create features below the minimum wall thickness, warn the user with the specific offending dimension, propose the maximum safe transform value that preserves printability, and do not apply the transform until the user confirms.
- If the edit is driven by reference photos, build or refresh the numbered contact sheet first (`python scripts/make_contact_sheet.py <image folder>`), read it once, and open only the tiles that show the feature being changed. See `stl-from-image-measurements` step 0.

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
- Use a stable `instanceId` such as `stl-preview`, so each edit refreshes the same panel instead of opening new ones.
- If the edit produced several output files, preview each one, using a distinct `instanceId` per file.
- Optionally call the `read_stats` action and report the post-edit facets and bounds together with the preview.
- If the canvas fails to open (extension unavailable or `stl_not_found`), report the failure and the file path explicitly instead of silently continuing.

## Source

- Prusa modeling for printability guidelines  
  https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135
