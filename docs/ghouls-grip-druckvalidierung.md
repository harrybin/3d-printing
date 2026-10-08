# The Ghoul's Grip – OrcaSlicer-Druckvalidierung

Status: **VERIFIED**  
Validiert: 2026-10-08  
OrcaSlicer: **2.4.2**

![Übersicht der geslicten G-Code-Pfade](images/ghouls-grip-slice-overview.png)

## Fester Profilvertrag

- Drucker: `Anycubic Kobra S1 0.4 nozzle`
- Düse: 0,4 mm
- Prozess: `0.20mm Standard @Anycubic Kobra S1 0.4 nozzle`
- Filament: `Anycubic PLA @Anycubic Kobra S1 0.4 nozzle`
- Druckbett: `Textured PEI Plate`
- Schichthöhe: 0,20 mm
- Starttemperaturen: Bett 55 °C, Düse 215 °C
- Stützen: nur vom Druckbett; Baumstützen für organische/äußere Formen,
  `normal(auto)`/`snug` für die fünf einzeln gedruckten Mechanikteile
- Prime Tower: aus, da jede Druckplatte nur eine PLA-Spule nutzt

Die offizielle OrcaSlicer-CLI wurde mit dem exakten gelieferten 3MF jeder
Platte aufgerufen. Jeder Slice erzeugte eine vollständige G-Code-Datei. Die
Logs enthalten keine verbleibende Floating-region-, Floating-cantilever-,
Toolpath-conflict-, Out-of-bed-, Empty-layer- oder Invalid-toolpath-Warnung.

## Platten und Ergebnisse

| Druckprojekt / Platte | Enthaltene Objekte | Schichten | PLA | Zeit | Stützen | Vorschau |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `ghouls-grip-print-black-pla.3mf`, Platte 1 | Deckel | 137 | 229,27 g | 12 h 24 min 01 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-black-pla-plate_1.png) |
| `ghouls-grip-print-black-pla.3mf`, Platte 2 | Schatulle | 490 | 386,16 g | 15 h 07 min 07 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-black-pla-plate_2.png) |
| `ghouls-grip-print-bone-pla.3mf` | Unterarm, Handfläche, Sehnenführung | 262 | 51,24 g | 3 h 26 min 50 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-bone-pla.png) |
| `ghouls-grip-print-mechanism-pla.3mf` | 4 Scherenarme, Schlitten, 8 kleine und 4 große Pins | 170 | 50,10 g | 2 h 30 min 41 s | nein | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-pla.png) |
| `ghouls-grip-print-mechanism-supported-platform-pla.3mf` | Hubjoch | 344 | 46,21 g | 1 h 58 min 44 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-platform-pla.png) |
| `ghouls-grip-print-mechanism-supported-latch-rocker-pla.3mf` | Klinkenrocker | 293 | 8,63 g | 34 min 30 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-latch-rocker-pla.png) |
| `ghouls-grip-print-mechanism-supported-latch-bracket-pla.3mf` | Klinkenhalter | 193 | 10,96 g | 29 min 01 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-latch-bracket-pla.png) |
| `ghouls-grip-print-mechanism-supported-crank-pla.3mf` | Kurbel | 375 | 11,54 g | 42 min 39 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-crank-pla.png) |
| `ghouls-grip-print-mechanism-supported-band-anchor-pla.3mf` | Bandanker | 143 | 12,25 g | 39 min 55 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-band-anchor-pla.png) |
| `ghouls-grip-print-accent-pla.3mf` | Totenkopf-Auslöser | 200 | 19,56 g | 1 h 07 min 09 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-accent-pla.png) |
| `ghouls-grip-print-fingers-pla.3mf` | Daumen und vier Finger | 57 | 12,01 g | 1 h 22 min 55 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-fingers-pla.png) |
| **Gesamt** | 33 physische Druckobjekte | - | **837,93 g** | **40 h 23 min 32 s** | - | - |

Nach der Fingerketten-Korrektur wurde
`ghouls-grip-print-fingers-pla.3mf` erneut mit demselben Profil gesliced:
57 Layer, 12,01 g, 1 h 22 min 55 s, Tree-Support und keine unaufgelösten
Toolpath-, Druckbett- oder Leerlagenfehler.

Die G-Code-Pfad-Vorschauen werden von `scripts/render_gcode_preview.py` direkt
aus den erfolgreichen OrcaSlicer-Ausgaben gerendert. Rosa markiert höhere,
blau niedrigere Extrusionspfade; die Bilder sind kein Ersatz für die
interaktive Layeransicht, belegen aber Platte, Bettlage und erzeugte Toolpaths.

## Behobene Slice-Probleme

1. Ohne Stützen meldete OrcaSlicer schwebende Bereiche an Fingern, Handteilen,
   Totenkopf, Deckel und Gehäuse. Bettgebundene Stützen beseitigen diese
   Warnungen.
2. Die fünf gestützten Mechanikteile erzeugten auf einer gemeinsamen Platte
   überlappende Stütz-/G-Code-Pfade. Sie wurden auf fünf Einzelprojekte
   aufgeteilt. Danach bestanden alle fünf Kollisionsprüfungen.
3. Die supportfreie Mechanik bleibt zusammen auf einer Platte, damit Arme,
   Schlitten und vollständige Pin-Stückzahlen gemeinsam geprüft werden.

## Dateibelege

Alle Dateien wurden am 2026-10-08 gegen den hier beschriebenen Slice-Stand
regeneriert. SHA-256:

| Datei | SHA-256 |
| --- | --- |
| `ghouls-grip-master.3mf` | `4FFAA81AA911C77F0191909AD5D2C279193F075819F618710C5A564425FCEAC7` |
| `ghouls-grip-master-retracted.3mf` | `D9B719864C32AD58569B4EF83BB7B7DEB26C9FD5A4D76220EF143F994D53ECCC` |
| `ghouls-grip-print-black-pla.3mf` | `F3943B53EED0658AE24C03229B5945876D764C2ED02F02141B674672CB14BB36` |
| `ghouls-grip-print-bone-pla.3mf` | `F009BDEC41E270C5E1116B4100A88DC40BDFA6A68E754845814B6F06AD5C0E8C` |
| `ghouls-grip-print-mechanism-pla.3mf` | `E3F8F0865559975912AF2389933DCE2395540C1111459EBFFCA0C4D3E0878A44` |
| `ghouls-grip-print-mechanism-supported-platform-pla.3mf` | `46F89CA5A1627FBC2EBAE0C6F8F5A7996C46D40E1D9EBA41552EC405C7DB555A` |
| `ghouls-grip-print-mechanism-supported-latch-rocker-pla.3mf` | `9C814FEA027A6FF71AC4F560E8CA570A699389CDED2EE15AA90C5383579E166A` |
| `ghouls-grip-print-mechanism-supported-latch-bracket-pla.3mf` | `3819005240948C6630A8DCF8E4EE7AD24CAC7A37D35645617C7A4253A821FED9` |
| `ghouls-grip-print-mechanism-supported-crank-pla.3mf` | `887860496E1EA3091A19F6A0C4993113932ACA866A3AFF9BF7449683636E2EB3` |
| `ghouls-grip-print-mechanism-supported-band-anchor-pla.3mf` | `8249AA87FF3613C8E16FFE9C43903E12CA906B702FE8CBDED0C126B319AA2A79` |
| `ghouls-grip-print-accent-pla.3mf` | `AAD5584D5BBE5538B6E86B5A93B3F2699570793AA3E4AC8073CCFF45EE466FB9` |
| `ghouls-grip-print-fingers-pla.3mf` | `9A5FD9E4FBE441D931D6F554EBBA44EA41F59174273305CE92CDB0B95346E51B` |

## Verbleibende physische Risiken

- Ein erfolgreicher Slice beweist keine reale Lebensdauer der 0,8-mm-PLA-
  Filmscharniere.
- Gummibandvorspannung, Seilspiel und Rastkraft müssen mit einem niedrigen
  Vorspannungs-Testaufbau abgestimmt werden.
- Gedruckte Pivot-Pins bleiben Verschleißteile; M3-Schrauben sind für die vier
  hoch belasteten Scherengelenke vorzuziehen.
- Vor dem Komplettdruck bleiben Arm-/Pin-/Passungscoupon und ein einzelner
  Finger-Testdruck verpflichtend.
