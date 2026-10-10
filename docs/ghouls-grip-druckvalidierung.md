# The Ghoul's Grip – OrcaSlicer-Druckvalidierung

Status: **VERIFIED**

Validiert: 2026-10-10

OrcaSlicer: **2.4.2**

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

Alle sechs Platten wurden nacheinander mit der OrcaSlicer-CLI aus den gelieferten 3MF-Projekten gesliced. Es gibt keine Floating-region-, Out-of-bed-, Empty-layer- oder Invalid-toolpath-Warnung. Die gemessenen Gesamtwerte sind außerdem als `status=verified` in `Metadata/ghouls_grip_print_metadata.xml` der jeweiligen 3MF gespeichert.

Orca meldet ausschließlich den nicht blockierenden Profilhinweis, dass
`precise wall` bei der gespeicherten Wandreihenfolge ignoriert wird.

## Ergebnisse

| Projekt / Platte | Inhalt | Schichten | Filament | Zeit | Vorschau |
| --- | --- | ---: | ---: | ---: | --- |
| Schwarz, Platte 1 | Schatulle mit Dornenranken und Maßwerk | 490 | 282,33 g | 10 h 01 min 52 s | [PNG](images/ghouls-grip-slice-black-plate-1.png) |
| Schwarz, Platte 2 | Deckel mit Totenkopfkartusche und Fledermausflügeln | 137 | 173,63 g | 8 h 48 min 08 s | [PNG](images/ghouls-grip-slice-black-plate-2.png) |
| Knochenbeige | Unterarm, Handfläche, fünf Finger | 250 | 45,72 g | 3 h 27 min 40 s | [PNG](images/ghouls-grip-slice-bone.png) |
| Mechanik, Platte 1 | 4 Arme, Schlitten, Folgejoch, Hubjoch, Ritzel, Deckeltrieb, Scherenrad | 455 | 130,12 g | 6 h 20 min 47 s | [PNG](images/ghouls-grip-slice-mechanism-plate-1.png) |
| Mechanik, Platte 2 | 3 Zwischenräder, Ausgangszahnrad/D-Welle, 10 kleine und 4 große Pins | 215 | 13,56 g | 59 min 25 s | [PNG](images/ghouls-grip-slice-mechanism-plate-2.png) |
| Grau | Anatomischer Totenkopf-Drehknopf | 135 | 23,14 g | 1 h 22 min 13 s | [PNG](images/ghouls-grip-slice-accent.png) |
| **Gesamt** | **39 Druckobjekte** | – | **668,50 g** | **31 h 00 min 05 s** | – |

Projektmetadaten:

| Projekt | Zeit | Masse | Länge | Volumen | Platten |
| --- | ---: | ---: | ---: | ---: | ---: |
| Schwarz | 67.800 s | 455,96 g | 152.877,63 mm | 367.720 mm³ | 2 |
| Knochenbeige | 12.460 s | 45,72 g | 15.329,80 mm | 36.870 mm³ | 1 |
| Mechanik | 26.412 s | 143,68 g | 48.171,67 mm | 115.860 mm³ | 2 |
| Grau | 4.933 s | 23,14 g | 7.759,25 mm | 18.660 mm³ | 1 |

Das schwarze Projekt benötigt 455,96 g statt der ursprünglichen 629,66 g. Einsparung: **173,70 g / 27,6 %**. Die sichtbare Außenseite bleibt geschlossen; die Schlittenführung erzeugt keinen äußeren Schlitz.

## Stützen und Objekt-Overrides

- Schatulle/Deckel: 3 Wände, 10 % Gyroid, Baumstützen nur an kritischen Regionen.
- Mechanik: 5–6 Wände, 40–100 % Infill; Arme, Zahnräder und Pins verstärkt. Normale Stützen sind nur für Plattform, Schlitten, beide Deckelzahnstangen und das lange Ausgangszahnrad/D-Wellen-Teil aktiviert.
- Hand/Knochen: 4 Wände, 25 %; organische Überhänge mit bettgebundenen Baumstützen.
- Finger: 2 Wände, 15 %, 30 mm/s Außenwand und reduzierte Beschleunigung für die 0,8-mm-PLA-Flexuren.
- Totenkopfknopf: 5 Wände, 40 %, supportfrei in der gespeicherten Druckorientierung.

## Behobene Probleme

1. 3MF-Build- und Komponenten-Transformationen sowie Orcas `plater_id` werden vom Canvas berücksichtigt; Objekte liegen nicht mehr übereinander.
2. Die interne Führung besitzt eine 1,8-mm-Außenabdeckung; außen bleibt die Kiste geschlossen.
3. Die Mechanikplatte wurde kompakt in zwei vollständige 250-mm-Platten gepackt. Alle 29 naturweißen Mechanikobjekte sind genau einmal zugeordnet.
4. Der frühere Hebel, Rastschieber, die Spule, Schlüssel, Bandanker, Seile, Gummibänder und Federn sind entfernt. Der graue Totenkopf dreht direkt die Ritzelwelle.
5. `scripts/render_ghouls_grip_print_projects.py` rendert die sechs
   farbcodierten Plattenvorschauen direkt aus den ausgelieferten 3MF-Szenen.
   Der im Export verwendete Plattenabstand von 300 mm wird dabei wieder in
   einzelne Druckplatten aufgelöst.

## Dateibelege

| Datei | SHA-256 |
| --- | --- |
| `ghouls-grip-master.3mf` | `51E7C08BA66DB753E608C5E5264311BE46782A400BDB2075F1F3EE42DAB4D0A7` |
| `ghouls-grip-master-retracted.3mf` | `1B3D3C249DD2893EEE3DC91CA095FEE2B9A9E6B40F0EFF17DD97042706F09075` |
| `ghouls-grip-print-black-pla.3mf` | `B6D6FAFE4C3E9980A15CD25D82E8E1DF9DE1BBD1BB7174E42F5783DC05FAA82D` |
| `ghouls-grip-print-bone-pla.3mf` | `E37FC2C033782C3D40C5ED8940B1B26C3A7EED51FA02BBFDB5E8D3A20483D53A` |
| `ghouls-grip-print-mechanism-pla.3mf` | `77545800B2750EA38774C2CBD3600FCB9038ED26417E8FBF086B0AD4932D2E3D` |
| `ghouls-grip-print-accent-pla.3mf` | `C75592C220E6788219B585999AA98F7D4F5A0F136EF153B314B61CC6E886D12B` |

## Physische Restrisiken

- Der direkte Totenkopf hat weniger mechanische Hebelwirkung als der verworfene lange Hebel. Passungen und Zahnflanken vor der Endmontage entgraten.
- Erfolgreiches Slicen und die kollisionsfreie Simulation ersetzen keinen realen Dauerlauf.
- Gedruckte Pins sowie PLA-Flexuren verschleißen. Hoch belastete Scherengelenke vorzugsweise mit M3×16-Schrauben sichern.
- Vor dem Komplettdruck bleiben Arm-/Pin-/Zahnrad-Passungscoupon und ein einzelner Finger-Testdruck empfohlen.
