# Egg-Cup Man – Maßdokumentation

Quelle: https://www.printables.com/model/1631406-funny-egg-cup-man-with-legs-cute-breakfast-egg-holder  
Modell-ID: 1631406  
Status: Maße sind **Schätzungen** aus dem Kontext des Originals; kein direkter Zugriff auf STL-Dateien.  
Alle Werte müssen durch einen Testdruck bestätigt und dann hier aktualisiert werden.

## Korpus (Body)

| Merkmal | Maß (mm) | Quelle | Konfidenz |
| --- | ---: | --- | --- |
| Gesamthöhe Korpus | 65 | Schätzung aus typischem Eierbecher-Maßstab | niedrig |
| Max. Außendurchmesser (Mitte) | 50 | Schätzung | niedrig |
| Ei-Aufnahme Innendurchmesser oben | 38 | Standard-Eierbecher (Hühnerei ⌀ ~42 mm, Spielraum) | mittel |
| Ei-Aufnahme Tiefe | 22 | Schätzung | niedrig |
| Wandstärke Becher | 3.0 | FDM-Richtwert | mittel |
| Flatten-Abstand Boden | 8 | Flacher Stand; Boden der Ellipse abgeschnitten | Schätzung |
| Bodenplatte Dicke | 2.0 | FDM-Richtwert | mittel |

## Arme

| Merkmal | Maß (mm) | Quelle | Konfidenz |
| --- | ---: | --- | --- |
| Arm-Zapfen-Durchmesser | 6.0 | Schätzung | niedrig |
| Arm-Zapfen-Tiefe (Eingriff) | 6.0 | Schätzung | niedrig |
| Arm-Zapfen Z-Höhe (ab Korpusboden) | 42 | ca. 2/3 der Körperhöhe | niedrig |
| Seitlicher Versatz (Mitte Korpus) | 25 | Hälfte des max. Durchmessers | niedrig |
| Press-Fit Spiel | 0.20 | Standard-Profil 0.4 mm Düse | mittel |

## Beine

| Merkmal | Maß (mm) | Quelle | Konfidenz |
| --- | ---: | --- | --- |
| Bein-Zapfen-Durchmesser | 8.0 | Schätzung | niedrig |
| Bein-Zapfen-Tiefe (Eingriff) | 8.0 | Schätzung | niedrig |
| Bein-Zapfen Y-Versatz (vorne/hinten) | 0 | mittig, nur X-Spread | Schätzung |
| X-Spread Beine (Mitte-Mitte) | 22 | Schätzung | niedrig |
| Z-Position Bein-Zapfen-Mitte | 10 | in der unteren Rundungszone | Schätzung |
| Press-Fit Spiel | 0.20 | Standard-Profil 0.4 mm Düse | mittel |

## TODO nach Testdruck

- [ ] Alle Durchmesser mit Schieblehre nachmessen
- [ ] Passung Arme/Beine prüfen und `PRESS_CLEAR` anpassen
- [ ] Ei-Aufnahme gegen echtes Hühnerei testen
