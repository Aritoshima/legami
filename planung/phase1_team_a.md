# Phase 1 – Team A: Kernraum, Hochtechnologie und Infrastruktur

Stand: 20.10.2026, erneut geprüft am 21.10.2026 (Neudurchlauf, siehe Abschnitt 7) · Grundlage:
`generate_space_trading_data.py` (Seed 42) und der Datenbestand in
`/home/user/bestand/space_trading_game_bestand.db` (ausgewertet mit pandas/sqlite3, nur lesend).

Kurzfassung: Team A schlägt **6 Firmen** vor (je 2 small, medium und large; 3 × de_DE, 3 × en_US), dazu **1 neues
Sternensystem** (Pellora, Freischaltstufe 1) und **5 neue Waren-Archetypen**. Die Firmen schließen belegte Lücken im
heutigen Netz: Energie im inneren Ring, Industriegüter und Rohstoffe in Aurelis und Myrrhen, Hochtechnologie, die heute
aus dem Grenzland (Kharon) in den Kernraum geflogen wird, Luxus- und Konsumgüter in Sol und ein bisher leeres
System (Orrin).

| # | Firma | key | Größe | Sprache | Spezialisierung | Heimatsystem | SKU |
|---|---|---|---|---|---|---|---|
| 1 | Graufalk Orbitalwerften AG | `graufalk` | large | de_DE | `shipbuilding` | orrin | GFW |
| 2 | Cindervale Cognitive Industries Inc. | `cindervale` | large | en_US | `ai_compute_and_robotics` | sol | CCI |
| 3 | Kuppelwerk Habitatbau AG | `kuppelwerk` | medium | de_DE | `habitat_construction` | aurelis | KHB |
| 4 | Emberline Fusion Fuels Inc. | `emberline` | medium | en_US | `fusion_fuel_refining` | pellora (neu) | EFF |
| 5 | Kometenpost Kurierdienste GmbH | `kometenpost` | small | de_DE | `express_courier` | sol | KPK |
| 6 | Lanternfish Leisure Co. | `lanternfish` | small | en_US | `consumer_entertainment` | aurelis | LFL |

---

## 1. Recherche-Erkenntnisse

### 1.1 Skript (relevante Abschnitte)

- **Mengengerüst (`SIZE_PROFILES`)**: Stationen small 2–3, medium 4–6, large 7–12; aktive Vereinbarungen small 1–3,
  medium 3–6, large 6–10. Gezählt wird **jede gerichtete aktive Vereinbarung, an der die Firma beteiligt ist** (als
  Verkäufer oder Käufer), siehe `run_quality_checks` („Partnerzahl passt zur Größe“).
- **Stationen** (`generate_stations`): erst `required_stations`, dann nach `station_type_weights` × `territory`
  aufgefüllt; erste Station = Hauptsitz. Sicherheit aus System + Typ (`free_port` eine Stufe niedriger,
  `military` immer high, `smuggler_haven` immer lawless).
- **Produkte** (`generate_products`): Pool je Kategorie = alle Archetypen × `CATEGORY_VARIANTS`, gemischt mit dem
  globalen `rng`. Kategorie `contraband` nur, wenn die Firma eine Station mit illegalem Markt hat. Pool-Größen:
  energy 5 × 4 = 20, technology 6 × 5 = 30, industrial_goods 10 × 5 = 50, luxury 8 × 4 = 32.
- **Märkte und Routen** (`plan_markets`): Firmenübergreifende Routen nur **vom Verkäufer zu Stationen seiner Käufer**
  (aktive Vereinbarung Verkäufer → Käufer), nur zu Stationstypen in `consumers` des Archetyps. Industriegüter werden
  von `industrial`-Stationen **nicht** nachgefragt (wichtig für Werften, siehe Archetyp `habitat_modules`).
- **Verträge** (`generate_contracts`): ausschließlich zwischen Partnerfirmen entlang von Partnerrouten; Nummern
  `{sku_prefix}-{VTR|CTR}-{Jahr}-{lfd. Nr.}`. Kunden vom Typ `corporate_partner` entstehen **beim Verkäufer**.
- **Ereignisse** (`plan_market_events`): pro Station zufällig; Nachbarstationen im selben System können mitbetroffen
  sein.
- **Qualitätsprüfungen**: Die Prüfung „Sechs Firmen: 2 small, 2 medium, 2 large“ ist hart auf 6 kodiert und muss in
  Phase 2 auf 18 Firmen (6/6/6) umgestellt werden. „Zentraler Hub ist eine große Firma“ und „unvollständiges Netz“
  bleiben mit unserem Entwurf erfüllt.

### 1.2 Datenbestand (Seed 42)

**Stationen je System (Freischaltstufe ≤ 2, also unser Schwerpunkt)**

| System | Stufe | Stationen | Betreiber | Auffälligkeit |
|---|---|---|---|---|
| Sol | 0 | 6 | Corvane, Eisenkrone, Helix | keine Bergbau-, Agrar- oder Kurierstation; Rohstoffe: 1 Angebot vs. 40 Nachfragen |
| Halcyon | 1 | 5 | Corvane, Eisenkrone, Helix | Medizin-Nachfrage 26 vs. 10 Angebote; Industriestation Förster 3 × KI-Ausfall |
| Tauvel | 1 | 3 | Lichtacker | nur Agrar/Forschung; Energie 0 Angebote, Technik 0 Angebote |
| Aurelis | 2 | 5 | Lichtacker, Corvane, Helix | Industriegüter 3 Angebote vs. 22 Nachfragen; Rohstoffe 1 vs. 24 |
| Myrrhen | 2 | 3 | Lichtacker, Eisenkrone | Industriegüter 0 vs. 26, Technik 0 vs. 17, Energie 4 vs. 8 |
| **Orrin** | 2 | **0** | – | „industriell erschlossen“, aber leer, obwohl Corvane, Eisenkrone und Helix es im Territorium haben |
| Isolde | 3 | 0 | – | äußerer Rand → überlassen wir Team B |

**Warenkategorien**: Energie ist die schwächste legale Kategorie (61 Angebotseinträge, 94 Nachfragen). Kaum
produzierte Archetypen: `structural_parts` (6 Produkte), `reactor_components` (5, nur Eisenkrone),
`medical_equipment` (6), `regolith` (3), `spirits` (6). In Sol stehen 38 Luxus-Nachfragen nur 14 Angeboten gegenüber.

**Lange Wege für Hochtechnologie**: Helix beliefert den inneren Ring mit Supraleitern, Navigationscomputern und
Elektronik aus Kharon (Stufe 4). Genau diese Verträge platzen:
`HMX-CTR-2057-0050` (Supraleiter Mk III, Kharon Exchange V → Cole Institute, 8,35 Mio. CR, gebrochen),
`HMX-CTR-2057-0019` (Notlieferung Supraleiter, gebrochen), `HMX-CTR-2058-0121` (Supraleiter Pro, Sol Exchange II →
Cole Institute, gebrochen), `HMX-CTR-2057-0010` und `HMX-CTR-2057-0098` (Navigationscomputer Mk III, Kharon Landing IV
→ Tauvel Labor II, gebrochen).

**Gebrochene Verträge, an die unsere Firmen anknüpfen** (80 Verträge sind `breached`, 328 Mio. CR):

| Vertrag | Verkäufer → Käufer | Ware, Route | Wert | Anknüpfung |
|---|---|---|---|---|
| HMX-CTR-2058-0159 | Helix → Lichtacker | Composite Steel, Dudley Landing → Tauvel Labor II | 17,18 Mio. | Kuppelwerk |
| HMX-CTR-2057-0043 | Helix → Lichtacker | Composite Steel, Dudley Landing → Tauvel Labor II | 12,38 Mio. | Kuppelwerk |
| HMX-CTR-2058-0139 | Helix → Lichtacker | Composite Steel, Munoz Landing → Agrarstation Tintzmann | 6,30 Mio. | Kuppelwerk |
| HMX-CTR-2057-0012 | Helix → Lichtacker | Glass Ceramics Reinforced, Kharon Landing IV → Agrarstation Lindner | 1,61 Mio. | Kuppelwerk |
| HMX-CTR-2058-0131 | Helix → Corvane | Helium-3 Industrial Batch, Blair Landing → Halcyon Works VI | 12,84 Mio. | Emberline |
| HMX-CTR-2057-0014 | Helix → Corvane | Helium-3 Industrial Batch, Blair Landing → Halcyon Works VI | 3,01 Mio. | Emberline |
| EKM-VTR-2058-0099 | Eisenkrone → Lichtacker | Plasmagas, Bergbaustation Hande → Agrarstation Seip | 7,06 Mio. | Emberline |
| EKM-VTR-2059-0167 / -2058-0105 | Eisenkrone → Lichtacker | Brennstoffzellen Industriecharge, Förster → Agrarstation Seip | 3,60 / 2,67 Mio. | Emberline |
| EKM-VTR-2058-0132 | Eisenkrone → Feldspat | Antimaterie-Kapseln, Freudenberger-Werk → Bergbaustation Becker | 5,87 Mio. | Emberline (Rivalität) |
| EKM-VTR-2059-0160 | Eisenkrone → Corvane | Robotikeinheiten Pro, Freudenberger-Werk → Blake Institute | 6,06 Mio. | Cindervale |
| EKM-VTR-2057-0064 | Eisenkrone → Corvane | Reaktorkomponenten Leichtbau, Holsten-Werk → Blake Institute | 5,00 Mio. | Graufalk |
| HMX-CTR-2058-0173 | Helix → Lichtacker | Drive Components Lightweight, Kharon Landing IV → Agrarstation Lindner | 3,87 Mio. | Graufalk |
| HMX-CTR-2059-0197 | Helix → Lichtacker | Medical Equipment Clinical Grade, Munoz Landing → Hartmann-Gartenring | 8,87 Mio. | Kometenpost |
| HMX-CTR-2059-0246 | Helix → Corvane | Entertainment Electronics Travel Size, Kharon Exchange IX → Cole Institute | 3,11 Mio. | Lanternfish |

**Ereignisse im Kernraum, an die wir anknüpfen**

| ID | Datum | Typ | Station (System) | Anknüpfung |
|---|---|---|---|---|
| 19, 36, 70 | 2058-02-04, 2058-11-13, 2059-11-29 | machine_failure („Ausfall eines KI-Leitsystems“) | Industriestation Förster (Halcyon, Eisenkrone) | Cindervale (Lieferant der Leitsysteme), Graufalk (springt bei Triebwerksteilen, Reaktorkomponenten, Bauteilen ein) |
| 3, 24 | 2057-03-18, 2058-04-29 | demand_boom („construction boom“) | Sol Exchange II (Sol, Helix) | Kuppelwerk, Cindervale |
| 18, 29 | 2058-01-25, 2058-07-11 | demand_boom (Bauboom) | Freudenberger-Werk (Sol) / Förster (Halcyon) | Kuppelwerk, Graufalk |
| 10, 30 | 2057-08-29, 2058-09-13 | asteroid_storm | Bergbaustation Hande / Halcyon Works VI (Halcyon) | Emberline (Deuterium, Helium-3 knapp) |
| 8, 27, 69, 72 | 2057–2059 | pirate_attack | Dudley Landing, Agrarstation Seip, Bergbaustation Löchel, Agrarstation Lindner | Kometenpost (Kurier mit Geleitschutz), Graufalk (Geleitschiffe) |
| 34, 37, 59 | 2058–2059 | quarantine | Sol Institute VII, Cole Institute, Halcyon Works VI | Kometenpost (Medizin-Express) |

**Lieferverzögerungen**: 463 Lieferungen kamen zu spät. Die häufigsten Korridore sind Sol → Brennus (34),
Kharon → Aurelis (25), Kharon → Sol (22), Brennus → Halcyon (19) und Sol → Aurelis (17). Die häufigsten Ursachen sind
Triebwerksschäden (86, de und en zusammen), Navigationsfehler nach Sensorausfall (73), Asteroidensturm (69) und
Zollkontrollen (65). Das sind Aufhänger für Graufalk (Triebwerksteile), Cindervale (Sensoren, Navigationscomputer)
und Kometenpost (Pünktlichkeit).

**Finanzen**: Die Vertragsstrafen von Helix steigen jedes Jahr (0,74 → 1,67 → 2,08 Mio. CR, 2057–2059), und Lichtackers
Warenumsatz sinkt (170,2 → 164,3 Mio. CR, 2058–2059). Beide Firmen brauchen also verlässlichere Lieferanten, was die
neuen Lieferverträge begründet.

**Schlüsselmitarbeiter, die in unseren Geschichten vorkommen** (alle aktiv; IDs aus `employees`)

| ID | Name | Firma, Rolle, Station | Einfluss / Loyalität / Bestechlichkeit | Rolle in unserer Geschichte |
|---|---|---|---|---|
| 178 | Annekatrin Schuchhardt | Eisenkrone, Stationsleitung, Industriestation Förster | 71 / 85 / 25 | Kennt die Ausfallprotokolle; loyal, also schwer zu kaufen |
| 170 | Esther Bauer | Eisenkrone, Partnerbetreuung, Freudenberger-Werk | 62 / 53 / 76 | Ansprechpartnerin für Graufalk und Cindervale, bestechlich |
| 171, 172 | Dolores Mühle, Josip Sölzer | Eisenkrone, Marktaufklärung | intel 3, Loyalität 96 / 87 | Ermitteln gegen Cindervale-Firmware (Sölzer seit 2052; Mühle erst ab Einstellung 2058-11-10, also ab Ereignis 36) |
| 168 | Roswitha van der Dussen | Eisenkrone, Vorstand (seit 2059-07-07) | ehrgeizig | Gegenspielerin von Graufalk, nur für Vorgänge ab Mitte 2059 |
| 299 | Desiree Schwartz | Helix, Marktaufklärung, Sol Exchange II (seit 2059-11-24) | Bestechlichkeit 78, gierig | Lecks über Helix-Lieferprobleme (für Cindervale, Kuppelwerk), nur ab Ende 2059 |
| 301 | Kurt Sullivan | Helix, Stationsleitung, Sol Exchange II | 70 / 70 / 50 | Empfänger beim Bauboom (Kuppelwerk, Lanternfish) |
| 47 | Toralf Gerlach | Lichtacker, Stationsleitung, Tauvel Labor II | 69 / 86 / 20 | Wartet auf den Verbundstahl aus den gebrochenen Helix-Verträgen |
| 45 | Hans-Werner Eberhardt | Lichtacker, Stationsleitung, Agrarstation Seip | 66 / 75 / 23 | Energie-Engpass und Piratenangriff (Ereignis 27) |
| 41 | Hülya Matthäi | Lichtacker, Partnerbetreuung | Loyalität 78 | Verhandelt mit Kuppelwerk |
| 123 | Matthew Thomas | Corvane, Stationsleitung, Halcyon Works VI | 66 / 66 / 27 | Helium-3-Ausfall (Emberline) |
| 120 | Richard Chavez | Corvane, Marktaufklärung, Cole Institute | Bestechlichkeit 76, gesprächig | Lecks über Supraleiter-Engpass (Cindervale) |

### 1.3 Inspiration (idlestar, nur gelesen)

`packages/content/data/resources.json` und `planets.json`: Komfortgüter (`comfort_goods`) und Verbundstahl als
Kolonisierungskosten, ein Gasriese mit Stürmen (`helios_v`: `gas_giant`, `storms`), Quantenquarz als Spezialressource
und Produktionsmodule für Stahl, Nahrung und Komfortgüter. Daraus übernommen haben wir die Ideen Gasriese als
Brennstoffquelle (Pellora), Komfortgüter (Lanternfish) und Habitatmodule als Bauware für Kolonien (Kuppelwerk). Namen
oder Inhalte haben wir nicht übernommen.

### 1.4 Welche Lücken unsere Firmen schließen

| Lücke (belegt) | Firma |
|---|---|
| Orrin ohne Stationen | Graufalk (Hauptsitz und Werften), Lanternfish (Territorium) |
| Energie: schwächste legale Kategorie; Tauvel 0 Angebote, Sol 9 vs. 21; Helium-3-Verträge an Halcyon gebrochen | Emberline (+ System Pellora) |
| Industriegüter in Aurelis (3 vs. 22) und Myrrhen (0 vs. 26); Verbundstahl-Verträge für Lichtacker gebrochen; Bauboom in Sol | Kuppelwerk |
| `structural_parts`, `reactor_components`, `drive_parts` schwach bzw. Monopol Eisenkrone; KI-Ausfälle in Förster | Graufalk |
| Hochtechnologie kommt aus Kharon (Stufe 4) und kommt zu spät; Myrrhen hat 0 Technik-Angebote bei 17 Nachfragen | Cindervale |
| Luxusgüter in Sol (14 vs. 38) und Aurelis (12 vs. 23) | Lanternfish |
| 463 verspätete Lieferungen; Medizin-Nachfrage in Halcyon 26 vs. 10; Quarantänen | Kometenpost |

---

## 2. Firmensteckbriefe

Die Felder entsprechen `CompanyProfile`. Für Phase 2 lassen sich die Blöcke direkt übernehmen.

### 2.1 Graufalk Orbitalwerften AG (large, de_DE)

```python
CompanyProfile(
    key="graufalk", name="Graufalk Orbitalwerften AG", slug="graufalk-orbitalwerften",
    language="de_DE", size_class="large", specialization="shipbuilding",
    network_role="shipyard_supplier", sku_prefix="GFW", home_system="orrin",
    territory={"orrin": 3.0, "sol": 1.5, "halcyon": 1.0, "aurelis": 1.0, "myrrhen": 0.5},
    required_stations=(("industrial", "orrin"), ("trade_hub", "orrin"), ("industrial", "sol")),
    station_type_weights={"industrial": 4.0, "military": 1.5, "mining": 1.0, "trade_hub": 1.0, "research": 0.5},
    category_weights={"industrial_goods": 0.50, "technology": 0.20, "raw_materials": 0.10, "energy": 0.10,
                      "luxury": 0.04, "food": 0.03, "medical": 0.03},
    founded_range=(2035, 2038), credit_ratings=("A", "A+"), loyalty_bias=4,
    description=(
        "Die {name} wurde {year} von {founder} gegründet, als die Eisenkrone ihre Werftsparte im Orrin-System "
        "abstieß. Aus den alten Trockendocks wurde der größte Werftverbund außerhalb Sols: KI-gesteuerte Hellinge "
        "fertigen Rumpfplatten, Triebwerksteile, Reaktorkomponenten und Lebenserhaltungsmodule. Graufalk baut die "
        "Schiffe, mit denen die Konzerne – und bald auch freie Händler – das All befahren, und hat mit der "
        "Eisenkrone noch eine offene Rechnung."
    ),
    fleet=("Kielholer", "Spantenriese", "Stapellauf", "Werftfeuer", "Nietenhammer", "Dockmeister", "Ankerlicht",
           "Helling", "Bugwelle", "Kranlicht", "Stahlkiel", "Graufalke"),
)
```

- **Stationen**: 7–12 (Größenklasse); erwartet 8–10, Schwerpunkt Orrin (Werften, Handelsstation, ggf. Militärstation
  als Kunde für Geleitschiffe).
- **Rolle im Netz**: Graufalk ist der Werft- und Schiffsteilelieferant des Kernraums. Die Firma kauft Ansteuerungen und
  Navigationstechnik bei Cindervale, Fusionsbrennstoff für Probefahrten bei Emberline, Bauteile und Glaskeramik bei
  Kuppelwerk sowie Komfortgüter für die Werftarbeiter bei Lanternfish. Sie beliefert Helix (Rumpfplatten und
  Triebwerksteile für die Helix-Flotte), Cindervale (strategische Allianz) und Emberline (Schöpfschiff-Teile).
- **Konkurrenz**: Graufalk greift das Industriegüter-Monopol der Eisenkrone an (Verbundstahl,
  Reaktorkomponenten, Triebwerksteile). Als Ereignis-Anker dienen die drei KI-Ausfälle in der Industriestation Förster
  (Ereignisse 19, 36, 70), bei denen die Produktion von Triebwerksteilen, Reaktorkomponenten und Bauteilen jeweils um
  über 60 % einbrach. Dazu kommen die gebrochenen Verträge EKM-VTR-2057-0064 (Reaktorkomponenten an Corvane) und
  HMX-CTR-2058-0173 (Triebwerksteile an Lichtacker).
- **Spielchancen**: Handel mit Schiffsteilen (hoher Wert pro Kubikmeter). Graufalk ist die logische Werft für spätere
  Schiffs-Upgrades des Spielers. Spionage: Eisenkrone und Graufalk beobachten sich gegenseitig, Esther Bauer
  (Eisenkrone) ist bestechlich. Freischaltung: Orrin (Stufe 2) bekommt erstmals Stationen und einen Grund für einen
  Besuch.

### 2.2 Cindervale Cognitive Industries Inc. (large, en_US)

```python
CompanyProfile(
    key="cindervale", name="Cindervale Cognitive Industries Inc.", slug="cindervale-cognitive",
    language="en_US", size_class="large", specialization="ai_compute_and_robotics",
    network_role="technology_core", sku_prefix="CCI", home_system="sol",
    territory={"sol": 3.0, "halcyon": 2.0, "aurelis": 1.0, "orrin": 1.0, "tauvel": 0.5},
    required_stations=(("research", "sol"), ("industrial", "halcyon")),
    station_type_weights={"research": 3.0, "industrial": 3.0, "trade_hub": 1.0, "military": 0.5},
    category_weights={"technology": 0.55, "industrial_goods": 0.15, "luxury": 0.12, "energy": 0.08,
                      "raw_materials": 0.05, "medical": 0.05},
    founded_range=(2031, 2034), credit_ratings=("AA-", "A+"), loyalty_bias=-3,
    description=(
        "{name} was founded in {year} by {founder}, only months after the first AI systems took over factory floors "
        "on Earth. Its compute foundries in Sol and Halcyon produce AI cores, robotics units and sensor arrays, and "
        "its control software runs half the automated plants of the inner ring – including, some say, the ones that "
        "keep failing. Cindervale sells the minds of the machine age and is never shy about the price."
    ),
    fleet=("Quiet Inference", "Gradient Descent", "Parallel Light", "Deep Cache", "Clean Compile", "Long Context",
           "Bright Kernel", "Null Pointer", "Warm Start", "Edge Case", "Soft Landing", "Open Weights"),
)
```

- **Stationen**: 7–12; erwartet 7–9 (Forschung und Fertigung in Sol und Halcyon, Handelsstation in Aurelis oder Orrin).
- **Rolle im Netz**: Cindervale ist der Hochtechnologie-Kern im inneren Ring und ersetzt die Technikflüsse, die heute
  aus Kharon kommen. Die Firma beliefert Eisenkrone (KI-Leitsysteme, Robotik), Graufalk (Navigations- und
  Sensortechnik), Lanternfish (Elektronik für Immersionskapseln) und Kometenpost (in Kommission: KI-Kerne,
  Quantenrelais). Sie kauft Energie bei Emberline, Expresslogistik bei Kometenpost und Schiffsteile bei Graufalk.
- **Konkurrenz**: Cindervale steht im Wettbewerb mit Helix um den Technikmarkt in Sol, Anker sind die gebrochenen
  Helix-Verträge HMX-CTR-2057-0050, -2058-0121, -2057-0019 (Supraleiter an Cole Institute) sowie die Nachfrageschübe
  bei Sol Exchange II (Ereignisse 3 und 24: Elektronik und Supraleiter +48 %). Gegenüber Eisenkrone gibt es eine
  heikle Doppelrolle: Cindervale ist Lieferant, steht aber unter Verdacht, dass seine Firmware die Förster-Ausfälle
  verursacht hat. Daraus können Schriftverkehr und Spionage entstehen.
- **Spielchancen**: KI-Kerne und Quantenrelais sind teuer und `restricted`. Für den Spieler bedeutet das hohe Margen,
  er braucht aber Genehmigungen. Spionage: Das Gerücht um die Firmware ist ein ideales Spionageziel (Eisenkrone-Analysten
  Mühle und Sölzer ermitteln, Richard Chavez bei Corvane ist gesprächig und bestechlich). Beziehungen: Die Firma hat
  einen negativen loyalty_bias, ihre Mitarbeiter sind also eher abwerbbar.

### 2.3 Kuppelwerk Habitatbau AG (medium, de_DE)

```python
CompanyProfile(
    key="kuppelwerk", name="Kuppelwerk Habitatbau AG", slug="kuppelwerk-habitatbau",
    language="de_DE", size_class="medium", specialization="habitat_construction",
    network_role="construction_supplier", sku_prefix="KHB", home_system="aurelis",
    territory={"aurelis": 3.0, "myrrhen": 1.5, "tauvel": 1.5, "sol": 1.0},
    required_stations=(("industrial", "aurelis"), ("mining", "myrrhen")),
    station_type_weights={"industrial": 3.0, "mining": 2.0, "trade_hub": 1.0},
    category_weights={"industrial_goods": 0.55, "raw_materials": 0.25, "energy": 0.05, "technology": 0.05,
                      "luxury": 0.05, "food": 0.05},
    founded_range=(2044, 2049), credit_ratings=("BBB", "BBB+"), loyalty_bias=6,
    description=(
        "Die {name} wurde {year} von {founder} im Aurelis-System gegründet, um Siedlungen schneller zu bauen, als die "
        "KI-Planer sie entwerfen konnten. Aus Regolith, Silikaten und Glaskeramik sintert das Unternehmen Bausteine, "
        "Kuppelsegmente und komplette Habitatmodule. Jeder Bauboom im inneren Ring füllt die Auftragsbücher – jede "
        "ausbleibende Verbundstahl-Lieferung legt die Baustellen still."
    ),
    fleet=("Grundstein", "Richtfest", "Mörtelmond", "Kuppelbauer", "Lotwaage", "Ziegelwind", "Bauhütte"),
)
```

- **Stationen**: 4–6; Industriestation in Aurelis (Hauptsitz), Regolith- und Eisförderung in Myrrhen, dazu nach
  Gewichtung Tauvel oder Sol.
- **Rolle im Netz**: Kuppelwerk liefert Baustoffe. Die Firma beliefert Lichtacker (Ersatz für die gebrochenen
  Verbundstahl- und Glaskeramik-Lieferungen von Helix an Tauvel Labor II, Agrarstation Tintzmann und Lindner) sowie
  Graufalk (Bauteile und Glaskeramik für Docks). Energie für die Sinteröfen bezieht sie bei Emberline.
- **Konkurrenz**: Kuppelwerk konkurriert mit Helix und Eisenkrone bei Verbundstahl und Bauteilen. In Myrrhen tritt
  die Firma als dritter Förderer neben Lichtacker und Eisenkrone auf (bestehende Rivalität um Wassereis,
  `resource_competition`). Darauf baut eine spätere Konfliktgeschichte auf, eine neue Rivalität legen wir nicht an.
- **Spielchancen**: Massengut-Handel mit kurzen, sicheren Wegen, gut für den Einstieg des Spielers. Die Bauboom-Ereignisse
  (3, 18, 24, 29) zeigen, wann sich Baustoffe lohnen. Beziehungen: Toralf Gerlach und Hülya Matthäi (Lichtacker) sind
  dankbare Abnehmer. Freischaltung: Mit `habitat_modules` lassen sich spätere Kolonien (Isolde, Team B) ausstatten.

### 2.4 Emberline Fusion Fuels Inc. (medium, en_US)

```python
CompanyProfile(
    key="emberline", name="Emberline Fusion Fuels Inc.", slug="emberline-fusion",
    language="en_US", size_class="medium", specialization="fusion_fuel_refining",
    network_role="energy_supplier", sku_prefix="EFF", home_system="pellora",
    territory={"pellora": 3.0, "sol": 1.5, "halcyon": 1.0, "tauvel": 0.5, "myrrhen": 0.5},
    required_stations=(("mining", "pellora"), ("industrial", "sol")),
    station_type_weights={"mining": 3.0, "industrial": 2.0, "trade_hub": 1.0},
    category_weights={"energy": 0.45, "raw_materials": 0.20, "industrial_goods": 0.15, "technology": 0.10,
                      "luxury": 0.05, "food": 0.05},
    founded_range=(2041, 2046), credit_ratings=("BBB+", "A-"), loyalty_bias=0,
    description=(
        "{name} was founded in {year} by {founder}, who anchored the first automated helium-3 scoops in the upper "
        "atmosphere of the gas giant Pellora. Today the company refines deuterium, helium-3 and fusion fuel pellets "
        "for reactors across the inner ring. Its fuel keeps stations warm and freighters moving – and every storm "
        "on Pellora is felt in the price of a canister on Sol."
    ),
    fleet=("Ember Run", "Plume Diver", "Steady Burn", "Deep Scoop", "Pilot Flame", "Torus Dream"),
)
```

- **Stationen**: 4–6; Schöpfstation (mining) in Pellora als Hauptsitz und Raffinerie (industrial) in Sol.
- **Pool-Hinweis**: Mit `fusion_pellets` hat Energie 6 × 4 = 24 Kombinationen. Bei 50–90 Produkten und Gewicht 0,45
  fallen 23–41 Energieprodukte an, die größere Zahl übersteigt den Pool. Der Generator weicht dann automatisch auf
  andere Kategorien aus. Das Gewicht ist deshalb bewusst unter 0,6 gesetzt.
- **Rolle im Netz**: Emberline ist der Energielieferant des inneren Rings. Die Firma beliefert Corvane (Helium-3 für
  Halcyon Works VI als Ersatz für die gebrochenen Helix-Verträge HMX-CTR-2058-0131 und -2057-0014), Graufalk, Kuppelwerk
  und Cindervale. Schöpfschiff-Teile kauft sie bei Graufalk.
- **Konkurrenz**: Emberline konkurriert mit Eisenkrone (Plasmagas, Brennstoffzellen und Deuterium aus Bergbaustation
  Hande). Anker sind die gebrochenen Lieferungen EKM-VTR-2058-0099, -2059-0167, -2058-0105 an Agrarstation Seip, der
  Asteroidensturm bei Hande (Ereignis 10) und die Piratenangriffe in Myrrhen (Ereignisse 27, 69). Mit Feldspat (Helium-3
  aus Brennus) gibt es Preiskonkurrenz, aber keine eigene Rivalität, weil Feldspat zum äußeren Rand gehört.
- **Spielchancen**: Energie ist überall gefragt (fast alle Stationstypen verbrauchen sie) und eignet sich als
  verlässliche Grundlast-Route für Anfänger. Freischaltung: Pellora ist ein neues Ziel auf Stufe 1. Ereignisse: Stürme
  im Gasriesen sind über `asteroid_storm` auf Bergbaustationen abbildbar (Rohstoffe und Energie).

### 2.5 Kometenpost Kurierdienste GmbH (small, de_DE)

```python
CompanyProfile(
    key="kometenpost", name="Kometenpost Kurierdienste GmbH", slug="kometenpost-kurier",
    language="de_DE", size_class="small", specialization="express_courier",
    network_role="logistics_provider", sku_prefix="KPK", home_system="sol",
    territory={"sol": 3.0, "halcyon": 1.5, "tauvel": 1.5, "aurelis": 1.0},
    required_stations=(("trade_hub", "sol"),),
    station_type_weights={"trade_hub": 3.0, "free_port": 1.0},
    category_weights={"technology": 0.35, "medical": 0.30, "luxury": 0.25, "energy": 0.10},
    founded_range=(2052, 2057), credit_ratings=("BB", "BB+"), loyalty_bias=10,
    description=(
        "Die {name} wurde {year} von {founder} gegründet, nachdem eine verspätete Medikamentenlieferung eine ganze "
        "Station wochenlang in Quarantäne gehalten hatte. Der kleine Kurierdienst kauft eilige, wertvolle Fracht – "
        "Ersatzteile, Medizin, Elektronik – und fliegt sie mit schnellen Leichtfrachtern zwischen Sol und dem "
        "inneren Ring aus. Kometenpost weiß, wer wann was bestellt, und ihre Pilotinnen und Piloten reden gern."
    ),
    fleet=("Eilfeder", "Postillion", "Sternschnuppe", "Laufbursche", "Blitzbrief"),
)
```

- **Stationen**: 2–3; Kontor in Sol (Hauptsitz), danach Halcyon, Tauvel oder Aurelis. Hinweis: Ein `free_port` in
  Aurelis hätte niedrige Sicherheit und damit einen illegalen Markt. Contraband bleibt trotzdem ausgeschlossen, weil
  `category_weights` keine Schwarzmarktware enthält.
- **Warenhandel**: Kometenpost ist keine reine Dienstleistung, sondern kauft und verkauft eigene Produkte (Medizin,
  Technik, Luxus) in kleinen Mengen über das normale Datenmodell (Stationen, Produkte, Routen, Bestellungen).
- **Rolle im Netz**: Kometenpost verkauft Waren von Cindervale in Kommission und liefert per
  `logistics_partnership` Medizin und Technik an Cindervale-Forschungsstationen.
- **Anknüpfung an den Bestand**: Grundlage sind die 463 verspäteten Lieferungen (Korridore Sol → Brennus, Sol → Aurelis,
  Kharon → Sol), die Quarantänen 34, 37 und 59 sowie der gebrochene Medizin-Vertrag HMX-CTR-2059-0197 (Munoz Landing
  → Hartmann-Gartenring, 8,87 Mio.).
- **Spielchancen**: Informationshändler. Die Firma hat einen hohen loyalty_bias, ihre Pilotinnen und Piloten sind
  aber gesprächig (Rollen `pilot` und `logistics`). Darüber kann der Spieler erfahren, welche Lieferungen anstehen.
  Gut geeignet für Express-Aufträge mit kleinem Laderaum ganz am Anfang.

### 2.6 Lanternfish Leisure Co. (small, en_US)

```python
CompanyProfile(
    key="lanternfish", name="Lanternfish Leisure Co.", slug="lanternfish-leisure",
    language="en_US", size_class="small", specialization="consumer_entertainment",
    network_role="consumer_goods_supplier", sku_prefix="LFL", home_system="aurelis",
    territory={"aurelis": 3.0, "sol": 1.5, "orrin": 1.0},
    required_stations=(("industrial", "aurelis"), ("trade_hub", "sol")),
    station_type_weights={"industrial": 2.0, "trade_hub": 2.0},
    category_weights={"luxury": 0.60, "technology": 0.20, "food": 0.10, "industrial_goods": 0.10},
    founded_range=(2050, 2055), credit_ratings=("BB-", "BB"), loyalty_bias=-5,
    description=(
        "{name} was founded in {year} by {founder}, a former station entertainment officer who noticed that "
        "automated freighters never get bored – but their crews do. From a small fabrication works in Aurelis the "
        "company builds immersion pods and entertainment electronics and imports little comforts like coffee and "
        "spirits for crews in Sol and the Middle Belt. Small, loud and well liked on every docking ring."
    ),
    fleet=("Matinee", "Encore", "Velvet Rope", "Bright Marquee", "Popcorn Comet"),
)
```

- **Stationen**: 2–3; Werk in Aurelis (Hauptsitz) und Handelsstation in Sol, optional eine dritte in Orrin.
- **Rolle im Netz**: Lanternfish liefert Konsumgüter. Die Firma bezieht Elektronik von Cindervale und beliefert
  Graufalk (Komfortgüter für die Werftarbeiter in Orrin).
- **Konkurrenz**: Bei Luxusgütern konkurriert Lanternfish mit Helix (Luxus-Gewicht 0,25). Anker ist der gebrochene
  Vertrag HMX-CTR-2059-0246 (Unterhaltungselektronik, Kharon Exchange IX → Cole Institute). Eine eigene Rivalität
  legen wir nicht an, weil die Firma dafür zu klein ist.
- **Spielchancen**: Luxusware hat stark schwankende Nachfrage (Saisonalität luxury 0,16). Das ist Spekulationshandel
  für den Spieler. Beziehungen: Die Firma hat einen negativen loyalty_bias, ihre Mitarbeiter sind also leicht für
  Gerüchte zu gewinnen.

### 2.7 Mengenprüfung

| Firma | Größe | Stationen (Bereich) | erwartet | Produkte | Verträge | Bestellungen | Vereinbarungen (Plan) |
|---|---|---|---|---|---|---|---|
| Graufalk | large | 7–12 | 8–10 | 120–220 | 150–300 | 1.200–2.500 | 7 (+0–3 mit Team B) |
| Cindervale | large | 7–12 | 7–9 | 120–220 | 150–300 | 1.200–2.500 | 7 (+0–3) |
| Kuppelwerk | medium | 4–6 | 5 | 50–90 | 60–120 | 400–800 | 3 (+0–3) |
| Emberline | medium | 4–6 | 5 | 50–90 | 60–120 | 400–800 | 5 (+0–1) |
| Kometenpost | small | 2–3 | 2–3 | 20–35 | 20–40 | 100–200 | 2 (+0–1) |
| Lanternfish | small | 2–3 | 2–3 | 20–35 | 20–40 | 100–200 | 2 (+0–1) |
| **Summe Team A** | | **26–42** | **≈ 32** | | | | |

**Datenbankgröße**: Heute erzeugen 6 Firmen (2/2/2) 14,1 MB, davon 93.648 Zeilen Preisverlauf. Pro Größenklasse
gemessen: large ≈ 29–37 Tsd. Preisverlaufszeilen, medium ≈ 12 Tsd., small ≈ 2 Tsd. Team A hat dieselbe
Größenverteilung, also kommen etwa 14 MB hinzu. Mit Team B ergeben sich etwa 40–45 MB und rund 280 Tsd. Zeilen
Preisverlauf. Das ist vertretbar, eine Änderung von `PRICE_HISTORY_INTERVAL_DAYS` ist nicht nötig.

**Stationen je System nach der Erweiterung (Erwartung Team A)**: Sol +5–7, Orrin +4–6 (vorher 0), Pellora +2–4 (neu),
Halcyon +2–3, Aurelis +3–4, Myrrhen +1–2, Tauvel +0–2. Sol bleibt das dichteste System, das passt zum Kernraum.

---

## 3. Verknüpfungen

### 3.1 Freie Plätze bei den Bestandsfirmen (wichtig für beide Teams)

Aktive Vereinbarungen heute (beide Richtungen gezählt) im Vergleich zur Obergrenze der Größenklasse:

| Firma | heute | Obergrenze | frei | Vorschlag Team A | Rest für Team B |
|---|---|---|---|---|---|
| Feldspat (small) | 3 | 3 | **0** | – | **0** |
| Driftwood (small) | 1 | 3 | 2 | – | 2 |
| Lichtacker (medium) | 4 | 6 | 2 | 1 (Kuppelwerk → Lichtacker) | 1 |
| Corvane (medium) | 5 | 6 | 1 | 1 (Emberline → Corvane) | 0 |
| Eisenkrone (large) | 7 | 10 | 3 | 1 (Cindervale → Eisenkrone) | 2 |
| Helix (large) | 8 | 10 | 2 | 1 (Graufalk → Helix) | 1 |

Insgesamt gibt es nur **10 freie Plätze**. Team A beansprucht davon 4.

### 3.2 Neue Vereinbarungen (gerichtet, Verkäufer → Käufer)

Mit Bestandsfirmen planen wir nur in der Richtung **neue Firma → Bestandsfirma**. Dann ändern sich Märkte, Routen,
Verträge und Kunden der Bestandsfirmen nicht, denn diese entstehen immer beim Verkäufer. Die Bestandsstationen kommen
nur als zusätzliches Ziel neuer Routen vor.

```python
PARTNERSHIP_BLUEPRINT_TEAM_A = (
    # mit Bestandsfirmen
    ("graufalk", "helix", "supply_agreement"),        # Rumpfplatten, Triebwerksteile für die Helix-Flotte
    ("cindervale", "eisenkrone", "supply_agreement"), # KI-Leitsysteme, Robotik (Förster-Ausfälle)
    ("kuppelwerk", "lichtacker", "supply_agreement"), # Verbundstahl, Glaskeramik, Habitatmodule nach Tauvel/Myrrhen
    ("emberline", "corvane", "supply_agreement"),     # Helium-3 für Halcyon Works VI
    # innerhalb Team A
    ("cindervale", "graufalk", "supply_agreement"),
    ("graufalk", "cindervale", "strategic_alliance"),
    ("emberline", "graufalk", "supply_agreement"),
    ("kuppelwerk", "graufalk", "supply_agreement"),
    ("graufalk", "emberline", "supply_agreement"),
    ("emberline", "kuppelwerk", "supply_agreement"),
    ("emberline", "cindervale", "supply_agreement"),
    ("cindervale", "kometenpost", "consignment"),
    ("kometenpost", "cindervale", "logistics_partnership"),
    ("cindervale", "lanternfish", "supply_agreement"),
    ("lanternfish", "graufalk", "supply_agreement"),
)
OPTIONAL_PARTNERSHIPS_TEAM_A = (("lanternfish", "kometenpost", "consignment", 0.5),)
HISTORIC_PARTNERSHIPS_TEAM_A = (("eisenkrone", "graufalk", "supply_agreement"),)  # Ausgliederung der Werftsparte, beendet
```

Wir haben geprüft, dass jede Vereinbarung Routen erzeugen kann (Verbraucher-Stationstypen beim Käufer):

- graufalk → helix: Industriegüter gehen an `trade_hub`, `free_port` und `military`, alle bei Helix vorhanden.
- cindervale → eisenkrone: Technik geht an `mining` und `research`, beides bei Eisenkrone vorhanden.
- kuppelwerk → lichtacker: Industriegüter gehen an `agricultural` und `research`.
- emberline → corvane: Energie geht an `research` und `industrial`.
- kuppelwerk → graufalk: Industriegüter werden von `industrial` nicht nachgefragt. Die Route funktioniert über die
  Pflicht-Handelsstation in Orrin bzw. über `habitat_modules`/`sinter_blocks`, die `industrial` zusätzlich als
  Verbraucher führen.
- kometenpost → cindervale: Technik und Medizin gehen an `research`, `trade_hub` und `industrial`.
- lanternfish → graufalk: Luxusgüter gehen an `trade_hub` und `military`.

Gezählt ergibt das: Graufalk 7, Cindervale 7, Emberline 5, Kuppelwerk 3, Kometenpost 2 (mit optionaler Vereinbarung 3),
Lanternfish 2 (3). Alle liegen in ihrer Größenklasse. Unvollständig bleibt das Netz trotzdem: Kometenpost und Graufalk
haben keine direkte Vereinbarung, sind aber beide mit Cindervale verbunden. Das erfüllt die Prüfung
„≥2 Firmen nur über Zwischenhändler verbunden“.

### 3.3 Rivalitäten (an echten Ereignissen und Verträgen festgemacht)

```python
RIVALRY_BLUEPRINT_TEAM_A = (
    ("graufalk", "eisenkrone", "market_dominance", "halcyon"),
    # Anker: KI-Ausfälle Förster (Ereignisse 19/36/70), Ausgliederung (historische Partnerschaft)
    ("cindervale", "helix", "market_dominance", "sol"),
    # Anker: gebrochene Supraleiter-Verträge HMX-CTR-2057-0050/-2058-0121/-2057-0019, Bauboom Sol Exchange II (3, 24)
    ("emberline", "eisenkrone", "resource_competition", "myrrhen"),
    # Anker: gebrochene Energie-Lieferungen an Agrarstation Seip (EKM-VTR-2058-0099/-2059-0167/-2058-0105),
    # Asteroidensturm Hande (10), Piraten Seip/Löchel (27, 69)
)
```

Achtung: Der Text für `resource_competition` lautet heute fest „… konkurrieren um die Wassereis-Vorkommen …“. Für
Emberline braucht es eine eigene Formulierung, z. B. einen neuen Typ `energy_supply_competition` mit Texten in de/en
oder einen optionalen Text je Rivalität. Für Eisenkrone ergeben sich damit 3 Rivalitäten (Helix, Graufalk, Emberline).
Das ist gewollt, Eisenkrone ist der natürliche Gegenspieler im Kernraum.

### 3.4 Anknüpfungen für Rahmenverträge und Schriftverkehr

Diese Punkte sind Vorschläge für Phase 2. Neue Firmen können nicht Partei bestehender Verträge werden, aber sie können
sich in Schreiben und neuen Rahmenverträgen auf diese Verträge beziehen.

- **Kuppelwerk an Lichtacker (Hülya Matthäi, Toralf Gerlach)**: Angebot eines Rahmenvertrags „Verbundstahl und
  Habitatbaustoffe Tauvel/Myrrhen“ mit Bezug auf die gebrochenen Verträge HMX-CTR-2058-0159, -2057-0043, -2058-0139
  und -2057-0012.
- **Emberline an Corvane (Matthew Thomas)**: Rahmenvertrag Helium-3 mit Bezug auf HMX-CTR-2058-0131 und -2057-0014
  sowie den Asteroidensturm bei Halcyon Works VI (Ereignis 30).
- **Eisenkrone an Cindervale**: Mängelrüge zu den KI-Leitsystemen in Förster (Ereignisse 19, 36, 70); intern
  Ermittlungen von Mühle und Sölzer.
- **Graufalk an Helix**: Flottenrahmenvertrag; Begründung mit den Lieferverzögerungen durch Triebwerksschäden
  (86 Vorfälle) in den Helix-Korridoren Kharon → Aurelis und Kharon → Sol.
- **Kometenpost**: Werbeschreiben an Lichtacker/Helix mit Bezug auf HMX-CTR-2059-0197 und verspätete Lieferungen.
- **Bestehende Verträge unter neue Rahmenverträge stellen**: Das betrifft nur Paare von Bestandsfirmen, z. B. die
  zahlreichen Helix → Lichtacker-Verträge über Composite Steel. Das klärt Phase 2 gemeinsam mit Team B, siehe offene
  Fragen.

---

## 4. Neue Sternensysteme und Waren-Archetypen

### 4.1 Neues System: Pellora (sparsam, genau eines)

```python
StarSystem("pellora", "Pellora", (-58.0, -136.0, -92.0), 1, "high", "inner_ring",
           "Gasriese mit automatischen Helium-3-Schöpfwerken – die Tankstelle des inneren Rings.",
           "A gas giant whose automated helium-3 scoops make it the fuel depot of the inner ring."),
```

**Begründung**:

1. Stufe 1 hat heute nur zwei Systeme (Halcyon, Tauvel), dem Spieler fehlen also frühe Ziele.
2. Energie ist die schwächste legale Kategorie, und Sol hat keine Bergbaustation.
3. Die Helium-3-Lieferungen nach Halcyon kommen heute aus Aurelis (Stufe 2) und brechen.

Abstände: Sol 174, Halcyon 230, Myrrhen 226, Tauvel 256 Raumeinheiten. Damit ist Pellora so gut erreichbar wie Tauvel
(173 von Sol). Bestandsschutz: Das System wird **am Ende** von `STAR_SYSTEMS` angehängt, damit die `system_id` der
10 bestehenden Systeme gleich bleiben.

Orrin (vorhanden, leer) wird ohne Änderung genutzt. Isolde lassen wir für Team B frei.

### 4.2 Neue Archetypen (5 Stück, am Ende von `PRODUCT_ARCHETYPES`)

```python
# Energieträger
_archetype("fusion_pellets", "energy", "Fusionspellets", "Fusion Fuel Pellets", "crate", 5200, 0.06, 22,
           producers=("industrial",)),
# Industriegüter / Habitatbau
_archetype("habitat_modules", "industrial_goods", "Habitatmodule", "Habitat Modules", "unit", 46000, 14.0, 6200,
           extra_consumers=("industrial",)),
_archetype("sinter_blocks", "industrial_goods", "Sinterbausteine", "Sintered Regolith Blocks", "pallet", 380, 0.9,
           1400, extra_consumers=("industrial",)),
# Hochtechnologie
_archetype("quantum_relays", "technology", "Quantenrelais", "Quantum Comm Relays", "unit", 19500, 0.25, 28,
           "restricted"),
# Luxus- und Konsumgüter
_archetype("immersion_pods", "luxury", "Immersionskapseln", "Immersion Pods", "unit", 13500, 2.4, 260,
           producers=("industrial",)),
```

| Archetyp | Begründung | Hauptnutzer |
|---|---|---|
| `fusion_pellets` | Raffiniertes Endprodukt aus Helium-3 und Deuterium, damit Energie auch an `industrial`-Stationen entsteht; vergrößert den kleinsten Pool (20 → 24) | Emberline |
| `habitat_modules` | Baustoff für Habitate, den es heute nicht gibt; großvolumig, damit `typical_quantity` sinnvoll klein bleibt (medium: 11–37 Stück je Route) | Kuppelwerk, Graufalk |
| `sinter_blocks` | Billiges Massengut für den Bauboom (Gegenstück zu `regolith` mit nur 3 Produkten) | Kuppelwerk |
| `quantum_relays` | Kommunikations-Hochtechnologie, `restricted` → Genehmigungs-Spielmechanik | Cindervale, Kometenpost |
| `immersion_pods` | Komfortgut für Besatzungen (Idee aus idlestar `comfort_goods`), unterscheidet sich von `entertainment_electronics` | Lanternfish |

Codes und Namen haben wir gegen den Bestand geprüft, es gibt keine Überschneidungen. `CATEGORY_VARIANTS` und
`CATEGORY_*` bleiben unverändert. Neue Kategorien sind nicht nötig.

---

## 5. Bestandsschutz – technische Befunde für Phase 2

Das Skript nutzt **einen** gemeinsamen `world.rng` und **eine** Faker-Instanz je Sprache für alle Schritte. Hängt man
neue Firmen einfach an `COMPANY_PROFILES` an, verschieben sich die Zufallsfolgen in jedem Schritt. Danach hätten auch
die 6 Bestandsfirmen andere Stationen, Koordinaten, Produkte und Mitarbeiter. Unsere Empfehlungen:

1. **Getrennte Zufallsströme**: Bestandsfirmen erzeugen weiter mit `world.rng` in der bisherigen Reihenfolge. Neue
   Firmen erzeugen danach mit einem eigenen `random.Random(f"{seed}-ext")` (oder einem je Firmen-key) und eigenen
   Faker-Instanzen (`Faker.seed_instance`). In jedem Schritt laufen die Bestandsfirmen zuerst, dann die neuen.
2. **Archetyp-Pool**: `generate_products` baut den Pool aus *allen* Archetypen der Kategorie. Neue Archetypen würden
   also die Kataloge der Bestandsfirmen ändern. Deshalb sollten neue Archetypen nur für neue Firmen sichtbar sein,
   z. B. über eine Menge `EXTENSION_ARCHETYPES` oder ein Feld `introduced_with="extension"` am Archetyp.
3. **Stationsnamen**: `used_names` muss die Namen der Bestandsstationen enthalten, bevor neue Namen gezogen werden.
   Das ist automatisch erfüllt, wenn die neuen Firmen in derselben Funktion nach den alten erzeugt werden.
4. **Lagerkapazität**: `finalize_station_capacity` berechnet `storage_capacity_m3` aus Lager und Bestellungen. Bestandsstationen,
   die neue Lieferungen bekommen (z. B. Tauvel Labor II), bekämen dadurch eine größere Kapazität. Das ist eine
   abgeleitete Größe, die wir als „nachvollziehbare Änderung“ dokumentieren würden.
5. **Ereignisse**: Ereignisse greifen auf Nachbarstationen im selben System über. Neue Stationen in Sol, Halcyon und
   Aurelis können also von bestehenden Ereignissen mitbetroffen sein. Die Ereignisse der Bestandsfirmen sollten mit dem
   alten Strom vor denen der neuen geplant werden.
6. **Qualitätsprüfung**: „Sechs Firmen: 2/2/2“ muss auf die neue Firmenzahl (18 = 6/6/6) angepasst werden. Sinnvoll
   ist ein zusätzlicher Check „Stammdaten der Bestandsfirmen unverändert“ als Vergleich mit
   `space_trading_game_bestand.db` (Firmen, Stationen inkl. Koordinaten, Produkte, Mitarbeiter).
7. **IDs**: Bestandsfirmen behalten die IDs 1–6 und die Bestandssysteme 1–10, wenn neue Einträge nur angehängt werden.
   Stations-, Produkt- und Mitarbeiter-IDs der Bestandsfirmen bleiben nur stabil, wenn die neuen Firmen ihre Zeilen in
   jeder Tabelle **nach** den Bestandszeilen erzeugen (Schritt 1 sichert das ab).

---

## 6. Offene Fragen an Team B

1. **Freie Plätze bei Bestandsfirmen**: Passt die Aufteilung aus 3.1? Team A nimmt je einen Platz bei Helix,
   Eisenkrone, Lichtacker und Corvane. Für euch bleiben Helix 1, Eisenkrone 2, Lichtacker 1, Driftwood 2. Corvane und
   Feldspat sind danach voll. Falls ihr Corvane dringender braucht (z. B. für Medizin oder Biotech), tauschen wir: Dann
   beliefert Emberline Corvane nicht direkt, sondern Halcyon über Cindervale.
2. **Richtung**: Wollt ihr ebenfalls nur „neue Firma → Bestandsfirma“ anlegen (siehe Abschnitt 3.2: Routen und
   Verträge der Bestandsfirmen bleiben dann stabil)?
3. **Systeme und Archetypen**: Welche neuen System-Codes und Archetyp-Codes plant ihr? Wir belegen `pellora`,
   `fusion_pellets`, `habitat_modules`, `sinter_blocks`, `quantum_relays` und `immersion_pods`. Koordinaten von Pellora:
   (-58, -136, -92). Bitte haltet mindestens 100 Einheiten Abstand.
4. **Isolde**: Wir lassen Isolde (Stufe 3, Habitatmonde) frei. Plant ihr dort Stationen? Kuppelwerk würde später gern
   `habitat_modules` dorthin liefern, das ginge über eine Vereinbarung zwischen unseren Firmen.
5. **Verbindungen zwischen den Teams**: Unsere großen Firmen haben noch 1–3 freie Plätze (Graufalk und Cindervale je bis
   zu 3, Kuppelwerk bis zu 3). Habt ihr Rohstoff- oder Agrarlieferanten, die Graufalk oder Kuppelwerk beliefern sollen?
   Dann würde Kuppelwerk Habitatmodule an eure Kolonien liefern.
6. **SKU-Präfixe**: Wir verwenden GFW, CCI, KHB, EFF, KPK und LFL. Bitte nicht doppelt vergeben.

---

## 7. Prüfvermerk Neudurchlauf (21.10.2026)

Der Bericht wurde im erneuten Phase-1-Durchlauf gegen Skript und Bestands-DB nachgeprüft. Die 6 Firmen, das System
`pellora`, die 5 Archetypen und die SKU-Präfixe bleiben **unverändert**, weil `phase2_entscheidung.md` und
`verknuepfungen.json` (verbindlich) bereits darauf aufbauen. Ein neuer Entwurf würde diese Entscheidung entwerten.

Nachgeprüft (alle Werte bestätigt):

- Alle 20 zitierten Vertragsnummern gibt es, alle sind `breached`, die Werte stimmen (z. B. HMX-CTR-2058-0159 17,18 Mio.).
  Insgesamt sind 80 Verträge gebrochen (328,25 Mio. CR).
- Die Ereignisse 3, 8, 10, 18, 19, 24, 27, 29, 30, 34, 36, 37, 59, 69, 70 und 72 stimmen in Datum, Typ und Station.
  19, 36 und 70 sind Maschinenausfälle in Station 22 (Förster).
- Stationen je System: Sol 6, Halcyon 5, Tauvel 3, Aurelis 5, Myrrhen 3, **Orrin 0**, **Isolde 0**.
- Lücken je System bestätigt: Myrrhen Industriegüter 0 vs. 26 und Technik 0 vs. 17, Aurelis Industriegüter 3 vs. 22 und
  Rohstoffe 1 vs. 24, Sol Luxus 14 vs. 38 und Rohstoffe 1 vs. 40, Tauvel Energie und Technik 0 Angebote. Energie
  insgesamt 61 Angebote vs. 94 Nachfragen. 463 verspätete Lieferungen.
- Mitarbeiter-IDs, Rollen und Werte stimmen. Neu vermerkt sind die späten Einstellungsdaten (Mühle, van der Dussen,
  Schwartz, siehe Tabelle 1.2). Das deckt sich mit dem Datumshinweis in Phase 2.
- Präfixregel: GFW, CCI, KHB, EFF, KPK und LFL liegen alle im Bereich A–M, kollidieren nicht mit dem Bestand und nicht
  mit Team B (PKB, RCS, RVF, OSP, SGM, SHR).
- Eisenkrone wurde 2033 gegründet. Die Graufalk-Gründung 2035–2038 als Ausgliederung der Eisenkrone-Werftsparte ist
  damit zeitlich möglich.

Spätere Präzisierungen aus Phase 2 (siehe `phase2_entscheidung.md`) gehen vor diesem Bericht: Exklusivitäten sind
jetzt Vorkaufsrechte, `emberline → lichtacker` ist hinzugekommen, und statt eines neuen Rivalitätstyps werden
`RIVALRY_TEXT_OVERRIDES` verwendet.
