# The Ghoul's Grip - Maße, Bauanleitung und Sicherheitskonzept

![Ausgefahren](images/ghouls-grip-deployed.png)
![Eingefahren](images/ghouls-grip-retracted.png)

## Status und Konstruktionsweg

Parametrischer Funktionsprototyp, kein getestetes Kinderspielzeug. Jedes Teil
entsteht aus einem Skript in `scripts/`; die STL-Dateien unter `models/` sind
reine Ausgaben und werden nie von Hand bearbeitet.

| Baugruppe | Skript |
| --- | --- |
| Gotische Schatulle und Deckel | `scripts/gothic_chest.py` |
| Hubwerk, Klinke, Kurbel, Unterarm | `scripts/mechanism.py` |
| Totenkopf und Totenkopf-Auslöser | `scripts/skull.py` |
| Skeletthand | `scripts/skeleton_hand.py` (+ `extract_hand_bones.py`) |
| Zusammenbau, Validierung, 3MF | `scripts/ghouls_grip.py` |
| Montage-Renderings | `scripts/render_ghouls_grip.py` |

Die Skeletthand ist **kein Freihandmodell**: Die 27 Handknochen stammen aus
einem anatomischen CT-Datensatz (siehe Abschnitt *Lizenz*), werden automatisch
geclustert, klassifiziert, in einen kanonischen Frame gedreht, dezimiert und
dann zu druckbaren Teilen verschmolzen.

Die beiden KI-Konzeptbilder unter `model-sources/ghouls-grip/` liefern nur Stil
und Bewegungsablauf. Die Bemaßungen im Blueprint-Bild (396/377/330/255 mm)
widersprechen der Aufgabenbeschreibung und wurden nicht verwendet.

## Maßvertrag

| Merkmal | Wert | Herkunft | Sicherheit |
| --- | ---: | --- | --- |
| Außenmaß geschlossen | 200 × 120 × 110 mm | Benutzerangabe | hoch |
| Grundkörper (ohne Dekor) | 200 × 120 × 86 mm | abgeleitet | hoch |
| Grundkörper mit Dekor/Scharnier | 210,5 × 130,8 × 98 mm | am Mesh gemessen | hoch |
| Deckel | 209 × 126 × 27,5 mm | am Mesh gemessen | hoch |
| Wand/Boden | 3,0 mm | Benutzerangabe | hoch |
| Innenraum | 194 × 114 × 80 mm | Benutzerangabe | hoch |
| Scherenarm | 90 mm Pivotabstand, 12 × 4 mm | Benutzerangabe | hoch |
| Scherenbohrung | 3,2 mm | Benutzerangabe | hoch |
| Sehnenkanal | 2,0 mm | Benutzerangabe | hoch |
| Flexursteg | 0,8 mm | Benutzerangabe | mittel; nur TPU |
| Gleitpassung `FIT` | 0,40 mm | Druckerprofil-Basiswert | mittel |
| Handfläche | **67,3 × 94,2 × 25,2 mm** | anatomisch, siehe unten | hoch |

### Abweichung: Handfläche

Vorgegeben waren 50 × 45 mm. Eine echte Mittelhand mit acht Handwurzelknochen
und fünf Mittelhandknochen lässt sich darauf nicht abbilden, ohne dass das Teil
wie ein Brett statt wie ein Skelett aussieht. Die Hand läuft deshalb mit
`HAND_SCALE = 0,72` (ca. 72 % einer erwachsenen Hand) und wird 67 × 94 mm.
Das passt weiterhin in den 194 × 114 mm großen Innenraum.

### Abweichung: Hubweg

Vorgegeben waren "ca. 160 mm über den Schatullenrand". Die Schere selbst hebt
die Schale um **62,5 mm** (eingefahren 24,8 mm, ausgefahren 87,3 mm
Scherenhöhe); die Schalenoberkante steht dann 23 mm über dem Rand. Zusammen mit
Unterarm und Hand erreichen die Fingerspitzen **289 mm über der Aufstellfläche**
und damit **188 mm über der geschlossenen Deckeloberkante** - der geforderte
Effekt wird also übertroffen.

## Kinematik (maßgeblich für jede Änderung)

- Armlänge L = 90 mm, Mittelpivot bei 45 mm.
- Fester Bodendrehpunkt: **x = -22 mm, z = 8 mm**, zwei Scherenpaare bei
  y = ±26 mm.
- Eingefahren θ = 16° → Hub 24,8 mm; ausgefahren θ = 76° → Hub 87,3 mm.
- Schlittenweg x = +64,5 → -0,2 mm (64,7 mm Weg) in Nut-Schienen
  4 (Z) × 3 (Y) mm auf z = 8 mm.
- Schale 104 × 104 mm, Ursprung x = +20 mm; Pin-Auge lokal x = -42 mm,
  Kulisse lokal -25 … +45 mm.
- Unterarm-Scharnier auf der Schale: lokal (14, ±11, 16) mm. Eingefahren klappt
  der Unterarm um 104° nach -X; dann liegt die gesamte Hand unter der
  Deckeloberkante (geprüfter Höchstpunkt 101,5 mm = Deckeloberkante).
- Deckelscharnier: Achse **z = 93 mm, x = -101 mm**, 1,75-mm-Filamentstift,
  Öffnungswinkel im Modell 108°.
- Totenkopf-Auslöser mittig auf der Front: (0, -60, 46) mm, Ø4,4-Stiftbohrung.
  Sein Zapfen trifft den Klinkenrocker bei z = 46 mm, der Haken gibt den
  Schlitten bei z = 8…14 mm frei.
- Kurbelbohrung Ø6,4 mm in der Rückwand bei (-100, 0, 30) mm.

## Sicherheitskonzept

- Die Hand ist eine **kraftbegrenzte Greifbewegung**, keine Schnappfalle. Die
  Finger werden von einer Sehne gezogen und schließen sich um Süßigkeiten,
  ohne um Finger zuzuschnappen.
- Zwei Haushaltsgummibänder treiben nur den Hub an. Mit **einem** Band je Seite
  beginnen und die Vorspannung erst nach einem Leerlauftest erhöhen.
- Der Deckel braucht ein Fangband auf höchstens 108° Öffnungswinkel.
- Alle Quetschstellen der Schere bleiben im Gehäuse.
- Nicht unbeaufsichtigt an Kinder geben, nicht auf Gesicht oder Augen richten.

## Stückliste (20 Druckteile, alle wasserdicht validiert)

| Datei | Anzahl | Maße (mm) | Material |
| --- | ---: | --- | --- |
| `chest.stl` | 1 | 210,5 × 130,8 × 98,0 | PLA/PETG schwarz |
| `lid.stl` | 1 | 209,0 × 126,0 × 27,5 | PLA/PETG schwarz |
| `scissor-arm.stl` | 4 | 102 × 12 × 4 | PETG |
| `slider.stl` | 1 | 44 × 119,2 × 26 | PETG |
| `platform.stl` | 1 | 104 × 104 × 45 | PETG |
| `latch-rocker.stl` | 1 | 5 × 31,5 × 45 | PETG |
| `latch-bracket.stl` | 1 | 40 × 16 × 32,5 | PETG |
| `crank.stl` | 1 | 52 × 28 × 47,7 | PETG |
| `band-anchor.stl` | 1 | 14 × 96 × 25,5 | PETG |
| `forearm.stl` | 1 | 25,8 × 18 × 50 | PLA knochenfarben |
| `pivot-pin-3.stl` | 8 | Ø6,2 × 26 | PETG |
| `pivot-pin-4.stl` | 4 | Ø7,2 × 34 | PETG |
| `skull-trigger.stl` | 1 | 42,2 × 47,9 × 40 | PLA grau |
| `hand-palm.stl` | 1 | 67,3 × 94,2 × 25,2 | PLA knochenfarben |
| `hand-tendon-guide.stl` | 1 | 62,0 × 77,4 × 25,0 | PLA knochenfarben |
| `hand-finger-thumb.stl` | 1 | 21,3 × 43,0 × 11,5 | TPU 95A |
| `hand-finger-index.stl` | 1 | 18,0 × 64,6 × 11,2 | TPU 95A |
| `hand-finger-middle.stl` | 1 | 12,2 × 73,8 × 11,0 | TPU 95A |
| `hand-finger-ring.stl` | 1 | 16,3 × 69,9 × 10,5 | TPU 95A |
| `hand-finger-little.stl` | 1 | 20,4 × 53,5 × 9,2 | TPU 95A |

Zusätzlich: `models/ghouls-grip.3mf` (Materialtrennung für OrcaSlicer) und
`models/ghouls-grip-preview.stl` (Vorschau für das STL-Canvas).

Nicht gedruckt: 2 × Haushaltsgummiband ca. 60 mm, ca. 1 m 0,8-mm-Angelsehne,
1,75-mm-Filament als Scharnierachse. Für hoch belastete Scherengelenke sind
M3×16-Schrauben mit selbstsichernden Muttern besser als die gedruckten Stifte.

## Empfohlene Druckeinstellungen

| Teil | Material | Wände/Infill |
| --- | --- | --- |
| Gehäuse/Deckel | PLA oder PETG | 4 Wände, 20-25 % Gyroid |
| Schere/Schlitten/Klinke/Schale | PETG | 5 Wände, 40 % Gyroid |
| Finger | TPU 95A | 2-3 Wände, 15 % Gyroid |
| Hand, Unterarm, Totenkopf | PLA | 4 Wände, 25 % Gyroid |

Schichthöhe 0,20 mm, 0,4-mm-Düse. `XY Hole Compensation` +0,10 mm.
`XY Contour Compensation` -0,05 mm nur an Gleitflächen, nicht am Dekor.
Elefantenfuß-Kompensation 0,15-0,20 mm. Reliefs und Nieten der Schatulle sind
2,6-3,0 mm erhaben und brauchen keine Stützen; der Deckel druckt flach mit der
Oberseite nach unten.

## Montage

1. Je zwei Scherenarme zu einem X-Paar verbinden (Mittelbohrung, `pivot-pin-3`).
   Zwei solche Paare bauen.
2. Untere Festpunkte auf die Pivotposten im Boden bei (-22, ±26) stecken; die
   Gegenenden in die Nut-Schienen des Schlittens.
3. Schlitten einsetzen und von Hand über den vollen Weg (x = +64,5 → -0,2)
   durchfahren. Gleitflächen trocken mit PTFE-Pulver behandeln, kein Fett.
4. Schale aufsetzen: festes Auge auf den einen Scherenkopf, zweiter Kopf in die
   Kulisse. Die Schale muss über den ganzen Hub waagerecht bleiben.
5. `latch-bracket` auf die beiden Sockellöcher bei (±14, -40) setzen,
   `latch-rocker` einhängen. Totenkopf-Auslöser von außen durch die Front
   stecken; sein Zapfen muss den Rocker sauber treffen.
6. `band-anchor` auf die Sockellöcher bei (-76, ±34) setzen und je ein
   Gummiband symmetrisch zum Schlitten spannen. Mit minimaler Vorspannung
   beginnen.
7. Kurbel von hinten durch die Ø6,4-Bohrung bei (-100, 0, 30) stecken; damit
   wird der Schlitten gegen die Bänder zurückgezogen, bis die Klinke einrastet.
8. Unterarm in die Scharnierohren der Schale hängen, Sehnenführungsplatte und
   Handfläche auf den Spigot stecken, die fünf TPU-Finger in die Zapfen der
   Handfläche drücken.
9. Angelsehne von jeder Fingerspitze durch die Führungsplatte zum hinteren
   Schnurauge der Schale führen. Länge so einstellen, dass die Finger erst im
   letzten Drittel des Hubs schließen - und nur so fest, dass sie Süßigkeiten
   **stützen**, nicht klemmen.
10. Deckel mit 1,75-mm-Filament auf der Achse z = 93 mm montieren, Fangband
    einhängen.
11. Leerlauftest: zehn Auslösungen ohne Süßigkeiten, danach Pins, Flexuren und
    Klinke auf Risse prüfen.

## OrcaSlicer-Ablauf

1. `models/ghouls-grip.3mf` öffnen und die Materialien den ACE-Pro-Slots
   zuordnen (schwarz, knochenfarben, grau, TPU).
2. Die Baugruppe dient nur der Kontrolle. Zum Drucken die Einzel-STLs
   materialweise auf getrennte Platten laden.
3. Gehäuse und Deckel flach auflegen, Scherenarme flach, Bohrungen ohne Stützen.
4. TPU-Finger flach drucken, keine adaptive Schichthöhe an den Flexurstegen,
   dort `Height Range Modifier` auf 1 Wandlinie.
5. Vor dem Gesamtdruck einen Arm, einen Pin und ein Fingerglied als
   Passungsmuster slicen.

## Offene Testdruck-Risiken

- Die Gummibandlänge von ca. 60 mm ist nur das ungespannte Kaufmaß;
  Vorspannung und Hebelarm müssen am Prototyp ermittelt werden.
- Die Sehnensteuerung ist geometrisch vorbereitet, aber der Auslösepunkt der
  Fingerbeugung ist nicht formschlüssig erzwungen, sondern über die Sehnenlänge
  eingestellt.
- Die 0,8-mm-Flexurstege sind die Schwachstelle der Hand. In PLA brechen sie;
  TPU 95A ist Pflicht.
- Gedruckte Pins in PETG sind für Dauerbetrieb grenzwertig. Bei Rissen auf
  M3-Schrauben wechseln.

## Lizenz der Knochengeometrie

Die 27 Handknochen stammen aus **"Wrist Bones Full Hand - Human Skeleton"**,
NIH 3D Print Exchange, Modell `3DPX-016815`, hochgeladen von *My Segmenter*
(mysegmenter.com), lizenziert unter **CC BY**.

Im Repository liegt nur der abgeleitete, klassifizierte und dezimierte Datensatz
`model-sources/ghouls-grip/reference/hand_bones.npz`. Die 12 MB große
Original-STL wird von `scripts/extract_hand_bones.py` bei Bedarf neu geladen und
nicht eingecheckt. Bei Weitergabe der Modelle muss die CC-BY-Nennung erhalten
bleiben.
