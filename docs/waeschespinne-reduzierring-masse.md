# Wäschespinne-Reduzierring – Maße

| Merkmal | Maß | Herkunft | Konfidenz |
| --- | ---: | --- | --- |
| Eindrehhülse, Innendurchmesser | 60,48 mm | Schieblehre, Referenzfoto Kachel 01, 2026-09-16 | Hoch |
| Wäschespinnenmast, Außendurchmesser | 43,04 mm | Schieblehre, Referenzfoto Kachel 00, 2026-09-16 | Hoch |
| Einstecktiefe | 50,00 mm | Benutzerangabe | Hoch |
| Kragen, Außendurchmesser | 70,00 mm | Benutzerentscheidung | Hoch |
| Kragenhöhe | 3,00 mm | Benutzerentscheidung | Hoch |
| Gesamthöhe | 53,00 mm | Abgeleitet: 50,00 + 3,00 mm | Hoch |
| Passung | 0,40 mm Durchmesserspiel an beiden Kontaktflächen | Konstruktive Wahl: ASA-Gleitpassung nach Druckerprofil | Mittel |
| Ringaußendurchmesser | 60,08 mm | Abgeleitet: 60,48 − 0,40 mm | Hoch |
| Ringinnendurchmesser | 43,44 mm | Abgeleitet: 43,04 + 0,40 mm | Hoch |
| Radiale Wandstärke | 8,32 mm | Abgeleitet aus Außen- und Innendurchmesser | Hoch |
| Einführfase außen | 1,00 mm am hülsenseitigen Ende | Konstruktive, nicht fit-kritische Wahl | Mittel |
| Einlaufrundung innen | Radius 1,00 mm an der mastseitigen Kragenfläche | Benutzerwunsch, rot markierte Kante im Referenzbild | Hoch |

## Befund zum ersten Druck

Das Referenzfoto Kachel 00 zeigt 43,04 mm außen am Mast. Die Anzeige wurde
zunächst irrtümlich als 47,04 mm gelesen; die vergrößerte Originalaufnahme
bestätigt eindeutig 43,04 mm. Der ursprüngliche Nennwert 43,00 mm war daher
grundsätzlich richtig, benötigte aber eine praktische Gleitpassung.

Die Kacheln 02 und 03 zeigen den schwarzen Fehldruck. Die abgelesenen Maße
35,85 mm und 52,11 mm liegen zudem deutlich außerhalb der Sollmaße des
damaligen STL (43,30 mm innen, 59,70 mm außen) und werden deshalb nicht als
Bauteilmaße verwendet. Ein solcher Unterschied ist keine normale ASA-
Schwindung; beim erneuten Druck muss die Slicer-Skalierung auf 100 % stehen.

## Einbaurichtung

Der Kragen liegt auf der Oberkante der 60,48-mm-Hülse auf und verhindert, dass
der Ring hineinrutscht. Der 50-mm-Zylinder zeigt in die Hülse; der
43,04-mm-Mast wird von der Kragenseite durch die innenliegende Einlaufrundung
eingeschoben.

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
