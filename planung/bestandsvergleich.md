# Bestandsvergleich nach der Erweiterung (Phase 3b, Team A)

Stand: 21.10.2026 · Skript `generate_space_trading_data.py` (18 Firmen, Rahmenverträge) · Vergleich mit
`/home/user/bestand/space_trading_game_bestand.db` (Seed 42, nur lesend).

## 1. Kurzfassung

- **Alle 115.705 Bestandszeilen in allen 18 Bestandstabellen sind bei Seed 42 unverändert.** Das gilt auch für
  abgeleitete Werte wie `stations.storage_capacity_m3`, `trade_partnerships.contract_volume`, Ereignis-IDs, Preisverläufe
  und Finanzmonate.
- Neu ist eine Spalte: `contracts.framework_agreement_id`. Sie ordnet **341 der 743 Bestandsverträge** einem
  Rahmenvertrag zu (2.309,1 Mio. CR ohne Stornos). Der Wert stimmt mit `verknuepfungen.json` überein, ebenso die
  **13 Volumen-Auslöser** und alle Regel-Nachträge der 7 Bestandspaare.
- Bestandsobjekte bekommen nur **neue Bezüge** von neuen Zeilen: Routen, Lager, Preisverläufe, Verträge und
  Bestellungen neuer Lieferanten an Bestandsstationen, neue Partnerschaften und Rivalitäten, neue Ereigniswirkungen.
- Bei den Seeds 7 und 123 sind die Bestandszeilen ebenfalls identisch mit dem Skript vor der Erweiterung (gleicher
  Seed, gleiche Zeilen). Der Bestandsschutz ist also nicht auf Seed 42 zugeschnitten.

## 2. Methode

1. Das Skript erzeugt alle Bestandsdaten zuerst und mit dem gemeinsamen Zufallsstrom (`world.rng` und eine
   Faker-Instanz je Sprache), Schritt für Schritt in derselben Reihenfolge wie vorher („Durchlauf 1“).
2. Die 12 neuen Firmen erzeugen ihre Daten danach in eigenen Strömen. Jeder Strom ist aus (Seed, Firmen-key, Schritt)
   abgeleitet (`derived_seed`: SHA-256, unabhängig von `PYTHONHASHSEED`), mit eigenen Faker-Instanzen über
   `seed_instance` (`World.company_stream`).
3. Schritte, die früher über alle Zeilen liefen, sind getrennt. Zuerst kommt der Bestandsteil, dann die Erweiterung.
   Das betrifft die Marktplanung (erst alle Bestandsfirmen, dann alle Bestandsvereinbarungen), Lager (sortiert),
   Reservierungen, Lagerkapazität, Lieferungen, Ereignisplanung (Bestandsereignisse wirken nur auf Bestandsware und
   Bestandsnachbarn), Preisverläufe und die Reihenfolge der Ereignisse.
4. Neue Archetypen (`extension=True`) sind nur in den Produkt-Pools neuer Firmen. Neue Systeme sind hinten an
   `STAR_SYSTEMS` angehängt.
5. Vergleich per SQL: Für jede Bestandstabelle zählt `SELECT <alte Spalten> FROM baseline.t EXCEPT SELECT <alte Spalten>
   FROM main.t`, wie viele Bestandszeilen fehlen oder verändert sind. Diese Prüfung läuft auch automatisch in der
   Qualitätsprüfung des Skripts (`--baseline`, Standard `../bestand/space_trading_game_bestand.db`, nur bei Seed 42).

## 3. Ergebnis je Tabelle (Seed 42)

| Tabelle | Bestand | jetzt | davon neu | Bestandszeilen unverändert | verändert |
|---|---:|---:|---:|---:|---:|
| companies | 6 | 18 | 12 | 6 | 0 |
| star_systems | 10 | 13 | 3 | 10 | 0 |
| stations | 33 | 109 | 76 | 33 | 0 |
| products | 504 | 1.519 | 1.015 | 504 | 0 |
| trade_partnerships | 15 | 55 | 40 | 15 | 0 |
| company_rivalries | 4 | 12 | 8 | 4 | 0 |
| trade_routes | 936 | 2.816 | 1.880 | 936 | 0 |
| inventory | 1.481 | 4.467 | 2.986 | 1.481 | 0 |
| contracts | 743 | 2.128 | 1.385 | 743 (alte Spalten) | 0 |
| customers | 445 | 1.325 | 880 | 445 | 0 |
| orders | 5.518 | 15.118 | 9.600 | 5.518 | 0 |
| order_items | 6.925 | 18.739 | 11.814 | 6.925 | 0 |
| shipments | 5.351 | 14.610 | 9.259 | 5.351 | 0 |
| price_history | 93.648 | 284.235 | 190.587 | 93.648 | 0 |
| employees | 491 | 1.536 | 1.045 | 491 | 0 |
| events | 74 | 255 | 181 | 74 | 0 |
| event_effects | 421 | 1.428 | 1.007 | 421 | 0 |
| company_financials | 144 | 432 | 288 | 144 | 0 |
| **Summe** | **115.705** | | | **115.705** | **0** |

Neue Tabellen: `framework_agreements` (21), `framework_agreement_amendments` (90), `framework_agreement_scope` (80).

## 4. Ergebnis je Bestandsfirma (Anzahl Bestand / jetzt, Zeilen identisch)

| Firma | Stationen | Produkte | Mitarbeiter | Kunden | Routen | Verträge | Bestellungen | Finanzmonate | Preispunkte eigener Ware |
|---|---|---|---|---|---|---|---|---|---|
| Feldspat (1) | 3/3 | 27/27 | 22/22 | 16/16 | 53/53 | 27/27 | 117/117 | 12/12 | 2.160/2.160 |
| Driftwood (2) | 3/3 | 21/21 | 15/15 | 18/18 | 50/50 | 20/20 | 111/111 | 12/12 | 1.917/1.917 |
| Lichtacker (3) | 6/6 | 84/84 | 77/77 | 54/54 | 153/153 | 86/86 | 512/512 | 24/24 | 12.667/12.667 |
| Corvane (4) | 4/4 | 77/77 | 53/53 | 44/44 | 143/143 | 81/81 | 542/542 | 24/24 | 11.766/11.766 |
| Eisenkrone (5) | 7/7 | 165/165 | 125/125 | 133/133 | 296/296 | 238/238 | 2.436/2.436 | 36/36 | 36.625/36.625 |
| Helix (6) | 10/10 | 130/130 | 199/199 | 180/180 | 241/241 | 291/291 | 1.800/1.800 | 36/36 | 28.513/28.513 |

## 5. Was sich geändert hat und warum

### 5.1 Neue Spalte `contracts.framework_agreement_id` (Bestandsverträge unter Rahmenverträgen)

Die Regel ist deterministisch. Ein Vertrag gehört zu einem Rahmen, wenn das Paar gleich ist, der Vertragstyp
`framework`, `recurring_supply` oder `exclusive_supply` ist, der Beginn zwischen Rahmenbeginn und dem dann gültigen
Laufzeitende liegt und die Ware am Beginn im Sortiment ist.

| Rahmen (ID) | Paar | zugeordnet | Summe ohne Stornos (Mio. CR) | Soll laut JSON | Volumen Basis → aktuell |
|---|---|---:|---:|---:|---|
| HMX-MSA-2057-01 (1) | Helix → Lichtacker | 54 | 423,6 | 54 | 250 → 550 |
| HMX-MSA-2057-02 (2) | Helix → Corvane | 68 | 549,4 | 68 | 300 → 600 (750 angeboten) |
| HMX-MSA-2057-03 (3) | Helix → Eisenkrone | 75 | 438,7 | 75 | 300 → 450 (550 angeboten) |
| EKM-RV-2057-01 (4) | Eisenkrone → Corvane | 65 | 440,9 | 65 | 350 → 450 (550 angeboten) |
| EKM-RV-2057-02 (5) | Eisenkrone → Helix | 39 | 275,9 | 39 | 200 → 300 (400 angeboten) |
| EKM-RV-2057-03 (6) | Eisenkrone → Lichtacker | 35 | 178,0 | 35 | 150 → 200 |
| FSP-RV-2059-01 (7) | Feldspat → Eisenkrone | 5 | 2,6 | 5 | 12 (20 angeboten) |
| **Summe** | | **341** | **2.309,1** | **341** | |

- Je Firma: Helix 197 von 291 Verträgen (1.565,7 Mio. CR mit Stornos), Eisenkrone 139 von 238, Feldspat 5 von 27.
  Driftwood, Lichtacker und Corvane verkaufen an Bestandsfirmen ohne Rahmen.
- Je Typ (Bestand): `framework` 153 von 214, `recurring_supply` 114 von 165, `exclusive_supply` 74 von 96. `spot`,
  `consignment` und `emergency_supply` sind nie zugeordnet.
- Abruftypen in Rahmenpaaren außerhalb des Rahmens, so beabsichtigt: **FSP-VTR-2059-0001** und **-0005** (beginnen vor
  dem Rahmenbeginn 2059-08-01) und **EKM-VTR-2060-0230** (Helium-3, Energie ist durch die Teilkündigung ab 2060-01-18
  aus dem Rahmen).
- **Volumen-Auslöser (13, alle getroffen)**: HMX-CTR-2058-0161, -2059-0259, -2058-0152, -2059-0213, -2060-0281,
  -2059-0192, -2059-0236, -2060-0275, EKM-VTR-2059-0160, -2060-0219, -2059-0151, -2060-0234, -2059-0211. Jeder
  Volumen-Nachtrag wirkt zum Monatsersten des auslösenden Vertrags, also vor ihm. Auslöser aus 2060 sind
  Entwurfsverträge, ihr Nachtrag ist `proposed` (angeboten im Dezember 2059).
- Die Regel-Nachträge der 7 Bestandspaare stimmen in Typ, Wirkungsdatum und Status vollständig mit
  `verknuepfungen.json` überein: Produktaufnahmen einzeln nach Δ2, 3 Verlängerungen `calloff_after_end` zum
  2059-11-01, Volumenwerte 400/550, 450/600/750, 350/450/550, 450/550, 300/400, 200.

### 5.2 Neue Zeilen mit Bezug auf Bestandsobjekte

Neue Vereinbarungen mit Bestandsfirmen gibt es nur in der Richtung „neue Firma → Bestandsfirma“. Bestandsverkäufer
bekommen deshalb keine neuen Kunden, Routen oder Verträge.

| Bestandsfirma | neue Routen an ihre Stationen | Lagerzeilen fremder Ware | Preispunkte dazu | Verträge als Käufer (Mio. CR) | Bestellungen als Firmenkunde | neue aktive / historische Vereinbarungen | neue Rivalitäten | Wirkungen neuer Ereignisse |
|---|---:|---:|---:|---|---:|---|---:|---:|
| Feldspat | 0 | 0 | 0 | 0 | 0 | 0 / 1 (Outmark, Lizenz bis 2058-06) | 1 | 0 |
| Driftwood | 0 | 0 | 0 | 0 | 0 | 0 / 1 (an Second Hull bis 2058-07) | 2 | 0 |
| Lichtacker | 39 | 37 | 1.961 | 42 (53,5) | 115 | 2 / 1 | 1 | 1 |
| Corvane | 4 | 4 | 212 | 17 (11,1) | 40 | 1 / 0 | 0 | 0 |
| Eisenkrone | 47 | 43 | 3.059 | 80 (265,3) | 252 | 2 / 2 | 2 | 8 |
| Helix | 96 | 90 | 7.110 | 151 (630,9) | 478 | 2 / 1 | 2 | 6 |

Dazu kommen 7 neue Kundenkonten `corporate_partner` bei den neuen Verkäufern, die auf Lichtacker, Corvane,
Eisenkrone und Helix verweisen. Bestehende Kundenkonten und Bestandsbestellungen ändern sich nicht.

### 5.3 Bewusst gleich gehaltene, abgeleitete Werte

- **Lagerkapazität** (`stations.storage_capacity_m3`): Bestandsstationen werden zuerst nur mit Bestandsware bemessen
  (gleiche Zufallszüge wie vorher). Nur wenn fremde Ware die Kapazität überschreiten würde, wird im Strom der
  Erweiterung aufgestockt. Bei Seed 42 war das an **0 von 33** Bestandsstationen nötig (die Reserve liegt bei
  30–80 %).
- **Ereignisse**: Die Bestandsereignisse behalten die IDs 1–74 und ihre Wirkungen. Ereignisse neuer Firmen (IDs
  75–255, 2057-02-05 bis 2059-12-22) entstehen an neuen Stationen. Sie wirken nur auf Ware neuer Firmen, auch an
  Bestandsstationen im selben System (15 Wirkungen). Folge: `event_id` ist nur noch innerhalb beider Blöcke
  chronologisch, nicht mehr über alle Ereignisse.
- **IDs**: Bestandsfirmen 1–6, Systeme 1–10, Partnerschaften 1–15 (bei Seed 42: 13 Blueprint + `helix → corvane` +
  historisch `corvane → driftwood`). Neue aktive Vereinbarungen haben die IDs 16–49, neue historische 50–55.
  Rivalitäten: Bestand 1–4, neu 5–12.
- **Preisverlauf**: Das Intervall bleibt bei 14 Tagen (`PRICE_HISTORY_INTERVAL_DAYS`). Die Datenbank ist bei
  Seed 42 39,8 MB groß, bei Seed 7 44,7 MB, bei Seed 123 43,1 MB, also unter 45 MB. Eine Anpassung war nicht nötig.
  Seed 7 liegt aber knapp darunter. Wenn später noch mehr Zeilen dazukommen, ist ein längeres Intervall nur für
  Erweiterungsware die erste Stellschraube (Bestand bleibt bei 14 Tagen).

## 6. Abweichungen vom Plan (`verknuepfungen.json`) und Gründe

| Punkt | Plan | Umsetzung | Grund |
|---|---|---|---|
| Nachträge gesamt | 82 (64/17/1) | **90** (71 signed / 18 proposed / 1 rejected) | Regel-Nachträge neuer Paare hängen an den erzeugten Verträgen. Zusätzliche Volumen-Nachträge gibt es bei GFW-RV-2057-01/-02, GFW-RV-2058-01, CCI-MSA-2057-01, RVF-RV-2058-02, OSP-MSA-2058-01 (3) und SGM-RV-2059-02 (2). Die Regel-Erhöhungen von KHB-RV-2059-01 und EFF-MSA-2059-01 werden nicht ausgelöst (Abrufe 18,1 von 30 bzw. 2,4 von 40 Mio. CR). Bei den 7 Bestandspaaren gibt es keine Abweichung. |
| Wirkungsdaten „rule“ neuer Paare | ohne Datum | Monatserster des ersten bzw. auslösenden Vertrags | Regel wie bei den Bestandspaaren |
| Tabellenname Nachträge | `framework_amendments` | `framework_agreement_amendments` (PK `amendment_id`) | Auftrag Phase 3b |
| Sortiment | Felder `is_exclusive`, `added_by/removed_by` | `entry_kind` (`include`/`exclude`/`exclusivity`), `exclusivity`, `added_by_amendment_id`, `removed_by_amendment_id` | Herausnahmen einzelner Archetypen (Helium-3) und Exklusivitätsrechte ändern das Sortiment nicht. So bleibt die Sortimentsprüfung eindeutig. |
| Bezüge (`trigger_contract_id`, `trigger_order_id`, `trigger_event_id`) fester Nachträge | Bestandsnummern | nur bei Seed 42 gesetzt | Bei anderen Seeds bezeichnen dieselben Nummern andere Objekte. Regel-Nachträge verweisen bei jedem Seed auf ihren auslösenden Vertrag. |
| K9 `HMX-MSA-2057-02` | nur bei gezogenem `helix → corvane` | umgesetzt | Seed 42 und 7: 21 Rahmen, Seed 123: 20 Rahmen |

## 7. Andere Seeds

Bei Seed 7 und 123 sind die Bestandszeilen identisch mit dem Skript vor der Erweiterung bei gleichem Seed. Geprüft
habe ich das mit dem alten Skript und demselben SQL-Vergleich: 18 von 18 Tabellen, 0 veränderte Zeilen. Der Vergleich
mit der Bestands-DB und die Sollwerte 341/13 gelten nur für Seed 42. Deshalb hat die Qualitätsprüfung dort 50
Prüfungen, bei anderen Seeds 47.

## 8. Phase 3c – Schriftverkehr (Team B, 21.10.2026)

### 8.1 Bestandsschutz

- Neu sind nur die Tabellen `correspondence` (3.492 Schreiben bei Seed 42) und `correspondence_copies` (15 Kopien).
  Bestehende Tabellen bekommen weder Zeilen noch Spalten.
- Der Schriftverkehr ist Schritt 16, also der letzte Generierungsschritt. Er liest die übrigen Tabellen nur und rechnet in
  einem eigenen Strom `random.Random(derived_seed(seed, "correspondence", "letters"))`. `world.rng` und die
  Faker-Instanzen werden nicht benutzt. Namen stammen aus `employees`, Faker wird also nicht gebraucht.
- Einzige Änderung an bestehendem Code: Die Strafformel aus `generate_financials` steht jetzt in
  `contract_penalty_bookings()`. Beide Teile nutzen die Funktion, damit Strafbescheide und `contract_penalties`
  dieselbe Formel haben. Reihenfolge und Arithmetik sind unverändert. `company_financials` ist bei allen drei Seeds
  zeilengleich.
- Ergebnis Seed 42: **115.705 von 115.705 Bestandszeilen unverändert** (18/18 Tabellen, automatische Prüfung). Zusätzlich
  habe ich den kompletten Datenstand mit dem Skript aus Commit abefaa6 verglichen (alle 21 Tabellen, auch die der neuen
  Firmen und die Rahmentabellen): Seed 42: 349.006 Zeilen, Seed 7: 397.139 Zeilen, Seed 123: 377.695 Zeilen,
  jeweils **0 verändert**.

### 8.2 Umfang (Seed 42)

| Briefart | Anzahl | davon zwischen Bestandsfirmen |
|---|---:|---:|
| payment_reminder | 925 | 270 |
| delay_notice | 377 | 135 |
| contract_confirmation | 369 | 158 |
| offer | 285 | 97 |
| delay_complaint | 257 | 90 |
| delivery_notice | 243 | 80 |
| penalty_notice | 223 | 80 |
| inquiry | 159 | 50 |
| termination_notice | 156 | 50 |
| internal_memo | 150 | 45 |
| amendment_offer / _confirmation / _rejection | 87 / 71 / 1 | 47 / 39 / 1 |
| counter_offer / offer_rejection | 47 / 15 | 19 / 8 |
| rumor / confidential_tip | 46 / 27 | 14 / 9 |
| breach_warning / protest / suspension_notice | 35 / 18 / 1 | 19 / 5 / 0 |
| **Summe** | **3.492** | **1.216** |

1.851 Schreiben sind deutsch, 1.641 englisch. 147 gehen an Nicht-Firmenkunden (Mahnungen). 293 sind vertraulich,
28 davon sind geleakt (Original mit `leaked_by`). 56 waren zum Stichtag ungelesen. 825 Schreiben zwischen
Bestandsfirmen beziehen sich auf Bestandsverträge. Alle 223 gebrochenen Verträge haben einen Strafbescheid,
zusammen 17.290.739,49 CR. Das entspricht in allen 164 Firmenmonaten `company_financials.contract_penalties`.

Größe und Laufzeit: Seed 42 44,5 MB (42,4 MiB, Ausgabe des Skripts), Seed 7 49,7 MB (47,4 MiB), Seed 123 48,0 MB
(45,8 MiB). Laufzeit ≈ 15 s. Der Schriftverkehr selbst braucht etwa 0,8 s und rund 2,8 MiB. Seed 7 liegt damit knapp
unter 50 MB (dezimal). Wenn noch mehr Daten dazukommen, bleibt die Stellschraube aus 5.3: ein längeres
Preisintervall nur für Erweiterungsware.

### 8.3 Abweichungen vom Plan (`correspondence_design`, Entscheidung 6.3) und Gründe

| Punkt | Plan | Umsetzung | Grund |
|---|---|---|---|
| Spaltennamen | `reference_number`, `letter_type`, `tone` | `correspondence_number`, `correspondence_type`, `sentiment` (`positive/neutral/negative/hostile`) | Auftrag Phase 3c |
| Vertraulichkeit | `public/business/confidential/secret` | `public/internal/confidential` plus `min_intel_access_level` 0–3 | Auftrag Phase 3c. `business` → `internal`. `secret` → `confidential` mit Stufe 3 (Vorstand oder Tipp) |
| Neue Felder | – | `channel` (`letter/email/encrypted_message/holo_call`), `direction` (`seller_to_buyer/buyer_to_seller/internal/to_rival/lateral`), `is_read`, `storyline_code` (V1–V41) | Auftrag Phase 3c; Vorgangscode für Spielautoren und QA |
| Nachträge | FK auf `framework_amendments` | FK auf `framework_agreement_amendments` | Tabellenname von Team A |
| Kopien | – | Hilfstabelle `correspondence_copies` (cc/bcc/forward) | z. B. V31, V39 (cc Esther Bauer), Rahmenbestätigungen |
| Bestätigung Rahmen | Unterschrift (Vorstände) | Verhandlung (Anfrage, Angebot, 0–2 Gegenangebote) zwischen Beginn − 60 T und der Unterzeichnung (Beginn − 30 T), Bestätigung am Vertragsstart | Die Einstellungsgrenzen der neuen Firmen (Δ8) gelten ab Beginn − 60 T. Bestätigung „zum Vertragsstart“ laut Auftrag |
| V7, V17, V18, V22 | Angebot/Gegenangebot nach der Unterzeichnung | vorgezogen auf 2058-06-12/06-22, 2059-02-18, 2059-02-16, 2059-06-18. Die Bestätigungen bleiben am Vertragsstart (08-01, 04-01, 04-01, 08-01). | Team A unterzeichnet 30 Tage vor Beginn. Eine Verhandlung nach der Unterschrift ist unlogisch. |
| V3 | Bestätigung 2058-03-01 | 2058-02-17 (`signed_date` von CCI-MSA-2057-01/A1) | Bestätigung immer am Unterzeichnungstag des Nachtrags |
| V9 | Antwort 2058-10-05 mit Storno LAK-VTR-2058-0039 | Antwort 2058-10-14 (nach Beginn von -0039), Ankündigung, -0039 auslaufen zu lassen. Die Kündigung folgt nach dem letzten Abruf (2059-03-03). | Laut Daten wurde -0039 bis März 2059 beliefert |
| V21 | 8 Geleitschutzbrüche | 7 bis 2059-06-10 | EKM-VTR-2059-0167 bricht erst im Oktober 2059 |
| V22 | Schulden 22,94 / 24,22 Mio. CR | berechnet je Schreiben: 2059-06-18 11 Rechnungen 22,94 Mio., 2059-08-01 aus den Daten | Angebot vorgezogen, siehe oben |
| V26 | Gerücht Hines → Gould | `internal_memo` (vertraulich, verweist auf den Tipp von Osborne) | beide Driftwood; firmenintern ist nur `internal_memo` zulässig |
| V36 | Briefart `inquiry` | `inquiry` mit `amendment_id` = GFW-RV-2057-01/N4 als Angebot des Nachtrags | Der Nachtrag ist am 2059-12-31 angeboten |
| Volumen | 2.200–2.800 | 3.492 (Seed 7: 3.608, Seed 123: 3.717) | Jede Mahnstufe (Fälligkeit +3..7/+21/+45 T) ist ein eigenes Schreiben; Nicht-Firmenkunden nur als Stichprobe (25 %) |
| Bezüge auf Auslöseverträge | – | Nachtragsschreiben nennen den Auslöser im Text, aber nicht als FK | Auslöser beginnen meist erst nach dem Nachtrag („kein Schreiben vor seinem Bezugsobjekt“) |

Alle Personen der Vorgänge V1–V41 sind bei Seed 42 am Versandtag beschäftigt und gehören zur richtigen Firma. Ersatz
nach Rolle war nicht nötig. Bei anderen Seeds werden die verankerten Vorgänge nicht erzeugt (gleiche Nummern, andere
Objekte), der regelbasierte Schriftverkehr entsteht wie bei Seed 42.

### 8.4 Neue Qualitätsprüfungen (12 bei Seed 42, 11 bei anderen Seeds)

Seed 42: 62/62, Seed 7: 58/58, Seed 123: 58/58. Geprüft werden:

1. Menge, Briefarten, Firmen, Bestandsbezug.
2. Nummer, Sprache und Werte.
3. Absender, Empfänger und Kopien gehören zur Firma und sind am Versandtag beschäftigt.
4. Gesprächsfäden.
5. Bezugsobjekte passen zu den Parteien.
6. Kein Schreiben vor seinem Bezugsobjekt.
7. Strafformel und Monatssummen = `contract_penalties`.
8. Mahnstufen.
9. Verzugsbeschwerden nur bei echter Verspätung.
10. Rahmen und Nachträge vollständig belegt.
11. Leck-Regel.
12. V1–V41 umgesetzt (nur Seed 42).

Die Prüfungen schlagen an: Ein Test mit absichtlich verfälschter Datenbank (Strafbetrag +1 CR, falsche Sprache, fremder
Absender, gelöschte Nachtragsbestätigung, falscher Leck-Mitarbeiter) ließ jeweils die passende Prüfung fehlschlagen.
