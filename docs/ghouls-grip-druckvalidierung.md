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
| `ghouls-grip-print-black-pla.3mf`, Platte 2 | Schatulle ohne offene Klinkenfenster | 490 | 400,39 g | 15 h 34 min 35 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-black-pla-plate_2.png) |
| `ghouls-grip-print-bone-pla.3mf` | Geneigter Unterarm, nach oben gerollte Handfläche, Sehnenführung | 284 | 53,21 g | 3 h 33 min 36 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-bone-pla.png) |
| `ghouls-grip-print-mechanism-pla.3mf` | 4 Scherenarme, Schlitten, 8 kleine und 4 große Pins | 170 | 50,10 g | 2 h 30 min 41 s | nein | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-pla.png) |
| `ghouls-grip-print-mechanism-supported-platform-pla.3mf` | Hubjoch | 344 | 46,21 g | 1 h 58 min 44 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-platform-pla.png) |
| `ghouls-grip-print-mechanism-supported-latch-slider-pla.3mf` | Interner Rastschieber | 344 | 8,94 g | 32 min 29 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-latch-slider-pla.png) |
| `ghouls-grip-print-mechanism-supported-latch-bracket-pla.3mf` | Interne Rastschieberführung mit Montagepads | 170 | 18,93 g | 35 min 22 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-latch-bracket-pla.png) |
| `ghouls-grip-print-mechanism-supported-crank-pla.3mf` | Interne Spule und abnehmbarer Schlüssel | 165 | 5,73 g | 22 min 31 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-crank-pla.png) |
| `ghouls-grip-print-mechanism-supported-band-anchor-pla.3mf` | Bandanker | 143 | 12,25 g | 39 min 56 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-band-anchor-pla.png) |
| `ghouls-grip-print-accent-pla.3mf` | Flacher Totenkopf-Auslöser mit kurzem Stößel | 107 | 14,32 g | 51 min 09 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-accent-pla.png) |
| `ghouls-grip-print-fingers-pla.3mf` | Daumen und vier Finger | 57 | 12,01 g | 1 h 22 min 55 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-fingers-pla.png) |
| **Gesamt** | 34 physische Druckobjekte | - | **851,36 g** | **40 h 25 min 59 s** | - | - |

Nach der Änderung auf die geneigte, handflächenoffene Präsentationslage wurde
`ghouls-grip-print-bone-pla.3mf` erneut mit demselben Profil gesliced:
284 Layer, 53,21 g, 3 h 33 min 36 s, Tree-Support und keine unaufgelösten
Toolpath-, Druckbett- oder Leerlagenfehler. Die Fingerplatte bleibt gegenüber
der zuvor verifizierten Fingerketten-Korrektur unverändert.

Die G-Code-Pfad-Vorschauen werden von `scripts/render_gcode_preview.py` direkt
aus den erfolgreichen OrcaSlicer-Ausgaben gerendert. Rosa markiert höhere,
blau niedrigere Extrusionspfade; die Bilder sind kein Ersatz für die
interaktive Layeransicht, belegen aber Platte, Bettlage und erzeugte Toolpaths.

## Behobene Slice-Probleme

1. Ohne Stützen meldete OrcaSlicer schwebende Bereiche an Fingern, Handteilen,
   Totenkopf, Deckel und Gehäuse. Bettgebundene Stützen beseitigen diese
   Warnungen.
2. Die gestützten Mechanikteile erzeugten auf einer gemeinsamen Platte
   überlappende Stütz-/G-Code-Pfade. Sie wurden auf fünf Einzelprojekte
   aufgeteilt. Spule und abnehmbarer Schlüssel teilen sich eine Platte mit
   30 mm Objektabstand und 20 mm Bettrand; danach bestanden alle
   Kollisions- und Druckbettprüfungen.
3. Die supportfreie Mechanik bleibt zusammen auf einer Platte, damit Arme,
   Schlitten und vollständige Pin-Stückzahlen gemeinsam geprüft werden.

## Dateibelege

Alle Dateien wurden am 2026-10-08 gegen den hier beschriebenen Slice-Stand
regeneriert. SHA-256:

| Datei | SHA-256 |
| --- | --- |
| `ghouls-grip-master.3mf` | `BF7EB4EDB047D935ABA0241B03E2314C9CC5306930E8DE1127AD244C57B5AAD4` |
| `ghouls-grip-master-retracted.3mf` | `95967162398AE5CFA751BD9B581CC8A072F58096AAB1928DE972BB32AFBD2E02` |
| `ghouls-grip-print-black-pla.3mf` | `DC2497738AECE10B078A0464AC9465A781173D018287D950306F3183B6C75A4C` |
| `ghouls-grip-print-bone-pla.3mf` | `0752E8D05864D4AE057553A367DFBCE915450C0C19A5CF7C5438E14BAA3F2DED` |
| `ghouls-grip-print-mechanism-pla.3mf` | `45FBAFDBD69E267CDD1A17C47C42DE0B2FB6F13EE3F4E8AD1E2015652B3F7641` |
| `ghouls-grip-print-mechanism-supported-platform-pla.3mf` | `8FE9E27AE31B1FA8985A88D6EE615899BF822B16C697A92A80ECA3FDD2CBC9C7` |
| `ghouls-grip-print-mechanism-supported-latch-slider-pla.3mf` | `A3F6709EE5148FC353F6C61E893A81BD31CB12AB0756377FE57CE50988E756D0` |
| `ghouls-grip-print-mechanism-supported-latch-bracket-pla.3mf` | `659B4457413D3D3A6447EA7536911789C978704039CBDBF5DCE43FD211849FD7` |
| `ghouls-grip-print-mechanism-supported-crank-pla.3mf` | `6C7159E5F025DBEA4C1F9A3CE15160ADFE48F15F03330EB1DE8F3B5CAEAD71A2` |
| `ghouls-grip-print-mechanism-supported-band-anchor-pla.3mf` | `82934F603F5007B3E7C2AC734D630FD4573E1B16E94AB7EC2180BCE8E6FA0296` |
| `ghouls-grip-print-accent-pla.3mf` | `EDAFBCFB91DB708F40D0CDFD04404F6682D86C16E59FB8EE42D57E7A29E5BC1F` |
| `ghouls-grip-print-fingers-pla.3mf` | `0583081F3B0224B13E08F9760EC6F516F10DE976204A6AB2775FD1202D5C54D1` |

## Verbleibende physische Risiken

- Ein erfolgreicher Slice beweist keine reale Lebensdauer der 0,8-mm-PLA-
  Filmscharniere.
- Gummibandvorspannung, Seilspiel und Rastkraft müssen mit einem niedrigen
  Vorspannungs-Testaufbau abgestimmt werden.
- Gedruckte Pivot-Pins bleiben Verschleißteile; M3-Schrauben sind für die vier
  hoch belasteten Scherengelenke vorzuziehen.
- Vor dem Komplettdruck bleiben Arm-/Pin-/Passungscoupon und ein einzelner
  Finger-Testdruck verpflichtend.
