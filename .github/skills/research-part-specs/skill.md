---
name: research-part-specs
description: Find real published dimensions for a part before modeling it, cite the source, and record the numbers in a measurement doc instead of guessing from a photo.
---

# Research part specs

Use this skill before creating geometry that has to mate with a **real, identifiable
product** - a lens cap, a hinge, a post plug, a rail profile, a standard fastener.
Photo scaling is good for shape; it is not good for the two or three numbers a fit
actually depends on.

Rule: **never invent a dimension.** Every fit-critical number is either measured by
the user, taken from a cited published spec, or explicitly flagged as an estimate
that needs a test print.

## When to use which source

| Source | Trust | Use for |
| --- | --- | --- |
| User caliper measurement | highest | anything fit-critical |
| Manufacturer datasheet / product page | high | outer sizes, thread sizes, standard parts |
| Standard (DIN/ISO/metric thread tables) | high | fasteners, o-rings, bearings, tubing |
| Retailer listing / community wiki | medium | cross-check only, never the sole source |
| Scaled from a photo | low | shape, proportions, feature positions |
| Model guess | forbidden | nothing |

## Workflow

### 1. Identify the part

Name it as precisely as the photos allow: manufacturer, product line, size code,
any printed marking. Read markings from the reference photos through the contact
sheet (`python scripts/make_contact_sheet.py <image folder>`) and cite the tile
number the marking is visible on.

If the part cannot be identified, stop and ask the user for the exact
designation before searching - a search for the wrong part is worse than no search.

### 2. Search for the published numbers

Use the agent web search for the datasheet, the official product page, or a
dimensional standard. Target the three or four numbers the design depends on,
typically: outer dimension, inner dimension, height/depth, thread or bore size.

Reject a result when it does not state units, mixes a different variant of the
product, or only gives a marketing "approximate" size.

### 3. Record in the measurement doc

Write the findings into the part's doc under `docs/` - the same doc the
`stl-from-image-measurements` workflow uses. That doc is authoritative and the
user may edit it, so re-read it before every geometry change.

Record per value:

| Field | Meaning |
| --- | --- |
| `value` | the number in mm |
| `origin` | `measured`, `datasheet`, `standard`, `photo-scaled`, `estimated` |
| `source` | URL or "user caliper, 2026-08-18" |
| `confidence` | high / medium / low |
| `used_in` | the parameter name in the generator script |

Example:

```markdown
| Feature | Value | Origin | Source | Confidence | Used in |
| --- | --- | --- | --- | --- | --- |
| Post outer diameter | 11.5 mm | measured | user caliper 2026-08-18 | high | `POST_OD` |
| Wall thickness | 2.0 mm | datasheet | https://example.com/spec.pdf | high | `WALL_T` |
| Rib spacing | 4.1 mm | photo-scaled | tile 07, scaled on the 11.5 mm OD | medium | `RIB_PITCH` |
```

### 4. Feed the numbers into the script, not into the mesh

Every researched value becomes a **named module-level constant** in the generator
script under `scripts/`, with the origin as a short comment. This is why
`scripts/lineal_clip_kappe.py` reads `RULER_WIDTH = 14.5  # from image scaling`.

Then regenerate and validate:

```powershell
python scripts\<generator>.py
python scripts\mesh_tool.py validate models\<part>.stl
```

### 5. Flag what still needs a test print

Any value with `origin` of `photo-scaled` or `estimated` that carries a fit is a
risk. Say so explicitly and propose the smallest possible test coupon - usually
just the mating feature, a few millimetres of surrounding material, printed in
under ten minutes - rather than the whole part.

## Photo scaling done right

When a number really can only come from a photo:

- Scale against a **landmark of known size** in the same photo and the same plane
  (a caliper reading, a coin, a printed ruler, a measured OD).
- Never scale across depth: a feature further from the camera is smaller in the
  image for reasons that have nothing to do with its size.
- Confirm the side and orientation of a feature by normalising **several** photos
  to one orientation. A single photo has already produced a mirrored feature in
  this repo.
- Project the candidate contour back onto the calibrated photo to check it, rather
  than trusting automatic silhouette extraction, which bleeds into shadows.

## Output format

Report:

- the identified part, with the evidence used to identify it
- the dimension table with origin, source and confidence per value
- the parameter names the values were written to
- everything still unverified, with the proposed test coupon
- an explicit statement when a fit-critical number could not be sourced, instead of
  filling it with a plausible-looking number

## Related

- `.github/skills/stl-from-image-measurements` - the photo-to-STL workflow this feeds
- `.github/skills/optimize-stl-for-print` - clearance and hole compensation on top
  of the nominal dimensions found here
