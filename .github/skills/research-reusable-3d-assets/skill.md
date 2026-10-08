---
name: research-reusable-3d-assets
description: Search for reusable 3D model assets before building from scratch, verify licensing and attribution, and choose reuse, hybrid rebuild, or original construction.
---

# Research reusable 3D assets

Use this skill before creating any new nontrivial object from scratch, including
free designs. Search for exact models when the object is recognizable and for
similar functional, structural, or stylistic templates when it is original. It owns
model asset discovery and licensing. `research-part-specs` remains the owner of
fit-critical dimensions and published specifications.

## Non-negotiable gate

Always search for suitable exact or similar assets before original modeling. A
result may be useful as an engineering pattern or visual reference even when it is
not an exact match. Do not treat a search result as usable merely because it can be
downloaded.

For every credible candidate, record:

- title, creator, source URL, and download URL
- exact license and the page that states it
- whether modification and redistribution are allowed
- attribution or share-alike obligations
- file formats, dimensions, component structure, and apparent mesh quality
- match quality: exact, adaptable, reference-only, or irrelevant

Reject an asset as a modeling base when:

- no clear license is stated
- the license forbids derivatives
- repository publication or redistribution would violate the license
- the geometry is extracted from a commercial product or game without a usable
  license
- the model cannot be traced back to its original publisher

Treat noncommercial licenses as incompatible with committed repository deliverables
unless the intended use and redistribution are explicitly confirmed as compliant.
They may still be listed as reference-only candidates.

## Search order

1. Manufacturer or project owner repositories and official downloads.
2. Public source repositories with an explicit license.
3. Established 3D model libraries with per-model license metadata.
4. Technical drawings, scans, or dimensional references when no reusable model is
   licensed.

Prefer primary sources. Do not re-download a repost when the original publication is
available.

## Decision

Choose exactly one path:

- `reuse`: the licensed asset already satisfies shape, dimensions, and editability.
- `hybrid`: reuse the licensed noncritical shape while rebuilding fit-critical or
  printer-specific geometry parametrically.
- `reference-only`: use published dimensions or visual evidence, but not the mesh.
- `rebuild`: no suitable licensed asset exists.

Even a reusable asset must pass unit, scale, topology, feature, and printability
checks. Online assets are never assumed to be dimensionally accurate or printable.

## Documentation

Write the result to `docs/<model>-quellen-und-lizenzen.md` or the model's existing
measurement document. Include rejected candidates when they materially explain why
the model was rebuilt.

When an asset is used, preserve required attribution in the documentation and PR.
Keep the original license file when its terms require distribution with derivatives.

## Handoff

- Send published dimensions to `research-part-specs`.
- Send organic or sculptural geometry to `blender-assisted-modeling`.
- Send technical geometry to `create-ascii-stl`.
- Send every imported mesh to `validate-stl-mesh` before modification and after
  export.

## Output evidence

Report the search terms, candidate table, selected path, license decision, required
attribution, and any remaining provenance uncertainty. If provenance or permission
is unclear, do not use the asset.

## Sources

- Creative Commons license conditions:
  https://creativecommons.org/share-your-work/cclicenses/
- GNU license compatibility guidance:
  https://www.gnu.org/licenses/license-compatibility.html
