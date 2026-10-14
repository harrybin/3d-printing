# Ohnezahn (Nachtschatten / Toothless) – Montage-, Kollisions- und Slicer-Prüfbericht

## 1. Gesamtmodell & Bauteil-Stückliste (BOM)

- **Gesamtabmessungen (zusammengebaut):** `77.66 × 46.58 × 60.97 mm` (Referenz-Ziel aus 2-Euro-Münzkalibrierung: `~78,0 × 45,5 × 60,5 mm`)
- **Unterseite Schwanz:** Glatt modelliert; der eingeprägte Fabrik-/Copyright-Code (`41204AFS`) wurde wie gewünscht vollständig weggelassen.
- **Farbstrategie:** 5 passgenaue, formschlüssig steckbare Einzelteile auf 4 sortenreinen Druckplatten (`0,00 g` Farbwechsel-/Purge-Abfall).

| Bauteil | Datei (`models/`) | ACE Pro Slot & Farbe | Facetten | Watertight | Euler-Zahl | Komponenten | Volumen (`mm³`) | Abmessungen Drucklage (`mm`) |
| --- | --- | --- | ---: | :---: | ---: | ---: | ---: | --- |
| `drache-koerper` | `models/drache-koerper.stl` | Slot 1: Koerper - schwarzes PLA (`#1C1E21`) | 46288 | `True` | `2` | `1` | `21433.9` | `77.66 × 46.58 × 60.97` |
| `drache-auge-links` | `models/drache-auge-links.stl` | Slot 2: Augen - hellgruenes PLA (`#4CC936`) | 1488 | `True` | `0` | `1` | `50.2` | `6.50 × 4.70 × 2.95` |
| `drache-auge-rechts` | `models/drache-auge-rechts.stl` | Slot 2: Augen - hellgruenes PLA (`#4CC936`) | 1488 | `True` | `0` | `1` | `50.2` | `6.50 × 4.70 × 2.95` |
| `drache-schwanzflosse-links-rot` | `models/drache-schwanzflosse-links-rot.stl` | Slot 3: Schwanzflosse - rotes PLA (`#D62828`) | 226 | `True` | `2` | `1` | `397.9` | `13.60 × 15.90 × 2.90` |
| `drache-emblem-weiss` | `models/drache-emblem-weiss.stl` | Slot 4: Wikinger-Emblem - weisses PLA (`#F4F5F7`) | 290 | `True` | `2` | `1` | `25.3` | `6.90 × 5.30 × 1.37` |

## 2. Kollisions- und Einschubweg-Prüfung (25-Schritt Manifold-Sweep)

Alle gesteckten Verbindungen wurden über ihren gesamten linearen Einschubweg (25 äquidistante Schritte von außerhalb des Gehäuses bis zum Endanschlag) mit `manifold3d` auf Schnittvolumen geprüft:

| Steckteil | Zielbauteil | Einschubvektor (Welt-XYZ) | Passungsspiel (`mm`) | Statisches Schnittvolumen (`mm³`) | Max. Sweep-Schnittvolumen (`mm³`) | Status |
| --- | --- | --- | ---: | ---: | ---: | :---: |
| `drache-auge-links` | `drache-koerper` | `(-0.6804, -0.6004, -0.4203)` | `0.15` | `0.00000` | `0.00000` | **PASS** |
| `drache-auge-rechts` | `drache-koerper` | `(-0.6990, +0.5792, -0.4194)` | `0.15` | `0.00000` | `0.00000` | **PASS** |
| `drache-schwanzflosse-links-rot` | `drache-koerper` | `(-0.0000, -1.0000, -0.0000)` | `0.15` | `0.00000` | `0.00000` | **PASS** |
| `drache-emblem-weiss` | `drache-schwanzflosse-links-rot` | `(-0.9207, -0.0000, -0.3903)` | `0.12` | `0.00000` | `0.00000` | **PASS** |

### Montagereihenfolge
1. **Grüne Augen (`drache-auge-links`, `drache-auge-rechts`):** Von schräg vorn/außen in die beiden Augenhöhlen des schwarzen Kopfes eindrücken. Die im schwarzen Kopf integrierten vertikalen Schlitzpupillen-Stege greifen exakt durch die Schlitze der grünen Augeneinsätze.
2. **Weißes Wikinger-Schädel-Emblem (`drache-emblem-weiss`):** Von oben in die formschlüssige Vertiefung der linken roten Schwanzflossen-Prothese (`drache-schwanzflosse-links-rot`) drücken (`0,12 mm` Presspassung).
3. **Rote Schwanzflossen-Prothese (`drache-schwanzflosse-links-rot`):** Seitlich von links entlang der Y-Achse (`(0, -1, 0)`) mit der asymmetrischen Feder in die Nut an der Schwanzspitze des schwarzen Körpers einschieben (`0,15 mm` Spiel).

## 3. Verifizierte OrcaSlicer-Druckdaten (`models/drache-print.3mf`)

- **Druckerprofil:** `Anycubic Kobra S1 0.4 nozzle`
- **Druckbett:** `Textured PEI Plate`
- **Prozessprofil:** `0.20mm Standard @Anycubic Kobra S1 0.4 nozzle` (`seam_position=random`, `ironing_type=top`, `enable_support=1`, `support_type=tree(auto)`)
- **Gesamtdruckzeit (alle 4 Platten):** `1h 29m 33s` (`5373 s`)
- **Gesamtfilamentbedarf:** `18.04 g` (`6049.03 mm`, `14550 mm³`)
- **Davon Support-Filament:** `0.79 g` (`266.04 mm`, `640 mm³`)

| Platte | Bezeichnung | Druckzeit | Filament gesamt (`g` / `mm`) | Support-Anteil (`g` / `mm`) | Status |
| :---: | --- | ---: | ---: | ---: | :---: |
| 1 | Plate 1 - Koerper - schwarzes PLA | `1h 18m 04s` (`4684 s`) | `17.36 g` (`5820.09 mm`) | `0.79 g` (`266.04 mm`) | **VERIFIED** |
| 2 | Plate 2 - Augen - hellgruenes PLA | `3m 50s` (`230 s`) | `0.15 g` (`50.60 mm`) | `0.00 g` (`0.00 mm`) | **VERIFIED** |
| 3 | Plate 3 - Schwanzflosse - rotes PLA | `4m 57s` (`297 s`) | `0.48 g` (`161.46 mm`) | `0.00 g` (`0.00 mm`) | **VERIFIED** |
| 4 | Plate 4 - Wikinger-Emblem - weisses PLA | `2m 42s` (`162 s`) | `0.05 g` (`16.88 mm`) | `0.00 g` (`0.00 mm`) | **VERIFIED** |

### Orientierungs- und Support-Nachweis
- **Platte 1 (`drache-koerper`):** Steht auf den vier plan abgeflachten Pfotensohlen (`Z = 0,000 mm`). Dadurch entsteht lediglich minimaler Tree-Support vom Druckbett aus (`0,79 g` unter Kinn/Bauch/Flügelspitzen), während Kopf-Oberseite, Ohrenhörner, Rückenkamm-Noppen, Sattel und Schwanzflosse zu 100 % frei von Support-Kontaktpunkten bleiben.
- **Platten 2, 3 und 4 (`drache-auge-links`, `drache-auge-rechts`, `drache-schwanzflosse-links-rot`, `drache-emblem-weiss`):** Liegen jeweils mit ihrer 100 % planen Rückseite auf `Z = 0,000 mm` und benötigen trotz aktiviertem Auto-Support (`enable_support=1`) exakt **`0,00 g` Support**.
