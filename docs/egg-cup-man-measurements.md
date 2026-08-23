# Egg-Cup Man – Maßdokumentation

Quelle: https://www.printables.com/model/1631406-funny-egg-cup-man-with-legs-cute-breakfast-egg-holder  
Modell-ID: 1631406  
Status: Körper-STL liegt vor (`models/egg-cup-man-body.stl`); Außenmaße aus Mesh-Bounds entnommen.  
Innenmaße (Ei-Aufnahme, Zapfen) sind weiterhin Schätzungen und müssen durch Testdruck bestätigt werden.

## Korpus (Body)

| Merkmal | Maß (mm) | Quelle | Konfidenz |
| --- | ---: | --- | --- |
| Gesamthöhe Korpus | 60 | STL Bounds (Z-Extent) | hoch |
| Max. Außendurchmesser (Mitte) | 50 | STL Bounds (X/Y-Extent) | hoch |
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
| Seitlicher Versatz (Mitte Korpus) | 25 | STL Bounds (X-Halbbreite) | hoch |
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
