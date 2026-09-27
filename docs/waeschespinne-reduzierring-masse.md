# Wäschespinne-Reduzierring – Maße

| Merkmal | Maß | Herkunft | Konfidenz |
| --- | ---: | --- | --- |
| Eindrehhülse, Innendurchmesser | 60,00 mm | Benutzerbestätigte Messung, 2026-09-27 (ersetzt 53/60,48 mm) | Hoch |
| Wäschespinnenmast, Außendurchmesser | 50,20 mm | Benutzerbestätigte Messung, 2026-09-27 (ersetzt 43/43,04 mm) | Hoch |
| Einstecktiefe | 50,00 mm | Benutzerangabe | Hoch |
| Kragen, Außendurchmesser | 70,00 mm | Benutzerentscheidung | Hoch |
| Kragenhöhe | 3,00 mm | Benutzerentscheidung | Hoch |
| Gesamthöhe | 53,00 mm | Abgeleitet: 50,00 + 3,00 mm | Hoch |
| Passung | 0,40 mm Durchmesserspiel an beiden Kontaktflächen | Konstruktive Wahl: ASA-Gleitpassung nach Druckerprofil | Mittel |
| Ringaußendurchmesser | 59,60 mm | Abgeleitet: 60,00 − 0,40 mm | Hoch |
| Ringinnendurchmesser | 50,60 mm | Abgeleitet: 50,20 + 0,40 mm | Hoch |
| Radiale Wandstärke | 4,50 mm | Abgeleitet aus Außen- und Innendurchmesser | Hoch |
| Einführfase außen | 1,00 mm am hülsenseitigen Ende | Konstruktive, nicht fit-kritische Wahl | Mittel |
| Einlaufrundung innen | Radius 1,00 mm an der mastseitigen Kragenfläche | Benutzerwunsch, rot markierte Kante im Referenzbild | Hoch |

## Befund zum ersten Druck

Die Maße 2026-09-27 ersetzen alle früheren Werte. Der Benutzer hat am Bauteil
**50,20 mm Mast-Außendurchmesser** und **60,00 mm Hülsen-Innendurchmesser**
bestätigt. Frühere Werte (43,00/43,04 mm Mast, 53,00/60,48 mm Hülse) stammten aus
Fotoablesungen und sind ungültig.

Die Kacheln 02 und 03 zeigen den schwarzen Fehldruck. Die abgelesenen Maße
35,85 mm und 52,11 mm werden nicht als Bauteilmaße verwendet. Beim erneuten Druck
muss die Slicer-Skalierung auf 100 % stehen.

## Einbaurichtung

Der Kragen (70 mm Außendurchmesser) liegt auf der Oberkante der 60-mm-Hülse auf
und verhindert, dass der Ring hineinrutscht. Der 50-mm-Zylinder zeigt in die
Hülse; der 50,20-mm-Mast wird von der Kragenseite durch die innenliegende
Einlaufrundung (R1) eingeschoben.

## Druckvorgabe

Material: ASA. Der Ring ist ein lasttragendes Funktionsteil, einfarbig und wird als
ASCII-STL erzeugt. Druck auf einer Stirnseite, mit mindestens fünf Perimetern und
**50 % Füllung im Slicer; nicht mit 100 % massiv drucken.** Empfohlen ist ein
rectilineares oder gyroides Füllmuster. Den Kragen auf dem Druckbett ausrichten. Nach dem Druck
das Teil umdrehen: Der lange Zylinder wird in die Hülse eingesetzt, der Kragen bleibt
oben auf der Hülsenkante und der Mast wird durch den Kragen eingeschoben. Die
Geometrie enthält keine unterstützungspflichtigen Überhänge.

Vor dem vollständigen Neudruck empfiehlt sich ein 8-10 mm hoher Passungsprobekörper
mit denselben Innen- und Außendurchmessern. Bleibt die Hülse durch Rost, Naht oder
Ovalität lokal enger, kann das Durchmesserspiel anschließend parametrisch erhöht
werden.
