# The Ghoul's Grip – OrcaSlicer-Druckvalidierung

Status: **GEOMETRY-OPTIMIZED / ORCASLICER RE-SLICE PENDING**

Geometrie-Optimierung: 2026-10-10

OrcaSlicer-Basisprofil: **2.4.3 GUI / 2.4.2 CLI zuvor verifiziert**

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

Die sechs Plattenwerte in der folgenden Tabelle gehören zur vorherigen, bereits
verifizierten Geometrie. Nach der aktuellen Deckel-Optimierung wurden alle
3MF-Projekte neu erzeugt; ihre Metadaten stehen deshalb korrekt auf
`status=not-verified`, bis die neue Orca-Slicer-Slice erneut erfolgreich
abgeschlossen ist. Die alten Zeit- und Massenwerte dürfen nicht als Werte der
optimierten Ausgabe interpretiert werden.

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

## Aktuelle Support-/Materialoptimierung

- Der Deckel besitzt jetzt selbsttragende, etwa 45° geneigte Dächer über den
  unteren Innenaussparungen statt der früheren großen horizontalen Decken.
- Der Deckel bleibt watertight/manifold: 23.816 Facetten, 206 × 129 × 27,5 mm.
- Die analytische Überhangprüfung meldet für den Deckel 746,68 mm²
  überhangkritische Fläche bei 45° (0,9 % der Gesamtfläche) und 16.110,24 mm²
  deckenartige Bridge-Fläche. Diese Bridge-Flächen müssen in OrcaSlicer mit
  der tatsächlichen Vorschau beurteilt werden; sie sind kein Ersatz für eine
  Slice-Messung.
- Das breite Chest-Skirt wurde bewusst nicht verändert: der getestete
  Frustum-Umbau destabilisiert die nachfolgenden Rail-/Service-Cut-Booleans.
  Dadurch bleiben die mechanischen Führungen und die sichtbare Außenform
  unverändert.
- Die aktualisierten farbigen Plattenvorschauen wurden aus den neuen 3MF-Szenen
  regeneriert. Sie zeigen die Material-/Farbgruppierung, nicht geslicte
  Supportvolumina.

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
| `ghouls-grip-master.3mf` | `2AF85EBB8BA3AA1859C0B1EDBD07CE3315C3161BA977F25A89033E5DF3FDCB83` |
| `ghouls-grip-master-retracted.3mf` | `97C242491AAF6A34D637542D732DB36A829888ADFFB6C09CE8CE4FB62B9ED21F` |
| `ghouls-grip-print-black-pla.3mf` | `2A188BAC57F24A18FBC8869E4F107A1ADABCB1AE00E005014E6E66AAFC961D0A` |
| `ghouls-grip-print-bone-pla.3mf` | `FB7BB84BE73051FFE32DA108DB5E8F1ECDEA3D9048D48C7174C553A3E88DEC9C` |
| `ghouls-grip-print-mechanism-pla.3mf` | `9FFF5F4D5813622608EB3C9AB7022D74F32EE0493C11ED7DED98F60098995945` |
| `ghouls-grip-print-accent-pla.3mf` | `D85BA298EAD99902B05911464E5C066046D7FAD21D2318CC95B9FFAFC53B00DC` |

## Physische Restrisiken

- Der direkte Totenkopf hat weniger mechanische Hebelwirkung als der verworfene lange Hebel. Passungen und Zahnflanken vor der Endmontage entgraten.
- Erfolgreiches Slicen und die kollisionsfreie Simulation ersetzen keinen realen Dauerlauf.
- Gedruckte Pins sowie PLA-Flexuren verschleißen. Hoch belastete Scherengelenke vorzugsweise mit M3×16-Schrauben sichern.
- Vor dem Komplettdruck bleiben Arm-/Pin-/Zahnrad-Passungscoupon und ein einzelner Finger-Testdruck empfohlen.
