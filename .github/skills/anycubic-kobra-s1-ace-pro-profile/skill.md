---
name: anycubic-kobra-s1-ace-pro-profile
description: Anycubic Kobra S1 Combo + ACE Pro defaults and constraints for STL authoring and editing.
---

# Anycubic Kobra S1 Combo + ACE Pro profile

Use this skill whenever creating or editing STL files intended for the Anycubic Kobra S1 Combo with ACE Pro multi-color workflow.

## Official defaults gathered from Anycubic docs

- Stock nozzle/hotend: **0.4 mm** (supported alternatives: 0.25 / 0.6 / 0.8 mm).
- Hotend temperature capability: up to **320 C**.

## Authoring defaults for STL geometry

When generating new STL geometry, apply these defaults unless user overrides:

- Units assumption: **millimeters**.
- Minimum printable wall (0.4 nozzle): **0.8 mm** (2 lines) recommended baseline.
- Durable wall baseline: **1.2 mm** (3 lines) for functional parts.
- Clearance defaults:
  - Tight fit: **0.20 mm**
  - General fit: **0.30 mm**
  - Easy/sliding fit: **0.40 mm**
- Minimum embossed/debossed text stroke: **0.5 mm**; depth/height >= **0.4 mm**.
- Overhang guidance for STL shaping: prefer <= **45 degrees** unsupported.
- Bridging guidance: keep unsupported bridge spans <= **10 mm**; add ribs or chamfers for spans between **10-25 mm**; require supports beyond **25 mm**.

## Non-default nozzle handling

- If the user specifies a non-0.4 mm nozzle, scale wall baselines to **2x** and **3x** the selected nozzle diameter, and flag that clearance and text stroke values may need manual review.

## ACE Pro (4-color) modeling guidance

- Prefer **separate solids per color region** where model intent allows.
- Add color boundaries at geometric transitions (fillets/chamfers/steps) to hide seams.
- Avoid tiny isolated color islands that cause excessive tool changes and purge waste.
- For multi-part assemblies, design keyed alignment features to simplify post-assembly.

## Required validation before finalizing STL

- If any validation check fails, halt finalization, report the specific failing check(s) with the affected geometry location if determinable, and ask the user how to proceed before outputting the STL.

- Mesh is watertight/manifold.
- No self-intersections or zero-area triangles.
- Normals are consistently outward.
- Bounding box matches intended physical dimensions in mm.
- Features smaller than 0.8 mm wall baseline are flagged.

## Research notes used for defaults

- 0.4 mm nozzle workflows should align model wall planning to perimeter width multiples.
- Movable fit baseline generally starts around 0.3 mm and is tuned by geometry/material.
- Overhang/support and orientation rules dominate surface quality and strength outcomes.

## Sources

- Anycubic product page:  
  https://store.anycubic.com/products/kobra-s1-combo
- Prusa modeling best practices:  
  https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135
