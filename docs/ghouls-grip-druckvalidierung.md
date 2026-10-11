# The Ghoul's Grip – OrcaSlicer-Druckvalidierung

Status: **VERIFIED**

Geometrie-Optimierung: 2026-10-10

OrcaSlicer-Basisprofil: **2.4.3 GUI / 2.4.2 CLI**

![Übersicht](images/ghouls-grip-slice-overview.png)

## Profilvertrag

- Drucker: `Anycubic Kobra S1 0.4 nozzle`
- Düse/Schicht: 0,4 mm / 0,20 mm
- Prozess: `0.20mm Standard @Anycubic Kobra S1 0.4 nozzle`
- Filament: `Anycubic PLA @Anycubic Kobra S1 0.4 nozzle`
- Bett: `Textured PEI Plate`
- Starttemperaturen: 55/215 °C
- Eine reale Spule/Farbe je Projekt, kein Prime Tower
- Farben: Schwarz `#202124`, Knochenbeige `#D8C6A5`, Naturweiß `#F1EBDD`, Grau `#777777`

Alle sechs Druckplatten wurden nach der Geometrie- und Orientierungsoptimierung
neu gesliced. Die Werte stammen aus den finalen G-Codes; die vier ausgelieferten
Material-3MFs enthalten dieselben Summen mit `status=verified`.

Orca meldet ausschließlich den nicht blockierenden Profilhinweis, dass
`precise wall` bei der gespeicherten Wandreihenfolge ignoriert wird.

## Ergebnisse

| Projekt / Platte | Inhalt | Schichten | Filament | davon Stützen | Zeit | Vorschau |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Schwarz, Platte 1 | Leichtbau-Schatulle stehend mit organisch skulptierten Kreaturenreliefs | 490 | 196,55 g | 0,33 g (0,2 %) | 8 h 15 min 57 s | [PNG](images/ghouls-grip-slice-black-plate-1.png) |
| Schwarz, Platte 2 | Gerippter Deckel auf seiner Hinterkante stehend | 645 | 132,82 g | 15,69 g (11,8 %) | 5 h 29 min 29 s | [PNG](images/ghouls-grip-slice-black-plate-2.png) |
| Knochenbeige | Unterarm, Handfläche hochkant, fünf Finger | 482 | 42,82 g | 12,51 g (29,2 %) | 3 h 12 min 04 s | [PNG](images/ghouls-grip-slice-bone.png) |
| Mechanik, Platte 1 | 4 gelochte Arme, offener Schlitten/Plattformrahmen, Zahnstangen und Speichenritzel | 464 | 111,88 g | 15,44 g (13,8 %) | 5 h 25 min 27 s | [PNG](images/ghouls-grip-slice-mechanism-plate-1.png) |
| Mechanik, Platte 2 | 3 Zwischenräder, Ausgangszahnrad/D-Welle, Pins und Splinte | 177 | 10,88 g | 1,24 g (11,4 %) | 0 h 52 min 46 s | [PNG](images/ghouls-grip-slice-mechanism-plate-2.png) |
| Grau | Anatomischer Totenkopf-Drehknopf, Gesicht nach oben | 135 | 20,30 g | 8,21 g (40,4 %) | 1 h 16 min 03 s | [PNG](images/ghouls-grip-slice-accent.png) |
| **Gesamt** | **39 Druckobjekte / 6 Platten** | – | **515,25 g** | **53,42 g (10,4 %)** | **24 h 31 min 46 s** | – |

Projektmetadaten (`status=verified` in den ausgelieferten 3MF-Dateien):

| Projekt | Zeit | Masse | Stützmaterial | Länge | Volumen | Platten |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Schwarz | 49.526 s | 329,37 g | 16,02 g | 110.432,98 mm | 265.620 mm³ | 2 |
| Knochenbeige | 11.524 s | 42,82 g | 12,51 g | 14.356,12 mm | 34.530 mm³ | 1 |
| Mechanik | 22.693 s | 122,76 g | 16,69 g | 41.157,86 mm | 99.000 mm³ | 2 |
| Grau | 4.563 s | 20,30 g | 8,21 g | 6.805,82 mm | 16.370 mm³ | 1 |

### Orientierungsoptimierung (gemessen, nicht geschätzt)

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

Gegenüber dem zuvor verifizierten Stand (528,22 g / 138,60 g Support) sinkt der
Stützbedarf um **85,18 g / 61,5 %** und die Gesamtmasse um 12,97 g, allein durch
gemessene Orientierungswechsel – die Geometrie wurde dafür nicht verändert.
Gegenüber dem ursprünglichen 629,66-g-Entwurf beträgt die Materialeinsparung
**114,41 g / 18,2 %**, gegenüber der Vor-Leichtbau-Schatulle (455,96 g schwarz)
**126,59 g / 27,8 %**.

Wichtig: Kein Projekt wird als „supportfrei“ bezeichnet. In allen vier Projekten
sind Baumstützen (`tree(auto)`, 30°-Schwelle, bettgebunden) aktiv. Die
angegebenen Stützmengen stammen aus den `;TYPE:Support`- und
`;TYPE:Support interface`-Extrusionswegen des G-Codes, skaliert mit dessen
Gesamtmasse/-länge.

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

## Aktuelle Support-/Materialoptimierung

- Der Deckel besitzt eine 2,4-mm-Deckhaut, offene Unterseiten-Träger,
  fünf gerippte Längstraversen und fünf kurze hintere Anschlagpads statt eines
  massiven, 193 mm breiten Querriegels. Er steht auf seiner Hinterkante: in
  dieser Lage ist weder die hohle Innendecke noch das skulptierte Kartuschen-
  relief ein großer Überhang (4.598,9 statt 20.336,1 Stütz-E).
- Schatulle und Deckel liegen auf zwei getrennten Platten desselben schwarzen
  Projekts, weil der stehende Deckel 129 mm hoch baut.
- Der Sockel und der obere Kranz der Schatulle wurden von horizontalen Stufen
  auf zwei geneigte, selbsttragende Kurse umgebaut. Die Pilasterkapitelle und
  die Unterseiten der Scharnierlager sind ebenfalls geneigt.
- Die dekorative Schatullenwand und der Boden sind 2,0 mm stark; die
  3,0-mm-Funktionsdatums an Schienen, Lagern und Führungen bleiben erhalten.
  Gerundete Außenkanten sowie vertiefte statt aufgesetzte Reliefs wirken
  organischer und vermeiden zusätzliche massive Zierkörper.
- Das Schatullen-Volumen sank von 295.062 auf 184.056 mm³
  (**−37,6 %**), das Deckelvolumen von 252.068 auf 124.903 mm³
  (**−50,5 %**). Zusammen sind das **−43,5 % Modellvolumen**.
- Acht überarbeitete Mechanikteile sanken durch offene Rahmen, Fenster und
  Speichen von 118.567 auf 82.649 mm³ (**−30,3 %**).
- Der Deckel bleibt ein einzelner watertight/manifold Körper:
  27.116 Facetten, 206 × 129 × 25,6 mm (24,0 mm Grundkörper plus 1,6 mm
  skulptiertes Kartuschenrelief).
- Die Schienen- und Lagerbooleans werden zuerst in der bewährten Kernschale
  erzeugt; die geneigten Zierkurse werden danach kontrolliert angefügt. Dadurch
  bleiben die mechanischen Führungen geschlossen und manifold.
- Die aktualisierten farbigen Plattenvorschauen wurden aus den neuen 3MF-Szenen
  regeneriert. Sie zeigen die Material-/Farbgruppierung, nicht geslicte
  Supportvolumina.

## Behobene Probleme

1. 3MF-Build- und Komponenten-Transformationen sowie Orcas `plater_id` werden vom Canvas berücksichtigt; Objekte liegen nicht mehr übereinander.
2. Die interne Führung besitzt eine 1,8-mm-Außenabdeckung; außen bleibt die Kiste geschlossen.
3. Die Mechanikplatte wurde kompakt in zwei vollständige 250-mm-Platten gepackt. Alle 29 naturweißen Mechanikobjekte sind genau einmal zugeordnet.
4. Der frühere Hebel, Rastschieber, die Spule, Schlüssel, Bandanker, Seile, Gummibänder und Federn sind entfernt. Der graue Totenkopf dreht direkt die Ritzelwelle.
5. `scripts/render_ghouls_grip_print_projects.py` rendert die fünf
   farbcodierten Plattenvorschauen direkt aus den ausgelieferten 3MF-Szenen.
   Der im Export verwendete Plattenabstand von 300 mm wird dabei wieder in
   einzelne Druckplatten aufgelöst.

## Dateibelege

| Datei | SHA-256 |
| --- | --- |
| `ghouls-grip-master.3mf` | `8BDA068705130408D9A91B6AABF8AF1AE575472CB5A1F3AD9F74C0815C7B76B5` |
| `ghouls-grip-master-retracted.3mf` | `905067CECDFA3E5DDB6CF00E15F4CD3330636D0CF336590BA7260929F32776F1` |
| `ghouls-grip-print-black-pla.3mf` | `5DBD4F49BDE80D10FDCAA41947862FD63827E318532E97D2FD8395489BA2DAF5` |
| `ghouls-grip-print-bone-pla.3mf` | `95E424893539C2F9D2AAD413214473E2F68BB06D82E800A66842C6821ECF8613` |
| `ghouls-grip-print-mechanism-pla.3mf` | `51478FAC1719AB7FB046616012DFEC29D6075A15809737D38AE457578064CDA0` |
| `ghouls-grip-print-accent-pla.3mf` | `03556A2356C72CEAB3E4491530B20DEA5D7E58D42DE23F058FDB7C8B8496FD49` |

## Physische Restrisiken

- Der direkte Totenkopf hat weniger mechanische Hebelwirkung als der verworfene lange Hebel. Passungen und Zahnflanken vor der Endmontage entgraten.
- Erfolgreiches Slicen und die kollisionsfreie Simulation ersetzen keinen realen Dauerlauf.
- Gedruckte Pins sowie PLA-Flexuren verschleißen. Hoch belastete Scherengelenke vorzugsweise mit M3×16-Schrauben sichern.
- Vor dem Komplettdruck bleiben Arm-/Pin-/Zahnrad-Passungscoupon und ein einzelner Finger-Testdruck empfohlen.
