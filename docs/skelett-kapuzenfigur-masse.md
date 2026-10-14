# Skelett-Kapuzenfigur (Chibi-Skelett im Hoodie) — Maße, Quellen & Lizenzentscheidung

Rekonstruktion der im Referenzvideo (`PXL_20261014_103834751.mp4`, Kontaktbogen `model-sources/archiv/skelett_kapuzenfigur-referenzfotos-index.png`, Kacheln `#01`–`#24`) gezeigten Chibi-Skelett-Figur im übergroßen Kapuzenpullover/Parka mit Händen in den Fronttaschen, Baggy-Hose und klobigen Sneakern.

---

## 1. Asset-Recherche & Lizenzentscheidung (`research-reusable-3d-assets`)

Vor der Modellierung wurde eine systematische Suche über Printables (inkl. GraphQL-API), MakerWorld, Thingiverse, Cults3D, Sketchfab und GitHub durchgeführt:

| Titel | Plattform / ID | Autor | Lizenz | Eignung / Entscheidung |
| --- | --- | --- | --- | --- |
| **Spooky Hooded Skeleton** | [Printables #1199238](https://www.printables.com/model/1199238-spooky-hooded-skeleton) | `Stigern` | **CC BY-NC 4.0** (Non-Commercial, Remix erlaubt) | **Visuelles Referenzmodell** (identische Stirnnaht, Kapuzenfalte, Taschenpose); wegen `NC`-Einschränkung **nicht als Mesh importiert**, sondern als reine Bild-/Formreferenz genutzt |
| **Funky Skeleton Figure in Hoodie** | [Printables #1182714](https://www.printables.com/model/1182714-funky-skeleton-figure-in-hoodie) | `Stigern` | **CC BY-NC 4.0** | Verwandte Variante desselben Autors; wegen `NC`-Lizenz nur Referenz |
| **Skelly Hoodie** | [Printables #1247094](https://www.printables.com/model/1247094-skelly-hoodie) | `Stigern` | **CC BY-NC 4.0** | Verwandte Variante (Baseball-Cap unter Kapuze); wegen `NC`-Lizenz nur Referenz |
| **Skeleton Kid in Hoodie** | [Printables #1230160](https://www.printables.com/model/1230160-skeleton-kid-in-hoodie) | `Stigern` | **CC BY-NC 4.0** | Variante mit Rucksack; wegen `NC`-Lizenz nur Referenz |
| **Cute Skeleton with a Hoodie Figurine/Keychain** | [Printables #1447558](https://www.printables.com/model/1447558-cute-skeleton-with-a-hoodie-figurinekeychain) | `FC2M3D` | **CC BY-NC-ND 4.0** (`disallowRemixing: true`) | Keine Derivate erlaubt (`ND`) — ausgeschlossen |
| **Skeleton in Hoodie - V2.0** | [Printables #1557278](https://www.printables.com/model/1557278-skeleton-in-hoodie-v20) | `MayPrinting` | **CC BY-NC 4.0** | Repost/Fix von #1182714; wegen `NC`-Lizenz nur Referenz |
| **Chibi Skeleton** | [Thingiverse #5990698](https://www.thingiverse.com/thing:5990698) | `CupioPaxMiniatures` | **CC BY 4.0** | Reines Skelett ohne Hoodie/Kleidung; stilistisch abweichend |

### Entscheidung: **Original-Neukonstruktion (Blender 5.2 + Python SDF/Manifold-Pipeline)**
Da das identifizierte Vorbild ([Printables #1199238](https://www.printables.com/model/1199238-spooky-hooded-skeleton) von `Stigern`) unter **CC BY-NC 4.0** steht und keine frei im Repo weiterverbreitbare CC0/CC-BY-Vorlage existiert, wird **kein fremdes Mesh importiert oder abgeleitet**. Die gesamte Geometrie wird vollständig neu und parametrisch über `scripts/skelett_kapuzenfigur.py` (mit Blender-5.2-Sculpting-/Remesh-Unterstützung und `trimesh`/`manifold3d`-Nachbereitung) aus den vermessenen Referenzansichten aufgebaut.

---

## 2. Maßreferenz: 2-Euro-Münze (`research-part-specs`)

Im Video liegt unmittelbar links neben den Füßen der Figur auf derselben Standebene (`z = 0`, Anycubic-Kartonoberfläche) eine **2-Euro-Münze**:

- **Offizielle Spezifikation (Europäische Zentralbank / Amtsblatt der EU C 373/2001):**
  - Außendurchmesser: **`25,75 mm`**
  - Randdicke / Höhe: **`2,20 mm`**
- **Kalibrierungsmethode:**
  1. In den Schräg- und Frontansichten (`#01`, `#03`, `#21`, `#24`) liegen Münze und Schuhsohlen exakt in derselben Ebene `z = 0`. Das Verhältnis zwischen Münzdurchmesser (`25,75 mm`) und der Außenbreite über beide Schuhe ist daher frei von vertikaler Perspektivverzerrung:
     - Kachel `#01`: Münze `310 px` (`25,75 mm`, `0,0831 mm/px`), Schuhbasis `225 px` $\rightarrow$ **`18,69 mm`**
     - Kachel `#03`: Münze `388 px` (`25,75 mm`, `0,0664 mm/px`), Schuhbasis `285 px` $\rightarrow$ **`18,91 mm`**
     - Kachel `#24`: Münze `370 px` (`25,75 mm`, `0,0696 mm/px`), Schuhbasis `265 px` $\rightarrow$ **`18,44 mm`**
     - **Mittelwert Schuhbasis-Außenbreite (`z = 0`):** **`18,68 mm`** (`± 0,24 mm`)
  2. In der nahezu horizontalen Rückansicht (`#11`) und linken Profilansicht (`#08`) beträgt die Schuhbasis-Außenbreite `245 px` (`0,07624 mm/px` in `#11`) bzw. die Gesamthöhe `770 px` (`#11`) und `800 px` (`#08`, `0,07339 mm/px`).

---

## 3. Abgeleitete Bauteilmaße & Proportionszonen

Alle Maße in Millimetern (`mm`), zentriert auf `(X = 0, Y = 0)`, Standfläche bei `Z = 0,0 mm` (`-Y` = Vorderseite / Blickrichtung, `+Y` = Rückseite):

| Merkmal / Zone | Maß (`mm`) | Herkunft / Kachel-Referenz | Status |
| --- | --- | --- | --- |
| **Gesamthöhe (`Z`)** | **`58,7 mm`** | `#08` (`800 px`), `#11` (`770 px`), `#24` (perspektivkorrigiert aus Münzellipse) | Kalibriert aus 2-€-Münze |
| **Kapuze Außenbreite (`X`)** | **`28,6 mm`** | `#01` (`320 px`), `#11` (`375 px`), `#24` (`385 px`) | Kalibriert |
| **Kapuze Außentiefe (`Y`)** | **`27,2 mm`** | `#08` (`370 px` von Vorderkante Kapuzenumschlag bis Hinterkopf) | Kalibriert |
| **Kapuze Z-Bereich** | **`27,1 .. 58,7 mm`** | `#08`, `#11`, `#24` (Kinnunterkante bei `Z = 27,1 mm`, Scheitel bei `Z = 58,7 mm`) | Kalibriert |
| **Kapuzen-Umschlagwulst (Rand)** | **`5,8 mm` breit** | `#01`, `#08` (`80 px` tiefer gerollter Saum mit leichter Spitze oben mittig) | Kalibriert |
| **Untere Sekundärkapuze / Kragenfalte hinten** | **`Z = 27,8 .. 35,5 mm`** | `#08`, `#11` (`y = 750..850 px`, ca. `21,5 mm` breit am oberen Rücken) | Kalibriert |
| **Schädelgesicht (in Kapuzenöffnung)** | **`20,5 × 20,0 mm`** | `#01`, `#24`: runde Chibi-Stirn mit vertikaler Stirnnaht (`4,2 mm` lang), schrägen ovalen Augenhöhlen (`6,2 × 4,8 mm`), dreieckiger Nasenhöhle (`3,2 × 3,6 mm`) und breitem vernähtem Zahn-Grinsen (`11,5 mm` breit) | Kalibriert |
| **Torso / Jacke Z-Bereich** | **`15,6 .. 28,5 mm`** | `#01`, `#08`, `#11`, `#24` (inkl. `2,6 mm` hohem Rippenbündchen am unteren Saum) | Kalibriert |
| **Torsobreite über Ellbogen (`X`)** | **`22,9 mm`** | `#01`, `#11` (`300 px`), `#24` | Kalibriert |
| **Jackensaum-Breite (`X`)** | **`19,1 mm`** | `#11` (`250 px`), `#24` | Kalibriert |
| **Torso-Tiefe inkl. Taschen/Arme (`Y`)** | **`19,1 mm`** | `#08` (`260 px` von Bauchtasche vorn bis Jackenrücken) | Kalibriert |
| **Ärmel & Taschenpose** | **3 Ellbogenfalten** | `#01`, `#08`, `#21`, `#24`: beide Arme angewinkelt, Hände mit Bündchen schräg in den Fronttaschen (`Z = 16,5 .. 23,5 mm`), offene Jackenfront mit Mittelspalt (`1,6 mm` breit) | Kalibriert |
| **Hose Z-Bereich** | **`5,2 .. 16,0 mm`** | `#08`, `#11`, `#24`: zwei getrennte Beine (`Spalt = 2,3 mm` mittig) mit je 3 horizontalen Stauchfalten | Kalibriert |
| **Schuhe / Sneaker (`Z = 0,0 .. 5,7 mm`)** | **`18,7 × 16,9 × 5,7 mm`** | `#01`, `#08`, `#11`, `#21`, `#24`: je Schuh `8,2 mm` breit, `16,9 mm` lang, leicht um `7°` nach außen gedreht, umlaufender Sohlenrand (`1,8 mm` hoch) mit Zehenkappe und Schnürung | Kalibriert auf `z = 0` |

---

## 4. Mesh-Validierung & OrcaSlicer-Druckvalidierung (`validate-stl-mesh`, `orcaslicer-print-validation`)

- **Generierte Artefakte:**
  - Parametrischer Generator: `scripts/skelett_kapuzenfigur.py`
  - Blender-5.2-Quelldatei: `models/skelett_kapuzenfigur.blend` (Blender `5.2.2 LTS`)
  - Druckfertiges ASCII-STL: `models/skelett_kapuzenfigur.stl`
  - Vorschaubild (6 Ansichten): `docs/images/skelett_kapuzenfigur-preview.png`
- **Mesh-Prüfung (`scripts/mesh_tool.py validate` & `overhang`):**
  - Facetten: `90.966` (`45.485` eindeutige Vertices)
  - Bounding Box: `(-14,398, -13,223, 0,000)` bis `(14,398, 13,223, 58,700) mm` (`28,80 × 26,45 × 58,70 mm`), `center-origin` auf `(0, 0)` zentriert
  - Volumen: `19.829,6 mm³` (`19,83 cm³`), Standfläche `Z = 0`: `232,03 mm²`
  - Status: **`PASS`** (`watertight = True`, `winding_consistent = True`, `euler_number = 2`, `0` degenerierte Dreiecke)
  - Überhänge (`> 45°`): `311,05 mm²` (`5,6 %` der Gesamtoberfläche `5.583,85 mm²`), maximale Brückenspannweite `0,50 mm` (`<= 10 mm` freies Limit)
- **OrcaSlicer-Validierung (`verified`):**
  - Slicer: **OrcaSlicer 2.4.2** (`C:\Program Files\OrcaSlicer\orca-slicer.exe`)
  - Profile: `Anycubic Kobra S1 0.4 nozzle` | `0.20mm Standard @Anycubic Kobra S1 0.4 nozzle` | `Anycubic PLA @Anycubic Kobra S1 0.4 nozzle` | Druckbett `Textured PEI Plate`
  - Prozess-Parameter: Schichthöhe `0,20 mm` (`293` Schichten), `wall_loops = 3`, `sparse_infill_density = 15 %` (`gyroid`), `seam_position = random`, `ironing_type = top`, `enable_support = 1` (`tree(auto)`, `support_on_build_plate_only = 1`, `support_critical_regions_only = 1`, `support_threshold_angle = 30°`)
  - Geschätzte Druckzeit: **`44m 17s`**
  - Filamentverbrauch gesamt: **`10,35 g`** (`3.470,08 mm`, `8,35 cm³`)
  - Davon Stützmaterial (`;TYPE:Support` + `;TYPE:Support interface`): **`0,16 g`** (`55,28 mm`, `0,13 cm³`, `1,6 %` — `44` kurze Stützpfade)
  - Slicer-Warnungen: Keine Kollisionen, keine leeren Schichten, keine Reparaturhinweise; Status **`verified`**.

