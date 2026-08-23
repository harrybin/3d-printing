# Egg-Cup Man – Maßdokumentation

Quelle der Maße: `model-sources/egg-cup-man-original.stl` (vom Nutzer geliefertes
Original-Druckplattenfile mit Korpus, 2 Armen und 2 Beinen).
Alle Werte wurden numerisch aus dem Mesh ausgelesen, nicht geschätzt.

Generator: [`scripts/egg_cup_man_body.py`](../scripts/egg_cup_man_body.py)
Ausgabe: `models/egg-cup-man-body.stl` – **eine** wasserdichte, sitzende Figur
(Korpus + Arme + Beine als Boolean-Union).

## Pose

Das Eiermännchen **sitzt**: Der Becher steht mit seiner runden Unterseite auf dem
Tisch, beide Beine liegen flach nach vorne (−Y), die Füße stehen am vorderen Ende
senkrecht hoch. Die Arme hängen seitlich (±X) unterhalb des Randes herab.

## Korpus (Becher)

| Merkmal | Maß (mm) | Quelle | Konfidenz |
| --- | ---: | --- | --- |
| Max. Außendurchmesser | 46.48 (r = 23.24) | STL-Mesh, Radialschnitt | hoch |
| Gesamthöhe Becher | 22.07 | STL-Mesh, Z-Extent | hoch |
| Ei-Kavität: Radial-Halbachse `a` | 21.10 | Ellipsoid-Fit auf Innenkontur | hoch |
| Ei-Kavität: Vertikal-Halbachse `b` | 23.30 | Ellipsoid-Fit auf Innenkontur | hoch |
| Ei-Kavität: Ellipsoid-Mittelpunkt `z` | 21.60 | Ellipsoid-Fit auf Innenkontur | hoch |
| Ei-Kavität: flacher Boden | z = 2.60 | STL-Mesh | hoch |
| Bodenstärke unter der Kavität | 2.60 | abgeleitet | hoch |
| Randwulst-Radius | 1.07 | Halbkreis-Fit, Zentrum (r 22.17, z 21.00) | hoch |
| Wandstärke am Rand | 2.14 | abgeleitet (23.24 − 21.10) | hoch |
| Wandstärke min. im Bauch | ca. 3.7 | abgeleitet aus Außen-/Innenkontur | hoch |

Der Ellipsoid-Fit der Kavität weicht über die gesamte Höhe um < 0.25 mm vom
gemessenen Mesh ab.

## Geänderte Unterseite (kugelige Abrundung)

Das Original hatte eine gerade Zylinderwand mit einer R3-Fase am Boden. Neu
rundet die Außenwand unterhalb von z = 14 mm **nach innen** ein – tangential an
die gerade Wand, damit keine Kante und **kein Bauch nach außen** entsteht:

    r(z) = 23.24 * sqrt(1 - ((14.00 - z) / 20.53)^2)

| Merkmal | Maß (mm) | Quelle | Konfidenz |
| --- | ---: | --- | --- |
| Beginn der Abrundung `BELLY_TOP_Z` | 14.00 | Designentscheidung | – |
| Standfläche-Radius `FOOT_R` | 17.00 (Ø 34.0) | Designentscheidung, überhangbegrenzt | – |
| Ellipsen-Halbachse `b` (berechnet) | 20.53 | aus `BELLY_TOP_Z` und `FOOT_R` | hoch |
| Max. Wandüberhang | 46.5° zur Senkrechten | vom Generator berechnet | hoch |
| Max. Außendurchmesser | unverändert 46.48 | Constraint | hoch |

`FOOT_R` ist bewusst so gewählt, dass der steilste Überhang unter 50° bleibt und
die Figur ohne Stützen druckbar ist. Ein kleinerer Fuß sieht runder aus, treibt
den Überhang aber schnell über 60°.

## Arme

| Merkmal | Maß (mm) | Quelle | Konfidenz |
| --- | ---: | --- | --- |
| Länge (Z-Extent im Quellfile) | 19.99 | STL-Mesh | hoch |
| Breite (X) | 12.30 | STL-Mesh | hoch |
| Dicke (Y) | 6.07 | STL-Mesh | hoch |
| Schulterfläche (flach, Normale −X) | 15.8 mm² | Flächenanalyse | hoch |
| Ansatzhöhe über Tisch `ARM_Z` | 1.00 | Designentscheidung | – |
| Eindringtiefe in die Wand `ARM_BITE` | 1.50 | Designentscheidung (Union-Naht) | – |

Die Arme werden unverändert aus dem Original übernommen und nur gespiegelt
platziert.

## Beine

| Merkmal | Maß (mm) | Quelle | Konfidenz |
| --- | ---: | --- | --- |
| Beinlänge (liegend, Y-Extent) | 23.00 | STL-Mesh | hoch |
| Beinbreite (X) | 10.57 | STL-Mesh | hoch |
| Beindicke liegend (Z) | ca. 6.0 | STL-Mesh | hoch |
| Fußhöhe (senkrecht stehend) | 16.56 | STL-Mesh | hoch |
| X-Spread Beine (Mitte–Mitte) | 18.92 (±9.46) | Original-Plattenlayout | hoch |
| Kontakthöhe am Korpus `LEG_CONTACT_Z` | 3.00 | Designentscheidung | – |
| Eindringtiefe in den Korpus `LEG_BITE` | 2.50 | Designentscheidung (Union-Naht) | – |

Die Beine werden unverändert aus dem Original übernommen, in −Y gespiegelt
(Blickrichtung nach vorn) und so weit in die neue runde Unterseite geschoben,
dass die Boolean-Union eine geschlossene Naht ergibt.

## Validierung

`python scripts/mesh_tool.py validate models/egg-cup-man-body.stl`

Aktueller Stand: watertight, manifold, `euler_number` 2, 1 Komponente,
0 degenerierte Facetten, Bauraum 68.1 × 60.9 × 22.1 mm (passt auf 250 × 250 mm).

## TODO nach Testdruck

- [ ] Ei-Aufnahme gegen echtes Hühnerei testen (Ø ~42 mm)
- [ ] Standfestigkeit der Ø34-Standfläche prüfen; ggf. `FOOT_R` erhöhen
- [ ] Überhang an der Unterseite im Druck kontrollieren (46.5°)
