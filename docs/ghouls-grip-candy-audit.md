# Ghoul's Grip: candy-hand geometry audit

**Status: PASS**. Sampled poses: 61.

| Check | Result |
| --- | --- |
| Frozen box/drive sources and 35 non-hand payloads | PASS |
| Hand and dish meshes | One closed, consistently wound, nondegenerate body per part required |
| Motion intersections | Every changed-hand pair against the complete scene; limit 0.5 mm3 |
| Finger insertion, including already installed fingers | Maximum 0.025903 mm3; limit 0.05 mm3 |
| Dish insertion/removal over 60 mm | Maximum 0.004280 mm3; limit 0.05 mm3 |
| Smallest closed cavity margin | 2.143 mm |
| Maximum opening tilt | 30.000 degrees |
| Minimum static capacity, 2 mm gravity freeboard | 10.980 ml |

Finger installation order: index, middle, ring, little, thumb; dish last.
Finger sockets and the gravity-seated dish are removable, not positively locked.

This is a sampled geometric/static-gravity proof, not a physical load,
friction, shock or sweets-retention test. Do not overfill; use wrapped sweets
or a suitable food-contact liner. PLA food-contact suitability is not certified.

See the assembly and dimensions document for parameter provenance and
the separate complete mechanism/assembly audit for unchanged drive parts.
