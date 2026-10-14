# Butterfly-Messer (`butterfly-messer`): Asset-Recherche & Lizenzentscheidung

## 1. Suchergebnisse wiederverwendbarer 3D-Assets (`research-reusable-3d-assets`)

Vor der Konstruktion wurde nach bestehenden Open-Source-SCAD-/CAD-/STL-Modellen für druckbare Balisong-/Butterfly-Messer und Trainer gesucht:

| Quelle / Repository | Autor | Lizenz | Geometrische Eignung | Entscheidung |
| --- | --- | --- | --- | --- |
| [ferretallicA/balisong-v2](https://github.com/ferretallicA/balisong-v2) (`balisong.scad`) | ferretallicA | Keine Lizenzdatei im Repository (`All Rights Reserved` per GitHub-Standard) | OpenSCAD-Balisong mit einfachen zylindrischen Pins, ohne klassische Skelett-Lochung (5 große + 6×2 kleine Bohrungen), ohne integrierten Zen-Pin-Anschlag und ohne werkzeuglose D-Bolzen/U-Clip-Sicherung | **Nur Referenz (`reference-only`)** — keine Lizenz zur Weiterverbreitung/Bearbeitung |
| [j557/balisong](https://github.com/j557/balisong) (`main.scad`, `balisong.stl`) | j557 | Keine Lizenzdatei im Repository (`All Rights Reserved` per GitHub-Standard) | Print-in-Place-Prototyp ohne getrennte Mehrfarb-Baugruppen, ohne Spachtel-/Kratzer-Schneide und ohne rastbaren T-Latch | **Nur Referenz (`reference-only`)** — unklare Lizenz & abweichende Funktionsarchitektur |

## 2. Gewählte Strategie (`asset_strategy = rebuild`, `modeling_route = python`)

- **Strategie:** Vollständige parametrische Neukonstruktion (`rebuild`) in [`scripts/butterfly_messer.py`](../scripts/butterfly_messer.py) auf Basis:
  1. des vom Benutzer bereitgestellten Referenzfotos ([`model-sources/archiv/butterfly-messer-referenzfotos-index.png`](../model-sources/archiv/butterfly-messer-referenzfotos-index.png), Kachel `00`),
  2. publizierter Standard-Balisong-Abmessungen (Benchmade 42 / klassisches 5-Loch-Edelstahl-Balisong mit T-Latch) und
  3. der im Benutzer-Interview festgelegten FDM-Konstruktionsparameter für den **Anycubic Kobra S1 Combo + ACE Pro**.
- **Warum Python statt Blender (`modeling_route = python`):** Alle 14 Bauteile sind technisch-funktionale, toleranzkritische Geometrien (Drehgelenke mit `0.30 mm` Radialspiel, verdrehgesicherte D-Bolzen, rastende U-Clips mit `0.15 mm` Sitz, Zen-Pin-Anschlaggeometrie für `0°` und `180°`, sowie eine beidseitig im 45°-Winkel gefaste Spachtel-/Kratzer-Klinge).
