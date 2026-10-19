# The Ghoul's Grip – OrcaSlicer-Druckvalidierung

Slice-Ergebnis: **erfolgreich** mit OrcaSlicer CLI 2.4.2; Profilkonformität: **nicht verifiziert**.

**Stand 2026-10-19 (Schalenhand mit massiven Fingergelenken, bündig steckbarer Süßigkeitenschale und Gold-Platte 4):** Die Druckdatei hat vier Plates und
42 Objekte (29 Teiletypen inklusive Reservepins, Kurbel-Distanzhülse `crank-spacer` und abnehmbarer Süßigkeitenschale `candy-dish`; 31 Naturweißteile auf Platte 3, 2 Gold-PLA-Teile (`#D4AF37`) auf Platte 4). Die fünf Finger und der opponierte Daumen (`55°` Yaw) werden direkt in gekrümmter Schalenpose mit voll geschlossenen, massiven Knöchelübergängen (keine V-Kerben oder Gelenklücken) gedruckt; Sehnenkanäle sind entfernt und die MCP-Steckverbindungen zur Handfläche sind auf 0,4 mm Spiel abgestimmt. Die früheren hervorstehenden Schalen-Stützstege an `hand-palm` wurden durch drei bündig in die Mittelhandknochen eingelassene Sacklöcher (Ø3,4 × 3,6 mm, > 3,5 mm geschlossener Boden zum Handrücken) ersetzt; die kurzen Beine und Ø3,0-mm-Steckstifte sitzen jetzt direkt an der Unterseite der tiefer in die Hand eingebetteten `candy-dish` (`DISH_OFFSET = [-1.5, -2.5, -3.5]`), die kopfüber auf ihrem flachen oberen Rand gedruckt wird. Ohne eingesetzte Schale bleibt die Knochenhand völlig glatt und anatomisch. Die Schatulle, der Deckel, die Anschlüsse zur Schatulle und das gesamte Antriebs-/Unterarmgetriebe (35 Nicht-Hand-Mesh-Payloads) bleiben exakt unverändert (`docs/ghouls-grip-printed-box-contract.json`). Der Montage-Audit `docs/ghouls-grip-montage-audit.md` sowie der 61-Stellungen-Schalenhand-Audit `docs/ghouls-grip-candy-audit.md` bestehen alle Prüfungen (11,518 ml statisches Rückhaltevolumen bei 2 mm Freibord).
Der finale Slice wurde am 2026-10-19 in
`build/ghoul-final-slices/print/` abgelegt (Exit 0, vier G-Codes).
Die aktualisierte Druckdatei hat den SHA-256
`EF3466CF1AB941DEF0AF65A71500187F2376B7CDD6945AD9DAD0B5F424292031`
und wurde nach dem Speichern der Slice-Metadaten am 2026-10-19 aktualisiert.

Historie (2026-10-12): Damals wurden die 16 Objekte der früheren Naturweiß-Platte 4 mit den 11 Hauptteilen
von Platte 3 zusammengepackt. `scripts/consolidate_ghouls_grip_mechanism_plates.py`
erhält Teileorientierungen und Z-Lagen, lässt 6 mm Abstand zwischen den
Bauteil-Begrenzungsrahmen und mindestens 10 mm Bettrand. Anschließend wurden
die sieben Knochenobjekte auf Platte 2 ausschließlich in XY neu angeordnet;
Mesh-Payloads, Rotation und Z-Lagen bleiben erhalten. Ihr Footprint-Abstand
beträgt mindestens 6 mm, der Bettrandabstand mindestens 69 mm. Der aktualisierte
OrcaSlicer-CLI-Slice 2.4.2 lief danach mit Exit-Code 0 und vier G-Codes.
Die damalige Druckdatei-SHA ist durch den Stand vom 2026-10-19 ersetzt.

Aktuelle finale SHA-256 (2026-10-19):

| Datei | SHA-256 |
| --- | --- |
| `models/ghouls-grip-view.3mf` | `7D1AFF26E50068C934F8F995A2FE73AB86CEBB43CF4A0E4D977AB7BD02364B4A` |
| `models/ghouls-grip-preview.stl` | `2D957B9ACB1567544F0BFA421FF53062CC2B40B3E2E56C1811ACB0762FE394FC` |
| `models/ghouls-grip-print.3mf` | `EF3466CF1AB941DEF0AF65A71500187F2376B7CDD6945AD9DAD0B5F424292031` |

Schatulle: 76.838 Facetten, 209 × 130,5 × 98 mm, 200.928,569 mm³,
ein geschlossener Einzelkörper, konsistente Normalen, keine degenerierten
Dreiecke. Das komplette ASCII-STL ist bewusst eine montierte
42-Körper-Vorschau, kein Drucklayout; 42 Druckobjekte inklusive Reservepins
und abnehmbarer Süßigkeitenschale sind im vierplattigen Print-Projekt.
Die finale Ansichtsdatei `models/ghouls-grip-view.3mf` wurde im STL-Canvas
geöffnet; die gerenderte Farbansicht liegt zusätzlich unter
`docs/images/ghouls-grip-view-preview.png`.

Historie (2026-10-12, 37-Objekt-Stand): Die damalige Bodenlagerreparatur
ersetzte ausschließlich die Schatullen-Geometrie;
die übrigen **36 Mesh-Payloads bleiben byteidentisch** zur übernommenen
Nutzerdatei (`HEAD`). Alle 37 Mesh-Payloads, Objekt-Overrides, Farben,
Materialien und `project_settings.config` bleiben erhalten. Die 16
Getriebe-/Verbinderteile liegen jetzt gemeinsam mit den 11 Hauptteilen auf
Platte 3; alle 37 Objekte bleiben genau einmal in der vollständigen Stückliste.
Die exakte finale Druckdatei wurde unabhängig geladen: 37 geschlossene,
orientierungskonsistente Einzelkörper, null degenerierte Dreiecke, alle innerhalb
ihres 250-mm-Betts, Z-Bettkontakt mit 0,01-mm-Rundtoleranz; größtes Bauteil-/Bauteil-Schnittvolumen
auf einer Druckplatte 0,000 mm³. Auch die Arm-/Bodenlagerpaare der montierten
Mechanik bestehen jetzt den 61-Zustands-Nachweis; das ist keine Lastfreigabe.
Prüfartefakt: `build/ghoul-floor-bearing-delivery.json`.

![Aktuelle Vier-Platten-Übersicht](images/ghouls-grip-print-preview.png)

## Sichtbare Stützstrukturen

**Orange zeigt tatsächlich extrudierte Support- und Support-Interface-Bahnen**
aus den vier frischen G-Codes; transparentes Grau zeigt die zugehörigen
Bauteile. Es ist ein G-Code-Bahnrender, kein OrcaSlicer-UI-Screenshot.

![Alle vier Plates mit tatsächlichen Stützbahnen](images/ghouls-grip-print-support-overview.png)

Einzelansichten: [Platte 1 – Schwarz](images/ghouls-grip-print-plate-1-supports.png),
[Platte 2 – Knochenbeige](images/ghouls-grip-print-plate-2-supports.png),
[Platte 3 – Naturweiß, 31 Teile](images/ghouls-grip-print-plate-3-supports.png),
[Platte 4 – Gold](images/ghouls-grip-print-plate-4-supports.png).

Die Screenshots basieren exakt auf der aktuellen Druckdatei und den am
2026-10-19 erzeugten vier G-Codes in
`build/ghoul-final-slices/print/`.
Reproduktion:
`python scripts\render_ghouls_grip_print_projects.py build\ghoul-final-slices\print --project models\ghouls-grip-print.3mf`
und
`python scripts\render_ghouls_grip_supports.py build\ghoul-final-slices\print --project models\ghouls-grip-print.3mf`.
Die Supportpfade bleiben eine separate Bildvorschau und werden nicht in die
3D-Modellgeometrie eingeblendet. Canvas und Web-UI bieten jetzt zusätzlich
direkte Buttons für die einzelnen Plattenbilder; ein Klick öffnet das Bild groß.
## Profilvertrag und tatsächliche Nutzereinstellungen

Das Druckprojekt wurde vom Nutzer in OrcaSlicer geändert. Die aktuellen
Einstellungen werden hier dokumentiert und nicht stillschweigend auf frühere
Vorgaben zurückgesetzt:

- Drucker: `Anycubic Kobra S1 0.4 nozzle`; Düse/Schichthöhe: 0,4 mm / 0,20 mm
- Ein separat benannter Prozessprofilname ist in der 3MF nicht gespeichert;
  die Prozesswerte sind in `Metadata/project_settings.config` eingebettet.
- Filamentprofil: `Anycubic PLA @Anycubic Kobra S1 0.4 nozzle` für vier PLA-Slots
- Im gespeicherten Projekt: Bett `High Temp Plate`, Naht `aligned`, Bügeln
  `no ironing`, global `enable_support=0`, globale Basiswerte 2 Wandlinien und
  15 % Infill.
- Bauteil-Overrides aktivieren Support (`enable_support=1`) für die betreffenden
  Objekte; alle vier frischen G-Codes enthalten echte Supportbahnen. Platte 3
  enthält jetzt sämtliche Naturweißteile einschließlich der früheren
  Transferzahnräder.
- Support nur auf Druckplatte, globaler Typ `tree(auto)`; Objekt-Overrides
  verwenden teils `normal(auto)`.

Diese Datei weicht damit vom Projektstandard `Textured PEI Plate`, `seam=random`,
`ironing=top` und global aktiviertem Support ab. Der Slice war erfolgreich, aber
Profilkonformität und Druckbereitschaft sind **nicht verifiziert**. OrcaSlicer
meldete für alle vier Plates, dass `precise wall` bei den gewählten
Wandsequenzen ignoriert wird. Zusätzlich enthält `stdout.log` 489 Meldungen
`Not precalculated Placeable areas requested, radius 0, layer 0, critical: 0`.
Der Lauf endete dennoch mit Exit-Code 0 und erzeugte alle vier G-Codes; die
wiederholte Diagnose ist nicht als geklärt einzustufen. Es wurde keine
automatische Wiederherstellung oder Neuanordnung der Teile zugelassen.

## Bodenlagerkorrektur, Reproduktion und Freigabegrenze

Die zentralen kollidierenden Bodenpfosten sind als kurze Doppelwangen um
die unveränderten Armhüllen neu aufgebaut. Der 12-mm-Kanal gibt 1 mm
Axialabstand; die 4-mm-Wangen haben 3 mm radiale Bohrungsstege und direkt
angebundene 9,2 × 4 mm Bodenwurzeln. Alle neuen Maße sind
Konstruktionsschätzungen/Default-Freiräume und brauchen einen PLA-Passungs-
und Lasttest, keine neu behaupteten Messwerte.
Die bestehenden 26-mm-Pins werden von der Kistenmitte eingeführt;
der Kopf des positiven Bodenpins ist im Ansichtsprojekt entsprechend
gespiegelt. Der Print-Pin und die komplette Stückliste bleiben unverändert.

Der ursprüngliche Wandcutter (14 × 12 × 24 mm bei X=-27, Y=58, Z=75)
ist entfernt. Der Folgejoch-Rack liegt 14,854 mm weiter innen; zwei gleiche
Transferzahnräder erhalten 1:1-Übersetzung, 7-mm-Hub und 108° Deckelbewegung.
Die neue Journalhalterung und die asymmetrische Haube schneiden weder Wand
noch mittleren Scharnierbock. Die Dach-/Wandproben zeigen durchgängiges Material.

Beim Print-Refresh verursachte reine Bounds-Zentrierung der höheren neuen Kurbel
einen Boden unter Z=0; OrcaSlicer 2.4.2 brach dabei mit Access Violation ab.
Der Export erhält jetzt die originale transformierte Bettkontakt-Ebene.
Historischer Befund der Wandkorrektur: Die 31 damals unbetroffenen Payloads
wurden nicht neu gerundet. Sowohl fünf einzelne
Platten-Slices als auch der abschließende `--slice=0`-Kontrolllauf waren danach
erfolgreich. Der **aktuelle finale** Kontrolllauf am 2026-10-12 mit
`scripts/slice_ghouls_grip.ps1` hat nach der Plattenzusammenlegung Exit-Code 0
und vier echte G-Codes. Die Kopfzeile jedes frischen G-Codes
bestätigt OrcaSlicer 2.4.2. Die tatsächliche Installation wurde unter
`C:\Program Files\OrcaSlicer\orca-slicer.exe` gefunden;
`--help` endete mit Exit 0 ohne Konsolentext, daher wurden die bereits
funktionierenden Optionen des vorhandenen Slice-Skripts verwendet.
Die externen Mesh-Relationships sind ohne XML-Namenspräfix serialisiert, wie
Orcas Importer es erwartet.

| Befehl / Nachweis | Ergebnis |
| --- | --- |
| `.\.venv\Scripts\python.exe -m unittest discover -s tests` | PASS: 63 Tests (Stand 2026-10-17) |
| `.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_ghouls_grip_print_refresh.py -v` | nach finaler Bettkontakt-Korrektur erneut bestanden; Originaltransforms, Overrides, Plate-Zuordnung, unveränderte Payloads und Idempotenz |
| `.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_slice_support_usage.py -v` | 3 Tests bestanden; M82/M83/G92 und Rückstellungen |
| `.\.venv\Scripts\python.exe scripts\verify_ghouls_grip_mechanics.py` | Gesamt-Nachweis PASS; 61 Scherenstellungen von 18° bis 78° inkl. 48°, alle vier individuellen Arm-/Kistenpaare jetzt hartes Fail-Gate bei >0,001 mm³; übrige geprüfte Paare 0 mm³; JSON in `build/ghoul-floor-bearing-verification.json` |
| `python scripts\consolidate_ghouls_grip_mechanism_plates.py` | PASS: alle 31 Naturweißteile auf einer Platte; mindestens 10 mm Bettrand, 6 mm Rahmenabstand, Teileorientierungen und Mesh-Payloads erhalten |
| `python scripts\arrange_ghouls_grip_bone_plate.py` | PASS: sieben Teile auf Platte 2 mit mindestens 6 mm Footprint-Abstand und mindestens 69 mm Bettrandabstand; nur XY-Translationen geändert |
| `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\slice_ghouls_grip.ps1` | Exit 0 und vier frische OrcaSlicer-2.4.2-G-Codes |
| `python scripts\update_ghouls_grip_slice_metadata.py build\ghoul-final-slices\print --project models\ghouls-grip-print.3mf` | PASS: finale Slice-Kennzahlen gespeichert; Profilstatus weiter `not-verified` |
| `python scripts\verify_ghouls_grip_candy.py --output build\ghoul-candy-verification.json --report docs\ghouls-grip-candy-audit.md` | PASS: 61 Posen, 35 eingefrorene Nicht-Hand-Payloads unverändert, >= 11,518 ml statisches Rückhaltevolumen bei 2 mm Freibord, alle 61 Einschubschritte (0..60 mm) frei |
| `python scripts\compact_output.py run --log build\test-assembly.log -- python -m unittest discover -s tests -p test_ghouls_grip_assembly.py -v` | PASS: 8 Tests (inkl. massiver Fingergelenke, Daumen-Opposition, bündiger Handflächen-Sacklöcher und Schalen-Steckstifte), Exit 0 |
| `python scripts\render_ghouls_grip_print_projects.py build\ghoul-final-slices\print --project models\ghouls-grip-print.3mf` und `python scripts\render_ghouls_grip_supports.py build\ghoul-final-slices\print --project models\ghouls-grip-print.3mf` | vier Plattenvorschauen, Komplett-Projektvorschau und vier tatsächliche G-Code-Support-Sidecars |
| `python scripts\mesh_tool.py validate models\ghouls-grip-preview.stl --allow-multibody` | PASS: 274.242 Facetten, 42 absichtlich getrennte montierte Körper, wasserdicht/orientierungskonsistent, null degenerierte Dreiecke, Euler-Zahl -180; die nicht druckbare Assembly-Vorschau ist im center-origin-System um 5,898 mm in Y versetzt und wurde nicht automatisch verschoben |

**Die dokumentierte Arm-/Bodenlagerkollision ist beseitigt:** Baseline
496,131 / 519,274 / 554,635 mm³ bei 18° / 48° / 78°; aktuell
0,000 mm³ bei drei Nachkommastellen in allen 61 Zuständen.
Maximaler numerischer Rest je Einzelarm: 0,000020464 mm³ an der
tangentialen Bodenberührung, unter 0,001 mm³ Boolean-Toleranz.
Das ist ausdrücklich kein mathematisch exakt nuller Floating-Point-Wert.
Alle anderen im Vollnachweis geprüften Paare sind 0 mm³ und die
Wandfüllung bleibt 100 %. Einzelpaarvolumina stehen in der
[Mechanik-Verifikation](ghouls-grip-mechanik-verifikation.md).
Weiterhin keine physische Druck-/Lastfreigabe: PLA-Passung,
Supportentfernung aus kleinen Querbohrungen, Axialwanderung der bisherigen
unverriegelten Bodenpins, Journalspiel, Zahnprofile, Bodeneinleitung und
Dauerfestigkeit müssen getestet werden. Der Slice enthält echte Supports,
deren Entfernbarkeit im kleinen Lagerbereich noch physisch zu prüfen ist.

![Exakter Endstand, durchgehende Wand und innenliegender Deckelantrieb](images/ghouls-grip-continuous-wall.png)

![Exakte Doppelwangen und unveränderte Arme, Kiste transparent](images/ghouls-grip-floor-bearings.png)

## Ergebnisse des aktuellen Slices

| Plate | Inhalt | Schichten | Filament | davon Stützen | Zeit | Ansicht |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 – Schwarz | Schatulle und Deckel (2) | 649 | 334,99 g | 6,71 g (2,0 %) | 12 h 02 min 22 s | [Supportbild](images/ghouls-grip-print-plate-1-supports.png) |
| 2 – Knochenbeige | Unterarm, Handfläche und Finger (7) | 482 | 45,77 g | 7,43 g (16,2 %) | 3 h 10 min 26 s | [Supportbild](images/ghouls-grip-print-plate-2-supports.png) |
| 3 – Naturweiß | Hauptmechanik, Zahnräder, Wellen, Pins und Kurbel-Distanzhülse (31) | 631 | 111,63 g | 11,48 g (10,3 %) | 4 h 35 min 22 s | [Supportbild](images/ghouls-grip-print-plate-3-supports.png) |
| 4 – Gold | Totenkopf-Auslöser und Süßigkeitenschale (2) | 195 | 36,40 g | 6,58 g (18,1 %) | 1 h 45 min 40 s | [Supportbild](images/ghouls-grip-print-plate-4-supports.png) |
| **Gesamt** | **42 Druckobjekte / 4 Plates** | – | **528,79 g** | **32,20 g (6,1 %)** | **21 h 33 min 50 s** | [Übersicht](images/ghouls-grip-print-support-overview.png) |

| Farbgruppe | Zeit | Masse | Stützmaterial | Länge | Volumen | Plates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Schwarz | 43.342 s | 334,99 g | 6,71 g | 112.316,83 mm | 270.150 mm³ | 1 |
| Knochenbeige | 11.426 s | 45,77 g | 7,43 g | 15.345,02 mm | 36.910 mm³ | 1 |
| Naturweiß | 16.522 s | 111,63 g | 11,48 g | 37.426,25 mm | 90.020 mm³ | 1 |
| Gold | 6.340 s | 36,40 g | 6,58 g | 12.202,89 mm | 29.350 mm³ | 1 |
| **Gesamt** | **77.630 s** | **528,79 g** | **32,20 g** | **177.290,99 mm** | **426.430 mm³** | **4** |

Die G-Code-Header weisen Gesamtkosten von 10,33 in der konfigurierten
OrcaSlicer-Kosteneinheit aus; eine Währungsbezeichnung ist in den Projektdaten
nicht dokumentiert.

Die Supportanteile werden aus positiven Extrusionen der Support-/Interface-
Bewegungen berechnet; `M82`, `M83` und `G92` werden berücksichtigt,
Extruder-only-Rückstellungen nicht als gedruckter Support gezählt.
Die vorherige absolute-E-Auswertung der relativen Orca-Extrusion war falsch.
Masse und Volumen werden mit dem jeweiligen Slice-Verhältnis umgerechnet:

| Plate | Supportlänge | Supportvolumen |
| --- | ---: | ---: |
| 1 | 2.249,61 mm | 5.411 mm³ |
| 2 | 2.492,69 mm | 5.996 mm³ |
| 3 | 3.849,50 mm | 9.259 mm³ |
| 4 | 2.205,44 mm | 5.304 mm³ |
| **Gesamt** | **10.797,24 mm** | **25.970 mm³** |

Die Summen und vier Einzelergebnisse sind in `models/ghouls-grip-print.3mf`
als slicer-neutrale Metadaten gespeichert; alle vier Platten stehen dort auf
`not-verified`. Der Metadatenstatus bleibt
`not-verified`, bis Profilabweichungen und CLI-Diagnose geprüft sind.
G-Code-, Mesh- und Modellhashes sowie ausgeführte Befehle stehen zusammen
in `build/ghoul-floor-bearing-quality.json`; Vollsweep und Print-Prüfung in
`build/ghoul-floor-bearing-verification.json` und
`build/ghoul-floor-bearing-delivery.json`.
### Historische Orientierungsoptimierung (A/B-gemessen, nicht aktueller Slice)

Alle Druckorientierungen sind durch echte A/B-Slices belegt. Die Audit-Skripte
klonen dieselbe Projektvorlage und tauschen nur das Build-Item aus, sodass
ausschließlich die Orientierung variiert:

| Teil | Orientierung | Stütz-Extrusion | Alternativen |
| --- | --- | ---: | --- |
| Deckel | auf der Hinterkante stehend | **4.598,9 E** | aufrecht 20.336,1 · kopfüber 20.553,3 · Vorderkante 14.840,6 |
| Handfläche | auf dem Handgelenkschnitt stehend | **290,0 E** | wie gebaut 2.958,9 · gespiegelt 1.970,5 · seitlich 2.084,5–3.102,7 |
| Totenkopfknopf | Gesicht nach oben auf dem Wellenbund | **968,7 E** | wie gebaut 3.266,5 · seitlich 655,8–793,9 (verworfen: Stützen im Gesicht) |
| Unterarm | wie gebaut | **0,0 E** | alle gekippten Varianten 318,2–414,1 |

Skripte: `scripts/audit_lid_orientation.py`, `scripts/audit_part_orientation.py`,
`scripts/audit_chest_support.py`.

Historischer Vergleich vor dieser Wandkorrektur: Gegenüber dem damals
verifizierten Stand (528,22 g / 138,60 g Support) sank der
Stützbedarf um **83,21 g / 60,0 %** und die Gesamtmasse um 11,38 g. Die
gemessenen Orientierungswechsel tragen den Hauptteil der Einsparung; die
zusätzliche geschlossene Deckelhaube erhöht das schwarze Projekt nur um 1,59 g.
Gegenüber dem ursprünglichen 629,66-g-Entwurf beträgt die Materialeinsparung
**112,82 g / 17,9 %**, gegenüber der Vor-Leichtbau-Schatulle (455,96 g schwarz)
**125,00 g / 27,4 %**.

Der Nutzerstand vor der Wandkorrektur lag bei 77.721 s, 527,20 g Filament und
28,42 g Support. Die aktuelle Änderung erhöht das um 279 s, 1,76 g Filament
und 1,36 g Support. Diese Differenz stammt aus echten Slices; die historischen
Werte ersetzen nicht die oben aufgeführten neuen Ergebnisse.

## Stützen und Objekt-Overrides

- Schatulle/Deckel: 3 Wände, 10 % Gyroid, Baumstützen `tree(auto)` bettgebunden;
  analytischer maximaler Deckel-Brückenspalt 10,0 mm, Schatulle 6,0 mm.
- Mechanik: 5–6 Wände, modellierte Öffnungen, Rahmen, Rippen und Speichen;
  20–50 % Infill in den verbleibenden Hohlräumen. Arme und Pins bleiben durch
  Wandlinien praktisch massiv.
- Hand/Knochen: 4 Wände, 25 %; die Handfläche steht auf dem Handgelenkschnitt,
  wodurch Fingertaschen und Daumenballen senkrecht statt überhängend drucken.
- Finger: 2 Wände, 15 %, 30 mm/s Außenwand und reduzierte Beschleunigung für die schlanken gekrümmten Finger mit massiven Gelenkübergängen.
- Totenkopfknopf: 5 Wände, 40 %, Gesicht nach oben, damit keine Stützstruktur
  die skulptierte Fläche berührt.
- Süßigkeitenschale (`candy-dish`): 4 Wände, 15 %, automatische Baumstützen (`tree(auto)`), auf dem flachen Boden neben dem Totenkopf auf Platte 4 platziert.

## Beibehaltene Support-/Materialoptimierung und Wandkorrektur

- Der Deckel besitzt eine 2,4-mm-Deckhaut, offene Unterseiten-Träger,
  fünf gerippte Längstraversen und fünf kurze hintere Anschlagpads statt eines
  massiven, 193 mm breiten Querriegels. Er steht auf seiner Hinterkante: in
  dieser Lage ist weder die hohle Innendecke noch das skulptierte Kartuschen-
  relief ein großer Überhang (4.598,9 statt 20.336,1 Stütz-E).
- Der frühere durchgehende Servicekanal für Yoke und Deckelkurbel ist nach außen
  vollständig geschlossen. Eine lokale schwarze Haube besitzt eine 2,0-mm-
  Dachhaut, eine ausschließlich nach innen offene Montagekavität und eine
  gemessene Labyrinth-Freistellung am Scharnier. Im geschlossenen Zustand liegt
  jedes interne Mechanikteil unter dieser Deckelgeometrie; der vollständige
  18°–78°-Sweep ergibt für `lid_crank_lid`, `lid_yoke_lid`, `lid_chest` und
  die jeweiligen Brustkontakte jeweils **0,000 mm³**.
- In der aktuellen Nutzerdatei teilen sich Schatulle und stehender Deckel
  dieselbe schwarze Platte; beide passen nebeneinander innerhalb des 250-mm-Betts.
  Die vorherige Sechs-Platten-Aufteilung hatte dafür zwei separate Schwarz-Platten.
- Der Sockel und der obere Kranz der Schatulle wurden von horizontalen Stufen
  auf zwei geneigte, selbsttragende Kurse umgebaut. Die Pilasterkapitelle und
  die Unterseiten der Scharnierlager sind ebenfalls geneigt.
- Die dekorative Schatullenwand und der Boden sind 2,0 mm stark; die
  3,0-mm-Funktionsdatums an Schienen, Lagern und Führungen bleiben erhalten.
  Gerundete Außenkanten sowie vertiefte statt aufgesetzte Reliefs wirken
  organischer und vermeiden zusätzliche massive Zierkörper.
- Historischer Leichtbauschritt: Das Schatullen-Volumen sank von 295.062 auf 184.056 mm³
  (**−37,6 %**), das Deckelvolumen von 252.068 auf 124.903 mm³
  (**−50,5 %**). Zusammen sind das **−43,5 % Modellvolumen**.
- Acht überarbeitete Mechanikteile sanken durch offene Rahmen, Fenster und
  Speichen von 118.567 auf 82.649 mm³ (**−30,3 %**).
- Der Deckel bleibt ein einzelner watertight/manifold Körper:
  27.868 Facetten, 206 × 129,786 × 28,2 mm. Die aktuelle Schatulle hat
  199.297,757 mm³, der Deckel 134.466,876 mm³. Die lokale Schutzhaube ist nur
  2,6 mm höher als das skulptierte Kartuschenrelief und enthält keine
  getrennten oder eingeschlossenen Körper.
- Die Schienen- und Lagerbooleans werden zuerst in der bewährten Kernschale
  erzeugt; die geneigten Zierkurse werden danach kontrolliert angefügt. Dadurch
  bleiben die mechanischen Führungen geschlossen und manifold.
- Die aktualisierten farbigen Plattenvorschauen wurden aus den neuen 3MF-Szenen
  regeneriert. Sie zeigen die Material-/Farbgruppierung, nicht geslicte
  Supportvolumina.

## Anzeige in Canvas und Web-Viewer

Die ausgelieferten 3MF-Dateien enthalten die verifizierten Projektwerte direkt
in `Metadata/ghouls_grip_print_metadata.xml`. Der gemeinsame Web-/Canvas-
Renderer zeigt daraus:

- eine kompakte Zeile mit Druckzeit, Gesamtmaterial, Supportmaterial,
  Filamentlänge und Validierungsstatus für **alle Plates**, unabhängig von
  der ausgewählten Ansicht;
- ein einklappbares Detail-Overlay rechts unten mit Maschine, Düse, Prozess,
  Filamentprofil, Material, Farbe, Bett, Wandzahl, Infill, Support und
  Plattenzahl;
- im Detail-Overlay eine separat aufklappbare Tabelle **Print data by plate**
  mit Druckzeit, Material, Supportmaterial, Filamentlänge, Supportlänge, Status und einem
  Supportbild-Button pro gesliceter Plate. Die Bilder zeigen die tatsächlich
  extrudierten Supportbahnen und sind in Canvas sowie Webview per Dialog
  anzusehen. Fehlende oder fehlerhafte Plate-Metadaten werden ausdrücklich angezeigt;
- ein Projektvorschau-Button für das vollständige farbcodierte
  Vier-Platten-Druckprojekt;
- die korrekte einzelne Platte oder alle Platten unter Berücksichtigung von
  3MF-Komponenten-Transformationen und OrcaSlicer-`plater_id`;
- ein einklappbares Werkzeugmenü für Reload, Auto-Reload, Zoom, Wireframe,
  Shading, Ansichten, Rotation, Hilfsanzeigen und Messung.

Mehrplattige Dateien starten in Canvas und Web-Viewer mit **All plates**.
Mehr als zwei Platten stehen nur in der Gesamtansicht in einem Grid mit
50 mm Zwischenraum; zwei Platten stehen nebeneinander. Die Einzelplatten-
Transformationen bleiben unverändert. Materialfarben folgen OrcaSlicers
Filamentpalette mit Objekt- und Teilzuweisungen; bei Standard-3MF-Dateien
werden weiterhin die 3MF-Materialressourcen verwendet.
Die Druckübersicht zeigt die eingebetteten
Projekt-Gesamtwerte (Zeit, Material, Support und Filamentlänge) sowie die
Plattenzahl. Einzelplatten bleiben über **Plate** auswählbar. Reload derselben
Datei behält die Auswahl; beim Öffnen einer anderen Datei wird wieder
**All plates** gewählt. Einzelplatten-3MF und STL bleiben unverändert.

Viewer-Prüfung (2026-10-12): `npm test --prefix web` bestanden
(22 Tests); `npm run build --prefix web` bestanden. Browser-Screenshots des lokalen
Canvas und der gebauten Web-SPA bestätigen beide schwarzen Druckplatten in
der Übersicht und die Projekt-Gesamtwerte. Einzelplattenwahl, Reload,
Dateiwechsel zur View-3MF und Auto-Reload einer anderen Mehrplatten-Datei
wurden ebenfalls geprüft.

In der lokalen Copilot-Canvas-Erweiterung öffnet **3mf öffnen** die
exakt ausgewählte Workspace-3MF mit dem registrierten Standardprogramm über einen lokalen POST-Endpunkt mit
Nonce-Prüfung und Pfadvalidierung. Der Button wird für STL, unsichere Pfade und
die öffentliche Web-SPA nicht als Desktop-Startweg angeboten.

## Behobene Probleme

1. 3MF-Build- und Komponenten-Transformationen sowie Orcas `plater_id` werden vom Canvas berücksichtigt; Objekte liegen nicht mehr übereinander.
2. Die interne Führung besitzt eine 1,8-mm-Außenabdeckung; außen bleibt die Kiste geschlossen.
3. Alle 31 naturweißen Mechanikteile sind kollisionsfrei auf einer
   250-mm-Platte gruppiert; jedes der 41 Druckobjekte ist genau einmal
   einer von vier Materialplatten zugeordnet.
4. Der frühere Hebel, Rastschieber, die Spule, Schlüssel, Bandanker, Seile, Gummibänder und Federn sind entfernt. Der graue Totenkopf dreht direkt die Ritzelwelle.
5. `scripts/render_ghouls_grip_print_projects.py` rendert alle vier
   farbcodierten Plattenvorschauen direkt aus der aktuellen 3MF-Datei.
   Das gespeicherte OrcaSlicer-Plattenraster wird abhängig von der Plattenzahl
   aufgelöst (drei Spalten bei fünf, zwei bei vier Plates); 300-mm-X- und
   -Y-Abstände werden für Einzelplattenbilder anhand der tatsächlichen
   Plattenzuordnungen entfernt.

## Dateibelege

Druckprojekt-Zeitstempel: `2026-10-19 15:44:40 UTC`.

| Datei | SHA-256 |
| --- | --- |
| `ghouls-grip-view.3mf` | `E325A4FDE54291256764328CCEAD007905607471CBA0798D8F6EBAF9ABE1D84B` |
| `ghouls-grip-preview.stl` | `E47873CE3DBB4E2192C9B89E549963A503C60DE109EEEFAF51E5722A193C4C10` |
| `ghouls-grip-print.3mf` | `024B680C48ED15F857201DEC84A029E69912E3578A38DA648FD4A126412659E8` |

## Physische Restrisiken

- Der direkte Totenkopf hat weniger mechanische Hebelwirkung als der verworfene lange Hebel. Passungen und Zahnflanken vor der Endmontage entgraten.
- Erfolgreiches Slicen und die kollisionsfreie Simulation ersetzen keinen realen Dauerlauf.
- Gedruckte Pins sowie PLA-Flexuren verschleißen. Hoch belastete Scherengelenke vorzugsweise mit M3×16-Schrauben sichern.
- Vor dem Komplettdruck bleiben Arm-/Pin-/Zahnrad-Passungscoupon und ein einzelner Finger-Testdruck empfohlen.
