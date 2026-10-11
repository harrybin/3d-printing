# Gothic-Truhe: Relief-Quellen, Lizenzen und Druckvalidierung

Stand: Sculpting-Durchgang "organischer, fotorealistischer" Reliefs.
Betrifft `scripts/gothic_chest.py`, `scripts/blender_chest_reliefs.py`,
`assets/gothic-chest-reliefs/*.npz`.

## 1. Asset-Recherche und Lizenzentscheidung

**Ergebnis: kein geeignetes, lizenzgeprüftes Asset gefunden — prozedural in
Blender skulptiert.**

Gesucht wurde nach plan verwendbaren Flachreliefs (gotisches Ornament,
Totenkopf, Drache, Schlange) mit klarer, derivat- und
weiterverbreitungsfreundlicher Lizenz:

| Quelle | Ergebnis | Grund der Ablehnung |
| --- | --- | --- |
| Sketchfab CC0-Sammlungen | Treffer, aber Rundplastiken | Vollplastische Scans, kein Basrelief; Umbau zu `z = f(x, y)` entspricht einer Neumodellierung |
| Smithsonian Open Access | nicht zugänglich | API/Download mit HTTP 403 geblockt |
| Scan the World / MyMiniFactory | Treffer | Lizenz überwiegend CC-BY-NC bzw. unklar, keine gesicherte Derivat-/Redistributionsfreigabe |
| Thingiverse (CC0-Filter) | Treffer | Lizenzangaben inkonsistent zum tatsächlichen Upload, nicht verifizierbar |
| Wikimedia Commons `Category:STL files` | wenige Treffer | keine gotischen Kreaturenreliefs in nutzbarer Qualität |
| awesome-cc0 / öffentliche CC0-Listen | keine Treffer | kein passendes Motiv |

Es wird folglich **kein fremdes Asset verwendet, keine Attributionspflicht**.
Sämtliche Geometrie ist Eigenerzeugnis dieses Repos und unterliegt der
Repo-Lizenz.

### Abgeleitetes Asset im Repo

`assets/gothic-chest-reliefs/{front,rear,side,lid}.npz` + `manifest.json` sind
zwischengespeicherte, auf 0..1 normalisierte Höhenfelder (Panel-Raster ca.
0.58–0.65 mm). Sie sind reproduzierbar über:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
    --background --python scripts\blender_chest_reliefs.py
```

Der Cache existiert nur, damit der Truhengenerator ohne Blender läuft.

## 2. Pipeline

1. **Blender 5.2 headless** (`scripts/blender_chest_reliefs.py`): Motive aus
   Metaball-Ketten (`ball`/`blob`/`chain`/`membrane`), Noise-Displacement,
   Smooth-Shading → organische, verschmolzene Massen statt gestapelter
   Primitive.
2. **Höhenfeld-Extraktion** per BVH-Raycast von oben; Hohlformen (Augenhöhlen,
   Nasenöffnung, Schläfengruben) werden 2D im Höhenfeld gesenkt.
   *Nicht* per Blender-Boolean: der EXACT-Solver kippt bei dutzenden
   überlappenden Ellipsoiden die Innen/Außen-Parität und zerstörte das Relief
   (24 269 → 3 957 Faces).
3. **Solid-Erzeugung** in `gothic_chest.py` (`_heightfield_solid`):
   Binomial-Glättung, Rand auf 0 geklemmt, geschlossenes Gitterprisma mit
   0.4 mm Rückenplatte.
4. **Platzierung**: 45°-Scherung `y += z` → jedes Basrelief `z = f(x, y)` hat
   danach konstruktionsbedingt keinen Überhang > 45°.

## 3. Motivinventar

| Ort | Motive | Erhaben / vertieft | Tiefe | Restmaterial |
| --- | --- | --- | --- | --- |
| Vorderwand | 2 Totenköpfe mit Schlangen, Ranken, 4 Voluten | erhaben, geschert | bis 2.43 mm über der Wand | Wand unberührt |
| Rückwand | zentraler Brustkorb, 2 konfrontierte Wyvern (Kopf, Hörner, Zähne, Klauen, Flughaut), Voluten, Ranken | erhaben, geschert | bis 2.37 mm | Wand unberührt |
| Seitenwände (2×) | Totenkopf mit Schlange, Voluten, Ranke | erhaben, geschert | bis 2.77 mm | Wand unberührt |
| Deckel | geflügelter Totenkopf-Kartusche mit Schlangen und Voluten | erhaben, geschert | bis 3.0 mm | Deckel unberührt |
| Pilaster (8 Außenflächen, je 3 Kanneluren) | gotische Kannelur | **vertieft** | 1.2 mm | 5.0 mm Stock → **3.8 mm**, über dem 1.8-mm-Minimum |

Die Kanneluren sind senkrechte Kapseln mit kugeligen Enden: keine waagerechte
Decke, keine scharfe Hinterschneidung — darum stützfrei.

Die 2.0-mm-Wandfelder selbst werden **nicht** graviert: mit der
sparsam getunten Schale bliebe dort unter 1.8 mm Restmaterial.

## 4. Validierung

```powershell
.\.venv\Scripts\python.exe scripts\gothic_chest.py
# chest  faces  74750 watertight True bodies 1 euler -8  extents [209.0, 130.5, 98.0]
# lid    faces  27116 watertight True bodies 1 euler -58 extents [206.0, 129.0, 25.6]

.\.venv\Scripts\python.exe scripts\mesh_tool.py validate model-sources\ghouls-grip\reference\_chest.stl
# PASS - watertight, manifold, euler_number -8, ready to slice
.\.venv\Scripts\python.exe scripts\mesh_tool.py validate model-sources\ghouls-grip\reference\_lid.stl
# PASS - watertight, manifold, euler_number -58, ready to slice

.\.venv\Scripts\python.exe -m unittest tests.test_gothic_chest_reliefs
# Ran 6 tests - OK
```

(Die `WARN not centered`-Meldung ist gewollt: die Truhe wird vom Exporter
platziert.)

## 5. Stütz-Gate (entscheidend)

`scripts/audit_chest_support.py` erzeugt ein **identisches**
OrcaSlicer-Projekt für Kontrolle und Dekoration — gleiche Prozess-, Maschinen-
und Supporteinstellungen (automatischer Tree-Support aktiv), einziger
Unterschied ist die Geometrie. Danach wird im G-Code die Pfadanzahl und die
Summe der positiven E-Deltas unter `;TYPE:Support` /
`;TYPE:Support interface` gezählt.

| Variante | Support-Pfade | Support-E | Filament |
| --- | --- | --- | --- |
| `build_chest(include_decoration=False)` (Kontrolle) | 71 | 82.376 | 188.61 g |
| skulptierte Truhe | **71** | **82.376** | 196.51 g |

**PASS — exakt stützneutral.** Der gesamte Support entsteht an Scharnier- und
Deckelauflagen, nicht am Relief. Zum Vergleich der früher gemessene
vollvertiefte Entwurf: 245 Pfade / 569.21 E.

Artefakte: `build/ornament-audit/audit-control.3mf`,
`audit-sculpted.3mf`, `audit-*-slice/plate_1.gcode`, `audit-*-slice.log`.

## 6. Bewertungs-Renders

- `build/ornament-audit/render-chest-front.png`
- `build/ornament-audit/render-chest-rear.png`
- `build/ornament-audit/render-chest-side.png`
- `build/ornament-audit/render-chest-hero.png`
- `build/ornament-audit/render-lid-top.png`
- `build/ornament-audit/render-lid-raking.png`
- Höhenfeld-/Hillshade-Previews: `height-*.png`, `shade-*.png`

## 7. Restrisiko

- Die Wyvern sind das schwächste Motiv: Kopf, Hörner und Flughaut lesen sich
  klar, die Klauen bleiben bei 0.6 mm Düsenbreite grenzwertig fein.
- Die Reliefspitzen liegen bei 2.4–3.0 mm; ein Nachschärfen der Tiefe würde das
  Stütz-Gate erneut erfordern.
- Der `.npz`-Cache muss nach jeder Blender-Änderung neu erzeugt werden, sonst
  divergieren Skript und Geometrie.
