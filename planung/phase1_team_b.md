# Phase 1 – Team B: Grenzraum, Expansion und Kolonisierung

Stand: 21.10.2026, überarbeitete Fassung (Revision 2) von Phase 1. Planung und Recherche, noch keine Änderung am Skript.

> **Revision 2 (Wiederholung Phase 1, verkleinerte Agentenbesetzung):** Die sechs Firmen bleiben **unverändert**, weil die verbindlichen Phase-2-Ergebnisse (`phase2_entscheidung.md`, `verknuepfungen.json`, Commit `bb1b10c`) genau auf diesen Keys, Präfixen, Systemen und Archetypen aufbauen. Ein Neuentwurf würde 48 Vereinbarungen, 12 Rivalitäten, 21 Rahmenverträge und 38 verankerte Schreiben ungültig machen. Stattdessen habe ich alle Bestandsangaben dieses Berichts erneut gegen die Bestands-DB geprüft und die Fehler korrigiert, die in Phase 2 gefunden wurden. Die Prüfprotokolle stehen in **Abschnitt 0**. Korrigierte Stellen sind mit *(korr. R2)* markiert.
 Grundlage: `generate_space_trading_data.py` (Seed 42) und der Datenbestand `/home/user/bestand/space_trading_game_bestand.db`. Die Zahlen unten stammen aus eigenen SQL-Abfragen auf diesen Bestand.

**Abgleich mit Team A (NACHRICHTEN.md, Phase-1-Eintrag von Team A):** Team A belegt Orrin, das System `pellora` und den Archetyp `habitat_modules` (Kuppelwerk Habitatbau AG). Daraufhin haben wir angepasst: Outmark sitzt jetzt auf Serravel statt in Orrin, Team B baut keine Station in Orrin, `habitat_modules` streichen wir bei uns und kaufen die Module von Kuppelwerk zu. Pionierwerk heißt jetzt „Kolonialausrüstung“ statt „Kolonialbau“ und konzentriert sich auf Terraforming und Kolonieausrüstung. Vereinbarungen mit Bestandsfirmen legen wir wie Team A nur in der Richtung „neue Firma → Bestandsfirma“ an.

Inhalt:
0. Revision 2: Nachprüfung gegen Bestand und Skript
1. Recherche-Erkenntnisse (Skript, Bestand, Lücken, technische Randbedingungen)
2. Überblick der 6 Firmen
3. Firmensteckbriefe (alle Felder)
4. Neue Sternensysteme, Sektor und Waren-Archetypen
5. Handelsnetz: Vereinbarungen, Rivalitäten, Bezüge zu Bestandsobjekten
6. Mengen und Datenbankgröße
7. Offene Fragen an Team A

---

## 0. Revision 2: Nachprüfung gegen Bestand und Skript

Alle Abfragen liefen lesend (`mode=ro`) auf `/home/user/bestand/space_trading_game_bestand.db`. Das Skript habe ich als Modul geladen, ohne es auszuführen.

| Prüfpunkt | Ergebnis heute | Status |
|---|---|---|
| Systeme ohne Station | Orrin 0, Isolde 0 (Nyx 1, Tauvel 3, Myrrhen 3) | bestätigt |
| Bestandsumfang | 33 Stationen, 504 Produkte, 491 Mitarbeiter, 5.518 Bestellungen, 93.648 Preispunkte, 74 Ereignisse | bestätigt |
| Lücken Angebot/Nachfrage | Kharon food 0/20, medical 3/12, raw 5/25; Myrrhen industrial 0/26, technology 0/17, medical 0/10; Brennus food 0/7, medical 0/9 | bestätigt |
| Weitere Lücken (neu notiert) | Sol raw 1/40, Aurelis raw 1/24, Sol food 6/36. Das ist Kerngebiet und gehört eher zum Themenfeld von Team A. | nur Hinweis |
| Wenig produzierte Waren | contraband 18 Angebotsplätze; Produkte je Archetyp: regolith 3, reactor_components 5, medical_equipment 6, ammonia_ice 7 | bestätigt |
| Geleitschutz-Zwischenfälle | 55 Lieferungen, 8 deswegen gebrochene Verträge (Liste in 1.2) | bestätigt |
| HMX-CTR-2059-0242 | gebrochen wegen **Quarantäneprüfung (+97 h)**, nicht wegen Geleitschutz | *(korr. R2)* |
| EKM-VTR-2058-0107 | startet in **Halcyon** (Bergbaustation Hande) → Kharon Exchange IX, Geleitschutz +71 h | *(korr. R2)* |
| Eisenkrone Brennus → Kharon | 8 Verträge, gebrochen sind **EKM-VTR-2057-0017** (Seltene Erden, 12,97 Mio. CR) und **EKM-VTR-2059-0162** (Quantenquarz, 7,74 Mio. CR), beide wegen Andockstau | *(korr. R2)* |
| Helix ab Kharon | 103 Verträge, 17 gebrochen | bestätigt |
| Feldspat → Eisenkrone | Vereinbarung `contract_volume` 6,05 Mio. CR; die 16 Verträge haben zusammen 8,08 Mio. CR | *(präzisiert R2)* |
| Aktive Vereinbarungen | Feldspat 3, Driftwood 1, Lichtacker 4, Corvane 5, Eisenkrone 7, Helix 8 | bestätigt |
| Ereignisse 26, 45, 52, 57, 58, 67, 74 | Datum, Typ, Station wie in 1.2; 26 und 58 sind im Text „mercenary raid“ | bestätigt |
| Einstellungsdaten | Theodor Krause (1) erst seit **2057-11-22**, Nathan Hines (33) seit 2058-01-20, Tyler Garcia (395) seit 2058-01-05. Vor diesen Daten zeichnen andere: für Feldspat Mikhail Gotthard (2, finance, seit 2055), für Eisenkrone Esther Bauer (170, relations, seit 2052). | *(korr. R2)* |
| Pool-Größen im Skript | Archetypen × Varianten: raw 12×5 = 60, energy 5×4 = 20, industrial 10×5 = 50, technology 6×5 = 30, food 7×5 = 35, medical 6×4 = 24, luxury 8×4 = 32, contraband 6×3 = 18. Mit den neuen Archetypen: raw 65, industrial 60 (mit `habitat_modules` von Team A), technology 35 bzw. 40 | bestätigt, die Pool-Summen in Kapitel 3 enthalten die neuen Archetypen |
| Distanzen neue Systeme | Vaskar: Isolde 283, Tauvel 590, Myrrhen 690. Serravel: Orrin 325, Halcyon 459, Brennus 525. Zu `pellora` (Team A) jeweils über 600 | bestätigt |
| QA im Skript | `run_quality_checks` prüft fest `len(companies) == 6` und 2/2/2 (Zeile 2970 f.) | bestätigt, Anpassung durch Team A (Phase 2) |

**Abgleich mit Phase 2:** Die Fragen aus Kapitel 7 wurden in Phase 2 beantwortet (`NACHRICHTEN.md`, `phase2_entscheidung.md`). Kapitel 5 zeigt den Stand von Phase 1. Verbindlich für die Umsetzung ist `verknuepfungen.json`, also mit den Kanten `kuppelwerk → pionierwerk`, `second_hull → graufalk`, `graufalk → ravenmoor` und `emberline → lichtacker` und ohne `raureif → emberline`.

---

## 1. Recherche-Erkenntnisse

### 1.1 Was das Skript vorgibt (für die Erweiterung wichtig)

| Thema | Befund im Skript | Folge für uns |
|---|---|---|
| Firmenprofil | `CompanyProfile` mit 18 Feldern; die erste Station in `required_stations` wird Hauptsitz (`headquarters_station_id`). | Hauptsitz bewusst als ersten Eintrag setzen. |
| Stationen | Die Pflichtstationen kommen zuerst. Die übrigen Stationen bis zum Ziel (small 2–3, medium 4–6, large 7–12) werden aus `station_type_weights` × `territory` gewürfelt. Sicherheit über `station_security()`: Militär immer `high`, Schmugglerhafen immer `lawless`, Freihafen eine Stufe unsicherer als das System. | Pflichtstationen höchstens so viele, wie die Größenklasse mindestens hat. |
| Produkte | Pool je Kategorie = alle Archetypen der Kategorie × `CATEGORY_VARIANTS`. Schwarzmarktware nur, wenn die Firma einen Freihafen in einem Low/Lawless-System oder einen Schmugglerhafen hat. | Große Firmen (bis 220 Produkte) brauchen Kategorien mit insgesamt ≥ 220 Pool-Einträgen. Bei allen Entwürfen geprüft (siehe Steckbriefe). |
| Erzeuger/Verbraucher | `CATEGORY_PRODUCERS`/`CATEGORY_CONSUMERS`: Rohstoffe nur aus `mining`, Medizin nur aus `research`, Lebensmittel nur aus `agricultural`. Ohne passende Station bietet die Firma die Ware über `trade_hub`/`free_port` an (wie Helix heute). | Stationstypen passend zu den Kategorien gewählt. |
| Partnerzahl | QA-Prüfung zählt **aktive Vereinbarungen in beide Richtungen**: small 1–3, medium 3–6, large 6–10. | **Harte Grenze für Verknüpfungen mit Bestandsfirmen**, siehe 1.3. |
| Partnerrouten | `plan_markets` erzwingt je Vereinbarung ≥ 4 Partnerrouten (Käuferstationen müssen Verbraucher der Ware sein). | Jede Vereinbarung unten geprüft: Käufer hat passende Stationstypen. |
| QA „Sechs Firmen“ | `run_quality_checks` prüft fest auf `len(companies) == 6` und 2/2/2. | Muss für 18 Firmen (6/6/6, je ≥ 2 de_DE/en_US) angepasst werden – gemeinsame Aufgabe in Phase 2. |
| Rivalitäten | `RIVALRY_BLUEPRINT` (Firma, Rivale, Typ, System); Text aus `RIVALRY_TEXTS` in der Sprache der ersten Firma. 4 Typen. | Wir nutzen 3 bestehende Typen und schlagen einen neuen vor (`armed_conflict`). |

### 1.2 Bestand (Seed 42) – was im Grenzraum heute fehlt

**Systeme ohne oder mit kaum Stationen**

| System | Stufe | Sicherheit | Stationen heute | Befund |
|---|---|---|---|---|
| Orrin | 2 | medium | 0 | Steht in den Territorien von Corvane (1,5), Eisenkrone (1,0) und Helix (1,5), aber dort wurde nie eine Station gewürfelt. |
| Isolde | 3 | medium | 0 | „Fruchtbare Habitatmonde“, steht im Territorium von Lichtacker (2,0) und Helix (1,0), trotzdem leer. |
| Nyx | 4 | lawless | 1 | Nur `Smugglers' Haven Hall` (Driftwood, Hauptsitz). |
| Kharon | 4 | low | 5 | 2 Driftwood, 3 Helix. Häufigstes Ziel von Piraten (6 von 74 Ereignissen). |

**Angebot und Nachfrage je System (Lagerplätze supply/demand)** – größte Lücken:

| System | Kategorie | Angebot | Nachfrage |
|---|---|---|---|
| Kharon | food | 0 | 20 |
| Kharon | medical | 3 | 12 |
| Kharon | raw_materials | 5 | 25 |
| Myrrhen | industrial_goods | 0 | 26 |
| Myrrhen | technology | 0 | 17 |
| Myrrhen | medical | 0 | 10 |
| Brennus | food | 0 | 7 |
| Brennus | medical | 0 | 9 |
| Nyx | alles | ≤ 4 | ≤ 4 |

Über alle Systeme: `contraband` hat nur 18 Angebotsplätze (16 Produkte), `regolith` nur 3 Produkte, `medical_equipment` 6, `ammonia_ice` 7, `reactor_components` 5 (nur Eisenkrone).

**Piraterie und Verspätungen (echte Bestandsobjekte)**
- 55 Lieferungen mit dem Zwischenfall „Piratenaktivität im Korridor, Geleitschutz abgewartet“ / „Pirate activity in the corridor, waited for escort“. Zielsysteme: Sol 12, Brennus 11, Myrrhen 9, Kharon/Aurelis/Halcyon je 7.
- **8 Verträge sind gebrochen (`breached`), weil ein Abruf auf Geleitschutz warten musste:** EKM-VTR-2057-0012, EKM-VTR-2057-0043, HMX-CTR-2057-0077, LAK-VTR-2058-0008, EKM-VTR-2058-0099, EKM-VTR-2058-0107 (Bergbaustation Hande, Halcyon → Kharon Exchange IX), HMX-CTR-2058-0183 (Kharon Exchange V → Tauvel Labor II, 10,57 Mio. CR), EKM-VTR-2059-0167.
- Helix hat 103 Verträge ab Kharon-Stationen, davon 17 gebrochen (zum Beispiel HMX-CTR-2059-0242, Medikamente, Kharon Landing IV → Brennus Schacht VII, 9,69 Mio. CR, Frist 27.11.2059). HMX-CTR-2059-0242 ist wegen einer Quarantäneprüfung gebrochen, nicht wegen Geleitschutz *(korr. R2)*. Eisenkrone Brennus → Kharon: 8 Verträge, davon 2 gebrochen, beide wegen Andockstau: EKM-VTR-2057-0017 (Seltene Erden, 12,97 Mio. CR) und EKM-VTR-2059-0162 (Quantenquarz, 7,74 Mio. CR) *(korr. R2)*. EKM-VTR-2058-0107 startet dagegen in Halcyon.
- Offene verspätete Bestellungen zum Stichtag: 7 (zum Beispiel DWS-ORD-2059-00107 nach Kharon Exchange V, EKM-BST-2059-02343 nach Kharon Exchange IX).

**Ereignisse, an die wir anknüpfen**

| ID | Datum | Typ | Station | Bezug für Team B |
|---|---|---|---|---|
| 26 | 2058-06-30 | black_market_raid („mercenary raid“) | Kharon Landing IV (Helix) | Söldner von Ravenmoor beschlagnahmen Waffen und Transitlizenzen |
| 58 | 2059-09-01 | black_market_raid („mercenary raid“, +125 %) | Smugglers' Haven Hall (Driftwood, Nyx) | Auslöser der Rivalität Ravenmoor ↔ Driftwood |
| 45, 57, 67 | 2059 | pirate_attack | Smugglers' Haven Hoffman (Driftwood, Kharon) | Driftwood beschuldigt Ravenmoor, Piraten gewähren zu lassen |
| 74 | 2059-12-20 | pirate_attack (läuft über den Stichtag) | Kharon Landing IV | Anlass für das Geleitschutzangebot an Helix |
| 52 | 2059-07-14 | resource_discovery, critical, 240 Tage | Bergbaustation Becker (Feldspat, Brennus) | Outmark behauptet, den Fund vorher vermessen zu haben |

**Schlüsselmitarbeiter, die für unsere Geschichten taugen (aktiv, aus `employees`)**

| Firma | Name | Rolle, Station | Loyalität / Bestechlichkeit | Ansatz |
|---|---|---|---|---|
| Driftwood | Carlos Osborne | station_manager, Smugglers' Haven Hoffman | 3 / 100, greedy | wahrscheinlicher Informant von Ravenmoor vor der Razzia 58 |
| Driftwood | Nathan Hines | security, Smugglers' Haven Hoffman | 36 / 81 | zweiter Leak-Kandidat (erst seit 2058-01-20 dabei) |
| Driftwood | Tina Gould | executive | 49 / 56 | Absenderin des Protestschreibens zur Razzia |
| Helix | Wayne Jacobson | station_manager, Kharon Landing IV | 48 / 73, greedy | verhandelt Geleitschutz mit Ravenmoor, zugleich Ziel der Razzia 26 |
| Helix | David Hendricks | station_manager, Kharon Exchange V | 78 / 28, loyal | seriöser Ansprechpartner für den Rahmenvertrag |
| Helix | Tyler Garcia | relations, Kharon Exchange V | 55 / 71 | Partnerbetreuung Kharon (seit 2058-01-05) |
| Feldspat | Slavko Geisel | relations, Davids-Kontor | 55 / 96, greedy | soll Vermessungsdaten von Outmark gekauft haben (Fund 52) |
| Feldspat | Theodor Krause | executive | 80 / 54 | Adressat der Claim-Beschwerde (erst seit 2057-11-22; vorher ist Mikhail Gotthard (2) der Adressat) *(korr. R2)* |
| Lichtacker | Kaspar Täsche | intelligence | 55 / 61 | beobachtet Pionierwerk auf Isolde |
| Lichtacker | Reimar Rörricht | executive | 66 / 63 | führt den Streit um die Isolde-Pachtrechte |
| Eisenkrone | Claire Rust | station_manager, Brennus Schacht VII | 90 / 17 | Empfängerin der verspäteten Helix-Lieferung (HMX-CTR-2059-0242, Quarantäne) |

### 1.3 Partnerkapazität der Bestandsfirmen (kritisch für beide Teams)

Die QA-Prüfung zählt aktive Vereinbarungen in **beide** Richtungen. Stand heute:

| Firma | Größe | aktiv heute | erlaubt | frei | Team B beansprucht | bleibt für Team A |
|---|---|---|---|---|---|---|
| Feldspat | small | 3 | 1–3 | **0** | 0 | 0 |
| Driftwood | small | 1 | 1–3 | 2 | 0 | 2 |
| Lichtacker | medium | 4 | 3–6 | 2 | 0 | 2 (Team A nimmt 1) |
| Corvane | medium | 5 | 3–6 | 1 | 0 | 1 (Team A nimmt 1) |
| Eisenkrone | large | 7 | 6–10 | 3 | 1 | 2 (Team A nimmt 1) |
| Helix | large | 8 | 6–10 | 2 | 1 | 1 (Team A nimmt 1) |

Mit der Planung von Team A (je 1 Platz bei Helix, Eisenkrone, Lichtacker und Corvane) bleiben danach frei: Helix 0, Eisenkrone 1, Lichtacker 1, Corvane 0, Driftwood 2. Rivalitäten zählen nicht mit. Deshalb vernetzen wir unsere Firmen hauptsächlich untereinander und hängen den Cluster über genau **zwei** Kanten an den Bestand (Raureif → Eisenkrone, Ravenmoor → Helix).

### 1.4 Bestandsschutz – technische Erkenntnis

1. **Gemeinsamer Zufallsstrom:** Alle Schritte nutzen `world.rng`. Jede neue Firma in `COMPANY_PROFILES` verschiebt den Strom, und zwar schon in Schritt 1 (Gründungsjahr, Rating, Zielmengen). Dadurch ändern sich Stationsnamen, Koordinaten, Produkte und Mitarbeiter der 6 Bestandsfirmen.
2. **Gemeinsamer Faker-Strom:** `Faker.seed(seed)` setzt den gemeinsamen Zufallsgenerator aller Faker-Instanzen. Jeder neue Gründer- oder Mitarbeitername verschiebt die Namen der Bestandsfirmen.
3. **Archetyp-Pools:** Neue Archetypen landen in `archetypes_by_category` und verändern über `shuffle`/`pop` auch die Kataloge der Bestandsfirmen.
4. **IDs:** Neue Systeme und Firmen nur **hinten anhängen**, dann bleiben `system_id` und `company_id` der Bestandsobjekte gleich.

Vorschlag (Entscheidung mit Team A in Phase 2):
- **Zwei Durchläufe.** Durchlauf 1 ist die heutige Pipeline mit den 6 Bestandsfirmen und erzeugt identische Stammdaten. Durchlauf 2 erweitert mit einem eigenen RNG (zum Beispiel `random.Random(f"{seed}:ext")`) und eigenen Faker-Instanzen (`seed_instance`).
- Neue Archetypen bekommen ein Feld (zum Beispiel `legacy=False`), damit Bestandsfirmen sie nicht ziehen.
- Neue Vereinbarungen mit Bestandsfirmen erzeugen **zusätzliche** Routen, Verträge und Bestellungen. Bestehende Zeilen bleiben unverändert, nur die Finanzen der betroffenen Bestandsfirmen werden neu summiert. So bleiben die Änderungen an den Bewegungsdaten nachvollziehbar.
- Für den Abgleich vorher/nachher bietet sich ein Vergleich gegen `/home/user/bestand/space_trading_game_bestand.db` an (Stationen, Produkte, Mitarbeiter je Bestandsfirma identisch?).

### 1.5 Inspiration aus `/home/user/idlestar` (nur gelesen)

- 13 Sektoren mit Gefahrenstufe 0–5, Spawns und Garnisonen nur in gefährlichen Sektoren → passt zu `unlock_tier` 5 und zu den Geleitschutzdiensten.
- Planetentypen (Wald, Wüste, Vulkan, Eis, Gas, Ozean) und Gebäude (Agrarkuppel, Tagebau, Raffinerie, Plasmagas-Anlage, Quantenquarz-Anlage) → Vorbild für einen Gasriesen mit Eismonden (Vaskar) und eine Terraforming-Welt (Serravel).
- Kolonisierung kostet Verbundstahl, Komfortgüter und Nahrung → Vorbild für die Warenkette Pionierwerk/Morgengrund/Second Hull.
- `expeditions.json` (Sonden, Signale, Fundorte) und `deposits.json` (33 beanspruchbare Lagerstätten je Sektor) → Vorbild für Outmark: Vermessung vor dem Abbau, Claims als Streitpunkt (Fund 52). *(R2)*
- `garrisons.json` (Garnisonen ab einer Mindestgefahr, Wellen nach Gefahrenstufe) → Vorbild für die Bastionen von Ravenmoor und den Geleitschutz als Voraussetzung für Stufe 5. *(R2)*
- `jumpLinks.json` (22 Sprungverbindungen mit Distanzen) → Hinweis für die Spiellogik: Vaskar nur über Isolde anbinden (283 Einheiten), Serravel über Orrin (325). *(R2)*
- Namen aus idlestar übernehmen wir bewusst nicht (eigene, fiktive Namen).

---

## 2. Überblick der 6 Firmen

| # | Name | key | Größe | Sprache | Spezialisierung | Heimatsystem | SKU |
|---|---|---|---|---|---|---|---|
| 1 | Pionierwerk Kolonialausrüstung AG | `pionierwerk` | large | de_DE | `colony_outfitting` | isolde | PKB |
| 2 | Ravenmoor Convoy & Security Group | `ravenmoor` | large | en_US | `convoy_security_and_supply` | kharon | RCS |
| 3 | Raureif Volatilförderung GmbH | `raureif` | medium | de_DE | `ice_and_gas_extraction` | vaskar (neu) | RVF |
| 4 | Outmark Survey & Prospecting Inc. | `outmark` | medium | en_US | `survey_and_prospecting` | serravel (neu) | OSP |
| 5 | Siedlergenossenschaft Morgengrund eG | `morgengrund` | small | de_DE | `settler_cooperative` | isolde | SGM |
| 6 | Second Hull Reclamation Co. | `second_hull` | small | en_US | `scrap_recycling` | nyx | SHR |

Verteilung: 2 small, 2 medium, 2 large; 3 de_DE, 3 en_US. SKU-Präfixe beginnen mit N–Z und kollidieren nicht mit FSP, DWS, LAK, CVB, EKM oder HMX. Vertrags- und Bestellnummern leiten sich daraus ab (zum Beispiel `PKB-VTR-2058-0001`, `RCS-ORD-2059-00042`).

---

## 3. Firmensteckbriefe

### 3.1 Pionierwerk Kolonialausrüstung AG (large, de_DE)

```python
CompanyProfile(
    key="pionierwerk", name="Pionierwerk Kolonialausrüstung AG", slug="pionierwerk-kolonialausruestung",
    language="de_DE", size_class="large", specialization="colony_outfitting",
    network_role="colonization_backbone", sku_prefix="PKB", home_system="isolde",
    territory={"isolde": 3.0, "serravel": 2.0, "myrrhen": 1.5, "vaskar": 1.0},
    required_stations=(("industrial", "isolde"), ("trade_hub", "isolde"),
                       ("industrial", "myrrhen"), ("agricultural", "serravel")),
    station_type_weights={"industrial": 3.0, "agricultural": 2.0, "trade_hub": 1.5,
                          "research": 1.0, "mining": 1.0},
    category_weights={"industrial_goods": 0.36, "food": 0.14, "technology": 0.12, "raw_materials": 0.12,
                      "luxury": 0.10, "energy": 0.08, "medical": 0.08},
    founded_range=(2035, 2039), credit_ratings=("A-", "A"), loyalty_bias=4,
    description=(
        "Die {name} wurde {year} von {founder} gegründet, um die Habitatmonde des Isolde-Systems "
        "bewohnbar zu machen. KI-gesteuerte Werke fertigen dort Lebenserhaltung, Atmosphärenwandler, "
        "Bauteile und Terraforming-Kulturen aus Recyclingmetall und Mondregolith, eigene Gartenringe "
        "versorgen die Bautrupps. Heute rüstet der Konzern jede neue Kolonie vom ersten Schweißpunkt bis "
        "zur ersten Ernte aus – und hält die alten Pachtansprüche anderer Konzerne auf Isolde für Makulatur."
    ),
    fleet=("Grundstein", "Richtfest", "Wegbereiter", "Fundament", "Kuppelbau", "Spatenstich", "Lotlinie",
           "Bauhütte", "Hebebaum", "Werkbank", "Schlussstein", "Firstwind"),
)
```

- **Hauptsitz:** Industriestation in Isolde (erste Pflichtstation).
- **Pool-Prüfung:** industrial_goods 60 (10 Bestandsarchetypen + `escort_drones` + `habitat_modules` von Team A) + food 35 + technology 35 + raw 65 + luxury 32 + energy 20 + medical 24 = 271 ≥ 220 (ohne die Archetypen von Team A: 266).
- **Rolle im Netz:** Rückgrat der Kolonisierung, als Generalausrüster und Terraformer. Den Habitatbau überlassen wir Kuppelwerk (Team A). Pionierwerk liefert Lebenserhaltung, Bauteile, Polymere, Werkzeugmaschinen und Terraforming-Kulturen an Morgengrund (Siedler) und Ravenmoor (Bastionen). Pionierwerk kauft Eis und Gas von Raureif, Recyclingmetall von Second Hull, Vermessungsdaten von Outmark, Lebensmittel von Morgengrund, Feldbedarf von Ravenmoor und, nach Vorschlag, Habitatmodule von Kuppelwerk.
- **Konkurrenz:** Mit Eisenkrone bei Industriegütern (Bauteile, Verbundstahl, Lebenserhaltung), teils auch mit Kuppelwerk (Team A). Mit Lichtacker um Isolde: Lichtacker hat Isolde im Territorium (Gewicht 2,0), aber dort nie gebaut → Rivalität `territorial_claims`.
- **Lücken, die die Firma schließt:** erste Stationen in Isolde. Industriestation in Myrrhen (dort heute 0 Angebot bei 26 Nachfrage nach Industriegütern und 0 bei 17 nach Technologie). Erste Agrarstation auf Serravel.
- **Spielchancen:** Handel mit großvolumigen, wertvollen Modulen (lohnt sich erst mit großem Laderaum, also ein Fortschrittsziel). Kolonie-Aufträge als Einstieg in die Freischaltung von Serravel. Beziehungen: Partnerbetreuung im Kontor Isolde. Spionage: Ausschreibungen im Wettstreit mit Eisenkrone, Pachtstreit mit Lichtacker (Kaspar Täsche).

### 3.2 Ravenmoor Convoy & Security Group (large, en_US)

```python
CompanyProfile(
    key="ravenmoor", name="Ravenmoor Convoy & Security Group", slug="ravenmoor-convoy",
    language="en_US", size_class="large", specialization="convoy_security_and_supply",
    network_role="frontier_quartermaster", sku_prefix="RCS", home_system="kharon",
    territory={"kharon": 3.0, "brennus": 2.0, "vaskar": 1.5, "serravel": 1.0, "nyx": 1.0, "aurelis": 0.5},
    required_stations=(("military", "kharon"), ("trade_hub", "kharon"),
                       ("military", "brennus"), ("free_port", "vaskar")),
    station_type_weights={"military": 3.0, "trade_hub": 1.5, "free_port": 1.0, "industrial": 1.0,
                          "research": 0.5},
    category_weights={"industrial_goods": 0.26, "technology": 0.24, "energy": 0.16, "medical": 0.12,
                      "food": 0.12, "contraband": 0.06, "raw_materials": 0.04},
    founded_range=(2036, 2040), credit_ratings=("BBB+", "A-"), loyalty_bias=10,
    description=(
        "{name} was founded in {year} by {founder} to escort the first AI-piloted ore convoys through "
        "the Brennus belt. Today its bastions in Kharon and Brennus guard the frontier corridors, and its "
        "quartermasters supply garrisons, mining crews and settlers with fuel, sensors, field medicine and "
        "spare parts. Ravenmoor sells safety by the light-hour – and whatever its patrols seize from "
        "smugglers has a way of reappearing on the free market."
    ),
    fleet=("Iron Vigil", "Long Watch", "Steady Hand", "Night Warden", "Rearguard", "Flint Shield",
           "Lantern Bearer", "Hold Fast", "Grey Sentry", "Far Escort", "Last Line", "Quiet Guardian"),
)
```

- **Hauptsitz:** Militärstation in Kharon. Militär ist immer `high`, damit entsteht ein sicherer Hafen im Grenzland. Der Freihafen in Vaskar wird `lawless`, damit darf Ravenmoor Schwarzmarktware führen (beschlagnahmte Waffen, Transitlizenzen).
- **Pool-Prüfung:** 60 + 35 + 20 + 24 + 35 + 18 + 65 = 257 ≥ 220.
- **Warum Warenhandel und nicht nur Dienstleistung:** Ravenmoor ist ein Quartiermeister des Grenzlands. Er verkauft Geleitschutzdrohnen (neu), Sensorarrays, Navigationscomputer, Rumpfplatten, Treibstoff, Feldmedizin und Rationen an Garnisonen, Bergbau und Siedler. Der Geleitschutz selbst steckt als Geschichte in Verträgen und Schreiben.
- **Rolle im Netz:** Verkauft an Helix (Kharon-Stationen), Pionierwerk und Outmark. Kauft Treibstoff und Eis von Raureif, Rationen von Morgengrund, aufbereitete Teile von Second Hull und Module von Pionierwerk.
- **Konkurrenz:** Mit Helix um Kharon (`market_dominance`). Gegner von Driftwood (neuer Typ `armed_conflict`, Anker: Razzien 26 und 58).
- **Lücken, die die Firma schließt:** Angebot an Lebensmitteln (0 bei 20 Nachfrage), Medizin (3 bei 12) und Rohstoffen (5 bei 25) in Kharon, Medizin in Brennus (0 bei 9), mehr Schwarzmarktangebot im Grenzland.
- **Spielchancen:** Geleitschutzaufträge und sichere Andockplätze. Beschlagnahmte Ware günstig im Freihafen Vaskar (Risiko). Beziehungen zu Offizieren (hohe Loyalität, `loyalty_bias` +10, also schwer zu bestechen, aber mit hohem Informationszugang). Spionage: wer hat die Razzien verraten (Carlos Osborne)? Freischaltung: Geleitschutzlizenz als Voraussetzung für Vaskar.

### 3.3 Raureif Volatilförderung GmbH (medium, de_DE)

```python
CompanyProfile(
    key="raureif", name="Raureif Volatilförderung GmbH", slug="raureif-volatilfoerderung",
    language="de_DE", size_class="medium", specialization="ice_and_gas_extraction",
    network_role="volatiles_supplier", sku_prefix="RVF", home_system="vaskar",
    territory={"vaskar": 3.0, "myrrhen": 1.5, "isolde": 1.0, "brennus": 0.5},
    required_stations=(("mining", "vaskar"), ("industrial", "vaskar"), ("mining", "myrrhen")),
    station_type_weights={"mining": 3.0, "industrial": 1.0, "trade_hub": 1.0},
    category_weights={"raw_materials": 0.45, "energy": 0.40, "industrial_goods": 0.10, "technology": 0.05},
    founded_range=(2045, 2049), credit_ratings=("BBB", "BBB+"), loyalty_bias=2,
    description=(
        "Die {name} wurde {year} von {founder} gegründet, als die ersten autonomen Gassammler in die "
        "Atmosphäre des Gasriesen Vaskar eintauchten. Das Unternehmen fördert Wasser-, Ammoniak- und "
        "Stickstoffeis auf den Vaskar-Monden und im Myrrhen-System und verarbeitet Helium-3 und Deuterium "
        "zu Treibstoff. Ohne Raureif gibt es in den neuen Kolonien weder Atemluft noch Wasser noch "
        "Brennstoff – entsprechend selbstbewusst verhandelt die Geschäftsführung."
    ),
    fleet=("Eisblume", "Frostfeder", "Kältebrücke", "Gasriese", "Polarnacht", "Reifglanz", "Schneegans"),
)
```

- **Hauptsitz:** Bergbaustation in Vaskar (neues System, Stufe 5). Gegründet 2045–2049: Konzerne erschließen Vaskar lange vor der Öffnung für freie Händler, die Stufe gilt nur für den Spieler.
- **Pool-Prüfung:** raw 65 + energy 20 + industrial 60 + technology 35 = 180 ≥ 90.
- **Rolle im Netz:** Lieferant von Volatilen. Verkauft Wasser-, Ammoniak- und Stickstoffeis, Helium-3, Deuterium, Plasmagas und Brennstoffzellen an Pionierwerk, Ravenmoor und Eisenkrone. Kauft Sensoren und Bergbaudrohnen von Outmark.
- **Konkurrenz:** Mit Feldspat als Eis- und Helium-3-Lieferant von Eisenkrone (Vereinbarungsvolumen Feldspat → Eisenkrone heute nur 6,05 Mio. CR, 16 Verträge mit zusammen 8,08 Mio. CR). Mit der Station Löchel (Eisenkrone) und den Agrarkolonien (Lichtacker) um Wassereis in Myrrhen. Dort gibt es die bestehende Rivalität Lichtacker ↔ Eisenkrone, die wir nur über Ereignisse und Preise berühren, nicht über eine weitere Rivalität.
- **Lücken, die die Firma schließt:** `ammonia_ice` (heute 7 Produkte), neue Ware `nitrogen_ice`, Energie für den Rand (Isolde, Vaskar).
- **Spielchancen:** Massengut mit niedriger Marge und langen Wegen, gut für Frachterkapitäne. Saisonale Engpässe über Asteroidensturm und Maschinenausfall. Beziehung zu den Stationsleitern in Vaskar. Freischaltung: Vaskar.

### 3.4 Outmark Survey & Prospecting Inc. (medium, en_US)

```python
CompanyProfile(
    key="outmark", name="Outmark Survey & Prospecting Inc.", slug="outmark-survey",
    language="en_US", size_class="medium", specialization="survey_and_prospecting",
    network_role="exploration_pioneer", sku_prefix="OSP", home_system="serravel",
    territory={"serravel": 3.0, "brennus": 1.5, "vaskar": 1.0, "isolde": 0.5},
    required_stations=(("research", "serravel"), ("mining", "serravel")),
    station_type_weights={"research": 2.5, "mining": 2.0, "trade_hub": 1.0},
    category_weights={"technology": 0.38, "raw_materials": 0.30, "luxury": 0.12, "medical": 0.10,
                      "industrial_goods": 0.10},
    founded_range=(2043, 2048), credit_ratings=("BB+", "BBB-"), loyalty_bias=-5,
    description=(
        "Founded in {year} by {founder}, {name} sends autonomous survey probes ahead of every corporate "
        "expansion. From its institute on Serravel it sells star charts, sensor arrays and "
        "prospecting drones, and it hauls the first samples – rare earths, quantum quartz, gemstones – back "
        "from worlds nobody has named yet. Outmark's data decides where the next colony is built, which "
        "makes its analysts popular, well paid and occasionally indiscreet."
    ),
    fleet=("Far Sounding", "Plumb Line", "Bearing Zero", "Parallax", "Long Baseline", "Blank Map"),
)
```

- **Hauptsitz:** Forschungsstation auf Serravel (neues System, Stufe 5). Ursprünglich war Orrin geplant, Team A nutzt Orrin.
- **Pool-Prüfung:** technology 40 (mit `terraforming_cultures` und `survey_charts`) + raw 65 + luxury 32 + medical 24 + industrial 60 = 221 ≥ 90.
- **Rolle im Netz:** Vorreiter der Erkundung. Verkauft Vermessungsdatenkerne (neu), Sensorarrays, Navigationscomputer und Bergbaudrohnen an Pionierwerk und Raureif. Erstfunde (Seltene Erden, Quantenquarz, Edelsteine, Bioproben) gehen über die Märkte. Kauft Expeditionsversorgung von Ravenmoor.
- **Konkurrenz:** Mit Feldspat (`territorial_claims` in Brennus, Anker: Rohstofffund 52 an der Bergbaustation Becker). Mit Corvane und Driftwood um Technologie.
- **Lücken, die die Firma schließt:** Mehr Angebot an Technologie am Rand (Brennus, Serravel). Seltene Rohstoffe aus Serravel. Bioproben aus Serravel für die Medizin-Lücke.
- **Spielchancen:** Spionage-Kern unseres Clusters (`loyalty_bias` −5): Analysten verkaufen Fundorte. Wer Vermessungsdaten kauft, schaltet Serravel frei (Vorschlag für die Spiellogik). Luxusware (Edelsteine) mit hoher Marge.

### 3.5 Siedlergenossenschaft Morgengrund eG (small, de_DE)

```python
CompanyProfile(
    key="morgengrund", name="Siedlergenossenschaft Morgengrund eG", slug="morgengrund-siedler",
    language="de_DE", size_class="small", specialization="settler_cooperative",
    network_role="colony_provisioner", sku_prefix="SGM", home_system="isolde",
    territory={"isolde": 3.0, "serravel": 1.5, "vaskar": 1.0},
    required_stations=(("agricultural", "isolde"),),
    station_type_weights={"agricultural": 3.0, "trade_hub": 1.5},
    category_weights={"food": 0.55, "luxury": 0.15, "raw_materials": 0.10, "industrial_goods": 0.10,
                      "medical": 0.10},
    founded_range=(2053, 2057), credit_ratings=("B+", "BB-"), loyalty_bias=12,
    description=(
        "Die {name} wurde {year} von {founder} und einer Handvoll Siedlerfamilien auf einem Habitatmond "
        "im Isolde-System gegründet. Die Genossenschaft betreibt Gewächskuppeln, eine Saatgutbank und einen "
        "kleinen Markt, auf dem Kolonisten Lebensmittel, Werkzeug und Selbstgebranntes tauschen. Jedes "
        "Mitglied hat eine Stimme, jeder Händler einen Platz am Tisch – solange er fair bezahlt."
    ),
    fleet=("Hoffnung", "Feldmaus", "Gemeinsinn", "Erntedank", "Taubenschlag"),
)
```

- **Hauptsitz:** Agrarstation in Isolde.
- **Pool-Prüfung:** food 35 + luxury 32 + raw 65 + industrial 60 + medical 24 ≫ 35.
- **Rolle im Netz:** Versorgt die Kolonien. Verkauft Lebensmittel und Spirituosen an Pionierwerk (Bautrupps) und Ravenmoor (Rationen für Garnisonen in Kharon und Brennus). Kauft Habitatmodule, Polymere und Terraforming-Kulturen von Pionierwerk.
- **Konkurrenz:** Mit Lichtacker als Lebensmittellieferant. Lichtacker hat Isolde im Territorium, aber dort keine Station.
- **Lücken, die die Firma schließt:** Lebensmittel für Kharon (0 bei 20) und Brennus (0 bei 7), über Ravenmoor weiterverteilt.
- **Spielchancen:** Einsteigerfreundlicher Partner (`loyalty_bias` +12, also kaum bestechlich, aber dankbar). Beziehungsgeschichte über Notlieferungen nach einem Ernteausfall. Kleine, sichere Mengen.

### 3.6 Second Hull Reclamation Co. (small, en_US)

```python
CompanyProfile(
    key="second_hull", name="Second Hull Reclamation Co.", slug="second-hull-reclamation",
    language="en_US", size_class="small", specialization="scrap_recycling",
    network_role="secondary_raw_supplier", sku_prefix="SHR", home_system="nyx",
    territory={"nyx": 3.0, "brennus": 1.0, "kharon": 0.5},
    required_stations=(("industrial", "nyx"),),
    station_type_weights={"industrial": 2.0, "mining": 2.0, "trade_hub": 0.5},
    category_weights={"raw_materials": 0.40, "industrial_goods": 0.35, "technology": 0.20, "luxury": 0.05},
    founded_range=(2052, 2056), credit_ratings=("B", "B+"), loyalty_bias=-6,
    description=(
        "{name} was founded in {year} by {founder}, who decided that the wrecks of Nyx were worth more "
        "melted down than stripped in the dark. The licensed recycler runs a smelter in the middle of the "
        "lawless graveyard, pays its protection money on time and turns derelict hulls into certified "
        "metals, refurbished components and salvaged electronics. The smugglers call it a traitor to the "
        "trade; the colonies call it their cheapest supplier."
    ),
    fleet=("Patchwork", "Mended Wing", "Scrap Sparrow", "Hand-Me-Down", "Make Do"),
)
```

- **Hauptsitz:** Industriestation in Nyx (`lawless`). Für den Wrackabbau als Rohstoffquelle sorgt meist eine zweite Station vom Typ `mining` aus den Gewichten.
- **Pool-Prüfung:** raw 65 + industrial 60 + technology 35 + luxury 32 ≫ 35.
- **Rolle im Netz:** Verkauft Recyclingmetall (Nickel-Eisen, Titan, Platinmetalle, Kohlenstoff) und aufbereitete Teile (Rumpfplatten, Triebwerksteile, Bauteile) an Pionierwerk und Ravenmoor. Optional übernimmt sie Bergegut von Driftwood in Kommission (siehe 5.1).
- **Konkurrenz:** Mit Driftwood um die Wracks von Nyx (Driftwood ist legal-grau, Second Hull lizenziert). Mit Feldspat und Eisenkrone bei Metallen.
- **Lücken, die die Firma schließt:** Nyx bekommt eine zweite und dritte Station, ein legales Angebot im gesetzlosen System und mehr Industriegüter am Rand.
- **Spielchancen:** Billige Teile mit extremem Routenrisiko (hohe Marge). Spionage: Wäscht Second Hull Driftwood-Ware? Beziehung zu einem kleinen, wackeligen Unternehmen (`loyalty_bias` −6).

---

## 4. Neue Sternensysteme, Sektor und Waren

### 4.1 Neuer Sektor (eine Zeile in `SECTOR_LABELS`)

```python
"far_reach": {"de_DE": "Ferne Weiten", "en_US": "Far Reach"},
```
Begründung: Die Stufe 5 liegt hinter dem Grenzland. Ein eigener Sektor zeigt im Spiel, dass das ein neuer Abschnitt der Freischaltung ist. Wenn Team A das nicht will, können beide Systeme auch `frontier` behalten.

### 4.2 Neue Systeme (hinten an `STAR_SYSTEMS` anhängen, damit die Bestands-IDs gleich bleiben)

```python
StarSystem("vaskar", "Vaskar", (-462.0, 438.0, 336.0), 5, "low", "far_reach",
           "Gasriese mit Eismonden jenseits von Isolde – Tankstelle und Kühlkammer der Kolonisierung.",
           "A gas giant ringed by ice moons beyond Isolde – fuel depot and cold store of colonisation."),
StarSystem("serravel", "Serravel", (412.0, -96.0, 388.0), 5, "medium", "far_reach",
           "Junge Terraforming-Welt mit dünner Atmosphäre; Siedler, Vermesser und Konzerngarnisonen teilen "
           "sich die ersten Kuppelstädte.",
           "A young terraforming world with a thin atmosphere; settlers, surveyors and corporate garrisons "
           "share the first domed towns."),
```

| System | nächste Nachbarn (Distanz in Raumeinheiten) | Reisezeit zum nächsten Nachbarn | Begründung |
|---|---|---|---|
| Vaskar | Isolde 283, Tauvel 590, Myrrhen 690 | ≈ 50 h | Volatile für die Isolde-Kolonien; Heimat von Raureif; Freihafen von Ravenmoor |
| Serravel | Orrin 325, Halcyon 459, Brennus 525 | ≈ 57 h | Terraforming-Ziel; Heimat von Outmark, Agrarstation von Pionierwerk |

Die Koordinaten liegen in −500..500. Mit Stationsstreuung (σ = 12) bleiben sie innerhalb der Grenze, sonst greift `clamp`. Zu jedem Bestandssystem sind es mehr als 280 Einheiten, zu `pellora` von Team A (−58/−136/−92) über 600.

**Freischaltung (Vorschlag für die Spiellogik):** Stufe 5 für beide. Vaskar wird über die Geleitschutzlizenz von Ravenmoor oder genug Ansehen bei Raureif freigeschaltet, Serravel über Vermessungsdatenkerne von Outmark. Isolde (Stufe 3) wird mit Pionierwerk und Morgengrund vom leeren System zum Einstieg in den Kolonie-Handel.

### 4.3 Neue Waren-Archetypen (sparsam: 3 + 1 optional)

```python
# Industriegüter (habitat_modules kommt von Team A und wird von uns mitgenutzt)
_archetype("escort_drones", "industrial_goods", "Geleitschutzdrohnen", "Escort Drones", "unit",
           21000, 2.4, 650, "restricted", producers=("industrial", "military")),
# Rohstoffe
_archetype("nitrogen_ice", "raw_materials", "Stickstoffeis", "Nitrogen Ice", "t", 75, 1.2, 1000,
           extra_consumers=("agricultural", "research")),
# Hochtechnologie
_archetype("terraforming_cultures", "technology", "Terraforming-Kulturen", "Terraforming Cultures",
           "canister", 7800, 0.06, 9, "restricted", producers=("research", "agricultural"),
           extra_consumers=("agricultural",)),
# optional
_archetype("survey_charts", "technology", "Vermessungsdatenkerne", "Survey Data Cores", "unit",
           5400, 0.01, 0.5, producers=("research",)),
```

| Archetyp | Begründung | Hauptanbieter |
|---|---|---|
| `escort_drones` | Physisches Gegenstück zum Geleitschutz. Einziger Archetyp, den auch eine Militärstation erzeugt. `restricted` mit Genehmigungspflicht. | Ravenmoor |
| `nitrogen_ice` | Puffergas für Terraforming-Atmosphären und Hydrokultur. Ergänzt Wasser- und Ammoniakeis. | Raureif |
| `terraforming_cultures` | Mikrobenkulturen für Terraforming. Schlägt die Brücke zwischen Forschung und Kolonien. `restricted`, also interessant für Schmuggel und Spionage. | Pionierwerk, Outmark |
| `survey_charts` (optional) | Vermessungsdaten als handelbarer Datenträger. Hebel für die Freischaltung von Serravel und Ziel für Spionage. | Outmark |

Hinweis: Diese Archetypen dürfen nicht in die Pools der Bestandsfirmen geraten (siehe 1.4, Punkt 3).

### 4.4 Neuer Rivalitätstyp (eine Ergänzung in `RIVALRY_TEXTS` und `intensity_ranges`)

```python
"armed_conflict": {
    "de_DE": "Söldner von {company} jagen Schmuggler im {system}-System; {rival} macht sie für die "
             "Razzien auf seine Häfen verantwortlich.",
    "en_US": "{company}'s mercenaries hunt smugglers in the {system} system; {rival} blames them for "
             "the raids on its havens.",
},
# intensity_ranges["armed_conflict"] = (60, 90)
```
Begründung: Keiner der 4 Typen beschreibt einen bewaffneten Konflikt. Die Bestandsereignisse 26 und 58 sind ausdrücklich Razzien einer Söldnertruppe („mercenary raid“).

---

## 5. Handelsnetz

### 5.1 Vereinbarungen (Verkäufer → Käufer), Ergänzung zu `PARTNERSHIP_BLUEPRINT`

```python
("raureif", "pionierwerk", "supply_agreement"),        # Eis, Gas, Treibstoff für Kolonien
("pionierwerk", "morgengrund", "supply_agreement"),    # Habitatmodule, Polymere, Terraforming-Kulturen
("morgengrund", "pionierwerk", "supply_agreement"),    # Lebensmittel für Bautrupps
("ravenmoor", "pionierwerk", "logistics_partnership"), # Feldbedarf, Drohnen, Sensoren für Baustellen
("pionierwerk", "ravenmoor", "supply_agreement"),      # Module und Bauteile für Bastionen
("outmark", "pionierwerk", "licensing"),               # Vermessungsdaten, Sensoren
("second_hull", "pionierwerk", "supply_agreement"),    # Recyclingmetall
("second_hull", "ravenmoor", "consignment"),           # aufbereitete Rumpfplatten, Triebwerksteile
("raureif", "ravenmoor", "supply_agreement"),          # Treibstoff für die Geleitflotte
("ravenmoor", "outmark", "logistics_partnership"),     # Expeditionsversorgung
("morgengrund", "ravenmoor", "supply_agreement"),      # Rationen für Garnisonen in Kharon und Brennus
("outmark", "raureif", "supply_agreement"),            # Bergbaudrohnen, Sensorarrays
("raureif", "eisenkrone", "supply_agreement"),         # Anschluss an den Bestand: Volatile für die Schwerindustrie
("ravenmoor", "helix", "logistics_partnership"),       # Anschluss an den Bestand: Grenzlandversorgung der Kharon-Stationen
```
Vorschlag für teamübergreifende Kanten, abhängig von der Bestätigung durch Team A, das freie Plätze bei Graufalk, Cindervale und Kuppelwerk angeboten hat:
```python
("kuppelwerk", "pionierwerk", "supply_agreement"),     # Habitatmodule für Isolde und Serravel
("second_hull", "graufalk", "supply_agreement"),       # Recyclingmetall und Rumpfplatten für die Werften
```
Alle Vereinbarungen mit Bestandsfirmen laufen in der Richtung „neue Firma → Bestandsfirma“ (wie bei Team A). Die frühere Option „driftwood → second_hull“ ist gestrichen. Wenn eine Driftwood-Kante gewünscht ist, ginge `("second_hull", "driftwood", "consignment")`, dann aber ohne die Graufalk-Kante, weil Second Hull sonst über 3 käme.

**Zählung (beide Richtungen):**

| Firma | Größe | Vereinbarungen | erlaubt |
|---|---|---|---|
| Pionierwerk | large | 7 (8 mit Kuppelwerk) | 6–10 ✓ |
| Ravenmoor | large | 7 | 6–10 ✓ |
| Raureif | medium | 4 | 3–6 ✓ |
| Outmark | medium | 3 | 3–6 ✓ |
| Morgengrund | small | 3 | 1–3 ✓ |
| Second Hull | small | 2 (3 mit Graufalk) | 1–3 ✓ |
| Eisenkrone | large | 7 → 8 | ✓ |
| Helix | large | 8 → 9 | ✓ |

**Routenprüfung:** Jeder Käufer hat Stationstypen, die die Ware des Verkäufers verbrauchen. Zum Beispiel Rohstoffe → `industrial`/`trade_hub`/`free_port`, Lebensmittel → `military`/`trade_hub`, Technologie → `mining`/`trade_hub`. Damit sind ≥ 4 Partnerrouten je Vereinbarung erreichbar.

**Netzprüfung:** Der Cluster hängt über Raureif–Eisenkrone und Ravenmoor–Helix am Bestand, das Netz bleibt zusammenhängend. Es gibt viele nur indirekt verbundene Paare, zum Beispiel Morgengrund ↔ Corvane. Helix kommt auf 6 direkte Partner und 9 Vereinbarungen, Ravenmoor auf 6 und 7, Pionierwerk auf 5 und 7. Die QA sortiert nach Partnern und dann nach Vereinbarungen, Helix bleibt also der Hub, und in jedem Fall ist der Hub eine große Firma.

### 5.2 Rivalitäten (Ergänzung zu `RIVALRY_BLUEPRINT`)

| Firma | Rivale | Typ | System | Anker im Bestand |
|---|---|---|---|---|
| lichtacker | pionierwerk | `territorial_claims` | isolde | Isolde im Lichtacker-Territorium (2,0), aber ohne Station; Pionierwerk baut dort |
| ravenmoor | driftwood | `armed_conflict` (neu) | nyx | Razzia 58 (Smugglers' Haven Hall, 2059-09-01), Piratenangriffe 45/57/67 auf Smugglers' Haven Hoffman |
| outmark | feldspat | `territorial_claims` | brennus | Rohstofffund 52 an der Bergbaustation Becker (2059-07-14); Leck über Slavko Geisel (Bestechlichkeit 96) |
| ravenmoor | helix | `market_dominance` | kharon | Partner und Konkurrent zugleich (wie Eisenkrone ↔ Helix in Sol); Razzia 26 trifft Helix' Kharon Landing IV |

Vorschlag: `since_date` für diese vier Einträge nicht würfeln, sondern auf das Ankerereignis setzen (zum Beispiel 2059-09-01 für ravenmoor ↔ driftwood). Für Lichtacker ↔ Pionierwerk passt ein Datum kurz nach der Gründung von Pionierwerk.

### 5.3 Bezüge für Rahmenverträge und Schriftverkehr (Vorschläge für Phase 2)

Rahmenverträge (falls eine Tabelle wie `framework_agreements` kommt, mit Verweis von `contracts`):
1. **„Geleitschutz-Rahmenvertrag Kharon-Korridor“** Ravenmoor ↔ Helix. Darunter fallen die neuen Verträge RCS → Helix. Als Bezug dienen die **103 bestehenden Helix-Verträge ab Kharon-Stationen**: Verträge ab 2059 könnten ein optionales Feld `escort_company_id = ravenmoor` bekommen (die Bestandszeilen selbst bleiben unverändert).
2. **„Rahmenvertrag Brennus–Kharon“** Eisenkrone → Helix. Er fasst die 8 bestehenden Verträge Brennus → Kharon zusammen, darunter die gebrochenen EKM-VTR-2057-0017 und EKM-VTR-2059-0162 (Andockstau) *(korr. R2)*, mit Geleitschutzklausel zugunsten von Ravenmoor.
3. **„Versorgungsrahmen Isolde“** Raureif → Pionierwerk sowie Morgengrund → Pionierwerk (neue Verträge, Vertragstyp `framework`).

Schriftverkehr, verankert an echten Objekten:

| Absender → Empfänger | Anlass (Bestand) | Inhalt |
|---|---|---|
| Ravenmoor → Helix (David Hendricks, Kharon Exchange V) | 8 wegen Geleitschutz gebrochene Verträge, Piratenangriff 74 (2059-12-20) | Angebot Geleitschutz-Rahmenvertrag |
| Helix (Wayne Jacobson) → Eisenkrone (Claire Rust, Brennus Schacht VII) | HMX-CTR-2059-0242 gebrochen (Medikamente, 9,69 Mio. CR, Quarantäne +97 h) *(korr. R2)* | Entschuldigung und Erklärung der Quarantäne. Den Geleitschutz-Bezug liefert stattdessen HMX-CTR-2058-0183 |
| Driftwood (Tina Gould) → Ravenmoor | Razzia 58 auf Smugglers' Haven Hall | Protest und Drohung |
| Outmark → Feldspat (Theodor Krause, im Amt seit 2057-11-22) | Fund 52 an der Bergbaustation Becker | Claim-Beschwerde, Vorwurf des Datendiebstahls |
| Lichtacker (Reimar Rörricht) → Pionierwerk | Rivalität Isolde | Verweis auf alte Pachtrechte |
| Morgengrund → Ravenmoor | Lebensmittellücke in Kharon (0 Angebot bei 20 Nachfrage) | Angebot Rationenlieferung |
| Eisenkrone → Raureif | Wassereiskonkurrenz in Myrrhen, Lieferung an Station Löchel | Mengenanfrage zum Vorzugspreis |

---

## 6. Mengen und Datenbankgröße

| Firma | Stationen (Ziel) | davon Pflicht | Produkte | Bestellungen | Mitarbeiter |
|---|---|---|---|---|---|
| Pionierwerk | 7–12 | 4 | 120–220 | 1.200–2.500 | 120–220 |
| Ravenmoor | 7–12 | 4 | 120–220 | 1.200–2.500 | 120–220 |
| Raureif | 4–6 | 3 | 50–90 | 400–800 | 40–80 |
| Outmark | 4–6 | 2 | 50–90 | 400–800 | 40–80 |
| Morgengrund | 2–3 | 1 | 20–35 | 100–200 | 12–24 |
| Second Hull | 2–3 | 1 | 20–35 | 100–200 | 12–24 |
| **Team B gesamt** | **26–42 (Erwartung ≈ 34)** | 15 | ≈ 550 | ≈ 5.200 | ≈ 480 |

Erwartete Stationsverteilung: Isolde 4–6, Serravel 3–5, Vaskar 3–5, Kharon +2–4, Myrrhen +1–2, Brennus +1–3, Nyx +1–3. Orrin bleibt Team A.

**Datenbankgröße:** Heute 14,1 MB bei 6 Firmen. Den Großteil machen `price_history` (93.648 Zeilen) und die Bestellungen der großen Firmen aus (Eisenkrone 36.625, Helix 28.513 Preispunkte). Team B verdoppelt etwa das Mengengerüst (+≈ 14 MB). Mit Team A ergibt sich eine Schätzung von ≈ 40–45 MB für 18 Firmen, das ist vertretbar. Falls kleiner gewünscht: Für die neuen großen Firmen die Stationszahl auf das untere Ende des Bereichs (7–8) legen. `SIZE_PROFILES` bleibt dabei unverändert, nur das Ziel wird gesteuert.

---

## 7. Offene Fragen an Team A

1. **Partnerplätze der Bestandsfirmen:** Euer Vorschlag passt. Team B nutzt nur 1 Platz bei Helix und 1 bei Eisenkrone, Corvane brauchen wir nicht. Nach beiden Teams sind noch frei: Eisenkrone 1, Lichtacker 1, Driftwood 2.
2. **Orrin/Isolde:** Erledigt. Orrin gehört euch, Outmark sitzt auf Serravel, Isolde übernehmen wir. Frage: Bleibt Orrin bei euch in medium-Sicherheit ohne neue Freischaltlogik? Für Serravel (Nachbar Orrin, 325) planen wir Stufe 5.
3. **Präfixe, Keys und Systemcodes:** Wir belegen PKB, RCS, RVF, OSP, SGM, SHR, die Keys `pionierwerk`, `ravenmoor`, `raureif`, `outmark`, `morgengrund`, `second_hull`, die Systeme `vaskar` und `serravel` sowie den Sektor `far_reach`. Plant ihr eigene neue Systeme? Bitte Codes und Koordinaten abstimmen (Abstand > 150).
4. **Bestandsschutz:** Seid ihr mit zwei Durchläufen und eigenem RNG bzw. Faker für die neuen Firmen einverstanden, mit einem `legacy`-Filter für neue Archetypen und der QA-Anpassung „18 Firmen, 6/6/6“ (Abschnitt 1.4)? Wer setzt das in Phase 2 um?
5. **Neue Archetypen:** `habitat_modules` gehört euch, wir nutzen ihn für Pionierwerk mit. Bitte bestätigt, dass neue Archetypen in den Pools aller neuen Firmen landen (nur nicht bei den Bestandsfirmen). Wir planen `escort_drones`, `nitrogen_ice`, `terraforming_cultures` und optional `survey_charts`. Ist `fusion_pellets` ein Energieträger aus Deuterium und Helium-3? Dann wäre `raureif → emberline` (supply_agreement) naheliegend. Hat Emberline dafür einen Platz frei?
8. **Teamübergreifende Kanten:** Nehmt ihr `kuppelwerk → pionierwerk` und `second_hull → graufalk` an (siehe 5.1)? Beide zählen bei euch je einen Platz.
6. **Rahmenverträge und Schriftverkehr:** Wer entwirft das Tabellenschema? Unser Vorschlag: `framework_agreements` (Verkäufer, Käufer, optional `escort_company_id`, Laufzeit, Volumen) mit `contracts.framework_id`, und `correspondence` (Absender- und Empfängermitarbeiter, Datum, Sprache, Bezug auf contract, order oder event).
7. **Rivalitätstyp `armed_conflict`:** Einverstanden, oder habt ihr eigene neue Typen, die wir zusammenführen sollten?

### 7.1 Offene Fragen nach Revision 2 (an Team A)

Die Fragen 1–8 sind in Phase 2 beantwortet. Neu sind nur noch:

- **R2-1:** Euer Bestandsvergleich (QA 6/6/6) sollte auch die in Abschnitt 0 genannten Ankerobjekte prüfen: die 8 Geleitschutzbrüche, HMX-CTR-2059-0242 und die Ereignisse 26, 52, 58 und 74. Sonst laufen die Schreiben von Team B ins Leere, falls sich der Bestandsstrom doch verschiebt. Übernehmt ihr das?
- **R2-2:** Prüft eure Schreiben bitte ebenfalls gegen `employees.hire_date`. Bei uns waren Krause, Hines und Garcia betroffen.
- **R2-3:** Die Rohstofflücken in Sol (1/40) und Aurelis (1/24) liegen im Kerngebiet und damit in eurem Themenfeld. Deckt ihr sie mit Graufalk oder Kuppelwerk ab, oder sollen wir Second Hull dafür stärker nach Brennus und Sol ausrichten? Das ginge nur über `territory`, eine neue Vereinbarung ist nicht nötig.
