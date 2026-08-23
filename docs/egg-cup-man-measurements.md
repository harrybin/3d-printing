# Egg-Cup Man – Maßdokumentation

Quelle der Korpusmaße: `model-sources/egg-cup-man-original.stl` (vom Nutzer
geliefertes Original-Druckplattenfile mit Korpus, 2 Armen und 2 Beinen).
Alle Korpuswerte wurden numerisch aus dem Mesh ausgelesen, nicht geschätzt.
Arme und Beine sind inzwischen frei parametrisch neu modelliert (humanoid mit
Ellbogen und Knien) und stammen nicht mehr aus dem Original.

Generator: [`scripts/egg_cup_man_body.py`](../scripts/egg_cup_man_body.py)
Ausgabe: `models/egg-cup-man-body.stl` – **eine** wasserdichte, sitzende Figur
(Korpus + Arme + Beine als Boolean-Union).

## Pose

Das Eiermännchen **sitzt**: Der Becher steht mit seiner runden Unterseite auf dem
Tisch, beide Beine reichen mit angewinkeltem Knie nach vorne (−Y), die Füße
stehen am vorderen Ende senkrecht hoch. Die Arme hängen seitlich (±X) mit
angewinkeltem Ellbogen herab.

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

## Arme (humanoid, parametrisch)

Die Arme sind **keine** Kopien aus dem Original mehr, sondern werden als
Kugel-Sweep erzeugt: aufeinanderfolgende Knoten werden über die konvexe Hülle
zweier Kugeln verbunden, die gemeinsame Kugel bleibt als Gelenk sichtbar.

| Knoten | x | y | z | Radius | Bedeutung |
| --- | ---: | ---: | ---: | ---: | --- |
| 1 | 21.0 | 0.0 | 17.8 | 4.2 | Schulter (in der Becherwand) |
| 2 | 26.5 | −0.5 | 14.5 | 3.4 | Oberarm |
| 3 | 29.8 | −2.5 | 9.5 | 3.5 | **Ellbogen** |
| 4 | 29.0 | −8.0 | 5.5 | 2.9 | Unterarm |
| 5 | 27.2 | −13.0 | 3.4 | 2.7 | Handgelenk |
| 6 | 26.2 | −16.0 | 3.6 | 3.5 | Hand |

Alle Werte sind Designentscheidungen (Konfidenz: n/a, keine Passmaße). Die
linke Seite entsteht durch Spiegeln von `x`. Der Schulterknoten liegt innerhalb
der Becherwand, damit die Boolean-Union eine geschlossene Naht ergibt.

## Beine (humanoid, parametrisch)

| Knoten | x | y | z | Radius | Bedeutung |
| --- | ---: | ---: | ---: | ---: | --- |
| 1 | 9.5 | −14.0 | 5.5 | 5.2 | Hüfte (in der runden Unterseite) |
| 2 | 10.4 | −22.0 | 6.4 | 4.9 | Oberschenkel |
| 3 | 11.2 | −29.5 | 7.4 | 4.7 | **Knie** (angewinkelt) |
| 4 | 11.4 | −36.5 | 5.2 | 4.2 | Schienbein |
| 5 | 11.4 | −42.5 | 3.6 | 3.6 | Knöchel |
| 6 | 11.4 | −44.0 | 8.0 | 4.2 | Rist (Fuß steht senkrecht) |
| 7 | 11.4 | −44.3 | 12.5 | 4.4 | Fußspitze |

Alle Werte sind Designentscheidungen. `limb_check()` im Generator prüft, dass
kein Knoten unter die Tischebene sinkt und dass der Wurzelknoten innerhalb der
Korpuswand liegt.

## Validierung

`python scripts/mesh_tool.py validate models/egg-cup-man-body.stl`

Aktueller Stand: watertight, manifold, `euler_number` 2, 1 Komponente,
0 degenerierte Facetten, Bauraum 66.6 × 71.9 × 22.1 mm (passt auf 250 × 250 mm).

## TODO nach Testdruck

- [ ] Ei-Aufnahme gegen echtes Hühnerei testen (Ø ~42 mm)
- [ ] Standfestigkeit der Ø34-Standfläche prüfen; ggf. `FOOT_R` erhöhen
- [ ] Überhang an der Unterseite im Druck kontrollieren (46.5°)
- [ ] Kniebogen: Unterseite schwebt ca. 2.7 mm über dem Tisch – im Druck auf
      Stützbedarf prüfen
