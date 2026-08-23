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
angewinkeltem Ellbogen herab; die Unterarme fallen nahezu senkrecht, sodass die
Hände seitlich auf dem Tisch abstützen.

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
Kugel-Sweep erzeugt. Die Knotenkette wird zuvor mit einer Catmull-Rom-Spline
(Position **und** Radius) nachabgetastet, damit die Gelenke als weiche Biegung
statt als Knick erscheinen. Der jeweils erste Knoten ist eine **Übergangskehle**:
eine dickere Kugel tief im Körper, deren Durchbruch durch die Wand einen
fließenden Kragen bildet.

| Knoten | x | y | z | Radius | Bedeutung |
| --- | ---: | ---: | ---: | ---: | --- |
| 0 | 20.6 | 0.0 | 15.2 | 5.0 | Übergangskehle (tief in der Becherwand) |
| 1 | 23.6 | −0.2 | 14.8 | 4.4 | Kragen – Durchbruch durch die Wand |
| 2 | 26.6 | −1.0 | 13.2 | 3.8 | Schulter |
| 3 | 30.4 | −3.0 | 9.8 | 3.4 | **Ellbogen** |
| 4 | 30.2 | −5.5 | 6.0 | 3.0 | Unterarm (fällt nahezu senkrecht) |
| 5 | 29.6 | −7.0 | 3.6 | 2.8 | Handgelenk |
| 6 | 29.2 | −8.5 | 2.45 | 3.3 | Handballen (`sx` 1.10, `sz` 0.85) – flach aufliegend |

## Bodenkontakt (Fersen und Handballen)

Fersen und Handballen sollen **aufsitzen**, nicht in einem Punkt tangieren.
Dafür werden sie bewusst ein Stück **unter** die Tischebene modelliert und der
Gliedmaßenkörper anschließend mit `build_ground_cutter()` bei `z = 0`
abgeschnitten. Aus der Kugelkalotte wird so eine echte ebene Fläche.

| Größe | Wert |
| --- | ---: |
| Eintauchtiefe Handballen | 0.35 mm |
| Eintauchtiefe Ferse | 0.48 mm |
| `GROUND_SINK` (Warnschwelle) | 0.60 mm |
| Aufstandsfläche gesamt (4 Stück) | 37.3 mm² |

Der Schnitt wird **nur auf die Gliedmaßen** angewendet, vor der Vereinigung mit
dem Korpus. Der Korpus hat bei `z = 0` bereits eine eigene ebene Standfläche;
ein Schnitt durch die fertige Figur würde dort koplanare Flächen erzeugen. Die
Aufstandsflächen liegen bei `r ≥ 30 mm` und überlappen die Ø34-Standfläche des
Korpus nicht, deshalb ist der Schnitt gefahrlos.

`limb_check()` meldet die Eintauchtiefe je Gliedmaße und warnt, wenn eine
Gliedmaße den Tisch **gar nicht** erreicht oder tiefer als `GROUND_SINK`
eintaucht (dann wird die Fläche unschön groß).


Kragen tritt 4.46 mm aus der Becherwand aus. Die Schulter liegt bewusst tief
(z ≤ 15.2), damit die Verrundung (siehe unten) den Becherrand nicht anhebt.

Alle Werte sind Designentscheidungen (Konfidenz: n/a, keine Passmaße). Die
linke Seite entsteht durch Spiegeln von `x`.

## Beine (humanoid, parametrisch)

| Knoten | x | y | z | Radius | sx | sy | sz | Bedeutung |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 7.2 | −10.2 | 6.2 | 6.00 | 1.00 | 1.00 | 1.00 | Übergangskehle (tief in der runden Unterseite) |
| 1 | 8.4 | −12.4 | 6.0 | 5.80 | 1.00 | 1.00 | 1.00 | innerer Kragen |
| 2 | 9.6 | −15.0 | 5.9 | 5.45 | 1.00 | 1.00 | 1.00 | äußerer Kragen – Durchbruch durch die Wand |
| 3 | 10.6 | −18.4 | 5.9 | 5.00 | 1.00 | 1.00 | 1.00 | Hüfte |
| 4 | 11.0 | −24.0 | 6.6 | 4.80 | 1.00 | 1.00 | 1.00 | Oberschenkel |
| 5 | 11.4 | −30.5 | 7.4 | 4.60 | 1.00 | 1.00 | 1.00 | **Knie** (angewinkelt) |
| 6 | 11.5 | −37.0 | 5.3 | 4.10 | 1.00 | 1.00 | 1.00 | Schienbein |
| 7 | 11.5 | −41.4 | 4.3 | 3.00 | 1.00 | 0.95 | 1.00 | **Knöchel** – schlanke Taille |
| 8 | 11.5 | −44.4 | 3.05 | 3.40 | 1.05 | 1.00 | 1.00 | **Ferse** – taucht unter den Tisch, wird abgeschnitten |
| 9 | 11.5 | −45.6 | 8.6 | 3.40 | 1.15 | 0.80 | 0.95 | Fußballen – breit, aber flacher |
| 10 | 11.5 | −45.9 | 11.4 | 2.60 | 1.18 | 0.60 | 0.75 | Zehen – schmal auslaufender Keil |

### Fußform

Referenz: Nutzerfoto eines Fußes im Profil (liegendes Bein, Ferse am Boden).
Daraus abgeleitet und als Designentscheidung umgesetzt:

- Der Fuß ist **kein senkrechter Zylinder** mehr, sondern eine L-Form:
  Schienbein → schlanker Knöchel → Ferse am Boden → Fuß steigt nach vorn-oben
  → Zehen.
- Der Querschnitt ist ab dem Knöchel **nicht mehr rund**. Die drei
  Skalierungsfaktoren `sx, sy, sz` je Knoten verformen die Sweep-Kugel zum
  Ellipsoid: quer breiter (`sx` bis 1.18), in Gehrichtung dünner (`sy` bis
  0.60). Das ergibt die Verjüngung eines echten Fußes.
- Nicht verwechseln mit „oben flach drücken": ein gleichmäßig gestauchter
  Zehenballen sieht aus, als wäre etwas daraufgefallen. Der Radius muss zur
  Spitze hin **abnehmen** (3.40 → 2.60), nur dann liest es sich als Zehen.

Kragen tritt 4.88 mm aus der Korpuswand aus. Die Radienstaffelung
5.00 → 5.45 → 5.80 → 6.00 wächst zum Körper hin **beschleunigt**; genau das
erzeugt den konkaven, fließenden Übergang statt einer aufgesetzten Kugel.

Spline-Parameter: `SPLINE_SAMPLES = 8` Stützstellen je Knotenintervall,
`SPHERE_SUBDIV = 3`. Radien **und** Skalierungsfaktoren werden auf den
Eingangsbereich geklemmt, sonst überschwingt die Spline an der scharfen
Knöchelbiegung.

Alle Werte sind Designentscheidungen. `limb_check()` im Generator meldet, wie
tief die Spline unter die Tischebene taucht (muss 0 sein, sonst schwebt der
Becher), wie weit sie in die Mulde ragt und wie weit der Kragen aus der Wand
tritt.

## Freihalten der Eiermulde

Die Gliedmaßen dürfen nicht in den Ei-Hohlraum hineinragen. Dafür wird ein
Rotationskörper der Mulde (`build_cavity()`) erzeugt und **von den Gliedmaßen**
abgezogen, bevor sie mit dem Korpus vereinigt werden.

| Parameter | Wert | Zweck |
| --- | ---: | --- |
| `CAVITY_MARGIN` | 0.20 mm | Übermaß des Cutters – verhindert koplanare Flächen |
| `CAVITY_CLEAR_H` | 5.00 mm | Reichweite des Cutters über den Rand hinaus |

Der Cutter wird bewusst **nur** auf die Gliedmaßen angewendet. Ein Abzug vom
fertigen Körper erzeugt koplanare Flächen mit der bereits vorhandenen
Muldenoberfläche und liefert ein nicht wasserdichtes Mesh (`euler_number` 37,
70 degenerierte Facetten – verifiziert).

Volumenprobe (`intersection(Gliedmaßen, Mulde)`):
ungeschnitten 333.6 mm³ → nach dem Schnitt **0.0 mm³**.

## Verrundung der Anbindungen (SDF-Fillet)

Eine boolesche Vereinigung hinterlässt an der Schnittkurve **immer** eine harte
Kante. Kein Kragen und keine Radienstaffelung kann das beheben – dafür braucht
es einen echten konkaven Fillet, und der lässt sich nur implizit erzeugen.

`scripts/sdf_blend.py` baut deshalb ein Distanzfeld:

1. Korpus und Mulde sind Rotationskörper, ihre SDF hängt nur von `(r, z)` ab.
   `RevolveSDF` legt dafür eine 2D-Tabelle mit 0.15 mm Raster an und
   interpoliert bilinear (Fehler ≈ 0.005 mm).
2. Die ≈240 Kapseln einer Gliedmaße werden mit einem **harten** `np.minimum`
   verknüpft. Das ist entscheidend: ein `smin` zwischen zwei Kapseln derselben
   Gliedmaße bläht sie über ihre ganze Länge um bis zu `BLEND_RADIUS/4` auf.
3. `smin` wird genau **einmal** angewendet – zwischen Korpusfeld und fertigem
   Gliedmaßenfeld. Nur dort entsteht die Kehle.
4. Das Feld wird um `BLEND_EROSION` erodiert. Abseits der Anbindungen liegt der
   Blend-Körper dadurch knapp **innerhalb** des exakten Meshes und trägt nichts
   bei; an den Anbindungen wölbt sich die Kehle weiter heraus und liefert die
   Verrundung.
5. Die Mulde wird **um denselben Betrag geweitet** wieder abgezogen, damit der
   Blend die Eiermulde nie verkleinern kann.
6. Das Feld wird bei `z = 0` gekappt – die Kehle wölbt sich sonst bis 0.83 mm
   unter die Tischebene und hebt beim Absenken auf z = 0 die ganze Figur an.

Ergebnis: `figure = union(exaktes Mesh, Blend-Körper)`. Becherwand,
Randverrundung und Eiermulde bleiben exakt erhalten, die Anbindungen bekommen
echte Kehlen.

| Parameter | Wert | Zweck |
| --- | ---: | --- |
| `BLEND_RADIUS` | 4.00 mm | Reichweite der Kehle |
| `BLEND_EROSION` | 0.08 mm | hält den Blend abseits der Kehlen im Mesh |
| `BLEND_PITCH` | 0.30 mm | Marching-Cubes-Raster |

Ein Gitterpunkt, der exakt auf der Iso-Fläche liegt, erzeugt einen
nicht-manifolden Pinch-Punkt, den manifold3d mit *„Not all meshes are
volumes!"* ablehnt. `blend_solid()` wiederholt den Marching-Cubes-Schritt
deshalb mit leicht verschobenem Level, bis die Fläche ein sauberes Volumen ist.
Die Offsets sind bewusst **nur nicht-negativ**: ein positives Level erodiert
zusätzlich (immer unbedenklich), ein negatives würde den Blend aufweiten und
in die Eiermulde fressen – verifiziert mit 5.6 mm³ Materialeintrag.

Volumenprobe gegen die Mulde: 2.2 mm³ beim exakten Prüfkörper, **0.0 mm³**
bei 0.05 mm geschrumpftem Prüfkörper – reine Oberflächentoleranz des
Marching-Cubes-Netzes, kein echtes Eindringen.

Zusatzvolumen durch die Kehlen: 18 438 → 18 758 mm³ (+320 mm³).
Die Kehle an der Schulter hebt den Becherrand lokal um 0.16 mm an
(Gesamthöhe 22.07 → 22.23 mm).

Abhängigkeit: `scikit-image` (Marching Cubes) in `requirements.txt`.

## Validierung

`python scripts/mesh_tool.py validate models/egg-cup-man-body.stl`

Aktueller Stand: watertight, manifold, `euler_number` 2, 1 Komponente,
104 544 Facetten, Bauraum 67.9 × 71.6 × 22.2 mm (passt auf 250 × 250 mm).

Das Netz enthält 4 Splitter-Dreiecke mit ~3·10⁻¹³ mm² Fläche aus dem
Marching-Cubes-Schritt. Sie sind **topologisch notwendig**: entfernt man sie
nach Fläche, fällt das Netz auf `euler_number` −33 und ist nicht mehr
wasserdicht (verifiziert). `mesh_tool validate` meldet PASS, Slicer stören sie
nicht – also stehen lassen.

## TODO nach Testdruck

- [ ] Ei-Aufnahme gegen echtes Hühnerei testen (Ø ~42 mm)
- [ ] Standfestigkeit der Ø34-Standfläche prüfen; ggf. `FOOT_R` erhöhen
- [ ] Überhang an der Unterseite im Druck kontrollieren (46.5°)
- [ ] Kniebogen: Unterseite schwebt ca. 2.7 mm über dem Tisch – im Druck auf
      Stützbedarf prüfen
