# Phase 2 – Entscheidung des Schiedsrichters: Verknüpfung der 18 Firmen

Stand: 20.10.2026 · Grundlage: `phase1_team_a.md`, `phase1_team_b.md`, `phase2_vorschlag_team_a.md`,
`phase2_vorschlag_team_b.md`, `NACHRICHTEN.md`, `generate_space_trading_data.py` (Seed 42) und eigene Abfragen auf den
Bestand `/home/user/bestand/space_trading_game_bestand.db` (nur lesend). Das maschinenlesbare Ergebnis steht in
`planung/verknuepfungen.json`. Alle Zählungen, Strafbeträge, Zuordnungen und Mitarbeiterdaten unten habe ich selbst
nachgerechnet (Skripte über die JSON-Datei und die Bestands-DB).

## 0. Kurzfassung

| Thema | Entscheidung |
|---|---|
| Vereinbarungen | **48 aktive**: die 13 Blueprint-Kanten des Bestands, `helix → corvane` (bleibt optional, p = 0,6, im Bestand aktiv) und 34 neue Kanten. Basis ist die Liste von Team A, die Team B ohne `emberline → lichtacker` ebenfalls hat. Alle 18 Firmen liegen im Bereich ihrer Größe. |
| Netz | zusammenhängend, 38 von 153 Paaren direkt, **66 nur über einen gemeinsamen Partner**, 45 mit Abstand 3, 4 mit Abstand 4. Hub ist Helix (large, 7 Partner, 10 Vereinbarungen). |
| Historie | 7 beendete Partnerschaften (Team A: alle von Team B plus `cindervale → helix` und `emberline → eisenkrone`) |
| Rivalitäten | 12 (4 Bestand, 8 neu). Neu ist nur der Typ `armed_conflict`, dazu 2 Text-Overrides. Alle neuen Rivalitäten haben feste Werte. |
| Rahmenverträge | **21** (7 für Bestandspaare, 14 für neue Paare), 78 Nachträge, davon 17 zum Stichtag offen (`proposed`) und 1 abgelehnt. **341 der 475** Abrufverträge des Bestands werden zugeordnet (2.309 Mio. CR). Außerhalb bleiben bewusst 134. |
| Schriftverkehr | Tabelle `correspondence` mit 20 Briefarten, Schema im Kern von Team B, Leck-Felder und -Formel von Team A. 38 Vorgänge sind an echte Bestandsobjekte geankert, Absender und Empfänger am Versanddatum beschäftigt (geprüft). |

Leitlinie: **Echte Brüche im Bestand erzeugen die neuen Partnerschaften.** Für die Bestandspaare habe ich die
Teamwerte nur übernommen, wenn sie den Bestandsdaten nicht widersprechen. Wo ein Vorschlag mit dem Bestand kollidierte,
habe ich ihn angepasst (Abschnitt 7).

---

## 1. Bewertung

Punkte 1–5 (5 = am besten). Grundlage: eigene Prüfung gegen Skript und Bestands-DB.

| Bereich | Kriterium | Team A | Team B | Begründung |
|---|---|---:|---:|---|
| Vereinbarungen | Plausibilität Warenflüsse | 5 | 4 | Die Listen sind bis auf eine Kante gleich. A ergänzt `emberline → lichtacker`: Lichtacker kündigt nach drei gebrochenen Energieverträgen (EKM-VTR-2058-0099, -0105, -2059-0167) und zwei Stornierungen (EKM-VTR-2059-0156, -0169) und braucht einen neuen Lieferanten. |
| | Regeltreue (Zählregel, Hub, Netz) | 5 | 5 | Beide nachgezählt: korrekt (A 48, B 47). |
| | Spielwert | 5 | 4 | Bei A wird die Kette Bruch → Teilkündigung → neuer Lieferant in Routen und Verträgen sichtbar. Bei B gibt es nur ein Kaltangebot ohne Datenfolge. |
| | Umsetzbarkeit | 5 | 5 | Beide nur in Richtung „neue Firma → Bestandsfirma“, keine neuen Zufallszüge im Bestandsstrom |
| Historie | Datenbezug | 5 | 4 | A hat 2 zusätzliche, gut verankerte Einträge (Lizenzverlust Helix 2054 als Ursache der Rivalität in Sol; Helium-3 für Hande bis 2056). Alle Daten sind gegen `founded_year` und das Datenfenster geprüft. |
| Rivalitäten | Datenbezug / Umsetzbarkeit | 4 | 5 | Die Listen sind gleich. B setzt feste `since`-, `intensity`- und `espionage_risk`-Werte, A nur feste Daten. Übernommen: B, für die Team-A-Rivalitäten Werte vom Schiedsrichter. |
| Rahmenverträge | Konsistenz mit Bestand | 3 | 5 | B: Die Regeln reproduzieren den Bestand exakt (alle Volumen-Auslöser stimmen, nur ein Nummernfehler). A: `EKM-RV` Eisenkrone → Helix mit Beginn am 2057-03-01 lässt EKM-VTR-2057-0002 heraus. Drei Exklusivitäten widersprechen dem Bestand oder einander (Abschnitt 7). |
| | Spielwert | 5 | 4 | A: Teilkündigung, Aussetzung, Wettbewerbs- und Geheimhaltungsklauseln. B: offene, dreiseitige Geleitschutzverhandlung zum Spielstart und Vorkaufsrechte mit Abmahnungen. |
| | Umsetzbarkeit | 4 | 5 | B: klare Regel, wann ein Rahmen entsteht, ein Nachtrag je Datensatz. A: detailliertere Nachtragstypen und Regel-Nachträge mit `effective_date: "rule"`. |
| Schriftverkehr | Schema | 4 | 5 | B: `read_at` (Posteingang), `tone`, `recipient_customer_id`, `sender_station_id`. A: `leak_status`, `leaked_by/to`, Leckformel. Beide werden vereinigt. |
| | Datenkorrektheit Anker | 5 | 3 | B adressiert 3 Schreiben an Personen, die zu diesem Datum noch nicht eingestellt waren (K10, K13, K24). A hat das gefunden. |
| | Mengengerüst | 3 | 4 | A erzeugt 743 Vertragsbestätigungen als Füllmasse. B ist schlanker. Übernommen: B mit Bestätigungen nur für Rahmen und `exclusive_supply`. |

---

## 2. Vereinbarungen (aktiv, gerichtet Verkäufer → Käufer)

### 2.1 Was übernommen wurde

- **Bestand (14, unverändert)**: 13 Blueprint-Kanten plus `helix → corvane` (logistics_partnership). Die Kante bleibt
  in `OPTIONAL_PARTNERSHIPS` mit p = 0,6. Würde sie fest, entfiele ein `rng.random()`-Zug im Bestandsstrom (Argument
  von Team A).
- **Neue Firma → Bestand (7)**: `graufalk → helix`, `cindervale → eisenkrone`, `kuppelwerk → lichtacker`,
  `emberline → corvane`, **`emberline → lichtacker`** (Team A), `raureif → eisenkrone`, `ravenmoor → helix`.
- **Innerhalb Team A (12)** und **innerhalb Team B (12)**: in beiden Vorschlägen gleich.
- **Teamübergreifend (3)**: `kuppelwerk → pionierwerk`, `second_hull → graufalk`, `graufalk → ravenmoor`.
- Nicht aufgenommen: `raureif → emberline` (beide Teams streichen die Kante: Vaskar–Pellora ≈ 820 Einheiten, und
  Emberline fördert Helium-3 selbst).

**Warum `emberline → lichtacker`**: Im Bestand liefert Eisenkrone Energie an die Agrarstation Seip. Diese Lieferungen
brechen dreimal (Strafen 219.444,96 + 60.263,34 + 58.589,66 CR), zwei weitere Energieverträge 2059 werden storniert.
Zusätzlich springt Helix schon ab 2059-09-18 mit `HMX-CTR-2059-0257` (Plasmagas an Seip) ein. Mit Emberline ergibt
sich ein Dreikampf um die Energie in Myrrhen, der in den Daten sichtbar ist. Lichtacker (6/6) und Emberline (6/6) sind
damit voll. Das ist zulässig.

### 2.2 Verbraucherprüfung

Für jede der 34 neuen Kanten habe ich die Kategorien des Verkäufers (`category_weights`) gegen `CATEGORY_CONSUMERS` und
die **sicheren** Stationstypen des Käufers geprüft: Bestandsstationen aus der DB, bei neuen Firmen nur
`required_stations`. Jede Kante hat mindestens 52 % des Warengewichts mit passendem Verbraucher. Den niedrigsten Wert
hat `pionierwerk → morgengrund` (Industriegüter, Energie und Medizin an eine Agrarstation). Knappster Fall bei den
Stationen ist `cindervale → eisenkrone`: Technik geht dort nur an die 3 Bergbaustationen. Für ≥ 4 Partnerrouten reicht
das, weil `plan_markets` Produkt-Stations-Paare zählt.

### 2.3 Finale Zählung je Firma (nachgezählt, beide Richtungen)

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
| **Summe** | | **96 = 2 × 48** | 48 | 48 | | | | |

- **Hub**: Die QA sortiert nach direkten Partnern und dann nach Vereinbarungen. Ergebnis: Helix 7/10 vor Graufalk 7/9
  und Ravenmoor 7/8, alle drei sind large. Würfelt ein anderer Seed `helix → corvane` nicht, bleibt Helix bei 7 Partnern
  (über `corvane → helix`) und 9 Vereinbarungen und damit weiter vorn.
- **Jede Firma hat ≥ 1 ausgehende Vereinbarung** (Minimum 1: Driftwood, Kometenpost).
- **Unvollständig**: 38/153 Paare sind direkt verbunden. Nur indirekt verbunden sind 66 Paare, z. B. Feldspat ↔ Raureif
  (über Eisenkrone), Driftwood ↔ Ravenmoor (über Helix), Lichtacker ↔ Pionierwerk (über Kuppelwerk), Helix ↔
  Morgengrund (über Ravenmoor). Abstand 4: Driftwood ↔ Kometenpost, Kometenpost ↔ Pionierwerk/Outmark/Morgengrund.
- **Reserve für Spielereignisse**: Driftwood 2, Cindervale 3, Outmark 3, Kuppelwerk 2, Raureif 2, Pionierwerk 2,
  Ravenmoor 2, Eisenkrone 1, Graufalk 1. Voll sind Helix, Lichtacker, Corvane, Emberline und die kleinen Firmen außer
  Driftwood.

### 2.4 Auswirkung auf die Bestandsfirmen (nachvollziehbar)

Stammdaten bleiben unverändert. Neu ist nur die Rolle als **Käufer** neuer Lieferanten: Helix (+Graufalk, +Ravenmoor),
Eisenkrone (+Cindervale, +Raureif), Lichtacker (+Kuppelwerk, +Emberline), Corvane (+Emberline). Die neuen Routen,
Verträge und Bestellungen gehören den neuen Verkäufern. Bestandsstationen sind nur zusätzliche Ziele. Die Finanzen der
Bestandsfirmen ändern sich nicht, weil Einkäufe bei Partnern im Modell beim Käufer nicht als Kosten gebucht werden.
Diese bekannte Unstimmigkeit (Hinweis von Team B) bleibt bewusst stehen. Neue `trade_partnerships`-Zeilen werden **nach**
der historischen Bestandszeile 15 (`corvane → driftwood`) eingefügt (Hinweis von Team B), damit die
`partnership_id` 1–15 gleich bleiben.

---

## 3. Historische Partnerschaften (7, feste Daten)

| Verkäufer → Käufer | Typ | Zeitraum | Quelle | Prüfung |
|---|---|---|---|---|
| corvane → driftwood | supply | 2057-04-27 – 2058-07-17 | Bestand (Bestandsstrom) | unverändert |
| eisenkrone → graufalk | supply | 2039-01-01 – 2049-06-30 | A | Beginn ≥ Gründung + 1 (EKM 2033, GFW ≤ 2038) |
| cindervale → helix | licensing | 2041-04-01 – 2054-03-31 | A (übernommen) | HMX 2036, CCI ≤ 2034; die Rivalität in Sol beginnt am Tag danach |
| lichtacker → pionierwerk | supply | 2045-03-01 – 2053-06-30 | B | LAK 2044 |
| emberline → eisenkrone | supply | 2047-02-01 – 2056-06-30 | A (übernommen) | EFF ≤ 2046; Ende ≥ 120 Tage vor 2057-01-01 |
| outmark → feldspat | licensing | 2055-02-01 – 2058-06-30 | B | FSP 2054; Ende vor 2058-09-03 |
| driftwood → second_hull | consignment | 2057-05-01 – 2058-07-01 | B | DWS 2056; Ende zwei Tage nach Razzia 26 |

Keine Kollision mit `UNIQUE(company_id, partner_company_id, relationship_type)`: Kein Paar ist zugleich historisch
und aktiv mit demselben Typ. `trust_level` (3–15) und `contract_volume` (0,8–4 Mio. CR) würfelt der Erweiterungsstrom.

## 4. Rivalitäten (12)

Die 4 Bestandsrivalitäten bleiben im Bestandsstrom. Für die 8 neuen sind alle Werte fest (keine Würfel):

| Firma → Rivale | Typ | System | seit | Intensität / Spionage | Anker (Bestand) | Informanten (ID) |
|---|---|---|---|---|---|---|
| graufalk → eisenkrone | market_dominance | halcyon | 2049-07-01 | 70 / 55 | KI-Ausfälle Förster 19/36/70, EKM-VTR-2057-0064 | Esther Bauer 170, Annekatrin Schuchhardt 178 |
| cindervale → helix | market_dominance | sol | 2054-04-01 | 65 / 50 | Nachfrageschübe 3/24, HMX-CTR-2057-0050, -2058-0121 | Desiree Schwartz 299 (ab 2059-11-24), Richard Chavez 120 |
| emberline → eisenkrone | resource_competition + Text-Override | myrrhen | 2058-08-15 | 55 / 40 | EKM-VTR-2058-0099, -0105, -2059-0167 | Polina Zahn 83, Hans-Werner Eberhardt 45 |
| lichtacker → pionierwerk | territorial_claims + Text-Override | isolde | 2053-07-01 | 60 / 55 | Ende der historischen Lieferung | Kaspar Täsche 43 |
| ravenmoor → driftwood | **armed_conflict** (neu, 60–90) | nyx | 2058-06-30 | 85 / 70 | Razzien 26/58, Piraten 45/54/57/67 | Carlos Osborne 29, Nathan Hines 33 |
| outmark → feldspat | territorial_claims | brennus | 2059-07-14 | 65 / 80 | Rohstofffund 52 Becker | Slavko Geisel 16 |
| ravenmoor → helix | market_dominance | kharon | 2057-11-17 | 55 / 45 | Piraten 16, Razzia 26 | Wayne Jacobson 302, Tyler Garcia 395, Brandon Jones 445 |
| second_hull → driftwood | territorial_claims | nyx | 2058-07-01 | 50 / 40 | Piraten 54, Ende der Kommission | Douglas Lawson 27 |

Die Werte der drei Team-A-Rivalitäten hat der Schiedsrichter festgelegt, innerhalb der Bereiche aus
`generate_rivalries`. Die Team-B-Werte sind übernommen. `UNIQUE(company_id, rival_company_id)` ist eingehalten.
Statt eines Typs `price_war` gibt es `RIVALRY_TEXT_OVERRIDES` (beide Teams einverstanden).

---

## 5. Rahmenverträge (21)

### 5.1 Schema (vereinigt)

- Tabellen `framework_agreements`, `framework_agreement_scope` (Name von B), `framework_amendments`, dazu die Spalte
  `contracts.framework_agreement_id`. Spaltennamen für Verkäufer und Käufer sind **`company_id`/`partner_company_id`**,
  wie in `contracts` und `trade_partnerships`. Die Zuordnungsregel ist dann ein direkter Join.
- Enums (vereinigt): `price_formula` fixed/index_linked/cost_plus/market_minus (B: `spot_discount` = `market_minus`);
  `indexation` none/category_price_index/fuel_index/risk_index; `exclusivity`
  none/right_of_first_refusal/buyer_exclusive/seller_exclusive/mutual/regional_exclusive (B: `category_exclusive`
  wird zu `buyer_exclusive` mit Scope, `system_exclusive` zu `regional_exclusive`); Nachtragsstatus
  proposed/signed/rejected/withdrawn; Rahmenstatus negotiating/active/suspended/expired/terminated.
- 17 Nachtragstypen: alle von A plus `volume_reduction` und `product_removal` von B. `termination_notice` ist kein
  Nachtrag, sondern ein Schreiben.
- Zuordnungsregel (beide Teams gleich, deterministisch): gleiches Paar, Typ `framework`/`recurring_supply`/
  `exclusive_supply`, Beginn zwischen Rahmenbeginn und dem zu diesem Zeitpunkt gültigen Ende, Kategorie bzw. Archetyp am
  Beginn im Scope.
- Regel-Nachträge (Monatserster vor dem ersten Vertrag einer Kategorie; über 90 % Auslastung führen zur Erhöhung zum
  Monatsersten des auslösenden Vertrags, 2060 als `proposed`; Verlängerung 60 Tage vor Ablauf).
- Neue Paare: Vor Rahmenbeginn gibt es nur spot/emergency_supply/consignment (A), Rahmentypen nur für Waren im Scope.
- Nummern stehen fest im JSON. Die Nachträge werden nach `proposed_date` nummeriert.

### 5.2 Bestandspaare (7): Nachweis am Bestand

| Nr. | Paar | Basis | Deckel zum Stichtag | zugeordnet | Summe (ohne storniert) | Auslastung | Herkunft / wichtigste Nachträge |
|---|---|---:|---:|---:|---:|---:|---|
| HMX-MSA-2057-01 | helix → lichtacker | 250 | 550 | 54 | 423,6 | 77 % | B (Vorkaufsrecht Industriegüter, Wegfall 2059-03-15 nach 3 Verbundstahl-Brüchen) + A (Strafklausel 2058-03-14) |
| HMX-MSA-2057-02 | helix → corvane | 300 | 600 (750 angeboten) | 68 | 549,4 | 92 % | B (Helium-3 heraus 2059-03-15) + A (Energie käuferexklusiv 2057-05 bis 2059-03-15). Geprüft: Corvane bezieht Energie im Bestand nur von Helix. |
| HMX-MSA-2057-03 | helix → eisenkrone | 300 | 450 (550 angeboten) | 75 | 438,7 | 97 % | B (Senkung auf 250 nach Ereignis 19; Einbruch 2058: 53,5 statt 155,2 Mio. CR). Auslöser korrigiert: HMX-CTR-2059-**0236** statt -0235. |
| EKM-RV-2057-01 | eisenkrone → corvane | 350 | 450 (550 angeboten) | 65 | 440,9 | 98 % | B (Vorkaufsrecht Rohstoffe → Abmahnung wegen LAK-VTR-2058-0033) + A (Service-Level-Nachtrag offen nach EKM-VTR-2059-0160) |
| EKM-RV-2057-02 | eisenkrone → helix | 200 | 300 | 39 | 275,9 | 92 % | B (Beginn 2057-01-01, damit liegt EKM-VTR-2057-0002 im Rahmen) + A (Strafklausel nach EKM-VTR-2057-0017, 303.807,21 CR). Geleitschutzklausel mit Ravenmoor **offen** (B). |
| EKM-RV-2057-03 | eisenkrone → lichtacker | 150 | 200 | 35 | 178,0 | 89 % | **Mischung**: Teilkündigung Energie (A, Zugang 2059-10-20, wirksam 2060-01-18) und Rettungsangebot −5 % (B), von Lichtacker abgelehnt. Entwurf EKM-VTR-2060-0230 liegt sichtbar außerhalb des Rahmens. |
| FSP-RV-2059-01 | feldspat → eisenkrone | 12 | 12 (20 angeboten) | 5 | 2,6 | 22 % | A, aber mit **Vorkaufsrecht** statt Verkäuferexklusivität. +12 % nach den Nachfrageschüben 65/66. Erzählt die 25,5 Mio. CR Schulden. |

Summe: **341 von 475** Abrufverträgen, 2.309 Mio. CR. Außerhalb bleiben 131 Verträge von Paaren ohne Rahmen
(`eisenkrone → feldspat` wie bei B ohne Rahmen, dazu die vier kleinen Lieferpaare), FSP-VTR-2059-0001/-0005 (vor
Rahmenbeginn) und EKM-VTR-2060-0230 (nach der Teilkündigung). Alle anderen Spalten der Bestandsverträge bleiben gleich.

### 5.3 Neue Paare (14)

| Nr. | Paar | Beginn, Laufzeit | Basis | Preis / Exklusivität | Herkunft, Änderung |
|---|---|---|---:|---|---|
| GFW-RV-2057-01 | graufalk → helix | 2057-01-01, 48 M | 180 | index_linked | A-Beginn, B-Laufzeit. +60 am 2058-12-20 (HMX-CTR-2058-0173), Eilabrufklausel offen (B) |
| GFW-RV-2057-02 | graufalk → cindervale | 2057-01-01, 60 M | 220 | cost_plus / mutual **drive_parts** | A. Exklusivität von KI-Kernen auf Triebwerksteile/Navigationscomputer verlegt; Geheimhaltung offen |
| GFW-RV-2058-01 | graufalk → ravenmoor | 2058-07-15, 36 M | 90 | index_linked / Vorkaufsrecht hull_plating Kharon | A, statt Verkäuferexklusivität (Graufalk liefert Rumpfteile auch an Helix in Kharon) |
| CCI-MSA-2057-01 | cindervale → eisenkrone | 2057-01-01, 48 M | 120 | fixed / Technik käuferexklusiv Halcyon | B-Werte, A-Laufzeit und **Aussetzung** 2059-12-15 (Status `suspended`). Die Kündigung wird nur angedroht. |
| KHB-RV-2058-01 | kuppelwerk → pionierwerk | 2058-06-01, 36 M | 70 | cost_plus / Habitatmodule verkäuferexklusiv Isolde | B-Daten, A-Preisformel und -Exklusivität; Erweiterung um Serravel 2059-10-01 |
| KHB-RV-2059-01 | kuppelwerk → lichtacker | **2059-04-01**, 24 M | 30 | cost_plus | Beginn nach Wegfall des Helix-Vorkaufsrechts (B), Habitatmodule nach Quarantäne 53 (A), Myrrhen-Exklusivität offen |
| EFF-MSA-2059-01 | emberline → corvane | 2059-04-01, 24 M | 40 | index_linked (Treibstoff) | Beginn B, höhere Gewalt nach Quarantäne 59 (A), Helium-3-Exklusivität offen (B) |
| EFF-MSA-2059-02 | emberline → lichtacker | 2059-11-15, 24 M | 18 | index_linked / Vorkaufsrecht Energie Myrrhen ab 2060-01-18 | A, statt Käuferexklusivität (HMX-CTR-2059-0257 läuft bis 2060-03-30) |
| RCS-MSA-2058-01 | ravenmoor → helix | 2058-08-01, 36 M | 90 | cost_plus 15 % + risk_index / Sicherheitsgüter Kharon | B (vom Gegner zum Schutzpartner nach Razzia 26). Dreiseitige Geleitklausel und Ausweitung auf Kharon Landing IV offen. |
| RVF-RV-2058-01 | raureif → pionierwerk | 2058-01-01, 36 M | 80 | index_linked / Wasser- und Stickstoffeis Isolde | B |
| RVF-RV-2058-02 | raureif → eisenkrone | 2058-03-01, 24 M | 45 | index_linked, Mindestpreis | B (−6 % nach Fund 52), Verlängerung offen |
| OSP-MSA-2058-01 | outmark → pionierwerk | 2058-02-01, 36 M | 25 | fixed / Vermessungsdaten Serravel ab 2059-08-15 | B |
| SGM-RV-2059-01 | morgengrund → pionierwerk | 2059-01-01, 12 M + Auto-Verlängerung | 5 | fixed + Ernteklausel | B |
| SGM-RV-2059-02 | morgengrund → ravenmoor | 2059-03-01, 12 M | 6 | fixed + Ernteausfallklausel | A (Nahrungslücke Kharon: 0 Angebote bei 20 Nachfragen) |

Ohne Rahmen bleiben alle Kommissions- und die übrigen Lizenzbeziehungen sowie kleine Lieferanten (Driftwood,
Lanternfish, Kometenpost, Second Hull). Dort macht der Spieler Spot-Geschäfte.

---

## 6. Schriftverkehr

### 6.1 Entscheidung zum Design

- **Schema**: B als Basis (`read_at`, `tone`, `response_required`, `trust_effect`, `sender_station_id`,
  `recipient_customer_id`, `is_accurate`). Von A kommen `leak_status`, `leaked_by_employee_id` und
  `leaked_to_company_id`. A's `source_correspondence_id` heißt `refers_to_correspondence_id`. Aktenzeichen
  `{SKU}-KOR/COR-{Jahr}-{nnnnn}`.
- **20 Briefarten**: B's 17 plus `delay_notice`, `suspension_notice` (A) und neu `offer_rejection` (Absage auf ein
  Angebot oder einen Vertragsentwurf; A hatte dafür fälschlich `amendment_rejection`). Zuordnung: `quotation` =
  `offer`, `negotiation` = `counter_offer`, `amendment_acceptance` = `amendment_confirmation`.
- **Regeln**: Strafbescheid = `late_days × penalty_per_day` wie `generate_financials`, Summe je Firma und Monat =
  `contract_penalties` (QA, A). Ab 250.000 CR unterschreibt der Vorstand (B), sonst schreibt die Finanzabteilung an die
  Finanzabteilung (A). Mahnstufen Fälligkeit +3..7/+21/+45 Tage, nur bis zum Stichtag. Verzugsbeschwerde ab 48 h (B).
  Vertragsbestätigung nur für Rahmen und `exclusive_supply` (96 im Bestand) statt für alle 743 Verträge.
- **Spionage**: Leck-Wahrscheinlichkeit `espionage_risk/100 × bribe/100 × (1 − loyalty/150)` (A). `confidentiality`
  entspricht `intel_access_level` 0–3 (B). Wahrheitsgehalt: 30 % wahr, 50 % offen, 20 % falsch.
- **Mengen**: ca. 850 Schreiben zu Bestandsobjekten, ca. 2.200–2.800 für alle 18 Firmen.

### 6.2 Geprüfte Strafbeträge (Formel aus `generate_financials`, nachgerechnet)

HMX-CTR-2058-0159: 6 × 108.860,36 = **653.162,16** · HMX-CTR-2058-0131: 5 × 66.501,79 = **332.508,95** ·
EKM-VTR-2059-0162: 5 × 62.833,32 = **314.166,60** · EKM-VTR-2057-0017: 3 Tage = **303.807,21** · EKM-VTR-2058-0099:
**219.444,96** · HMX-CTR-2058-0139: **129.876,24** · HMX-CTR-2059-0197: **101.141,50** · EKM-VTR-2058-0105: **60.263,34**
· HMX-CTR-2059-0242: **60.719,68** · EKM-VTR-2059-0167: **58.589,66** · HMX-CTR-2057-0043: **47.848,75** ·
HMX-CTR-2058-0173: **43.066,84** CR.

### 6.3 Verankerte Vorgänge (verbindlich, IDs = `employee_id`, alle am Datum beschäftigt)

| # | Datum | Art | Absender → Empfänger | Bezug | Quelle |
|---|---|---|---|---|---|
| V1 | 2057-08-28 / 09-11 / 09-27 | payment_reminder 1–3 | Pamela Stroh 169 → **Mikhail Gotthard 2** | EKM-BST-2057-00352 (4,79 Mio.) | B K24, Empfänger korrigiert |
| V2 | 2057-12-20 | penalty_notice + amendment_offer | Elizabeth Lopez 293 → Esther Bauer 170 | EKM-VTR-2057-0017, EKM-RV-2057-02 | A |
| V3 | 2058-02-10 / 03-01 | breach_warning / amendment_confirmation | Annekatrin Schuchhardt 178 → Cindervale Partnerbetreuung | Ereignis 19, CCI-MSA-2057-01 | B K13 |
| V4 | 2058-02-15 | amendment_offer (Volumensenkung) | Esther Bauer 170 → Kayla Cannon 332 | HMX-MSA-2057-03, Ereignis 19 | B |
| V5 | 2058-04-01 | termination_notice | Second Hull → Erin Cisneros 26 | historische Kommission, Ende 2058-07-01 | B K27 |
| V6 | 2058-07-02 | internal_memo | Wayne Jacobson 302 → Elizabeth Lopez 293 | Ereignis 26 | B K1 |
| V7 | 2058-07-15 → 07-25 → 08-01 | offer → counter_offer → contract_confirmation | Ravenmoor → David Hendricks 304; Lopez 293 | RCS-MSA-2058-01 | B K2 |
| V8 | 2058-08-19 / 08-28 | delay_complaint / penalty_notice | Hans-Werner Eberhardt 45 → Irmingard Scholl 179; Lena Heß 40 → **Pamela Stroh 169** | EKM-VTR-2058-0099 | B K10, Empfänger korrigiert |
| V9 | 2058-08-20 / 10-05 | breach_warning / Antwort | Esther Bauer 170 → John Aguirre 119 | EKM-RV-2057-01, LAK-VTR-2058-0033, Storno LAK-VTR-2058-0039 | B K4 |
| V10 | 2058-09-12 | rumor (offen) | Erin Cisneros 26 → Elizabeth Lopez 293 | Rivalität Ravenmoor ↔ Helix | B K3 |
| V11 | 2058-11-20 | amendment_offer (−8 %) | Cindervale → **Esther Bauer 170** | Ereignis 36 | B K13, Empfänger korrigiert |
| V12 | 2058-12-16 / 12-20 | amendment_offer / confirmation | Kayla Cannon 332 → Graufalk | GFW-RV-2057-01 +60, HMX-CTR-2058-0173 | A |
| V13 | 2059-01-18 / 01-25 | delay_complaint / penalty_notice | Toralf Gerlach 47 → Kayla Cannon 332; Reimar Rörricht 38 → Lopez 293 | HMX-CTR-2058-0159, HMX-SHP-2059-01012 (+147 h) | A + B |
| V14 | 2059-01-20 / 01-28 / 02-05 | rumor (wahr) / offer / offer_rejection | Erkan Hesse 39 → Kuppelwerk; Kuppelwerk → Hülya Matthäi 41; Matthäi → Kuppelwerk (Vorkaufsrecht Helix) | Strafbescheid V13 | A, Absage neu |
| V15 | 2059-03-07 / 03-12 / 03-13 / 03-15 | delay_complaint / penalty_notice / amendment_offer / confirmation | Matthew Thomas 123 → Catherine Perry 308; Jason Armstrong 115 → Lopez 293 | HMX-CTR-2058-0131, HMX-SHP-2059-01094; Helium-3 heraus, Energie-Exklusivität aufgehoben | A + B |
| V16 | 2059-03-10 / 03-15 | breach_warning + amendment_offer / confirmation | Hülya Matthäi 41 → Kayla Cannon 332 | HMX-MSA-2057-01, HMX-CTR-2058-0139 | B K6 |
| V17 | 2059-03-20 / 04-01 | counter_offer / contract_confirmation | Matthäi 41 → Kuppelwerk; Rörricht 38 | KHB-RV-2059-01 | B K7 |
| V18 | 2059-03-20 / 04-01 | offer / contract_confirmation | Emberline → Matthew Thomas 123; Armstrong 115 | EFF-MSA-2059-01 | A + B K9 |
| V19 | 2059-05-12 | offer (kalt) | Kometenpost → Tilman Christoph 49 | HMX-CTR-2059-0197 (101.141,50 CR) | A |
| V20 | 2059-05-20 | confidential_tip (wahr) | Outmark → Slavko Geisel 16 | historische Lizenz, Fund 52 | B K21 |
| V21 | 2059-06-10 | rumor (offen) | Brandon Jones 445 → Ravenmoor Marktaufklärung | 8 wegen Geleitschutz gebrochene Verträge | A, Zweck: Vorbereitung der dreiseitigen Klausel |
| V22 | 2059-07-20 / 08-01 | offer / contract_confirmation | Aleksandra Koch 4 → Esther Bauer 170; Theodor Krause 1 / Roswitha van der Dussen 168 | FSP-RV-2059-01 | A |
| V23 | 2059-07-25 / 08-20 | amendment_offer / confidential_tip | Henryk Ullmann 175 → Raureif; Esther Bauer 170 → Aleksandra Koch 4 | RVF-RV-2058-02 −6 %, Fund 52 | B K23 |
| V24 | 2059-07-28 / 08-05 | protest / Antwort | Outmark-Vorstand → Theodor Krause 1 | Rivalität Outmark ↔ Feldspat | B K22 |
| V25 | 2059-08-05 | penalty_notice | **Lopez 293 → van der Dussen 168** | EKM-VTR-2059-0162 (314.166,60) | A, Absender nach 250k-Regel |
| V26 | 2059-08-27 / 09-03 / 09-10 | confidential_tip (wahr) / protest / rumor (offen) | Carlos Osborne 29 → Ravenmoor; Tina Gould 23 → Ravenmoor-Vorstand; Nathan Hines 33 → Gould | Razzia 58 | B K19/K20 |
| V27 | 2059-09-10 | payment_reminder (2.) | Pamela Stroh 169 → Mikhail Gotthard 2 | EKM-BST-2059-01903 + 12 weitere (25,5 Mio.) | A |
| V28 | 2059-10-11 → 11-15 | delay_complaint → confidential_tip → termination_notice → offer → amendment_offer → amendment_rejection → contract_confirmation | Eberhardt 45 → Bauer 170 (10-11); Polina Zahn 83 → Emberline (10-14); Rörricht 38 → van der Dussen 168 (10-20, Teilkündigung); Emberline → Eberhardt (10-20); Bauer 170 → Matthäi 41 (10-28, −5 %); Rörricht 38 → Bauer (11-10, Absage); EFF-MSA-2059-02 (11-15) | EKM-VTR-2059-0167, EKM-RV-2057-03 | **Mischung A + B** |
| V29 | 2059-11-05 / 12-15 | internal_memo / offer (kalt) | Kaspar Täsche 43 → Rörricht 38; Morgengrund → Tilman Christoph 49 | Rivalität Isolde; Ernteausfälle 61/71 | B K26 |
| V30 | 2059-11-29 / 12-02 / 12-08 | delay_complaint / Antwort / penalty_notice | Claire Rust 174 → Wayne Jacobson 302; Pamela Stroh 169 → Donald Morris 294 | HMX-CTR-2059-0242 (60.719,68) | B K15 |
| V31 | 2059-12-01 → 12-29 | internal_memo, termination_notice (Androhung), internal_memo, rumor, rumor, suspension_notice, internal_memo, rumor, amendment_offer | Schuchhardt 178 → vdD 168 (12-01); vdD → Cindervale (12-05); Dolores Mühle 171 → vdD (12-10); Desiree Schwartz 299 → Cindervale (12-12); Richard Chavez 120 → Josip Sölzer 172 (12-14); vdD → Cindervale (12-15); Mühle → vdD (12-20); Bauer 170 → Graufalk (12-27); Cindervale → Graufalk (12-29, Geheimhaltung, offen) | Ereignis 70, CCI-MSA-2057-01, GFW-RV-2057-02 | A + B, Reihenfolge korrigiert |
| V32 | 2059-12-05 | payment_reminder (3.) | Pamela Stroh 169 → Dawn Turner 118 | EKM-BST-2059-01408 (4,39 Mio.) | A |
| V33 | 2059-12-18 / 12-29 | offer / offer_rejection | Esther Bauer 170 → Heinz Dieter Schmidtke 42; Schmidtke → Bauer | Entwurf EKM-VTR-2060-0230 | A, Briefart korrigiert |
| V34 | 2059-12-22 | amendment_offer (offen, dreiseitig) | Ravenmoor → David Hendricks 304, weitergeleitet an Bauer 170 | EKM-RV-2057-02 + RCS-MSA-2058-01, Piraten 74 | B K16 |
| V35 | 2059-12-26 / 12-30 / 12-31 | delivery_notice / delay_notice / delay_complaint (Vorbehalt) | Marijan Hörle 254 → Eric Adkins 307; Edward Bennett 370 → Bauer 170 | EKM-BST-2059-02343 (offen, delayed) | A + B |
| V36 | 2059-12-28 | inquiry | Kurt Sullivan 301 → Graufalk | HMX-ORD-2059-01763/-01788 | B K18 |
| V37 | 2059-12-28 | payment_reminder | Donald Morris 294 → Dawn Turner 118 | HMX-ORD-2059-01645 (3,78 Mio.) | B K25, Finanzen an Finanzen |
| V38 | 2059-12-30 | delay_notice | Dorothee Girschner 9 → Irmingard Scholl 179 | FSP-BST-2059-00111 (offen) | A |

Neue Firmen erscheinen mit ihrer Rolle (Partnerbetreuung, Vorstand, Marktaufklärung). Ihre Mitarbeiter entstehen erst
im zweiten Durchlauf.

---

## 7. Widersprüche, Korrekturen, Namenskonflikte

| # | Problem | Lösung |
|---|---|---|
| 1 | B adressiert Schreiben an Roswitha van der Dussen (Vorstand **ab 2059-07-07**) im Jahr 2058 und an Theodor Krause (ab **2057-11-22**) im August 2057 | Eisenkrone und Feldspat hatten davor keinen Vorstand. Es zeichnen Esther Bauer 170, Pamela Stroh 169 (Finanzen) bzw. Mikhail Gotthard 2. |
| 2 | A: `FSP-RV-2059-01` mit Verkäuferexklusivität für Quantenquarz, Feldspat verkauft aber ab 2059-08 an 4 Kunden für 1,46 Mio. CR | Vorkaufsrecht |
| 3 | A: `EFF-MSA-2059-02` Energie käuferexklusiv ab 2060-01-18, aber `HMX-CTR-2059-0257` (Helix → Seip) läuft bis 2060-03-30 | Vorkaufsrecht Energie Myrrhen |
| 4 | A: KI-Kerne zugleich käuferexklusiv für Eisenkrone (CCI) und gegenseitig exklusiv mit Graufalk | Allianz-Exklusivität auf drive_parts/nav_computers |
| 5 | A: `GFW-RV-2058-01` verkäuferexklusive Rumpfplatten in Kharon, Graufalk liefert aber auch an Helix in Kharon | Vorkaufsrecht für Ravenmoor (verschärft die Rivalität Ravenmoor ↔ Helix) |
| 6 | A: `KHB-RV-2059-01` beginnt 2059-02-15, das Helix-Vorkaufsrecht (B) entfällt aber erst 2059-03-15 | Beginn 2059-04-01; das Angebot vom Januar wird abgelehnt (V14) |
| 7 | A: Geheimhaltungsklausel 2059-12-20 vor ihrem Auslöser (Gerücht 2059-12-27) | `proposed` am 2059-12-29 |
| 8 | A: `EKM-RV` Eisenkrone → Helix beginnt 2057-03-01, damit fällt EKM-VTR-2057-0002 heraus | Beginn 2057-01-01, 42 M (B) |
| 9 | B: CCI-Rahmen 36 M endet am Stichtag, Aussetzung bzw. Kündigung wären wirkungslos | 48 M (A) |
| 10 | B: Auslöser HMX-CTR-2059-0235 | nachgerechnet: HMX-CTR-2059-0236 |
| 11 | B: `helix → corvane` Nachtrag „medical“, ohne Medizinvertrag im Paar | gestrichen |
| 12 | B: Titel der en_US-Firmen (HMX, RCS, EFF, CCI, OSP) deutsch | Titel in der Sprache des Verkäufers (englisch) |
| 13 | Nummern `EKM-RV-2057-0x` unterschiedlich (A 4 Rahmen, B 3) | Nummern von B, `eisenkrone → feldspat` ohne Rahmen |
| 14 | `RVF-RV-2058-01/-02` vertauscht | chronologisch: -01 Pionierwerk (2058-01-01), -02 Eisenkrone (2058-03-01) |
| 15 | `SGM-RV-2059-01` bei A an Ravenmoor, bei B an Pionierwerk | beide behalten: -01 Pionierwerk (Jan.), -02 Ravenmoor (März) |
| 16 | `RCS-MSA-2059-01` (A) / `RCS-MSA-2058-01` (B) | B, Beginn 2058-08-01 |
| 17 | Briefarten und Aktenzeichen unterschiedlich benannt | Abschnitt 6.1 |
| 18 | Eisenkrone → Lichtacker: Teilkündigung (A) oder Androhung (B) | beide: Teilkündigung wirksam, das Rettungsangebot −5 % wird abgelehnt |
| 19 | Geleitschutzklausel: bei A unterschrieben (2059-09-01), bei B offen | offen (B), damit der Spieler zum Spielstart vermitteln kann |

## 8. Umsetzung (Zuständigkeit wie zwischen den Teams vereinbart)

1. Durchlauf 1 bleibt unverändert (6 Bestandsfirmen inkl. `OPTIONAL_PARTNERSHIPS`/`HISTORIC_PARTNERSHIPS`).
2. **Team A**: Durchlauf 2 mit eigenem RNG/Faker, Archetyp-Filter, neue Vereinbarungen, Historie und Rivalitäten aus
   `verknuepfungen.json`, Vertragsregel für neue Paare, QA 6/6/6 mit Bestandsvergleich.
3. **Team B**: `generate_framework_agreements` (deterministisch für Bestandspaare; Prüfwerte `expected_assigned_contracts`
   im JSON), `generate_correspondence` mit eigenem Strom, QA aus 5.4/6.4 (A) und 6.6/7.6 (B). Dazu kommt: Verstöße gegen
   Exklusivität (nicht gegen Vorkaufsrecht) erzeugen ein `breach_warning`-Schreiben, statt die QA scheitern zu lassen.
4. Neue QA-Prüfungen: Zählung aus Tabelle 2.3; ≥ 2 Paare nur indirekt verbunden; 341 zugeordnete Bestandsverträge;
   Strafbescheide = `contract_penalties`.
