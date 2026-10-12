# The Ghoul's Grip – OrcaSlicer-Druckvalidierung

Slice-Ergebnis: **erfolgreich** mit OrcaSlicer CLI 2.4.2; Profilkonformität: **nicht verifiziert**.

Die korrigierte Druckdatei hat fünf Plates und 37 Objekte. Der frische Slice
wurde am 2026-10-12 aus `models/ghouls-grip-print.3mf` erzeugt.
SHA-256 der Slice-Eingabe:
`ECBBEF59149898DD2EF6E12B4B6D6452004245496125DD89904A31550C9F7AB2`.
Nach Ergänzung der Druckmetadaten lautet der SHA-256 der Ausgabedatei:
`770BD97BD47C1F17CB70FB96AE29FC918638C7142442921230E31DBBA5BAAD74`.
Geometrie, Plate-Anordnung und Druckeinstellungen wurden dabei nicht geändert.

Die Wandkorrektur ersetzt ausschließlich Schatulle, Deckel, Folgejoch/Zahnstange
und Deckelkurbel; die übrigen 31 ursprünglichen Mesh-Payloads bleiben byteidentisch.
Alle 35 ursprünglichen Build-Transforms, Objekt-Overrides, fünf Plattengruppen
und `project_settings.config` bleiben erhalten. Zwei Transferzahnräder ergänzen
die bestehende Verbinderplatte in freiem Raum.
Die exakte finale Druckdatei wurde unabhängig geladen: 37 geschlossene,
orientierungskonsistente Einzelkörper, null degenerierte Dreiecke, alle innerhalb
ihres 250-mm-Betts, Z-Bettkontakt mit 0,01-mm-Rundtoleranz; größtes Bauteil-/Bauteil-Schnittvolumen
auf einer Druckplatte 0,000 mm³. Das betrifft die Druckanordnung, nicht die
unten ausdrücklich eingeschränkte montierte Gesamtmechanik.

![Aktuelle Fünf-Platten-Übersicht](images/ghouls-grip-print-preview.png)

## Sichtbare Stützstrukturen

**Orange zeigt tatsächlich extrudierte Support- und Support-Interface-Bahnen**
aus den fünf frischen G-Codes; transparentes Grau zeigt die zugehörigen
Bauteile. Es ist ein G-Code-Bahnrender, kein OrcaSlicer-UI-Screenshot.

![Alle fünf Plates mit tatsächlichen Stützbahnen](images/ghouls-grip-print-support-overview.png)

Einzelansichten: [Platte 1 – Schwarz](images/ghouls-grip-print-plate-1-supports.png),
[Platte 2 – Knochenbeige](images/ghouls-grip-print-plate-2-supports.png),
[Platte 3 – Naturweiß](images/ghouls-grip-print-plate-3-supports.png),
[Platte 4 – Naturweiß](images/ghouls-grip-print-plate-4-supports.png),
[Platte 5 – Grau](images/ghouls-grip-print-plate-5-supports.png).

Die Screenshots basieren exakt auf der aktuellen Nutzerdatei und den am
2026-10-12 neu erzeugten G-Codes in `build/ghoul-final-slices/print/`.
Reproduktion:
`.\.venv\Scripts\python.exe scripts\render_ghouls_grip_print_projects.py build\ghoul-final-slices\print --project models\ghouls-grip-print.3mf`
und
`.\.venv\Scripts\python.exe scripts\render_ghouls_grip_supports.py build\ghoul-final-slices\print --project models\ghouls-grip-print.3mf`.
Canvas/Webview zeigen die Modellgeometrie und Metadaten, aber keine Supportpfade.
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
  Objekte; alle fünf frischen G-Codes enthalten echte Supportbahnen, auch
  0,54 g auf Platte 4 für die ergänzten Transferzahnräder.
- Support nur auf Druckplatte, globaler Typ `tree(auto)`; Objekt-Overrides
  verwenden teils `normal(auto)`.

Diese Datei weicht damit vom Projektstandard `Textured PEI Plate`, `seam=random`,
`ironing=top` und global aktiviertem Support ab. Der Slice war erfolgreich, aber
Profilkonformität und Druckbereitschaft sind **nicht verifiziert**. OrcaSlicer
CLI gab wiederholt die Diagnose `Not precalculated Placeable areas requested`
aus, erzeugte aber Exit-Code 0 und alle fünf G-Codes. Diese Meldung wurde nicht
im OrcaSlicer-GUI nachbewertet.

## Korrektur, Reproduktion und Freigabegrenze

Der ursprüngliche Wandcutter (14 × 12 × 24 mm bei X=-27, Y=58, Z=75)
ist entfernt. Der Folgejoch-Rack liegt 14,854 mm weiter innen; zwei gleiche
Transferzahnräder erhalten 1:1-Übersetzung, 7-mm-Hub und 108° Deckelbewegung.
Die neue Journalhalterung und die asymmetrische Haube schneiden weder Wand
noch mittleren Scharnierbock. Die Dach-/Wandproben zeigen durchgängiges Material.

Beim Print-Refresh verursachte reine Bounds-Zentrierung der höheren neuen Kurbel
einen Boden unter Z=0; OrcaSlicer 2.4.2 brach dabei mit Access Violation ab.
Der Export erhält jetzt die originale transformierte Bettkontakt-Ebene.
Die 31 unbetroffenen Payloads werden nicht neu gerundet. Sowohl fünf einzelne
Platten-Slices als auch der abschließende `--slice=0`-Kontrolllauf waren danach
erfolgreich: Exit-Code 0, fünf echte G-Codes, keine Layout-/Profiländerung.
Die externen Mesh-Relationships sind ohne XML-Namenspräfix serialisiert, wie
Orcas Importer es erwartet.

| Befehl / Nachweis | Ergebnis |
| --- | --- |
| `.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_ghouls_grip*.py` | 26 Tests bestanden; Wand-/Dachhaut, 109 aktive Deckelstellungen, Journaleinführung, Deckelschlüssel-Einführung und ±5° Kraftschluss, Datums und gespeicherte Plate-Einstellungen |
| `.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_ghouls_grip_print_refresh.py -v` | nach finaler Bettkontakt-Korrektur erneut bestanden; Originaltransforms, Overrides, Plate-Zuordnung, unveränderte Payloads und Idempotenz |
| `.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_slice_support_usage.py -v` | 3 Tests bestanden; M82/M83/G92 und Rückstellungen |
| `.\.venv\Scripts\python.exe scripts\verify_ghouls_grip_mechanics.py` | Wandkorrektur PASS; 61 Scherenstellungen von 18° bis 78° inkl. 48°, alle korrigierten Kontaktpaare 0,000 mm³; Bestandsfehler separat |
| `powershell -File scripts\slice_ghouls_grip.ps1` | fünf G-Codes nach einzelplattenweiser Diagnose; abschließend gleiche Eingabe mit `orca-slicer.exe --slice=0 --outputdir=build\slice-all-fixed` ebenfalls Exit 0 und fünf G-Codes; das Skript verwendet wieder `--slice=0` |
| `.\.venv\Scripts\python.exe scripts\update_ghouls_grip_slice_metadata.py build\ghoul-final-slices\print --project models\ghouls-grip-print.3mf` | neue reale Kennzahlen gespeichert; Status weiter `not-verified` |
| `.\.venv\Scripts\python.exe scripts\render_3mf_previews.py models\ghouls-grip-view.3mf models\ghouls-grip-print.3mf` | beide finalen Standard-Sidecars aus den exakten 3MFs regeneriert |
| Renderbefehle oben und `.\.venv\Scripts\python.exe scripts\render_ghouls_grip_wall.py` | fünf neue Support-Sidecars, Supportübersicht und beleuchtetes Wanddetail |

**Keine Freigabe der gesamten Mechanik:** Die unveränderten Paare
`arm-0-False / chest (Bodenlager)` und `arm-1-False / chest (Bodenlager)`
überschneiden sich weiterhin. Gesamtvolumen: 496,131 mm³ bei 18°,
519,274 mm³ bei 48° und 554,635 mm³ bei 78°. Die Differenz zur Baseline
`f396e7a` ist in allen 61 geprüften Stellungen 0,000000 mm³.
Einzelpaarvolumina stehen in der
[Mechanik-Verifikation](ghouls-grip-mechanik-verifikation.md).
Arm-/Bodenlagerdatums bleiben auf Nutzeranweisung unverändert. Dafür ist eine
separate Reparaturentscheidung erforderlich; außerdem stehen PLA-Passungstest,
Journalspiel, kleine Zahnprofile und Belastbarkeit der Kragträger noch aus.

![Exakter Endstand, durchgehende Wand und innenliegender Deckelantrieb](images/ghouls-grip-continuous-wall.png)

## Ergebnisse des aktuellen Slices

| Plate | Inhalt | Schichten | Filament | davon Stützen | Zeit | Ansicht |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 – Schwarz | Schatulle und Deckel (2) | 649 | 338,50 g | 7,16 g (2,1 %) | 12 h 06 min 03 s | [Supportbild](images/ghouls-grip-print-plate-1-supports.png) |
| 2 – Knochenbeige | Unterarm, Handfläche und Finger (7) | 482 | 43,51 g | 5,90 g (13,6 %) | 3 h 04 min 12 s | [Supportbild](images/ghouls-grip-print-plate-2-supports.png) |
| 3 – Naturweiß | Mechanik-Hauptteile (11) | 492 | 112,23 g | 12,78 g (11,4 %) | 4 h 17 min 14 s | [Supportbild](images/ghouls-grip-print-plate-3-supports.png) |
| 4 – Naturweiß | Zahnräder und Verbinder (16) | 424 | 10,67 g | 0,54 g (5,1 %) | 1 h 01 min 26 s | [Supportbild](images/ghouls-grip-print-plate-4-supports.png) |
| 5 – Grau | Totenkopf-Auslöser (1) | 135 | 24,05 g | 3,40 g (14,1 %) | 1 h 11 min 05 s | [Supportbild](images/ghouls-grip-print-plate-5-supports.png) |
| **Gesamt** | **37 Druckobjekte / 5 Plates** | – | **528,96 g** | **29,78 g (5,6 %)** | **21 h 40 min 00 s** | [Übersicht](images/ghouls-grip-print-support-overview.png) |

| Farbgruppe | Zeit | Masse | Stützmaterial | Länge | Volumen | Plates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Schwarz | 43.563 s | 338,50 g | 7,16 g | 113.494,95 mm | 272.990 mm³ | 1 |
| Knochenbeige | 11.052 s | 43,51 g | 5,90 g | 14.587,15 mm | 35.090 mm³ | 1 |
| Naturweiß | 19.120 s | 122,90 g | 13,32 g | 41.203,95 mm | 99.100 mm³ | 2 |
| Grau | 4.265 s | 24,05 g | 3,40 g | 8.063,74 mm | 19.400 mm³ | 1 |
| **Gesamt** | **78.000 s** | **528,96 g** | **29,78 g** | **177.349,79 mm** | **426.580 mm³** | **5** |

Die Supportanteile werden aus positiven Extrusionen der Support-/Interface-
Bewegungen berechnet; `M82`, `M83` und `G92` werden berücksichtigt,
Extruder-only-Rückstellungen nicht als gedruckter Support gezählt.
Die vorherige absolute-E-Auswertung der relativen Orca-Extrusion war falsch.
Masse und Volumen werden mit dem jeweiligen Slice-Verhältnis umgerechnet:

| Plate | Supportlänge | Supportvolumen |
| --- | ---: | ---: |
| 1 | 2.400,96 mm | 5.775 mm³ |
| 2 | 1.977,14 mm | 4.756 mm³ |
| 3 | 4.285,33 mm | 10.307 mm³ |
| 4 | 180,25 mm | 433 mm³ |
| 5 | 1.140,98 mm | 2.745 mm³ |
| **Gesamt** | **9.984,66 mm** | **24.016 mm³** |

Die Summen und fünf Einzelergebnisse sind in `models/ghouls-grip-print.3mf`
als slicer-neutrale Metadaten gespeichert. Der Metadatenstatus bleibt
`not-verified`, bis Profilabweichungen und CLI-Diagnose geprüft sind.
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
- Finger: 2 Wände, 15 %, 30 mm/s Außenwand und reduzierte Beschleunigung für die 0,8-mm-PLA-Flexuren.
- Totenkopfknopf: 5 Wände, 40 %, Gesicht nach oben, damit keine Stützstruktur
  die skulptierte Fläche berührt.

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
  Fünf-Platten-Druckprojekt;
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

In der lokalen Copilot-Canvas-Erweiterung öffnet **Open in OrcaSlicer** die
exakt ausgewählte Workspace-3MF über einen lokalen POST-Endpunkt mit
Nonce-Prüfung und Pfadvalidierung. Der Button wird für STL, unsichere Pfade und
die öffentliche Web-SPA nicht als Desktop-Startweg angeboten.

## Behobene Probleme

1. 3MF-Build- und Komponenten-Transformationen sowie Orcas `plater_id` werden vom Canvas berücksichtigt; Objekte liegen nicht mehr übereinander.
2. Die interne Führung besitzt eine 1,8-mm-Außenabdeckung; außen bleibt die Kiste geschlossen.
3. Die naturweiße Mechanik ist kompakt auf zwei vollständige 250-mm-Platten
   verteilt; alle 25 Mechanikobjekte sind genau einmal zugeordnet.
4. Der frühere Hebel, Rastschieber, die Spule, Schlüssel, Bandanker, Seile, Gummibänder und Federn sind entfernt. Der graue Totenkopf dreht direkt die Ritzelwelle.
5. `scripts/render_ghouls_grip_print_projects.py` rendert alle fünf
   farbcodierten Plattenvorschauen direkt aus der aktuellen 3MF-Datei.
   Der Export platziert die Platten entsprechend dem OrcaSlicer-3-Spaltenraster;
   der Renderer löst dessen 300-mm-X- und -Y-Abstände für Einzelplattenbilder
   aus den tatsächlichen Plattenzuordnungen auf.

## Dateibelege

| Datei | SHA-256 |
| --- | --- |
| `ghouls-grip-view.3mf` | `687FE6888E0508B58957DA3004B6B71AE6FCFE25A05929F34A0A118B3231A28F` |
| `ghouls-grip-print.3mf` | `770BD97BD47C1F17CB70FB96AE29FC918638C7142442921230E31DBBA5BAAD74` |

## Physische Restrisiken

- Der direkte Totenkopf hat weniger mechanische Hebelwirkung als der verworfene lange Hebel. Passungen und Zahnflanken vor der Endmontage entgraten.
- Erfolgreiches Slicen und die kollisionsfreie Simulation ersetzen keinen realen Dauerlauf.
- Gedruckte Pins sowie PLA-Flexuren verschleißen. Hoch belastete Scherengelenke vorzugsweise mit M3×16-Schrauben sichern.
- Vor dem Komplettdruck bleiben Arm-/Pin-/Zahnrad-Passungscoupon und ein einzelner Finger-Testdruck empfohlen.
