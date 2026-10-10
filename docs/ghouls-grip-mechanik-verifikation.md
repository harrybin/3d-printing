# Ghoul's Grip - Mechanik-Verifikation

Ergebnis: **PASS**

Geprüft wird die starre, manuell reversible Kraftkette: Drehbarer Totenkopf -> Antriebsritzel -> Schlittenzahnstange -> Doppelschere sowie Antriebsritzel -> Deckelzahnstange -> gefangener Deckelkurbelzapfen. Ein mitfahrendes Fünf-Zahnrad-Getriebe mit drei Zwischenrädern überträgt die Scherenarmdrehung auf den Unterarm. Es gibt keine Seile, Gummibänder, Federn oder Wickelspulen.

| Nachweis | Ergebnis |
| --- | ---: |
| Max. Pivot-Schließfehler | 0.000000 mm |
| Kleinster Scherenkulissenrand | 1.524 mm |
| Ritzel/Zahnstangen-Schließfehler | 0.000000 mm |
| Deckelkurbel-Schließfehler | 0.000000 mm |
| Kleinster Deckelzapfen-Kulissenrand | 1.000 mm |
| Max. Zahnrad-Mittenfehler | 0.000000 mm |
| Max. Zahnrad-Teilungsfehler | 0.162 mm |
| Zwischenrad-Pinspiel | 0.400 mm |
| Unterarm-Einsetzsweep | 0.000 mm³ |
| D-Wellen-Einsetzsweep | 0.000 mm³ |
| Totenkopf-Drehweg | 113.54° |
| Einzelkörper je Druckteil | {'scissor-arm': 1, 'slider': 1, 'lid-follower-rack': 1, 'platform': 1, 'drive-pinion': 1, 'lid-rack': 1, 'lid-crank': 1, 'scissor-drive-gear': 1, 'idler-gear': 1, 'forearm-output-gear': 1, 'forearm': 1, 'chest': 1, 'lid': 1} |
| Laufzeit | 381.8 s |
| Sweep hand_chest | 0.000 mm³ |
| Sweep hand_lid | 0.000 mm³ |
| Sweep hand_platform | 0.000 mm³ |
| Sweep hand_scissor | 0.000 mm³ |
| Sweep forearm_platform | 0.000 mm³ |
| Sweep input_gear_platform | 0.000 mm³ |
| Sweep idler_gear_0_platform | 0.000 mm³ |
| Sweep idler_gear_1_platform | 0.000 mm³ |
| Sweep idler_gear_2_platform | 0.000 mm³ |
| Sweep output_gear_platform | 0.000 mm³ |
| Sweep output_gear_forearm | 0.000 mm³ |
| Sweep gear_mesh_0_1 | 0.000 mm³ |
| Sweep gear_mesh_1_2 | 0.000 mm³ |
| Sweep gear_mesh_2_3 | 0.000 mm³ |
| Sweep gear_mesh_3_4 | 0.000 mm³ |
| Sweep slider_chest | 0.000 mm³ |
| Sweep lid_chest | 0.000 mm³ |
| Sweep lid_rack_lid | 0.000 mm³ |
| Sweep lid_rack_chest | 0.000 mm³ |
| Sweep lid_yoke_lid | 0.000 mm³ |
| Sweep lid_yoke_chest | 0.000 mm³ |

## Gekoppelte Bewegung

| Scherenwinkel | Totenkopf/Ritzel | Deckel | Unterarm |
| ---: | ---: | ---: | ---: |
| 18° | 0.0° | -0.0° | -105.0° |
| 23° | 4.7° | -33.9° | -100.0° |
| 28° | 10.4° | -75.7° | -95.0° |
| 33° | 17.2° | -108.0° | -90.0° |
| 38° | 24.9° | -108.0° | -85.0° |
| 43° | 33.6° | -108.0° | -80.0° |
| 48° | 43.1° | -108.0° | -75.0° |
| 53° | 53.4° | -108.0° | -70.0° |
| 58° | 64.3° | -108.0° | -65.0° |
| 63° | 75.9° | -108.0° | -60.0° |
| 68° | 88.1° | -108.0° | -55.0° |
| 73° | 100.6° | -108.0° | -50.0° |
| 78° | 113.5° | -108.0° | -45.0° |

Der knochenfarbene Unterarm wird ohne Zahnrad von oben zwischen die beiden Lagerohren gesetzt. Anschließend wird das naturweiße Ausgangszahnrad mit seiner D-Welle von der Zahnradseite axial durch beide Rundlager und die passende D-Nabe des Unterarms geschoben. Ein 1,75-mm-Filamentstift im äußeren Querloch sichert die Welle gegen Herausrutschen; erst danach werden die Zwischenräder aufgesteckt.

Die Finger bleiben als druckbare, vorgekrümmte PLA-Flexuren in der kompakten Greifpose. Die neue starre Kraftkette betätigt Deckel, Scherenhub und Unterarm; sie enthält bewusst keine vorgetäuschte Sehnenbetätigung.
