# Maß- und Quellen-Dokumentation: Ohnezahn / Toothless Drachenfigur (`drache`)

## 1. Identifikation des Referenzobjekts

- **Motiv / Charakter**: **Ohnezahn (Toothless / Nachtschatten / Night Fury)** aus *Drachenzähmen leicht gemacht* (*How to Train Your Dragon*).
- **Figuren-Vorlage**: Gesprühte/gegossene Miniatur-Sammelfigur (Spin Master *Dragons* Mini-Figur, ca. 3 Zoll / ~78 mm Klasse).
- **Wichtige Benutzervorgabe**: Den auf der Schwanzunterseite aufgedruckten Produktions-/Copyright-Code (`41204AFS`) **weglassen**.
- **Referenz-Indexblatt**: `model-sources/drache_frames/_index.png` (25 extrahierte Video-Einzelbilder, Kacheln `#00` bis `#24`).

### Farbbereiche / Material-Semantik aus den Referenzbildern

| Bereich | Farbe / Erscheinungsbild | Referenz-Kacheln (`_index.png`) |
| --- | --- | --- |
| Hauptkörper, Beine, Kopf, Flügel, Rückenkämme, rechte Schwanzflosse | **Schwarz (matt)** mit leicht strukturierter Schuppenoberfläche an Beinen und Rücken | `#00`–`#24` (`frame_03_f0064.jpg`, `frame_13_f0384.jpg`, `frame_19_f0576.jpg`) |
| Augen (links & rechts) | **Hellgrün / Limettengrün** mit vertikaler **schwarzer Schlitzpupille** | `#02` (`frame_03_f0064.jpg`), `#16` (`frame_17_f0512.jpg`), `#18` (`frame_19_f0576.jpg`), `#23` (`frame_24_f0736.jpg`) |
| Linke Schwanzflossen-Prothese | **Rot** | `#02` (`frame_03_f0064.jpg`), `#07` (`frame_08_f0224.jpg`), `#18` (`frame_19_f0576.jpg`), `#23` (`frame_24_f0736.jpg`) |
| Emblem auf der linken roten Schwanzflosse | **Weiß** (stilisiertes Wikinger-/Schädel-Symbol auf der Oberseite) | `#02` (`frame_03_f0064.jpg`), `#18` (`frame_19_f0576.jpg`), `#23` (`frame_24_f0736.jpg`) |

---

## 2. Maßstabsreferenz & Photogrammetrische Vermessung

Als Maßstabsreferenz liegt direkt neben der Figur auf derselben Karton-Ebene eine **2-Euro-Münze**.

### Offizielle Normmaße der 2-Euro-Münze (Europäische Zentralbank)

| Parameter | Wert | Quelle | Vertrauensstufe |
| --- | --- | --- | --- |
| Münzdurchmesser (`D_coin`) | **25,75 mm** | EZB / Amtsblatt der Europäischen Union | **Verifiziert (Normmaß)** |
| Münzdicke (`H_coin`) | **2,20 mm** | EZB / Amtsblatt der Europäischen Union | **Verifiziert (Normmaß)** |

### Abgeleitete Figurenmaße (1:1 Maßstab über 2-Euro-Münze kalibriert)

Aus den Kacheln `#02` (`frame_03_f0064.jpg`, Seitenansicht rechts), `#07` (`frame_08_f0224.jpg`, Rückansicht mit Münze auf identischer Tiefenebene `y ≈ 1045 px`, `180 px = 25,75 mm` → `0,1431 mm/px`), `#12` (`frame_13_f0384.jpg`, Seitenansicht links), `#18` (`frame_19_f0576.jpg`, Vorderansicht mit Münze `196 px = 25,75 mm` → `0,1314 mm/px`) und `#23` (`frame_24_f0736.jpg`, Schrägansicht):

| Maß / Merkmal | Wert (mm) | Herleitung / Kachel-Referenz | Status |
| --- | --- | --- | --- |
| **Gesamtlänge (X)** (Schnauzenspitze bis hintere Schwanzflossenspitze) | **78,0 mm** (`± 2,0 mm`) | Kachel `#02`: `674 px` bei Tiefenkorrektur `0,1125 mm/px` und Gierwinkel `~12°` (`3,03 × D_coin`) | Foto-abgeleitet (über 2-€-Münze kalibriert) |
| **Gesamtbreite (Y)** (Flügelspitze links bis Flügelspitze rechts) | **45,5 mm** (`± 1,5 mm`) | Kachel `#07`: `317 px × 0,1431 mm/px = 45,35 mm` (`1,76 × D_coin`) | Foto-abgeleitet (über 2-€-Münze kalibriert) |
| **Gesamthöhe (Z)** (Standfläche bis Spitze der roten Schwanzflosse) | **60,5 mm** (`± 2,0 mm`) | Kachel `#02` & `#23`: `540 px × 0,1125 mm/px = 60,75 mm` (`2,35 × D_coin`) | Foto-abgeleitet (über 2-€-Münze kalibriert) |
| **Flügelspitzenhöhe (Z)** (Standfläche bis Oberkante Hauptflügel) | **50,0 mm** (`± 1,5 mm`) | Kachel `#02` (`50,9 mm`) & Kachel `#07` (`49,5 mm`) | Foto-abgeleitet |
| **Standbreite Hinterbeine (Y)** (Außenkante linke bis rechte Hinterpfote) | **40,0 mm** (`± 1,0 mm`) | Kachel `#07`: `280 px × 0,1431 mm/px = 40,06 mm` | Foto-abgeleitet |
| **Spannweite Nebenflügel / Hüftflossen (Y)** | **36,8 mm** (`± 1,0 mm`) | Kachel `#07`: `257 px × 0,1431 mm/px = 36,77 mm` | Foto-abgeleitet |
| **Rumpfbreite an der Hüfte (Y)** | **25,5 mm** (`± 1,0 mm`) | Kachel `#07`: `178 px × 0,1431 mm/px = 25,46 mm` (`≈ 1,0 × D_coin`) | Foto-abgeleitet |
| **Kopfbreite (Y)** (Wange zu Wange ohne seitliche Fortsätze / mit Fortsätzen) | **28,0 mm / 31,5 mm** | Kachel `#18` & `#02` | Foto-abgeleitet |
| **Kopflänge (X)** (Schnauze bis Hinterkopf / inkl. langer Kopfzapfen) | **25,0 mm / 35,0 mm** | Kachel `#02` & `#12`: `221 px` bzw. `311 px × 0,1125 mm/px` | Foto-abgeleitet |
| **Kopfhöhe (Z)** (Kinn bis Schädeldecke) | **22,5 mm** | Kachel `#02`: `200 px × 0,1125 mm/px` | Foto-abgeleitet |
| **Schulter-/Rückenhöhe (Z)** (Standfläche bis Rückenlinie zwischen den Flügeln) | **30,5 mm** | Kachel `#02` & `#12`: `270 px × 0,1125 mm/px` | Foto-abgeleitet |
| **Rücken- und Schwanznoppen (4 große Noppen auf Rücken/Schwanz)** | **Ø 3,6–4,2 mm, Höhe 3,5–4,5 mm** | Kachel `#02`, `#12`, `#23`: charakteristische abgerundete Steck-/Rückennoppen vor den kleineren Schwanzzacken | Foto-abgeleitet |
| **Schwanzflossen-Spannweite (quer zur Schwanzachse)** | **22,0 mm** | Kachel `#02`, `#18`, `#23`: asymmetrisches V-Profil (links rot mit weißem Symbol, rechts schwarz) | Foto-abgeleitet |

---

## 3. Recherche wiederverwendbarer 3D-Assets (`research-reusable-3d-assets`)

Vor der Modellierung wurde nach bestehenden 3D-Modellen von *Toothless / Night Fury* gesucht:

1. **Printables / MakerWorld / MyMiniFactory (*Toothless – Night Fury* von José Pedro / marjers, Becca_3D / Kaijumon)**:
   - Lizenz: `CC BY-NC-SA 4.0` bzw. *Standard Digital File License (Personal Use Only)*.
   - Einstufung: **Nur visuelle Referenz (`reference-only`)**, da restriktive NC-Lizenzen und abweichende Posen.
2. **Sketchfab (*Night Fury Toothless* von BenAissa_Karim, *Toothless night fury* von LunaEagle)**:
   - Lizenz: `CC-BY` laut Metadaten, jedoch hinter Login-Wall und mit fliegenden/stehenden Posen, die nicht der kompakten geduckten Spielfigur mit den charakteristischen Rückennoppen, Doppel-Kurzflügeln und dem hochgebogenen S-Schwanz entsprechen.
3. **Entscheidung (`asset_strategy = rebuild` in Blender + Python)**:
   - Vollständige, lizenzfreie Original-Neukonstruktion der exakten Figur in **Blender 5.2** (organische Skulptur aus Subsurface-/Metaball-/Voxel-Remesh-Geometrie mit präzise ausgeformten Farbkörpern) kombiniert mit **Python (`trimesh` / `manifold3d`)** für exakte Maßkalibrierung, ebene Standflächen der vier Pfoten, boolesche Farbzonen-Trennung, Mesh-Validierung und OrcaSlicer-3MF-Paketierung.
