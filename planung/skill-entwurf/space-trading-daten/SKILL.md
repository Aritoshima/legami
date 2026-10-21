---
name: space-trading-daten
description: Erzeugt oder bearbeitet die synthetische Spieldaten-Basis des Space-Trading-Spiels (generate_space_trading_data.py, SQLite) in Phasen – Bestand sichern, planen, verknüpfen, umsetzen, abnehmen. Verwenden, wenn neue Firmen, Systeme, Waren, Verträge, Rahmenverträge, Schriftverkehr oder andere Datenbereiche hinzukommen oder bestehende geändert werden sollen ("füge Firmen hinzu", "erweitere die Daten um …", "ändere Firma X", "baue Tabelle Y ein").
---

# Space-Trading-Daten in Phasen erstellen oder bearbeiten

Dieser Skill beschreibt, wie die Datenbasis in `generate_space_trading_data.py` erweitert oder geändert wird, ohne den Bestand zu beschädigen. Hintergrund und Begründungen stehen in `planung/ERKENNTNISSE.md`.

## Grundregeln

- **Ein Skript.** Alles bleibt in `generate_space_trading_data.py` (nur faker, pandas, Standardbibliothek). Keine weiteren Module oder Abhängigkeiten.
- **Bestandsschutz.** Bei gleichem Seed bleiben alle bestehenden Zeilen identisch. Neue Firmen und neue Merkmale ziehen ihre Zufallszahlen aus eigenen Strömen (`derived_seed(seed, key, schritt)`, `World.company_stream`), nie zusätzlich aus `world.rng` vor bestehenden Schritten. Neue Systeme und Archetypen werden hinten angehängt.
- **Abnahme durch Prüfungen.** Jede neue Tabelle und jede Regel bekommt eine Prüfung in `run_quality_checks`. Fertig ist eine Änderung erst, wenn alle Prüfungen bei den Seeds 42, 7 und 123 bestehen und der Bestandsvergleich (`--baseline`) bei Seed 42 grün ist.
- **Grenzen.** Datenbank ≤ 50 MB (Dezimal-MB, das Skript zeigt MiB an), Laufzeit ≤ 75 s, Python 3.11.
- **Inhalt.** Nur fiktive Namen. Sprachen nur `de_DE` und `en_US`; Texte folgen der Sprache der jeweiligen Firma. Technische Bezeichner und Enums englisch in snake_case.
- **Ein Bearbeiter pro Datei.** Schritte, die das Skript ändern, laufen nacheinander. Parallel arbeiten nur Planungsschritte, die in eigene Dateien schreiben.

## Modus wählen

| Anfrage | Modus | Phasen |
|---|---|---|
| Neue Firmen, Systeme oder ganze Datenbereiche | Erweitern | 0 → 1 → 2 → 3 → 4 |
| Neues Merkmal ohne neue Firmen (z. B. eine Tabelle) | Merkmal | 0 → 2 (nur Design) → 3 → 4 |
| Werte einer bestehenden Firma oder Regel ändern | Bearbeiten | 0 → 3 → 4, Bestandsvergleich zeigt die gewollte Abweichung |
| Nur neu erzeugen (anderer Seed) | Erzeugen | `python generate_space_trading_data.py --seed N --output …` |

Beim Bearbeiten ist eine Abweichung vom Bestand gewollt: Sie wird in `planung/bestandsvergleich.md` begründet, danach wird die Referenz-Datenbank neu erzeugt.

## Phase 0 – Bestand sichern

1. Aktuellen Stand mit Seed 42 erzeugen: `python generate_space_trading_data.py --output /home/user/bestand/space_trading_game_bestand.db`.
2. `planung/bestand_uebersicht.md` aktualisieren: Zeilen je Tabelle, Stationen je System, Angebot und Nachfrage je Warenkategorie, aktive Vereinbarungen, Schlüsselmitarbeiter, Finanzen.
3. Committen. Die Datenbank selbst gehört nicht ins Repo (`.gitignore` enthält `*.db`).

## Phase 1 – Planung und Recherche

- Bei mehreren Bearbeitern: Themenfelder klar trennen und SKU-Präfixe aufteilen (Team A A–M, Team B N–Z).
- Jeder wertet den Bestand per SQL aus und sucht echte Lücken und Anknüpfungspunkte (Systeme ohne Stationen, unterversorgte Kategorien, gebrochene Verträge, Ereignisse, Schlüsselmitarbeiter mit Einstellungsdatum).
- Jede neue Firma braucht alle Felder von `CompanyProfile`; Größenklasse und Mengen folgen `SIZE_PROFILES`. Firmen mit Schwarzmarktware brauchen eine Station, die `is_illegal_market` erfüllt.
- Ergebnis: `planung/phase1_<team>.md`, dazu ein angehängter Eintrag in `planung/NACHRICHTEN.md` (nur anhängen, nie überschreiben).

## Phase 2 – Verknüpfungen und Entscheidung

- Jeder liest alle Phase-1-Berichte und schlägt Verknüpfungen vor: gerichtete Vereinbarungen (Verkäufer → Käufer), historische Partnerschaften, Rivalitäten, Rahmenverträge mit Nachträgen, Schriftverkehr-Vorgänge.
- Regeln für das Netz (aktive Vereinbarungen je Firma, beide Richtungen gezählt): small 1–3, medium 3–6, large 6–10; zusammenhängend, aber unvollständig; mindestens ein großer Hub; mindestens zwei Paare nur über Zwischenhändler verbunden; jede Firma mindestens eine ausgehende Vereinbarung; der Käufer hat Stationen, die die Waren konsumieren (`CATEGORY_CONSUMERS`).
- Ein Schiedsrichter vergleicht die Vorschläge, übernimmt die besseren Elemente, zählt die Regeln selbst nach und prüft Klauseln und Personen gegen den Bestand.
- Ergebnis: `planung/phase2_entscheidung.md` und die verbindliche Vorlage `planung/verknuepfungen.json`.

## Phase 3 – Umsetzung (nacheinander)

1. **Integration:** Firmen, Systeme, Archetypen und Verknüpfungen aus `verknuepfungen.json` direkt in die Tupel des Skripts übernehmen. Für neue Schritte eigene Ströme verwenden; Schritte über alle Zeilen in „Bestand, dann Erweiterung“ teilen.
2. **Merkmale:** jedes neue Merkmal als eigener Generierungsschritt in `PIPELINE`, mit Schema (Fremdschlüssel, CHECKs, Indizes), `PRIMARY_KEYS`, `INSERT_ORDER`, Docstring und Zusammenfassung. Bisher vorhanden: Rahmenverträge (Schritte 5 und 15), Schriftverkehr (Schritt 16).
3. Nach jedem Teilschritt: Skript ausführen, alle Prüfungen grün, committen.

## Phase 4 – Abnahme

- `python generate_space_trading_data.py --output /tmp/check.db` für die Seeds 42, 7 und 123; alle Prüfungen bestanden.
- Bestandsvergleich bei Seed 42 grün bzw. gewollte Abweichungen in `planung/bestandsvergleich.md` begründet.
- Größe und Laufzeit innerhalb der Grenzen; Stichproben der neuen Texte lesen (Sprache, Bezüge, Daten).
- `planung/ERKENNTNISSE.md` um neue Erkenntnisse ergänzen; bei Bedarf das Dashboard aktualisieren.

## Mit mehreren Agenten

- Planungsphasen dürfen parallel laufen, Umsetzungsschritte am Skript nicht.
- Nach jeder Phase committen, damit ein Abbruch (Session-Limit) nichts kostet.
- Einen abgebrochenen Schritt einzeln neu starten, statt einen ganzen Workflow fortzusetzen; vorher prüfen, was schon in `planung/` liegt.
