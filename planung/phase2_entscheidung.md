# Phase 2 – Entscheidung des Schiedsrichters: Verknüpfung der 18 Firmen (R2)

Stand: 21.10.2026 (Neudurchlauf mit halber Besetzung) · Ersetzt die Fassung vom 20.10.2026. Grundlage:
`phase1_team_a.md` und `phase1_team_b.md` (beide R2, Firmen unverändert), `phase2_vorschlag_team_a.md` (R2, Δ1–Δ9),
`phase2_vorschlag_team_b.md` (R2, K1–K11), `NACHRICHTEN.md`, `generate_space_trading_data.py` (Seed 42) und eigene
Abfragen auf `/home/user/bestand/space_trading_game_bestand.db` (nur lesend, `mode=ro`). Das maschinenlesbare Ergebnis
steht in `planung/verknuepfungen.json` und ist für die Umsetzung verbindlich. Alle Zählungen und Prüfungen unten habe ich
mit eigenen Skripten über die JSON-Datei und die Bestands-DB nachgerechnet.

## 0. Kurzfassung

Beide Teams haben das verbindliche Netz der ersten Entscheidung übernommen und nur nachgeprüft. Für R2 gibt es deshalb
**kein neues Netz**. Ich entscheide über die Korrekturen: alle 11 von Team B (K1–K11) und alle 9 von Team A (Δ1–Δ9).
Fast alles übernehme ich, an drei Stellen korrigiere ich die Teams (Abschnitt 7).

| Thema | Entscheidung R2 |
|---|---|
| Vereinbarungen | **48 aktive, unverändert** (47 fest + `helix → corvane` optional). Team B führt `helix → corvane` im JSON als feste Kante. Das widerspricht ihrem eigenen Text und ist abgelehnt. |
| Netz | zusammenhängend, 38/153 Paare direkt, **66 nur indirekt**, 45 mit Abstand 3, 4 mit Abstand 4. Hub ist **Helix** (large, 7/10). |
| Historie / Rivalitäten | 7 bzw. 12, unverändert. Die Informanten der Rivalitäten sind nach der Leck-Regel bereinigt (Δ6 Team A). |
| Rahmenverträge | **21**, **82 Nachträge** (64 unterzeichnet, 17 offen, 1 abgelehnt). Basis ist das JSON von Team A, das K1/K2/K6/K7/K10 von B schon enthält, dazu Δ2/Δ3 und K9 von B. 341/475 Bestandsverträge, **13** Volumen-Auslöser. |
| Filter für neue Verkäufer | Vereinigung K8 (B) ∪ Δ4 (A): 8 Regeln, im JSON `exclusivity_filter_new_pairs` |
| Schriftverkehr | Schema unverändert. Vorgänge **V1–V41**: Datumskorrekturen K3–K6 (B), V14 korrigiert (Δ7, A), neu V39 (B), V40 und V41 (A) |
| Profile neuer Firmen | K11 (Morgengrund `trade_hub` Isolde) und Δ9 (Kuppelwerk `mining` Aurelis) angenommen |
| QA | Ankerliste von A (ohne die Nicht-Bestandsnummer `PKB-VTR-2058-0001`), Einstellungsgrenzen Δ8, Mahn- und Reihenfolgeregeln K3–K6 |

---

## 1. Bewertung (Punkt für Punkt)

Punkte 1–5 (5 = am besten), bewertet ist nur der R2-Beitrag.

| Bereich | Kriterium | Team A | Team B | Begründung (eigene Prüfung) |
|---|---|---:|---:|---|
| Vereinbarungen | Plausibilität Warenflüsse | 5 | 5 | Beide haben dieselben 48 Kanten. Die Verbraucherprüfung ist bei beiden richtig (≥ 52 %). Ich habe `pionierwerk → morgengrund` selbst nachgerechnet: 0,52, mit K11 1,00. |
| | Regeltreue | 5 | 4 | Zählung, Hub und Netz stimmen bei beiden. B schreibt im JSON aber `helix → corvane` als feste Kante (48 in `partnerships`). Das würde einen `rng.random()`-Zug im Bestandsstrom entfernen. |
| | Spielwert | 4 | 5 | B zeigt mit Morgengrund ↔ Kuppelwerk eine indirekte Verbindung, die die Exklusivität erzwingt, und schlägt K11 vor (Handelsplatz in Isolde). |
| | Umsetzbarkeit | 5 | 4 | A trennt fest und optional sauber. Beim Hub-Gleichstand ohne `helix → corvane` hat A recht: Die Sortierung legt die Reihenfolge nicht fest. B behauptet eine Reihenfolge nach `company_id`. |
| Historie | alle | 5 | 5 | identisch, unverändert |
| Rivalitäten | Datenbezug / Leck-Regel | 5 | 3 | Δ6 (A): Schuchhardt 178 (85/25) und Eberhardt 45 (75/23) erfüllen die Leck-Regel nicht. Im Bestand geprüft. Mit Freddy Dörr 235 (45/88, Station Förster = Ort der Ausfälle 19/36/70) und Darren Harris 319 (35/69, seit 2056-02-19) gibt es echte Quellen. B prüft nur `hire_date`. |
| Rahmenverträge | Konsistenz mit Bestand | 5 | 4 | Beide finden K1 (Corvane liefert Technik an Hande, CVB-CTR-2059-0066 `exclusive_supply` bis 2060-08-05, geprüft). **Die Funde K2, K6, K7, K9 und K10 kommen von B** (alle im Bestand bestätigt). A hat Δ2 (Produktaufnahmen, Daten geprüft) und Δ3 (Lichtacker hat nur Agrar- und Forschungsstationen). B zählt die Volumen-Auslöser falsch („12 von 12“, es sind 13). Im JSON von B fehlen außerdem `price_floor` (RVF-RV-2058-02) und `harvest_clause` (SGM-RV-2059-01). |
| | Spielwert | 4 | 5 | B: Liegeplatz-Teil der dreiseitigen Klausel (K2) gibt Ravenmoors Handelsstation eine Aufgabe; Schuldenstand nach Datum (K10). A: Kette Chavez → Rüge → Aussetzung (mit B). |
| | Umsetzbarkeit | 5 | 4 | Das JSON von A enthält alle angenommenen Korrekturen beider Teams und ist direkt nutzbar. B fehlen Δ2 und Δ3, außerdem gingen zwei Felder verloren. |
| Filter | Vollständigkeit | 5 | 4 | K8 (B) ist der Kern. Δ4 (A) ergänzt Kuppelwerk (`water_ice` nach Isolde, `nav_computers` an Graufalk) und die Verkäuferexklusivität `habitat_modules`. |
| Schriftverkehr | Datenkorrektheit | 4 | 5 | **K3–K6 (B)** sind echte Fehler der ersten Entscheidung: Fälligkeiten und ein Schreiben vor seiner Bestellung. Ich habe alle vier nachgerechnet. A findet Δ7 (V14: Leck-Regel und Reihenfolge). In der Ankerliste von A steht mit `PKB-VTR-2058-0001` eine Nummer, die es im Bestand nicht gibt. |
| | Spielwert | 5 | 4 | V40 (A) ist ein Spionage-Rätsel: Lichtacker verdächtigt Erkan Hesse (39), der am 2059-06-11 entlassen wird (Bestand). Das wahre Leck ist Täsche. V39 (B) ist die Brücke zur Aussetzung. |
| QA | Bestandsvergleich | 5 | 4 | A hat eine Obermenge der Liste von B (geprüft: alle B-Objekte enthalten) und legt die Vergleichsfelder fest. Dazu kommt Δ8 (Einstellungsgrenzen neuer Firmen), eine echte Lücke im Generator. |

---

## 2. Vereinbarungen (aktiv, gerichtet Verkäufer → Käufer)

### 2.1 Was übernommen wurde

Unverändert aus der ersten Entscheidung, von beiden Teams bestätigt:

- **Bestand (14)**: 13 Blueprint-Kanten plus `helix → corvane` (logistics_partnership, bleibt in
  `OPTIONAL_PARTNERSHIPS` mit p = 0,6). **Abgelehnt** ist die feste Kante im JSON von Team B (Abschnitt 7, Nr. 1).
- **Neue Firma → Bestand (7)**: `graufalk → helix`, `cindervale → eisenkrone`, `kuppelwerk → lichtacker`,
  `emberline → corvane`, `emberline → lichtacker`, `raureif → eisenkrone`, `ravenmoor → helix`.
- **Innerhalb Team A (12)**, **innerhalb Team B (12)**, **teamübergreifend (3)**: `kuppelwerk → pionierwerk`,
  `second_hull → graufalk`, `graufalk → ravenmoor`.
- Neue Kanten mit Bestandsfirmen gibt es nur in Richtung „neue Firma → Bestandsfirma“. Routen, Verträge und Kunden der
  Bestandsfirmen bleiben so stabil. Neue `trade_partnerships`-Zeilen kommen nach Zeile 15.

### 2.2 Verbraucherprüfung

Jede Kante hat ≥ 52 % des Warengewichts des Verkäufers mit passendem Verbraucher-Stationstyp beim Käufer
(`CATEGORY_CONSUMERS` plus Zusatzverbraucher je Archetyp). Bei neuen Firmen zählen nur die Pflichtstationen. Nachgerechnet
habe ich die knappste Kante `pionierwerk → morgengrund`: Industriegüter 0,36, Energie 0,08 und Medizin 0,08 gehen an eine
Agrarstation, das sind **0,52**. Mit der zweiten Pflichtstation `trade_hub` (K11) sind es **1,00**.

### 2.3 Finale Zählung je Firma (selbst ausgezählt, beide Richtungen)

| Firma | Größe | Vereinb. | ausgehend | eingehend | direkte Partner | erlaubt | frei | ok |
|---|---|---:|---:|---:|---:|---|---:|---|
| Feldspat | small | 3 | 2 | 1 | 2 | 1–3 | 0 | ✓ |
| Driftwood | small | 1 | 1 | 0 | 1 | 1–3 | 2 | ✓ |
| Lichtacker | medium | 6 | 2 | 4 | 5 | 3–6 | 0 | ✓ |
| Corvane | medium | 6 | 2 | 4 | 4 | 3–6 | 0 | ✓ |
| Eisenkrone | large | 9 | 4 | 5 | 6 | 6–10 | 1 | ✓ |
| **Helix (Hub)** | large | **10** | 3 | 7 | **7** | 6–10 | 0 | ✓ |
| Graufalk | large | 9 | 4 | 5 | 7 | 6–10 | 1 | ✓ |
| Cindervale | large | 7 | 4 | 3 | 5 | 6–10 | 3 | ✓ |
| Kuppelwerk | medium | 4 | 3 | 1 | 4 | 3–6 | 2 | ✓ |
| Emberline | medium | 6 | 5 | 1 | 5 | 3–6 | 0 | ✓ |
| Kometenpost | small | 3 | 1 | 2 | 2 | 1–3 | 0 | ✓ |
| Lanternfish | small | 3 | 2 | 1 | 3 | 1–3 | 0 | ✓ |
| Pionierwerk | large | 8 | 2 | 6 | 6 | 6–10 | 2 | ✓ |
| Ravenmoor | large | 8 | 3 | 5 | 7 | 6–10 | 2 | ✓ |
| Raureif | medium | 4 | 3 | 1 | 4 | 3–6 | 2 | ✓ |
| Outmark | medium | 3 | 2 | 1 | 3 | 3–6 | 3 | ✓ |
| Morgengrund | small | 3 | 2 | 1 | 2 | 1–3 | 0 | ✓ |
| Second Hull | small | 3 | 3 | 0 | 3 | 1–3 | 0 | ✓ |
| **Summe** | | **96 = 2 × 48** | 48 | 48 | | | 16 | |

- **Hub**: Helix 7 Partner / 10 Vereinbarungen, vor Graufalk 7/9 und Ravenmoor 7/8, alle drei large.
  **Ohne** `helix → corvane` (anderer Seed): Helix hat 7/9 und liegt gleichauf mit Graufalk 7/9. Corvane hat dann 5,
  liegt also noch im Bereich, und alle Firmen bleiben im Größenbereich (nachgerechnet). Die QA soll deshalb als dritten
  Sortierschlüssel `company_id` und `kind="stable"` verwenden. Das Ergebnis „Hub ist large“ gilt so oder so.
- **Jede Firma hat ≥ 1 ausgehende Vereinbarung.** Das Minimum ist 1 (Driftwood, Kometenpost).
- **Unvollständig, ≥ 2 nur indirekt verbundene Paare**: Abstand 1: 38, Abstand 2: **66**, Abstand 3: 45, Abstand 4: 4.
  Das Netz ist zusammenhängend, der Durchmesser ist 4. Beispiele: Feldspat ↔ Raureif (über Eisenkrone), Driftwood ↔
  Ravenmoor (über Helix), Lichtacker ↔ Pionierwerk (über Kuppelwerk), Morgengrund ↔ Kuppelwerk (über Pionierwerk).
- Kein Paar ist zugleich historisch und aktiv mit demselben Typ. Die 12 Rivalitäten sind eindeutig je Paar.

---

## 3. Historische Partnerschaften (7, unverändert)

`corvane → driftwood` (Bestand), `eisenkrone → graufalk` 2039-01-01–2049-06-30, `cindervale → helix` (licensing)
2041-04-01–2054-03-31, `lichtacker → pionierwerk` 2045-03-01–2053-06-30, `emberline → eisenkrone` 2047-02-01–2056-06-30,
`outmark → feldspat` (licensing) 2055-02-01–2058-06-30, `driftwood → second_hull` (consignment) 2057-05-01–2058-07-01.
Beide Teams haben die Daten gegen `founded_year` und `window_start − 120 T` geprüft. Ich habe das bestätigt.

## 4. Rivalitäten (12) – Informanten nach Leck-Regel (Δ6)

Typen, Systeme, since, intensity und espionage_risk sind unverändert. Neu ist die Trennung der Informanten in
**Leck-Quellen** (Regel bribe ≥ 50 oder loyalty ≤ 50 erfüllt) und **Zeugen/Ziele**:

| Firma → Rivale | Leck-Quellen (ID, Loyalität/Bestechlichkeit) | Zeugen / Ziele |
|---|---|---|
| graufalk → eisenkrone | Esther Bauer 170 (53/76), **Freddy Dörr 235** (45/88, Sicherheit Förster, Zugang 1) | Ziel: Annekatrin Schuchhardt 178 (85/25) |
| cindervale → helix | **Darren Harris 319** (35/69, seit 2056-02-19), Desiree Schwartz 299 (58/78, ab 2059-11-24) | Zeuge: Richard Chavez 120 (Corvane) |
| emberline → eisenkrone | Esther Bauer 170 | Zeugen: Polina Zahn 83, Hans-Werner Eberhardt 45 (Lichtacker) |
| lichtacker → pionierwerk | Kaspar Täsche 43 (55/61) | – |
| ravenmoor → driftwood | Carlos Osborne 29 (3/100), Nathan Hines 33 (36/81) | – |
| outmark → feldspat | Slavko Geisel 16 (55/96) | – |
| ravenmoor → helix | Wayne Jacobson 302 (48/73), Tyler Garcia 395 (55/71), Brandon Jones 445 (38/89) | – |
| second_hull → driftwood | Douglas Lawson 27 (57/61) | – |

Ergänzung des Schiedsrichters: Polina Zahn (55/88) erfüllt die Leck-Regel. Sie bleibt in V28 die Absenderin des Tipps an
Emberline (Lichtacker-Interna, `leaked_by` 83) und ist im JSON als `third_party_leaks` geführt. Damit bleibt V28
unverändert.

---

## 5. Rahmenverträge (21, 82 Nachträge)

### 5.1 Basis und Änderungen R2

Grundlage ist das JSON von Team A. Es enthält schon die angenommenen Korrekturen von B. Alle Punkte habe ich im
Bestand nachgeprüft:

| # | Änderung | Herkunft | Prüfung im Bestand |
|---|---|---|---|
| K1/Δ1 | CCI-MSA-2057-01: `buyer_exclusive` → **`right_of_first_refusal`** (Technik Halcyon), Folge-Vorgang V39 | B und A | CVB-CTR-2058-0003 (spot), -0013, -0038 (framework), -2059-0044 (recurring), **-2059-0066 (`exclusive_supply` Robotik, 2059-08-24 bis 2060-08-05, active)**, alle an Bergbaustation Hande |
| K2 | Geleitschutzklausel EKM-RV-2057-02 an **EKM-VTR-2057-0043/-2058-0107** (Geleitschutz abgewartet +118 h/+71 h). Die Andockstau-Brüche **-2057-0017/-2059-0162** (+118 h/+127 h) begründen Ausweich-Liegeplätze bei Ravenmoor in Kharon. | B | bestätigt, Paar Eisenkrone → Helix |
| K6 | Eilabrufklausel GFW-RV-2057-01 `proposed_date` 2059-12-31, Anker HMX-SHP-2059-01721/-01746 | B | HMX-ORD-2059-01788 bestellt 2059-12-29 17:13 |
| K7 | RVF-RV-2058-01: Basis-Exklusivität nur `water_ice`. Der Nachtrag 2058-09-01 ist `exclusivity_clause` für `nitrogen_ice`. | B | – |
| K9 | HMX-MSA-2057-02 nur, wenn `helix → corvane` gezogen wird (Feld `condition`) | B | Seed 42: gezogen |
| K10 | FSP-RV-2059-01: Schuldenstand nach Datum | B | 2059-07-20: 11 Bestellungen, 22.941.712,52 · 08-01: 12, 24.217.471,21 · ab 09-23: 13, 25.522.655,14 CR |
| Δ2 | Produktaufnahmen einzeln: HMX-MSA-2057-03 medical 07-01 / technology **09-01** / industrial_goods **11-01**; EKM-RV-2057-01 luxury 05-01 / technology **06-01**; EKM-RV-2057-02 food 06-01 / technology **10-01** (alle 2057) → +4 Nachträge | A | erste Abrufverträge: 07-31, 09-23, 11-04; 05-25, 06-06; 06-25, 10-03 |
| Δ3 | KHB-RV-2059-01: Rohstoffe nur `regolith`/`water_ice` (`scope_archetypes`) | A | Lichtacker hat 5 Agrarstationen und 1 Forschungsstation. `raw_materials` wird dort nur über Zusatzverbraucher abgenommen (water_ice: agricultural/research, regolith: agricultural). |
| – | `price_floor` (RVF-RV-2058-02) und `harvest_clause` (SGM-RV-2059-01) bleiben | Schiedsrichter | fehlten im JSON von B |

### 5.2 Übersicht

| Nr. | Paar | Beginn, Laufzeit | Basis (Mio. CR) | Nachträge (offen) | Bestandsverträge |
|---|---|---|---:|---|---:|
| HMX-MSA-2057-01 | helix → lichtacker | 2057-01-01, 36 M | 250 | 7 | 54 |
| HMX-MSA-2057-02 | helix → corvane (K9) | 2057-01-01, 36 M | 300 | 10 (1) | 68 |
| HMX-MSA-2057-03 | helix → eisenkrone | 2057-01-01, 48 M | 300 | 7 (1) | 75 |
| EKM-RV-2057-01 | eisenkrone → corvane | 2057-01-01, 60 M | 350 | 6 (2) | 65 |
| EKM-RV-2057-02 | eisenkrone → helix | 2057-01-01, 42 M | 200 | 9 (3) | 39 |
| EKM-RV-2057-03 | eisenkrone → lichtacker | 2057-01-01, 36 M | 150 | 7 (1 abgelehnt) | 35 |
| FSP-RV-2059-01 | feldspat → eisenkrone | 2059-08-01, 24 M | 12 | 2 (1) | 5 |
| GFW-RV-2057-01 | graufalk → helix | 2057-01-01, 48 M | 180 | 3 (1) | neu |
| GFW-RV-2057-02 | graufalk → cindervale | 2057-01-01, 60 M | 220 | 3 (1) | neu |
| GFW-RV-2058-01 | graufalk → ravenmoor | 2058-07-15, 36 M | 90 | 2 | neu |
| CCI-MSA-2057-01 | cindervale → eisenkrone | 2057-01-01, 48 M | 120 | 3, `suspended` ab 2059-12-15 | neu |
| KHB-RV-2058-01 | kuppelwerk → pionierwerk | 2058-06-01, 36 M | 70 | 2 | neu |
| KHB-RV-2059-01 | kuppelwerk → lichtacker | 2059-04-01, 24 M | 30 | 3 (1) | neu |
| EFF-MSA-2059-01 | emberline → corvane | 2059-04-01, 24 M | 40 | 3 (1) | neu |
| EFF-MSA-2059-02 | emberline → lichtacker | 2059-11-15, 24 M | 18 | 1 | neu |
| RCS-MSA-2058-01 | ravenmoor → helix | 2058-08-01, 36 M | 90 | 3 (2) | neu |
| RVF-RV-2058-01 | raureif → pionierwerk | 2058-01-01, 36 M | 80 | 3 (1) | neu |
| RVF-RV-2058-02 | raureif → eisenkrone | 2058-03-01, 24 M | 45 | 2 (1) | neu |
| OSP-MSA-2058-01 | outmark → pionierwerk | 2058-02-01, 36 M | 25 | 2 | neu |
| SGM-RV-2059-01 | morgengrund → pionierwerk | 2059-01-01, 12 M + Auto | 5 | 2 | neu |
| SGM-RV-2059-02 | morgengrund → ravenmoor | 2059-03-01, 12 M | 6 | 2 (1) | neu |
| **Summe** | | | | **82** (64 / 17 / 1) | **341** |

Nachgezählt: 21 Nummern, alle eindeutig, alle Paare haben eine aktive Vereinbarung. 82 Nachträge (64 signed,
17 proposed, 1 rejected). Für die 7 Bestandspaare gibt es **13 Volumen-Auslöser**: HMX-CTR-2058-0161, -2059-0259,
-2058-0152, -2059-0213, -2060-0281, -2059-0192, -2059-0236, -2060-0275, EKM-VTR-2059-0160, -2060-0219, -2059-0151,
-2060-0234, -2059-0211. 341 Abrufverträge werden zugeordnet (2.309,1 Mio. CR). Außerhalb liegen genau
EKM-VTR-2060-0230 und FSP-VTR-2059-0001/-0005.

### 5.3 Exklusivitätsfilter für neue Verkäufer (K8 ∪ Δ4, verbindlich)

Diese Regeln gelten in Durchlauf 2 für Verträge und Partnerbestellungen. Vorkaufsrechte filtern nicht, Verstöße gegen sie
werden als Schreiben erzählt (V39).

| Verkäufer → Käufer | gesperrt | System, Zeitraum | Grund |
|---|---|---|---|
| emberline → corvane | `energy` | bis 2059-03-14 | HMX-MSA-2057-02 Energie käuferexklusiv |
| kuppelwerk → lichtacker | `industrial_goods` | bis 2059-03-14 | Vorkaufsrecht Helix, Absage V14 |
| graufalk → helix | `escort_drones`, `sensor_arrays` | Kharon, ab 2058-08-01 | RCS-MSA-2058-01 |
| emberline, kometenpost → cindervale | `drive_parts` | ab 2058-03-15 | GFW ↔ CCI gegenseitig |
| emberline, lanternfish, second_hull, kuppelwerk → graufalk | `nav_computers` | ab 2058-03-15 | GFW ↔ CCI gegenseitig |
| second_hull, outmark, morgengrund, kuppelwerk → pionierwerk | `water_ice` / `nitrogen_ice` | Isolde, ab 2058-01-01 / 2058-09-01 | RVF-RV-2058-01 (K7) |
| kuppelwerk → andere als pionierwerk | `habitat_modules` | Isolde, ab 2058-06-01 | KHB-RV-2058-01 verkäuferexklusiv |

---

## 6. Schriftverkehr

### 6.1 Design (unverändert, Ergänzungen R2)

Tabelle `correspondence` mit 20 Briefarten, Feldern, Verknüpfungen und Leckformel wie in `verknuepfungen.json`
(`correspondence_design`). Neu sind 4 QA-Regeln:

1. Mahnungen frühestens Fälligkeit (Ankunft + 30 T) + 3 T, Stufen +3..7 / +21 / +45 T (K3–K5).
2. Kein Schreiben vor seinem Bezugsobjekt (K6).
3. Unterzeichner der Rahmen sind am `signed_date` beschäftigt. Für neue Firmen gelten die Einstellungsgrenzen Δ8
   (`hire_date_caps_new_firms`, z. B. Graufalk/Cindervale ≤ 2056-11-02).
4. Jeder `leaked_by` erfüllt die Leck-Regel (Δ6/Δ7).

Mengen: ca. 860 Schreiben zu Bestandsobjekten (+4 aus Δ2, +6 aus V39–V41), ca. 2.200–2.800 für alle 18 Firmen.

### 6.2 Geprüfte Strafbeträge (unverändert)

HMX-CTR-2058-0159 **653.162,16** · HMX-CTR-2058-0131 **332.508,95** · EKM-VTR-2059-0162 **314.166,60** ·
EKM-VTR-2057-0017 **303.807,21** · EKM-VTR-2058-0099 **219.444,96** · HMX-CTR-2058-0139 **129.876,24** ·
HMX-CTR-2059-0197 **101.141,50** · EKM-VTR-2058-0105 **60.263,34** · HMX-CTR-2059-0242 **60.719,68** ·
EKM-VTR-2059-0167 **58.589,66** · HMX-CTR-2057-0043 **47.848,75** · HMX-CTR-2058-0173 **43.066,84** CR.

### 6.3 Verankerte Vorgänge (verbindlich, IDs = `employee_id`)

Die Vorgänge V2–V13, V15–V21, V23–V26, V28–V31, V33–V35, V37 und V38 bleiben wie in der Fassung vom 20.10. Ihr Inhalt ist
hier zur Vollständigkeit wiederholt. **Geänderte und neue Vorgänge sind fett markiert.**

| # | Datum | Art | Absender → Empfänger | Bezug |
|---|---|---|---|---|
| **V1** | **2057-08-28 / 09-13 / 10-07** (K4) | payment_reminder 1–3 | Pamela Stroh 169 → Mikhail Gotthard 2 | EKM-BST-2057-00352 (4,79 Mio., Ankunft 07-24, fällig 08-23) |
| V2 | 2057-12-20 | penalty_notice + amendment_offer | Elizabeth Lopez 293 → Esther Bauer 170 | EKM-VTR-2057-0017, EKM-RV-2057-02 |
| V3 | 2058-02-10 / 03-01 | breach_warning / amendment_confirmation | Annekatrin Schuchhardt 178 → Cindervale Partnerbetreuung | Ereignis 19, CCI-MSA-2057-01 |
| V4 | 2058-02-15 | amendment_offer (Volumensenkung) | Esther Bauer 170 → Kayla Cannon 332 | HMX-MSA-2057-03, Ereignis 19 |
| V5 | 2058-04-01 | termination_notice | Second Hull → Erin Cisneros 26 | historische Kommission, Ende 2058-07-01 |
| V6 | 2058-07-02 | internal_memo | Wayne Jacobson 302 → Elizabeth Lopez 293 | Ereignis 26 |
| V7 | 2058-07-15 → 07-25 → 08-01 | offer → counter_offer → contract_confirmation | Ravenmoor → David Hendricks 304; Lopez 293 | RCS-MSA-2058-01 |
| V8 | 2058-08-19 / 08-28 | delay_complaint / penalty_notice | Hans-Werner Eberhardt 45 → Irmingard Scholl 179; Lena Heß 40 → Pamela Stroh 169 | EKM-VTR-2058-0099 |
| V9 | 2058-08-20 / 10-05 | breach_warning / Antwort | Esther Bauer 170 → John Aguirre 119 | EKM-RV-2057-01, LAK-VTR-2058-0033, Storno LAK-VTR-2058-0039 |
| V10 | 2058-09-12 | rumor (offen) | Erin Cisneros 26 → Elizabeth Lopez 293 | Rivalität Ravenmoor ↔ Helix |
| V11 | 2058-11-20 | amendment_offer (−8 %) | Cindervale → Esther Bauer 170 | Ereignis 36 |
| V12 | 2058-12-16 / 12-20 | amendment_offer / confirmation | Kayla Cannon 332 → Graufalk | GFW-RV-2057-01 +60, HMX-CTR-2058-0173 |
| V13 | 2059-01-18 / 01-25 | delay_complaint / penalty_notice | Toralf Gerlach 47 → Kayla Cannon 332; Reimar Rörricht 38 → Lopez 293 | HMX-CTR-2058-0159, HMX-SHP-2059-01012 (+147 h) |
| **V14** | **2059-01-27** / 01-28 / 02-05 (Δ7) | rumor (wahr) / offer / offer_rejection | **Kaspar Täsche 43** (`leaked_by`) → Kuppelwerk; Kuppelwerk → Hülya Matthäi 41; Matthäi → Kuppelwerk | Strafbescheid V13, Vorkaufsrecht HMX-MSA-2057-01 |
| V15 | 2059-03-07 / 03-12 / 03-13 / 03-15 | delay_complaint / penalty_notice / amendment_offer / confirmation | Matthew Thomas 123 → Catherine Perry 308; Jason Armstrong 115 → Lopez 293 | HMX-CTR-2058-0131, HMX-SHP-2059-01094 |
| V16 | 2059-03-10 / 03-15 | breach_warning + amendment_offer / confirmation | Hülya Matthäi 41 → Kayla Cannon 332 | HMX-MSA-2057-01, HMX-CTR-2058-0139 |
| V17 | 2059-03-20 / 04-01 | counter_offer / contract_confirmation | Matthäi 41 → Kuppelwerk; Rörricht 38 | KHB-RV-2059-01 |
| V18 | 2059-03-20 / 04-01 | offer / contract_confirmation | Emberline → Matthew Thomas 123; Armstrong 115 | EFF-MSA-2059-01 |
| V19 | 2059-05-12 | offer (kalt) | Kometenpost → Tilman Christoph 49 | HMX-CTR-2059-0197 |
| V20 | 2059-05-20 | confidential_tip (wahr) | Outmark → Slavko Geisel 16 | historische Lizenz, Fund 52 |
| V21 | 2059-06-10 | rumor (offen) | Brandon Jones 445 → Ravenmoor Marktaufklärung | 8 wegen Geleitschutz gebrochene Verträge |
| **V22** | 2059-07-20 / 08-01 | offer / contract_confirmation | Aleksandra Koch 4 → Esther Bauer 170; Theodor Krause 1 / Roswitha van der Dussen 168 | FSP-RV-2059-01, **Schulden 22,94 / 24,22 Mio. CR** (K10) |
| V23 | 2059-07-25 / 08-20 | amendment_offer / confidential_tip | Henryk Ullmann 175 → Raureif; Esther Bauer 170 → Aleksandra Koch 4 | RVF-RV-2058-02 −6 %, Fund 52 |
| V24 | 2059-07-28 / 08-05 | protest / Antwort | Outmark-Vorstand → Theodor Krause 1 | Rivalität Outmark ↔ Feldspat |
| V25 | 2059-08-05 | penalty_notice | Lopez 293 → van der Dussen 168 | EKM-VTR-2059-0162 |
| V26 | 2059-08-27 / 09-03 / 09-10 | confidential_tip / protest / rumor | Carlos Osborne 29 → Ravenmoor; Tina Gould 23 → Ravenmoor-Vorstand; Nathan Hines 33 → Gould | Razzia 58 |
| **V27** | **2059-10-14** (K3) | payment_reminder (2.) | Pamela Stroh 169 → Mikhail Gotthard 2 | EKM-BST-2059-01903 + 12 weitere, **25.522.655,14 CR** |
| V28 | 2059-10-11 → 11-15 | delay_complaint → confidential_tip → termination_notice → offer → amendment_offer → amendment_rejection → contract_confirmation | Eberhardt 45 → Bauer 170; Polina Zahn 83 (`leaked_by`) → Emberline; Rörricht 38 → van der Dussen 168; Emberline → Eberhardt; Bauer → Matthäi 41; Rörricht → Bauer; EFF-MSA-2059-02 | EKM-VTR-2059-0167, EKM-RV-2057-03 |
| V29 | 2059-11-05 / 12-15 | internal_memo / offer (kalt) | Kaspar Täsche 43 → Rörricht 38; Morgengrund → Tilman Christoph 49 | Rivalität Isolde, Ernteausfälle 61/71 |
| V30 | 2059-11-29 / 12-02 / 12-08 | delay_complaint / Antwort / penalty_notice | Claire Rust 174 → Wayne Jacobson 302; Pamela Stroh 169 → Donald Morris 294 | HMX-CTR-2059-0242 |
| V31 | 2059-12-01 → 12-29 | Kette Aussetzung CCI (9 Schreiben) | Schuchhardt 178, van der Dussen 168, Dolores Mühle 171, Desiree Schwartz 299, Richard Chavez 120 → Josip Sölzer 172, Bauer 170, Cindervale → Graufalk | Ereignis 70, CCI-MSA-2057-01, GFW-RV-2057-02 |
| **V32** | **2059-03-29** (K5) | payment_reminder (3.) | Pamela Stroh 169 → Dawn Turner 118 | EKM-BST-2059-01408 (4,39 Mio., fällig 02-12) |
| V33 | 2059-12-18 / 12-29 | offer / offer_rejection | Esther Bauer 170 → Heinz Dieter Schmidtke 42; Schmidtke → Bauer | Entwurf EKM-VTR-2060-0230 |
| V34 | 2059-12-22 | amendment_offer (offen, dreiseitig: Geleit + Liegeplätze, K2) | Ravenmoor → David Hendricks 304, weitergeleitet an Bauer 170 | EKM-RV-2057-02 + RCS-MSA-2058-01, Piraten 74 |
| V35 | 2059-12-26 / 12-30 / 12-31 | delivery_notice / delay_notice / delay_complaint | Marijan Hörle 254 → Eric Adkins 307; Edward Bennett 370 → Bauer 170 | EKM-BST-2059-02343 |
| **V36** | **2059-12-31** (K6) | inquiry (Eilabruf) | **Kayla Cannon 332** → Graufalk | HMX-ORD-2059-01763/-01788, HMX-SHP-2059-01721/-01746 |
| V37 | 2059-12-28 | payment_reminder | Donald Morris 294 → Dawn Turner 118 | HMX-ORD-2059-01645 |
| V38 | 2059-12-30 | delay_notice | Dorothee Girschner 9 → Irmingard Scholl 179 | FSP-BST-2059-00111 |
| **V39** | **2059-08-28 / 09-02 / 09-12** (K1, B) | rumor (wahr, `leaked_by` 120) / breach_warning / Antwort | Richard Chavez 120 → Cindervale Marktaufklärung; Cindervale-Vorstand → van der Dussen 168 (cc Bauer 170); Bauer 170 → Cindervale | CVB-CTR-2059-0066, CCI-MSA-2057-01, Ereignisse 19/36 |
| **V40** | **2059-06-04** (A) | internal_memo (confidential) | Reimar Rörricht 38 → Lena Heß 40 | refers_to V14: Verdacht gegen Erkan Hesse 39 (entlassen 2059-06-11, Bestand). Das wahre Leck ist Täsche. |
| **V41** | **2058-11-20** (A) | confidential_tip (business, wahr) | Freddy Dörr 235 (`leaked_by`) → Graufalk Marktaufklärung | Ereignis 36 (2058-11-13), Rivalität graufalk → eisenkrone |

Geprüft: Alle neuen und geänderten Personen-Datums-Paare liegen in der Beschäftigungszeit (Hesse ist bis 2059-06-11
beschäftigt, van der Dussen ab 2059-07-07). Die Leck-Absender erfüllen die Regel: Täsche 55/61, Chavez 53/76,
Dörr 45/88, Zahn 55/88.

---

## 7. Widersprüche, Korrekturen, Namenskonflikte (R2)

| # | Problem | Lösung |
|---|---|---|
| 1 | B: JSON führt `helix → corvane` unter `partnerships` (48 feste), der Text nennt es optional | bleibt in `optional_partnerships` (p = 0,6), sonst verschiebt sich der Bestandsstrom |
| 2 | B: „12 von 12 Volumen-Auslösern“, in der eigenen Tabelle stehen 13 | **13** (selbst ausgezählt), QA-Sollwert 13 |
| 3 | B: `price_floor` (RVF-RV-2058-02) und `harvest_clause` (SGM-RV-2059-01) fehlen im JSON | wieder aufgenommen (wie Entscheidung 20.10. und A) |
| 4 | A: Ankerliste enthält `PKB-VTR-2058-0001`, das ist keine Bestandsnummer (A behauptet „57/57 vorhanden“) | gestrichen, **56 Verträge** + 9 Bestellungen + 2 Lieferungen + 31 Ereignisse + 49 Mitarbeiter |
| 5 | Hub-Gleichstand ohne `helix → corvane`: B behauptet eine Reihenfolge nach `company_id`, A sagt „nicht festgelegt“ | A hat recht. Die QA sortiert zusätzlich nach `company_id`, `kind="stable"`. |
| 6 | Δ6 macht Polina Zahn zur reinen Zeugin, V28 nutzt sie aber als Leck | Zahn erfüllt die Regel und bleibt Leck-Quelle für Lichtacker-Interna (`third_party_leaks`) |
| 7 | Namenskonflikt V39 (A- und B-Entwurf) | V39 = B. Die A-Vorgänge heißen V40 und V41. |
| 8 | B: K2 als Notiz im Nachtrag, A: als `berth_anchor_contracts` | Feldname von A (`anchor_contracts` = Geleit, `berth_anchor_contracts` = Andockstau) |
| 9 | Δ9 ändert ein Phase-1-Profil, B hat es nicht gesehen | angenommen: B hat die Rohstofflücke Aurelis selbst als Frage R2-3 gestellt. Medium erlaubt 4–6 Stationen, die Pflichtstationen sind dann 3. |

## 8. Umsetzung (Zuständigkeit unverändert)

1. Durchlauf 1 unverändert (6 Bestandsfirmen inkl. `OPTIONAL_PARTNERSHIPS`/`HISTORIC_PARTNERSHIPS`).
2. **Team A**, Durchlauf 2: eigener RNG/Faker, Archetyp-Filter, Profiländerungen (`profile_changes_new_firms`:
   Kuppelwerk `mining` Aurelis, Morgengrund `trade_hub` Isolde), Einstellungsgrenzen (`hire_date_caps_new_firms`),
   Vereinbarungen, Historie, Rivalitäten (`rivalry_details` mit Leck-Quellen/Zeugen), Verträge mit Rahmenregel und
   `exclusivity_filter_new_pairs`, QA 6/6/6 mit Bestandsvergleich über `qa_anchor_objects`.
3. **Team B**: `generate_framework_agreements` (82 Nachträge, Prüfwerte `expected_assigned_contracts`, 13 Auslöser,
   K9-Bedingung) und `generate_correspondence` (V1–V41 nach 6.3, QA nach 6.1).
4. Neue QA-Prüfungen: Zählung 2.3; ≥ 2 Paare nur indirekt (Soll 66); Hub large; 341 Zuordnungen; 13 Volumen-Auslöser;
   Scope mit Verbraucher (Δ3); keine Exklusivitätsverstöße neuer Verkäufer; Strafbescheide = `contract_penalties`;
   Mahn- und Reihenfolgeregeln; Leck-Regel.
