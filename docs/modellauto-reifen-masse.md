# Modellauto-Ersatzreifen – Maße

## Abschluss / Archiv

Vom Benutzer am 2026-10-11 als fertig gemeldet und zur Archivierung freigegeben.
Generator, STL, Druckprojekt, Praesentationsrender und Referenzindex bleiben
unter den unten genannten Pfaden im Repository erhalten.
Das nachtraeglich vom Benutzer gespeicherte 3MF ist die archivierte Projektfassung.
Seine Meshdaten und die unten aufgefuehrten Druckprofile sind gegenueber dem
urspruenglich gesliceten OrcaSlicer-Projekt unveraendert; die gespeicherte
Projektfassung selbst enthaelt keine vollstaendigen Slice-Ergebnisse.
Die Zeit- und Materialangaben unten stammen daher vom urspruenglichen Slice.
Eine konkrete Passungs- oder Gripbewertung wurde nicht mitgeteilt.

Referenzindex: `model-sources/archiv/modellauto-reifen-referenzfotos-index.png`
(Kacheln siehe `model-sources/archiv/README.md`).

| Merkmal | Maß | Herkunft | Konfidenz |
| --- | ---: | --- | --- |
| Reifen-Außendurchmesser | 37,20 mm | Benutzermessung am intakten Reifen, 2026-10-10 | Hoch |
| Reifenbreite | 26,00 mm | Benutzermessung am intakten Reifen | Hoch |
| Rippenkranz der Felge, Außen-Ø (Reifensitz) | 33,74 mm | Schieblehre, Kachel 04 | Hoch |
| Vorderer Felgenring, Außen-Ø | 22,54 mm | Schieblehre, Kachel 02 | Hoch |
| Felgenbreite axial | 23,20 mm | Schieblehre, Kachel 00 | Hoch |
| Umlaufender Ring im Rippenkranz, Breite | 2,29 mm | Schieblehre, Kachel 05 (nicht modelliert) | Hoch |
| Wandstärke Originalreifen | 2,05 mm | Schieblehre am Bruchstück, Kachel 01 | Hoch |
| Passungsspiel Sitz (Ø) | 0,20 mm | Konstruktive Wahl: Presspassung nach Druckerprofil | Mittel – Testdruck |
| Innen-Ø Reifensitz | 33,94 mm | Abgeleitet: 33,74 + 0,20 | Mittel |
| Lauffläche radial | 1,63 mm | Abgeleitet: (37,20 − 33,94) / 2 | Hoch |
| Lippen-Öffnung vorn | 23,00 mm | Abgeleitet: 22,54 + ≈0,45 Spiel | Mittel |
| Lippenstärke vorn | 1,40 mm | Abgeleitet: (26,0 − 23,2) / 2, wie Original-Seitenwand | Mittel |

## Konstruktion

PLA ist starr und darf nicht geklebt werden (Benutzerwunsch). Der Reifen ist
deshalb eine Hülse mit vorderer Lippe: Er wird von der Achsseite auf den
Rippenkranz geschoben, bis die Lippe an der Felgenfront anliegt. Er hält per
Presssitz. Die Rückseite ist offen (Einführfase innen).

Druck: Lippe/Stirnseite auf dem Bett, keine Stützen. Sitzt der Reifen zu locker,
`FIT_CLEAR` auf 0,10 mm senken; klemmt er, auf 0,30 mm erhöhen.

## Ausgaben und Slice

- `models/modellauto-reifen.stl` (Generator: `scripts/modellauto_reifen.py`)
- `models/modellauto-reifen-print.3mf` (OrcaSlicer-Druckprojekt)
- Render: `docs/images/modellauto-reifen-render.png`

OrcaSlicer 2.4.2, Drucker `Anycubic Kobra S1 0.4 nozzle`, Prozess
`0.20mm Standard @Anycubic Kobra S1 0.4 nozzle`, Filament
`Anycubic PLA @Anycubic Kobra S1 0.4 nozzle`: Slice erfolgreich, 20 min 3 s,
6,28 g / 2,11 m PLA, keine Stützen, 2 Wände, 15 % Infill.

Asset-Recherche: Generischer Rotationskörper (Hülse mit Lippe) ohne
fahrzeugspezifische Form; eigene Konstruktion aus Messwerten, keine Fremdlizenz.
