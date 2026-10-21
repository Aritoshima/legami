#!/usr/bin/env python3
"""
generate_space_trading_data.py
==============================

Erzeugt einen zusammenhängenden, synthetischen Datensatz für ein Space-Trading-Spiel
und schreibt ihn in eine normalisierte SQLite-Datenbank.

Hintergrund der Spielwelt
-------------------------
Ab 2030 übernehmen KI-Systeme große Teile der Industrie. Die Konzerne lassen ihre Hütten,
Werften und Schürfdrohnen von KI-Leitsystemen betreiben und bauen damit bis in die 2050er
eine automatisierte Infrastruktur im All auf. Am 1. Januar 2060 (Stichtag der Daten) wird
der Weltraum für freie Händler geöffnet – das ist der Spielstart. Alle Historien
(Bestellungen, Verträge, Preise) liegen vor diesem Stichtag; Vertragsentwürfe und
laufende Lieferungen reichen in die Zukunft.

Die Sternensysteme haben eine Freischaltstufe (`unlock_tier`): Sol ist ab Spielbeginn
erreichbar, weiter entfernte Systeme werden nach und nach freigeschaltet.

Firmen, Bestandsschutz und Rahmenverträge
-----------------------------------------
Die Welt enthält 18 Raumhandelsgesellschaften (je 6 small/medium/large, Deutsch und Englisch).
Die ersten sechs Firmen sind der „Bestand“: Ihre Daten entstehen in jedem Schritt zuerst und mit
dem gemeinsamen Zufallsstrom (`world.rng`, Faker-Instanzen je Sprache) – genau wie vor der
Erweiterung. Die zwölf neuen Firmen erzeugen ihre Daten danach in eigenen Zufallsströmen, die aus
(Seed, Firmen-key, Schritt) abgeleitet sind („Durchlauf 2“). Neue Firmen verschieben die
Zufallsfolge der Bestandsfirmen deshalb nicht: Bei Seed 42 sind alle Bestandszeilen identisch mit
dem Datenstand vor der Erweiterung. Neue Vereinbarungen mit Bestandsfirmen gibt es nur in der
Richtung „neue Firma → Bestandsfirma“, damit Routen, Verträge und Kunden der Bestandsfirmen
stabil bleiben.

Rahmenverträge (`framework_agreements`) bündeln die Einzelverträge eines Paares. Nachträge
(`framework_agreement_amendments`) erweitern Sortiment, Volumen und Laufzeit; Regel-Nachträge
werden aus den Einzelverträgen abgeleitet (erster Abruf einer Kategorie, kumulierte Summe über
90 % des Rahmenvolumens, Abruf nach Laufzeitende) und liegen immer zeitlich vor den Verträgen, die
sie nutzen. `framework_agreement_scope` hält das Sortiment mit Gültigkeitszeiträumen,
`contracts.framework_agreement_id` die Zuordnung der Einzelverträge.

Schriftverkehr
--------------
`correspondence` hält einige tausend Schreiben zwischen den Firmen (und an Nicht-Firmenkunden): Anfragen,
Angebote und Gegenangebote vor der Unterzeichnung eines Rahmens, Bestätigungen zum Vertragsstart, Nachtragsangebote
und -bestätigungen an den Daten der Nachträge, Lieferavise, Verzögerungsmeldungen, Verzugsbeschwerden,
Strafbescheide (gleiche Strafformel wie die Finanzdaten), Mahnstufen, Abmahnungen, Kündigungen, Aussetzungen,
Proteste unter Rivalen, interne Notizen sowie vertrauliche Tipps und Gerüchte. Vertrauliche Schreiben sind
Spionageziele: Mitarbeiter mit hoher Bestechlichkeit oder geringer Loyalität verraten sie an Rivalen.
Absender und Empfänger sind Mitarbeiter der jeweiligen Firma, die am Versandtag beschäftigt sind; der Text steht in
der Sprache der Absenderfirma. `correspondence_copies` hält Kopienempfänger. Der Schriftverkehr entsteht als letzter
Schritt in einem eigenen Zufallsstrom und liest die übrigen Tabellen nur; bei Seed 42 sind zusätzlich die
verankerten Vorgänge V1–V41 aus der Planung mit echten Bestandsobjekten umgesetzt.

Aufruf
------
    pip install faker pandas
    python generate_space_trading_data.py
    python generate_space_trading_data.py --seed 42 --output space_trading_game.db
    python generate_space_trading_data.py --baseline ../bestand/space_trading_game_bestand.db

Mit `--baseline` (Standard: `../bestand/space_trading_game_bestand.db` neben dem Skriptordner,
falls vorhanden) vergleicht die Qualitätsprüfung bei Seed 42 die Bestandszeilen mit dem alten
Datenstand.

Abhängigkeiten: Python 3.11+, faker, pandas, Standardbibliothek (sqlite3).
Alle Namen von Firmen, Personen und Orten sind fiktiv.
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import math
import random
import sqlite3
import sys
import time
from collections import defaultdict, deque
from collections.abc import Callable, Hashable, Iterable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, TypeVar

import pandas as pd
from faker import Faker

# ---------------------------------------------------------------------------
# Globale Konstanten
# ---------------------------------------------------------------------------

DEFAULT_SEED = 42
DEFAULT_OUTPUT = "space_trading_game.db"
BASELINE_SEED = 42  # Seed des Bestandsdatenstands
DEFAULT_BASELINE = Path(__file__).resolve().parent.parent / "bestand" / "space_trading_game_bestand.db"

GAME_REFERENCE_DATE = date(2060, 1, 1)
GAME_REFERENCE_DATETIME = datetime(2060, 1, 1, 0, 0, 0)
CURRENCY_CODE = "CR"

CRUISE_SPEED_UNITS_PER_HOUR = 6.0  # Raumeinheiten pro Stunde
DOCKING_OVERHEAD_HOURS = 3.0  # Ab- und Andocken, Freigaben
PRICE_HISTORY_INTERVAL_DAYS = 14
PRICE_ELASTICITY = 0.45
PAYMENT_TERMS_DAYS = 30

FUEL_COST_PER_DISTANCE_UNIT = 22.0  # Grundverbrauch eines Frachters je Raumeinheit
FUEL_COST_PER_TONNE_DISTANCE = 0.006  # Zusatzverbrauch je Tonne Ladung und Raumeinheit
ILLEGAL_INSURANCE_SURCHARGE = 0.03

MIN_TOTAL_STATIONS = 30
MIN_PARTNER_ROUTES_PER_AGREEMENT = 4
COORDINATE_LIMIT = 500.0

LANGUAGES = ("de_DE", "en_US")
SIZE_CLASSES = ("small", "medium", "large")
SECURITY_LEVELS = ("high", "medium", "low", "lawless")
RISK_LEVELS = ("low", "medium", "high", "extreme")
ILLEGAL_MARKET_STATION_TYPES = frozenset({"smuggler_haven", "free_port"})
ILLEGAL_MARKET_SECURITY = frozenset({"low", "lawless"})

ORDER_STATUSES = ("pending", "confirmed", "in_transit", "delivered", "delayed", "cancelled")
SHIPMENT_STATUSES = ("pending", "in_transit", "delayed", "delivered")
PAYMENT_STATUSES = ("unpaid", "invoiced", "partially_paid", "paid", "overdue", "void", "refunded")
CONTRACT_STATUSES = ("draft", "active", "completed", "breached", "cancelled")

# Zulässige Kombinationen von Bestell- und Zahlungsstatus
ALLOWED_PAYMENT_BY_ORDER_STATUS: dict[str, frozenset[str]] = {
    "pending": frozenset({"unpaid"}),
    "confirmed": frozenset({"unpaid", "invoiced"}),
    "in_transit": frozenset({"invoiced", "partially_paid"}),
    "delayed": frozenset({"invoiced", "partially_paid"}),
    "delivered": frozenset({"invoiced", "paid", "overdue"}),
    "cancelled": frozenset({"void", "refunded"}),
}

SECURITY_RISK_SCORE = {"high": 0.0, "medium": 1.0, "low": 2.0, "lawless": 3.0}
SECURITY_PRICE_PREMIUM = {"high": 1.00, "medium": 1.04, "low": 1.10, "lawless": 1.18}
DELAY_PROBABILITY = {"low": 0.03, "medium": 0.06, "high": 0.12, "extreme": 0.20}
INSURANCE_RATE = {"low": 0.002, "medium": 0.005, "high": 0.012, "extreme": 0.025}
TARIFF_RATE = {"high": 0.06, "medium": 0.045, "low": 0.025, "lawless": 0.0}  # Einfuhrzoll am Zielort
BLACK_MARKET_FEE_RATE = 0.15  # Schutz- und Schmiergelder statt Zoll bei Schwarzmarktware

T = TypeVar("T")
K = TypeVar("K", bound=Hashable)


# ---------------------------------------------------------------------------
# Stammdaten-Definitionen (Größenklassen, Systeme, Stationstypen, Firmen, Waren)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SizeProfile:
    """Mengengerüst und Wirtschaftskennzahlen einer Unternehmensgröße."""

    customers: tuple[int, int]
    products: tuple[int, int]
    stations: tuple[int, int]
    contracts: tuple[int, int]
    orders: tuple[int, int]
    months: int
    employees: tuple[int, int]
    agreements: tuple[int, int]
    hold_capacity_m3: float
    max_haul_value: float
    storage_factor: float
    starting_cash: tuple[float, float]
    salary_factor: float
    upkeep_factor: float
    fleet_cost_per_ship: float
    population_factor: float
    order_share: tuple[float, float]  # Anteil der typischen Routenmenge je Bestellposition


SIZE_PROFILES: dict[str, SizeProfile] = {
    "small": SizeProfile(
        customers=(15, 25), products=(20, 35), stations=(2, 3), contracts=(20, 40),
        orders=(100, 200), months=12, employees=(12, 24), agreements=(1, 3),
        hold_capacity_m3=1_800.0, max_haul_value=600_000.0, storage_factor=1.0,
        starting_cash=(1_500_000.0, 3_000_000.0), salary_factor=0.85, upkeep_factor=0.25,
        fleet_cost_per_ship=20_000.0, population_factor=0.15, order_share=(0.35, 0.9),
    ),
    "medium": SizeProfile(
        customers=(40, 70), products=(50, 90), stations=(4, 6), contracts=(60, 120),
        orders=(400, 800), months=24, employees=(40, 80), agreements=(3, 6),
        hold_capacity_m3=3_000.0, max_haul_value=1_500_000.0, storage_factor=2.2,
        starting_cash=(12_000_000.0, 25_000_000.0), salary_factor=1.0, upkeep_factor=0.6,
        fleet_cost_per_ship=180_000.0, population_factor=0.5, order_share=(0.15, 0.6),
    ),
    "large": SizeProfile(
        customers=(100, 180), products=(120, 220), stations=(7, 12), contracts=(150, 300),
        orders=(1_200, 2_500), months=36, employees=(120, 220), agreements=(6, 10),
        hold_capacity_m3=6_000.0, max_haul_value=4_000_000.0, storage_factor=4.5,
        starting_cash=(80_000_000.0, 160_000_000.0), salary_factor=1.15, upkeep_factor=1.0,
        fleet_cost_per_ship=900_000.0, population_factor=1.0, order_share=(0.1, 0.55),
    ),
}


@dataclass(frozen=True)
class StarSystem:
    """Ein Sternensystem der Spielwelt."""

    code: str
    name: str
    center: tuple[float, float, float]
    unlock_tier: int
    base_security: str
    sector_code: str
    description_de: str
    description_en: str


STAR_SYSTEMS: tuple[StarSystem, ...] = (
    StarSystem("sol", "Sol", (0.0, 0.0, 0.0), 0, "high", "core",
               "Heimatsystem der Menschheit. Erde, Luna und Mars bilden das Rückgrat der KI-gesteuerten Industrie.",
               "Humanity's home system. Earth, Luna and Mars form the backbone of the AI-run industry."),
    StarSystem("halcyon", "Halcyon", (118.0, -64.0, 37.0), 1, "high", "inner_ring",
               "Ruhiges Doppelsternsystem mit Forschungsstationen und strengen Sterilauflagen.",
               "A calm binary system known for research stations and strict sterile protocols."),
    StarSystem("tauvel", "Tauvel", (-142.0, 96.0, -22.0), 1, "high", "inner_ring",
               "Sonnenreiches System, dessen Hydrokultur-Ringe den inneren Ring ernähren.",
               "A sun-rich system whose hydroponic rings feed the inner ring."),
    StarSystem("aurelis", "Aurelis", (64.0, 188.0, -84.0), 2, "medium", "middle_belt",
               "Handelsknoten im Mittelgürtel mit dichtem Frachtverkehr.",
               "A trade junction in the Middle Belt with dense freight traffic."),
    StarSystem("myrrhen", "Myrrhen", (-226.0, -148.0, 58.0), 2, "medium", "middle_belt",
               "Eisreiches System mit Wasserabbau und ersten Agrarkolonien.",
               "An ice-rich system with water mining and early agricultural colonies."),
    StarSystem("orrin", "Orrin", (252.0, 44.0, 142.0), 2, "medium", "middle_belt",
               "Industriell erschlossenes System am Übergang zum äußeren Rand.",
               "An industrialised system on the edge of the Outer Rim."),
    StarSystem("brennus", "Brennus", (334.0, -212.0, -118.0), 3, "low", "outer_rim",
               "Dichter Asteroidengürtel voller Erze – und voller Gefahren.",
               "A dense asteroid belt full of ore – and full of hazards."),
    StarSystem("isolde", "Isolde", (-338.0, 262.0, 152.0), 3, "medium", "outer_rim",
               "Abgelegenes System mit fruchtbaren Habitatmonden.",
               "A remote system with fertile habitat moons."),
    StarSystem("kharon", "Kharon", (418.0, 296.0, -204.0), 4, "low", "frontier",
               "Grenzsystem, in dem Recht oft eine Verhandlungsfrage ist.",
               "A frontier system where law is often a matter of negotiation."),
    StarSystem("nyx", "Nyx", (-432.0, -384.0, -262.0), 4, "lawless", "frontier",
               "Gesetzloses Wracksystem – Heimat von Bergern, Schmugglern und Piraten.",
               "A lawless graveyard of wrecks – home to salvagers, smugglers and pirates."),
    # Erweiterung (hinten angehängt, damit die system_id der Bestandssysteme gleich bleiben)
    StarSystem("pellora", "Pellora", (-58.0, -136.0, -92.0), 1, "high", "inner_ring",
               "Gasriese mit automatischen Helium-3-Schöpfwerken – die Tankstelle des inneren Rings.",
               "A gas giant whose automated helium-3 scoops make it the fuel depot of the inner ring."),
    StarSystem("vaskar", "Vaskar", (-462.0, 438.0, 336.0), 5, "low", "far_reach",
               "Gasriese mit Eismonden jenseits von Isolde – Tankstelle und Kühlkammer der Kolonisierung.",
               "A gas giant ringed by ice moons beyond Isolde – fuel depot and cold store of colonisation."),
    StarSystem("serravel", "Serravel", (412.0, -96.0, 388.0), 5, "medium", "far_reach",
               "Junge Terraforming-Welt mit dünner Atmosphäre; Siedler, Vermesser und Konzerngarnisonen teilen "
               "sich die ersten Kuppelstädte.",
               "A young terraforming world with a thin atmosphere; settlers, surveyors and corporate garrisons "
               "share the first domed towns."),
)

SECTOR_LABELS: dict[str, dict[str, str]] = {
    "core": {"de_DE": "Kernsektor", "en_US": "Core Sector"},
    "inner_ring": {"de_DE": "Innerer Ring", "en_US": "Inner Ring"},
    "middle_belt": {"de_DE": "Mittelgürtel", "en_US": "Middle Belt"},
    "outer_rim": {"de_DE": "Äußerer Rand", "en_US": "Outer Rim"},
    "frontier": {"de_DE": "Grenzland", "en_US": "Frontier"},
    "far_reach": {"de_DE": "Ferne Weiten", "en_US": "Far Reach"},
}

SECURITY_LABELS: dict[str, dict[str, str]] = {
    "high": {"de_DE": "hoch", "en_US": "high"},
    "medium": {"de_DE": "mittel", "en_US": "medium"},
    "low": {"de_DE": "niedrig", "en_US": "low"},
    "lawless": {"de_DE": "gesetzlos", "en_US": "lawless"},
}


@dataclass(frozen=True)
class StationTypeInfo:
    """Lokalisierte Bezeichnungen und Kennzahlen eines Stationstyps."""

    label_de: str
    label_en: str
    suffix_de: str
    suffix_en: str
    population: tuple[int, int]
    base_upkeep: float
    base_storage_m3: float
    purpose_de: str
    purpose_en: str


STATION_TYPES: dict[str, StationTypeInfo] = {
    "trade_hub": StationTypeInfo("Handelsstation", "Trade Station", "Kontor", "Exchange", (20_000, 250_000),
                                 180_000, 60_000, "Umschlagplatz für Waren aller Art",
                                 "a transshipment point for all kinds of goods"),
    "industrial": StationTypeInfo("Industriestation", "Industrial Station", "Werk", "Works", (5_000, 60_000),
                                  260_000, 80_000, "verarbeitet Rohstoffe zu Fertigwaren",
                                  "turns raw materials into finished goods"),
    "mining": StationTypeInfo("Bergbaustation", "Mining Station", "Schacht", "Deep", (300, 8_000),
                              90_000, 45_000, "fördert Erze, Eis und Gase aus dem Umfeld",
                              "extracts ore, ice and gases from its surroundings"),
    "research": StationTypeInfo("Forschungsstation", "Research Station", "Labor", "Institute", (200, 5_000),
                                140_000, 12_000, "entwickelt Medizin und Hochtechnologie",
                                "develops medicine and high technology"),
    "agricultural": StationTypeInfo("Agrarstation", "Agricultural Station", "Gartenring", "Gardens",
                                    (2_000, 40_000), 110_000, 35_000, "produziert Lebensmittel in Hydrokultur",
                                    "grows food in hydroponic rings"),
    "free_port": StationTypeInfo("Freihafen", "Free Port", "Freihafen", "Landing", (3_000, 50_000),
                                 120_000, 40_000, "handelt zollfrei und stellt wenige Fragen",
                                 "trades duty-free and asks few questions"),
    "military": StationTypeInfo("Militärstation", "Military Outpost", "Bastion", "Bastion", (1_000, 15_000),
                                220_000, 25_000, "sichert die Handelswege des Systems",
                                "secures the system's trade lanes"),
    "smuggler_haven": StationTypeInfo("Schmugglerhafen", "Smugglers' Haven", "Schattenhafen", "Hollow",
                                      (300, 6_000), 40_000, 15_000, "dient als Umschlagplatz für Schwarzmarktware",
                                      "serves as a hub for black-market goods"),
}


@dataclass(frozen=True)
class CompanyProfile:
    """Steckbrief einer der 18 Raumhandelsgesellschaften (6 Bestandsfirmen, 12 Erweiterungsfirmen)."""

    key: str
    name: str
    slug: str
    language: str
    size_class: str
    specialization: str
    network_role: str
    sku_prefix: str
    home_system: str
    territory: dict[str, float]
    required_stations: tuple[tuple[str, str], ...]
    station_type_weights: dict[str, float]
    category_weights: dict[str, float]
    founded_range: tuple[int, int]
    credit_ratings: tuple[str, ...]
    loyalty_bias: int
    description: str
    fleet: tuple[str, ...]


COMPANY_PROFILES: tuple[CompanyProfile, ...] = (
    CompanyProfile(
        key="feldspat", name="Feldspat Orbitalbergbau GmbH", slug="feldspat-orbitalbergbau",
        language="de_DE", size_class="small", specialization="asteroid_mining",
        network_role="raw_material_supplier", sku_prefix="FSP", home_system="brennus",
        territory={"brennus": 3.0, "kharon": 1.5},
        required_stations=(("mining", "brennus"),),
        station_type_weights={"mining": 4.0, "trade_hub": 1.0},
        category_weights={"raw_materials": 0.62, "energy": 0.23, "industrial_goods": 0.10, "luxury": 0.05},
        founded_range=(2049, 2054), credit_ratings=("BB", "BB+", "BBB-"), loyalty_bias=8,
        description=(
            "Die {name} wurde {year} von {founder} gegründet, als autonome Schürfdrohnen den "
            "Asteroidenbergbau erstmals bezahlbar machten. Das kleine Unternehmen fördert Erze, Wassereis "
            "und Helium-3 im Brennus-System und verkauft fast die gesamte Förderung an die großen "
            "Industriekonzerne. Gilt als zuverlässig, ist aber chronisch knapp bei Kasse – ein dankbarer "
            "Partner für jeden, der pünktlich zahlt."
        ),
        fleet=("Erzschwalbe", "Tiefgang", "Glück Auf", "Steinbeißer", "Schürfgeist", "Kieselwind"),
    ),
    CompanyProfile(
        key="driftwood", name="Driftwood Salvage & Supply Co.", slug="driftwood-salvage",
        language="en_US", size_class="small", specialization="salvage_and_grey_trade",
        network_role="fringe_trader", sku_prefix="DWS", home_system="nyx",
        territory={"nyx": 3.0, "kharon": 1.5},
        required_stations=(("smuggler_haven", "nyx"), ("free_port", "kharon")),
        station_type_weights={"smuggler_haven": 2.0, "free_port": 2.0, "mining": 1.0},
        category_weights={"contraband": 0.30, "technology": 0.20, "luxury": 0.20,
                          "raw_materials": 0.15, "industrial_goods": 0.15},
        founded_range=(2051, 2056), credit_ratings=("B-", "B", "CCC+"), loyalty_bias=-15,
        description=(
            "{name} was founded in {year} by {founder}, a former salvage pilot who never asked too many "
            "questions. Operating out of the lawless Nyx system, the company strips derelicts, resells "
            "salvaged technology and – officially never – moves goods that no customs office would clear. "
            "Small, nimble and well connected on the fringe, but only one serious corporation still does "
            "business with it."
        ),
        fleet=("Rusty Promise", "Night Heron", "Second Chance", "Quiet Margin", "Loose Change"),
    ),
    CompanyProfile(
        key="lichtacker", name="Lichtacker Agrarsysteme AG", slug="lichtacker-agrarsysteme",
        language="de_DE", size_class="medium", specialization="hydroponic_agriculture",
        network_role="food_supplier", sku_prefix="LAK", home_system="tauvel",
        territory={"tauvel": 3.0, "myrrhen": 2.0, "isolde": 2.0, "aurelis": 0.5},
        required_stations=(("agricultural", "tauvel"),),
        station_type_weights={"agricultural": 4.0, "trade_hub": 1.0, "research": 1.0},
        category_weights={"food": 0.58, "luxury": 0.14, "medical": 0.10, "raw_materials": 0.10,
                          "industrial_goods": 0.08},
        founded_range=(2040, 2045), credit_ratings=("BBB+", "A-"), loyalty_bias=5,
        description=(
            "Die {name} entstand {year}, als {founder} die ersten vollautomatisierten Hydrokultur-Ringe "
            "im Tauvel-System in Betrieb nahm. Heute versorgt das Unternehmen Stationsbesatzungen und "
            "Bergbaukolonien mit Gemüse, Proteinpasten und Kulturfleisch. Ernteausfälle treffen den Konzern "
            "hart, gute Ernten machen ihn zum wichtigsten Lebensmittellieferanten des inneren Rings."
        ),
        fleet=("Saatkorn", "Ährenwind", "Grünspross", "Morgentau", "Erntemond", "Kleeblatt", "Sonnenhof"),
    ),
    CompanyProfile(
        key="corvane", name="Corvane Biomedical Inc.", slug="corvane-biomedical",
        language="en_US", size_class="medium", specialization="biomedical_research",
        network_role="specialist_supplier", sku_prefix="CVB", home_system="halcyon",
        territory={"halcyon": 3.0, "aurelis": 2.0, "orrin": 1.5, "sol": 0.5},
        required_stations=(("research", "halcyon"),),
        station_type_weights={"research": 3.0, "trade_hub": 1.0, "industrial": 1.0, "agricultural": 1.0},
        category_weights={"medical": 0.50, "technology": 0.20, "food": 0.12, "luxury": 0.05,
                          "raw_materials": 0.05, "energy": 0.08},
        founded_range=(2042, 2047), credit_ratings=("A-", "A"), loyalty_bias=0,
        description=(
            "Founded in {year} by {founder}, {name} turned AI-driven drug discovery into a spacefaring "
            "business. Its research stations produce pharmaceuticals, vaccines and nanomedicine under strict "
            "sterile protocols. Corvane guards its formulas jealously – rumour has it that a former partner "
            "tried to sell stolen samples on the black market."
        ),
        fleet=("Sterile Horizon", "Mercy Run", "Petri Star", "Cold Chain", "Antigen", "Clean Room"),
    ),
    CompanyProfile(
        key="eisenkrone", name="Eisenkrone Montan- und Industrie-AG", slug="eisenkrone-montan",
        language="de_DE", size_class="large", specialization="heavy_industry",
        network_role="industrial_core", sku_prefix="EKM", home_system="sol",
        territory={"sol": 3.0, "halcyon": 2.0, "myrrhen": 2.0, "brennus": 2.0, "aurelis": 1.0, "orrin": 1.0},
        required_stations=(("industrial", "sol"), ("mining", "brennus")),
        station_type_weights={"industrial": 4.0, "mining": 3.0, "trade_hub": 1.0, "military": 1.0,
                              "research": 0.5},
        category_weights={"raw_materials": 0.22, "energy": 0.10, "industrial_goods": 0.38, "technology": 0.18,
                          "food": 0.04, "medical": 0.03, "luxury": 0.05},
        founded_range=(2031, 2034), credit_ratings=("A+", "AA-"), loyalty_bias=3,
        description=(
            "Die {name} wurde {year} von {founder} gegründet und war einer der ersten Konzerne, die ihre "
            "Hütten und Walzwerke vollständig an KI-Leitsysteme übergaben. Von Luna aus steuert sie heute "
            "Schmelzöfen, Werften und Bergbaustationen in mehreren Systemen. Eisenkrone kauft Rohstoffe in "
            "großen Mengen, liefert Verbundstahl, Reaktorkomponenten und Maschinen – und betrachtet jeden "
            "anderen Großkonzern als Konkurrenten."
        ),
        fleet=("Amboss", "Hammerschlag", "Schmiedefeuer", "Walzwerk", "Stahlriese", "Glutkern", "Hochofen",
               "Nordwall", "Bergfried", "Schwerlast", "Eisenfaust", "Funkenflug"),
    ),
    CompanyProfile(
        key="helix", name="Helix Meridian Trading Consortium", slug="helix-meridian",
        language="en_US", size_class="large", specialization="interstellar_trade",
        network_role="central_hub", sku_prefix="HMX", home_system="sol",
        territory={"sol": 3.0, "tauvel": 1.5, "halcyon": 1.5, "aurelis": 1.5, "orrin": 1.5, "isolde": 1.0,
                   "myrrhen": 1.0, "kharon": 1.0},
        required_stations=(("trade_hub", "sol"), ("free_port", "kharon")),
        station_type_weights={"trade_hub": 4.0, "free_port": 1.5, "military": 0.5, "research": 1.0,
                              "agricultural": 0.5},
        category_weights={"raw_materials": 0.08, "energy": 0.08, "industrial_goods": 0.14, "technology": 0.18,
                          "food": 0.12, "medical": 0.10, "luxury": 0.25, "contraband": 0.05},
        founded_range=(2033, 2037), credit_ratings=("AA", "AA+"), loyalty_bias=0,
        description=(
            "{name} was established in {year} by {founder} as an AI-run commodity exchange and grew into "
            "the central trading hub between Sol and the frontier. It owns trade stations and free ports "
            "across the inner ring and beyond, buys from almost everyone and sells almost everything. "
            "Whoever wants to reach the wider market eventually has to deal with Helix Meridian – on "
            "Helix Meridian's terms."
        ),
        fleet=("Meridian Star", "Golden Ledger", "Silk Comet", "Grand Exchange", "Long Haul", "Fair Wind",
               "Bright Margin", "Open Ledger", "Quiet Fortune", "Cross Current", "High Tide", "Trade Wind"),
    ),
    # ----- Erweiterung Team A: Kernraum, Hochtechnologie und Infrastruktur -----
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
            "abstieß. Aus den alten Trockendocks wurde der größte Werftverbund außerhalb Sols: KI-gesteuerte "
            "Hellinge fertigen Rumpfplatten, Triebwerksteile, Reaktorkomponenten und Lebenserhaltungsmodule. "
            "Graufalk baut die Schiffe, mit denen die Konzerne – und bald auch freie Händler – das All befahren, "
            "und hat mit der Eisenkrone noch eine offene Rechnung."
        ),
        fleet=("Kielholer", "Spantenriese", "Stapellauf", "Werftfeuer", "Nietenhammer", "Dockmeister", "Ankerlicht",
               "Helling", "Bugwelle", "Kranlicht", "Stahlkiel", "Graufalke"),
    ),
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
            "{name} was founded in {year} by {founder}, only months after the first AI systems took over factory "
            "floors on Earth. Its compute foundries in Sol and Halcyon produce AI cores, robotics units and sensor "
            "arrays, and its control software runs half the automated plants of the inner ring – including, some "
            "say, the ones that keep failing. Cindervale sells the minds of the machine age and is never shy about "
            "the price."
        ),
        fleet=("Quiet Inference", "Gradient Descent", "Parallel Light", "Deep Cache", "Clean Compile", "Long Context",
               "Bright Kernel", "Null Pointer", "Warm Start", "Edge Case", "Soft Landing", "Open Weights"),
    ),
    CompanyProfile(
        key="kuppelwerk", name="Kuppelwerk Habitatbau AG", slug="kuppelwerk-habitatbau",
        language="de_DE", size_class="medium", specialization="habitat_construction",
        network_role="construction_supplier", sku_prefix="KHB", home_system="aurelis",
        territory={"aurelis": 3.0, "myrrhen": 1.5, "tauvel": 1.5, "sol": 1.0},
        required_stations=(("industrial", "aurelis"), ("mining", "myrrhen"), ("mining", "aurelis")),
        station_type_weights={"industrial": 3.0, "mining": 2.0, "trade_hub": 1.0},
        category_weights={"industrial_goods": 0.55, "raw_materials": 0.25, "energy": 0.05, "technology": 0.05,
                          "luxury": 0.05, "food": 0.05},
        founded_range=(2044, 2049), credit_ratings=("BBB", "BBB+"), loyalty_bias=6,
        description=(
            "Die {name} wurde {year} von {founder} im Aurelis-System gegründet, um Siedlungen schneller zu bauen, "
            "als die KI-Planer sie entwerfen konnten. Aus Regolith, Silikaten und Glaskeramik sintert das "
            "Unternehmen Bausteine, Kuppelsegmente und komplette Habitatmodule. Jeder Bauboom im inneren Ring füllt "
            "die Auftragsbücher – jede ausbleibende Verbundstahl-Lieferung legt die Baustellen still."
        ),
        fleet=("Grundstein", "Richtfest", "Mörtelmond", "Kuppelbauer", "Lotwaage", "Ziegelwind", "Bauhütte"),
    ),
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
            "{name} was founded in {year} by {founder}, who anchored the first automated helium-3 scoops in the "
            "upper atmosphere of the gas giant Pellora. Today the company refines deuterium, helium-3 and fusion "
            "fuel pellets for reactors across the inner ring. Its fuel keeps stations warm and freighters moving – "
            "and every storm on Pellora is felt in the price of a canister on Sol."
        ),
        fleet=("Ember Run", "Plume Diver", "Steady Burn", "Deep Scoop", "Pilot Flame", "Torus Dream"),
    ),
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
            "Die {name} wurde {year} von {founder} gegründet, nachdem eine verspätete Medikamentenlieferung eine "
            "ganze Station wochenlang in Quarantäne gehalten hatte. Der kleine Kurierdienst kauft eilige, wertvolle "
            "Fracht – Ersatzteile, Medizin, Elektronik – und fliegt sie mit schnellen Leichtfrachtern zwischen Sol "
            "und dem inneren Ring aus. Kometenpost weiß, wer wann was bestellt, und ihre Pilotinnen und Piloten "
            "reden gern."
        ),
        fleet=("Eilfeder", "Postillion", "Sternschnuppe", "Laufbursche", "Blitzbrief"),
    ),
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
            "automated freighters never get bored – but their crews do. From a small fabrication works in Aurelis "
            "the company builds immersion pods and entertainment electronics and imports little comforts like "
            "coffee and spirits for crews in Sol and the Middle Belt. Small, loud and well liked on every docking "
            "ring."
        ),
        fleet=("Matinee", "Encore", "Velvet Rope", "Bright Marquee", "Popcorn Comet"),
    ),
    # ----- Erweiterung Team B: Grenzraum, Expansion und Kolonisierung -----
    CompanyProfile(
        key="pionierwerk", name="Pionierwerk Kolonialausrüstung AG", slug="pionierwerk-kolonialausruestung",
        language="de_DE", size_class="large", specialization="colony_outfitting",
        network_role="colonization_backbone", sku_prefix="PKB", home_system="isolde",
        territory={"isolde": 3.0, "serravel": 2.0, "myrrhen": 1.5, "vaskar": 1.0},
        required_stations=(("industrial", "isolde"), ("trade_hub", "isolde"),
                           ("industrial", "myrrhen"), ("agricultural", "serravel")),
        station_type_weights={"industrial": 3.0, "agricultural": 2.0, "trade_hub": 1.5, "research": 1.0,
                              "mining": 1.0},
        category_weights={"industrial_goods": 0.36, "food": 0.14, "technology": 0.12, "raw_materials": 0.12,
                          "luxury": 0.10, "energy": 0.08, "medical": 0.08},
        founded_range=(2035, 2039), credit_ratings=("A-", "A"), loyalty_bias=4,
        description=(
            "Die {name} wurde {year} von {founder} gegründet, um die Habitatmonde des Isolde-Systems bewohnbar zu "
            "machen. KI-gesteuerte Werke fertigen dort Lebenserhaltung, Atmosphärenwandler, Bauteile und "
            "Terraforming-Kulturen aus Recyclingmetall und Mondregolith, eigene Gartenringe versorgen die "
            "Bautrupps. Heute rüstet der Konzern jede neue Kolonie vom ersten Schweißpunkt bis zur ersten Ernte "
            "aus – und hält die alten Pachtansprüche anderer Konzerne auf Isolde für Makulatur."
        ),
        fleet=("Grundstein", "Richtfest", "Wegbereiter", "Fundament", "Kuppelbau", "Spatenstich", "Lotlinie",
               "Bauhütte", "Hebebaum", "Werkbank", "Schlussstein", "Firstwind"),
    ),
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
            "{name} was founded in {year} by {founder} to escort the first AI-piloted ore convoys through the "
            "Brennus belt. Today its bastions in Kharon and Brennus guard the frontier corridors, and its "
            "quartermasters supply garrisons, mining crews and settlers with fuel, sensors, field medicine and "
            "spare parts. Ravenmoor sells safety by the light-hour – and whatever its patrols seize from smugglers "
            "has a way of reappearing on the free market."
        ),
        fleet=("Iron Vigil", "Long Watch", "Steady Hand", "Night Warden", "Rearguard", "Flint Shield",
               "Lantern Bearer", "Hold Fast", "Grey Sentry", "Far Escort", "Last Line", "Quiet Guardian"),
    ),
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
            "Stickstoffeis auf den Vaskar-Monden und im Myrrhen-System und verarbeitet Helium-3 und Deuterium zu "
            "Treibstoff. Ohne Raureif gibt es in den neuen Kolonien weder Atemluft noch Wasser noch Brennstoff – "
            "entsprechend selbstbewusst verhandelt die Geschäftsführung."
        ),
        fleet=("Eisblume", "Frostfeder", "Kältebrücke", "Gasriese", "Polarnacht", "Reifglanz", "Schneegans"),
    ),
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
            "expansion. From its institute on Serravel it sells star charts, sensor arrays and prospecting drones, "
            "and it hauls the first samples – rare earths, quantum quartz, gemstones – back from worlds nobody has "
            "named yet. Outmark's data decides where the next colony is built, which makes its analysts popular, "
            "well paid and occasionally indiscreet."
        ),
        fleet=("Far Sounding", "Plumb Line", "Bearing Zero", "Parallax", "Long Baseline", "Blank Map"),
    ),
    CompanyProfile(
        key="morgengrund", name="Siedlergenossenschaft Morgengrund eG", slug="morgengrund-siedler",
        language="de_DE", size_class="small", specialization="settler_cooperative",
        network_role="colony_provisioner", sku_prefix="SGM", home_system="isolde",
        territory={"isolde": 3.0, "serravel": 1.5, "vaskar": 1.0},
        required_stations=(("agricultural", "isolde"), ("trade_hub", "isolde")),
        station_type_weights={"agricultural": 3.0, "trade_hub": 1.5},
        category_weights={"food": 0.55, "luxury": 0.15, "raw_materials": 0.10, "industrial_goods": 0.10,
                          "medical": 0.10},
        founded_range=(2053, 2057), credit_ratings=("B+", "BB-"), loyalty_bias=12,
        description=(
            "Die {name} wurde {year} von {founder} und einer Handvoll Siedlerfamilien auf einem Habitatmond im "
            "Isolde-System gegründet. Die Genossenschaft betreibt Gewächskuppeln, eine Saatgutbank und einen "
            "kleinen Markt, auf dem Kolonisten Lebensmittel, Werkzeug und Selbstgebranntes tauschen. Jedes Mitglied "
            "hat eine Stimme, jeder Händler einen Platz am Tisch – solange er fair bezahlt."
        ),
        fleet=("Hoffnung", "Feldmaus", "Gemeinsinn", "Erntedank", "Taubenschlag"),
    ),
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
            "{name} was founded in {year} by {founder}, who decided that the wrecks of Nyx were worth more melted "
            "down than stripped in the dark. The licensed recycler runs a smelter in the middle of the lawless "
            "graveyard, pays its protection money on time and turns derelict hulls into certified metals, "
            "refurbished components and salvaged electronics. The smugglers call it a traitor to the trade; the "
            "colonies call it their cheapest supplier."
        ),
        fleet=("Patchwork", "Mended Wing", "Scrap Sparrow", "Hand-Me-Down", "Make Do"),
    ),
)
# Bestandsfirmen: erzeugen ihre Daten mit dem gemeinsamen Zufallsstrom (Bestandsschutz)
LEGACY_COMPANY_KEYS: frozenset[str] = frozenset(
    {"feldspat", "driftwood", "lichtacker", "corvane", "eisenkrone", "helix"})

# Gerichtete Vereinbarungen (Verkäufer -> Käufer). Unvollständiges Netz mit Helix als Hub.
PARTNERSHIP_BLUEPRINT: tuple[tuple[str, str, str], ...] = (
    ("eisenkrone", "helix", "supply_agreement"),
    ("helix", "eisenkrone", "strategic_alliance"),
    ("helix", "lichtacker", "distribution_agreement"),
    ("lichtacker", "helix", "supply_agreement"),
    ("corvane", "helix", "licensing"),
    ("feldspat", "helix", "consignment"),
    ("driftwood", "helix", "consignment"),
    ("feldspat", "eisenkrone", "supply_agreement"),
    ("eisenkrone", "feldspat", "supply_agreement"),
    ("eisenkrone", "lichtacker", "supply_agreement"),
    ("corvane", "eisenkrone", "supply_agreement"),
    ("eisenkrone", "corvane", "joint_venture"),
    ("lichtacker", "corvane", "supply_agreement"),
    # Erweiterung: neue Firma -> Bestandsfirma (nie umgekehrt, Bestandsschutz)
    ("graufalk", "helix", "supply_agreement"),
    ("cindervale", "eisenkrone", "supply_agreement"),
    ("kuppelwerk", "lichtacker", "supply_agreement"),
    ("emberline", "corvane", "supply_agreement"),
    ("emberline", "lichtacker", "supply_agreement"),
    ("raureif", "eisenkrone", "supply_agreement"),
    ("ravenmoor", "helix", "logistics_partnership"),
    # Erweiterung: innerhalb Team A
    ("cindervale", "graufalk", "supply_agreement"),
    ("graufalk", "cindervale", "strategic_alliance"),
    ("emberline", "graufalk", "supply_agreement"),
    ("graufalk", "emberline", "supply_agreement"),
    ("kuppelwerk", "graufalk", "supply_agreement"),
    ("emberline", "kuppelwerk", "supply_agreement"),
    ("emberline", "cindervale", "supply_agreement"),
    ("cindervale", "kometenpost", "consignment"),
    ("kometenpost", "cindervale", "logistics_partnership"),
    ("cindervale", "lanternfish", "supply_agreement"),
    ("lanternfish", "graufalk", "supply_agreement"),
    ("lanternfish", "kometenpost", "consignment"),
    # Erweiterung: innerhalb Team B
    ("raureif", "pionierwerk", "supply_agreement"),
    ("pionierwerk", "morgengrund", "supply_agreement"),
    ("morgengrund", "pionierwerk", "supply_agreement"),
    ("ravenmoor", "pionierwerk", "logistics_partnership"),
    ("pionierwerk", "ravenmoor", "supply_agreement"),
    ("outmark", "pionierwerk", "licensing"),
    ("second_hull", "pionierwerk", "supply_agreement"),
    ("second_hull", "ravenmoor", "consignment"),
    ("raureif", "ravenmoor", "supply_agreement"),
    ("ravenmoor", "outmark", "logistics_partnership"),
    ("morgengrund", "ravenmoor", "supply_agreement"),
    ("outmark", "raureif", "supply_agreement"),
    # Erweiterung: teamübergreifend
    ("kuppelwerk", "pionierwerk", "supply_agreement"),
    ("second_hull", "graufalk", "supply_agreement"),
    ("graufalk", "ravenmoor", "supply_agreement"),
)
OPTIONAL_PARTNERSHIPS: tuple[tuple[str, str, str, float], ...] = (
    ("helix", "corvane", "logistics_partnership", 0.6),
)
# Beendete Beziehungen (vor dem Datenzeitraum) – Grundlage für Rivalität und Spionage
HISTORIC_PARTNERSHIPS: tuple[tuple[str, str, str], ...] = (
    ("corvane", "driftwood", "supply_agreement"),
    ("eisenkrone", "graufalk", "supply_agreement"),
    ("cindervale", "helix", "licensing"),
    ("lichtacker", "pionierwerk", "supply_agreement"),
    ("emberline", "eisenkrone", "supply_agreement"),
    ("outmark", "feldspat", "licensing"),
    ("driftwood", "second_hull", "consignment"),
)
# Feste Laufzeiten der historischen Erweiterungs-Partnerschaften (Bestand: zufällig wie bisher)
HISTORIC_PARTNERSHIP_DATES: dict[tuple[str, str], tuple[str, str]] = {
    ("eisenkrone", "graufalk"): ("2039-01-01", "2049-06-30"),  # Ausgliederung der Werftsparte Orrin
    ("cindervale", "helix"): ("2041-04-01", "2054-03-31"),  # Lizenzverlust, Technik seither über Kharon
    ("lichtacker", "pionierwerk"): ("2045-03-01", "2053-06-30"),  # Versorgung Isolde bis zum Pachtstreit
    ("emberline", "eisenkrone"): ("2047-02-01", "2056-06-30"),  # Helium-3 für Hande bis zur Eigenförderung
    ("outmark", "feldspat"): ("2055-02-01", "2058-06-30"),  # Vermessungsdaten Brennus, später Fund 52
    ("driftwood", "second_hull"): ("2057-05-01", "2058-07-01"),  # Bergegut Nyx, Bruch nach Razzia 26
}

TRUST_RANGES: dict[str, tuple[int, int]] = {
    "strategic_alliance": (70, 92), "joint_venture": (65, 90), "supply_agreement": (50, 85),
    "distribution_agreement": (55, 82), "consignment": (35, 65), "licensing": (45, 75),
    "logistics_partnership": (50, 78),
}

RIVALRY_BLUEPRINT: tuple[tuple[str, str, str, str], ...] = (
    ("eisenkrone", "helix", "market_dominance", "sol"),
    ("driftwood", "corvane", "industrial_espionage", "halcyon"),
    ("feldspat", "driftwood", "territorial_claims", "kharon"),
    ("lichtacker", "eisenkrone", "resource_competition", "myrrhen"),
    # Erweiterung (an Ereignissen und Verträgen des Bestands festgemacht)
    ("graufalk", "eisenkrone", "market_dominance", "halcyon"),  # KI-Ausfälle Förster (19/36/70)
    ("cindervale", "helix", "market_dominance", "sol"),  # Nachfrageschübe Sol Exchange II (3/24)
    ("emberline", "eisenkrone", "resource_competition", "myrrhen"),  # Energiebrüche Agrarstation Seip
    ("lichtacker", "pionierwerk", "territorial_claims", "isolde"),  # Pachtstreit Isolde
    ("ravenmoor", "driftwood", "armed_conflict", "nyx"),  # Söldner-Razzien 26/58
    ("outmark", "feldspat", "territorial_claims", "brennus"),  # Rohstofffund 52 bei Becker
    ("ravenmoor", "helix", "market_dominance", "kharon"),  # Kharon-Korridor (16/26)
    ("second_hull", "driftwood", "territorial_claims", "nyx"),  # Wracks von Nyx (54)
)
# Feste Kennzahlen der Erweiterungs-Rivalitäten: (since_date, intensity, espionage_risk)
RIVALRY_DETAILS: dict[tuple[str, str], tuple[str, int, int]] = {
    ("graufalk", "eisenkrone"): ("2049-07-01", 70, 55),
    ("cindervale", "helix"): ("2054-04-01", 65, 50),
    ("emberline", "eisenkrone"): ("2058-08-15", 55, 40),
    ("lichtacker", "pionierwerk"): ("2053-07-01", 60, 55),
    ("ravenmoor", "driftwood"): ("2058-06-30", 85, 70),
    ("outmark", "feldspat"): ("2059-07-14", 65, 80),
    ("ravenmoor", "helix"): ("2057-11-17", 55, 45),
    ("second_hull", "driftwood"): ("2058-07-01", 50, 40),
}
RIVALRY_TEXT_OVERRIDES: dict[tuple[str, str], dict[str, str]] = {
    ("emberline", "eisenkrone"): {
        "de_DE": "{company} und {rival} liefern beide Energie ins {system}-System und unterbieten sich bei jedem "
                 "Liefervertrag.",
        "en_US": "{company} and {rival} both supply energy to the {system} system and undercut each other on every "
                 "supply contract.",
    },
    ("lichtacker", "pionierwerk"): {
        "de_DE": "Streit um Pachtrechte im {system}-System: {company} hält {rival} vor, alte Pachtverträge für "
                 "Makulatur erklärt zu haben.",
        "en_US": "A dispute over lease rights in the {system} system: {company} accuses {rival} of tearing up old "
                 "lease contracts.",
    },
}
RIVALRY_TEXTS: dict[str, dict[str, str]] = {
    "market_dominance": {
        "de_DE": "Kampf um die Vorherrschaft im {system}-System: {company} und {rival} sind aufeinander "
                 "angewiesen, unterbieten sich aber bei jeder Ausschreibung.",
        "en_US": "A struggle for dominance in the {system} system: {company} and {rival} depend on each "
                 "other, yet undercut each other in every tender.",
    },
    "industrial_espionage": {
        "de_DE": "{company} wird verdächtigt, Rezepturen von {rival} auf dem Schwarzmarkt zu verkaufen.",
        "en_US": "{company} is suspected of selling {rival}'s formulas on the black market; both sides "
                 "keep informants inside the other's staff.",
    },
    "territorial_claims": {
        "de_DE": "Streit um Schürfrechte im {system}-System – {company} wirft {rival} Claim-Diebstahl vor.",
        "en_US": "A dispute over mining claims in the {system} system – {company} accuses {rival} of "
                 "claim jumping.",
    },
    "resource_competition": {
        "de_DE": "{company} und {rival} konkurrieren um die Wassereis-Vorkommen im {system}-System.",
        "en_US": "{company} and {rival} compete for the water-ice deposits in the {system} system.",
    },
    "armed_conflict": {
        "de_DE": "Söldner von {company} jagen Schmuggler im {system}-System; {rival} macht sie für die Razzien auf "
                 "seine Häfen verantwortlich.",
        "en_US": "{company}'s mercenaries hunt smugglers in the {system} system; {rival} blames them for the raids "
                 "on its havens.",
    },
}
RIVALRY_INTENSITY_RANGES: dict[str, tuple[int, int]] = {
    "market_dominance": (55, 80), "industrial_espionage": (70, 95), "territorial_claims": (40, 75),
    "resource_competition": (35, 65), "armed_conflict": (60, 90),
}

CATEGORY_LABELS: dict[str, tuple[str, str]] = {
    "raw_materials": ("Rohstoffe", "Raw Materials"),
    "energy": ("Energieträger", "Energy Carriers"),
    "industrial_goods": ("Industriegüter", "Industrial Goods"),
    "technology": ("Hochtechnologie", "High Technology"),
    "food": ("Lebensmittel", "Food"),
    "medical": ("Medizin", "Medical Supplies"),
    "luxury": ("Luxusgüter", "Luxury Goods"),
    "contraband": ("Schwarzmarktware", "Contraband"),
}

CATEGORY_FLAVOR: dict[str, tuple[str, str]] = {
    "raw_materials": ("Unverarbeiteter Rohstoff für Hütten und Fabrikationsringe.",
                      "Unprocessed raw material for smelters and fabrication rings."),
    "energy": ("Energieträger für Reaktoren, Antriebe und Stationsnetze.",
               "Energy carrier for reactors, drives and station grids."),
    "industrial_goods": ("Zwischen- oder Fertigprodukt aus KI-gesteuerter Fertigung.",
                         "Intermediate or finished product from AI-run manufacturing."),
    "technology": ("Hochtechnologie mit hohem Wert pro Kubikmeter.",
                   "High technology with a high value per cubic metre."),
    "food": ("Lebensmittel zur Versorgung von Stationsbesatzungen und Kolonien.",
             "Food for station crews and colonies."),
    "medical": ("Medizinisches Gut, gekühlt und unter Sterilauflagen transportiert.",
                "Medical goods, shipped refrigerated under sterile protocols."),
    "luxury": ("Luxusware mit stark schwankender Nachfrage.", "Luxury goods with highly volatile demand."),
    "contraband": ("Schwarzmarktware – hohe Margen, hohes Risiko.", "Black-market goods – high margins, high risk."),
}

LEGAL_NOTES: dict[str, tuple[str, str]] = {
    "legal": ("", ""),
    "restricted": (" Handel nur mit Genehmigung der Raumfahrtbehörde.", " Trade requires a space authority permit."),
    "illegal": (" Im gesamten Kernraum verboten – Handel nur über Schattenhäfen.",
                " Banned throughout core space – traded only through shadow ports."),
}

CATEGORY_MARGIN: dict[str, tuple[float, float]] = {
    "raw_materials": (1.10, 1.25), "energy": (1.12, 1.30), "industrial_goods": (1.15, 1.38),
    "technology": (1.18, 1.45), "food": (1.08, 1.25), "medical": (1.20, 1.50), "luxury": (1.30, 1.90),
    "contraband": (1.60, 2.50),
}
CATEGORY_DISTANCE_PREMIUM: dict[str, float] = {
    "raw_materials": 0.25, "energy": 0.18, "industrial_goods": 0.15, "technology": 0.10, "food": 0.20,
    "medical": 0.12, "luxury": 0.08, "contraband": 0.10,
}
# (Amplitude Angebot, Amplitude Nachfrage, Phase in Tagen)
CATEGORY_SEASONALITY: dict[str, tuple[float, float, int]] = {
    "raw_materials": (0.04, 0.05, 30), "energy": (0.05, 0.10, 0), "industrial_goods": (0.04, 0.06, 90),
    "technology": (0.03, 0.08, 300), "food": (0.14, 0.06, 200), "medical": (0.03, 0.07, 20),
    "luxury": (0.04, 0.16, 330), "contraband": (0.06, 0.08, 150),
}

UNIT_LABELS: dict[str, tuple[str, str]] = {
    "t": ("t", "t"), "crate": ("Kiste", "crate"), "unit": ("Stück", "unit"), "barrel": ("Fass", "barrel"),
    "canister": ("Kanister", "canister"), "pallet": ("Palette", "pallet"),
}

CATEGORY_PRODUCERS: dict[str, frozenset[str]] = {
    "raw_materials": frozenset({"mining"}),
    "energy": frozenset({"mining", "industrial"}),
    "industrial_goods": frozenset({"industrial"}),
    "technology": frozenset({"industrial", "research"}),
    "food": frozenset({"agricultural"}),
    "medical": frozenset({"research"}),
    "luxury": frozenset({"trade_hub", "agricultural", "industrial"}),
    "contraband": frozenset({"smuggler_haven", "free_port"}),
}
CATEGORY_CONSUMERS: dict[str, frozenset[str]] = {
    "raw_materials": frozenset({"industrial", "trade_hub", "free_port"}),
    "energy": frozenset({"industrial", "military", "trade_hub", "free_port", "research", "agricultural", "mining"}),
    "industrial_goods": frozenset({"mining", "agricultural", "military", "trade_hub", "free_port", "research",
                                   "smuggler_haven"}),
    "technology": frozenset({"trade_hub", "military", "research", "mining", "free_port", "smuggler_haven"}),
    "food": frozenset({"mining", "industrial", "military", "trade_hub", "free_port", "research", "smuggler_haven"}),
    "medical": frozenset({"mining", "industrial", "military", "trade_hub", "free_port", "agricultural",
                          "smuggler_haven"}),
    "luxury": frozenset({"trade_hub", "free_port", "research", "military", "smuggler_haven"}),
    "contraband": frozenset({"smuggler_haven", "free_port"}),
}

CATEGORY_VARIANTS: dict[str, tuple[tuple[str, str, float], ...]] = {
    "raw_materials": (("Rohförderung", "Raw Haul", 0.85), ("Güteklasse B", "Grade B", 1.0),
                      ("Güteklasse A", "Grade A", 1.22), ("Hochrein", "High Purity", 1.6),
                      ("Raffiniert", "Refined", 1.9)),
    "energy": (("Standard", "Standard", 1.0), ("Hochdicht", "High Density", 1.35),
               ("Industriecharge", "Industrial Batch", 0.9), ("Raumfahrtnorm", "Flight Grade", 1.5)),
    "industrial_goods": (("Standard", "Standard", 1.0), ("Verstärkt", "Reinforced", 1.3),
                         ("Serie K", "K-Series", 1.15), ("Militärnorm", "Mil-Spec", 1.7),
                         ("Leichtbau", "Lightweight", 1.25)),
    "technology": (("Mk I", "Mk I", 0.85), ("Standard", "Standard", 1.0), ("Mk III", "Mk III", 1.3),
                   ("Pro", "Pro", 1.6), ("Feldversion", "Field Edition", 1.1)),
    "food": (("Standard", "Standard", 1.0), ("Premium", "Premium", 1.4), ("Notration", "Emergency Ration", 0.85),
             ("Bio", "Organic", 1.3), ("Großgebinde", "Bulk Pack", 0.9)),
    "medical": (("Standard", "Standard", 1.0), ("Klinikqualität", "Clinical Grade", 1.4),
                ("Feldausführung", "Field Kit", 1.15), ("Generikum", "Generic", 0.75)),
    "luxury": (("Klassisch", "Classic", 1.0), ("Limitierte Edition", "Limited Edition", 1.5),
               ("Sammlerstück", "Collector's Item", 2.2), ("Reiseformat", "Travel Size", 0.7)),
    "contraband": (("Standard", "Standard", 1.0), ("Sonderposten", "Special Batch", 1.35),
                   ("Restposten", "Leftover Stock", 0.8)),
}


@dataclass(frozen=True)
class ProductArchetype:
    """Grundware des Warenkatalogs, aus der firmenspezifische Produkte abgeleitet werden."""

    code: str
    category: str
    name_de: str
    name_en: str
    unit: str
    base_price: float
    volume_m3: float
    mass_kg: float
    legal_status: str
    producers: frozenset[str]
    consumers: frozenset[str]
    extension: bool = False  # True: nur im Produkt-Pool der Erweiterungsfirmen (Bestandsschutz)


def _archetype(code: str, category: str, name_de: str, name_en: str, unit: str, base_price: float,
               volume_m3: float, mass_kg: float, legal_status: str = "legal",
               producers: Iterable[str] | None = None,
               extra_consumers: Iterable[str] = (), extension: bool = False) -> ProductArchetype:
    """Erzeugt einen Waren-Archetyp mit kategorieabhängigen Erzeuger- und Verbraucherstationen."""
    return ProductArchetype(
        code=code, category=category, name_de=name_de, name_en=name_en, unit=unit, base_price=base_price,
        volume_m3=volume_m3, mass_kg=mass_kg, legal_status=legal_status,
        producers=frozenset(producers) if producers else CATEGORY_PRODUCERS[category],
        consumers=CATEGORY_CONSUMERS[category] | frozenset(extra_consumers), extension=extension,
    )


PRODUCT_ARCHETYPES: tuple[ProductArchetype, ...] = (
    # Rohstoffe
    _archetype("iron_ore", "raw_materials", "Eisenerz", "Iron Ore", "t", 85, 0.35, 1000),
    _archetype("titanium_ore", "raw_materials", "Titanerz", "Titanium Ore", "t", 420, 0.30, 1000),
    _archetype("silicon", "raw_materials", "Silizium", "Silicon", "t", 260, 0.43, 1000),
    _archetype("water_ice", "raw_materials", "Wassereis", "Water Ice", "t", 60, 1.09, 1000,
               extra_consumers=("agricultural", "military", "research")),
    _archetype("rare_earths", "raw_materials", "Seltene Erden", "Rare Earth Elements", "t", 2400, 0.2, 1000,
               extra_consumers=("research",)),
    _archetype("nickel_iron", "raw_materials", "Nickel-Eisen", "Nickel-Iron", "t", 140, 0.13, 1000),
    _archetype("cobalt", "raw_materials", "Kobalt", "Cobalt", "t", 1100, 0.12, 1000),
    _archetype("regolith", "raw_materials", "Regolith-Granulat", "Regolith Aggregate", "t", 30, 0.6, 1000,
               extra_consumers=("agricultural",)),
    _archetype("carbon", "raw_materials", "Kohlenstoffkonzentrat", "Carbon Concentrate", "t", 180, 0.5, 1000),
    _archetype("ammonia_ice", "raw_materials", "Ammoniak-Eis", "Ammonia Ice", "t", 95, 1.2, 1000,
               extra_consumers=("agricultural",)),
    _archetype("quantum_quartz", "raw_materials", "Quantenquarz", "Quantum Quartz", "crate", 9200, 0.05, 40,
               extra_consumers=("research",)),
    _archetype("platinum", "raw_materials", "Platinmetalle", "Platinum Group Metals", "crate", 15500, 0.01, 50,
               extra_consumers=("research",)),
    # Energieträger
    _archetype("helium3", "energy", "Helium-3", "Helium-3", "canister", 6500, 0.08, 6, "restricted",
               producers=("mining",)),
    _archetype("deuterium", "energy", "Deuterium", "Deuterium", "canister", 1800, 0.08, 12, producers=("mining",)),
    _archetype("fuel_cells", "energy", "Brennstoffzellen", "Fuel Cells", "crate", 950, 0.25, 40,
               producers=("industrial",)),
    _archetype("plasma_gas", "energy", "Plasmagas", "Plasma Gas", "canister", 2100, 0.1, 8, producers=("mining",)),
    _archetype("antimatter", "energy", "Antimaterie-Kapseln", "Antimatter Capsules", "unit", 48000, 0.02, 15,
               "restricted", producers=("research",)),
    # Industriegüter
    _archetype("composite_steel", "industrial_goods", "Verbundstahl", "Composite Steel", "t", 1300, 0.14, 1000),
    _archetype("structural_parts", "industrial_goods", "Bauteile", "Structural Components", "crate", 650, 0.6, 180),
    _archetype("reactor_components", "industrial_goods", "Reaktorkomponenten", "Reactor Components", "unit",
               28000, 1.2, 900, "restricted"),
    _archetype("machine_tools", "industrial_goods", "Werkzeugmaschinen", "Machine Tools", "unit", 15000, 3.5, 2200),
    _archetype("hull_plating", "industrial_goods", "Rumpfplatten", "Hull Plating", "pallet", 3800, 1.8, 1400),
    _archetype("drive_parts", "industrial_goods", "Triebwerksteile", "Drive Components", "crate", 7200, 0.7, 320),
    _archetype("life_support", "industrial_goods", "Lebenserhaltungsmodule", "Life Support Modules", "unit",
               22000, 4.0, 1600),
    _archetype("mining_drones", "industrial_goods", "Bergbaudrohnen", "Mining Drones", "unit", 18000, 2.2, 700),
    _archetype("polymers", "industrial_goods", "Polymere", "Polymers", "t", 900, 1.0, 1000),
    _archetype("glass_ceramics", "industrial_goods", "Glaskeramik", "Glass Ceramics", "pallet", 1600, 1.0, 800),
    # Hochtechnologie
    _archetype("electronics", "technology", "Elektronik", "Electronics", "crate", 2400, 0.5, 60),
    _archetype("ai_cores", "technology", "KI-Kerne", "AI Cores", "unit", 36000, 0.1, 18, "restricted"),
    _archetype("sensor_arrays", "technology", "Sensorarrays", "Sensor Arrays", "crate", 8500, 0.4, 55),
    _archetype("nav_computers", "technology", "Navigationscomputer", "Navigation Computers", "unit", 14000, 0.15, 22),
    _archetype("robotics", "technology", "Robotikeinheiten", "Robotics Units", "unit", 26000, 1.6, 450),
    _archetype("superconductors", "technology", "Supraleiter", "Superconductors", "crate", 11000, 0.2, 90),
    # Lebensmittel
    _archetype("protein_paste", "food", "Proteinpaste", "Protein Paste", "crate", 140, 0.3, 120),
    _archetype("hydroponic_produce", "food", "Hydrokulturgemüse", "Hydroponic Produce", "crate", 210, 0.5, 60),
    _archetype("freeze_dried", "food", "Gefriergetrocknete Rationen", "Freeze-Dried Rations", "crate", 180, 0.3, 25),
    _archetype("algae_concentrate", "food", "Algenkonzentrat", "Algae Concentrate", "barrel", 120, 0.2, 200),
    _archetype("cultured_meat", "food", "Kulturfleisch", "Cultured Meat", "crate", 420, 0.25, 40),
    _archetype("orbital_grain", "food", "Orbitalgetreide", "Orbital Grain", "t", 520, 1.4, 1000),
    _archetype("fresh_fruit", "food", "Frischobst", "Fresh Fruit", "crate", 380, 0.4, 35),
    # Medizin
    _archetype("pharmaceuticals", "medical", "Medikamente", "Pharmaceuticals", "crate", 1800, 0.2, 25),
    _archetype("medical_equipment", "medical", "Medizinische Ausrüstung", "Medical Equipment", "unit",
               9500, 0.8, 120),
    _archetype("bio_samples", "medical", "Bioproben", "Bio Samples", "canister", 4200, 0.05, 8, "restricted",
               producers=("research", "agricultural")),
    _archetype("vaccines", "medical", "Impfstoffe", "Vaccines", "crate", 3100, 0.15, 18),
    _archetype("nanomedicine", "medical", "Nanomedizin", "Nanomedicine", "crate", 12500, 0.05, 6),
    _archetype("radiation_meds", "medical", "Strahlenschutzpräparate", "Radiation Countermeasures", "crate",
               1400, 0.15, 20),
    # Luxusgüter
    _archetype("art_objects", "luxury", "Kunstobjekte", "Art Objects", "unit", 45000, 1.5, 120,
               producers=("trade_hub",)),
    _archetype("gemstones", "luxury", "Edelsteine", "Gemstones", "unit", 12000, 0.002, 0.5, producers=("mining",)),
    _archetype("spirits", "luxury", "Spirituosen", "Spirits", "crate", 1600, 0.06, 18, producers=("agricultural",)),
    _archetype("entertainment_electronics", "luxury", "Unterhaltungselektronik", "Entertainment Electronics",
               "crate", 3200, 0.4, 35, producers=("industrial",)),
    _archetype("earth_wine", "luxury", "Erd-Wein", "Earth Wine", "crate", 2600, 0.05, 16,
               producers=("agricultural", "trade_hub")),
    _archetype("designer_textiles", "luxury", "Designertextilien", "Designer Textiles", "crate", 2200, 0.3, 20,
               producers=("industrial", "trade_hub")),
    _archetype("real_wood_furniture", "luxury", "Echtholzmöbel", "Real-Wood Furniture", "unit", 8800, 1.8, 90,
               producers=("agricultural", "trade_hub")),
    _archetype("orbital_coffee", "luxury", "Orbitalkaffee", "Orbital Coffee", "crate", 950, 0.08, 30,
               producers=("agricultural",)),
    # Schwarzmarktware
    _archetype("stolen_tech", "contraband", "Gestohlene Technologie", "Stolen Technology", "crate", 24000,
               0.3, 40, "illegal"),
    _archetype("unregistered_weapons", "contraband", "Unregistrierte Waffen", "Unregistered Weapons", "crate",
               16000, 0.4, 80, "illegal"),
    _archetype("banned_biotech", "contraband", "Verbotene Biotech-Waren", "Banned Biotech Goods", "canister",
               21000, 0.05, 6, "illegal"),
    _archetype("combat_stims", "contraband", "Kampfstimulanzien", "Combat Stims", "crate", 6800, 0.05, 10, "illegal"),
    _archetype("forged_permits", "contraband", "Gefälschte Transitlizenzen", "Forged Transit Permits", "unit",
               9000, 0.001, 0.1, "illegal"),
    _archetype("hacked_ai_cores", "contraband", "Gehackte KI-Kerne", "Hacked AI Cores", "unit", 52000, 0.1, 18,
               "illegal"),
    # Erweiterung (nur in den Pools der neuen Firmen, damit die Bestandskataloge gleich bleiben)
    _archetype("fusion_pellets", "energy", "Fusionspellets", "Fusion Fuel Pellets", "crate", 5200, 0.06, 22,
               producers=("industrial",), extension=True),
    _archetype("habitat_modules", "industrial_goods", "Habitatmodule", "Habitat Modules", "unit", 46000, 14.0, 6200,
               extra_consumers=("industrial",), extension=True),
    _archetype("sinter_blocks", "industrial_goods", "Sinterbausteine", "Sintered Regolith Blocks", "pallet", 380,
               0.9, 1400, extra_consumers=("industrial",), extension=True),
    _archetype("quantum_relays", "technology", "Quantenrelais", "Quantum Comm Relays", "unit", 19500, 0.25, 28,
               "restricted", extension=True),
    _archetype("immersion_pods", "luxury", "Immersionskapseln", "Immersion Pods", "unit", 13500, 2.4, 260,
               producers=("industrial",), extension=True),
    _archetype("escort_drones", "industrial_goods", "Geleitschutzdrohnen", "Escort Drones", "unit", 21000, 2.4, 650,
               "restricted", producers=("industrial", "military"), extension=True),
    _archetype("nitrogen_ice", "raw_materials", "Stickstoffeis", "Nitrogen Ice", "t", 75, 1.2, 1000,
               extra_consumers=("agricultural", "research"), extension=True),
    _archetype("terraforming_cultures", "technology", "Terraforming-Kulturen", "Terraforming Cultures", "canister",
               7800, 0.06, 9, "restricted", producers=("research", "agricultural"),
               extra_consumers=("agricultural",), extension=True),
    _archetype("survey_charts", "technology", "Vermessungsdatenkerne", "Survey Data Cores", "unit", 5400, 0.01, 0.5,
               producers=("research",), extension=True),
)
ARCHETYPES_BY_CODE: dict[str, ProductArchetype] = {a.code: a for a in PRODUCT_ARCHETYPES}

CONTRACT_TYPES: dict[str, dict[str, Any]] = {
    "spot": {"label": ("Einzelliefervertrag", "Spot delivery contract"), "calloffs": (1, 1), "days": (20, 60)},
    "framework": {"label": ("Rahmenvertrag", "Framework agreement"), "calloffs": (2, 5), "days": (90, 300)},
    "recurring_supply": {"label": ("Dauerliefervertrag", "Recurring supply contract"), "calloffs": (2, 5),
                         "days": (60, 240)},
    "exclusive_supply": {"label": ("Exklusivliefervertrag", "Exclusive supply contract"), "calloffs": (2, 4),
                         "days": (120, 360)},
    "consignment": {"label": ("Kommissionsvertrag", "Consignment contract"), "calloffs": (1, 3),
                    "days": (45, 150)},
    "emergency_supply": {"label": ("Notliefervertrag", "Emergency supply contract"), "calloffs": (1, 1),
                         "days": (10, 30)},
}
CONTRACT_TYPE_WEIGHTS_BY_AGREEMENT: dict[str, dict[str, float]] = {
    "consignment": {"consignment": 5, "spot": 3, "emergency_supply": 1},
    "strategic_alliance": {"framework": 4, "exclusive_supply": 2, "recurring_supply": 2, "spot": 2},
    "joint_venture": {"exclusive_supply": 3, "framework": 3, "recurring_supply": 2, "spot": 1},
}
DEFAULT_CONTRACT_TYPE_WEIGHTS: dict[str, float] = {
    "spot": 4, "framework": 3, "recurring_supply": 3, "exclusive_supply": 1, "emergency_supply": 1,
}
CONTRACT_PREFIX = {"de_DE": "VTR", "en_US": "CTR"}
ORDER_PREFIX = {"de_DE": "BST", "en_US": "ORD"}
SHIPMENT_PREFIX = {"de_DE": "LFR", "en_US": "SHP"}

ORDER_NOTES: dict[str, tuple[str, ...]] = {
    "de_DE": ("Lieferung an Frachtdock {dock}.", "Zollpapiere bitte vorab übermitteln.", "Kühlkette einhalten.",
              "Anlieferung nur im Nachtzyklus.", "Teillieferung nicht zulässig.", "Ware vor Annahme scannen."),
    "en_US": ("Deliver to cargo dock {dock}.", "Please transmit customs papers in advance.",
              "Maintain the cold chain.", "Delivery during night cycle only.", "No partial deliveries.",
              "Scan goods before acceptance."),
}
CALLOFF_NOTE = {"de_DE": "Abruf {index}/{total} aus Vertrag {number}.",
                "en_US": "Call-off {index}/{total} under contract {number}."}

# ---------------------------------------------------------------------------
# Rahmenverträge (Grundlage: planung/verknuepfungen.json, Entscheidung Phase 2)
# ---------------------------------------------------------------------------

# Einzelvertragstypen, die als Abruf unter einem Rahmenvertrag laufen
FRAMEWORK_CALLOFF_TYPES: frozenset[str] = frozenset({"framework", "recurring_supply", "exclusive_supply"})
# Vor Rahmenbeginn (bzw. außerhalb des Rahmens) schließen neue Paare nur diese Vertragstypen
OUTSIDE_FRAMEWORK_CONTRACT_TYPES: frozenset[str] = frozenset({"spot", "emergency_supply", "consignment"})
FRAMEWORK_VOLUME_THRESHOLD = 0.90  # kumulierte Abrufe über 90 % des Rahmenvolumens -> Volumen-Nachtrag
FRAMEWORK_EXTENSION_LEAD_DAYS = 60  # Verlängerung wirksam 60 Tage vor Laufzeitende
FRAMEWORK_SIGNING_LEAD_DAYS = 30  # Unterzeichnung 30 Tage vor Rahmenbeginn
DEFAULT_RENEWAL_MONTHS = 12
DEFAULT_PENALTY_RATE_PCT = 0.6  # Vertragsstrafe in % des Abrufwerts je Verzugstag
DEFAULT_PROPOSAL_DATE_2060 = date(2059, 12, 10)  # Nachträge mit Wirkung 2060 werden im Dezember 2059 angeboten

AMENDMENT_RULES = ("first_contract_of_category", "cumulative_over_90pct", "calloff_after_end")
AMENDMENT_PREFIX = {"de_DE": "N", "en_US": "A"}

PRICE_FORMULA_TEXTS: dict[str, tuple[str, str]] = {
    "fixed": ("Festpreise laut Preisanhang", "fixed prices per price schedule"),
    "index_linked": ("indexierte Preise ({index}), Anpassung höchstens {cap} % je Quartal",
                     "index-linked prices ({index}), adjusted by at most {cap}% per quarter"),
    "cost_plus": ("Herstellkosten zuzüglich {pct} % Aufschlag", "production cost plus a {pct}% mark-up"),
    "market_minus": ("Marktpreis abzüglich {pct} % Rahmenrabatt", "market price less a {pct}% framework discount"),
}
INDEXATION_LABELS: dict[str, tuple[str, str]] = {
    "none": ("ohne Index", "no index"),
    "category_price_index": ("Preisindex {category}", "{category} price index"),
    "fuel_index": ("Treibstoffindex", "fuel index"),
    "risk_index": ("Risikoindex der Korridore", "corridor risk index"),
}
EXCLUSIVITY_LABELS: dict[str, tuple[str, str]] = {
    "none": ("keine Exklusivität", "no exclusivity"),
    "right_of_first_refusal": ("Vorkaufsrecht des Käufers", "buyer's right of first refusal"),
    "buyer_exclusive": ("Käuferexklusivität", "buyer exclusivity"),
    "seller_exclusive": ("Verkäuferexklusivität", "seller exclusivity"),
    "mutual": ("gegenseitige Exklusivität", "mutual exclusivity"),
    "regional_exclusive": ("regionale Exklusivität", "regional exclusivity"),
}
AMENDMENT_TEXTS: dict[str, tuple[str, str]] = {
    "volume_increase": ("Das Rahmenvolumen wird ab {effective} von {before} auf {after} CR erhöht.{trigger}",
                        "The framework volume is raised from {before} to {after} CR as of {effective}.{trigger}"),
    "volume_reduction": ("Das Rahmenvolumen wird ab {effective} von {before} auf {after} CR gesenkt.{trigger}",
                         "The framework volume is reduced from {before} to {after} CR as of {effective}.{trigger}"),
    "product_addition": ("Ab {effective} wird das Sortiment des Rahmens um {items} erweitert.{trigger}",
                         "As of {effective}, the framework scope is extended by {items}.{trigger}"),
    "product_removal": ("Ab {effective} wird das Sortiment des Rahmens um {items} verringert.{trigger}",
                        "As of {effective}, the framework scope no longer includes {items}.{trigger}"),
    "price_adjustment": ("Die Rahmenpreise ändern sich ab {effective} um {pct} %{items_suffix}.{trigger}",
                         "Framework prices change by {pct}% as of {effective}{items_suffix}.{trigger}"),
    "term_extension": ("Die Laufzeit wird bis {end} verlängert (wirksam ab {effective}).{trigger}",
                       "The term is extended until {end} (effective {effective}).{trigger}"),
    "exclusivity_clause": ("Ab {effective} gilt {exclusivity} für {items}{system_suffix}.{trigger}",
                           "As of {effective}, {exclusivity} applies to {items}{system_suffix}.{trigger}"),
    "exclusivity_waiver": ("Ab {effective} entfällt die Exklusivität für {items}.{trigger}",
                           "As of {effective}, exclusivity for {items} is waived.{trigger}"),
    "penalty_clause": ("Ab {effective} gilt eine verschärfte Vertragsstrafenklausel für verspätete Abrufe.{trigger}",
                       "As of {effective}, a stricter penalty clause applies to late call-offs.{trigger}"),
    "service_level_clause": ("Ab {effective} gelten zugesicherte Lieferzeiten und Gewährleistungsfristen.{trigger}",
                             "As of {effective}, guaranteed delivery times and warranty periods apply.{trigger}"),
    "escort_clause": ("Ab {effective} werden Konvois im Korridor durch {escort} begleitet.{trigger}",
                      "As of {effective}, convoys in the corridor are escorted by {escort}.{trigger}"),
    "force_majeure_clause": ("Ab {effective} gilt eine erweiterte Klausel zu höherer Gewalt.{trigger}",
                             "As of {effective}, an extended force majeure clause applies.{trigger}"),
    "competition_clause": ("Ab {effective} gilt ein Wettbewerbsverbot für {items}.{trigger}",
                           "As of {effective}, a non-compete clause covers {items}.{trigger}"),
    "confidentiality_clause": ("Ab {effective} gilt eine verschärfte Vertraulichkeitsklausel.{trigger}",
                               "As of {effective}, a stricter confidentiality clause applies.{trigger}"),
    "scope_extension": ("Ab {effective} erstreckt sich der Rahmen auf {items}{system_suffix}.{trigger}",
                        "As of {effective}, the framework extends to {items}{system_suffix}.{trigger}"),
    "partial_termination": ("Teilkündigung: Ab {effective} umfasst der Rahmen keine {items} mehr.{trigger}",
                            "Partial termination: as of {effective}, the framework no longer covers {items}.{trigger}"),
    "suspension": ("Der Rahmen ruht ab {effective}; neue Abrufe sind ausgesetzt.{trigger}",
                   "The framework is suspended as of {effective}; no new call-offs are accepted.{trigger}"),
}
AMENDMENT_RULE_NOTES: dict[str, tuple[str, str]] = {
    "first_contract_of_category": (" Anlass: erster Abrufvertrag {contract}.",
                                   " Reason: first call-off contract {contract}."),
    "cumulative_over_90pct": (" Anlass: Vertrag {contract} bringt die Abrufe über 90 % des Rahmenvolumens.",
                              " Reason: contract {contract} takes call-offs above 90% of the framework volume."),
    "calloff_after_end": (" Anlass: Abruf {contract} beginnt nach dem bisherigen Laufzeitende.",
                          " Reason: call-off {contract} starts after the previous end of term."),
    "anchor": (" Bezug: {contract}.", " Reference: {contract}."),
}

FRAMEWORK_BLUEPRINT: tuple[dict[str, Any], ...] = (
    {
        "number": "HMX-MSA-2057-01", "seller": "helix", "buyer": "lichtacker",
        "title": "Distribution Framework Agreement Agricultural Rings Tauvel, Aurelis & Myrrhen",
        "start": "2057-01-01", "term_months": 36, "base_volume_mcr": 250, "price_formula": "index_linked",
        "indexation": "category_price_index", "adjustment_cap_pct": 8, "exclusivity": "right_of_first_refusal",
        "exclusive_categories": ("industrial_goods",), "notice_days": 180,
        "scope": ("luxury", "food", "industrial_goods"),
        "amendments": (
            {
                "type": "product_addition", "effective": "2057-04-01", "status": "signed",
                "categories": ("energy", "technology"), "rule": "first_contract_of_category",
            },
            {
                "type": "product_addition", "effective": "2057-09-01", "status": "signed", "categories": ("medical",),
                "rule": "first_contract_of_category",
            },
            {
                "type": "penalty_clause", "effective": "2058-03-14", "status": "signed", "proposed": "2058-02-20",
                "initiated_by": "lichtacker", "contracts": ("HMX-CTR-2057-0043",),
            },
            {
                "type": "volume_increase", "effective": "2058-09-01", "status": "signed", "volume_after_mcr": 400,
                "rule": "cumulative_over_90pct", "contracts": ("HMX-CTR-2058-0161",),
            },
            {
                "type": "exclusivity_waiver", "effective": "2059-03-15", "status": "signed", "proposed": "2059-03-10",
                "initiated_by": "lichtacker", "categories": ("industrial_goods",),
                "contracts": ("HMX-CTR-2057-0043", "HMX-CTR-2058-0139", "HMX-CTR-2058-0159"),
            },
            {
                "type": "volume_increase", "effective": "2059-10-01", "status": "signed", "volume_after_mcr": 550,
                "rule": "cumulative_over_90pct", "contracts": ("HMX-CTR-2059-0259",),
            },
            {
                "type": "term_extension", "effective": "2059-11-01", "status": "signed", "initiated_by": "lichtacker",
                "new_end_date": "2060-12-31", "rule": "calloff_after_end",
            },
        ),
    },
    {
        "number": "HMX-MSA-2057-02", "seller": "helix", "buyer": "corvane",
        "title": "Logistics & Supply Master Agreement Halcyon/Aurelis", "start": "2057-01-01", "term_months": 36,
        "base_volume_mcr": 300, "price_formula": "market_minus", "indexation": "category_price_index",
        "base_discount_pct": 4, "exclusivity": "none", "notice_days": 120, "scope": ("luxury", "raw_materials"),
        "amendments": (
            {
                "type": "product_addition", "effective": "2057-03-01", "status": "signed",
                "categories": ("technology",), "rule": "first_contract_of_category",
            },
            {
                "type": "product_addition", "effective": "2057-05-01", "status": "signed", "categories": ("energy",),
                "rule": "first_contract_of_category",
            },
            {
                "type": "exclusivity_clause", "effective": "2057-05-01", "status": "signed", "initiated_by": "helix",
                "categories": ("energy",), "exclusivity": "buyer_exclusive",
            },
            {
                "type": "product_addition", "effective": "2058-01-01", "status": "signed",
                "categories": ("industrial_goods",), "rule": "first_contract_of_category",
            },
            {
                "type": "volume_increase", "effective": "2058-08-01", "status": "signed", "volume_after_mcr": 450,
                "rule": "cumulative_over_90pct", "contracts": ("HMX-CTR-2058-0152",),
            },
            {
                "type": "product_removal", "effective": "2059-03-15", "status": "signed", "proposed": "2059-03-13",
                "initiated_by": "corvane", "archetypes": ("helium3",),
                "contracts": ("HMX-CTR-2058-0131", "HMX-CTR-2057-0014"), "events": (30,),
            },
            {
                "type": "exclusivity_waiver", "effective": "2059-03-15", "status": "signed", "proposed": "2059-03-13",
                "initiated_by": "corvane", "categories": ("energy",), "contracts": ("HMX-CTR-2058-0131",),
            },
            {
                "type": "volume_increase", "effective": "2059-04-01", "status": "signed", "volume_after_mcr": 600,
                "rule": "cumulative_over_90pct", "contracts": ("HMX-CTR-2059-0213",),
            },
            {
                "type": "term_extension", "effective": "2059-11-01", "status": "signed", "initiated_by": "corvane",
                "new_end_date": "2060-12-31", "rule": "calloff_after_end",
            },
            {
                "type": "volume_increase", "effective": "2060-02-01", "status": "proposed", "proposed": "2059-12-15",
                "volume_after_mcr": 750, "rule": "cumulative_over_90pct", "contracts": ("HMX-CTR-2060-0281",),
            },
        ),
    },
    {
        "number": "HMX-MSA-2057-03", "seller": "helix", "buyer": "eisenkrone",
        "title": "Strategic Supply Framework Sol/Halcyon/Brennus", "start": "2057-01-01", "term_months": 48,
        "base_volume_mcr": 300, "price_formula": "cost_plus", "indexation": "category_price_index",
        "cost_plus_pct": 9, "exclusivity": "none", "notice_days": 360, "scope": ("food", "raw_materials", "energy"),
        "amendments": (
            {
                "type": "product_addition", "effective": "2057-07-01", "status": "signed", "categories": ("medical",),
                "rule": "first_contract_of_category",
            },
            {
                "type": "product_addition", "effective": "2057-09-01", "status": "signed",
                "categories": ("technology",), "rule": "first_contract_of_category",
            },
            {
                "type": "product_addition", "effective": "2057-11-01", "status": "signed",
                "categories": ("industrial_goods",), "rule": "first_contract_of_category",
            },
            {
                "type": "volume_reduction", "effective": "2058-03-01", "status": "signed", "proposed": "2058-02-15",
                "initiated_by": "eisenkrone", "volume_after_mcr": 250, "events": (19,),
            },
            {
                "type": "volume_increase", "effective": "2059-01-01", "status": "signed", "volume_after_mcr": 350,
                "rule": "cumulative_over_90pct", "contracts": ("HMX-CTR-2059-0192",),
            },
            {
                "type": "volume_increase", "effective": "2059-06-01", "status": "signed", "volume_after_mcr": 450,
                "rule": "cumulative_over_90pct", "contracts": ("HMX-CTR-2059-0236",),
            },
            {
                "type": "volume_increase", "effective": "2060-01-01", "status": "proposed", "proposed": "2059-12-10",
                "volume_after_mcr": 550, "rule": "cumulative_over_90pct", "contracts": ("HMX-CTR-2060-0275",),
            },
        ),
    },
    {
        "number": "EKM-RV-2057-01", "seller": "eisenkrone", "buyer": "corvane",
        "title": "Joint-Venture-Liefervertrag Halcyon", "start": "2057-01-01", "term_months": 60,
        "base_volume_mcr": 350, "price_formula": "cost_plus", "indexation": "category_price_index",
        "cost_plus_pct": 12, "exclusivity": "right_of_first_refusal", "exclusive_categories": ("raw_materials",),
        "notice_days": 360, "scope": ("raw_materials", "industrial_goods"),
        "amendments": (
            {
                "type": "product_addition", "effective": "2057-05-01", "status": "signed", "categories": ("luxury",),
                "rule": "first_contract_of_category",
            },
            {
                "type": "product_addition", "effective": "2057-06-01", "status": "signed",
                "categories": ("technology",), "rule": "first_contract_of_category",
            },
            {
                "type": "penalty_clause", "effective": "2058-05-01", "status": "signed", "proposed": "2058-04-28",
                "initiated_by": "corvane", "contracts": ("EKM-VTR-2057-0064",),
            },
            {
                "type": "volume_increase", "effective": "2059-03-01", "status": "signed", "volume_after_mcr": 450,
                "rule": "cumulative_over_90pct", "contracts": ("EKM-VTR-2059-0160",),
            },
            {
                "type": "service_level_clause", "effective": "2060-02-01", "status": "proposed",
                "proposed": "2059-12-23", "initiated_by": "corvane", "contracts": ("EKM-VTR-2059-0160",),
            },
            {
                "type": "volume_increase", "effective": "2060-01-01", "status": "proposed", "proposed": "2059-12-10",
                "volume_after_mcr": 550, "rule": "cumulative_over_90pct", "contracts": ("EKM-VTR-2060-0219",),
            },
        ),
    },
    {
        "number": "EKM-RV-2057-02", "seller": "eisenkrone", "buyer": "helix",
        "title": "Rahmenvertrag Erze und Energie Brennus/Halcyon – Kharon/Sol", "start": "2057-01-01",
        "term_months": 42, "base_volume_mcr": 200, "price_formula": "index_linked",
        "indexation": "category_price_index", "price_index_category": "raw_materials", "adjustment_cap_pct": 10,
        "exclusivity": "none", "notice_days": 180, "scope": ("energy", "raw_materials"),
        "amendments": (
            {
                "type": "product_addition", "effective": "2057-06-01", "status": "signed", "categories": ("food",),
                "rule": "first_contract_of_category",
            },
            {
                "type": "product_addition", "effective": "2057-10-01", "status": "signed",
                "categories": ("technology",), "rule": "first_contract_of_category",
            },
            {
                "type": "product_addition", "effective": "2058-01-01", "status": "signed",
                "categories": ("industrial_goods",), "rule": "first_contract_of_category",
            },
            {
                "type": "penalty_clause", "effective": "2058-01-09", "status": "signed", "proposed": "2057-12-20",
                "initiated_by": "helix", "contracts": ("EKM-VTR-2057-0017",),
            },
            {
                "type": "product_addition", "effective": "2058-08-01", "status": "signed", "categories": ("luxury",),
                "rule": "first_contract_of_category",
            },
            {
                "type": "volume_increase", "effective": "2059-02-01", "status": "signed", "volume_after_mcr": 300,
                "rule": "cumulative_over_90pct", "contracts": ("EKM-VTR-2059-0151",),
            },
            {
                "type": "escort_clause", "effective": "2060-02-01", "status": "proposed", "proposed": "2059-12-22",
                "initiated_by": "helix", "escort": "ravenmoor",
                "contracts": ("EKM-VTR-2057-0043", "EKM-VTR-2058-0107"), "orders": ("EKM-BST-2059-02343",),
                "events": (74,),
            },
            {
                "type": "volume_increase", "effective": "2060-02-01", "status": "proposed", "proposed": "2059-12-22",
                "volume_after_mcr": 400, "rule": "cumulative_over_90pct", "contracts": ("EKM-VTR-2060-0234",),
            },
            {
                "type": "term_extension", "effective": "2060-07-01", "status": "proposed", "proposed": "2059-12-22",
                "initiated_by": "helix", "new_end_date": "2061-06-30",
            },
        ),
    },
    {
        "number": "EKM-RV-2057-03", "seller": "eisenkrone", "buyer": "lichtacker",
        "title": "Liefervertrag Industriegüter und Energie Myrrhen/Tauvel", "start": "2057-01-01", "term_months": 36,
        "base_volume_mcr": 150, "price_formula": "index_linked", "indexation": "category_price_index",
        "price_index_category": "energy", "adjustment_cap_pct": 6, "exclusivity": "none", "notice_days": 90,
        "scope": ("industrial_goods", "luxury", "raw_materials"),
        "amendments": (
            {
                "type": "product_addition", "effective": "2057-08-01", "status": "signed", "categories": ("energy",),
                "rule": "first_contract_of_category",
            },
            {
                "type": "product_addition", "effective": "2058-02-01", "status": "signed",
                "categories": ("technology",), "rule": "first_contract_of_category",
            },
            {
                "type": "penalty_clause", "effective": "2058-09-14", "status": "signed", "proposed": "2058-08-28",
                "initiated_by": "lichtacker", "contracts": ("EKM-VTR-2058-0099",),
            },
            {
                "type": "partial_termination", "effective": "2060-01-18", "status": "signed",
                "proposed": "2059-10-20", "initiated_by": "lichtacker", "categories": ("energy",),
                "contracts": ("EKM-VTR-2059-0167", "EKM-VTR-2058-0105", "EKM-VTR-2058-0099"),
            },
            {
                "type": "price_adjustment", "effective": "2060-01-18", "status": "rejected", "proposed": "2059-10-28",
                "initiated_by": "eisenkrone", "categories": ("energy",), "pct": -5,
            },
            {
                "type": "volume_increase", "effective": "2059-11-01", "status": "signed", "volume_after_mcr": 200,
                "rule": "cumulative_over_90pct", "contracts": ("EKM-VTR-2059-0211",),
            },
            {
                "type": "term_extension", "effective": "2059-11-01", "status": "signed", "initiated_by": "lichtacker",
                "new_end_date": "2060-12-31", "rule": "calloff_after_end",
            },
        ),
    },
    {
        "number": "FSP-RV-2059-01", "seller": "feldspat", "buyer": "eisenkrone",
        "title": "Abnahmerahmen Quantenquarz Becker", "start": "2059-08-01", "term_months": 24, "base_volume_mcr": 12,
        "price_formula": "market_minus", "indexation": "category_price_index", "base_discount_pct": 5,
        "exclusivity": "right_of_first_refusal", "exclusive_archetypes": ("quantum_quartz",), "notice_days": 90,
        "scope": ("raw_materials",),
        "amendments": (
            {
                "type": "price_adjustment", "effective": "2059-11-20", "status": "signed", "proposed": "2059-11-05",
                "initiated_by": "feldspat", "pct": 12, "contracts": ("FSP-VTR-2059-0019",), "events": (65, 66),
            },
            {
                "type": "volume_increase", "effective": "2060-01-15", "status": "proposed", "proposed": "2059-12-15",
                "initiated_by": "feldspat", "volume_after_mcr": 20,
            },
        ),
    },
    {
        "number": "GFW-RV-2057-01", "seller": "graufalk", "buyer": "helix",
        "title": "Flottenrahmenvertrag Rumpf- und Triebwerksteile", "start": "2057-01-01", "term_months": 48,
        "base_volume_mcr": 180, "price_formula": "index_linked", "indexation": "category_price_index",
        "price_index_category": "industrial_goods", "exclusivity": "none", "notice_days": 180,
        "scope": ("industrial_goods",),
        "amendments": (
            {
                "type": "product_addition", "effective": "rule", "status": "signed", "categories": ("technology",),
                "rule": "first_contract_of_category",
            },
            {
                "type": "volume_increase", "effective": "2058-12-20", "status": "signed", "proposed": "2058-12-16",
                "initiated_by": "helix", "delta_mcr": 60, "contracts": ("HMX-CTR-2058-0173",),
            },
            {
                "type": "service_level_clause", "effective": "2060-01-15", "status": "proposed",
                "proposed": "2059-12-31", "initiated_by": "helix",
                "orders": ("HMX-ORD-2059-01763", "HMX-ORD-2059-01788"),
                "shipments": ("HMX-SHP-2059-01721", "HMX-SHP-2059-01746"),
            },
        ),
    },
    {
        "number": "GFW-RV-2057-02", "seller": "graufalk", "buyer": "cindervale",
        "title": "Allianzvertrag Navigationsplattform", "start": "2057-01-01", "term_months": 60,
        "base_volume_mcr": 220, "price_formula": "cost_plus", "indexation": "category_price_index",
        "cost_plus_pct": 8, "exclusivity": "none", "notice_days": 365, "scope": ("industrial_goods", "technology"),
        "amendments": (
            {
                "type": "exclusivity_clause", "effective": "2058-03-15", "status": "signed", "proposed": "2058-02-20",
                "initiated_by": "graufalk", "archetypes": ("drive_parts",), "exclusivity": "mutual", "events": (19,),
            },
            {
                "type": "volume_increase", "effective": "rule", "status": "signed", "delta_mcr": 80,
                "rule": "cumulative_over_90pct",
            },
            {
                "type": "confidentiality_clause", "effective": "2060-01-15", "status": "proposed",
                "proposed": "2059-12-29", "initiated_by": "cindervale",
            },
        ),
    },
    {
        "number": "GFW-RV-2058-01", "seller": "graufalk", "buyer": "ravenmoor",
        "title": "Geleitschiff-Rahmenvertrag Kharon/Brennus", "start": "2058-07-15", "term_months": 36,
        "base_volume_mcr": 90, "price_formula": "index_linked", "indexation": "category_price_index",
        "exclusivity": "right_of_first_refusal", "exclusive_archetypes": ("hull_plating",),
        "exclusivity_system": "kharon", "notice_days": 180, "scope": ("industrial_goods",),
        "amendments": (
            {
                "type": "product_addition", "effective": "rule", "status": "signed", "categories": ("technology",),
                "rule": "first_contract_of_category",
            },
            {
                "type": "volume_increase", "effective": "2059-09-01", "status": "signed", "proposed": "2059-08-25",
                "initiated_by": "ravenmoor", "delta_mcr": 40, "events": (45, 57, 58),
            },
        ),
    },
    {
        "number": "CCI-MSA-2057-01", "seller": "cindervale", "buyer": "eisenkrone",
        "title": "AI Control & Robotics Framework Agreement", "start": "2057-01-01", "term_months": 48,
        "base_volume_mcr": 120, "price_formula": "fixed", "indexation": "none",
        "exclusivity": "right_of_first_refusal", "exclusive_categories": ("technology",),
        "exclusivity_system": "halcyon", "notice_days": 180, "scope": ("technology", "industrial_goods"),
        "amendments": (
            {
                "type": "service_level_clause", "effective": "2058-03-01", "status": "signed",
                "proposed": "2058-02-10", "initiated_by": "eisenkrone", "events": (19,),
            },
            {
                "type": "price_adjustment", "effective": "2058-12-15", "status": "signed", "proposed": "2058-11-20",
                "initiated_by": "cindervale", "pct": -8, "events": (36,),
            },
            {
                "type": "suspension", "effective": "2059-12-15", "status": "signed", "proposed": "2059-12-05",
                "initiated_by": "eisenkrone", "events": (70,),
            },
        ),
    },
    {
        "number": "KHB-RV-2058-01", "seller": "kuppelwerk", "buyer": "pionierwerk",
        "title": "Rahmenvertrag Habitatmodule Isolde", "start": "2058-06-01", "term_months": 36,
        "base_volume_mcr": 70, "price_formula": "cost_plus", "indexation": "fuel_index", "cost_plus_pct": 10,
        "exclusivity": "seller_exclusive", "exclusive_archetypes": ("habitat_modules",),
        "exclusivity_system": "isolde", "notice_days": 180, "scope": ("industrial_goods",),
        "amendments": (
            {
                "type": "volume_increase", "effective": "2059-05-01", "status": "signed", "proposed": "2059-04-15",
                "initiated_by": "pionierwerk", "delta_mcr": 35,
            },
            {
                "type": "scope_extension", "effective": "2059-10-01", "status": "signed", "proposed": "2059-09-10",
                "initiated_by": "pionierwerk", "archetypes": ("sinter_blocks",), "system": "serravel",
            },
        ),
    },
    {
        "number": "KHB-RV-2059-01", "seller": "kuppelwerk", "buyer": "lichtacker",
        "title": "Baustoffrahmen Verbundstahl und Habitatbaustoffe Tauvel/Myrrhen", "start": "2059-04-01",
        "term_months": 24, "base_volume_mcr": 30, "price_formula": "cost_plus", "indexation": "fuel_index",
        "cost_plus_pct": 10, "exclusivity": "none", "notice_days": 90, "scope": ("industrial_goods", "raw_materials"),
        "scope_archetypes": {"raw_materials": ("regolith", "water_ice")},
        "amendments": (
            {
                "type": "product_addition", "effective": "2059-08-01", "status": "signed", "proposed": "2059-07-20",
                "initiated_by": "kuppelwerk", "archetypes": ("habitat_modules",), "events": (53,),
            },
            {"type": "volume_increase", "effective": "rule", "status": "signed", "rule": "cumulative_over_90pct",},
            {
                "type": "exclusivity_clause", "effective": "2060-02-01", "status": "proposed",
                "proposed": "2059-12-10", "initiated_by": "kuppelwerk",
                "archetypes": ("sinter_blocks", "habitat_modules"), "exclusivity": "regional_exclusive",
                "system": "myrrhen",
            },
        ),
    },
    {
        "number": "EFF-MSA-2059-01", "seller": "emberline", "buyer": "corvane",
        "title": "Helium-3 Supply Framework Halcyon Works VI", "start": "2059-04-01", "term_months": 24,
        "base_volume_mcr": 40, "price_formula": "index_linked", "indexation": "fuel_index", "exclusivity": "none",
        "notice_days": 90, "scope": ("energy",),
        "amendments": (
            {
                "type": "force_majeure_clause", "effective": "2059-09-15", "status": "signed",
                "proposed": "2059-09-05", "initiated_by": "emberline", "events": (59,),
            },
            {"type": "volume_increase", "effective": "rule", "status": "signed", "rule": "cumulative_over_90pct",},
            {
                "type": "exclusivity_clause", "effective": "2060-01-01", "status": "proposed",
                "proposed": "2059-12-05", "initiated_by": "emberline", "archetypes": ("helium3",),
                "exclusivity": "buyer_exclusive", "system": "halcyon",
            },
        ),
    },
    {
        "number": "EFF-MSA-2059-02", "seller": "emberline", "buyer": "lichtacker",
        "title": "Energy Framework Agreement Agrarstation Seip", "start": "2059-11-15", "term_months": 24,
        "base_volume_mcr": 18, "price_formula": "index_linked", "indexation": "fuel_index", "exclusivity": "none",
        "notice_days": 90, "scope": ("energy",),
        "amendments": (
            {
                "type": "exclusivity_clause", "effective": "2060-01-18", "status": "signed", "proposed": "2059-11-15",
                "initiated_by": "lichtacker", "categories": ("energy",), "exclusivity": "right_of_first_refusal",
                "system": "myrrhen",
            },
        ),
    },
    {
        "number": "RCS-MSA-2058-01", "seller": "ravenmoor", "buyer": "helix",
        "title": "Escort & Frontier Supply Framework Kharon Corridor", "start": "2058-08-01", "term_months": 36,
        "base_volume_mcr": 90, "price_formula": "cost_plus", "indexation": "risk_index", "cost_plus_pct": 15,
        "exclusivity": "regional_exclusive", "exclusive_archetypes": ("escort_drones", "sensor_arrays"),
        "exclusivity_system": "kharon", "notice_days": 90,
        "scope": ("industrial_goods", "technology", "medical", "food"), "escort": "ravenmoor",
        "amendments": (
            {
                "type": "volume_increase", "effective": "2059-06-15", "status": "signed", "proposed": "2059-06-05",
                "initiated_by": "helix", "delta_mcr": 40, "events": (51,),
            },
            {
                "type": "escort_clause", "effective": "2060-02-01", "status": "proposed", "proposed": "2059-12-22",
                "initiated_by": "ravenmoor", "escort": "ravenmoor", "events": (74,),
            },
            {
                "type": "scope_extension", "effective": "2060-01-15", "status": "proposed", "proposed": "2059-12-23",
                "initiated_by": "helix", "station": "Kharon Landing IV", "events": (74,),
            },
        ),
    },
    {
        "number": "RVF-RV-2058-01", "seller": "raureif", "buyer": "pionierwerk",
        "title": "Versorgungsrahmen Isolde – Volatile", "start": "2058-01-01", "term_months": 36,
        "base_volume_mcr": 80, "price_formula": "index_linked", "indexation": "fuel_index",
        "exclusivity": "regional_exclusive", "exclusive_archetypes": ("water_ice",), "exclusivity_system": "isolde",
        "notice_days": 180, "scope": ("raw_materials", "energy"),
        "amendments": (
            {
                "type": "exclusivity_clause", "effective": "2058-09-01", "status": "signed", "proposed": "2058-08-15",
                "initiated_by": "pionierwerk", "archetypes": ("nitrogen_ice",), "exclusivity": "regional_exclusive",
                "system": "isolde",
            },
            {
                "type": "volume_increase", "effective": "2059-06-01", "status": "signed", "proposed": "2059-05-15",
                "initiated_by": "pionierwerk", "delta_mcr": 30,
            },
            {
                "type": "price_adjustment", "effective": "2060-01-01", "status": "proposed", "proposed": "2059-11-20",
                "initiated_by": "raureif", "pct": 10,
            },
        ),
    },
    {
        "number": "RVF-RV-2058-02", "seller": "raureif", "buyer": "eisenkrone",
        "title": "Volatile-Liefervertrag Myrrhen/Brennus", "start": "2058-03-01", "term_months": 24,
        "base_volume_mcr": 45, "price_formula": "index_linked", "indexation": "category_price_index",
        "price_index_category": "raw_materials", "exclusivity": "none", "notice_days": 90,
        "scope": ("raw_materials", "energy"), "price_floor": True,
        "amendments": (
            {
                "type": "price_adjustment", "effective": "2059-08-01", "status": "signed", "proposed": "2059-07-25",
                "initiated_by": "eisenkrone", "pct": -6, "events": (52,),
            },
            {
                "type": "term_extension", "effective": "2060-02-29", "status": "proposed", "proposed": "2059-12-15",
                "initiated_by": "eisenkrone", "new_end_date": "2061-02-28",
            },
        ),
    },
    {
        "number": "OSP-MSA-2058-01", "seller": "outmark", "buyer": "pionierwerk",
        "title": "Survey Data License Framework Serravel/Isolde", "start": "2058-02-01", "term_months": 36,
        "base_volume_mcr": 25, "price_formula": "fixed", "indexation": "none", "exclusivity": "none",
        "notice_days": 180, "scope": ("technology", "raw_materials"),
        "amendments": (
            {
                "type": "exclusivity_clause", "effective": "2059-08-15", "status": "signed", "proposed": "2059-07-30",
                "initiated_by": "pionierwerk", "archetypes": ("survey_charts",), "exclusivity": "regional_exclusive",
                "system": "serravel", "events": (52,),
            },
            {
                "type": "product_addition", "effective": "2059-11-01", "status": "signed",
                "archetypes": ("terraforming_cultures",), "condition": "archetype_in_seller_pool",
            },
        ),
    },
    {
        "number": "SGM-RV-2059-01", "seller": "morgengrund", "buyer": "pionierwerk",
        "title": "Versorgungsrahmen Isolde – Lebensmittel für Bautrupps", "start": "2059-01-01", "term_months": 12,
        "base_volume_mcr": 5, "price_formula": "fixed", "indexation": "none", "exclusivity": "none",
        "notice_days": 60, "scope": ("food",), "auto_renewal": True, "renewal_months": 12, "harvest_clause": True,
        "amendments": (
            {
                "type": "volume_increase", "effective": "2059-07-01", "status": "signed", "proposed": "2059-06-15",
                "initiated_by": "pionierwerk", "delta_mcr": 2,
            },
            {"type": "term_extension", "effective": "2060-01-01", "status": "signed", "new_end_date": "2060-12-31",},
        ),
    },
    {
        "number": "SGM-RV-2059-02", "seller": "morgengrund", "buyer": "ravenmoor",
        "title": "Garnisonsrationen Kharon und Brennus", "start": "2059-03-01", "term_months": 12,
        "base_volume_mcr": 6, "price_formula": "fixed", "indexation": "none", "exclusivity": "none",
        "notice_days": 60, "scope": ("food",),
        "amendments": (
            {
                "type": "force_majeure_clause", "effective": "2059-03-01", "status": "signed",
                "proposed": "2059-02-15", "initiated_by": "morgengrund",
            },
            {
                "type": "term_extension", "effective": "2060-02-29", "status": "proposed", "proposed": "2059-12-20",
                "initiated_by": "ravenmoor", "new_end_date": "2061-02-28",
            },
        ),
    },
)

# Sperren für neue Verkäufer (Durchlauf 2): gelten für Verträge (Beginn) und Partner-Spotbestellungen (Datum).
# Vorkaufsrechte filtern nicht; ihre Verstöße sind Stoff für den Schriftverkehr.
EXCLUSIVITY_FILTERS: tuple[dict[str, Any], ...] = (
    {"sellers": ("emberline",), "buyer": "corvane", "categories": ("energy",), "until": "2059-03-14",
     "reason": "HMX-MSA-2057-02: Energie käuferexklusiv"},
    {"sellers": ("kuppelwerk",), "buyer": "lichtacker", "categories": ("industrial_goods",), "until": "2059-03-14",
     "reason": "Vorkaufsrecht Helix (HMX-MSA-2057-01)"},
    {"sellers": ("graufalk",), "buyer": "helix", "archetypes": ("escort_drones", "sensor_arrays"),
     "system": "kharon", "from": "2058-08-01", "reason": "RCS-MSA-2058-01 regional exklusiv"},
    {"sellers": ("emberline", "kometenpost"), "buyer": "cindervale", "archetypes": ("drive_parts",),
     "from": "2058-03-15", "reason": "GFW-RV-2057-02 gegenseitig"},
    {"sellers": ("emberline", "lanternfish", "second_hull", "kuppelwerk"), "buyer": "graufalk",
     "archetypes": ("nav_computers",), "from": "2058-03-15", "reason": "GFW-RV-2057-02 gegenseitig"},
    {"sellers": ("second_hull", "outmark", "morgengrund", "kuppelwerk"), "buyer": "pionierwerk",
     "archetypes": ("water_ice",), "system": "isolde", "from": "2058-01-01", "reason": "RVF-RV-2058-01 regional"},
    {"sellers": ("second_hull", "outmark", "morgengrund", "kuppelwerk"), "buyer": "pionierwerk",
     "archetypes": ("nitrogen_ice",), "system": "isolde", "from": "2058-09-01",
     "reason": "RVF-RV-2058-01, Nachtrag Stickstoffeis"},
    {"sellers": ("kuppelwerk",), "allowed_buyer": "pionierwerk", "archetypes": ("habitat_modules",),
     "system": "isolde", "from": "2058-06-01", "reason": "KHB-RV-2058-01 verkäuferexklusiv"},
)

# Einstellungsgrenzen der neuen Firmen: Vorstand, erste Partnerbetreuung und erste Marktaufklärung sind
# spätestens an diesem Tag eingestellt (frühestes verankertes Schreiben bzw. Rahmenbeginn minus Vorlauf).
HIRE_DATE_CAPS: dict[str, date] = {
    "graufalk": date(2056, 11, 2), "cindervale": date(2056, 11, 2), "kuppelwerk": date(2058, 4, 2),
    "emberline": date(2059, 1, 31), "kometenpost": date(2059, 4, 12), "pionierwerk": date(2057, 11, 2),
    "ravenmoor": date(2058, 5, 16), "raureif": date(2057, 11, 2), "outmark": date(2057, 12, 3),
    "morgengrund": date(2058, 11, 2), "second_hull": date(2058, 3, 2),
}
HIRE_CAP_ROLES = ("executive", "relations", "intelligence")

# Sollwerte des Bestandsvergleichs bei Seed 42 (Entscheidung Phase 2, Abschnitt 5.2)
BASELINE_EXPECTED_ASSIGNED_CONTRACTS = 341
BASELINE_EXPECTED_VOLUME_TRIGGERS: frozenset[str] = frozenset({
    "HMX-CTR-2058-0161", "HMX-CTR-2059-0259", "HMX-CTR-2058-0152", "HMX-CTR-2059-0213", "HMX-CTR-2060-0281",
    "HMX-CTR-2059-0192", "HMX-CTR-2059-0236", "HMX-CTR-2060-0275", "EKM-VTR-2059-0160", "EKM-VTR-2060-0219",
    "EKM-VTR-2059-0151", "EKM-VTR-2060-0234", "EKM-VTR-2059-0211",
})

INCIDENT_CAUSES: tuple[tuple[str, str], ...] = (
    ("Ausweichkurs wegen Asteroidensturm", "Rerouted around an asteroid storm"),
    ("Verzögerte Zollkontrolle am Zielhafen", "Held up by customs inspection at destination"),
    ("Triebwerksschaden, Notreparatur unterwegs", "Drive malfunction, emergency repair en route"),
    ("Piratenaktivität im Korridor, Geleitschutz abgewartet", "Pirate activity in the corridor, waited for escort"),
    ("Andockstau an der Zielstation", "Docking congestion at destination"),
    ("Navigationsfehler nach Sensorausfall", "Navigation error after sensor failure"),
    ("Quarantäneprüfung der Ladung", "Cargo held for quarantine screening"),
)
ILLEGAL_INCIDENT = ("Razzia im Zielsystem – Umweg über eine Schattenroute",
                    "Raid in the destination system – detour via a shadow lane")

CUSTOMER_TYPE_BY_STATION: dict[str, tuple[str, ...]] = {
    "mining": ("mining_crew", "independent_trader"),
    "research": ("research_outpost", "independent_trader"),
    "agricultural": ("colony", "station_operator"),
    "trade_hub": ("independent_trader", "station_operator", "colony"),
    "free_port": ("independent_trader", "station_operator"),
    "smuggler_haven": ("independent_trader",),
    "military": ("military_garrison", "station_operator"),
    "industrial": ("manufacturer", "station_operator"),
}
CUSTOMER_NAME_TEMPLATES: dict[str, dict[str, str]] = {
    "de_DE": {
        "colony": "Siedlergemeinschaft {last}", "station_operator": "{last} Stationsdienste GmbH",
        "independent_trader": "Freihandel {first} {last}", "research_outpost": "Forschungsaußenposten {last}",
        "mining_crew": "Schürfkollektiv {last}", "military_garrison": "Garnisonsverwaltung {last}",
        "manufacturer": "{last} Fertigung KG",
    },
    "en_US": {
        "colony": "{last} Settlers' Collective", "station_operator": "{last} Station Services LLC",
        "independent_trader": "{first} {last} Free Trading", "research_outpost": "{last} Research Outpost",
        "mining_crew": "{last} Mining Crew", "military_garrison": "{last} Garrison Quartermaster",
        "manufacturer": "{last} Fabrication Inc.",
    },
}
CUSTOMER_CREDIT_LIMIT: dict[str, tuple[float, float]] = {
    "colony": (50_000, 400_000), "station_operator": (200_000, 1_500_000), "independent_trader": (20_000, 250_000),
    "research_outpost": (80_000, 600_000), "mining_crew": (30_000, 200_000),
    "military_garrison": (300_000, 2_000_000), "manufacturer": (250_000, 2_500_000),
    "corporate_partner": (2_000_000, 25_000_000),
}


@dataclass(frozen=True)
class RoleInfo:
    """Rolle eines Mitarbeiters mit Gehalts-, Einfluss- und Informationszugang."""

    title_de: str
    title_en: str
    salary: tuple[float, float]
    influence: tuple[int, int]
    intel_access_level: int


ROLES: dict[str, RoleInfo] = {
    "executive": RoleInfo("Vorstandsvorsitz", "Chief Executive Officer", (38_000, 60_000), (85, 100), 3),
    "station_manager": RoleInfo("Stationsleitung", "Station Manager", (14_000, 24_000), (60, 85), 2),
    "trader": RoleInfo("Handelsagent:in", "Trade Agent", (6_000, 11_000), (25, 55), 1),
    "logistics": RoleInfo("Frachtdisposition", "Logistics Coordinator", (5_000, 8_500), (20, 45), 1),
    "security": RoleInfo("Sicherheitsdienst", "Security Officer", (4_500, 8_000), (15, 40), 1),
    "engineer": RoleInfo("Stationstechnik", "Station Engineer", (6_000, 10_000), (15, 40), 0),
    "pilot": RoleInfo("Frachtpilot:in", "Freighter Pilot", (7_000, 12_000), (15, 35), 1),
    "researcher": RoleInfo("Forschung & Entwicklung", "Research Scientist", (7_000, 13_000), (20, 45), 1),
    "agronomist": RoleInfo("Agrartechnik", "Agronomist", (4_500, 7_500), (10, 30), 0),
    "miner": RoleInfo("Bergbautechnik", "Mining Technician", (4_000, 7_000), (5, 25), 0),
    "finance": RoleInfo("Finanzbuchhaltung", "Finance Officer", (6_000, 10_500), (35, 60), 2),
    "customs": RoleInfo("Zollabwicklung", "Customs Broker", (5_000, 8_500), (20, 45), 1),
    "relations": RoleInfo("Partnerbetreuung", "Partner Relations Manager", (8_000, 14_000), (45, 75), 2),
    "intelligence": RoleInfo("Marktaufklärung", "Market Intelligence Analyst", (9_000, 16_000), (40, 70), 3),
}
STATION_ROLE_WEIGHTS: dict[str, dict[str, float]] = {
    "mining": {"miner": 5, "engineer": 2, "pilot": 1, "logistics": 1, "security": 1},
    "industrial": {"engineer": 5, "logistics": 2, "trader": 1, "security": 1, "customs": 0.5},
    "trade_hub": {"trader": 5, "logistics": 2, "customs": 1, "finance": 1, "security": 1, "relations": 1},
    "research": {"researcher": 5, "engineer": 1, "security": 1},
    "agricultural": {"agronomist": 5, "logistics": 1, "engineer": 1},
    "free_port": {"trader": 3, "customs": 1, "security": 2, "logistics": 1, "pilot": 1, "intelligence": 0.5},
    "military": {"security": 5, "pilot": 2, "engineer": 1, "logistics": 1},
    "smuggler_haven": {"trader": 3, "pilot": 2, "security": 2, "intelligence": 1},
}
PERSONALITIES = ("ambitious", "cautious", "greedy", "loyal", "idealistic", "pragmatic", "talkative")


@dataclass(frozen=True)
class EventType:
    """Regeln für einen Ereignistyp: wo er auftreten kann und wie er den Markt beeinflusst."""

    label_de: str
    label_en: str
    station_types: frozenset[str] | None
    security_levels: frozenset[str] | None
    product_filter: Callable[[dict[str, Any], dict[str, Any]], bool]
    supply: tuple[float, float]
    demand: tuple[float, float]
    duration_days: tuple[int, int]
    max_stations: int
    max_products: int
    weight: float
    text_de: str
    text_en: str


def _category_filter(*categories: str) -> Callable[[dict[str, Any], dict[str, Any]], bool]:
    """Produktfilter: nur Waren der genannten Kategorien."""
    allowed = frozenset(categories)
    return lambda product, _inventory: product["category_code"] in allowed


EVENT_TYPES: dict[str, EventType] = {
    "pirate_attack": EventType(
        "Piratenangriff", "Pirate Attack", None, frozenset({"medium", "low", "lawless"}),
        lambda product, _inv: True, (-0.45, -0.20), (0.0, 0.12), (21, 45), 2, 6, 3.0,
        "Piraten überfallen Frachter im Anflug auf {station} ({system}). Lieferungen von {products} brechen um "
        "{supply_pct} % ein, die Preise steigen um bis zu {price_pct} %.",
        "Pirates raid freighters approaching {station} ({system}). Deliveries of {products} drop by {supply_pct}%, "
        "prices climb by up to {price_pct}%."),
    "asteroid_storm": EventType(
        "Asteroidensturm", "Asteroid Storm", frozenset({"mining", "industrial", "research"}), None,
        _category_filter("raw_materials", "energy"), (-0.60, -0.30), (0.0, 0.05), (21, 40), 3, 6, 2.5,
        "Ein Asteroidensturm legt die Förderung rund um {station} ({system}) lahm. {products} werden knapp, "
        "Preisanstieg bis zu {price_pct} %.",
        "An asteroid storm halts extraction around {station} ({system}). {products} run short, prices up to "
        "{price_pct}% higher."),
    "strike": EventType(
        "Streik", "Strike", frozenset({"industrial", "mining", "trade_hub", "agricultural"}), None,
        _category_filter("industrial_goods", "technology", "raw_materials", "food"), (-0.50, -0.20), (0.0, 0.0),
        (21, 60), 1, 6, 1.5,
        "Die Besatzung von {station} ({system}) streikt für bessere Gefahrenzulagen. Die Produktion von {products} "
        "sinkt um {supply_pct} %.",
        "The crew of {station} ({system}) strikes for better hazard pay. Output of {products} falls by "
        "{supply_pct}%."),
    "machine_failure": EventType(
        "Maschinenausfall", "Machine Failure", frozenset({"industrial", "mining", "agricultural", "research"}), None,
        lambda _product, inv: inv["market_role"] == "supply", (-0.70, -0.35), (0.0, 0.0), (21, 40), 1, 3, 2.0,
        "Ausfall eines KI-Leitsystems auf {station} ({system}): Die Produktion von {products} bricht um "
        "{supply_pct} % ein.",
        "An AI control system fails on {station} ({system}): production of {products} drops by {supply_pct}%."),
    "crop_failure": EventType(
        "Ernteausfall", "Crop Failure", frozenset({"agricultural"}), None, _category_filter("food", "luxury"),
        (-0.70, -0.40), (0.05, 0.15), (45, 120), 2, 6, 3.0,
        "Ein Pilzbefall vernichtet Teile der Hydrokultur-Ringe von {station} ({system}). {products} werden knapp, "
        "Preise steigen um bis zu {price_pct} %.",
        "A fungal blight destroys parts of the hydroponic rings at {station} ({system}). {products} become scarce, "
        "prices rise by up to {price_pct}%."),
    "resource_discovery": EventType(
        "Rohstofffund", "Resource Discovery", frozenset({"mining"}), None, _category_filter("raw_materials", "energy"),
        (0.40, 1.00), (0.0, 0.0), (90, 240), 2, 5, 1.5,
        "Neue Vorkommen nahe {station} ({system}) entdeckt: Das Angebot an {products} steigt um {supply_pct} %, "
        "die Preise fallen um bis zu {price_pct} %.",
        "New deposits discovered near {station} ({system}): supply of {products} rises by {supply_pct}%, prices "
        "fall by up to {price_pct}%."),
    "customs_inspection": EventType(
        "Zollkontrolle", "Customs Inspection", frozenset({"trade_hub", "free_port", "military"}),
        frozenset({"high", "medium"}), lambda product, _inv: product["legal_status"] != "illegal",
        (-0.35, -0.15), (0.0, 0.05), (21, 30), 1, 5, 1.5,
        "Verschärfte Zollkontrollen auf {station} ({system}) bremsen die Einfuhr von {products}.",
        "Tightened customs checks at {station} ({system}) slow down imports of {products}."),
    "quarantine": EventType(
        "Quarantäne", "Quarantine", None, None, _category_filter("medical", "food"), (-0.20, -0.05), (0.50, 1.20),
        (30, 75), 1, 6, 1.2,
        "Quarantäne über {station} ({system}) verhängt. Die Nachfrage nach {products} steigt um {demand_pct} %.",
        "Quarantine imposed on {station} ({system}). Demand for {products} jumps by {demand_pct}%."),
    "black_market_raid": EventType(
        "Schwarzmarkt-Razzia", "Black Market Raid", frozenset({"smuggler_haven", "free_port"}),
        frozenset({"low", "lawless"}), _category_filter("contraband"), (-0.80, -0.50), (0.10, 0.30), (30, 60), 2, 4,
        4.0,
        "Razzia einer Söldnertruppe auf {station} ({system}): Bestände an {products} werden beschlagnahmt, "
        "Schwarzmarktpreise steigen um bis zu {price_pct} %.",
        "A mercenary raid hits {station} ({system}): stocks of {products} are seized, black-market prices climb "
        "by up to {price_pct}%."),
    "demand_boom": EventType(
        "Nachfrageboom", "Demand Boom", frozenset({"trade_hub", "industrial", "free_port", "military", "research"}),
        None, lambda product, _inv: True, (0.0, 0.0), (0.40, 1.00), (45, 120), 1, 5, 2.0,
        "Ein Bauboom auf {station} ({system}) lässt die Nachfrage nach {products} um {demand_pct} % steigen.",
        "A construction boom at {station} ({system}) drives demand for {products} up by {demand_pct}%."),
}


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def weighted_choice(rng: random.Random, weights: dict[K, float]) -> K:
    """Wählt einen Schlüssel gewichtet zufällig aus."""
    keys = [key for key, weight in weights.items() if weight > 0]
    return rng.choices(keys, weights=[weights[key] for key in keys], k=1)[0]


def pick_count(rng: random.Random, available: int, weights: dict[int, float]) -> int:
    """Wählt eine gewichtete Anzahl, die die verfügbare Menge nicht überschreitet."""
    options = {count: weight for count, weight in weights.items() if count <= available}
    return weighted_choice(rng, options) if options else 0


def clamp(value: float, low: float, high: float) -> float:
    """Begrenzt einen Wert auf ein Intervall."""
    return max(low, min(high, value))


def shift_months(day: date, months: int) -> date:
    """Verschiebt ein Datum um eine Anzahl Monate (Tag wird auf Monatsende begrenzt)."""
    month_index = day.year * 12 + (day.month - 1) + months
    year, month_zero = divmod(month_index, 12)
    last_day = calendar.monthrange(year, month_zero + 1)[1]
    return date(year, month_zero + 1, min(day.day, last_day))


def random_datetime(rng: random.Random, start: datetime, end: datetime) -> datetime:
    """Zufälliger Zeitpunkt (minutengenau) zwischen zwei Zeitpunkten."""
    span_seconds = max((end - start).total_seconds(), 0.0)
    moment = start + timedelta(seconds=rng.uniform(0, span_seconds))
    return moment.replace(second=0, microsecond=0)


def random_date(rng: random.Random, start: date, end: date) -> date:
    """Zufälliges Datum zwischen zwei Daten (inklusive)."""
    return start + timedelta(days=rng.randint(0, max((end - start).days, 0)))


def to_datetime(day: date) -> datetime:
    """Wandelt ein Datum in einen Zeitpunkt um 00:00 Uhr um."""
    return datetime(day.year, day.month, day.day)


def fmt_dt(moment: datetime) -> str:
    """ISO-Format für Zeitpunkte in der Datenbank."""
    return moment.strftime("%Y-%m-%d %H:%M:%S")


def fmt_date(day: date | datetime) -> str:
    """ISO-Format für Kalenderdaten in der Datenbank."""
    return day.strftime("%Y-%m-%d")


def fmt_number(value: float, language: str, decimals: int = 0) -> str:
    """Formatiert Zahlen mit sprachüblichen Tausender- und Dezimaltrennzeichen."""
    text = f"{value:,.{decimals}f}"
    if language == "de_DE":
        text = text.replace(",", "§").replace(".", ",").replace("§", ".")
    return text


def fmt_human_date(day: date, language: str) -> str:
    """Datum für Fließtexte."""
    return day.strftime("%d.%m.%Y") if language == "de_DE" else day.strftime("%b %d, %Y")


def lang_index(language: str) -> int:
    """Index 0 für Deutsch, 1 für Englisch in (de, en)-Tupeln."""
    return 0 if language == "de_DE" else 1


def person_name(fake: Faker) -> str:
    """Fiktiver Personenname aus Vor- und Nachname (ohne akademische Titel)."""
    return f"{fake.first_name()} {fake.last_name()}"


def roman(number: int) -> str:
    """Kleine römische Zahl für Stationsnamen."""
    return ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X")[(number - 1) % 10]


def euclidean_distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    """3D-Distanz zwischen zwei Stationen in Raumeinheiten."""
    return math.dist((a["x"], a["y"], a["z"]), (b["x"], b["y"], b["z"]))


def travel_time_hours(distance_units: float) -> float:
    """Reisezeit aus Distanz: Andockzeit plus Reiseflug mit fester Geschwindigkeit."""
    return round(DOCKING_OVERHEAD_HOURS + distance_units / CRUISE_SPEED_UNITS_PER_HOUR, 2)


def fuel_cost(distance_units: float, cargo_mass_kg: float, cargo_volume_m3: float, hold_capacity_m3: float) -> float:
    """Treibstoffkosten einer Sendung: Grundverbrauch anteilig zur Laderaumauslastung plus Masse.

    Frachter fahren gebündelt; eine Sendung trägt den Grundverbrauch nur im Verhältnis ihres Volumens.
    """
    utilisation = clamp(cargo_volume_m3 / hold_capacity_m3, 0.05, 1.0)
    tonnes = cargo_mass_kg / 1000.0
    return round(distance_units * (FUEL_COST_PER_DISTANCE_UNIT * utilisation
                                   + tonnes * FUEL_COST_PER_TONNE_DISTANCE), 2)


def round_quantity(value: float) -> int:
    """Rundet Mengen auf handelsübliche Gebinde."""
    if value >= 2000:
        return int(round(value / 50.0) * 50)
    if value >= 200:
        return int(round(value / 10.0) * 10)
    return max(1, int(round(value)))


def is_illegal_market(station: dict[str, Any]) -> bool:
    """Schwarzmarkt-tauglich sind nur Freihäfen und Schmugglerhäfen mit niedriger Sicherheit."""
    return (station["station_type"] in ILLEGAL_MARKET_STATION_TYPES
            and station["security_level"] in ILLEGAL_MARKET_SECURITY)


def can_trade_at(station: dict[str, Any], product: dict[str, Any]) -> bool:
    """Illegale Waren dürfen nur an Schwarzmarkt-tauglichen Stationen auftauchen."""
    return product["legal_status"] != "illegal" or is_illegal_market(station)


def route_risk_level(origin: dict[str, Any], destination: dict[str, Any], distance_units: float,
                     legal_status: str) -> str:
    """Risiko einer Route aus Sicherheitslage, Distanz und Legalstatus der Ware."""
    score = max(SECURITY_RISK_SCORE[origin["security_level"]], SECURITY_RISK_SCORE[destination["security_level"]])
    score += distance_units / 500.0
    score += {"legal": 0.0, "restricted": 0.6, "illegal": 2.0}[legal_status]
    if score < 1.0:
        return "low"
    if score < 2.0:
        return "medium"
    if score < 3.2:
        return "high"
    return "extreme"


def max_risk(levels: Iterable[str]) -> str:
    """Höchste Risikostufe einer Menge."""
    return max(levels, key=RISK_LEVELS.index)


# ---------------------------------------------------------------------------
# Datencontainer
# ---------------------------------------------------------------------------

PRIMARY_KEYS: dict[str, str] = {
    "companies": "company_id", "star_systems": "system_id", "stations": "station_id", "products": "product_id",
    "trade_partnerships": "partnership_id", "company_rivalries": "rivalry_id", "trade_routes": "route_id",
    "inventory": "inventory_id", "contracts": "contract_id", "customers": "customer_id", "orders": "order_id",
    "order_items": "order_item_id", "shipments": "shipment_id", "price_history": "price_history_id",
    "employees": "employee_id", "events": "event_id", "event_effects": "event_effect_id",
    "company_financials": "financial_id", "framework_agreements": "framework_agreement_id",
    "framework_agreement_amendments": "amendment_id", "framework_agreement_scope": "scope_id",
    "correspondence": "correspondence_id", "correspondence_copies": "copy_id",
}

INSERT_ORDER: tuple[str, ...] = (
    "companies", "star_systems", "stations", "products", "trade_partnerships", "company_rivalries",
    "framework_agreements", "trade_routes", "inventory", "contracts", "customers", "orders", "order_items",
    "shipments", "price_history", "employees", "events", "event_effects", "company_financials",
    "framework_agreement_amendments", "framework_agreement_scope", "correspondence", "correspondence_copies",
)


@dataclass
class World:
    """Hält alle erzeugten Zeilen sowie Nachschlage-Indizes während der Generierung."""

    seed: int
    rng: random.Random
    fakers: dict[str, Faker]
    rows: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))
    id_counters: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    profiles: dict[int, CompanyProfile] = field(default_factory=dict)
    company_ids_by_key: dict[str, int] = field(default_factory=dict)
    companies: dict[int, dict[str, Any]] = field(default_factory=dict)
    systems: dict[str, dict[str, Any]] = field(default_factory=dict)
    systems_by_id: dict[int, dict[str, Any]] = field(default_factory=dict)
    stations: dict[int, dict[str, Any]] = field(default_factory=dict)
    stations_by_company: dict[int, list[dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))
    products: dict[int, dict[str, Any]] = field(default_factory=dict)
    products_by_company: dict[int, list[dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))
    active_agreements: dict[tuple[int, int], dict[str, Any]] = field(default_factory=dict)
    market: dict[tuple[int, int], dict[str, Any]] = field(default_factory=dict)
    supply_stations: dict[int, list[int]] = field(default_factory=lambda: defaultdict(list))
    routes_by_pair: dict[tuple[int, int], list[dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))
    inventory: dict[tuple[int, int], dict[str, Any]] = field(default_factory=dict)
    contract_plans: dict[int, dict[str, Any]] = field(default_factory=dict)
    customers_by_company: dict[int, list[dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))
    order_timelines: dict[int, dict[str, Any]] = field(default_factory=dict)
    planned_events: list[dict[str, Any]] = field(default_factory=list)
    shocks: dict[tuple[int, int], list[dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))
    targets: dict[int, dict[str, int]] = field(default_factory=dict)
    frameworks: dict[tuple[int, int], dict[str, Any]] = field(default_factory=dict)
    extension_fakers: dict[str, Faker] = field(default_factory=dict)
    correspondence_notes: list[str] = field(default_factory=list)

    def add(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        """Fügt eine Zeile mit fortlaufender ID hinzu und gibt sie zurück."""
        self.id_counters[table] += 1
        full_row = {PRIMARY_KEYS[table]: self.id_counters[table], **row}
        self.rows[table].append(full_row)
        return full_row

    def window_start(self, company_id: int) -> date:
        """Beginn des Datenzeitraums einer Firma (abhängig von der Größe)."""
        months = SIZE_PROFILES[self.companies[company_id]["size_class"]].months
        return shift_months(GAME_REFERENCE_DATE, -months)

    def language(self, company_id: int) -> str:
        """Sprache einer Firma."""
        return self.companies[company_id]["language"]

    def fake(self, company_id: int) -> Faker:
        """Faker-Instanz in der Sprache der Firma (im aktiven Zufallsstrom)."""
        return self.fakers[self.language(company_id)]

    def key_of(self, company_id: int) -> str:
        """Profil-key einer Firma."""
        return self.profiles[company_id].key

    def is_legacy(self, company_id: int) -> bool:
        """True für die sechs Bestandsfirmen."""
        return self.profiles[company_id].key in LEGACY_COMPANY_KEYS

    def legacy_company_ids(self) -> list[int]:
        """Bestandsfirmen in fester Reihenfolge."""
        return [cid for cid in self.companies if self.is_legacy(cid)]

    def extension_company_ids(self) -> list[int]:
        """Erweiterungsfirmen in fester Reihenfolge."""
        return [cid for cid in self.companies if not self.is_legacy(cid)]

    @contextmanager
    def company_stream(self, key: str, step: str) -> Iterator[random.Random]:
        """Aktiviert den Zufallsstrom einer Firma für einen Generierungsschritt.

        Bestandsfirmen nutzen weiter den gemeinsamen Strom (`self.rng`, Faker je Sprache) in der
        bisherigen Reihenfolge. Erweiterungsfirmen bekommen einen eigenen, aus (Seed, key, Schritt)
        abgeleiteten Strom samt eigener Faker-Instanzen. So verschieben neue Firmen die Zufallsfolge
        der Bestandsfirmen nicht.
        """
        if key in LEGACY_COMPANY_KEYS:
            yield self.rng
            return
        saved_rng, saved_fakers = self.rng, self.fakers
        stream_seed = derived_seed(self.seed, key, step)
        if not self.extension_fakers:
            self.extension_fakers = {language: Faker(language) for language in LANGUAGES}
        for offset, (language, fake) in enumerate(self.extension_fakers.items()):
            fake.seed_instance(stream_seed + offset)
        self.rng, self.fakers = random.Random(stream_seed), self.extension_fakers
        try:
            yield self.rng
        finally:
            self.rng, self.fakers = saved_rng, saved_fakers


def derived_seed(seed: int, key: str, step: str) -> int:
    """Stabiler Teil-Seed aus (Seed, Firmen-key, Schritt), unabhängig von PYTHONHASHSEED."""
    digest = hashlib.sha256(f"{seed}:{key}:{step}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def build_world(seed: int) -> World:
    """Initialisiert Zufallsgeneratoren und Faker-Instanzen reproduzierbar."""
    Faker.seed(seed)
    fakers = {language: Faker(language) for language in LANGUAGES}
    return World(seed=seed, rng=random.Random(seed), fakers=fakers)


# ---------------------------------------------------------------------------
# 1. Firmen
# ---------------------------------------------------------------------------


def generate_companies(world: World) -> None:
    """Legt die 18 Firmen samt Mengenzielen innerhalb der Größenklassen an.

    Zuerst die sechs Bestandsfirmen mit dem gemeinsamen Strom (inklusive der bisherigen
    Mindest-Stationszahl), danach die Erweiterungsfirmen in eigenen Strömen.
    """
    for profile in COMPANY_PROFILES:
        if profile.key in LEGACY_COMPANY_KEYS:
            add_company(world, profile)
    ensure_minimum_station_count(world, world.legacy_company_ids())
    for profile in COMPANY_PROFILES:
        if profile.key not in LEGACY_COMPANY_KEYS:
            with world.company_stream(profile.key, "company"):
                add_company(world, profile)
    with world.company_stream("extension", "station_minimum"):
        ensure_minimum_station_count(world, world.extension_company_ids())


def add_company(world: World, profile: CompanyProfile) -> None:
    """Legt eine Firma samt Mengenzielen im aktiven Zufallsstrom an."""
    rng = world.rng
    size = SIZE_PROFILES[profile.size_class]
    founded_year = rng.randint(*profile.founded_range)
    founder = person_name(world.fakers[profile.language])
    row = world.add("companies", {
        "name": profile.name,
        "slug": profile.slug,
        "language": profile.language,
        "size_class": profile.size_class,
        "headquarters_station_id": None,  # wird in Schritt 2 gesetzt
        "founded_year": founded_year,
        "description": profile.description.format(name=profile.name, year=founded_year, founder=founder),
        "credit_rating": rng.choice(profile.credit_ratings),
        "is_player_accessible": 1,
        "specialization": profile.specialization,
        "network_role": profile.network_role,
        "data_window_start": fmt_date(shift_months(GAME_REFERENCE_DATE, -size.months)),
        "starting_cash": round(rng.uniform(*size.starting_cash), -3),
    })
    company_id = row["company_id"]
    world.companies[company_id] = row
    world.profiles[company_id] = profile
    world.company_ids_by_key[profile.key] = company_id
    world.targets[company_id] = {
        "stations": rng.randint(*size.stations),
        "products": rng.randint(*size.products),
        "contracts": rng.randint(*size.contracts),
        "orders": rng.randint(*size.orders),
        "customers": rng.randint(*size.customers),
        "employees": rng.randint(*size.employees),
    }


def ensure_minimum_station_count(world: World, candidates: Sequence[int]) -> None:
    """Erhöht Stationszahlen großer/mittlerer Firmen, bis die Welt mindestens 30 Stationen hat.

    Aufgestockt werden nur die übergebenen Firmen (Bestandsschutz: im zweiten Aufruf nur neue Firmen).
    """
    while sum(target["stations"] for target in world.targets.values()) < MIN_TOTAL_STATIONS:
        expandable = [cid for cid, company in world.companies.items()
                      if cid in candidates and company["size_class"] in ("large", "medium")
                      and world.targets[cid]["stations"] < SIZE_PROFILES[company["size_class"]].stations[1]]
        if not expandable:
            raise RuntimeError("Mindestanzahl an Stationen ist mit den Größenklassen nicht erreichbar.")
        large_first = [cid for cid in expandable if world.companies[cid]["size_class"] == "large"]
        world.targets[world.rng.choice(large_first or expandable)]["stations"] += 1


# ---------------------------------------------------------------------------
# 2. Sternensysteme und Stationen
# ---------------------------------------------------------------------------


def generate_star_systems(world: World) -> None:
    """Legt die Sternensysteme mit Koordinaten und Freischaltstufe an."""
    for system in STAR_SYSTEMS:
        row = world.add("star_systems", {
            "code": system.code,
            "name": system.name,
            "sector_code": system.sector_code,
            "x": system.center[0], "y": system.center[1], "z": system.center[2],
            "unlock_tier": system.unlock_tier,
            "base_security": system.base_security,
            "description_de": system.description_de,
            "description_en": system.description_en,
        })
        world.systems[system.code] = row
        world.systems_by_id[row["system_id"]] = row


def station_security(base_security: str, station_type: str) -> str:
    """Sicherheitslevel einer Station aus Systemlage und Stationstyp."""
    if station_type == "military":
        return "high"
    if station_type == "smuggler_haven":
        return "lawless"
    index = SECURITY_LEVELS.index(base_security)
    if station_type == "free_port":
        index = min(index + 1, len(SECURITY_LEVELS) - 1)
    return SECURITY_LEVELS[index]


def make_station_name(world: World, company_id: int, station_type: str, system_name: str,
                      used_names: set[str]) -> str:
    """Erzeugt einen eindeutigen, lokalisierten Stationsnamen (Faker-Nachnamen als Pioniernamen)."""
    rng = world.rng
    language = world.language(company_id)
    fake = world.fake(company_id)
    info = STATION_TYPES[station_type]
    for attempt in range(50):
        surname = fake.last_name()
        pattern = rng.randint(0, 2)
        if language == "de_DE":
            candidates = (f"{info.label_de} {surname}", f"{surname}-{info.suffix_de}",
                          f"{system_name} {info.suffix_de} {roman(rng.randint(1, 9))}")
        else:
            port_name = f"Port {surname}" if station_type in ("trade_hub", "free_port") else f"{info.label_en} {surname}"
            candidates = (f"{surname} {info.suffix_en}", port_name,
                          f"{system_name} {info.suffix_en} {roman(rng.randint(1, 9))}")
        name = candidates[pattern]
        if attempt > 30:
            name = f"{name} {roman(attempt % 10 + 1)}"
        if name not in used_names:
            used_names.add(name)
            return name
    raise RuntimeError("Konnte keinen eindeutigen Stationsnamen erzeugen.")


def station_description(language: str, station_type: str, system: dict[str, Any], operator: str,
                        security: str) -> str:
    """Lokalisierte Kurzbeschreibung einer Station."""
    info = STATION_TYPES[station_type]
    sector = SECTOR_LABELS[system["sector_code"]][language]
    security_label = SECURITY_LABELS[security][language]
    if language == "de_DE":
        return (f"{info.label_de} im {system['name']}-System ({sector}), betrieben von {operator}. "
                f"Die Station {info.purpose_de}. Sicherheitsniveau: {security_label}.")
    return (f"{info.label_en} in the {system['name']} system ({sector}), operated by {operator}. "
            f"The station {info.purpose_en}. Security level: {security_label}.")


def generate_stations(world: World) -> None:
    """Verteilt die Stationen jeder Firma auf ihr Territorium; die erste Station ist der Hauptsitz."""
    used_names: set[str] = set()
    for company_id in world.companies:
        with world.company_stream(world.key_of(company_id), "stations"):
            generate_company_stations(world, company_id, used_names)


def generate_company_stations(world: World, company_id: int, used_names: set[str]) -> None:
    """Stationen einer Firma im aktiven Zufallsstrom (Namen eindeutig über alle Firmen)."""
    rng = world.rng
    company = world.companies[company_id]
    profile = world.profiles[company_id]
    language = company["language"]
    target = world.targets[company_id]["stations"]
    layout: list[tuple[str, str]] = list(profile.required_stations)
    while len(layout) < target:
        layout.append((weighted_choice(rng, profile.station_type_weights),
                       weighted_choice(rng, profile.territory)))
    for station_type, system_code in layout:
        system = world.systems[system_code]
        info = STATION_TYPES[station_type]
        security = station_security(system["base_security"], station_type)
        size = SIZE_PROFILES[company["size_class"]]
        population = int(rng.randint(*info.population) * size.population_factor
                         * (2 if system["unlock_tier"] == 0 else 1))
        coords = [clamp(system[axis] + rng.gauss(0, 12.0), -COORDINATE_LIMIT, COORDINATE_LIMIT)
                  for axis in ("x", "y", "z")]
        name = make_station_name(world, company_id, station_type, system["name"], used_names)
        row = world.add("stations", {
            "name": name,
            "company_id": company_id,
            "system_id": system["system_id"],
            "system_name": system["name"],
            "sector": SECTOR_LABELS[system["sector_code"]][language],
            "x": round(coords[0], 2), "y": round(coords[1], 2), "z": round(coords[2], 2),
            "population": population,
            "station_type": station_type,
            "security_level": security,
            "description": station_description(language, station_type, system, company["name"], security),
            "unlock_tier": system["unlock_tier"],
            "storage_capacity_m3": 0.0,  # wird nach Lager und Bestellungen berechnet
            "monthly_upkeep": round((info.base_upkeep + population * 3.5)
                                    * size.upkeep_factor, -2),
            "docking_fee": round(rng.uniform(150, 600) * SECURITY_PRICE_PREMIUM[security]
                                 * (1.6 if system["unlock_tier"] == 0 else 1.0), 2),
        })
        world.stations[row["station_id"]] = row
        world.stations_by_company[company_id].append(row)
    company["headquarters_station_id"] = world.stations_by_company[company_id][0]["station_id"]


# ---------------------------------------------------------------------------
# 3. Produkte
# ---------------------------------------------------------------------------


def generate_products(world: World) -> None:
    """Leitet für jede Firma einen Warenkatalog aus Archetypen und Varianten ab.

    Erweiterungs-Archetypen stehen nur den neuen Firmen zur Verfügung, damit die Pools (und damit die
    Kataloge) der Bestandsfirmen unverändert bleiben.
    """
    for company_id in world.companies:
        legacy = world.is_legacy(company_id)
        archetypes_by_category: dict[str, list[ProductArchetype]] = defaultdict(list)
        for archetype in PRODUCT_ARCHETYPES:
            if not (legacy and archetype.extension):
                archetypes_by_category[archetype.category].append(archetype)
        with world.company_stream(world.key_of(company_id), "products"):
            generate_company_products(world, company_id, archetypes_by_category)


def generate_company_products(world: World, company_id: int,
                              archetypes_by_category: dict[str, list[ProductArchetype]]) -> None:
    """Warenkatalog einer Firma im aktiven Zufallsstrom."""
    rng = world.rng
    company = world.companies[company_id]
    profile = world.profiles[company_id]
    language = company["language"]
    idx = lang_index(language)
    has_black_market = any(is_illegal_market(s) for s in world.stations_by_company[company_id])
    weights = {cat: w for cat, w in profile.category_weights.items()
               if cat != "contraband" or has_black_market}
    pool: dict[str, list[tuple[ProductArchetype, tuple[str, str, float]]]] = {
        cat: [(arch, variant) for arch in archetypes_by_category[cat] for variant in CATEGORY_VARIANTS[cat]]
        for cat in weights
    }
    for options in pool.values():
        rng.shuffle(options)
    target = world.targets[company_id]["products"]
    sku_counter: dict[str, int] = defaultdict(int)
    for _ in range(target):
        available = {cat: w for cat, w in weights.items() if pool[cat]}
        if not available:
            break
        category = weighted_choice(rng, available)
        archetype, variant = pool[category].pop()
        variant_label = variant[idx]
        base_name = archetype.name_de if language == "de_DE" else archetype.name_en
        name = base_name if variant_label == "Standard" else f"{base_name} {variant_label}"
        base_price = round(archetype.base_price * variant[2] * rng.uniform(0.92, 1.10), 2)
        base_cost = round(base_price / rng.uniform(*CATEGORY_MARGIN[category]), 2)
        volume = round(archetype.volume_m3 * rng.uniform(0.95, 1.05), 4)
        mass = round(archetype.mass_kg * rng.uniform(0.95, 1.05), 3)
        unit = UNIT_LABELS[archetype.unit][idx]
        sku_counter[category] += 1
        sku = f"{profile.sku_prefix}-{category[:3].upper()}-{sku_counter[category]:04d}"
        tradeable = 0 if (category in ("technology", "industrial_goods", "medical") and rng.random() < 0.03) else 1
        description = (
            f"{name} aus dem Sortiment der {company['name']}. {CATEGORY_FLAVOR[category][0]} "
            f"Gehandelt je {unit}: {fmt_number(volume, language, 3)} m³, {fmt_number(mass, language, 1)} kg."
            if language == "de_DE" else
            f"{name} from the {company['name']} catalogue. {CATEGORY_FLAVOR[category][1]} "
            f"Traded per {unit}: {fmt_number(volume, language, 3)} m³, {fmt_number(mass, language, 1)} kg."
        ) + LEGAL_NOTES[archetype.legal_status][idx]
        if not tradeable:
            description += (" Prototyp – nur für den internen Gebrauch." if language == "de_DE"
                            else " Prototype – internal use only.")
        row = world.add("products", {
            "company_id": company_id,
            "sku": sku,
            "name": name,
            "category": CATEGORY_LABELS[category][idx],
            "category_code": category,
            "archetype_code": archetype.code,
            "description": description,
            "base_price": base_price,
            "base_cost": base_cost,
            "unit": unit,
            "volume_m3": volume,
            "mass_kg": mass,
            "legal_status": archetype.legal_status,
            "is_tradeable": tradeable,
        })
        world.products[row["product_id"]] = row
        world.products_by_company[company_id].append(row)


# ---------------------------------------------------------------------------
# 4. Partnerschaften und Rivalitäten
# ---------------------------------------------------------------------------


def partnership_start_date(world: World, seller_id: int, buyer_id: int) -> date:
    """Beginn einer Partnerschaft: nach Gründung beider Firmen, vor dem Datenzeitraum des Verkäufers."""
    earliest = date(max(world.companies[seller_id]["founded_year"], world.companies[buyer_id]["founded_year"]) + 1, 1, 1)
    latest = world.window_start(seller_id) - timedelta(days=30)
    if earliest > latest:
        earliest = latest - timedelta(days=365)
    return random_date(world.rng, earliest, latest)


def is_legacy_pair(*keys: str) -> bool:
    """True, wenn alle beteiligten Firmen Bestandsfirmen sind."""
    return all(key in LEGACY_COMPANY_KEYS for key in keys)


def add_active_partnership(world: World, seller_key: str, buyer_key: str, relationship: str) -> None:
    """Legt eine aktive, gerichtete Vereinbarung im aktiven Zufallsstrom an."""
    rng = world.rng
    seller_id = world.company_ids_by_key[seller_key]
    buyer_id = world.company_ids_by_key[buyer_key]
    trust = rng.randint(*TRUST_RANGES[relationship])
    if "driftwood" in (seller_key, buyer_key):
        trust = max(10, trust - 15)
    row = world.add("trade_partnerships", {
        "company_id": seller_id,
        "partner_company_id": buyer_id,
        "relationship_type": relationship,
        "trust_level": trust,
        "contract_volume": 0.0,  # Summe der Verträge, wird nach Schritt 8 gesetzt
        "start_date": fmt_date(partnership_start_date(world, seller_id, buyer_id)),
        "end_date": None,
        "is_active": 1,
    })
    world.active_agreements[(seller_id, buyer_id)] = row


def add_historic_partnership(world: World, seller_key: str, buyer_key: str, relationship: str) -> None:
    """Legt eine beendete Vereinbarung an (Bestand: zufällige Daten, Erweiterung: feste Daten)."""
    rng = world.rng
    seller_id = world.company_ids_by_key[seller_key]
    buyer_id = world.company_ids_by_key[buyer_key]
    fixed = HISTORIC_PARTNERSHIP_DATES.get((seller_key, buyer_key))
    if fixed is not None:
        start, end = date.fromisoformat(fixed[0]), date.fromisoformat(fixed[1])
    else:
        founded = max(world.companies[seller_id]["founded_year"], world.companies[buyer_id]["founded_year"])
        start = random_date(rng, date(founded + 1, 1, 1), date(founded + 2, 12, 31))
        end = random_date(rng, start + timedelta(days=200), world.window_start(buyer_id) - timedelta(days=120))
    world.add("trade_partnerships", {
        "company_id": seller_id,
        "partner_company_id": buyer_id,
        "relationship_type": relationship,
        "trust_level": rng.randint(3, 15),
        "contract_volume": round(rng.uniform(800_000, 4_000_000), 2),  # historisch, vor dem Datenzeitraum
        "start_date": fmt_date(start),
        "end_date": fmt_date(end),
        "is_active": 0,
    })


def generate_partnerships(world: World) -> None:
    """Erzeugt das gerichtete, unvollständige Partnerschaftsnetz (Verkäufer -> Käufer).

    Reihenfolge wie vor der Erweiterung: Bestandskanten (inkl. optionaler Kanten) und die historische
    Bestandskante im gemeinsamen Strom; danach die Erweiterungskanten, jede in einem eigenen Strom.
    """
    rng = world.rng
    blueprint = [edge for edge in PARTNERSHIP_BLUEPRINT if is_legacy_pair(edge[0], edge[1])]
    extension = [edge for edge in PARTNERSHIP_BLUEPRINT if not is_legacy_pair(edge[0], edge[1])]
    for seller, buyer, relationship, probability in OPTIONAL_PARTNERSHIPS:
        if is_legacy_pair(seller, buyer):
            if rng.random() < probability:
                blueprint.append((seller, buyer, relationship))
        else:
            with world.company_stream(seller, f"optional_partnership:{buyer}") as stream:
                if stream.random() < probability:
                    extension.append((seller, buyer, relationship))

    for seller_key, buyer_key, relationship in blueprint:
        add_active_partnership(world, seller_key, buyer_key, relationship)
    for seller_key, buyer_key, relationship in HISTORIC_PARTNERSHIPS:
        if is_legacy_pair(seller_key, buyer_key):
            add_historic_partnership(world, seller_key, buyer_key, relationship)

    for seller_key, buyer_key, relationship in extension:
        with world.company_stream(seller_key, f"partnership:{buyer_key}"):
            add_active_partnership(world, seller_key, buyer_key, relationship)
    for seller_key, buyer_key, relationship in HISTORIC_PARTNERSHIPS:
        if not is_legacy_pair(seller_key, buyer_key):
            stream_key = seller_key if seller_key not in LEGACY_COMPANY_KEYS else buyer_key
            with world.company_stream(stream_key, f"historic:{seller_key}:{buyer_key}"):
                add_historic_partnership(world, seller_key, buyer_key, relationship)


def generate_rivalries(world: World) -> None:
    """Legt Konkurrenz- und Spionagebeziehungen zwischen Firmen an.

    Bestandsrivalitäten werden wie bisher zufällig im gemeinsamen Strom bemessen; die
    Erweiterungsrivalitäten haben feste, an Bestandsereignissen festgemachte Kennzahlen.
    """
    rng = world.rng
    for company_key, rival_key, rivalry_type, system_code in RIVALRY_BLUEPRINT:
        company_id = world.company_ids_by_key[company_key]
        rival_id = world.company_ids_by_key[rival_key]
        language = world.language(company_id)
        system = world.systems[system_code]
        template = RIVALRY_TEXT_OVERRIDES.get((company_key, rival_key), RIVALRY_TEXTS[rivalry_type])[language]
        description = template.format(company=world.companies[company_id]["name"],
                                      rival=world.companies[rival_id]["name"], system=system["name"])
        details = RIVALRY_DETAILS.get((company_key, rival_key))
        if details is None:
            founded = max(world.companies[company_id]["founded_year"], world.companies[rival_id]["founded_year"])
            intensity = rng.randint(*RIVALRY_INTENSITY_RANGES[rivalry_type])
            espionage = rng.randint(50, 95) if rivalry_type == "industrial_espionage" else rng.randint(10, 60)
            since = fmt_date(random_date(rng, date(founded + 1, 1, 1), GAME_REFERENCE_DATE - timedelta(days=90)))
        else:
            since, intensity, espionage = details
        world.add("company_rivalries", {
            "company_id": company_id,
            "rival_company_id": rival_id,
            "rivalry_type": rivalry_type,
            "intensity": intensity,
            "contested_system_id": system["system_id"],
            "espionage_risk": espionage,
            "since_date": since,
            "description": description,
        })


# ---------------------------------------------------------------------------
# 5. Rahmenverträge (Grundlage; Zuordnung und Nachträge im letzten Schritt)
# ---------------------------------------------------------------------------


def month_start(day: date) -> date:
    """Erster Tag des Monats."""
    return day.replace(day=1)


def round_up(value: float, step: float) -> float:
    """Rundet auf ein Vielfaches von step auf."""
    return math.ceil(value / step - 1e-9) * step


def exclusivity_blocks(world: World, seller_id: int, buyer_id: int | None, product: dict[str, Any],
                       destination: dict[str, Any], day: date) -> bool:
    """True, wenn eine Exklusivitätssperre (EXCLUSIVITY_FILTERS) den Verkauf verbietet.

    buyer_id ist die Käuferfirma (None bei Nicht-Firmenkunden). Gilt nur für Erweiterungsverkäufer.
    """
    seller_key = world.key_of(seller_id)
    if seller_key in LEGACY_COMPANY_KEYS:
        return False
    buyer_key = world.key_of(buyer_id) if buyer_id is not None else None
    for rule in EXCLUSIVITY_FILTERS:
        if seller_key not in rule["sellers"]:
            continue
        if "categories" in rule and product["category_code"] not in rule["categories"]:
            continue
        if "archetypes" in rule and product["archetype_code"] not in rule["archetypes"]:
            continue
        if "system" in rule and destination["system_id"] != world.systems[rule["system"]]["system_id"]:
            continue
        if "from" in rule and day < date.fromisoformat(rule["from"]):
            continue
        if "until" in rule and day > date.fromisoformat(rule["until"]):
            continue
        if "allowed_buyer" in rule:
            if buyer_key != rule["allowed_buyer"]:
                return True
        elif buyer_key == rule["buyer"]:
            return True
    return False


def scope_entry(category: str, archetype: str | None, system_id: int | None, valid_from: date,
                kind: str = "include", exclusivity: str | None = None,
                amendment: dict[str, Any] | None = None) -> dict[str, Any]:
    """Ein Sortimentseintrag eines Rahmenvertrags.

    entry_kind: include (Ware gehört zum Rahmen), exclude (Ware ausdrücklich ausgenommen) oder
    exclusivity (Exklusivitätsrecht auf die Ware; ändert das Sortiment selbst nicht).
    """
    return {"category_code": category, "archetype_code": archetype, "system_id": system_id,
            "valid_from": valid_from, "valid_to": None, "entry_kind": kind, "exclusivity": exclusivity,
            "added_by": amendment, "removed_by": None}


def entry_active(entry: dict[str, Any], day: date) -> bool:
    """Eintrag gilt am Tag?"""
    return entry["valid_from"] <= day and (entry["valid_to"] is None or day <= entry["valid_to"])


def entry_matches(entry: dict[str, Any], category: str, archetype: str | None, system_id: int | None) -> bool:
    """Deckt der Eintrag Ware und Zielsystem ab? (system_id None = Systemprüfung entfällt)"""
    if entry["archetype_code"] is None:
        matches = entry["category_code"] == category
    else:
        matches = entry["archetype_code"] == archetype
    return matches and (entry["system_id"] is None or system_id is None or entry["system_id"] == system_id)


def scope_covers(entries: list[dict[str, Any]], category: str, archetype: str, system_id: int | None,
                 day: date) -> bool:
    """Ware am Tag im Sortiment (aufgenommen und nicht ausgenommen)?"""
    active = [e for e in entries if entry_active(e, day) and entry_matches(e, category, archetype, system_id)]
    return (any(e["entry_kind"] == "include" for e in active)
            and not any(e["entry_kind"] == "exclude" for e in active))


def scope_closed_for(entries: list[dict[str, Any]], category: str, archetype: str, day: date) -> bool:
    """Wurde die Ware vor dem Tag ausdrücklich herausgenommen (Teilkündigung, Herausnahme)?"""
    for entry in entries:
        if not entry_matches(entry, category, archetype, None):
            continue
        if entry["entry_kind"] == "exclude" and entry_active(entry, day):
            return True
        if (entry["entry_kind"] == "include" and entry["removed_by"] is not None
                and entry["valid_to"] is not None and entry["valid_to"] < day
                and entry["removed_by"]["amendment_type"] in ("partial_termination", "product_removal")):
            return True
    return False


def amendment_items(spec: dict[str, Any]) -> list[tuple[str, str | None]]:
    """(Kategorie, Archetyp)-Paare eines Nachtrags."""
    items: list[tuple[str, str | None]] = [(category, None) for category in spec.get("categories", ())]
    items += [(ARCHETYPES_BY_CODE[code].category, code) for code in spec.get("archetypes", ())]
    return items


def apply_scope_change(world: World, entries: list[dict[str, Any]], amendment: dict[str, Any]) -> None:
    """Wirkung eines Nachtrags auf das Sortiment."""
    effective = amendment["effective_date"]
    kind = amendment["amendment_type"]
    system_id = amendment.get("exclusive_system_id")

    def close(predicate: Callable[[dict[str, Any]], bool]) -> None:
        for entry in entries:
            if entry["valid_to"] is None and entry["valid_from"] <= effective and predicate(entry):
                entry["valid_to"] = effective - timedelta(days=1)
                entry["removed_by"] = amendment

    for category, archetype in amendment["items"]:
        if kind == "product_addition":
            entries.append(scope_entry(category, archetype, None, effective, amendment=amendment))
        elif kind == "scope_extension":
            entries.append(scope_entry(category, archetype, system_id, effective, amendment=amendment))
        elif kind == "product_removal":
            if archetype is None:
                close(lambda e, c=category: e["category_code"] == c and e["entry_kind"] != "exclude")
            else:
                entries.append(scope_entry(category, archetype, None, effective, kind="exclude", amendment=amendment))
        elif kind == "partial_termination":
            close(lambda e, c=category: e["category_code"] == c and e["entry_kind"] != "exclude")
        elif kind == "exclusivity_clause":
            entries.append(scope_entry(category, archetype, system_id, effective, kind="exclusivity",
                                       exclusivity=amendment.get("exclusivity"), amendment=amendment))
        elif kind == "exclusivity_waiver":
            close(lambda e, c=category, a=archetype: e["entry_kind"] == "exclusivity"
                  and e["category_code"] == c and e["archetype_code"] == a)


def base_scope_entries(world: World, spec: dict[str, Any], start: date) -> list[dict[str, Any]]:
    """Grundsortiment eines Rahmenvertrags inklusive Exklusivitätsrechten."""
    exclusive_system = (world.systems[spec["exclusivity_system"]]["system_id"]
                        if spec.get("exclusivity_system") else None)
    entries: list[dict[str, Any]] = []
    for category in spec["scope"]:
        archetypes = spec.get("scope_archetypes", {}).get(category)
        if archetypes:
            entries += [scope_entry(category, code, None, start) for code in archetypes]
        else:
            entries.append(scope_entry(category, None, None, start))
    for category in spec.get("exclusive_categories", ()):
        entries.append(scope_entry(category, None, exclusive_system, start, kind="exclusivity",
                                   exclusivity=spec["exclusivity"]))
    for code in spec.get("exclusive_archetypes", ()):
        entries.append(scope_entry(ARCHETYPES_BY_CODE[code].category, code, exclusive_system, start,
                                   kind="exclusivity", exclusivity=spec["exclusivity"]))
    return entries


def fixed_amendment_specs(world: World, framework: dict[str, Any]) -> list[dict[str, Any]]:
    """Feste (nicht regelbasierte) Nachträge eines Rahmenvertrags als Arbeitsobjekte."""
    seller_id, buyer_id = framework["seller_id"], framework["buyer_id"]
    result = []
    for index, spec in enumerate(framework["spec"]["amendments"]):
        if spec.get("rule") in AMENDMENT_RULES:
            continue
        if spec.get("condition") == "archetype_in_seller_pool" and not any(
                p["archetype_code"] in spec.get("archetypes", ()) for p in world.products_by_company[seller_id]):
            continue
        effective = date.fromisoformat(spec["effective"])
        initiator = spec.get("initiated_by")
        result.append({
            "spec": spec, "order": index, "amendment_type": spec["type"], "status": spec["status"],
            "effective_date": effective,
            "proposed_date": date.fromisoformat(spec["proposed"]) if spec.get("proposed") else None,
            "initiated_by_company_id": world.company_ids_by_key[initiator] if initiator else buyer_id,
            "items": amendment_items(spec), "rule": None,
            "exclusive_system_id": world.systems[spec["system"]]["system_id"] if spec.get("system") else None,
            "escort_company_id": world.company_ids_by_key[spec["escort"]] if spec.get("escort") else None,
            "exclusivity": spec.get("exclusivity") or (framework["spec"]["exclusivity"]
                                                       if spec["type"] == "exclusivity_clause" else None),
        })
    return sorted(result, key=lambda a: (a["effective_date"], a["order"]))


def framework_extension_end(framework: dict[str, Any], current_end: date, template: dict[str, Any] | None) -> date:
    """Neues Laufzeitende einer Regel-Verlängerung (Vorlage oder Verlängerungszeitraum des Rahmens)."""
    if template is not None and template.get("new_end_date"):
        proposed = date.fromisoformat(template["new_end_date"])
        if proposed > current_end:
            return proposed
    months = framework["spec"].get("renewal_months", DEFAULT_RENEWAL_MONTHS)
    return shift_months(current_end + timedelta(days=1), months) - timedelta(days=1)


def generate_framework_agreements(world: World) -> None:
    """Legt die Rahmenverträge der aktiven Vereinbarungen an (nach den Partnerschaften, vor den Verträgen).

    Jeder Rahmen gehört zu genau einer aktiven, gerichteten Vereinbarung; fehlt sie (z. B. eine nicht
    gezogene optionale Vereinbarung), entfällt der Rahmen. Für die Vertragsplanung der neuen Paare wird
    das geplante Sortiment (Grundsortiment, feste Nachträge, Regel-Aufnahmen) vorab bestimmt.
    """
    for spec in FRAMEWORK_BLUEPRINT:
        seller_id = world.company_ids_by_key[spec["seller"]]
        buyer_id = world.company_ids_by_key[spec["buyer"]]
        agreement = world.active_agreements.get((seller_id, buyer_id))
        if agreement is None:
            continue
        language = world.language(seller_id)
        start = date.fromisoformat(spec["start"])
        end = shift_months(start, spec["term_months"]) - timedelta(days=1)
        signed = start - timedelta(days=FRAMEWORK_SIGNING_LEAD_DAYS)
        price_index_category = spec.get("price_index_category")
        if price_index_category is None and spec["indexation"] == "category_price_index":
            price_index_category = spec["scope"][0]
        row = world.add("framework_agreements", {
            "agreement_number": spec["number"],
            "partnership_id": agreement["partnership_id"],
            "company_id": seller_id,
            "partner_company_id": buyer_id,
            "title": spec["title"],
            "language": language,
            "signed_date": fmt_date(signed),
            "start_date": fmt_date(start),
            "term_months": spec["term_months"],
            "end_date": fmt_date(end),
            "current_end_date": fmt_date(end),  # nach Nachträgen im letzten Schritt
            "status": "active",
            "base_volume": round(spec["base_volume_mcr"] * 1_000_000.0, 2),
            "current_volume_cap": round(spec["base_volume_mcr"] * 1_000_000.0, 2),
            "price_formula": spec["price_formula"],
            "indexation": spec["indexation"],
            "price_index_category": price_index_category,
            "base_discount_pct": spec.get("base_discount_pct"),
            "cost_plus_pct": spec.get("cost_plus_pct"),
            "adjustment_cap_pct": spec.get("adjustment_cap_pct"),
            "exclusivity": spec["exclusivity"],
            "exclusivity_system_id": (world.systems[spec["exclusivity_system"]]["system_id"]
                                      if spec.get("exclusivity_system") else None),
            "notice_period_days": spec["notice_days"],
            "auto_renewal": int(bool(spec.get("auto_renewal"))),
            "renewal_months": spec.get("renewal_months"),
            "penalty_rate_pct": DEFAULT_PENALTY_RATE_PCT,
            "escort_company_id": world.company_ids_by_key[spec["escort"]] if spec.get("escort") else None,
            "seller_signatory_id": None,  # nach den Mitarbeitern
            "buyer_signatory_id": None,
            "description": "",
        })
        framework = {"row": row, "spec": spec, "seller_id": seller_id, "buyer_id": buyer_id,
                     "language": language, "start": start, "end": end}
        row["description"] = framework_text(world, framework)
        # Geplantes Sortiment für die Vertragsplanung: Grundsortiment + feste Nachträge + Regel-Aufnahmen
        planned = base_scope_entries(world, spec, start)
        planned_end, suspended = end, None
        for amendment in fixed_amendment_specs(world, framework):
            if amendment["status"] != "signed":
                continue
            apply_scope_change(world, planned, amendment)
            if amendment["amendment_type"] == "term_extension" and amendment["spec"].get("new_end_date"):
                planned_end = max(planned_end, date.fromisoformat(amendment["spec"]["new_end_date"]))
            if amendment["amendment_type"] == "suspension":
                suspended = amendment["effective_date"]
        rule_categories = {category for a in spec["amendments"] if a.get("rule") == "first_contract_of_category"
                           for category in a.get("categories", ())}
        if any(a.get("rule") == "calloff_after_end" for a in spec["amendments"]):
            planned_end = framework_extension_end(framework, planned_end, None)
        framework.update(planned_scope=planned, planned_end=planned_end, planned_suspension=suspended,
                         rule_categories=rule_categories)
        world.frameworks[(seller_id, buyer_id)] = framework


def planned_framework_covers(world: World, framework: dict[str, Any], route: dict[str, Any], day: date) -> bool:
    """Darf ein neues Paar an diesem Tag einen Abrufvertrag über diese Route schließen?"""
    if day < framework["start"] or day > framework["planned_end"]:
        return False
    if framework["planned_suspension"] is not None and day >= framework["planned_suspension"]:
        return False
    product = world.products[route["product_id"]]
    system_id = world.stations[route["destination_station_id"]]["system_id"]
    if scope_covers(framework["planned_scope"], product["category_code"], product["archetype_code"], system_id, day):
        return True
    restricted = product["category_code"] in framework["spec"].get("scope_archetypes", {})
    return (product["category_code"] in framework["rule_categories"] and not restricted
            and not scope_closed_for(framework["planned_scope"], product["category_code"],
                                     product["archetype_code"], day))


def framework_text(world: World, framework: dict[str, Any]) -> str:
    """Vertragstext des Rahmenvertrags in der Sprache des Verkäufers."""
    spec, row = framework["spec"], framework["row"]
    language = framework["language"]
    idx = lang_index(language)
    seller = world.companies[framework["seller_id"]]["name"]
    buyer = world.companies[framework["buyer_id"]]["name"]
    scope_parts = []
    for category in spec["scope"]:
        label = CATEGORY_LABELS[category][idx]
        archetypes = spec.get("scope_archetypes", {}).get(category)
        if archetypes:
            names = [getattr(ARCHETYPES_BY_CODE[code], "name_de" if idx == 0 else "name_en") for code in archetypes]
            label = f"{label} ({', '.join(names)})"
        scope_parts.append(label)
    index_category = CATEGORY_LABELS[row["price_index_category"]][idx] if row["price_index_category"] else ""
    index_label = INDEXATION_LABELS[spec["indexation"]][idx].format(category=index_category)
    formula = PRICE_FORMULA_TEXTS[spec["price_formula"]][idx].format(
        index=index_label, cap=fmt_number(spec.get("adjustment_cap_pct", 5), language),
        pct=fmt_number(spec.get("cost_plus_pct", spec.get("base_discount_pct", 0)), language))
    exclusivity = EXCLUSIVITY_LABELS[spec["exclusivity"]][idx]
    excl_items = [CATEGORY_LABELS[c][idx] for c in spec.get("exclusive_categories", ())]
    excl_items += [getattr(ARCHETYPES_BY_CODE[c], "name_de" if idx == 0 else "name_en")
                   for c in spec.get("exclusive_archetypes", ())]
    if excl_items:
        exclusivity += (" für " if idx == 0 else " for ") + ", ".join(excl_items)
    if spec.get("exclusivity_system"):
        system_name = world.systems[spec["exclusivity_system"]]["name"]
        exclusivity += f" (System {system_name})" if idx == 0 else f" ({system_name} system)"
    volume = fmt_number(row["base_volume"], language)
    start = fmt_human_date(framework["start"], language)
    end = fmt_human_date(framework["end"], language)
    if idx == 0:
        text = (f"Rahmenvertrag {row['agreement_number']} zwischen der {seller} (Verkäufer) und der {buyer} "
                f"(Käufer). Gegenstand: {', '.join(scope_parts)}. Laufzeit {spec['term_months']} Monate vom {start} "
                f"bis {end}. Rahmenvolumen {volume} {CURRENCY_CODE}. Preisbildung: {formula}. Exklusivität: "
                f"{exclusivity}. Kündigungsfrist {spec['notice_days']} Tage. Abrufe erfolgen als Einzelverträge "
                f"(Rahmen-, Dauer- und Exklusivlieferverträge) und werden auf das Rahmenvolumen angerechnet.")
        if spec.get("auto_renewal"):
            text += f" Verlängert sich automatisch um {spec.get('renewal_months', DEFAULT_RENEWAL_MONTHS)} Monate."
        if spec.get("price_floor"):
            text += " Mindestpreisklausel: Indexanpassungen nach unten sind auf den Basispreis begrenzt."
        if spec.get("harvest_clause"):
            text += " Ernteklausel: Mindermengen nach Ernteausfällen begründen keinen Vertragsbruch."
        if row["escort_company_id"]:
            text += f" Geleitschutz durch {world.companies[row['escort_company_id']]['name']}."
        return text
    text = (f"Framework agreement {row['agreement_number']} between {seller} (seller) and {buyer} (buyer). "
            f"Scope: {', '.join(scope_parts)}. Term {spec['term_months']} months from {start} to {end}. "
            f"Framework volume {volume} {CURRENCY_CODE}. Pricing: {formula}. Exclusivity: {exclusivity}. Notice "
            f"period {spec['notice_days']} days. Call-offs are placed as individual contracts (framework, recurring "
            f"and exclusive supply contracts) and count against the framework volume.")
    if spec.get("auto_renewal"):
        text += f" Renews automatically for {spec.get('renewal_months', DEFAULT_RENEWAL_MONTHS)} months."
    if spec.get("price_floor"):
        text += " Price floor: downward index adjustments are capped at the base price."
    if spec.get("harvest_clause"):
        text += " Harvest clause: shortfalls after crop failures do not constitute a breach."
    if row["escort_company_id"]:
        text += f" Escort provided by {world.companies[row['escort_company_id']]['name']}."
    return text


def amendment_dates(amendment: dict[str, Any]) -> None:
    """Ergänzt Angebots- und Unterzeichnungsdatum eines Nachtrags (alles bis spätestens 31.12.2059)."""
    effective = amendment["effective_date"]
    last_day = GAME_REFERENCE_DATE - timedelta(days=1)
    explicit = amendment.get("proposed_date")
    if explicit is None:
        explicit = (DEFAULT_PROPOSAL_DATE_2060 if amendment["status"] != "signed" and effective >= GAME_REFERENCE_DATE
                    else effective - timedelta(days=14))
        amendment["proposed_date"] = min(explicit, last_day)
        signed = effective - timedelta(days=3)
    else:
        signed = min(effective, explicit + timedelta(days=7))
    amendment["signed_date"] = min(signed, last_day) if amendment["status"] == "signed" else None


def finalize_framework_agreements(world: World) -> None:
    """Ordnet Einzelverträge den Rahmen zu und leitet die Nachträge ab (letzter Generierungsschritt).

    Regel (deterministisch): gleiches Paar, Vertragstyp framework/recurring_supply/exclusive_supply,
    Beginn zwischen Rahmenbeginn und dem dann gültigen Laufzeitende, Ware am Beginn im Sortiment.
    Feste Nachträge stammen aus FRAMEWORK_BLUEPRINT; Regel-Nachträge entstehen aus den Verträgen:
    erster Abruf einer neuen Kategorie (Aufnahme zum Monatsersten), kumulierte Abrufe über 90 % des
    Volumens (Erhöhung zum Monatsersten des auslösenden Vertrags) und Abrufe nach Laufzeitende
    (Verlängerung, wirksam 60 Tage vor Ablauf). Jeder Nachtrag wirkt vor dem Vertrag, der ihn nutzt.
    """
    contracts_by_pair: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for contract in world.rows["contracts"]:
        contracts_by_pair[(contract["company_id"], contract["partner_company_id"])].append(contract)
    lookups = {
        "contracts": {c["contract_number"]: c["contract_id"] for c in world.rows["contracts"]},
        "orders": {o["order_number"]: o["order_id"] for o in world.rows["orders"]},
        "events": {e["event_id"] for e in world.rows["events"]},
    }
    for framework in sorted(world.frameworks.values(), key=lambda f: f["row"]["framework_agreement_id"]):
        pair = (framework["seller_id"], framework["buyer_id"])
        process_framework(world, framework, sorted(contracts_by_pair[pair],
                                                   key=lambda c: (c["start_date"], c["contract_id"])), lookups)
    assign_framework_signatories(world)


def process_framework(world: World, framework: dict[str, Any], contracts: list[dict[str, Any]],
                      lookups: dict[str, Any]) -> None:
    """Zuordnung, Nachträge und Sortiment eines Rahmenvertrags."""
    spec, row = framework["spec"], framework["row"]
    buyer_id = framework["buyer_id"]
    entries = base_scope_entries(world, spec, framework["start"])
    pending = fixed_amendment_specs(world, framework)
    amendments: list[dict[str, Any]] = []
    granularity = 10_000_000.0 if row["base_volume"] >= 50_000_000.0 else 1_000_000.0
    state: dict[str, Any] = {"cap": row["base_volume"], "end": framework["end"], "suspended": None, "cum": 0.0,
                             "last_volume_effective": framework["start"] - timedelta(days=1),
                             "last_addition": None}
    volume_templates = [a for a in spec["amendments"] if a.get("rule") == "cumulative_over_90pct"]
    extension_templates = [a for a in spec["amendments"] if a.get("rule") == "calloff_after_end"]
    counters = {"volume": 0, "extension": 0}

    def new_amendment(kind: str, effective: date, rule: str | None, contract: dict[str, Any] | None,
                      initiator: int, items: list[tuple[str, str | None]] | None = None,
                      proposed: date | None = None) -> dict[str, Any]:
        amendment = {"spec": {}, "order": len(amendments) + 1000, "amendment_type": kind, "effective_date": effective,
                     "status": "signed" if effective < GAME_REFERENCE_DATE else "proposed",
                     "proposed_date": proposed, "initiated_by_company_id": initiator, "items": items or [],
                     "rule": rule, "exclusive_system_id": None, "escort_company_id": None, "exclusivity": None,
                     "trigger_contract": contract}
        amendments.append(amendment)
        return amendment

    def apply(amendment: dict[str, Any]) -> None:
        kind = amendment["amendment_type"]
        a_spec = amendment["spec"]
        if kind == "price_adjustment" and "pct" in a_spec:
            amendment["price_change_pct"] = a_spec["pct"]
            amendment["price_factor"] = round(1.0 + a_spec["pct"] / 100.0, 4)
        if kind == "term_extension" and a_spec.get("new_end_date"):
            amendment["end_date_new"] = date.fromisoformat(a_spec["new_end_date"])
        if kind in ("volume_increase", "volume_reduction"):
            before = state["cap"]
            if a_spec.get("volume_after_mcr") is not None:
                after = a_spec["volume_after_mcr"] * 1_000_000.0
            else:
                after = before + a_spec.get("delta_mcr", 0) * 1_000_000.0
            if kind == "volume_reduction":
                after = max(after, round_up(state["cum"], granularity))
            amendment["volume_before"], amendment["volume_after"] = before, after
        if amendment["status"] in ("rejected", "withdrawn"):
            return
        if kind in ("volume_increase", "volume_reduction"):
            state["cap"] = amendment["volume_after"]
            state["last_volume_effective"] = amendment["effective_date"]
        elif kind == "term_extension" and amendment.get("end_date_new"):
            state["end"] = max(state["end"], amendment["end_date_new"])
        elif kind == "suspension":
            state["suspended"] = amendment["effective_date"]
        apply_scope_change(world, entries, amendment)

    def apply_due(day: date) -> None:
        while pending and pending[0]["effective_date"] <= day:
            amendment = pending.pop(0)
            amendments.append(amendment)
            apply(amendment)

    for contract in contracts:
        day = date.fromisoformat(contract["start_date"])
        apply_due(day)
        if contract["contract_type"] not in FRAMEWORK_CALLOFF_TYPES or day < framework["start"]:
            continue
        if state["suspended"] is not None and day >= state["suspended"]:
            continue
        while day > state["end"] and counters["extension"] < 3:
            template = (extension_templates[counters["extension"]]
                        if counters["extension"] < len(extension_templates) else None)
            counters["extension"] += 1
            effective = max(framework["start"], state["end"] - timedelta(days=FRAMEWORK_EXTENSION_LEAD_DAYS))
            initiator = world.company_ids_by_key[template["initiated_by"]] if template and template.get(
                "initiated_by") else buyer_id
            amendment = new_amendment("term_extension", effective, "calloff_after_end", contract, initiator)
            amendment["end_date_new"] = framework_extension_end(framework, state["end"], template)
            state["end"] = amendment["end_date_new"]
        if day > state["end"]:
            continue
        product = world.products[contract["product_id"]]
        category, archetype = product["category_code"], product["archetype_code"]
        system_id = world.stations[contract["destination_station_id"]]["system_id"]
        if not scope_covers(entries, category, archetype, system_id, day):
            if (category in spec.get("scope_archetypes", {})
                    or scope_closed_for(entries, category, archetype, day)):
                continue
            effective = max(framework["start"], month_start(day))
            last = state["last_addition"]
            if last is not None and last["effective_date"] == effective:
                last["items"].append((category, None))
                entries.append(scope_entry(category, None, None, effective, amendment=last))
            else:
                last = new_amendment("product_addition", effective, "first_contract_of_category", contract,
                                     buyer_id, [(category, None)])
                state["last_addition"] = last
                apply_scope_change(world, entries, last)
        contract["framework_agreement_id"] = row["framework_agreement_id"]
        if contract["status"] == "cancelled":
            continue
        state["cum"] += contract["total_value"]
        if state["cum"] > FRAMEWORK_VOLUME_THRESHOLD * state["cap"]:
            template = (volume_templates[counters["volume"]]
                        if counters["volume"] < len(volume_templates) else None)
            counters["volume"] += 1
            before = state["cap"]
            preferred = None
            if template is not None and template.get("volume_after_mcr") is not None:
                preferred = template["volume_after_mcr"] * 1_000_000.0
            elif template is not None and template.get("delta_mcr") is not None:
                preferred = before + template["delta_mcr"] * 1_000_000.0
            generic = round_up(max(before * 1.5, state["cum"] / 0.75), granularity)
            after = preferred if preferred is not None and preferred > state["cum"] else generic
            effective = max(month_start(day), framework["start"], state["last_volume_effective"] + timedelta(days=1))
            effective = min(effective, day)
            proposed = (date.fromisoformat(template["proposed"]) if template is not None and template.get("proposed")
                        and effective >= GAME_REFERENCE_DATE else None)
            amendment = new_amendment("volume_increase", effective, "cumulative_over_90pct", contract,
                                      buyer_id, proposed=proposed)
            amendment["volume_before"], amendment["volume_after"] = before, after
            state["cap"], state["last_volume_effective"] = after, effective
    while pending:
        amendment = pending.pop(0)
        amendments.append(amendment)
        apply(amendment)
    write_framework_amendments(world, framework, amendments, entries, lookups)


def write_framework_amendments(world: World, framework: dict[str, Any], amendments: list[dict[str, Any]],
                               entries: list[dict[str, Any]], lookups: dict[str, Any]) -> None:
    """Nummeriert die Nachträge chronologisch, schreibt Nachträge und Sortiment und aktualisiert den Rahmen."""
    row = framework["row"]
    language = framework["language"]
    use_anchors = world.seed == BASELINE_SEED  # Bezüge auf konkrete Bestandsobjekte gelten nur für Seed 42
    for amendment in amendments:
        amendment_dates(amendment)
    ordered = sorted(amendments, key=lambda a: (a["proposed_date"], a["effective_date"], a["order"]))
    for number, amendment in enumerate(ordered, start=1):
        a_spec = amendment["spec"]
        trigger_contract = amendment.get("trigger_contract")
        trigger_contract_id = trigger_contract["contract_id"] if trigger_contract else None
        trigger_order_id = trigger_event_id = None
        anchors: list[str] = []
        if use_anchors and not amendment["rule"]:
            contract_numbers = [n for n in a_spec.get("contracts", ()) if n in lookups["contracts"]]
            order_numbers = [n for n in a_spec.get("orders", ()) if n in lookups["orders"]]
            event_ids = [e for e in a_spec.get("events", ()) if e in lookups["events"]]
            trigger_contract_id = lookups["contracts"][contract_numbers[0]] if contract_numbers else None
            trigger_order_id = lookups["orders"][order_numbers[0]] if order_numbers else None
            trigger_event_id = event_ids[0] if event_ids else None
            anchors = contract_numbers + order_numbers + [
                f"{'Ereignis' if language == 'de_DE' else 'event'} {e}" for e in event_ids]
        items = amendment["items"]
        categories = sorted({c for c, a in items if a is None})
        archetypes = sorted({a for _c, a in items if a is not None})
        volume_before = amendment.get("volume_before")
        volume_after = amendment.get("volume_after")
        record = world.add("framework_agreement_amendments", {
            "framework_agreement_id": row["framework_agreement_id"],
            "amendment_no": number,
            "amendment_number": f"{row['agreement_number']}/{AMENDMENT_PREFIX[language]}{number}",
            "amendment_type": amendment["amendment_type"],
            "status": amendment["status"],
            "rule": amendment["rule"],
            "proposed_date": fmt_date(amendment["proposed_date"]),
            "signed_date": fmt_date(amendment["signed_date"]) if amendment["signed_date"] else None,
            "effective_date": fmt_date(amendment["effective_date"]),
            "initiated_by_company_id": amendment["initiated_by_company_id"],
            "volume_before": round(volume_before, 2) if volume_before is not None else None,
            "volume_delta": round(volume_after - volume_before, 2) if volume_after is not None else None,
            "volume_after": round(volume_after, 2) if volume_after is not None else None,
            "price_change_pct": amendment.get("price_change_pct"),
            "price_factor": amendment.get("price_factor"),
            "end_date_new": fmt_date(amendment["end_date_new"]) if amendment.get("end_date_new") else None,
            "category_code": categories[0] if len(categories) == 1 and not archetypes else None,
            "archetype_code": archetypes[0] if len(archetypes) == 1 and not categories else None,
            "exclusivity": amendment.get("exclusivity"),
            "exclusive_system_id": amendment.get("exclusive_system_id"),
            "escort_company_id": amendment.get("escort_company_id"),
            "trigger_contract_id": trigger_contract_id,
            "trigger_order_id": trigger_order_id,
            "trigger_event_id": trigger_event_id,
            "description": amendment_text(world, framework, amendment, trigger_contract, anchors),
        })
        amendment["amendment_id"] = record["amendment_id"]
    for entry in entries:
        world.add("framework_agreement_scope", {
            "framework_agreement_id": row["framework_agreement_id"],
            "category_code": entry["category_code"],
            "archetype_code": entry["archetype_code"],
            "system_id": entry["system_id"],
            "entry_kind": entry["entry_kind"],
            "exclusivity": entry["exclusivity"],
            "valid_from": fmt_date(entry["valid_from"]),
            "valid_to": fmt_date(entry["valid_to"]) if entry["valid_to"] else None,
            "added_by_amendment_id": entry["added_by"]["amendment_id"] if entry["added_by"] else None,
            "removed_by_amendment_id": entry["removed_by"]["amendment_id"] if entry["removed_by"] else None,
        })
    signed = [a for a in sorted(amendments, key=lambda a: (a["effective_date"], a["proposed_date"]))
              if a["status"] == "signed"]
    volumes = [a["volume_after"] for a in signed if a["amendment_type"] in ("volume_increase", "volume_reduction")]
    ends = [a["end_date_new"] for a in signed if a["amendment_type"] == "term_extension" and a.get("end_date_new")]
    current_end = max([framework["end"], *ends])
    row["current_volume_cap"] = round(volumes[-1], 2) if volumes else row["base_volume"]
    row["current_end_date"] = fmt_date(current_end)
    if any(a["amendment_type"] == "suspension" and a["effective_date"] < GAME_REFERENCE_DATE for a in signed):
        row["status"] = "suspended"
    elif current_end < GAME_REFERENCE_DATE:
        row["status"] = "expired"
    elif framework["start"] > GAME_REFERENCE_DATE:
        row["status"] = "negotiating"
    else:
        row["status"] = "active"


def amendment_text(world: World, framework: dict[str, Any], amendment: dict[str, Any],
                   trigger_contract: dict[str, Any] | None, anchors: list[str]) -> str:
    """Beschreibender Nachtragstext in der Sprache des Verkäufers."""
    language = framework["language"]
    idx = lang_index(language)
    names = []
    for category, archetype in amendment["items"]:
        if archetype is None:
            names.append(CATEGORY_LABELS[category][idx])
        else:
            names.append(getattr(ARCHETYPES_BY_CODE[archetype], "name_de" if idx == 0 else "name_en"))
    joiner = " und " if idx == 0 else " and "
    items = joiner.join([", ".join(names[:-1]), names[-1]]) if len(names) > 1 else (names[0] if names else "")
    if amendment["rule"] and trigger_contract is not None:
        trigger = AMENDMENT_RULE_NOTES[amendment["rule"]][idx].format(contract=trigger_contract["contract_number"])
    elif anchors:
        trigger = AMENDMENT_RULE_NOTES["anchor"][idx].format(contract=", ".join(anchors))
    else:
        trigger = ""
    system_id = amendment.get("exclusive_system_id")
    system_name = world.systems_by_id[system_id]["name"] if system_id else ""
    system_suffix = ((f" im System {system_name}" if idx == 0 else f" in the {system_name} system")
                     if system_name else "")
    station = amendment["spec"].get("station")
    if station and items:
        system_suffix += f" ({station})"
    elif station:
        items = f"die Station {station}" if idx == 0 else f"the station {station}"
    escort_id = amendment.get("escort_company_id")
    pct = amendment.get("price_change_pct")
    return AMENDMENT_TEXTS[amendment["amendment_type"]][idx].format(
        effective=fmt_human_date(amendment["effective_date"], language),
        before=fmt_number(amendment.get("volume_before") or 0, language),
        after=fmt_number(amendment.get("volume_after") or 0, language),
        items=items or ("das gesamte Sortiment" if idx == 0 else "the entire scope"),
        items_suffix=((" für " if idx == 0 else " for ") + items) if items else "",
        pct=fmt_number(pct, language, 1) if pct is not None else "0",
        end=fmt_human_date(amendment["end_date_new"], language) if amendment.get("end_date_new") else "",
        exclusivity=EXCLUSIVITY_LABELS[amendment.get("exclusivity") or "right_of_first_refusal"][idx],
        system_suffix=system_suffix,
        escort=world.companies[escort_id]["name"] if escort_id else "",
        trigger=trigger,
    )


SIGNATORY_ROLE_PRIORITY: dict[str, int] = {"executive": 0, "relations": 1, "finance": 2, "station_manager": 3}


def assign_framework_signatories(world: World) -> None:
    """Unterzeichner je Seite: am Unterzeichnungstag beschäftigt, bevorzugt Vorstand, dann Partnerbetreuung."""
    employees_by_company: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for employee in world.rows["employees"]:
        employees_by_company[employee["company_id"]].append(employee)
    for framework in world.frameworks.values():
        row = framework["row"]
        signed = row["signed_date"]
        for column, company_id in (("seller_signatory_id", framework["seller_id"]),
                                   ("buyer_signatory_id", framework["buyer_id"])):
            candidates = [e for e in employees_by_company[company_id] if e["hire_date"] <= signed
                          and (e["termination_date"] is None or e["termination_date"] > signed)]
            candidates.sort(key=lambda e: (SIGNATORY_ROLE_PRIORITY.get(e["role_code"], 9), e["hire_date"],
                                           e["employee_id"]))
            row[column] = candidates[0]["employee_id"] if candidates else None


# ---------------------------------------------------------------------------
# 6. Handelsrouten (inkl. Marktplanung: wer bietet an, wer fragt nach)
# ---------------------------------------------------------------------------

INTERNAL_DEMAND_WEIGHTS = {0: 0.30, 1: 0.45, 2: 0.25}
PARTNER_DEMAND_WEIGHTS = {
    "small": {0: 0.20, 1: 0.50, 2: 0.30},
    "medium": {0: 0.35, 1: 0.45, 2: 0.20},
    "large": {0: 0.45, 1: 0.40, 2: 0.15},
}
SECOND_SUPPLY_PROBABILITY = {"small": 0.0, "medium": 0.15, "large": 0.35}


def choose_supply_stations(world: World, company_id: int, product: dict[str, Any]) -> list[dict[str, Any]]:
    """Wählt die Stationen, an denen eine Firma ein Produkt erzeugt bzw. anbietet."""
    archetype = ARCHETYPES_BY_CODE[product["archetype_code"]]
    own = [s for s in world.stations_by_company[company_id] if can_trade_at(s, product)]
    candidates = [s for s in own if s["station_type"] in archetype.producers]
    if not candidates:
        candidates = [s for s in own if s["station_type"] in ("trade_hub", "free_port", "smuggler_haven")]
    if not candidates:
        candidates = own[:1]
    size_class = world.companies[company_id]["size_class"]
    count = 2 if len(candidates) >= 2 and world.rng.random() < SECOND_SUPPLY_PROBABILITY[size_class] else 1
    return world.rng.sample(candidates, count)


def demand_anchor_price(world: World, product: dict[str, Any], station: dict[str, Any],
                        supply_ids: Sequence[int]) -> float:
    """Basispreis einer nachfragenden Station: Distanz, Sicherheit, Freischaltstufe und Legalstatus."""
    rng = world.rng
    nearest = min(euclidean_distance(station, world.stations[sid]) for sid in supply_ids)
    price = product["base_price"] * rng.uniform(1.06, 1.20)
    price *= SECURITY_PRICE_PREMIUM[station["security_level"]]
    price *= 1.0 + CATEGORY_DISTANCE_PREMIUM[product["category_code"]] * nearest / 1000.0
    price *= 1.0 + 0.025 * station["unlock_tier"]
    if product["legal_status"] == "illegal":
        price *= rng.uniform(1.35, 1.75)
    elif product["legal_status"] == "restricted":
        price *= 1.08
    return round(price, 2)


def supply_anchor_price(world: World, product: dict[str, Any]) -> float:
    """Basispreis am Erzeugerort: unter dem Listenpreis, aber über den Herstellkosten."""
    price = product["base_price"] * world.rng.uniform(0.84, 0.93)
    return round(max(price, product["base_cost"] * 1.04), 2)


def plan_company_markets(world: World, company_id: int, demand_by_product: dict[int, list[int]]) -> None:
    """Legt für die Waren einer Firma Angebots- und Nachfragestationen fest (aktiver Zufallsstrom)."""
    rng = world.rng
    company = world.companies[company_id]
    buyer_ids = [buyer for (seller, buyer) in world.active_agreements if seller == company_id]
    partner_stations = [s for buyer in buyer_ids for s in world.stations_by_company[buyer]]
    for product in world.products_by_company[company_id]:
        archetype = ARCHETYPES_BY_CODE[product["archetype_code"]]
        supply = choose_supply_stations(world, company_id, product)
        if not product["is_tradeable"]:
            world.market[(supply[0]["station_id"], product["product_id"])] = {"role": "internal"}
            continue
        supply_ids = [s["station_id"] for s in supply]
        world.supply_stations[product["product_id"]] = supply_ids
        for sid in supply_ids:
            world.market[(sid, product["product_id"])] = {"role": "supply"}
        internal = [s for s in world.stations_by_company[company_id]
                    if s["station_id"] not in supply_ids and s["station_type"] in archetype.consumers
                    and can_trade_at(s, product)]
        external = [s for s in partner_stations
                    if s["station_type"] in archetype.consumers and can_trade_at(s, product)]
        chosen = rng.sample(internal, pick_count(rng, len(internal), INTERNAL_DEMAND_WEIGHTS))
        chosen += rng.sample(external, pick_count(rng, len(external),
                                                  PARTNER_DEMAND_WEIGHTS[company["size_class"]]))
        if not chosen and (internal or external):
            chosen = [rng.choice(internal + external)]
        demand_by_product[product["product_id"]].extend(s["station_id"] for s in chosen)


def ensure_agreement_demand(world: World, seller_id: int, buyer_id: int,
                            demand_by_product: dict[int, list[int]]) -> None:
    """Jede gerichtete Vereinbarung braucht genug Routen für Verträge und Bestellungen."""
    rng = world.rng
    buyer_station_ids = {s["station_id"] for s in world.stations_by_company[buyer_id]}

    def partner_pairs() -> int:
        return sum(1 for p in world.products_by_company[seller_id]
                   for sid in demand_by_product.get(p["product_id"], []) if sid in buyer_station_ids)

    candidates = [p for p in world.products_by_company[seller_id] if p["is_tradeable"]]
    rng.shuffle(candidates)
    for product in candidates:
        if partner_pairs() >= MIN_PARTNER_ROUTES_PER_AGREEMENT:
            break
        archetype = ARCHETYPES_BY_CODE[product["archetype_code"]]
        options = [s for s in world.stations_by_company[buyer_id]
                   if s["station_type"] in archetype.consumers and can_trade_at(s, product)
                   and s["station_id"] not in demand_by_product[product["product_id"]]]
        if options:
            demand_by_product[product["product_id"]].append(rng.choice(options)["station_id"])
    if partner_pairs() < 1:
        raise RuntimeError(f"Keine Handelsroute für Vereinbarung {seller_id}->{buyer_id} möglich.")


def plan_markets(world: World) -> dict[int, list[int]]:
    """Legt fest, welche Stationen welche Ware anbieten (supply) bzw. nachfragen (demand).

    Bestandsfirmen: erst alle Firmen, dann alle Vereinbarungen (bisherige Reihenfolge, gemeinsamer
    Strom). Erweiterungsfirmen: je Firma Waren und eigene Vereinbarungen im eigenen Strom.
    """
    demand_by_product: dict[int, list[int]] = defaultdict(list)
    for company_id in world.legacy_company_ids():
        plan_company_markets(world, company_id, demand_by_product)
    for seller_id, buyer_id in world.active_agreements:
        if world.is_legacy(seller_id):
            ensure_agreement_demand(world, seller_id, buyer_id, demand_by_product)
    for company_id in world.extension_company_ids():
        with world.company_stream(world.key_of(company_id), "markets"):
            plan_company_markets(world, company_id, demand_by_product)
            for seller_id, buyer_id in world.active_agreements:
                if seller_id == company_id:
                    ensure_agreement_demand(world, seller_id, buyer_id, demand_by_product)
    return demand_by_product


def build_product_routes(world: World, product_id: int, demand_ids: list[int]) -> None:
    """Erzeugt die Routen einer Ware von ihren Erzeuger- zu den Verbraucherstationen (aktiver Strom)."""
    rng = world.rng
    product = world.products[product_id]
    company_id = product["company_id"]
    size = SIZE_PROFILES[world.companies[company_id]["size_class"]]
    supply_ids = world.supply_stations[product_id]
    for sid in supply_ids:
        world.market[(sid, product_id)]["price"] = supply_anchor_price(world, product)
    for demand_id in demand_ids:
        destination = world.stations[demand_id]
        world.market[(demand_id, product_id)] = {
            "role": "demand", "price": demand_anchor_price(world, product, destination, supply_ids)}
        ordered = sorted(supply_ids, key=lambda sid: euclidean_distance(world.stations[sid], destination))
        origins = ordered[:1] + [sid for sid in ordered[1:] if rng.random() < 0.35]
        for origin_id in origins:
            origin = world.stations[origin_id]
            distance = euclidean_distance(origin, destination)
            price_origin = world.market[(origin_id, product_id)]["price"]
            price_destination = world.market[(demand_id, product_id)]["price"]
            by_volume = size.hold_capacity_m3 * rng.uniform(0.2, 0.5) / product["volume_m3"]
            by_value = size.max_haul_value * rng.uniform(0.3, 1.0) / price_origin
            typical = round_quantity(min(by_volume, by_value))
            risk = route_risk_level(origin, destination, distance, product["legal_status"])
            haul_fuel = fuel_cost(distance, typical * product["mass_kg"], typical * product["volume_m3"],
                                  size.hold_capacity_m3)
            insurance_rate = INSURANCE_RATE[risk] + (ILLEGAL_INSURANCE_SURCHARGE
                                                     if product["legal_status"] == "illegal" else 0.0)
            transport_per_unit = round((haul_fuel + typical * price_origin * insurance_rate) / typical, 2)
            profit = round(price_destination - price_origin, 2)
            route = world.add("trade_routes", {
                "origin_station_id": origin_id,
                "destination_station_id": demand_id,
                "product_id": product_id,
                "company_id": company_id,
                "typical_quantity": typical,
                "base_price_origin": price_origin,
                "base_price_destination": price_destination,
                "estimated_profit_per_unit": profit,
                "travel_time_hours": travel_time_hours(distance),
                "risk_level": risk,
                "is_active": 0 if rng.random() < 0.06 else 1,
                "distance_units": round(distance, 2),
                "transport_cost_per_unit": transport_per_unit,
                "net_profit_per_unit": round(profit - transport_per_unit, 2),
                "route_scope": "internal" if destination["company_id"] == company_id else "partner",
            })
            world.routes_by_pair[(origin_id, demand_id)].append(route)


def generate_trade_routes(world: World) -> None:
    """Erzeugt Handelsrouten von Erzeuger- zu Verbraucherstationen inklusive Preisanker und Risiko."""
    demand_by_product = plan_markets(world)
    for product_id, demand_ids in demand_by_product.items():
        if world.is_legacy(world.products[product_id]["company_id"]):
            build_product_routes(world, product_id, demand_ids)
    for company_id in world.extension_company_ids():
        with world.company_stream(world.key_of(company_id), "routes"):
            for product_id, demand_ids in demand_by_product.items():
                if world.products[product_id]["company_id"] == company_id:
                    build_product_routes(world, product_id, demand_ids)
    ensure_active_partner_routes(world)


def ensure_active_partner_routes(world: World) -> None:
    """Stellt sicher, dass jede Vereinbarung mindestens zwei aktive Partnerrouten hat."""
    for seller_id, buyer_id in world.active_agreements:
        routes = [r for r in world.rows["trade_routes"] if r["company_id"] == seller_id
                  and world.stations[r["destination_station_id"]]["company_id"] == buyer_id]
        active = [r for r in routes if r["is_active"]]
        for route in [r for r in routes if not r["is_active"]][: max(0, 2 - len(active))]:
            route["is_active"] = 1


# ---------------------------------------------------------------------------
# 7. Lager
# ---------------------------------------------------------------------------


def generate_inventory(world: World) -> None:
    """Erzeugt Lagerbestände passend zu Marktrolle und typischen Routenmengen.

    Bestandsware (Ware einer Bestandsfirma) zuerst und im gemeinsamen Strom, danach die Ware jeder
    Erweiterungsfirma in deren Strom – auch wenn sie an einer Bestandsstation nachgefragt wird.
    """
    outgoing: dict[tuple[int, int], int] = defaultdict(int)
    incoming: dict[tuple[int, int], int] = defaultdict(int)
    for route in world.rows["trade_routes"]:
        outgoing[(route["origin_station_id"], route["product_id"])] += route["typical_quantity"]
        incoming[(route["destination_station_id"], route["product_id"])] += route["typical_quantity"]
    entries = sorted(world.market.items())
    owner = {key: world.products[key[1]]["company_id"] for key, _market in entries}
    add_inventory_rows(world, [(key, market) for key, market in entries if world.is_legacy(owner[key])],
                       outgoing, incoming)
    for company_id in world.extension_company_ids():
        with world.company_stream(world.key_of(company_id), "inventory"):
            add_inventory_rows(world, [(key, market) for key, market in entries if owner[key] == company_id],
                               outgoing, incoming)


def add_inventory_rows(world: World, entries: list[tuple[tuple[int, int], dict[str, Any]]],
                       outgoing: dict[tuple[int, int], int], incoming: dict[tuple[int, int], int]) -> None:
    """Lagerzeilen für die übergebenen Station-Ware-Kombinationen (aktiver Zufallsstrom)."""
    rng = world.rng
    for (station_id, product_id), market in entries:
        product = world.products[product_id]
        role = market["role"]
        if role == "supply":
            base = max(outgoing[(station_id, product_id)], 10)
            restock_target = max(20, round_quantity(base * rng.uniform(1.5, 3.0)))
            quantity = int(restock_target * rng.uniform(0.55, 1.25))
            price = market["price"]
        elif role == "demand":
            base = max(incoming[(station_id, product_id)], 5)
            restock_target = max(10, round_quantity(base * rng.uniform(0.6, 1.4)))
            quantity = int(restock_target * rng.uniform(0.05, 0.75))
            price = market["price"]
        else:  # internal: nicht handelbare Prototypen
            restock_target = rng.randint(2, 40)
            quantity = rng.randint(0, restock_target)
            price = product["base_price"]
        row = world.add("inventory", {
            "station_id": station_id,
            "product_id": product_id,
            "quantity": quantity,
            "reserved_quantity": 0,  # wird nach den Bestellungen gebucht
            "restock_target": restock_target,
            "last_updated": fmt_dt(GAME_REFERENCE_DATETIME),
            "market_role": role,
            "local_base_price": price,
        })
        world.inventory[(station_id, product_id)] = row


# ---------------------------------------------------------------------------
# 8. Verträge
# ---------------------------------------------------------------------------


def partner_routes_of(world: World, seller_id: int, buyer_id: int | None = None) -> list[dict[str, Any]]:
    """Aktive Partnerrouten eines Verkäufers (optional zu einem bestimmten Käufer)."""
    return [r for r in world.rows["trade_routes"]
            if r["company_id"] == seller_id and r["is_active"] and r["route_scope"] == "partner"
            and (buyer_id is None or world.stations[r["destination_station_id"]]["company_id"] == buyer_id)]


def contract_description(world: World, company_id: int, contract_type: str, route: dict[str, Any],
                         quantity: int, price: float, penalty: float, deadline: date) -> str:
    """Lokalisierter Vertragstext."""
    language = world.language(company_id)
    idx = lang_index(language)
    product = world.products[route["product_id"]]
    origin = world.stations[route["origin_station_id"]]["name"]
    destination = world.stations[route["destination_station_id"]]["name"]
    label = CONTRACT_TYPES[contract_type]["label"][idx]
    if language == "de_DE":
        return (f"{label} über {fmt_number(quantity, language)} × {product['name']} ({product['unit']}), "
                f"Lieferung frei {destination} ab {origin} bis {fmt_human_date(deadline, language)}. "
                f"Vereinbarter Preis {fmt_number(price, language, 2)} {CURRENCY_CODE} je {product['unit']}, "
                f"Vertragsstrafe {fmt_number(penalty, language, 2)} {CURRENCY_CODE} pro Verzugstag.")
    return (f"{label} for {fmt_number(quantity, language)} × {product['name']} ({product['unit']}), delivered to "
            f"{destination} from {origin} by {fmt_human_date(deadline, language)}. Agreed price "
            f"{fmt_number(price, language, 2)} {CURRENCY_CODE} per {product['unit']}, penalty "
            f"{fmt_number(penalty, language, 2)} {CURRENCY_CODE} per day of delay.")


def plan_calloffs(world: World, start: datetime, duration_days: int, travel_hours: float, count: int,
                  typical_quantity: int) -> list[dict[str, Any]]:
    """Plant Abrufbestellungen gleichmäßig über die Vertragslaufzeit, sodass jede Lieferung rechtzeitig ankommt."""
    rng = world.rng
    usable_days = max(duration_days - travel_hours / 24.0 - 5.0, float(count))
    calloffs = []
    for index in range(count):
        offset_days = usable_days * (index + rng.uniform(0.15, 0.85)) / count
        calloffs.append({
            "order_dt": (start + timedelta(days=offset_days, hours=rng.uniform(0, 8))).replace(second=0, microsecond=0),
            "quantity": max(1, round_quantity(typical_quantity * rng.uniform(0.4, 1.0))),
        })
    return calloffs


def schedule_breached_calloff(plan: dict[str, Any], travel_hours: float, rng: random.Random) -> None:
    """Legt den letzten Abruf eines gebrochenen Vertrags knapp vor die Frist (geringe, realistische Verspätung)."""
    last = plan["calloffs"][-1]
    previous = plan["calloffs"][-2]["order_dt"] if len(plan["calloffs"]) > 1 else plan["start"]
    latest_possible = plan["deadline"] - timedelta(hours=travel_hours + rng.uniform(30, 96))
    last["order_dt"] = max(previous + timedelta(hours=1), latest_possible).replace(second=0, microsecond=0)


def materialized_calloffs(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Abrufe, die bis zum Stichtag tatsächlich zu Bestellungen geworden sind."""
    status = plan["status"]
    if status == "draft":
        return []
    if status in ("completed", "breached"):
        return plan["calloffs"]
    if status == "cancelled":
        return [c for c in plan["calloffs"] if c["order_dt"] < plan["cancelled_at"]]
    return [c for c in plan["calloffs"] if c["order_dt"] < GAME_REFERENCE_DATETIME]


def contract_status(rng: random.Random, start: datetime, deadline: datetime) -> str:
    """Vertragsstatus aus Lage von Beginn und Frist zum Stichtag."""
    if start > GAME_REFERENCE_DATETIME:
        return "draft"
    if deadline < GAME_REFERENCE_DATETIME:
        return weighted_choice(rng, {"completed": 0.80, "breached": 0.12, "cancelled": 0.08})
    return "cancelled" if rng.random() < 0.07 else "active"


def finish_contract_plan(world: World, plan: dict[str, Any], duration: int, count: int) -> dict[str, Any]:
    """Ergänzt einen Vertragsplan um Abrufe, Storno- und Bruchtermine (aktiver Zufallsstrom)."""
    rng = world.rng
    route = plan["route"]
    plan["calloffs"] = plan_calloffs(world, plan["start"], duration, route["travel_time_hours"], count,
                                     route["typical_quantity"])
    if plan["status"] == "cancelled":
        plan["cancelled_at"] = random_datetime(rng, plan["start"], min(plan["deadline"], GAME_REFERENCE_DATETIME))
    if plan["status"] == "breached":
        schedule_breached_calloff(plan, route["travel_time_hours"], rng)
    return plan


def plan_legacy_contracts(world: World, company_id: int, buyers: list[int],
                          routes_by_buyer: dict[int, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Vertragspläne einer Bestandsfirma – unveränderte Zufallsfolge wie vor der Erweiterung."""
    rng = world.rng
    window_start = to_datetime(world.window_start(company_id))
    plans: list[dict[str, Any]] = []
    for _ in range(world.targets[company_id]["contracts"]):
        buyer_id = rng.choice(buyers)
        route = rng.choice(routes_by_buyer[buyer_id])
        agreement = world.active_agreements[(company_id, buyer_id)]
        type_weights = CONTRACT_TYPE_WEIGHTS_BY_AGREEMENT.get(agreement["relationship_type"],
                                                              DEFAULT_CONTRACT_TYPE_WEIGHTS)
        contract_type = weighted_choice(rng, type_weights)
        spec = CONTRACT_TYPES[contract_type]
        count = rng.randint(*spec["calloffs"])
        travel_days = route["travel_time_hours"] / 24.0
        duration = max(rng.randint(*spec["days"]), int(math.ceil(count * 7 + travel_days + 6)))
        if rng.random() < 0.06:
            start = random_datetime(rng, GAME_REFERENCE_DATETIME + timedelta(days=5),
                                    GAME_REFERENCE_DATETIME + timedelta(days=75))
        else:
            start = random_datetime(rng, window_start, GAME_REFERENCE_DATETIME - timedelta(days=5))
        deadline = start + timedelta(days=duration)
        plan = {"route": route, "buyer_id": buyer_id, "contract_type": contract_type, "start": start,
                "deadline": deadline, "status": contract_status(rng, start, deadline)}
        plans.append(finish_contract_plan(world, plan, duration, count))
    return plans


def plan_extension_contracts(world: World, company_id: int, buyers: list[int],
                             routes_by_buyer: dict[int, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Vertragspläne einer Erweiterungsfirma mit Rahmenregel und Exklusivitätssperren.

    Vor Rahmenbeginn (und außerhalb von Laufzeit oder Sortiment eines Rahmens) schließt das Paar nur
    Spot-, Not- und Kommissionsverträge; danach gelten die bisherigen Gewichte. Gesperrte Ware
    (EXCLUSIVITY_FILTERS) wird gar nicht erst vertraglich gebunden.
    """
    rng = world.rng
    window_start = to_datetime(world.window_start(company_id))
    plans: list[dict[str, Any]] = []
    for _ in range(world.targets[company_id]["contracts"]):
        for _attempt in range(200):
            buyer_id = rng.choice(buyers)
            route = rng.choice(routes_by_buyer[buyer_id])
            if rng.random() < 0.06:
                start = random_datetime(rng, GAME_REFERENCE_DATETIME + timedelta(days=5),
                                        GAME_REFERENCE_DATETIME + timedelta(days=75))
            else:
                start = random_datetime(rng, window_start, GAME_REFERENCE_DATETIME - timedelta(days=5))
            if not exclusivity_blocks(world, company_id, buyer_id, world.products[route["product_id"]],
                                      world.stations[route["destination_station_id"]], start.date()):
                break
        else:
            raise RuntimeError(f"Keine zulässige Vertragsware für Firma {company_id} gefunden.")
        agreement = world.active_agreements[(company_id, buyer_id)]
        type_weights = dict(CONTRACT_TYPE_WEIGHTS_BY_AGREEMENT.get(agreement["relationship_type"],
                                                                   DEFAULT_CONTRACT_TYPE_WEIGHTS))
        framework = world.frameworks.get((company_id, buyer_id))
        if framework is not None and not planned_framework_covers(world, framework, route, start.date()):
            type_weights = {code: weight for code, weight in type_weights.items()
                            if code in OUTSIDE_FRAMEWORK_CONTRACT_TYPES} or {"spot": 1.0}
        contract_type = weighted_choice(rng, type_weights)
        spec = CONTRACT_TYPES[contract_type]
        count = rng.randint(*spec["calloffs"])
        travel_days = route["travel_time_hours"] / 24.0
        duration = max(rng.randint(*spec["days"]), int(math.ceil(count * 7 + travel_days + 6)))
        deadline = start + timedelta(days=duration)
        plan = {"route": route, "buyer_id": buyer_id, "contract_type": contract_type, "start": start,
                "deadline": deadline, "status": contract_status(rng, start, deadline)}
        plans.append(finish_contract_plan(world, plan, duration, count))
    return plans


def generate_company_contracts(world: World, company_id: int) -> None:
    """Verträge einer Firma im aktiven Zufallsstrom samt Abrufplanung."""
    rng = world.rng
    company = world.companies[company_id]
    language = company["language"]
    profile = world.profiles[company_id]
    buyers = [buyer for (seller, buyer) in world.active_agreements if seller == company_id]
    routes_by_buyer = {buyer: partner_routes_of(world, company_id, buyer) for buyer in buyers}
    buyers = [buyer for buyer in buyers if routes_by_buyer[buyer]]
    if world.is_legacy(company_id):
        plans = plan_legacy_contracts(world, company_id, buyers, routes_by_buyer)
    else:
        plans = plan_extension_contracts(world, company_id, buyers, routes_by_buyer)

    # Abrufbestellungen dürfen höchstens 55 % des Bestellvolumens ausmachen.
    budget = int(world.targets[company_id]["orders"] * 0.55)
    while sum(len(materialized_calloffs(p)) for p in plans) > budget:
        reducible = [p for p in plans if len(materialized_calloffs(p)) > 1]
        if not reducible:
            break
        victim = rng.choice(reducible)
        victim["calloffs"].remove(materialized_calloffs(victim)[-1])
        if victim["status"] == "breached":
            schedule_breached_calloff(victim, victim["route"]["travel_time_hours"], rng)

    for sequence, plan in enumerate(sorted(plans, key=lambda p: p["start"]), start=1):
        route = plan["route"]
        product = world.products[route["product_id"]]
        quantity = sum(c["quantity"] for c in plan["calloffs"])
        price = route["base_price_destination"] * rng.uniform(0.86, 0.97)
        price = round(max(price, route["base_price_origin"] * 1.03, product["base_cost"] * 1.05), 2)
        total_value = round(quantity * price, 2)
        penalty = round(total_value * rng.uniform(0.002, 0.01), 2)
        row = world.add("contracts", {
            "contract_number": f"{profile.sku_prefix}-{CONTRACT_PREFIX[language]}-{plan['start'].year}-{sequence:04d}",
            "company_id": company_id,
            "partner_company_id": plan["buyer_id"],
            "origin_station_id": route["origin_station_id"],
            "destination_station_id": route["destination_station_id"],
            "product_id": route["product_id"],
            "route_id": route["route_id"],
            "contract_type": plan["contract_type"],
            "quantity": quantity,
            "agreed_price_per_unit": price,
            "total_value": total_value,
            "start_date": fmt_date(plan["start"]),
            "deadline": fmt_date(plan["deadline"]),
            "status": plan["status"],
            "penalty_per_day": penalty,
            "description": contract_description(world, company_id, plan["contract_type"], route, quantity,
                                                price, penalty, plan["deadline"].date()),
            "framework_agreement_id": None,  # Zuordnung im letzten Schritt (Rahmenverträge)
        })
        world.contract_plans[row["contract_id"]] = plan


def generate_contracts(world: World) -> None:
    """Erzeugt Verträge entlang aktiver Vereinbarungen und plant deren Abrufbestellungen."""
    for company_id in world.companies:
        with world.company_stream(world.key_of(company_id), "contracts"):
            generate_company_contracts(world, company_id)

    # Vertragsvolumen der Partnerschaften = Summe der (nicht stornierten) Verträge in dieser Richtung
    volumes: dict[tuple[int, int], float] = defaultdict(float)
    for contract in world.rows["contracts"]:
        if contract["status"] != "cancelled":
            volumes[(contract["company_id"], contract["partner_company_id"])] += contract["total_value"]
    for key, agreement in world.active_agreements.items():
        agreement["contract_volume"] = round(volumes[key], 2)


# ---------------------------------------------------------------------------
# 9. Kunden, Bestellungen und Bestellpositionen
# ---------------------------------------------------------------------------


def generate_customers(world: World) -> None:
    """Erzeugt Kundenkonten: Partnerfirmen und fiktive Kolonien, Händler und Stationsbetreiber."""
    for company_id in world.companies:
        with world.company_stream(world.key_of(company_id), "customers"):
            generate_company_customers(world, company_id)


def generate_company_customers(world: World, company_id: int) -> None:
    """Kundenkonten einer Firma im aktiven Zufallsstrom."""
    rng = world.rng
    company = world.companies[company_id]
    language = company["language"]
    fake = world.fake(company_id)
    size = SIZE_PROFILES[company["size_class"]]
    used_names: set[str] = set()
    window_start = world.window_start(company_id)
    active_routes = [r for r in world.rows["trade_routes"] if r["company_id"] == company_id and r["is_active"]]

    for (seller_id, buyer_id), agreement in world.active_agreements.items():
        if seller_id != company_id:
            continue
        buyer_routes = [r for r in active_routes
                        if world.stations[r["destination_station_id"]]["company_id"] == buyer_id]
        if not buyer_routes:
            continue
        home = max({r["destination_station_id"] for r in buyer_routes},
                   key=lambda sid: sum(1 for r in buyer_routes if r["destination_station_id"] == sid))
        name = world.companies[buyer_id]["name"]
        used_names.add(name)
        row = world.add("customers", {
            "company_id": company_id, "linked_company_id": buyer_id, "name": name,
            "customer_type": "corporate_partner", "home_station_id": home,
            "contact_name": person_name(world.fake(buyer_id)),
            "credit_limit": round(rng.uniform(*CUSTOMER_CREDIT_LIMIT["corporate_partner"]) * size.storage_factor, -3),
            "since_date": agreement["start_date"], "is_active": 1,
        })
        world.customers_by_company[company_id].append(row)

    destination_weights: dict[int, float] = defaultdict(float)
    for route in active_routes:
        destination_weights[route["destination_station_id"]] += 1.0
    npc_count = world.targets[company_id]["customers"] - len(world.customers_by_company[company_id])
    for _ in range(npc_count):
        home_id = weighted_choice(rng, destination_weights)
        customer_type = rng.choice(CUSTOMER_TYPE_BY_STATION[world.stations[home_id]["station_type"]])
        template = CUSTOMER_NAME_TEMPLATES[language][customer_type]
        name = template.format(first=fake.first_name(), last=fake.last_name())
        while name in used_names:
            name = template.format(first=fake.first_name(), last=fake.last_name())
        used_names.add(name)
        since = random_date(rng, window_start - timedelta(days=5 * 365), GAME_REFERENCE_DATE - timedelta(days=60))
        row = world.add("customers", {
            "company_id": company_id, "linked_company_id": None, "name": name,
            "customer_type": customer_type, "home_station_id": home_id, "contact_name": person_name(fake),
            "credit_limit": round(rng.uniform(*CUSTOMER_CREDIT_LIMIT[customer_type]), -3),
            "since_date": fmt_date(since), "is_active": 0 if rng.random() < 0.05 else 1,
        })
        world.customers_by_company[company_id].append(row)


def simulate_order_timeline(rng: random.Random, order_dt: datetime, travel_hours: float, risk: str,
                            language: str, *, allow_cancel: bool, allow_delay: bool,
                            force_late_after: datetime | None = None,
                            illegal_cargo: bool = False) -> dict[str, Any]:
    """Simuliert Bestätigung, Abflug, Ankunft, Verzögerungen und leitet Bestell-/Zahlungsstatus ab."""
    now = GAME_REFERENCE_DATETIME
    confirmed_at = order_dt + timedelta(hours=rng.uniform(2, 36))
    departure = (confirmed_at + timedelta(hours=rng.uniform(12, 72))).replace(second=0, microsecond=0)
    expected_arrival = departure + timedelta(hours=travel_hours)
    required = (expected_arrival + timedelta(days=rng.uniform(1, 5))).date()
    timeline: dict[str, Any] = {
        "order_dt": order_dt, "departure": departure, "expected_arrival": expected_arrival,
        "actual_arrival": expected_arrival, "required_delivery_date": required, "incident": None,
        "delay_hours": 0.0,
    }
    if allow_cancel and rng.random() < 0.04:
        cancelled_at = random_datetime(rng, order_dt, departure)
        if cancelled_at <= now:
            timeline.update(status="cancelled", payment="refunded" if rng.random() < 0.3 else "void")
            return timeline

    delay_hours = 0.0
    if allow_delay and rng.random() < DELAY_PROBABILITY[risk]:
        delay_hours = travel_hours * rng.uniform(0.15, 0.8) + rng.uniform(6, 48)
    if force_late_after is not None:
        minimum = (force_late_after - expected_arrival).total_seconds() / 3600.0 + rng.uniform(24, 144)
        delay_hours = max(delay_hours, minimum)
    incident_moment = departure + timedelta(hours=travel_hours * 0.3)
    if delay_hours > 0 and (incident_moment <= now or force_late_after is not None):
        cause = ILLEGAL_INCIDENT if illegal_cargo and rng.random() < 0.5 else rng.choice(INCIDENT_CAUSES)
        timeline["incident"] = f"{cause[lang_index(language)]} (+{delay_hours:.0f} h)"
        timeline["delay_hours"] = delay_hours
        timeline["actual_arrival"] = (expected_arrival + timedelta(hours=delay_hours)).replace(second=0,
                                                                                                microsecond=0)

    if now < confirmed_at:
        status, payment = "pending", "unpaid"
    elif now < departure:
        status, payment = "confirmed", ("unpaid" if rng.random() < 0.3 else "invoiced")
    elif now < timeline["actual_arrival"]:
        status = "delayed" if timeline["incident"] else "in_transit"
        payment = "partially_paid" if rng.random() < 0.4 else "invoiced"
    else:
        status = "delivered"
        due = timeline["actual_arrival"] + timedelta(days=PAYMENT_TERMS_DAYS)
        if now < due:
            payment = "paid" if rng.random() < 0.55 else "invoiced"
        else:
            payment = "paid" if rng.random() < 0.96 else "overdue"
    timeline.update(status=status, payment=payment)
    return timeline


def build_order(world: World, company_id: int, customer: dict[str, Any], lines: list[tuple[dict[str, Any], int, float]],
                order_dt: datetime, sequence: int, *, contract: dict[str, Any] | None = None,
                calloff_index: int = 0, calloff_total: int = 0, force_late_after: datetime | None = None,
                allow_cancel: bool = True, allow_delay: bool = True) -> None:
    """Legt eine Bestellung mit Positionen an; Fracht/Versicherung/Gebühren werden ausgewiesen."""
    rng = world.rng
    language = world.language(company_id)
    profile = world.profiles[company_id]
    first_route = lines[0][0]
    origin_id = first_route["origin_station_id"]
    destination_id = first_route["destination_station_id"]
    distance = first_route["distance_units"]
    risk = max_risk(route["risk_level"] for route, _q, _p in lines)
    illegal = any(world.products[route["product_id"]]["legal_status"] == "illegal" for route, _q, _p in lines)

    item_rows = []
    cargo_mass = 0.0
    cargo_volume = 0.0
    for route, quantity, unit_price in lines:
        product = world.products[route["product_id"]]
        cargo_mass += quantity * product["mass_kg"]
        cargo_volume += quantity * product["volume_m3"]
        item_rows.append({"product_id": product["product_id"], "quantity": quantity, "unit_price": unit_price,
                          "line_total": round(quantity * unit_price, 2)})
    subtotal = round(sum(item["line_total"] for item in item_rows), 2)
    hold_capacity = SIZE_PROFILES[world.companies[company_id]["size_class"]].hold_capacity_m3
    actual_fuel = fuel_cost(distance, cargo_mass, cargo_volume, hold_capacity)
    insurance_rate = INSURANCE_RATE[risk] + (ILLEGAL_INSURANCE_SURCHARGE if illegal else 0.0)
    actual_insurance = round(subtotal * insurance_rate, 2)
    if contract is not None:  # Vertragspreise verstehen sich frei Bestimmungsort
        freight, insurance, handling = 0.0, 0.0, 0.0
    else:
        freight = round(actual_fuel * rng.uniform(1.15, 1.35), 2)
        insurance = round(actual_insurance * rng.uniform(1.0, 1.1), 2)
        handling = round(min(2500.0, 120.0 + subtotal * 0.004), 2)

    timeline = simulate_order_timeline(rng, order_dt, first_route["travel_time_hours"], risk, language,
                                       allow_cancel=allow_cancel, allow_delay=allow_delay,
                                       force_late_after=force_late_after, illegal_cargo=illegal)
    if contract is not None:
        note = CALLOFF_NOTE[language].format(index=calloff_index, total=calloff_total,
                                             number=contract["contract_number"])
    elif rng.random() < 0.4:
        note = rng.choice(ORDER_NOTES[language]).format(dock=rng.randint(1, 24))
    else:
        note = None
    order = world.add("orders", {
        "order_number": f"{profile.sku_prefix}-{ORDER_PREFIX[language]}-{order_dt.year}-{sequence:05d}",
        "company_id": company_id,
        "customer_company_id": customer["linked_company_id"],
        "customer_id": customer["customer_id"],
        "customer_name": customer["name"],
        "contract_id": contract["contract_id"] if contract else None,
        "origin_station_id": origin_id,
        "destination_station_id": destination_id,
        "order_date": fmt_dt(order_dt),
        "required_delivery_date": fmt_date(timeline["required_delivery_date"]),
        "status": timeline["status"],
        "payment_status": timeline["payment"],
        "subtotal": subtotal,
        "freight_cost": freight,
        "insurance_cost": insurance,
        "handling_fee": handling,
        "total_amount": round(subtotal + freight + insurance + handling, 2),
        "currency": CURRENCY_CODE,
        "notes": note,
    })
    for item in item_rows:
        world.add("order_items", {"order_id": order["order_id"], **item})
    timeline.update(cargo_mass=round(cargo_mass, 3), cargo_volume=round(cargo_volume, 4),
                    fuel_cost=actual_fuel, insurance_cost=actual_insurance, route_ids=[r["route_id"] for r, _q, _p in lines])
    world.order_timelines[order["order_id"]] = timeline


def spot_unit_price(world: World, route: dict[str, Any], is_partner: bool) -> float:
    """Marktnaher Stückpreis für Spot-Bestellungen (Partner erhalten Rabatt)."""
    product = world.products[route["product_id"]]
    price = route["base_price_destination"] * world.rng.uniform(0.94, 1.06) * (0.96 if is_partner else 1.0)
    return round(max(price, product["base_cost"] * 1.02), 2)


def generate_orders(world: World) -> None:
    """Erzeugt Vertragsabrufe und Spot-Bestellungen entlang aktiver Routen."""
    generate_customers(world)
    contracts_by_company: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for contract in world.rows["contracts"]:
        contracts_by_company[contract["company_id"]].append(contract)
    routes_by_id = {r["route_id"]: r for r in world.rows["trade_routes"]}
    for company_id in world.companies:
        with world.company_stream(world.key_of(company_id), "orders"):
            generate_company_orders(world, company_id, contracts_by_company[company_id], routes_by_id)
    book_inventory_reservations(world)
    finalize_station_capacity(world)


def generate_company_orders(world: World, company_id: int, contracts: list[dict[str, Any]],
                            routes_by_id: dict[int, dict[str, Any]]) -> None:
    """Abrufe und Spot-Bestellungen einer Firma im aktiven Zufallsstrom.

    Erweiterungsfirmen beachten die Exklusivitätssperren: gesperrte Positionen werden neu gezogen.
    """
    rng = world.rng
    legacy = world.is_legacy(company_id)
    pending_orders: list[dict[str, Any]] = []
    partner_customers = {c["linked_company_id"]: c for c in world.customers_by_company[company_id]
                         if c["linked_company_id"] is not None}
    for contract in contracts:
        plan = world.contract_plans[contract["contract_id"]]
        done = materialized_calloffs(plan)
        for index, calloff in enumerate(done, start=1):
            late = plan["deadline"] if plan["status"] == "breached" and index == len(done) else None
            pending_orders.append({
                "order_dt": calloff["order_dt"], "customer": partner_customers[contract["partner_company_id"]],
                "lines": [(routes_by_id[contract["route_id"]], calloff["quantity"],
                           contract["agreed_price_per_unit"])],
                "contract": contract, "calloff_index": index, "calloff_total": len(plan["calloffs"]),
                "force_late_after": late, "allow_cancel": False,
                "allow_delay": plan["status"] not in ("completed", "breached"),
            })

    active_routes = [r for r in world.rows["trade_routes"] if r["company_id"] == company_id and r["is_active"]]
    pairs: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for route in active_routes:
        pairs[(route["origin_station_id"], route["destination_station_id"])].append(route)
    pairs_into: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for pair in pairs:
        pairs_into[pair[1]].append(pair)
    npc_customers = [c for c in world.customers_by_company[company_id]
                     if c["linked_company_id"] is None and pairs_into[c["home_station_id"]]]
    window_start = to_datetime(world.window_start(company_id))
    size = SIZE_PROFILES[world.companies[company_id]["size_class"]]

    def draw_spot_order() -> dict[str, Any]:
        if partner_customers and rng.random() < 0.3:
            customer = rng.choice(list(partner_customers.values()))
            buyer_stations = {s["station_id"] for s in world.stations_by_company[customer["linked_company_id"]]}
            candidate_pairs = [pair for pair in pairs if pair[1] in buyer_stations]
        else:
            customer = rng.choice(npc_customers)
            candidate_pairs = pairs_into[customer["home_station_id"]]
        pair = rng.choice(candidate_pairs)
        routes = pairs[pair]
        line_count = pick_count(rng, len(routes), {1: 0.45, 2: 0.30, 3: 0.15, 4: 0.10})
        is_partner = customer["linked_company_id"] is not None
        lines = [(route, max(1, round_quantity(route["typical_quantity"] * rng.uniform(*size.order_share))),
                  spot_unit_price(world, route, is_partner))
                 for route in rng.sample(routes, line_count)]
        earliest = max(window_start, to_datetime(date.fromisoformat(customer["since_date"])))
        if rng.random() < 0.07:
            earliest = max(earliest, GAME_REFERENCE_DATETIME - timedelta(days=21))
        order_dt = random_datetime(rng, earliest, GAME_REFERENCE_DATETIME - timedelta(hours=1))
        return {"order_dt": order_dt, "customer": customer, "lines": lines, "contract": None,
                "calloff_index": 0, "calloff_total": 0, "force_late_after": None,
                "allow_cancel": True, "allow_delay": True}

    spot_count = max(0, world.targets[company_id]["orders"] - len(pending_orders))
    for _ in range(spot_count):
        spec = draw_spot_order()
        if not legacy:
            for _attempt in range(100):
                buyer_id = spec["customer"]["linked_company_id"]
                allowed = [line for line in spec["lines"] if not exclusivity_blocks(
                    world, company_id, buyer_id, world.products[line[0]["product_id"]],
                    world.stations[line[0]["destination_station_id"]], spec["order_dt"].date())]
                if allowed:
                    spec["lines"] = allowed
                    break
                spec = draw_spot_order()
            else:
                raise RuntimeError(f"Keine zulässige Spot-Bestellung für Firma {company_id} gefunden.")
        pending_orders.append(spec)

    for sequence, spec in enumerate(sorted(pending_orders, key=lambda o: o["order_dt"]), start=1):
        build_order(world, company_id, spec["customer"], spec["lines"], spec["order_dt"], sequence,
                    contract=spec["contract"], calloff_index=spec["calloff_index"],
                    calloff_total=spec["calloff_total"], force_late_after=spec["force_late_after"],
                    allow_cancel=spec["allow_cancel"], allow_delay=spec["allow_delay"])


def book_inventory_reservations(world: World) -> None:
    """Reserviert Lagerware für noch nicht abgeflogene Bestellungen (pending/confirmed).

    Bestandsware im gemeinsamen Strom, Ware der Erweiterungsfirmen im Strom des Anbieters.
    """
    reserved: dict[tuple[int, int], int] = defaultdict(int)
    orders = {o["order_id"]: o for o in world.rows["orders"]}
    for item in world.rows["order_items"]:
        order = orders[item["order_id"]]
        if order["status"] in ("pending", "confirmed"):
            reserved[(order["origin_station_id"], item["product_id"])] += item["quantity"]
    owner = {key: world.products[key[1]]["company_id"] for key in reserved}
    apply_reservations(world, [(key, qty) for key, qty in reserved.items() if world.is_legacy(owner[key])])
    for company_id in world.extension_company_ids():
        with world.company_stream(world.key_of(company_id), "reservations"):
            apply_reservations(world, [(key, qty) for key, qty in reserved.items() if owner[key] == company_id])


def apply_reservations(world: World, reserved: list[tuple[tuple[int, int], int]]) -> None:
    """Bucht Reservierungen und stockt knappe Lager auf (aktiver Zufallsstrom)."""
    rng = world.rng
    for key, quantity in reserved:
        inventory = world.inventory[key]
        inventory["reserved_quantity"] = quantity
        if inventory["quantity"] < quantity:
            inventory["quantity"] = quantity + int(inventory["restock_target"] * rng.uniform(0.05, 0.3))


def station_capacity(world: World, station: dict[str, Any], used: float) -> float:
    """Lagerkapazität: Nennkapazität oder belegtes Volumen mit Reserve (aktiver Zufallsstrom)."""
    size = SIZE_PROFILES[world.companies[station["company_id"]]["size_class"]]
    nominal = STATION_TYPES[station["station_type"]].base_storage_m3 * size.storage_factor
    return float(round(max(nominal, used * world.rng.uniform(1.3, 1.8)), -2))


def finalize_station_capacity(world: World) -> None:
    """Setzt die Lagerkapazität jeder Station über das tatsächlich belegte Volumen.

    Bestandsstationen werden zuerst nur mit Bestandsware bemessen (gemeinsamer Strom, Werte wie vor der
    Erweiterung). Reicht die Kapazität für zusätzliche Ware neuer Lieferanten nicht, wird sie im Strom
    der Erweiterung aufgestockt.
    """
    used_legacy: dict[int, float] = defaultdict(float)
    used_all: dict[int, float] = defaultdict(float)
    for inventory in world.rows["inventory"]:
        product = world.products[inventory["product_id"]]
        volume = inventory["quantity"] * product["volume_m3"]
        used_all[inventory["station_id"]] += volume
        if world.is_legacy(product["company_id"]):
            used_legacy[inventory["station_id"]] += volume
    for station in world.rows["stations"]:
        if world.is_legacy(station["company_id"]):
            station["storage_capacity_m3"] = station_capacity(world, station, used_legacy[station["station_id"]])
    with world.company_stream("extension", "capacity_topup"):
        for station in world.rows["stations"]:
            used = used_all[station["station_id"]]
            if world.is_legacy(station["company_id"]) and used > station["storage_capacity_m3"]:
                station["storage_capacity_m3"] = station_capacity(world, station, used)
    for company_id in world.extension_company_ids():
        with world.company_stream(world.key_of(company_id), "capacity"):
            for station in world.stations_by_company[company_id]:
                station["storage_capacity_m3"] = station_capacity(world, station, used_all[station["station_id"]])


# ---------------------------------------------------------------------------
# 10. Lieferungen
# ---------------------------------------------------------------------------


def generate_shipments(world: World) -> None:
    """Erzeugt je bestätigter Bestellung eine Lieferung mit Reisezeit passend zur Distanz."""
    counters: dict[int, int] = defaultdict(int)
    add_shipments(world, [o for o in world.rows["orders"] if world.is_legacy(o["company_id"])], counters)
    for company_id in world.extension_company_ids():
        with world.company_stream(world.key_of(company_id), "shipments"):
            add_shipments(world, [o for o in world.rows["orders"] if o["company_id"] == company_id], counters)


def add_shipments(world: World, orders: list[dict[str, Any]], counters: dict[int, int]) -> None:
    """Lieferungen für die übergebenen Bestellungen (aktiver Zufallsstrom)."""
    rng = world.rng
    shipment_status = {"confirmed": "pending", "in_transit": "in_transit", "delayed": "delayed",
                       "delivered": "delivered"}
    for order in orders:
        if order["status"] not in shipment_status:
            continue
        timeline = world.order_timelines[order["order_id"]]
        company_id = order["company_id"]
        language = world.language(company_id)
        counters[company_id] += 1
        delivered = order["status"] == "delivered"
        world.add("shipments", {
            "shipment_number": (f"{world.profiles[company_id].sku_prefix}-{SHIPMENT_PREFIX[language]}-"
                                f"{timeline['departure'].year}-{counters[company_id]:05d}"),
            "order_id": order["order_id"],
            "origin_station_id": order["origin_station_id"],
            "destination_station_id": order["destination_station_id"],
            "departure_date": fmt_dt(timeline["departure"]),
            "arrival_date": fmt_dt(timeline["expected_arrival"]),
            "actual_arrival_date": fmt_dt(timeline["actual_arrival"]) if delivered else None,
            "status": shipment_status[order["status"]],
            "ship_name": rng.choice(world.profiles[company_id].fleet),
            "cargo_mass_kg": timeline["cargo_mass"],
            "cargo_volume_m3": timeline["cargo_volume"],
            "fuel_cost": timeline["fuel_cost"],
            "insurance_cost": timeline["insurance_cost"],
            "risk_incident": timeline["incident"] if order["status"] in ("delayed", "delivered") else None,
        })


# ---------------------------------------------------------------------------
# 11. Preisverläufe (inkl. Planung der Marktereignisse, die die Kurven prägen)
# ---------------------------------------------------------------------------


def series_start_date(world: World, station_id: int, product_id: int) -> date:
    """Beginn der Preishistorie: kürzerer Datenzeitraum von Stationsbetreiber und Produktanbieter."""
    station_owner = world.stations[station_id]["company_id"]
    product_owner = world.products[product_id]["company_id"]
    return max(world.window_start(station_owner), world.window_start(product_owner))


def history_dates(start: date) -> list[date]:
    """Stützstellen der Preishistorie im Abstand von 14 Tagen, endend am Stichtag."""
    dates = []
    current = GAME_REFERENCE_DATE
    while current >= start:
        dates.append(current)
        current -= timedelta(days=PRICE_HISTORY_INTERVAL_DAYS)
    return list(reversed(dates))


def price_impact(supply_impact: float, demand_impact: float) -> float:
    """Preiswirkung aus Angebots- und Nachfrageänderung (gleiche Elastizität wie die Preiskurven)."""
    return ((1.0 + demand_impact) / max(1.0 + supply_impact, 0.05)) ** PRICE_ELASTICITY - 1.0


def plan_market_events(world: World) -> None:
    """Plant lokale Marktereignisse (ein System, max. drei Stationen) als Schocks für die Preiskurven.

    Bestand: Ereignisse an Bestandsstationen wirken nur auf Bestandsware und Bestandsnachbarn
    (gemeinsamer Strom, unverändert). Erweiterung: Ereignisse an neuen Stationen (Strom der Firma)
    wirken nur auf Ware der Erweiterungsfirmen, auch an Bestandsstationen im selben System.
    """
    legacy_inventory = [inv for inv in world.rows["inventory"]
                        if world.is_legacy(world.products[inv["product_id"]]["company_id"])]
    extension_inventory = [inv for inv in world.rows["inventory"]
                           if not world.is_legacy(world.products[inv["product_id"]]["company_id"])]
    legacy_stations = [s for s in world.rows["stations"] if world.is_legacy(s["company_id"])]
    plan_station_events(world, legacy_stations, legacy_inventory, legacy_stations, legacy=True)
    for company_id in world.extension_company_ids():
        with world.company_stream(world.key_of(company_id), "events"):
            plan_station_events(world, world.stations_by_company[company_id], extension_inventory,
                                world.rows["stations"], legacy=False)


def plan_station_events(world: World, origins: list[dict[str, Any]], inventory_rows: list[dict[str, Any]],
                        neighbourhood: list[dict[str, Any]], *, legacy: bool) -> None:
    """Ereignisse an den Ursprungsstationen; betroffen sind nur die übergebenen Lagerzeilen."""
    rng = world.rng
    tradeable_by_station: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for inventory in inventory_rows:
        if inventory["market_role"] in ("supply", "demand"):
            tradeable_by_station[inventory["station_id"]].append(inventory)
    stations_by_system: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for station in neighbourhood:
        stations_by_system[station["system_id"]].append(station)

    def eligible_inventory(event_type: EventType, station: dict[str, Any], event_date: date) -> list[dict[str, Any]]:
        return [inv for inv in tradeable_by_station[station["station_id"]]
                if event_type.product_filter(world.products[inv["product_id"]], inv)
                and series_start_date(world, inv["station_id"], inv["product_id"]) <= event_date - timedelta(days=14)]

    for station in origins:
        owner_id = station["company_id"]
        months = SIZE_PROFILES[world.companies[owner_id]["size_class"]].months
        event_count = max(0, round(rng.gauss(0.6 + months / 18.0, 0.9)))
        for _ in range(event_count):
            event_date = random_date(rng, world.window_start(owner_id) + timedelta(days=28),
                                     GAME_REFERENCE_DATE - timedelta(days=10))
            options = {code: et.weight for code, et in EVENT_TYPES.items()
                       if (et.station_types is None or station["station_type"] in et.station_types)
                       and (et.security_levels is None or station["security_level"] in et.security_levels)
                       and eligible_inventory(et, station, event_date)}
            if not options:
                continue
            code = weighted_choice(rng, options)
            event_type = EVENT_TYPES[code]
            supply_base = rng.uniform(*event_type.supply)
            demand_base = rng.uniform(*event_type.demand)
            duration = rng.randint(*event_type.duration_days)
            effects: list[dict[str, Any]] = []
            primary_inventory = eligible_inventory(event_type, station, event_date)
            for inv in rng.sample(primary_inventory, min(event_type.max_products, len(primary_inventory))):
                effects.append(_event_effect(rng, inv, supply_base, demand_base, 1.0))
            neighbours = [s for s in stations_by_system[station["system_id"]] if s["station_id"] != station["station_id"]]
            rng.shuffle(neighbours)
            for neighbour in neighbours[: max(0, event_type.max_stations - 1)]:
                if rng.random() < 0.5:
                    continue
                neighbour_inventory = eligible_inventory(event_type, neighbour, event_date)
                factor = rng.uniform(0.35, 0.65)
                for inv in rng.sample(neighbour_inventory,
                                      min(max(1, event_type.max_products // 2), len(neighbour_inventory))):
                    effects.append(_event_effect(rng, inv, supply_base, demand_base, factor))
            event = {"station": station, "code": code, "event_date": event_date, "duration": duration,
                     "supply": supply_base, "demand": demand_base, "effects": effects, "legacy": legacy}
            world.planned_events.append(event)
            for effect in effects:
                world.shocks[(effect["station_id"], effect["product_id"])].append({
                    "date": event_date, "duration": duration, "supply": effect["supply_impact"],
                    "demand": effect["demand_impact"]})


def _event_effect(rng: random.Random, inventory: dict[str, Any], supply_base: float, demand_base: float,
                  factor: float) -> dict[str, Any]:
    """Wirkung eines Ereignisses auf eine Station-Ware-Kombination."""
    supply = round(supply_base * factor * rng.uniform(0.85, 1.15), 3)
    demand = round(demand_base * factor * rng.uniform(0.85, 1.15), 3)
    return {"station_id": inventory["station_id"], "product_id": inventory["product_id"],
            "supply_impact": supply, "demand_impact": demand, "price_impact": round(price_impact(supply, demand), 3)}


def build_price_series(world: World, inventory: dict[str, Any]) -> None:
    """Erzeugt die Preishistorie einer Station-Ware-Kombination.

    Angebot = Bestand / Zielbestand. Preis = Basispreis × Regime × (Nachfrage / Angebot)^Elastizität.
    Enthalten: Saisonalität, AR(1)-Rauschen, Engpässe, Nachfragespitzen, Preisbrüche und Ereignisschocks.
    Der letzte Punkt entspricht exakt dem aktuellen Lagerbestand.
    """
    rng = world.rng
    product = world.products[inventory["product_id"]]
    dates = history_dates(series_start_date(world, inventory["station_id"], inventory["product_id"]))
    count = len(dates)
    is_supply = inventory["market_role"] == "supply"
    base_supply = 1.0 if is_supply else 0.45
    base_demand = 0.75 if is_supply else 1.35
    amp_supply, amp_demand, phase_days = CATEGORY_SEASONALITY[product["category_code"]]
    phase_days += rng.randint(-25, 25)
    break_index = int(count * rng.uniform(0.2, 0.85)) if rng.random() < 0.22 else None
    break_factor = rng.choice((rng.uniform(0.80, 0.90), rng.uniform(1.12, 1.30)))
    shocks = world.shocks.get((inventory["station_id"], inventory["product_id"]), [])

    supply_noise = demand_noise = 0.0
    shortage_left = 0
    shortage_factor = 1.0
    spike = 1.0
    supplies: list[float] = []
    demands: list[float] = []
    regimes: list[float] = []
    for index, day in enumerate(dates):
        supply_noise = 0.75 * supply_noise + rng.gauss(0, 0.06)
        demand_noise = 0.75 * demand_noise + rng.gauss(0, 0.05)
        if shortage_left == 0 and rng.random() < 0.03:
            shortage_left, shortage_factor = rng.randint(2, 5), rng.uniform(0.35, 0.65)
        current_shortage = shortage_factor if shortage_left > 0 else 1.0
        shortage_left = max(0, shortage_left - 1)
        spike = 1.0 + (spike - 1.0) * 0.55
        if rng.random() < 0.025:
            spike = rng.uniform(1.3, 1.9)
        season = 2 * math.pi * ((day - GAME_REFERENCE_DATE).days + phase_days) / 365.25
        shock_supply = shock_demand = 1.0
        for shock in shocks:
            elapsed = (day - shock["date"]).days
            if 0 <= elapsed < shock["duration"]:
                intensity = 1.0 - elapsed / shock["duration"]
                shock_supply *= 1.0 + shock["supply"] * intensity
                shock_demand *= 1.0 + shock["demand"] * intensity
        supplies.append(base_supply * math.exp(supply_noise) * (1 + amp_supply * math.sin(season))
                        * current_shortage * shock_supply)
        demands.append(base_demand * math.exp(demand_noise) * (1 + amp_demand * math.sin(season + math.pi))
                       * spike * shock_demand)
        regimes.append(break_factor if break_index is not None and index >= break_index else 1.0)

    # Brückenkorrektur: Angebotskurve endet exakt beim aktuellen Lagerbestand
    target = inventory["restock_target"]
    final_supply = inventory["quantity"] / target
    correction = math.log(max(final_supply, 0.02)) - math.log(max(supplies[-1], 0.02))
    for index in range(count):
        weight = index / (count - 1) if count > 1 else 1.0
        supplies[index] = max(supplies[index], 0.0) * math.exp(correction * weight)

    anchor = inventory["local_base_price"]
    for index, day in enumerate(dates):
        last = index == count - 1
        stock = inventory["quantity"] if last else max(0, int(round(supplies[index] * target)))
        supply_index = round(final_supply if last else stock / target, 4)
        ratio = (demands[index] / base_demand) / (max(supplies[index], 0.03) / base_supply)
        price = anchor * regimes[index] * ratio ** PRICE_ELASTICITY
        price = round(clamp(price, anchor * 0.3, anchor * 3.5), 2)
        world.add("price_history", {
            "station_id": inventory["station_id"], "product_id": inventory["product_id"], "date": fmt_date(day),
            "supply_index": supply_index, "demand_index": round(demands[index], 4),
            "market_price": max(price, 0.01), "stock_quantity": stock,
        })


def generate_price_history(world: World) -> None:
    """Plant Marktereignisse und erzeugt Preishistorien für alle handelbaren Station-Ware-Kombinationen."""
    plan_market_events(world)
    for inventory in world.rows["inventory"]:
        if inventory["market_role"] in ("supply", "demand") and world.is_legacy(
                world.products[inventory["product_id"]]["company_id"]):
            build_price_series(world, inventory)
    for company_id in world.extension_company_ids():
        with world.company_stream(world.key_of(company_id), "prices"):
            for inventory in world.rows["inventory"]:
                if (inventory["market_role"] in ("supply", "demand")
                        and world.products[inventory["product_id"]]["company_id"] == company_id):
                    build_price_series(world, inventory)


# ---------------------------------------------------------------------------
# 12. Mitarbeiter
# ---------------------------------------------------------------------------


def generate_employees(world: World) -> None:
    """Erzeugt Mitarbeiter mit Rollen, Gehältern und Spielwerten für Beziehungspflege und Spionage."""
    for company_id in world.companies:
        with world.company_stream(world.key_of(company_id), "employees"):
            generate_company_employees(world, company_id)


def generate_company_employees(world: World, company_id: int) -> None:
    """Mitarbeiter einer Firma im aktiven Zufallsstrom.

    Bei Erweiterungsfirmen sind Vorstand, erste Partnerbetreuung und erste Marktaufklärung spätestens
    zur Einstellungsgrenze (HIRE_DATE_CAPS) eingestellt und zum Stichtag aktiv – sie unterzeichnen
    Rahmenverträge und Schreiben.
    """
    rng = world.rng
    company = world.companies[company_id]
    hire_cap = None if world.is_legacy(company_id) else HIRE_DATE_CAPS.get(world.key_of(company_id))
    capped_roles: set[str] = set()
    profile = world.profiles[company_id]
    size = SIZE_PROFILES[company["size_class"]]
    language = company["language"]
    fake = world.fake(company_id)
    stations = world.stations_by_company[company_id]
    headquarters = stations[0]
    assignments: list[tuple[str, dict[str, Any]]] = [("executive", headquarters)]
    assignments += [("finance", headquarters)] * rng.randint(1, 3)
    assignments += [("relations", headquarters)] * rng.randint(1, 2)
    assignments += [("intelligence", headquarters)] * {"small": rng.randint(0, 1), "medium": 1, "large": 2}[company["size_class"]]
    assignments += [("station_manager", station) for station in stations]
    station_weights = {station["station_id"]: math.sqrt(station["population"]) for station in stations}
    while len(assignments) < world.targets[company_id]["employees"]:
        station = world.stations[weighted_choice(rng, station_weights)]
        assignments.append((weighted_choice(rng, STATION_ROLE_WEIGHTS[station["station_type"]]), station))

    founded = date(company["founded_year"], 1, 1)
    for role_code, station in assignments:
        role = ROLES[role_code]
        personality = rng.choice(PERSONALITIES)
        salary = round(rng.uniform(*role.salary) * size.salary_factor, -1)
        salary_norm = (salary / size.salary_factor - role.salary[0]) / (role.salary[1] - role.salary[0])
        loyalty = rng.gauss(65 + profile.loyalty_bias, 14)
        loyalty += {"loyal": 12, "greedy": -10, "ambitious": -6}.get(personality, 0)
        loyalty = int(clamp(loyalty, 0, 100))
        bribe = 100 - loyalty * 0.6 - salary_norm * 20 + rng.gauss(0, 10)
        bribe += {"greedy": 20, "talkative": 8, "idealistic": -15, "loyal": -10}.get(personality, 0)
        hire_earliest = max(founded, GAME_REFERENCE_DATE - timedelta(days=15 * 365))
        hire_date = random_date(rng, hire_earliest, GAME_REFERENCE_DATE - timedelta(days=14))
        is_active = 0 if role_code not in ("executive", "station_manager") and rng.random() < 0.06 else 1
        if hire_cap is not None and role_code in HIRE_CAP_ROLES and role_code not in capped_roles:
            capped_roles.add(role_code)
            if hire_date > hire_cap:
                hire_date = random_date(rng, min(hire_earliest, hire_cap), hire_cap)
            is_active = 1
        termination = (fmt_date(random_date(rng, hire_date + timedelta(days=60), GAME_REFERENCE_DATE - timedelta(days=1)))
                       if not is_active and hire_date + timedelta(days=60) < GAME_REFERENCE_DATE else None)
        if not is_active and termination is None:
            is_active = 1
        world.add("employees", {
            "company_id": company_id,
            "station_id": station["station_id"],
            "full_name": person_name(fake),
            "role": role.title_de if language == "de_DE" else role.title_en,
            "role_code": role_code,
            "salary": salary,
            "hire_date": fmt_date(hire_date),
            "is_active": is_active,
            "termination_date": termination,
            "influence": int(clamp(rng.randint(*role.influence) + rng.gauss(0, 4), 0, 100)),
            "loyalty": loyalty,
            "bribe_susceptibility": int(clamp(bribe, 0, 100)),
            "intel_access_level": role.intel_access_level,
            "personality": personality,
        })


# ---------------------------------------------------------------------------
# 13. Ereignisse
# ---------------------------------------------------------------------------


def severity_for(supply_impact: float, demand_impact: float) -> str:
    """Schweregrad aus der stärksten Angebots- oder Nachfragewirkung."""
    magnitude = max(abs(supply_impact), abs(demand_impact))
    if magnitude < 0.3:
        return "minor"
    if magnitude < 0.5:
        return "moderate"
    if magnitude < 0.75:
        return "major"
    return "critical"


def generate_events(world: World) -> None:
    """Schreibt die geplanten Marktereignisse samt aller betroffenen Stationen und Waren.

    Bestandsereignisse zuerst (chronologisch, gleiche event_id wie vor der Erweiterung), danach die
    Ereignisse der Erweiterungsfirmen (ebenfalls chronologisch).
    """
    ordered = (sorted([e for e in world.planned_events if e["legacy"]], key=lambda e: e["event_date"])
               + sorted([e for e in world.planned_events if not e["legacy"]], key=lambda e: e["event_date"]))
    for planned in ordered:
        station = planned["station"]
        event_type = EVENT_TYPES[planned["code"]]
        language = world.language(station["company_id"])
        primary_effects = [e for e in planned["effects"] if e["station_id"] == station["station_id"]]
        primary = max(primary_effects, key=lambda e: abs(e["price_impact"]))
        product_names = [world.products[e["product_id"]]["name"] for e in primary_effects[:3]]
        joiner = " und " if language == "de_DE" else " and "
        if len(primary_effects) > 3:
            products_text = ", ".join(product_names) + (" u. a." if language == "de_DE" else " and more")
        elif len(product_names) > 1:
            products_text = ", ".join(product_names[:-1]) + joiner + product_names[-1]
        else:
            products_text = product_names[0]
        template = event_type.text_de if language == "de_DE" else event_type.text_en
        description = template.format(
            station=station["name"], system=station["system_name"], products=products_text,
            supply_pct=fmt_number(abs(primary["supply_impact"]) * 100, language),
            demand_pct=fmt_number(abs(primary["demand_impact"]) * 100, language),
            price_pct=fmt_number(abs(primary["price_impact"]) * 100, language))
        event = world.add("events", {
            "station_id": station["station_id"],
            "event_date": fmt_date(planned["event_date"]),
            "event_type": planned["code"],
            "title": event_type.label_de if language == "de_DE" else event_type.label_en,
            "severity": severity_for(primary["supply_impact"], primary["demand_impact"]),
            "affected_product_id": primary["product_id"],
            "description": description,
            "price_impact": primary["price_impact"],
            "supply_impact": primary["supply_impact"],
            "demand_impact": primary["demand_impact"],
            "duration_days": planned["duration"],
        })
        for effect in planned["effects"]:
            world.add("event_effects", {"event_id": event["event_id"], **effect})


# ---------------------------------------------------------------------------
# 14. Finanzdaten
# ---------------------------------------------------------------------------


def generate_financials(world: World) -> None:
    """Leitet Monatsabschlüsse je Firma aus Bestellungen, Lieferungen, Personal und Stationen ab."""
    orders = pd.DataFrame(world.rows["orders"])
    items = pd.DataFrame(world.rows["order_items"])
    shipments = pd.DataFrame(world.rows["shipments"])
    employees = pd.DataFrame(world.rows["employees"])
    products = pd.DataFrame(world.rows["products"])[["product_id", "base_cost", "legal_status"]]
    contracts = pd.DataFrame(world.rows["contracts"])
    destinations = pd.DataFrame(world.rows["stations"])[["station_id", "security_level", "docking_fee"]].rename(
        columns={"station_id": "destination_station_id"})

    delivered = shipments[shipments["status"] == "delivered"][["order_id", "actual_arrival_date"]]
    delivered = delivered.merge(orders, on="order_id")
    delivered["period"] = delivered["actual_arrival_date"].str[:7]
    delivered["service_revenue"] = delivered["freight_cost"] + delivered["insurance_cost"] + delivered["handling_fee"]
    lines = items.merge(products, on="product_id").merge(
        orders[["order_id", "destination_station_id"]], on="order_id").merge(destinations, on="destination_station_id")
    lines["cogs"] = lines["quantity"] * lines["base_cost"]
    # Einfuhrzoll auf legale Ware am Zielort; Schmuggelware zahlt stattdessen Schutz- und Schmiergelder
    is_illegal = lines["legal_status"] == "illegal"
    lines["duties"] = lines["line_total"] * lines["security_level"].map(TARIFF_RATE).where(~is_illegal,
                                                                                          BLACK_MARKET_FEE_RATE)
    per_order = lines.groupby("order_id", as_index=False)[["cogs", "duties"]].sum()
    delivered = delivered.merge(per_order, on="order_id").merge(
        destinations[["destination_station_id", "docking_fee"]], on="destination_station_id")
    delivered["duties_and_fees"] = delivered["duties"] + delivered["docking_fee"]
    revenue = delivered.groupby(["company_id", "period"]).agg(
        goods_revenue=("subtotal", "sum"), service_revenue=("service_revenue", "sum"),
        cost_of_goods_sold=("cogs", "sum"), duties_and_fees=("duties_and_fees", "sum"),
        orders_delivered=("order_id", "count"))

    shipped = shipments[shipments["status"] != "pending"].merge(orders[["order_id", "company_id"]], on="order_id")
    shipped["period"] = shipped["departure_date"].str[:7]
    shipped["logistics"] = shipped["fuel_cost"] + shipped["insurance_cost"]
    logistics = shipped.groupby(["company_id", "period"])["logistics"].sum()

    penalties: dict[tuple[int, str], float] = defaultdict(float)
    for booking in contract_penalty_bookings(contracts, orders, shipments):
        penalties[(booking["company_id"], booking["period"])] += booking["amount"]

    for company_id, company in world.companies.items():
        upkeep = sum(s["monthly_upkeep"] for s in world.stations_by_company[company_id])
        fleet = len(world.profiles[company_id].fleet) * SIZE_PROFILES[company["size_class"]].fleet_cost_per_ship
        staff = employees[employees["company_id"] == company_id]
        cash = company["starting_cash"]
        month = world.window_start(company_id).replace(day=1)
        while month < GAME_REFERENCE_DATE:
            period = month.strftime("%Y-%m")
            month_end = shift_months(month, 1) - timedelta(days=1)
            on_payroll = staff[(staff["hire_date"] <= fmt_date(month_end))
                               & (staff["termination_date"].isna() | (staff["termination_date"] >= fmt_date(month)))]
            key = (company_id, period)
            values = revenue.loc[key] if key in revenue.index else None
            goods = float(values["goods_revenue"]) if values is not None else 0.0
            services = float(values["service_revenue"]) if values is not None else 0.0
            cost_of_goods = float(values["cost_of_goods_sold"]) if values is not None else 0.0
            duties = float(values["duties_and_fees"]) if values is not None else 0.0
            delivered_count = int(values["orders_delivered"]) if values is not None else 0
            logistics_cost = float(logistics.get(key, 0.0))
            payroll = float(on_payroll["salary"].sum())
            penalty = penalties.get(key, 0.0)
            net = goods + services - cost_of_goods - duties - logistics_cost - fleet - payroll - upkeep - penalty
            cash += net
            world.add("company_financials", {
                "company_id": company_id, "period": period, "orders_delivered": delivered_count,
                "goods_revenue": round(goods, 2), "service_revenue": round(services, 2),
                "cost_of_goods_sold": round(cost_of_goods, 2), "duties_and_fees": round(duties, 2),
                "logistics_cost": round(logistics_cost, 2), "fleet_operations": round(fleet, 2),
                "payroll_cost": round(payroll, 2), "station_upkeep": round(upkeep, 2),
                "contract_penalties": round(penalty, 2), "net_income": round(net, 2),
                "cash_balance": round(cash, 2),
            })
            month = shift_months(month, 1)


# ---------------------------------------------------------------------------
# 16. Schriftverkehr
# ---------------------------------------------------------------------------

CORRESPONDENCE_TYPES: tuple[str, ...] = (
    "inquiry", "offer", "counter_offer", "offer_rejection", "contract_confirmation", "amendment_offer",
    "amendment_confirmation", "amendment_rejection", "delivery_notice", "delay_notice", "delay_complaint",
    "penalty_notice", "payment_reminder", "breach_warning", "termination_notice", "suspension_notice", "protest",
    "confidential_tip", "rumor", "internal_memo",
)
CORRESPONDENCE_CHANNELS = ("letter", "email", "encrypted_message", "holo_call")
CORRESPONDENCE_DIRECTIONS = ("seller_to_buyer", "buyer_to_seller", "internal", "to_rival", "lateral")
CONFIDENTIALITY_LEVELS: dict[str, int] = {"public": 0, "internal": 1, "confidential": 2}
SENTIMENTS = ("positive", "neutral", "negative", "hostile")
CORRESPONDENCE_STATUSES = ("sent", "read", "answered", "rejected", "escalated", "closed")
CORRESPONDENCE_PREFIX = {"de_DE": "KOR", "en_US": "COR"}
COPY_TYPES = ("cc", "bcc", "forward")

# Briefarten ohne Parteienregel (Bezugsobjekt muss nur eine der beiden Firmen betreffen)
EXEMPT_PARTY_TYPES: frozenset[str] = frozenset({"confidential_tip", "rumor", "internal_memo", "protest"})
# Verhandlungsschreiben dürfen vor dem Beginn ihres Vertrags bzw. vor der Unterzeichnung des Rahmens liegen
NEGOTIATION_TYPES: frozenset[str] = frozenset({"inquiry", "offer", "counter_offer", "offer_rejection"})
EXECUTIVE_PENALTY_THRESHOLD = 250_000.0  # darüber zeichnet der Vorstand, sonst die Finanzbuchhaltung
LATE_COMPLAINT_HOURS = 48.0  # Verzugsbeschwerde ab 48 h Verspätung einer Abruflieferung
REMINDER_STAGE_DAYS: tuple[tuple[int, int], ...] = ((3, 7), (21, 21), (45, 45))  # nach Fälligkeit (K3–K5)
DELIVERY_NOTICE_MIN_AMOUNT = 3_000_000.0  # Lieferavis für große Abrufe
LEAK_SCALE = 0.50  # dämpft die Leckformel auf eine spielbare Menge vertraulicher Tipps
RUMOR_TRUTH_SPLIT: dict[int | None, float] = {1: 0.3, None: 0.5, 0: 0.2}

SENTIMENT_BY_TYPE: dict[str, str] = {
    "inquiry": "neutral", "offer": "positive", "counter_offer": "neutral", "offer_rejection": "negative",
    "contract_confirmation": "positive", "amendment_offer": "neutral", "amendment_confirmation": "positive",
    "amendment_rejection": "negative", "delivery_notice": "neutral", "delay_notice": "negative",
    "delay_complaint": "negative", "penalty_notice": "negative", "payment_reminder": "neutral",
    "breach_warning": "negative", "termination_notice": "negative", "suspension_notice": "hostile",
    "protest": "hostile", "confidential_tip": "neutral", "rumor": "neutral", "internal_memo": "neutral",
}
TRUST_EFFECTS: dict[str, tuple[int, int]] = {
    "inquiry": (0, 2), "offer": (1, 3), "counter_offer": (-1, 1), "offer_rejection": (-4, -1),
    "contract_confirmation": (3, 6), "amendment_offer": (0, 2), "amendment_confirmation": (2, 4),
    "amendment_rejection": (-5, -2), "delivery_notice": (0, 1), "delay_notice": (-2, 0),
    "delay_complaint": (-5, -2), "penalty_notice": (-9, -4), "payment_reminder": (-3, -1),
    "breach_warning": (-10, -5), "termination_notice": (-12, -6), "suspension_notice": (-16, -10),
    "protest": (-18, -10), "confidential_tip": (0, 0), "rumor": (-2, 0), "internal_memo": (0, 0),
}
CORRESPONDENCE_ROLE_ORDER: dict[str, tuple[str, ...]] = {
    "executive": ("executive", "relations", "station_manager"),
    "relations": ("relations", "executive", "station_manager"),
    "finance": ("finance", "relations", "executive"),
    "intelligence": ("intelligence", "relations", "executive"),
    "logistics": ("logistics", "station_manager", "relations", "executive"),
    "station": ("station_manager", "logistics", "relations", "executive"),
}
TYPE_LABELS: dict[str, tuple[str, str]] = {
    "inquiry": ("Anfrage", "Inquiry"), "offer": ("Angebot", "Offer"),
    "counter_offer": ("Gegenangebot", "Counter-offer"), "offer_rejection": ("Absage", "Rejection"),
    "contract_confirmation": ("Vertragsbestätigung", "Contract confirmation"),
    "amendment_offer": ("Nachtragsangebot", "Amendment proposal"),
    "amendment_confirmation": ("Bestätigung Nachtrag", "Amendment confirmation"),
    "amendment_rejection": ("Ablehnung Nachtrag", "Amendment rejected"),
    "delivery_notice": ("Lieferavis", "Delivery notice"), "delay_notice": ("Verzögerungsmeldung", "Delay notice"),
    "delay_complaint": ("Verzugsbeschwerde", "Delay complaint"),
    "penalty_notice": ("Vertragsstrafenbescheid", "Penalty notice"),
    "payment_reminder": ("Mahnung", "Payment reminder"),
    "breach_warning": ("Abmahnung", "Breach warning"), "termination_notice": ("Kündigung", "Termination notice"),
    "suspension_notice": ("Aussetzung", "Suspension notice"), "protest": ("Protest", "Protest"),
    "confidential_tip": ("Vertraulicher Hinweis", "Confidential tip"), "rumor": ("Gerücht", "Rumour"),
    "internal_memo": ("Interne Notiz", "Internal memo"),
}
SEVERITY_LABELS: dict[str, tuple[str, str]] = {
    "minor": ("gering", "minor"), "moderate": ("mittel", "moderate"), "major": ("schwer", "major"),
    "critical": ("kritisch", "critical"),
}
REMINDER_LABELS: tuple[tuple[str, str], ...] = (
    ("Zahlungserinnerung", "Payment reminder"), ("2. Mahnung", "Second reminder"),
    ("Letzte Mahnung", "Final reminder"))

# Verankerte Vorgänge V1–V41 (phase2_entscheidung.md, Abschnitt 6.3); gelten nur bei Seed 42
STORYLINE_CODES: tuple[str, ...] = tuple(f"V{n}" for n in range(1, 42))


def satisfies_leak_rule(employee: dict[str, Any]) -> bool:
    """Leck-Regel: bestechlich (≥ 50) oder wenig loyal (≤ 50)."""
    return employee["bribe_susceptibility"] >= 50 or employee["loyalty"] <= 50


def employed_on(employee: dict[str, Any], day: str) -> bool:
    """Am Tag (ISO-Datum) beschäftigt: eingestellt und nicht vorher ausgeschieden."""
    return employee["hire_date"] <= day and (employee["termination_date"] is None or employee["termination_date"] > day)


def contract_penalty_bookings(contracts: pd.DataFrame, orders: pd.DataFrame,
                              shipments: pd.DataFrame) -> list[dict[str, Any]]:
    """Vertragsstrafen gebrochener Verträge (Formel aus generate_financials, gleiche Reihenfolge).

    Strafe = Verzugstage × penalty_per_day; Verzugstage zählen von der Frist bis zur letzten Ankunft eines
    Abrufs. Ist ein Abruf noch unterwegs, läuft die Strafe bis zum Vortag des Stichtags auf. Gebucht wird beim
    Verkäufer (`company_id`) im Monat der letzten Ankunft.
    """
    breached = contracts[contracts["status"] == "breached"]
    order_by_contract = orders.dropna(subset=["contract_id"]).merge(shipments[["order_id", "actual_arrival_date"]],
                                                                   on="order_id")
    bookings = []
    for contract in breached.itertuples():
        arrivals = order_by_contract[order_by_contract["contract_id"] == contract.contract_id]["actual_arrival_date"]
        # Noch verspätet unterwegs: Strafe läuft bis zum Stichtag auf
        in_transit = bool(arrivals.isna().any())
        last_arrival = (GAME_REFERENCE_DATETIME - timedelta(days=1) if in_transit
                        else datetime.fromisoformat(arrivals.max()))
        late_days = max(0, (last_arrival.date() - date.fromisoformat(contract.deadline)).days)
        bookings.append({"contract_id": int(contract.contract_id), "company_id": contract.company_id,
                         "period": last_arrival.strftime("%Y-%m"), "late_days": late_days,
                         "penalty_per_day": contract.penalty_per_day, "amount": late_days * contract.penalty_per_day,
                         "last_arrival": last_arrival, "in_transit": in_transit})
    return bookings


@dataclass
class Letter:
    """Ein Schreiben während der Generierung (IDs und Nummern werden zum Schluss chronologisch vergeben)."""

    key: int
    sent_at: datetime
    letter_type: str
    sender_company_id: int
    sender_employee_id: int | None
    recipient_company_id: int | None
    recipient_employee_id: int | None
    recipient_customer_id: int | None
    subject: str
    body: str
    channel: str
    direction: str
    confidentiality: str
    min_intel_access_level: int
    sentiment: str
    refs: dict[str, int | None]
    amount: float | None = None
    due_date: str | None = None
    response_required: int = 0
    trust_effect: int = 0
    is_accurate: int | None = None
    intel_value: int = 0
    reply_to: int | None = None
    thread: int | None = None
    refers_to: int | None = None
    leak_status: str = "none"
    leaked_by: int | None = None
    leaked_to: int | None = None
    storyline: str | None = None
    copies: list[tuple[int, str]] = field(default_factory=list)


UNIT_LABELS_BY_TEXT: dict[str, tuple[str, str]] = {label: labels for labels in UNIT_LABELS.values() for label in labels}
REFERENCE_KEYS = ("partnership_id", "rivalry_id", "framework_agreement_id", "amendment_id", "contract_id", "order_id",
                  "shipment_id", "event_id")


class CorrespondenceDesk:
    """Erzeugt den Schriftverkehr im eigenen Zufallsstrom und hält die Nachschlage-Indizes dafür.

    Der Strom ist aus (Seed, "correspondence") abgeleitet; der gemeinsame Strom `world.rng` und die
    Faker-Instanzen werden nicht benutzt. Bestehende Tabellen werden nur gelesen.
    """

    def __init__(self, world: World) -> None:
        self.world = world
        self.rng = random.Random(derived_seed(world.seed, "correspondence", "letters"))
        self.letters: list[Letter] = []
        self.by_key: dict[int, Letter] = {}
        self.claimed: set[tuple[Any, ...]] = set()
        self.adaptations: list[str] = []
        rows = world.rows
        self.employees = {e["employee_id"]: e for e in rows["employees"]}
        self.staff: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for employee in rows["employees"]:
            self.staff[employee["company_id"]].append(employee)
        self.contracts = {c["contract_id"]: c for c in rows["contracts"]}
        self.contract_by_number = {c["contract_number"]: c for c in rows["contracts"]}
        self.orders = {o["order_id"]: o for o in rows["orders"]}
        self.order_by_number = {o["order_number"]: o for o in rows["orders"]}
        self.orders_by_contract: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for order in rows["orders"]:
            if order["contract_id"] is not None:
                self.orders_by_contract[order["contract_id"]].append(order)
        self.items_by_order: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for item in rows["order_items"]:
            self.items_by_order[item["order_id"]].append(item)
        self.shipment_by_order = {s["order_id"]: s for s in rows["shipments"]}
        self.shipment_by_number = {s["shipment_number"]: s for s in rows["shipments"]}
        self.events = {e["event_id"]: e for e in rows["events"]}
        self.frameworks = {f["framework_agreement_id"]: f for f in rows["framework_agreements"]}
        self.framework_by_number = {f["agreement_number"]: f for f in rows["framework_agreements"]}
        self.amendments = {a["amendment_id"]: a for a in rows["framework_agreement_amendments"]}
        self.amendment_by_number = {a["amendment_number"]: a for a in rows["framework_agreement_amendments"]}
        self.scope = rows["framework_agreement_scope"]
        self.partnerships = {p["partnership_id"]: p for p in rows["trade_partnerships"]}
        self.active_pair = {(p["company_id"], p["partner_company_id"]): p for p in rows["trade_partnerships"]
                            if p["is_active"]}
        self.rivalries = {r["rivalry_id"]: r for r in rows["company_rivalries"]}
        self.rivalries_of: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for rivalry in rows["company_rivalries"]:
            self.rivalries_of[rivalry["company_id"]].append(rivalry)
            self.rivalries_of[rivalry["rival_company_id"]].append(rivalry)
        self.customers = {c["customer_id"]: c for c in rows["customers"]}
        self.penalties = {b["contract_id"]: b for b in contract_penalty_bookings(
            pd.DataFrame(rows["contracts"]), pd.DataFrame(rows["orders"]), pd.DataFrame(rows["shipments"]))}

    # -- Grunddaten -------------------------------------------------------------------------------------
    def lang(self, company_id: int) -> str:
        """Sprache einer Firma."""
        return self.world.language(company_id)

    def name(self, company_id: int) -> str:
        """Firmenname."""
        return self.world.companies[company_id]["name"]

    def station_name(self, station_id: int) -> str:
        """Stationsname."""
        return self.world.stations[station_id]["name"]

    def product_label(self, product_id: int) -> str:
        """Produktname (Eigenname in der Sprache des Herstellers)."""
        return self.world.products[product_id]["name"]

    def unit(self, product_id: int, language: str) -> str:
        """Mengeneinheit in der Briefsprache."""
        unit = self.world.products[product_id]["unit"]
        labels = UNIT_LABELS_BY_TEXT.get(unit)
        return labels[lang_index(language)] if labels else unit

    def money(self, value: float, language: str) -> str:
        """Betrag mit Währung."""
        return f"{fmt_number(value, language, 2)} {CURRENCY_CODE}"

    def day_text(self, value: date | datetime | str, language: str) -> str:
        """Datum für Fließtext."""
        if isinstance(value, str):
            value = date.fromisoformat(value[:10])
        if isinstance(value, datetime):
            value = value.date()
        return fmt_human_date(value, language)

    def event_label(self, event: dict[str, Any], language: str) -> str:
        """Ereignis mit Typ, Station und Datum."""
        event_type = EVENT_TYPES[event["event_type"]]
        label = event_type.label_de if language == "de_DE" else event_type.label_en
        station, day = self.station_name(event["station_id"]), self.day_text(event["event_date"], language)
        return f"{label} an {station} am {day}" if language == "de_DE" else f"{label} at {station} on {day}"

    def contract_line(self, contract: dict[str, Any], language: str) -> str:
        """Kurzbeschreibung eines Vertrags."""
        product = contract["product_id"]
        quantity = fmt_number(contract["quantity"], language)
        if language == "de_DE":
            return (f"{contract['contract_number']} über {quantity} {self.unit(product, language)} "
                    f"{self.product_label(product)} von {self.station_name(contract['origin_station_id'])} nach "
                    f"{self.station_name(contract['destination_station_id'])}")
        return (f"{contract['contract_number']} for {quantity} {self.unit(product, language)} of "
                f"{self.product_label(product)} from {self.station_name(contract['origin_station_id'])} to "
                f"{self.station_name(contract['destination_station_id'])}")

    def order_line(self, order: dict[str, Any], language: str) -> str:
        """Kurzbeschreibung einer Bestellung (erste Position)."""
        items = self.items_by_order[order["order_id"]]
        item = items[0]
        more = len(items) - 1
        quantity = fmt_number(item["quantity"], language)
        product = item["product_id"]
        text = f"{order['order_number']} ({quantity} {self.unit(product, language)} {self.product_label(product)}"
        if more:
            text += f" u. a., {more + 1} Positionen" if language == "de_DE" else f" and more, {more + 1} lines"
        return text + ")"

    # -- Personen -----------------------------------------------------------------------------------------
    def pick(self, company_id: int, moment: datetime, role: str, station_id: int | None = None,
             salt: int = 0) -> dict[str, Any] | None:
        """Ansprechpartner einer Firma am Versandtag (stabil je Gegenüber über `salt`)."""
        day = fmt_date(moment)
        for role_code in CORRESPONDENCE_ROLE_ORDER[role]:
            pool = [e for e in self.staff[company_id] if e["role_code"] == role_code and employed_on(e, day)]
            if station_id is not None and role_code in ("station_manager", "logistics"):
                pool = [e for e in pool if e["station_id"] == station_id]
            if pool:
                return pool[salt % len(pool)]
        pool = [e for e in self.staff[company_id] if e["intel_access_level"] >= 2 and employed_on(e, day)]
        return pool[salt % len(pool)] if pool else None

    def person(self, employee_id: int | None, company_id: int, moment: datetime, role: str,
               station_id: int | None = None, salt: int = 0, note: str = "") -> dict[str, Any] | None:
        """Vorgegebene Person (verankerter Vorgang) prüfen; sonst Ersatz nach Rolle (wird dokumentiert)."""
        employee = self.employees.get(employee_id) if employee_id is not None else None
        if employee is not None and employee["company_id"] == company_id and employed_on(employee, fmt_date(moment)):
            return employee
        replacement = self.pick(company_id, moment, role, station_id, salt)
        if employee_id is not None and note:
            self.adaptations.append(f"{note}: Mitarbeiter {employee_id} am {fmt_date(moment)} nicht verfügbar, ersetzt "
                                    f"durch {replacement['employee_id'] if replacement else '–'}")
        return replacement

    # -- Zeit -------------------------------------------------------------------------------------------------
    def at(self, day: date, earliest: datetime | None = None) -> datetime | None:
        """Versandzeitpunkt im Bürobetrieb am Tag, nie vor `earliest` und immer vor dem Stichtag."""
        moment = datetime(day.year, day.month, day.day, 8, 0) + timedelta(minutes=self.rng.randint(0, 600))
        if earliest is not None and moment <= earliest:
            moment = earliest + timedelta(minutes=self.rng.randint(20, 180))
        if moment >= GAME_REFERENCE_DATETIME:
            if earliest is None or earliest + timedelta(minutes=2) >= GAME_REFERENCE_DATETIME:
                return None
            moment = earliest + timedelta(minutes=1)
        return moment.replace(second=0, microsecond=0)

    # -- Schreiben anlegen ----------------------------------------------------------------------------------
    def compose(self, language: str, recipient_name: str | None, paragraphs: list[str], sender: dict[str, Any],
                channel: str, moment: datetime) -> str:
        """Fließtext mit Anrede, Absätzen und Schlussformel in der Briefsprache."""
        company = self.name(sender["company_id"])
        de = language == "de_DE"
        first = paragraphs[0]
        if not de or channel == "holo_call":  # deutsche Briefe beginnen nach der Anrede klein (außer Substantiven)
            paragraphs = [first[:1].upper() + first[1:], *paragraphs[1:]]
        if channel == "holo_call":
            head = (f"Gesprächsnotiz zum Holo-Ruf vom {self.day_text(moment, language)}, {moment:%H:%M} Uhr"
                    if de else f"Call note, holo call on {self.day_text(moment, language)} at {moment:%H:%M}")
            partner = (f" mit {recipient_name}" if de else f" with {recipient_name}") if recipient_name else ""
            signature = f"{sender['full_name']}, {sender['role']}, {company}"
            return f"{head}{partner}.\n\n" + "\n\n".join(paragraphs) + f"\n\n{signature}"
        if channel == "encrypted_message":
            head = ("[Verschlüsselte Nachricht – nur für den Empfänger]" if de
                    else "[Encrypted message – recipient only]")
            greeting = f"{recipient_name}," if recipient_name else ""
            return f"{head}\n\n{greeting}\n\n" + "\n\n".join(paragraphs) + f"\n\n– {sender['full_name']}"
        if recipient_name:
            greeting = f"Guten Tag {recipient_name}," if de else f"Dear {recipient_name},"
        else:
            greeting = "Sehr geehrte Damen und Herren," if de else "Dear Sir or Madam,"
        closing = "Mit freundlichen Grüßen" if de else "Kind regards"
        return (f"{greeting}\n\n" + "\n\n".join(paragraphs)
                + f"\n\n{closing}\n{sender['full_name']}\n{sender['role']}, {company}")

    def channel_for(self, letter_type: str, confidentiality: str, amount: float | None) -> str:
        """Übertragungsweg nach Briefart, Vertraulichkeit und Betrag."""
        rng = self.rng
        if letter_type in ("confidential_tip", "rumor"):
            return "encrypted_message" if rng.random() < 0.75 else "holo_call"
        if letter_type == "counter_offer":
            return "holo_call" if rng.random() < 0.45 else "email"
        if letter_type in ("termination_notice", "suspension_notice", "contract_confirmation", "protest"):
            return "letter"
        if letter_type == "penalty_notice":
            return "letter" if (amount or 0) > EXECUTIVE_PENALTY_THRESHOLD else "email"
        if letter_type == "internal_memo":
            return "encrypted_message" if confidentiality == "confidential" else "email"
        if confidentiality == "confidential":
            return "letter" if rng.random() < 0.6 else "encrypted_message"
        if letter_type == "payment_reminder":
            return "letter" if rng.random() < 0.5 else "email"
        if letter_type in ("delivery_notice", "delay_notice"):
            return "email"
        return "email" if rng.random() < 0.85 else "holo_call"

    def add(self, *, moment: datetime | None, letter_type: str, sender: dict[str, Any] | None,
            recipient: dict[str, Any] | None = None, recipient_company_id: int | None = None,
            customer: dict[str, Any] | None = None, subject: str, paragraphs: list[str], direction: str,
            confidentiality: str = "internal", refs: dict[str, int | None] | None = None,
            amount: float | None = None, due_date: str | None = None, response_required: int = 0,
            reply_to: Letter | None = None, thread: Letter | None = None, refers_to: Letter | None = None,
            is_accurate: int | None = None, leaked_by: int | None = None, leaked_to: int | None = None,
            storyline: str | None = None, sentiment: str | None = None, channel: str | None = None,
            claim: tuple[Any, ...] | None = None, copies: list[tuple[int, str]] | None = None) -> Letter | None:
        """Legt ein Schreiben an (Sprache = Absenderfirma); liefert None, wenn es nicht zulässig wäre."""
        if moment is None or sender is None or (recipient is None and customer is None):
            return None
        if reply_to is not None and reply_to.sender_company_id == sender["company_id"]:
            thread, reply_to = reply_to, None  # eigenes Folgeschreiben: gleicher Vorgang, keine Antwort
        if thread is not None and moment <= thread.sent_at:
            moment = thread.sent_at + timedelta(minutes=self.rng.randint(30, 240))
        if reply_to is not None and moment <= reply_to.sent_at:
            moment = reply_to.sent_at + timedelta(minutes=self.rng.randint(30, 240))
        if moment >= GAME_REFERENCE_DATETIME:
            return None
        sender_company = sender["company_id"]
        if recipient is not None:
            recipient_company_id = recipient["company_id"]
        language = self.lang(sender_company)
        channel = channel or self.channel_for(letter_type, confidentiality, amount)
        recipient_name = recipient["full_name"] if recipient is not None else customer["contact_name"]
        body = self.compose(language, recipient_name, paragraphs, sender, channel, moment)
        level = CONFIDENTIALITY_LEVELS[confidentiality]
        roles = (sender["role_code"], (recipient or {}).get("role_code"))
        if confidentiality == "confidential" and ("executive" in roles or letter_type in ("confidential_tip", "rumor")):
            level = 3
        low, high = TRUST_EFFECTS[letter_type]
        intel = {"public": (0, 8), "internal": (10, 35), "confidential": (40, 75)}[confidentiality]
        intel_value = self.rng.randint(*intel) + (min(20, int(math.log10(amount + 1) * 2)) if amount else 0)
        if letter_type in ("confidential_tip", "rumor"):
            intel_value += 10
        letter = Letter(
            key=len(self.letters) + 1, sent_at=moment, letter_type=letter_type, sender_company_id=sender_company,
            sender_employee_id=sender["employee_id"], recipient_company_id=recipient_company_id,
            recipient_employee_id=recipient["employee_id"] if recipient is not None else None,
            recipient_customer_id=customer["customer_id"] if customer is not None else None,
            subject=subject, body=body, channel=channel, direction=direction, confidentiality=confidentiality,
            min_intel_access_level=level, sentiment=sentiment or SENTIMENT_BY_TYPE[letter_type],
            refs={key: (refs or {}).get(key) for key in REFERENCE_KEYS},
            amount=round(amount, 2) if amount is not None else None,
            due_date=due_date, response_required=response_required, trust_effect=self.rng.randint(low, high),
            is_accurate=is_accurate, intel_value=int(clamp(intel_value, 0, 100)),
            reply_to=reply_to.key if reply_to else None,
            thread=(reply_to.thread if reply_to else (thread.thread if thread else None)),
            refers_to=refers_to.key if refers_to else None, leaked_by=leaked_by, leaked_to=leaked_to,
            storyline=storyline, copies=list(copies or []))
        if letter.thread is None:
            letter.thread = letter.key
        self.letters.append(letter)
        self.by_key[letter.key] = letter
        if claim is not None:
            self.claimed.add(claim)
        return letter

    def subject(self, letter_type: str, language: str, detail: str) -> str:
        """Betreff aus Briefart und Bezug."""
        return f"{TYPE_LABELS[letter_type][lang_index(language)]}: {detail}"

    # -- Rahmenverträge -----------------------------------------------------------------------------------
    def framework_terms(self, framework: dict[str, Any], language: str) -> str:
        """Eckdaten eines Rahmenvertrags in der Briefsprache."""
        idx = lang_index(language)
        fid = framework["framework_agreement_id"]
        categories = sorted({e["category_code"] for e in self.scope if e["framework_agreement_id"] == fid
                             and e["entry_kind"] == "include" and e["valid_from"] <= framework["start_date"]})
        scope_text = ", ".join(CATEGORY_LABELS[c][idx] for c in categories) or "–"
        index_code = framework["price_index_category"]
        index_category = CATEGORY_LABELS[index_code][idx] if index_code else ""
        index_label = INDEXATION_LABELS[framework["indexation"]][idx].format(category=index_category)
        pct = framework["cost_plus_pct"]
        if pct is None:
            pct = framework["base_discount_pct"] or 0
        formula = PRICE_FORMULA_TEXTS[framework["price_formula"]][idx].format(
            index=index_label, cap=fmt_number(framework["adjustment_cap_pct"] or 5, language),
            pct=fmt_number(pct, language))
        exclusivity = EXCLUSIVITY_LABELS[framework["exclusivity"]][idx]
        start = self.day_text(framework["start_date"], language)
        volume = self.money(framework["base_volume"], language)
        if idx == 0:
            return (f"Sortiment: {scope_text}. Laufzeit {framework['term_months']} Monate ab {start}, Rahmenvolumen "
                    f"{volume}. Preisbildung: {formula}. Exklusivität: {exclusivity}. Kündigungsfrist "
                    f"{framework['notice_period_days']} Tage.")
        return (f"Scope: {scope_text}. Term {framework['term_months']} months from {start}, framework volume {volume}. "
                f"Pricing: {formula}. Exclusivity: {exclusivity}. Notice period {framework['notice_period_days']} "
                "days.")

    def framework_refs(self, framework: dict[str, Any], **extra: int | None) -> dict[str, int | None]:
        """Bezüge eines Rahmenschreibens."""
        return {"framework_agreement_id": framework["framework_agreement_id"],
                "partnership_id": framework["partnership_id"], **extra}

    def framework_letter(self, framework: dict[str, Any], letter_type: str, moment: datetime | None,
                         sender: dict[str, Any] | None, recipient: dict[str, Any] | None, *,
                         reply_to: Letter | None = None, extra: list[str] | None = None,
                         storyline: str | None = None, claim: tuple[Any, ...] | None = None) -> Letter | None:
        """Verhandlungs- oder Bestätigungsschreiben zu einem Rahmenvertrag."""
        if sender is None or recipient is None or moment is None:
            return None
        language = self.lang(sender["company_id"])
        de = language == "de_DE"
        number, title = framework["agreement_number"], framework["title"]
        seller = framework["company_id"]
        from_seller = sender["company_id"] == seller
        terms = self.framework_terms(framework, language)
        partner = self.name(recipient["company_id"])
        if letter_type == "inquiry":
            text = ("für die kommenden Jahre möchten wir unsere Abrufe bei Ihnen in einem Rahmenvertrag bündeln. "
                    f"Bitte senden Sie uns ein Angebot für „{title}“ (Arbeitsnummer {number})." if de else
                    "we would like to bundle our future call-offs with you in a framework agreement. Please send us "
                    f"an offer for “{title}” (working number {number}).")
            paragraphs = [text]
        elif letter_type == "offer":
            paragraphs = [(f"gern unterbreiten wir der {partner} unser Angebot zum Rahmenvertrag {number} „{title}“."
                           if de else f"We are pleased to offer {partner} the framework agreement {number} “{title}”."),
                          terms]
        elif letter_type == "counter_offer":
            if from_seller:
                text = (f"Ihre Rückmeldung zu {number} haben wir geprüft. Am Preisgerüst halten wir fest, kommen Ihnen "
                        "aber beim Zahlungsziel (45 statt 30 Tage) und bei den Abrufmengen entgegen." if de else
                        f"We have reviewed your feedback on {number}. We keep the pricing, but offer 45 instead of 30 "
                        "days payment terms and more flexible call-off quantities.")
            else:
                text = (f"zu Ihrem Angebot {number} schlagen wir vor: Kündigungsfrist und Vertragsstrafe bleiben, "
                        f"dafür bitten wir um {fmt_number(self.rng.choice((1.5, 2.0, 2.5, 3.0)), language, 1)} % "
                        "Nachlass auf die Listenpreise der ersten zwölf Monate." if de else
                        f"regarding your offer {number}, we propose to keep notice period and penalty clause, but ask "
                        f"for a {fmt_number(self.rng.choice((1.5, 2.0, 2.5, 3.0)), language, 1)}% discount on list "
                        "prices for the first twelve months.")
            paragraphs = [text]
        else:  # contract_confirmation zum Vertragsstart
            signed = self.day_text(framework["signed_date"], language)
            start = self.day_text(framework["start_date"], language)
            paragraphs = [(f"mit dem heutigen Tag beginnt der am {signed} unterzeichnete Rahmenvertrag {number} "
                           f"„{title}“. Wir bestätigen die vereinbarten Bedingungen:" if de else
                           f"today the framework agreement {number} “{title}”, signed on {signed}, takes effect "
                           f"({start}). We confirm the agreed terms:"), terms]
        paragraphs += extra or []
        direction = "seller_to_buyer" if from_seller else "buyer_to_seller"
        confidentiality = "confidential" if letter_type in ("offer", "counter_offer") else "internal"
        return self.add(moment=moment, letter_type=letter_type, sender=sender, recipient=recipient,
                        subject=self.subject(letter_type, language, f"{number} – {title}"), paragraphs=paragraphs,
                        direction=direction, confidentiality=confidentiality, refs=self.framework_refs(framework),
                        amount=framework["base_volume"] if letter_type == "offer" else None,
                        response_required=int(letter_type in ("inquiry", "offer", "counter_offer")),
                        reply_to=reply_to, storyline=storyline, claim=claim)

    def framework_thread(self, framework: dict[str, Any]) -> None:
        """Anfrage → Angebot → 0–2 Gegenangebote vor der Unterzeichnung, Bestätigung zum Vertragsstart."""
        fid = framework["framework_agreement_id"]
        seller, buyer = framework["company_id"], framework["partner_company_id"]
        signed = date.fromisoformat(framework["signed_date"])
        last: Letter | None = None
        if ("fw_thread", fid) not in self.claimed:
            day = signed - timedelta(days=self.rng.randint(24, 30))  # frühestens Beginn − 60 T (Einstellungsgrenzen)
            moment = self.at(day)
            buyer_contact = self.pick(buyer, moment, "relations", salt=seller)
            seller_contact = self.pick(seller, moment, "relations", salt=buyer)
            last = self.framework_letter(framework, "inquiry", moment, buyer_contact, seller_contact,
                                         claim=("fw_thread", fid))
            day += timedelta(days=self.rng.randint(3, 6))
            moment = self.at(day)
            last = self.framework_letter(framework, "offer", moment, self.pick(seller, moment, "executive"),
                                         buyer_contact, reply_to=last) or last
            trust = self.partnerships[framework["partnership_id"]]["trust_level"]
            rounds = 2 if trust < 60 else self.rng.choice((0, 1, 1))
            for round_no in range(rounds):
                day += timedelta(days=self.rng.randint(3, 6))
                if day >= signed - timedelta(days=1) or last is None:
                    break
                moment = self.at(day)
                side, other = (buyer, seller) if round_no % 2 == 0 else (seller, buyer)
                sender = self.pick(side, moment, "relations", salt=other)
                recipient = self.person(last.sender_employee_id, other, moment, "relations", salt=side)
                counter = self.framework_letter(framework, "counter_offer", moment, sender, recipient, reply_to=last)
                last = counter or last
        if ("fw_confirm", fid) not in self.claimed:
            start = date.fromisoformat(framework["start_date"])
            if start >= GAME_REFERENCE_DATE:
                return
            moment = self.at(start)
            sender = self.person(framework["buyer_signatory_id"], buyer, moment, "executive")
            recipient = self.person(framework["seller_signatory_id"], seller, moment, "executive")
            copies = [(e["employee_id"], "cc") for e in (self.pick(buyer, moment, "relations", salt=seller),)
                      if e is not None and sender is not None and e["employee_id"] != sender["employee_id"]]
            letter = self.framework_letter(framework, "contract_confirmation", moment, sender, recipient,
                                           reply_to=last, claim=("fw_confirm", fid))
            if letter is not None:
                letter.copies += copies

    # -- Nachträge ------------------------------------------------------------------------------------------
    def amendment_summary(self, amendment: dict[str, Any], language: str) -> str:
        """Inhalt eines Nachtrags (Vorlage AMENDMENT_TEXTS) in der Briefsprache."""
        idx = lang_index(language)
        aid = amendment["amendment_id"]
        entries = [e for e in self.scope if aid in (e["added_by_amendment_id"], e["removed_by_amendment_id"])]
        codes = [(e["category_code"], e["archetype_code"]) for e in entries]
        if not codes and (amendment["category_code"] or amendment["archetype_code"]):
            codes = [(amendment["category_code"], amendment["archetype_code"])]
        names = []
        for category, archetype in dict.fromkeys(codes):
            if archetype:
                names.append(getattr(ARCHETYPES_BY_CODE[archetype], "name_de" if idx == 0 else "name_en"))
            elif category:
                names.append(CATEGORY_LABELS[category][idx])
        joiner = " und " if idx == 0 else " and "
        items = joiner.join([", ".join(names[:-1]), names[-1]]) if len(names) > 1 else (names[0] if names else "")
        system_id = amendment["exclusive_system_id"]
        system_name = self.world.systems_by_id[system_id]["name"] if system_id else ""
        system_suffix = ((f" im System {system_name}" if idx == 0 else f" in the {system_name} system")
                         if system_name else "")
        trigger = ""
        if amendment["trigger_contract_id"]:
            contract = self.contracts[amendment["trigger_contract_id"]]
            note = "rule" if amendment["rule"] else "anchor"
            trigger = AMENDMENT_RULE_NOTES[amendment["rule"] if note == "rule" else "anchor"][idx].format(
                contract=contract["contract_number"])
        escort = amendment["escort_company_id"]
        pct = amendment["price_change_pct"]
        return AMENDMENT_TEXTS[amendment["amendment_type"]][idx].format(
            effective=self.day_text(amendment["effective_date"], language),
            before=fmt_number(amendment["volume_before"] or 0, language),
            after=fmt_number(amendment["volume_after"] or 0, language),
            items=items or ("das gesamte Sortiment" if idx == 0 else "the entire scope"),
            items_suffix=((" für " if idx == 0 else " for ") + items) if items else "",
            pct=fmt_number(pct, language, 1) if pct is not None else "0",
            end=self.day_text(amendment["end_date_new"], language) if amendment["end_date_new"] else "",
            exclusivity=EXCLUSIVITY_LABELS[amendment["exclusivity"] or "right_of_first_refusal"][idx],
            system_suffix=system_suffix, escort=self.name(escort) if escort else "", trigger=trigger)

    def amendment_letters(self, amendment: dict[str, Any], *, offer_sender: int | None = None,
                          offer_recipient: int | None = None, reply_sender: int | None = None,
                          reply_recipient: int | None = None, offer_type: str | None = None,
                          extra_offer: list[str] | None = None, extra_reply: list[str] | None = None,
                          thread: Letter | None = None, refers_to: Letter | None = None,
                          refs: dict[str, int | None] | None = None,
                          storyline: str | None = None) -> tuple[Letter | None, Letter | None]:
        """Angebot des Initiators am Angebotsdatum; Bestätigung (Unterzeichnung) oder Ablehnung der Gegenseite."""
        aid = amendment["amendment_id"]
        framework = self.frameworks[amendment["framework_agreement_id"]]
        seller, buyer = framework["company_id"], framework["partner_company_id"]
        initiator = amendment["initiated_by_company_id"]
        other = buyer if initiator == seller else seller
        kind = amendment["amendment_type"]
        heavy = kind in ("suspension", "partial_termination")
        letter_type = offer_type or {"suspension": "suspension_notice",
                                     "partial_termination": "termination_notice"}.get(kind, "amendment_offer")
        confidentiality = ("confidential" if kind in ("price_adjustment", "suspension", "partial_termination",
                                                      "volume_reduction", "exclusivity_clause", "exclusivity_waiver",
                                                      "escort_clause", "confidentiality_clause") else "internal")
        offer = reply = None
        # Auslösende Verträge beginnen oft erst nach dem Nachtrag: sie stehen im Text, nicht als Bezug
        refs = {**self.framework_refs(framework, amendment_id=aid, event_id=amendment["trigger_event_id"]),
                **(refs or {})}
        if ("amend_offer", aid) not in self.claimed:
            moment = self.at(date.fromisoformat(amendment["proposed_date"]))
            sender = self.person(offer_sender, initiator, moment, "executive" if heavy else "relations", salt=other,
                                 note=f"{storyline or amendment['amendment_number']} Angebot")
            recipient = self.person(offer_recipient, other, moment, "executive" if heavy else "relations",
                                    salt=initiator, note=f"{storyline or amendment['amendment_number']} Angebot")
            if sender is not None and recipient is not None:
                language = self.lang(initiator)
                de = language == "de_DE"
                summary = self.amendment_summary(amendment, language)
                head = (f"zum Rahmenvertrag {framework['agreement_number']} schlagen wir den Nachtrag "
                        f"{amendment['amendment_number']} vor:" if de else
                        f"for framework agreement {framework['agreement_number']} we propose amendment "
                        f"{amendment['amendment_number']}:")
                if letter_type == "suspension_notice":
                    head = (f"hiermit setzen wir den Rahmenvertrag {framework['agreement_number']} aus (Nachtrag "
                            f"{amendment['amendment_number']}):" if de else
                            f"we hereby suspend framework agreement {framework['agreement_number']} (amendment "
                            f"{amendment['amendment_number']}):")
                elif letter_type == "termination_notice":
                    head = (f"hiermit kündigen wir den Rahmenvertrag {framework['agreement_number']} teilweise "
                            f"(Nachtrag {amendment['amendment_number']}, Kündigungsfrist "
                            f"{framework['notice_period_days']} Tage):" if de else
                            f"we hereby give partial notice on framework agreement {framework['agreement_number']} "
                            f"(amendment {amendment['amendment_number']}, notice period "
                            f"{framework['notice_period_days']} days):")
                effective = self.day_text(amendment["effective_date"], language)
                ask = (f"Wir bitten um Gegenzeichnung bis zum {effective}." if de else
                       f"Please countersign by {effective}.")
                paragraphs = [head, summary, *(extra_offer or []), ask]
                direction = "seller_to_buyer" if initiator == seller else "buyer_to_seller"
                volume = None
                if amendment["volume_after"] is not None and amendment["volume_before"] is not None:
                    volume = abs(amendment["volume_after"] - amendment["volume_before"])
                offer = self.add(moment=moment, letter_type=letter_type, sender=sender, recipient=recipient,
                                 subject=self.subject(letter_type, language,
                                                      f"{amendment['amendment_number']} ({framework['title']})"),
                                 paragraphs=paragraphs, direction=direction, confidentiality=confidentiality,
                                 refs=refs, amount=volume, response_required=1, thread=thread, refers_to=refers_to,
                                 storyline=storyline, claim=("amend_offer", aid))
        if ("amend_reply", aid) in self.claimed or amendment["status"] == "proposed":
            return offer, None
        if amendment["status"] == "signed":
            day = date.fromisoformat(amendment["signed_date"])
            reply_type = "amendment_confirmation"
        else:
            day = date.fromisoformat(amendment["proposed_date"]) + timedelta(days=self.rng.randint(3, 9))
            day = min(day, date.fromisoformat(amendment["effective_date"]), GAME_REFERENCE_DATE - timedelta(days=1))
            reply_type = "amendment_rejection"
        moment = self.at(day, earliest=offer.sent_at if offer else None)
        if moment is None:
            return offer, None
        sender = self.person(reply_sender, other, moment, "executive" if heavy else "relations", salt=initiator,
                             note=f"{storyline or amendment['amendment_number']} Antwort")
        original = self.employees.get(offer.sender_employee_id) if offer else None
        recipient = self.person(reply_recipient or (original["employee_id"] if original else None), initiator, moment,
                                "relations", salt=other, note=f"{storyline or amendment['amendment_number']} Antwort")
        if sender is None or recipient is None:
            return offer, None
        language = self.lang(other)
        de = language == "de_DE"
        if reply_type == "amendment_confirmation":
            text = (f"wir zeichnen den Nachtrag {amendment['amendment_number']} zum Rahmenvertrag "
                    f"{framework['agreement_number']} gegen; er wird am "
                    f"{self.day_text(amendment['effective_date'], language)} wirksam." if de else
                    f"we countersign amendment {amendment['amendment_number']} to framework agreement "
                    f"{framework['agreement_number']}; it takes effect on "
                    f"{self.day_text(amendment['effective_date'], language)}.")
        else:
            text = (f"den Nachtrag {amendment['amendment_number']} zum Rahmenvertrag {framework['agreement_number']} "
                    "lehnen wir ab. Die bisherigen Bedingungen gelten unverändert weiter." if de else
                    f"we decline amendment {amendment['amendment_number']} to framework agreement "
                    f"{framework['agreement_number']}. The existing terms remain in force.")
        reply = self.add(moment=moment, letter_type=reply_type, sender=sender, recipient=recipient,
                         subject=self.subject(reply_type, language, amendment["amendment_number"]),
                         paragraphs=[text, *(extra_reply or [])],
                         direction="seller_to_buyer" if other == seller else "buyer_to_seller",
                         confidentiality=confidentiality, refs=refs, reply_to=offer,
                         thread=thread if offer is None else None, storyline=storyline, claim=("amend_reply", aid))
        return offer, reply

    # -- Einzelverträge ---------------------------------------------------------------------------------------
    def contract_refs(self, contract: dict[str, Any], **extra: int | None) -> dict[str, int | None]:
        """Bezüge eines Vertragsschreibens (Vertrag, Rahmen, Vereinbarung)."""
        partnership = self.active_pair.get((contract["company_id"], contract["partner_company_id"]))
        return {"contract_id": contract["contract_id"], "framework_agreement_id": contract["framework_agreement_id"],
                "partnership_id": partnership["partnership_id"] if partnership else None, **extra}

    def contract_confirmation(self, contract: dict[str, Any]) -> None:
        """Vertragsbestätigung des Verkäufers zum Vertragsstart (Exklusivlieferungen und große Abrufverträge)."""
        cid = contract["contract_id"]
        start = date.fromisoformat(contract["start_date"])
        if ("contract_confirm", cid) in self.claimed or start >= GAME_REFERENCE_DATE:
            return
        seller, buyer = contract["company_id"], contract["partner_company_id"]
        moment = self.at(start)
        sender = self.pick(seller, moment, "relations", salt=buyer)
        recipient = self.pick(buyer, moment, "relations", salt=seller)
        language = self.lang(seller)
        de = language == "de_DE"
        line = self.contract_line(contract, language)
        deadline = self.day_text(contract["deadline"], language)
        text = (f"wir bestätigen den heute beginnenden Vertrag {line}. Liefertermin ist der {deadline}, vereinbart "
                f"sind {self.money(contract['agreed_price_per_unit'], language)} je Einheit, Gesamtwert "
                f"{self.money(contract['total_value'], language)}. Bei Verzug fallen "
                f"{self.money(contract['penalty_per_day'], language)} je Tag an." if de else
                f"we confirm contract {line}, starting today. Delivery is due by {deadline} at "
                f"{self.money(contract['agreed_price_per_unit'], language)} per unit, total value "
                f"{self.money(contract['total_value'], language)}. Late delivery incurs "
                f"{self.money(contract['penalty_per_day'], language)} per day.")
        paragraphs = [text]
        if contract["framework_agreement_id"]:
            number = self.frameworks[contract["framework_agreement_id"]]["agreement_number"]
            paragraphs.append(f"Der Vertrag wird auf den Rahmenvertrag {number} angerechnet." if de else
                              f"The contract counts against framework agreement {number}.")
        self.add(moment=moment, letter_type="contract_confirmation", sender=sender, recipient=recipient,
                 subject=self.subject("contract_confirmation", language, contract["contract_number"]),
                 paragraphs=paragraphs, direction="seller_to_buyer", refs=self.contract_refs(contract),
                 amount=contract["total_value"], claim=("contract_confirm", cid))

    def contract_offer(self, contract: dict[str, Any], *, day: date | None = None, sender_id: int | None = None,
                       recipient_id: int | None = None, inquiry: bool = False, storyline: str | None = None,
                       extra: list[str] | None = None) -> Letter | None:
        """Angebot zu einem Vertrag (Entwürfe 2060, Stichprobe der Spotverträge mit vorheriger Anfrage)."""
        cid = contract["contract_id"]
        if ("contract_offer", cid) in self.claimed:
            return None
        seller, buyer = contract["company_id"], contract["partner_company_id"]
        start = date.fromisoformat(contract["start_date"])
        first: Letter | None = None
        if inquiry:
            moment = self.at(start - timedelta(days=self.rng.randint(5, 12)))
            asker = self.pick(buyer, moment, "station", station_id=contract["destination_station_id"], salt=seller)
            answerer = self.pick(seller, moment, "relations", salt=buyer)
            language = self.lang(buyer)
            de = language == "de_DE"
            product = self.product_label(contract["product_id"])
            text = (f"wir benötigen kurzfristig {fmt_number(contract['quantity'], language)} "
                    f"{self.unit(contract['product_id'], language)} {product} für "
                    f"{self.station_name(contract['destination_station_id'])}, Lieferung bis "
                    f"{self.day_text(contract['deadline'], language)}. Bitte nennen Sie uns Preis und "
                    "Termin." if de else
                    f"we need {fmt_number(contract['quantity'], language)} "
                    f"{self.unit(contract['product_id'], language)} of {product} for "
                    f"{self.station_name(contract['destination_station_id'])} at short notice, delivery by "
                    f"{self.day_text(contract['deadline'], language)}. Please quote price and date.")
            first = self.add(moment=moment, letter_type="inquiry", sender=asker, recipient=answerer,
                             subject=self.subject("inquiry", language, product),
                             paragraphs=[text],
                             direction="buyer_to_seller", confidentiality="public",
                             refs={"partnership_id": self.contract_refs(contract)["partnership_id"]},
                             response_required=1)
            if first is None:
                return None
            day = (first.sent_at + timedelta(days=self.rng.randint(1, 3))).date()
            if day >= start:
                day = start - timedelta(days=1)
        if day is None:
            latest = min(start - timedelta(days=7), GAME_REFERENCE_DATE - timedelta(days=1))
            earliest = max(latest - timedelta(days=50), date(2059, 9, 1))
            day = random_date(self.rng, min(earliest, latest), latest)
        moment = self.at(day, earliest=first.sent_at if first else None)
        sender = (self.person(sender_id, seller, moment, "relations", salt=buyer, note=storyline or "Angebot")
                  if moment else None)
        if moment is None:
            recipient = None
        elif first is not None:
            recipient = self.person(first.sender_employee_id, buyer, moment, "station", salt=seller)
        else:
            recipient = self.person(recipient_id, buyer, moment, "relations", salt=seller, note=storyline or "Angebot")
        language = self.lang(seller)
        de = language == "de_DE"
        line = self.contract_line(contract, language)
        text = (f"wir bieten Ihnen den Vertrag {line} an: {self.money(contract['agreed_price_per_unit'], language)} je "
                f"Einheit, Gesamtwert {self.money(contract['total_value'], language)}, Beginn "
                f"{self.day_text(contract['start_date'], language)}, Liefertermin "
                f"{self.day_text(contract['deadline'], language)}." if de else
                f"we offer you contract {line}: {self.money(contract['agreed_price_per_unit'], language)} per unit, "
                f"total value {self.money(contract['total_value'], language)}, start "
                f"{self.day_text(contract['start_date'], language)}, delivery by "
                f"{self.day_text(contract['deadline'], language)}.")
        offer = self.add(moment=moment, letter_type="offer", sender=sender, recipient=recipient,
                         subject=self.subject("offer", language, contract["contract_number"]),
                         paragraphs=[text, *(extra or [])], direction="seller_to_buyer",
                         refs=self.contract_refs(contract), amount=contract["total_value"], response_required=1,
                         reply_to=first, storyline=storyline, claim=("contract_offer", cid))
        return offer

    def offer_reply(self, offer: Letter, contract: dict[str, Any], letter_type: str, *, day: date | None = None,
                    sender_id: int | None = None, storyline: str | None = None,
                    extra: list[str] | None = None) -> Letter | None:
        """Gegenangebot oder Absage des Käufers auf ein Vertragsangebot."""
        buyer = contract["partner_company_id"]
        day = day or (offer.sent_at + timedelta(days=self.rng.randint(2, 8))).date()
        moment = self.at(day, earliest=offer.sent_at)
        if moment is None:
            return None
        sender = self.person(sender_id or offer.recipient_employee_id, buyer, moment, "relations",
                             salt=contract["company_id"], note=storyline or "Antwort")
        recipient = self.person(offer.sender_employee_id, contract["company_id"], moment, "relations", salt=buyer)
        language = self.lang(buyer)
        de = language == "de_DE"
        number = contract["contract_number"]
        if letter_type == "counter_offer":
            pct = fmt_number(self.rng.choice((3, 4, 5, 6, 8)), language)
            text = (f"zu Ihrem Angebot {number}: Menge und Termin passen, beim Preis erwarten wir {pct} % weniger."
                    if de else f"regarding your offer {number}: quantity and date work for us, but we expect a price "
                               f"{pct}% lower.")
        else:
            text = (f"vielen Dank für Ihr Angebot {number}. Wir nehmen es derzeit nicht an." if de else
                    f"thank you for your offer {number}. We will not accept it at this time.")
        return self.add(moment=moment, letter_type=letter_type, sender=sender, recipient=recipient,
                        subject=self.subject(letter_type, language, number),
                        paragraphs=[text, *(extra or [])], direction="buyer_to_seller",
                        confidentiality="confidential" if letter_type == "counter_offer" else "internal",
                        refs=self.contract_refs(contract), reply_to=offer, storyline=storyline,
                        response_required=int(letter_type == "counter_offer"))

    def contract_activity_end(self, contract: dict[str, Any]) -> datetime | None:
        """Letzter Abflug bzw. letzte Ankunft der nicht stornierten Abrufe eines Vertrags."""
        moments = []
        for order in self.orders_by_contract[contract["contract_id"]]:
            if order["status"] == "cancelled":
                continue
            moments.append(datetime.fromisoformat(order["order_date"]))
            shipment = self.shipment_by_order.get(order["order_id"])
            if shipment:
                moments.append(datetime.fromisoformat(shipment["actual_arrival_date"] or shipment["arrival_date"]))
        return max(moments) if moments else None

    def contract_termination(self, contract: dict[str, Any], *, sender_side: int | None = None,
                             storyline: str | None = None, extra: list[str] | None = None) -> Letter | None:
        """Kündigung (Storno) eines Vertrags nach dem letzten Abruf, innerhalb der Laufzeit."""
        cid = contract["contract_id"]
        if ("termination", cid) in self.claimed:
            return None
        start = to_datetime(date.fromisoformat(contract["start_date"]))
        activity = self.contract_activity_end(contract)
        earliest = max(start, activity) if activity else start
        latest = min(to_datetime(date.fromisoformat(contract["deadline"])) + timedelta(days=1), GAME_REFERENCE_DATETIME)
        if earliest + timedelta(days=1) >= latest:
            return None
        day = random_date(self.rng, (earliest + timedelta(days=1)).date(), (latest - timedelta(days=1)).date())
        moment = self.at(day, earliest=earliest)
        side = sender_side or self.rng.choice((contract["company_id"], contract["partner_company_id"]))
        other = contract["partner_company_id"] if side == contract["company_id"] else contract["company_id"]
        sender = self.pick(side, moment, "relations", salt=other) if moment else None
        recipient = self.pick(other, moment, "relations", salt=side) if moment else None
        language = self.lang(side)
        de = language == "de_DE"
        line = self.contract_line(contract, language)
        text = (f"hiermit kündigen wir den Vertrag {line} zum heutigen Tag. Offene Restmengen werden nicht mehr "
                "abgerufen; bereits gelieferte Mengen rechnen wir wie vereinbart ab." if de else
                f"we hereby terminate contract {line} with immediate effect. Remaining quantities will not be called "
                "off; quantities already delivered are invoiced as agreed.")
        return self.add(moment=moment, letter_type="termination_notice", sender=sender, recipient=recipient,
                        subject=self.subject("termination_notice", language, contract["contract_number"]),
                        paragraphs=[text, *(extra or [])],
                        direction="seller_to_buyer" if side == contract["company_id"] else "buyer_to_seller",
                        refs=self.contract_refs(contract), storyline=storyline, claim=("termination", cid))

    # -- Lieferungen ------------------------------------------------------------------------------------------
    def shipment_refs(self, order: dict[str, Any], shipment: dict[str, Any]) -> dict[str, int | None]:
        """Bezüge eines Lieferschreibens."""
        contract = self.contracts.get(order["contract_id"]) if order["contract_id"] else None
        refs = self.contract_refs(contract) if contract else {
            "partnership_id": (self.active_pair.get((order["company_id"], order["customer_company_id"])) or {}).get(
                "partnership_id")}
        return {**refs, "order_id": order["order_id"], "shipment_id": shipment["shipment_id"]}

    def delay_hours(self, shipment: dict[str, Any]) -> float:
        """Verspätung gegenüber der geplanten Ankunft (bei noch offenen Lieferungen bis zum Stichtag)."""
        planned = datetime.fromisoformat(shipment["arrival_date"])
        actual = (datetime.fromisoformat(shipment["actual_arrival_date"]) if shipment["actual_arrival_date"]
                  else max(GAME_REFERENCE_DATETIME, planned))
        return (actual - planned).total_seconds() / 3600

    def delivery_notice(self, order: dict[str, Any], *, day: date | None = None, sender_id: int | None = None,
                        recipient_id: int | None = None, storyline: str | None = None) -> Letter | None:
        """Lieferavis des Verkäufers beim Abflug."""
        shipment = self.shipment_by_order[order["order_id"]]
        if ("delivery", shipment["shipment_id"]) in self.claimed:
            return None
        departure = datetime.fromisoformat(shipment["departure_date"])
        moment = (self.at(day, earliest=departure) if day else
                  departure + timedelta(minutes=self.rng.randint(30, 360)))
        if moment is None or moment >= GAME_REFERENCE_DATETIME:
            return None
        seller, buyer = order["company_id"], order["customer_company_id"]
        sender = self.person(sender_id, seller, moment, "logistics", station_id=order["origin_station_id"], salt=buyer,
                             note=storyline or "Lieferavis")
        recipient = self.person(recipient_id, buyer, moment, "station", station_id=order["destination_station_id"],
                                salt=seller, note=storyline or "Lieferavis")
        language = self.lang(seller)
        de = language == "de_DE"
        eta = self.day_text(shipment["arrival_date"], language)
        text = (f"die Lieferung {shipment['shipment_number']} zur Bestellung {self.order_line(order, language)} hat "
                f"{self.station_name(order['origin_station_id'])} mit der {shipment['ship_name']} verlassen. Geplante "
                f"Ankunft in {self.station_name(order['destination_station_id'])}: {eta}." if de else
                f"shipment {shipment['shipment_number']} for order {self.order_line(order, language)} has left "
                f"{self.station_name(order['origin_station_id'])} aboard the {shipment['ship_name']}. Estimated "
                f"arrival at {self.station_name(order['destination_station_id'])}: {eta}.")
        return self.add(moment=moment, letter_type="delivery_notice", sender=sender, recipient=recipient,
                        subject=self.subject("delivery_notice", language, shipment["shipment_number"]),
                        paragraphs=[text], direction="seller_to_buyer", confidentiality="public",
                        refs=self.shipment_refs(order, shipment), amount=order["total_amount"], storyline=storyline,
                        claim=("delivery", shipment["shipment_id"]))

    def delay_notice(self, order: dict[str, Any], *, day: date | None = None, sender_id: int | None = None,
                     recipient_id: int | None = None, reply_to: Letter | None = None, storyline: str | None = None,
                     extra: list[str] | None = None) -> Letter | None:
        """Verzögerungsmeldung des Verkäufers (geplante Ankunft; bei Ankunft nach dem Stichtag unterwegs)."""
        shipment = self.shipment_by_order[order["order_id"]]
        if ("delay_notice", shipment["shipment_id"]) in self.claimed or not shipment["risk_incident"]:
            return None
        departure = datetime.fromisoformat(shipment["departure_date"])
        planned = datetime.fromisoformat(shipment["arrival_date"])
        if day is not None:
            moment = self.at(day, earliest=departure)
        elif planned < GAME_REFERENCE_DATETIME:
            moment = planned - timedelta(minutes=self.rng.randint(20, 240))
            moment = max(moment, departure + timedelta(minutes=10))
        else:
            span = (GAME_REFERENCE_DATETIME - departure).total_seconds() / 60
            moment = departure + timedelta(minutes=self.rng.uniform(0.3, 0.9) * span) if span > 30 else None
        if moment is None or moment >= GAME_REFERENCE_DATETIME:
            return None
        moment = moment.replace(second=0, microsecond=0)
        seller, buyer = order["company_id"], order["customer_company_id"]
        sender = self.person(sender_id, seller, moment, "logistics", station_id=order["origin_station_id"], salt=buyer,
                             note=storyline or "Verzögerung")
        recipient = self.person(recipient_id, buyer, moment, "station", station_id=order["destination_station_id"],
                                salt=seller, note=storyline or "Verzögerung")
        if reply_to is not None:
            recipient = self.person(reply_to.sender_employee_id, buyer, moment, "station",
                                    station_id=order["destination_station_id"], salt=seller)
        language = self.lang(seller)
        de = language == "de_DE"
        text = (f"die Lieferung {shipment['shipment_number']} (Bestellung {order['order_number']}) verzögert sich: "
                f"{shipment['risk_incident']}. Ursprünglich geplante Ankunft: "
                f"{self.day_text(shipment['arrival_date'], language)}. Wir halten Sie auf dem Laufenden." if de else
                f"shipment {shipment['shipment_number']} (order {order['order_number']}) is delayed: "
                f"{shipment['risk_incident']}. Originally scheduled arrival: "
                f"{self.day_text(shipment['arrival_date'], language)}. We will keep you posted.")
        return self.add(moment=moment, letter_type="delay_notice", sender=sender, recipient=recipient,
                        subject=self.subject("delay_notice", language, shipment["shipment_number"]),
                        paragraphs=[text, *(extra or [])], direction="seller_to_buyer",
                        confidentiality="internal" if reply_to else "public",
                        refs=self.shipment_refs(order, shipment), reply_to=reply_to, storyline=storyline,
                        claim=("delay_notice", shipment["shipment_id"]))

    def delay_complaint(self, order: dict[str, Any], *, day: date | None = None, sender_id: int | None = None,
                        recipient_id: int | None = None, storyline: str | None = None,
                        extra: list[str] | None = None) -> Letter | None:
        """Verzugsbeschwerde des Käufers nach Ankunft der verspäteten Lieferung (offen: nach geplanter Ankunft)."""
        shipment = self.shipment_by_order[order["order_id"]]
        key = ("complaint", order["contract_id"]) if order["contract_id"] else ("complaint_order", order["order_id"])
        if key in self.claimed:
            return None
        if shipment["actual_arrival_date"]:
            earliest = datetime.fromisoformat(shipment["actual_arrival_date"])
        else:
            earliest = datetime.fromisoformat(shipment["arrival_date"]) + timedelta(hours=12)
        if day is not None:
            moment = self.at(day, earliest=earliest)
        else:
            moment = earliest + timedelta(minutes=self.rng.randint(45, 36 * 60))
        if moment is None or moment >= GAME_REFERENCE_DATETIME:
            return None
        moment = moment.replace(second=0, microsecond=0)
        seller, buyer = order["company_id"], order["customer_company_id"]
        sender = self.person(sender_id, buyer, moment, "station", station_id=order["destination_station_id"],
                             salt=seller, note=storyline or "Beschwerde")
        recipient = self.person(recipient_id, seller, moment, "relations", salt=buyer, note=storyline or "Beschwerde")
        language = self.lang(buyer)
        de = language == "de_DE"
        hours = fmt_number(self.delay_hours(shipment), language)
        contract = self.contracts.get(order["contract_id"]) if order["contract_id"] else None
        reference = (f"zum Vertrag {self.contract_line(contract, language)}" if de else
                     f"under contract {self.contract_line(contract, language)}") if contract else (
            f"zur Bestellung {self.order_line(order, language)}" if de
            else f"for order {self.order_line(order, language)}")
        if shipment["actual_arrival_date"] and self.delay_hours(shipment) < 1 and contract:
            arrived = self.day_text(shipment["actual_arrival_date"], language)
            text = (f"mit der Lieferung {shipment['shipment_number']} {reference} am {arrived} ist die Vertragsfrist "
                    "überschritten." if de else
                    f"with shipment {shipment['shipment_number']} {reference} arriving on {arrived}, the contract "
                    "deadline has been missed.")
        elif shipment["actual_arrival_date"]:
            text = (f"die Lieferung {shipment['shipment_number']} {reference} ist erst am "
                    f"{self.day_text(shipment['actual_arrival_date'], language)} eingetroffen, {hours} Stunden nach "
                    "dem zugesagten Termin. Die Verzögerung hat unsere Abläufe in "
                    f"{self.station_name(order['destination_station_id'])} empfindlich gestört." if de else
                    f"shipment {shipment['shipment_number']} {reference} only arrived on "
                    f"{self.day_text(shipment['actual_arrival_date'], language)}, {hours} hours behind schedule. The "
                    "delay has seriously disrupted operations at "
                    f"{self.station_name(order['destination_station_id'])}.")
        else:
            text = (f"die Lieferung {shipment['shipment_number']} {reference} sollte am "
                    f"{self.day_text(shipment['arrival_date'], language)} eintreffen und ist bis heute nicht "
                    "angekommen." if de
                    else f"shipment {shipment['shipment_number']} {reference} was due on "
                         f"{self.day_text(shipment['arrival_date'], language)} and has still not arrived.")
        if contract and contract["status"] == "breached":
            text += (f" Die Frist {self.day_text(contract['deadline'], language)} ist damit überschritten; wir "
                     "behalten uns die vereinbarte Vertragsstrafe vor." if de else
                     f" The deadline of {self.day_text(contract['deadline'], language)} has passed; we reserve the "
                     "right to the agreed contractual penalty.")
        return self.add(moment=moment, letter_type="delay_complaint", sender=sender, recipient=recipient,
                        subject=self.subject("delay_complaint", language, shipment["shipment_number"]),
                        paragraphs=[text, *(extra or [])], direction="buyer_to_seller",
                        refs=self.shipment_refs(order, shipment), response_required=1, storyline=storyline, claim=key)

    def late_contract_shipment(self, contract: dict[str, Any]) -> dict[str, Any] | None:
        """Maßgebliche verspätete Abruflieferung: bei Bruch die letzte, sonst die erste über 48 h."""
        orders = [o for o in self.orders_by_contract[contract["contract_id"]]
                  if o["order_id"] in self.shipment_by_order]
        if not orders:
            return None
        if contract["status"] == "breached":
            def arrival(order: dict[str, Any]) -> str:
                shipment = self.shipment_by_order[order["order_id"]]
                return shipment["actual_arrival_date"] or "9999"
            return max(orders, key=lambda o: (arrival(o), o["order_id"]))
        late = [o for o in orders if self.delay_hours(self.shipment_by_order[o["order_id"]]) > LATE_COMPLAINT_HOURS
                and (self.shipment_by_order[o["order_id"]]["actual_arrival_date"] or o["status"] == "delayed")]
        if not late:
            return None
        return min(late, key=lambda o: (self.shipment_by_order[o["order_id"]]["arrival_date"], o["order_id"]))

    # -- Vertragsstrafen --------------------------------------------------------------------------------------
    def penalty_notice(self, contract: dict[str, Any], *, day: date | None = None, sender_id: int | None = None,
                       recipient_id: int | None = None, storyline: str | None = None,
                       extra: list[str] | None = None) -> Letter | None:
        """Strafbescheid des Käufers: Verzugstage × penalty_per_day (Formel wie generate_financials)."""
        cid = contract["contract_id"]
        booking = self.penalties.get(cid)
        if ("penalty", cid) in self.claimed or booking is None or booking["amount"] <= 0:
            return None
        complaint = next((letter for letter in reversed(self.letters) if letter.letter_type == "delay_complaint"
                          and letter.refs["contract_id"] == cid), None)
        earliest = max(booking["last_arrival"], complaint.sent_at if complaint else booking["last_arrival"])
        if day is None:
            day = min(booking["last_arrival"].date() + timedelta(days=self.rng.randint(3, 14)),
                      GAME_REFERENCE_DATE - timedelta(days=1))
        moment = self.at(day, earliest=earliest)
        if moment is None:
            return None
        seller, buyer = contract["company_id"], contract["partner_company_id"]
        amount = booking["amount"]
        heavy = amount > EXECUTIVE_PENALTY_THRESHOLD
        sender = self.person(sender_id, buyer, moment, "executive" if heavy else "finance", salt=seller,
                             note=storyline or "Strafbescheid")
        recipient = self.person(recipient_id, seller, moment, "executive" if heavy else "finance", salt=buyer,
                                note=storyline or "Strafbescheid")
        language = self.lang(buyer)
        de = language == "de_DE"
        line = self.contract_line(contract, language)
        days = booking["late_days"]
        per_day = self.money(booking["penalty_per_day"], language)
        due = fmt_date(moment + timedelta(days=30))
        if booking["in_transit"]:
            status = ("Die Lieferung ist bis heute nicht vollständig eingetroffen; die Strafe ist bis zum "
                      f"{self.day_text(booking['last_arrival'], language)} berechnet." if de else
                      "Delivery is still incomplete; the penalty is calculated up to "
                      f"{self.day_text(booking['last_arrival'], language)}.")
        else:
            arrived = self.day_text(booking["last_arrival"], language)
            status = (f"Die letzte Teillieferung traf am {arrived} ein." if de else
                      f"The last partial delivery arrived on {arrived}.")
        text = (f"der Vertrag {line} war bis zum {self.day_text(contract['deadline'], language)} zu erfüllen. {status} "
                f"Für {days} Verzugstage zu je {per_day} setzen wir die vertraglich vereinbarte Strafe fest: {days} × "
                f"{per_day} = {self.money(amount, language)}." if de else
                f"contract {line} was due by {self.day_text(contract['deadline'], language)}. {status} For {days} days "
                f"of delay at {per_day} each, we assess the agreed contractual penalty: {days} × {per_day} = "
                f"{self.money(amount, language)}.")
        ask = (f"Bitte begleichen Sie den Betrag bis zum {self.day_text(due, language)}." if de else
               f"Please settle the amount by {self.day_text(due, language)}.")
        return self.add(moment=moment, letter_type="penalty_notice", sender=sender, recipient=recipient,
                        subject=self.subject("penalty_notice", language, contract["contract_number"]),
                        paragraphs=[text, *(extra or []), ask], direction="buyer_to_seller",
                        confidentiality="confidential" if heavy else "internal", refs=self.contract_refs(contract),
                        amount=amount, due_date=due, response_required=1, thread=complaint,
                        sentiment="hostile" if amount > 500_000 else "negative", storyline=storyline,
                        claim=("penalty", cid))

    def penalty_memo(self, penalty: Letter, contract: dict[str, Any]) -> Letter | None:
        """Interne Notiz des Verkäufers bei Strafen über 250.000 CR (Finanzbuchhaltung an Vorstand)."""
        seller = contract["company_id"]
        moment = self.at((penalty.sent_at + timedelta(days=self.rng.randint(0, 2))).date(), earliest=penalty.sent_at)
        if moment is None:
            return None
        sender = self.pick(seller, moment, "finance")
        recipient = self.pick(seller, moment, "executive")
        if sender is None or recipient is None or sender["employee_id"] == recipient["employee_id"]:
            return None
        language = self.lang(seller)
        de = language == "de_DE"
        text = (f"{self.name(contract['partner_company_id'])} fordert für {contract['contract_number']} "
                f"{self.money(penalty.amount or 0, language)} Vertragsstrafe. Die Forderung ist rechnerisch korrekt; "
                "ich empfehle, sie zu begleichen und die Disposition der Strecke "
                f"{self.station_name(contract['origin_station_id'])} – "
                f"{self.station_name(contract['destination_station_id'])} zu prüfen." if de else
                f"{self.name(contract['partner_company_id'])} claims {self.money(penalty.amount or 0, language)} in "
                f"penalties for {contract['contract_number']}. The claim is arithmetically correct; I recommend paying "
                f"it and reviewing dispatch on the {self.station_name(contract['origin_station_id'])} – "
                f"{self.station_name(contract['destination_station_id'])} lane.")
        return self.add(moment=moment, letter_type="internal_memo", sender=sender, recipient=recipient,
                        subject=self.subject("internal_memo", language, contract["contract_number"]),
                        paragraphs=[text], direction="internal", confidentiality="confidential",
                        refs={"contract_id": contract["contract_id"]}, amount=penalty.amount, refers_to=penalty)

    # -- Mahnungen --------------------------------------------------------------------------------------------
    def payment_reminders(self, order: dict[str, Any], *, days: tuple[date | None, ...] | None = None,
                          sender_id: int | None = None, recipient_id: int | None = None,
                          storyline: str | None = None, skip: frozenset[int] = frozenset()) -> list[Letter]:
        """Mahnstufen zu einer überfälligen Bestellung: Fälligkeit (Ankunft + 30 T) + 3..7 / +21 / +45 T."""
        shipment = self.shipment_by_order.get(order["order_id"])
        if order["payment_status"] != "overdue" or shipment is None or not shipment["actual_arrival_date"]:
            return []
        due = datetime.fromisoformat(shipment["actual_arrival_date"]).date() + timedelta(days=PAYMENT_TERMS_DAYS)
        seller = order["company_id"]
        letters: list[Letter] = []
        previous: Letter | None = None
        for stage, (low, high) in enumerate(REMINDER_STAGE_DAYS):
            if stage in skip or ("reminder", order["order_id"], stage) in self.claimed:
                continue
            day = days[stage] if days and days[stage] else due + timedelta(days=self.rng.randint(low, high))
            if day >= GAME_REFERENCE_DATE:
                break
            moment = self.at(day, earliest=previous.sent_at if previous else None)
            if moment is None:
                break
            sender = self.person(sender_id, seller, moment, "finance", salt=order["customer_id"],
                                 note=storyline or "Mahnung")
            customer = None
            recipient = None
            if order["customer_company_id"]:
                recipient = self.person(recipient_id, order["customer_company_id"], moment, "finance", salt=seller,
                                        note=storyline or "Mahnung")
            else:
                customer = self.customers[order["customer_id"]]
            language = self.lang(seller)
            de = language == "de_DE"
            label = REMINDER_LABELS[stage][lang_index(language)]
            amount = order["total_amount"]
            texts = (
                (f"unsere Rechnung zur Bestellung {self.order_line(order, language)} über "
                 f"{self.money(amount, language)} war am {self.day_text(due, language)} fällig. Sicher handelt es sich "
                 "um ein Versehen – bitte überweisen Sie den Betrag in den nächsten Tagen.",
                 f"our invoice for order {self.order_line(order, language)} over {self.money(amount, language)} was "
                 f"due on {self.day_text(due, language)}. This is surely an oversight – please transfer the amount "
                 "within the next few days."),
                (f"trotz unserer Zahlungserinnerung ist die Rechnung zur Bestellung {order['order_number']} über "
                 f"{self.money(amount, language)} (fällig seit {self.day_text(due, language)}) weiter offen. Wir "
                 "bitten um Ausgleich innerhalb von zehn Tagen.",
                 f"despite our reminder, the invoice for order {order['order_number']} over "
                 f"{self.money(amount, language)} (due since {self.day_text(due, language)}) is still unpaid. Please "
                 "settle within ten days."),
                (f"die Rechnung zur Bestellung {order['order_number']} über {self.money(amount, language)} ist seit "
                 f"{self.day_text(due, language)} überfällig. Geht die Zahlung nicht binnen sieben Tagen ein, liefern "
                 "wir nur noch gegen Vorkasse und übergeben die Forderung dem Inkasso.",
                 f"the invoice for order {order['order_number']} over {self.money(amount, language)} has been overdue "
                 f"since {self.day_text(due, language)}. Unless payment is received within seven days, we will only "
                 "deliver against prepayment and refer the claim to collection."),
            )
            letter = self.add(moment=moment, letter_type="payment_reminder", sender=sender, recipient=recipient,
                              recipient_company_id=order["customer_company_id"], customer=customer,
                              subject=f"{label}: {order['order_number']}",
                              paragraphs=[texts[stage][lang_index(language)]],
                              direction="seller_to_buyer", confidentiality="internal",
                              refs={"order_id": order["order_id"], "contract_id": order["contract_id"],
                                    "shipment_id": shipment["shipment_id"]},
                              amount=amount, due_date=fmt_date(due), response_required=1, thread=previous,
                              sentiment=("neutral", "negative", "hostile")[stage], storyline=storyline,
                              claim=("reminder", order["order_id"], stage))
            if letter is not None:
                letters.append(letter)
                previous = letter
        return letters

    # -- Abmahnungen, Ereignisse, Rivalitäten -----------------------------------------------------------------
    def repeat_breach_warning(self, framework: dict[str, Any], penalty: Letter, count: int) -> Letter | None:
        """Abmahnung des Käufers nach dem zweiten (vierten, …) Vertragsbruch innerhalb eines Rahmens."""
        seller, buyer = framework["company_id"], framework["partner_company_id"]
        moment = self.at((penalty.sent_at + timedelta(days=self.rng.randint(1, 4))).date(), earliest=penalty.sent_at)
        if moment is None:
            return None
        sender = self.pick(buyer, moment, "executive")
        recipient = self.pick(seller, moment, "executive")
        language = self.lang(buyer)
        de = language == "de_DE"
        number = framework["agreement_number"]
        text = (f"mit {self.contracts[penalty.refs['contract_id']]['contract_number']} ist bereits der {count}. Abruf "
                f"aus dem Rahmenvertrag {number} verspätet und gebrochen. Wir mahnen die Einhaltung der Liefertermine "
                "ausdrücklich ab. Im Wiederholungsfall prüfen wir eine Teilkündigung des Rahmens." if de else
                f"{self.contracts[penalty.refs['contract_id']]['contract_number']} is already call-off no. {count} "
                f"under framework agreement {number} to be late and in breach. We formally insist on the agreed "
                "delivery dates. Should this recur, we will consider a partial termination of the framework.")
        return self.add(moment=moment, letter_type="breach_warning", sender=sender, recipient=recipient,
                        subject=self.subject("breach_warning", language, number), paragraphs=[text],
                        direction="buyer_to_seller", confidentiality="confidential",
                        refs=self.framework_refs(framework, contract_id=penalty.refs["contract_id"]),
                        response_required=1, refers_to=penalty)

    def event_memo(self, event: dict[str, Any], *, day: date | None = None, sender_id: int | None = None,
                   recipient_id: int | None = None, storyline: str | None = None,
                   extra: list[str] | None = None) -> Letter | None:
        """Interne Notiz der Stationsleitung an den Vorstand nach einem schweren Ereignis."""
        if ("event_memo", event["event_id"]) in self.claimed:
            return None
        station = self.world.stations[event["station_id"]]
        company = station["company_id"]
        event_day = date.fromisoformat(event["event_date"])
        moment = self.at(day or event_day + timedelta(days=self.rng.randint(0, 2)))
        if moment is None:
            return None
        sender = self.person(sender_id, company, moment, "station", station_id=station["station_id"],
                             note=storyline or "Notiz")
        recipient = self.person(recipient_id, company, moment, "executive", note=storyline or "Notiz")
        if sender is None or recipient is None or sender["employee_id"] == recipient["employee_id"]:
            return None
        language = self.lang(company)
        de = language == "de_DE"
        product = self.product_label(event["affected_product_id"]) if event["affected_product_id"] else "–"
        text = (f"Lagebericht: {self.event_label(event, language)} (Schweregrad "
                f"{SEVERITY_LABELS[event['severity']][0]}). Am stärksten betroffen ist {product}, Preiswirkung "
                f"{fmt_number(event['price_impact'] * 100, language, 1)} %, voraussichtliche Dauer "
                f"{event['duration_days']} Tage. Ich bitte um Freigabe, Partner und Kunden mit offenen Abrufen vorab "
                "zu informieren." if de else
                f"Situation report: {self.event_label(event, language)} (severity "
                f"{SEVERITY_LABELS[event['severity']][1]}). Most affected is {product}, price impact "
                f"{fmt_number(event['price_impact'] * 100, language, 1)}%, expected duration {event['duration_days']} "
                "days. Requesting approval to brief partners and customers with open call-offs.")
        return self.add(moment=moment, letter_type="internal_memo", sender=sender, recipient=recipient,
                        subject=self.subject("internal_memo", language, self.event_label(event, language)),
                        paragraphs=[text, *(extra or [])], direction="internal",
                        confidentiality="confidential" if event["severity"] == "critical" else "internal",
                        refs={"event_id": event["event_id"]}, storyline=storyline,
                        claim=("event_memo", event["event_id"]))

    def rivalry_protest(self, rivalry: dict[str, Any]) -> None:
        """Protest des Vorstands an den Vorstand des Rivalen (Anlass: Beginn der Rivalität oder Ereignis im System)."""
        rid = rivalry["rivalry_id"]
        if ("protest", rid) in self.claimed:
            return
        company, rival = rivalry["company_id"], rivalry["rival_company_id"]
        since = date.fromisoformat(rivalry["since_date"])
        stations = self.world.stations
        events = [e for e in self.events.values()
                  if stations[e["station_id"]]["system_id"] == rivalry["contested_system_id"]
                  and stations[e["station_id"]]["company_id"] in (company, rival)
                  and e["severity"] in ("major", "critical") and e["event_date"] >= "2057-01-01"]
        event = events[-1] if events else None
        if event is not None:
            day = date.fromisoformat(event["event_date"]) + timedelta(days=self.rng.randint(2, 10))
        elif since >= date(2057, 1, 1):
            day = since + timedelta(days=self.rng.randint(3, 20))
        else:
            day = random_date(self.rng, date(2058, 6, 1), date(2059, 11, 30))
        moment = self.at(min(day, GAME_REFERENCE_DATE - timedelta(days=2)))
        if moment is None:
            return
        sender = self.pick(company, moment, "executive")
        recipient = self.pick(rival, moment, "executive")
        language = self.lang(company)
        de = language == "de_DE"
        system = self.world.systems_by_id[rivalry["contested_system_id"]]["name"]
        cause = (f" Anlass ist {self.event_label(event, language)}." if de else
                 f" The occasion is {self.event_label(event, language)}.") if event else ""
        text = (f"wir protestieren in aller Form gegen das Vorgehen der {self.name(rival)} im {system}-System.{cause} "
                "Wir fordern Sie auf, Ihre Aktivitäten dort zu unterlassen, und behalten uns alle Schritte "
                "vor." if de else
                f"we formally protest against the conduct of {self.name(rival)} in the {system} system.{cause} We "
                "demand that you cease these activities and reserve all further steps.")
        protest = self.add(moment=moment, letter_type="protest", sender=sender, recipient=recipient,
                           subject=self.subject("protest", language, system), paragraphs=[text], direction="to_rival",
                           confidentiality="public", refs={"rivalry_id": rid,
                                                           "event_id": event["event_id"] if event else None},
                           response_required=1, claim=("protest", rid))
        if protest is not None and self.rng.random() < 0.5:
            self.protest_reply(protest, rivalry)

    def protest_reply(self, protest: Letter, rivalry: dict[str, Any], *, day: date | None = None,
                      sender_id: int | None = None, storyline: str | None = None,
                      extra: list[str] | None = None) -> Letter | None:
        """Antwort des Rivalen auf einen Protest."""
        rival = protest.recipient_company_id
        moment = self.at(day or (protest.sent_at + timedelta(days=self.rng.randint(3, 10))).date(),
                         earliest=protest.sent_at)
        if moment is None or rival is None:
            return None
        sender = self.person(sender_id or protest.recipient_employee_id, rival, moment, "executive",
                             note=storyline or "Protestantwort")
        language = self.lang(rival)
        de = language == "de_DE"
        text = (f"Ihre Vorwürfe weisen wir zurück. Die {self.name(rival)} handelt im Rahmen ihrer Lizenzen; für "
                f"Verluste der {self.name(protest.sender_company_id)} sind wir nicht verantwortlich." if de else
                f"we reject your allegations. {self.name(rival)} operates within its licences and is not responsible "
                f"for losses incurred by {self.name(protest.sender_company_id)}.")
        return self.add(moment=moment, letter_type="protest", sender=sender,
                        recipient=self.person(protest.sender_employee_id, protest.sender_company_id, moment,
                                              "executive"),
                        subject=self.subject("protest", language, protest.subject.split(": ", 1)[-1]),
                        paragraphs=[text, *(extra or [])], direction="to_rival", confidentiality="public",
                        refs={"rivalry_id": rivalry["rivalry_id"]}, reply_to=protest, storyline=storyline)

    def truth(self) -> int | None:
        """Wahrheitsgehalt eines Gerüchts (30 % wahr, 50 % offen, 20 % falsch)."""
        return weighted_choice(self.rng, RUMOR_TRUTH_SPLIT)

    def rivalry_rumors(self, rivalry: dict[str, Any]) -> None:
        """Gerüchte im Umfeld einer Rivalität: ein Leck-Kandidat der einen Firma steckt der anderen Vertragsinterna."""
        rid = rivalry["rivalry_id"]
        for _ in range(self.rng.randint(2, 4)):
            source, target = ((rivalry["company_id"], rivalry["rival_company_id"]) if self.rng.random() < 0.5
                              else (rivalry["rival_company_id"], rivalry["company_id"]))
            start = max(date.fromisoformat(rivalry["since_date"]), date(2057, 6, 1))
            if start >= date(2059, 12, 20):
                continue
            moment = self.at(random_date(self.rng, start, date(2059, 12, 20)))
            if moment is None:
                continue
            day = fmt_date(moment)
            leakers = [e for e in self.staff[source] if employed_on(e, day) and e["intel_access_level"] >= 1
                       and satisfies_leak_rule(e)]
            contracts = [c for c in self.contracts.values() if source in (c["company_id"], c["partner_company_id"])
                         and c["start_date"] <= day <= c["deadline"] and c["status"] != "draft"]
            if not leakers or not contracts:
                continue
            leaker = self.rng.choice(leakers)
            contract = self.rng.choice(contracts)
            recipient = self.pick(target, moment, "intelligence", salt=source)
            accuracy = self.truth()
            language = self.lang(source)
            de = language == "de_DE"
            factor = 1.0 if accuracy != 0 else self.rng.uniform(1.3, 1.8)
            value = self.money(contract["total_value"] * factor, language)
            partner = contract["partner_company_id"] if contract["company_id"] == source else contract["company_id"]
            text = (f"unter uns: Der Vertrag {contract['contract_number']} mit der {self.name(partner)} ist {value} "
                    "schwer und wackelt. Man spricht intern von Nachverhandlung – wer jetzt ein besseres Angebot "
                    "macht, hat gute Chancen." if de else
                    f"between us: contract {contract['contract_number']} with {self.name(partner)} is worth {value} "
                    "and on shaky ground. Internally there is talk of renegotiation – a better offer now stands a "
                    "good chance.")
            self.add(moment=moment, letter_type="rumor", sender=leaker, recipient=recipient,
                     subject=self.subject("rumor", language, contract["contract_number"]), paragraphs=[text],
                     direction="to_rival", confidentiality="confidential",
                     refs={"rivalry_id": rid, "contract_id": contract["contract_id"]}, is_accurate=accuracy,
                     leaked_by=leaker["employee_id"], leaked_to=target)

    # -- Lecks vertraulicher Schreiben --------------------------------------------------------------------------
    def leak_letters(self) -> None:
        """Vertrauliche Schreiben können über Leck-Kandidaten an Rivalen gelangen (Formel aus correspondence_design).

        Wahrscheinlichkeit = espionage_risk/100 × Bestechlichkeit/100 × (1 − Loyalität/150), gedämpft mit LEAK_SCALE.
        Der Tipp geht an die Marktaufklärung des Rivalen und verweist auf das Original.
        """
        for original in list(self.letters):
            if (original.confidentiality != "confidential" or original.leak_status != "none"
                    or original.letter_type in ("confidential_tip", "rumor")):
                continue
            day = fmt_date(original.sent_at)
            for side in dict.fromkeys(c for c in (original.sender_company_id, original.recipient_company_id) if c):
                rivals = self.rivalries_of[side]
                if not rivals:
                    continue
                rivalry = self.rng.choice(rivals)
                rival = rivalry["rival_company_id"] if rivalry["company_id"] == side else rivalry["company_id"]
                pool = [e for e in self.staff[side] if employed_on(e, day) and satisfies_leak_rule(e)
                        and e["intel_access_level"] >= original.min_intel_access_level]
                if not pool:
                    continue
                leaker = self.rng.choice(pool)
                probability = (rivalry["espionage_risk"] / 100 * leaker["bribe_susceptibility"] / 100
                               * (1 - leaker["loyalty"] / 150) * LEAK_SCALE)
                if self.rng.random() >= probability:
                    continue
                moment = self.at((original.sent_at + timedelta(days=self.rng.randint(1, 12))).date(),
                                 earliest=original.sent_at)
                if moment is None or not employed_on(leaker, fmt_date(moment)):
                    continue
                recipient = self.pick(rival, moment, "intelligence", salt=side)
                if recipient is None:
                    continue
                tip = self.rng.random() < 0.65
                accuracy = 1 if tip else self.truth()
                letter = self.leak_message(original, leaker, recipient, moment, tip, accuracy, rivalry)
                if letter is not None:
                    original.leak_status = "leaked" if tip else "rumored"
                    original.leaked_by, original.leaked_to = leaker["employee_id"], rival
                    break

    def leak_message(self, original: Letter, leaker: dict[str, Any], recipient: dict[str, Any], moment: datetime,
                     tip: bool, accuracy: int | None, rivalry: dict[str, Any] | None,
                     storyline: str | None = None, extra: list[str] | None = None) -> Letter | None:
        """Tipp oder Gerücht über ein vertrauliches Schreiben."""
        language = self.lang(leaker["company_id"])
        de = language == "de_DE"
        sender_name = self.name(original.sender_company_id)
        target_name = self.name(original.recipient_company_id) if original.recipient_company_id else "–"
        amount = original.amount
        if amount and accuracy == 0:
            amount *= self.rng.uniform(1.3, 1.8)
        amount_text = ""
        if amount:
            value = self.money(amount, language)
            amount_text = f" Es geht um {value}." if de else f" The amount is {value}."
        kind = TYPE_LABELS[original.letter_type][lang_index(language)]
        if tip:
            text = (f"mir liegt ein vertrauliches Schreiben vor: {kind} der {sender_name} an die {target_name} vom "
                    f"{self.day_text(original.sent_at, language)}, Betreff „{original.subject}“.{amount_text} Eine "
                    "Kopie kann ich beschaffen – gegen die übliche Anerkennung." if de else
                    f"I have seen a confidential letter: {kind} from {sender_name} to {target_name}, dated "
                    f"{self.day_text(original.sent_at, language)}, subject “{original.subject}”.{amount_text} I can "
                    "obtain a copy – for the usual consideration.")
        else:
            text = (f"man hört, zwischen der {sender_name} und der {target_name} gebe es Ärger: {kind} vom "
                    f"{self.day_text(original.sent_at, language)}.{amount_text} Bestätigen kann ich das "
                    "noch nicht." if de else
                    f"word is there is trouble between {sender_name} and {target_name}: {kind} dated "
                    f"{self.day_text(original.sent_at, language)}.{amount_text} I cannot confirm it yet.")
        letter_type = "confidential_tip" if tip else "rumor"
        refs = {key: original.refs[key] for key in ("contract_id", "framework_agreement_id", "event_id", "order_id")}
        refs["rivalry_id"] = rivalry["rivalry_id"] if rivalry else None
        return self.add(moment=moment, letter_type=letter_type, sender=leaker, recipient=recipient,
                        subject=self.subject(letter_type, language, original.subject.split(": ", 1)[-1]),
                        paragraphs=[text, *(extra or [])], direction="to_rival" if rivalry else "lateral",
                        confidentiality="confidential", refs=refs, amount=amount, is_accurate=accuracy,
                        leaked_by=leaker["employee_id"], leaked_to=recipient["company_id"], refers_to=original,
                        storyline=storyline)

    # -- Abschluss --------------------------------------------------------------------------------------------
    def finalize(self) -> None:
        """Vergibt IDs und Nummern chronologisch, löst Bezüge auf und setzt Lese- und Bearbeitungsstatus."""
        world = self.world
        ordered = sorted(self.letters, key=lambda letter: (letter.sent_at, letter.key))
        ids = {letter.key: number for number, letter in enumerate(ordered, start=1)}
        replies: dict[int, list[Letter]] = defaultdict(list)
        followers: dict[int, list[Letter]] = defaultdict(list)
        for letter in ordered:
            if letter.reply_to is not None:
                replies[letter.reply_to].append(letter)
            if letter.thread != letter.key:
                followers[letter.thread].append(letter)
        counters: dict[tuple[int, int], int] = defaultdict(int)
        for letter in ordered:
            company = world.companies[letter.sender_company_id]
            language = company["language"]
            counters[(letter.sender_company_id, letter.sent_at.year)] += 1
            serial = counters[(letter.sender_company_id, letter.sent_at.year)]
            number = (f"{world.profiles[letter.sender_company_id].sku_prefix}-{CORRESPONDENCE_PREFIX[language]}-"
                      f"{letter.sent_at.year}-{serial:05d}")
            delay_hours = {"holo_call": 0.0, "encrypted_message": self.rng.uniform(0.1, 12),
                           "email": self.rng.uniform(0.3, 48), "letter": self.rng.uniform(20, 120)}[letter.channel]
            read_at = letter.sent_at + timedelta(hours=delay_hours)
            if letter.channel == "holo_call":
                read_at = letter.sent_at
            elif (GAME_REFERENCE_DATETIME - letter.sent_at).days < 20 and self.rng.random() < 0.1:
                read_at = None  # liegt zum Stichtag ungelesen im Postfach
            if read_at is not None and read_at >= GAME_REFERENCE_DATETIME:
                read_at = None
            answers = replies.get(letter.key, [])
            if any(a.letter_type in ("offer_rejection", "amendment_rejection") for a in answers):
                status = "rejected"
            elif answers:
                status = "answered"
            elif letter.letter_type == "payment_reminder" and any(
                    f.letter_type == "payment_reminder" and f.sent_at > letter.sent_at
                    for f in [self.by_key[letter.thread], *followers.get(letter.thread, [])]):
                status = "escalated"
            elif letter.letter_type in ("contract_confirmation", "amendment_confirmation", "delivery_notice",
                                        "internal_memo") and read_at is not None:
                status = "closed"
            else:
                status = "read" if read_at is not None else "sent"
            if read_at is None and status in ("answered", "rejected", "closed"):
                read_at = min((a.sent_at for a in answers), default=letter.sent_at)
                read_at = max(read_at, letter.sent_at)
            sender_station = (self.employees[letter.sender_employee_id]["station_id"] if letter.sender_employee_id
                              else None)
            row = world.add("correspondence", {
                "correspondence_number": number,
                "correspondence_type": letter.letter_type,
                "channel": letter.channel,
                "direction": letter.direction,
                "thread_id": ids[letter.thread],
                "in_reply_to_id": ids[letter.reply_to] if letter.reply_to is not None else None,
                "refers_to_correspondence_id": ids[letter.refers_to] if letter.refers_to is not None else None,
                "sent_at": fmt_dt(letter.sent_at),
                "is_read": int(read_at is not None),
                "read_at": fmt_dt(read_at) if read_at is not None else None,
                "sender_company_id": letter.sender_company_id,
                "sender_employee_id": letter.sender_employee_id,
                "sender_station_id": sender_station,
                "recipient_company_id": letter.recipient_company_id,
                "recipient_employee_id": letter.recipient_employee_id,
                "recipient_customer_id": letter.recipient_customer_id,
                "language": language,
                "subject": letter.subject,
                "body": letter.body,
                "confidentiality": letter.confidentiality,
                "min_intel_access_level": letter.min_intel_access_level,
                "sentiment": letter.sentiment,
                "amount": letter.amount,
                "due_date": letter.due_date,
                "response_required": letter.response_required,
                "status": status,
                "trust_effect": letter.trust_effect,
                "is_accurate": letter.is_accurate,
                "intel_value": letter.intel_value,
                "leak_status": letter.leak_status,
                "leaked_by_employee_id": letter.leaked_by,
                "leaked_to_company_id": letter.leaked_to,
                **letter.refs,
                "storyline_code": letter.storyline,
            })
            assert row["correspondence_id"] == ids[letter.key]
            seen = {letter.sender_employee_id, letter.recipient_employee_id}
            for employee_id, copy_type in letter.copies:
                if employee_id in seen:
                    continue
                seen.add(employee_id)
                world.add("correspondence_copies", {"correspondence_id": row["correspondence_id"],
                                                    "employee_id": employee_id, "copy_type": copy_type})


def escort_breaches(desk: CorrespondenceDesk, company_ids: set[int], until: str) -> list[dict[str, Any]]:
    """Gebrochene Verträge zwischen den Firmen, deren Abrufe wegen abgewarteten Geleitschutzes zu spät kamen."""
    hits = []
    for contract in desk.contracts.values():
        if (contract["status"] != "breached" or contract["company_id"] not in company_ids
                or contract["partner_company_id"] not in company_ids):
            continue
        for order in desk.orders_by_contract[contract["contract_id"]]:
            shipment = desk.shipment_by_order.get(order["order_id"])
            incident = (shipment or {}).get("risk_incident") or ""
            arrival = (shipment or {}).get("actual_arrival_date") or "9999"
            if ("Geleitschutz" in incident or "escort" in incident) and arrival[:10] <= until:
                hits.append(contract)
                break
    return sorted(hits, key=lambda c: c["contract_number"])


def overdue_orders(desk: CorrespondenceDesk, seller_id: int, buyer_id: int, day: date) -> list[dict[str, Any]]:
    """Überfällige Bestellungen eines Firmenkunden an einem Tag (Fälligkeit = Ankunft + 30 T)."""
    result = []
    for order in desk.orders.values():
        key = (order["company_id"], order["customer_company_id"], order["payment_status"])
        if key != (seller_id, buyer_id, "overdue"):
            continue
        shipment = desk.shipment_by_order.get(order["order_id"])
        if shipment and shipment["actual_arrival_date"]:
            due = datetime.fromisoformat(shipment["actual_arrival_date"]).date() + timedelta(days=PAYMENT_TERMS_DAYS)
            if due < day:
                result.append(order)
    return sorted(result, key=lambda o: o["order_number"])


def add_storylines(desk: CorrespondenceDesk) -> None:
    """Verankerte Vorgänge V1–V41 (Entscheidung Phase 2, Abschnitt 6.3) mit echten Bestandsobjekten (Seed 42).

    Jeder Vorgang prüft seine Bezugsobjekte und Personen. Fehlt ein Objekt, entfällt der Vorgang; ist eine
    Person am Datum nicht beschäftigt, springt ein Ersatz nach Rolle ein. Abweichungen vom Plan landen in
    `desk.adaptations`. Datumsanpassungen an die Daten (Unterzeichnung = Beginn − 30 T) sind hier vermerkt.
    """
    d = date.fromisoformat
    ids = desk.world.company_ids_by_key
    employee = desk.employees.get
    contract = desk.contract_by_number.get
    order_no = desk.order_by_number.get
    framework = desk.framework_by_number.get
    amendment = desk.amendment_by_number.get
    note = desk.adaptations.append

    def at(day_text: str, earliest: datetime | None = None) -> datetime | None:
        return desk.at(d(day_text), earliest)

    def who(employee_id: int | None, key: str, moment: datetime | None, role: str, code: str,
            station_id: int | None = None) -> dict[str, Any] | None:
        if moment is None:
            return None
        return desk.person(employee_id, ids[key], moment, role, station_id, salt=0, note=code)

    def contact(key: str, moment: datetime | None, role: str, other: str) -> dict[str, Any] | None:
        return desk.pick(ids[key], moment, role, salt=ids[other]) if moment else None

    def missing(code: str, *objects: Any) -> bool:
        if any(o is None for o in objects):
            note(f"{code}: Bezugsobjekt fehlt im Datenstand, Vorgang entfällt")
            return True
        return False

    def order_of(shipment_number: str) -> dict[str, Any] | None:
        shipment = desk.shipment_by_number.get(shipment_number)
        return desk.orders.get(shipment["order_id"]) if shipment else None

    def rivalry(key: str, rival_key: str) -> dict[str, Any] | None:
        return next((r for r in desk.rivalries.values()
                     if (r["company_id"], r["rival_company_id"]) == (ids[key], ids[rival_key])), None)

    def complaint_first(k: dict[str, Any]) -> None:
        late = desk.late_contract_shipment(k)
        if late is not None:
            desk.delay_complaint(late)

    # V1 – Mahnstufen 1–3 Eisenkrone → Feldspat (K4)
    order = order_no("EKM-BST-2057-00352")
    if not missing("V1", order):
        desk.payment_reminders(order, days=(d("2057-08-28"), d("2057-09-13"), d("2057-10-07")), sender_id=169,
                               recipient_id=2, storyline="V1")

    # V2 – Strafbescheid EKM-VTR-2057-0017 und Strafklausel EKM-RV-2057-02/N4
    k, a = contract("EKM-VTR-2057-0017"), amendment("EKM-RV-2057-02/N4")
    if not missing("V2", k, a):
        complaint_first(k)
        penalty = desk.penalty_notice(k, day=d("2057-12-20"), sender_id=293, recipient_id=170, storyline="V2",
                                      extra=["We are attaching a proposal for a stricter penalty clause under "
                                             "framework agreement EKM-RV-2057-02 (amendment EKM-RV-2057-02/N4)."])
        desk.amendment_letters(a, offer_sender=293, offer_recipient=170, thread=penalty, storyline="V2")

    # V3 – Abmahnung nach KI-Ausfall Förster (Ereignis 19), Servicevereinbarung CCI-MSA-2057-01/A1
    fw, a, event = framework("CCI-MSA-2057-01"), amendment("CCI-MSA-2057-01/A1"), desk.events.get(19)
    if not missing("V3", fw, a, event):
        moment = at("2058-02-10")
        warning = desk.add(
            moment=moment, letter_type="breach_warning", sender=who(178, "eisenkrone", moment, "station", "V3"),
            recipient=contact("cindervale", moment, "relations", "eisenkrone"),
            subject=desk.subject("breach_warning", "de_DE", f"{fw['agreement_number']} – Ausfall Förster"),
            paragraphs=[f"am {desk.day_text(event['event_date'], 'de_DE')} ist die KI-Leitsteuerung der "
                        f"{desk.station_name(event['station_id'])} ausgefallen; die Fertigung stand "
                        f"{event['duration_days']} Tage. Die Steuerkerne stammen aus dem Rahmenvertrag "
                        f"{fw['agreement_number']}.",
                        "Wir mahnen die zugesicherte Verfügbarkeit ab und erwarten eine Servicevereinbarung mit "
                        "garantierten Reaktionszeiten. Einen Nachtrag dazu erhalten Sie von unserer "
                        "Partnerbetreuung."],
            direction="buyer_to_seller", confidentiality="confidential",
            refs=desk.framework_refs(fw, event_id=event["event_id"]), response_required=1, storyline="V3")
        desk.amendment_letters(a, offer_sender=170, thread=warning, storyline="V3")

    # V4 – Volumensenkung HMX-MSA-2057-03/A4 nach Ereignis 19
    a = amendment("HMX-MSA-2057-03/A4")
    if not missing("V4", a, event):
        desk.amendment_letters(a, offer_sender=170, offer_recipient=332, reply_sender=332, storyline="V4",
                               extra_offer=["Nach dem Ausfall an der Industriestation Förster brauchen wir 2058 "
                                            "deutlich weniger Vorprodukte aus Sol und Halcyon."])

    # V5 – Ende der Kommission Driftwood → Second Hull
    partnership = desk.active_pair.get((ids["driftwood"], ids["second_hull"])) or next(
        (p for p in desk.partnerships.values() if (p["company_id"], p["partner_company_id"])
         == (ids["driftwood"], ids["second_hull"])), None)
    if not missing("V5", partnership):
        moment = at("2058-04-01")
        desk.add(moment=moment, letter_type="termination_notice",
                 sender=contact("second_hull", moment, "executive", "driftwood"),
                 recipient=who(26, "driftwood", moment, "relations", "V5"),
                 subject=desk.subject("termination_notice", "en_US", "consignment arrangement"),
                 paragraphs=["we hereby give notice to end our consignment arrangement with "
                             f"{desk.name(ids['driftwood'])} as of {desk.day_text(partnership['end_date'], 'en_US')}. "
                             "Salvage lots already in our yards will be settled at the agreed rates.",
                             "Second Hull will source hull scrap in Nyx directly from now on."],
                 direction="buyer_to_seller", refs={"partnership_id": partnership["partnership_id"]}, storyline="V5")

    # V6 – Interne Notiz nach der Söldner-Razzia 26
    event = desk.events.get(26)
    if not missing("V6", event):
        desk.event_memo(event, day=d("2058-07-02"), sender_id=302, recipient_id=293, storyline="V6",
                        extra=[f"The raid was carried out by mercenaries working for {desk.name(ids['ravenmoor'])}. "
                               "Weapons and transit licences were seized; I recommend we talk to Ravenmoor before "
                               "their escort framework is signed."])

    # V7 – Geleitschutzrahmen RCS-MSA-2058-01 (Verhandlung vor der Unterzeichnung 2058-07-02)
    fw = framework("RCS-MSA-2058-01")
    if not missing("V7", fw):
        fid = fw["framework_agreement_id"]
        moment = at("2058-06-12")
        offer = desk.framework_letter(
            fw, "offer", moment, contact("ravenmoor", moment, "executive", "helix"),
            who(304, "helix", moment, "station", "V7"), storyline="V7", claim=("fw_thread", fid),
            extra=["After the pirate attack on Kharon Landing IV (November 2057) we offer armed escorts and frontier "
                   "supplies for the Kharon corridor under one framework."])
        moment = at("2058-06-22")
        counter = desk.framework_letter(fw, "counter_offer", moment, who(304, "helix", moment, "station", "V7"),
                                        desk.employees.get(offer.sender_employee_id) if offer else None,
                                        reply_to=offer, storyline="V7")
        moment = at("2058-08-01")
        desk.framework_letter(fw, "contract_confirmation", moment, who(293, "helix", moment, "executive", "V7"),
                              who(fw["seller_signatory_id"], "ravenmoor", moment, "executive", "V7"),
                              reply_to=counter or offer, storyline="V7", claim=("fw_confirm", fid))
        note("V7: Angebot und Gegenangebot auf 2058-06-12/06-22 vorgezogen (Unterzeichnung 2058-07-02 laut Daten), "
             "Bestätigung zum Vertragsstart 2058-08-01")

    # V8 – Verzugsbeschwerde und Strafbescheid EKM-VTR-2058-0099
    k = contract("EKM-VTR-2058-0099")
    if not missing("V8", k):
        desk.delay_complaint(desk.late_contract_shipment(k), day=d("2058-08-19"), sender_id=45, recipient_id=179,
                             storyline="V8")
        desk.penalty_notice(k, day=d("2058-08-28"), sender_id=40, recipient_id=169, storyline="V8")

    # V9 – Abmahnung Erstandienung Rohstoffe Halcyon (EKM-RV-2057-01) und Antwort Corvane
    fw, k33, k39 = framework("EKM-RV-2057-01"), contract("LAK-VTR-2058-0033"), contract("LAK-VTR-2058-0039")
    if not missing("V9", fw, k33, k39):
        moment = at("2058-08-20")
        warning = desk.add(
            moment=moment, letter_type="breach_warning", sender=who(170, "eisenkrone", moment, "relations", "V9"),
            recipient=who(119, "corvane", moment, "relations", "V9"),
            subject=desk.subject("breach_warning", "de_DE", f"{fw['agreement_number']} – Rohstoffe Halcyon"),
            paragraphs=[f"nach unseren Informationen bezieht die {desk.name(ids['corvane'])} seit dem "
                        f"{desk.day_text(k33['start_date'], 'de_DE')} {desk.product_label(k33['product_id'])} von der "
                        f"{desk.name(ids['lichtacker'])} ({k33['contract_number']}).",
                        f"Rohstoffe für Halcyon sind nach dem Joint-Venture-Liefervertrag {fw['agreement_number']} "
                        "zuerst der Eisenkrone anzufragen. Wir erwarten, dass künftige Rohstoffabrufe wieder über den "
                        "Rahmen laufen."],
            direction="seller_to_buyer", confidentiality="confidential", refs=desk.framework_refs(fw),
            response_required=1, storyline="V9")
        moment = at("2058-10-14")
        desk.add(moment=moment, letter_type="breach_warning", sender=who(119, "corvane", moment, "relations", "V9"),
                 recipient=who(170, "eisenkrone", moment, "relations", "V9"),
                 subject=desk.subject("breach_warning", "en_US", f"Re: {fw['agreement_number']}"),
                 paragraphs=[f"we have reviewed your letter. {k33['contract_number']} covers a grade that was not "
                             f"offered under {fw['agreement_number']}, so we see no breach.",
                             "As a gesture of goodwill, we will not extend the follow-up contract "
                             f"{k39['contract_number']} beyond its current call-offs."],
                 direction="buyer_to_seller", confidentiality="confidential", refs=desk.framework_refs(fw),
                 reply_to=warning, storyline="V9")
        desk.contract_termination(k39, sender_side=ids["corvane"], storyline="V9",
                                  extra=["As announced to Eisenkrone, we are winding down raw material purchases "
                                         "outside our framework agreements."])
        note("V9: Antwort auf 2058-10-14 (nach Beginn von LAK-VTR-2058-0039); die Stornierung folgt laut Daten erst "
             "nach dem letzten Abruf (2059-03-03)")

    # V10 – offenes Gerücht Driftwood → Helix über Ravenmoor
    r = rivalry("ravenmoor", "helix")
    fw = framework("RCS-MSA-2058-01")
    if not missing("V10", r, fw):
        moment = at("2058-09-12")
        desk.add(moment=moment, letter_type="rumor", sender=who(26, "driftwood", moment, "relations", "V10"),
                 recipient=who(293, "helix", moment, "executive", "V10"),
                 subject=desk.subject("rumor", "en_US", "Ravenmoor in Kharon"),
                 paragraphs=["a word of warning from a long-standing partner: Ravenmoor's new escort framework with "
                             f"you ({fw['agreement_number']}) is said to be only a foothold. Their dispatchers are "
                             "reportedly approaching your customers in Kharon directly."],
                 direction="lateral", confidentiality="confidential",
                 refs={"rivalry_id": r["rivalry_id"], "framework_agreement_id": fw["framework_agreement_id"]},
                 is_accurate=None, storyline="V10")

    # V11 – Preisnachlass CCI-MSA-2057-01/A2 nach Ereignis 36
    a, event36 = amendment("CCI-MSA-2057-01/A2"), desk.events.get(36)
    if not missing("V11", a, event36):
        desk.amendment_letters(a, offer_recipient=170, storyline="V11",
                               extra_offer=[f"After the second failure at {desk.station_name(event36['station_id'])} "
                                            f"({desk.day_text(event36['event_date'], 'en_US')}) we offer this price "
                                            "reduction as a gesture of goodwill."])

    # V12 – Volumenerhöhung GFW-RV-2057-01/N3
    a, k173 = amendment("GFW-RV-2057-01/N3"), contract("HMX-CTR-2058-0173")
    if not missing("V12", a, k173):
        desk.amendment_letters(a, offer_sender=332, reply_recipient=332, storyline="V12",
                               extra_offer=[f"After the failed spot delivery {k173['contract_number']} we need "
                                            "additional hull and drive parts in Kharon at short notice."])

    # V13 – Verzugsbeschwerde und Strafbescheid HMX-CTR-2058-0159
    k159, order = contract("HMX-CTR-2058-0159"), order_of("HMX-SHP-2059-01012")
    penalty159 = None
    if not missing("V13", k159, order):
        desk.delay_complaint(order, day=d("2059-01-18"), sender_id=47, recipient_id=332, storyline="V13")
        penalty159 = desk.penalty_notice(k159, day=d("2059-01-25"), sender_id=38, recipient_id=293, storyline="V13")

    # V14 – Gerücht Täsche → Kuppelwerk, Angebot und Absage (Vorkaufsrecht Helix)
    fw1 = framework("HMX-MSA-2057-01")
    partnership = desk.active_pair.get((ids["kuppelwerk"], ids["lichtacker"]))
    kuppel_offer = None
    if not missing("V14", penalty159, fw1, partnership):
        moment = at("2059-01-27", earliest=penalty159.sent_at)
        leaker = who(43, "lichtacker", moment, "intelligence", "V14")
        rumor = desk.add(
            moment=moment, letter_type="rumor", sender=leaker, recipient=contact("kuppelwerk", moment, "intelligence",
                                                                                 "lichtacker"),
            subject=desk.subject("rumor", "de_DE", "Industriegüter Tauvel"),
            paragraphs=[f"unter uns: Für {k159['contract_number']} haben wir der Helix gerade "
                        f"{desk.money(penalty159.amount or 0, 'de_DE')} Vertragsstrafe in Rechnung gestellt. Im "
                        f"Vorstand wächst der Unmut über den Rahmen {fw1['agreement_number']}. Wer jetzt "
                        "Industriegüter anbietet, findet offene Ohren."],
            direction="lateral", confidentiality="confidential",
            refs={"contract_id": k159["contract_id"], "framework_agreement_id": fw1["framework_agreement_id"]},
            amount=penalty159.amount, is_accurate=1, leaked_by=leaker["employee_id"] if leaker else None,
            leaked_to=ids["kuppelwerk"], refers_to=penalty159, storyline="V14")
        if rumor is not None:
            penalty159.leak_status, penalty159.leaked_by = "leaked", rumor.sender_employee_id
            penalty159.leaked_to = ids["kuppelwerk"]
            moment = at("2059-01-28", earliest=rumor.sent_at)
            kuppel_offer = desk.add(
                moment=moment, letter_type="offer", sender=contact("kuppelwerk", moment, "relations", "lichtacker"),
                recipient=who(41, "lichtacker", moment, "relations", "V14"),
                subject=desk.subject("offer", "de_DE", "Verbundstahl und Habitatbaustoffe"),
                paragraphs=["wir hören, dass Ihre Versorgung mit Industriegütern aus Kharon zuletzt holprig war. Die "
                            f"{desk.name(ids['kuppelwerk'])} bietet Verbundstahl und Habitatbaustoffe ab Aurelis zu "
                            "Festpreisen und mit garantierten Lieferfenstern an."],
                direction="seller_to_buyer", refs={"partnership_id": partnership["partnership_id"]},
                response_required=1, storyline="V14")
            moment = at("2059-02-05", earliest=kuppel_offer.sent_at if kuppel_offer else None)
            desk.add(moment=moment, letter_type="offer_rejection",
                     sender=who(41, "lichtacker", moment, "relations", "V14"),
                     recipient=desk.employees.get(kuppel_offer.sender_employee_id) if kuppel_offer else None,
                     subject=desk.subject("offer_rejection", "de_DE", "Verbundstahl und Habitatbaustoffe"),
                     paragraphs=["vielen Dank für Ihr Angebot. Für Industriegüter gilt bis auf Weiteres das "
                                 f"Vorkaufsrecht der {desk.name(ids['helix'])} aus dem Rahmenvertrag "
                                 f"{fw1['agreement_number']}. Wir kommen auf Sie zu, sobald diese Bindung entfällt."],
                     direction="buyer_to_seller", refs={"partnership_id": partnership["partnership_id"]},
                     reply_to=kuppel_offer, storyline="V14")

    # V15 – Helium-3-Verzug HMX-CTR-2058-0131, Strafbescheid, Nachträge A6/A7
    k131, order = contract("HMX-CTR-2058-0131"), order_of("HMX-SHP-2059-01094")
    if not missing("V15", k131, order, amendment("HMX-MSA-2057-02/A6"), amendment("HMX-MSA-2057-02/A7")):
        desk.delay_complaint(order, day=d("2059-03-07"), sender_id=123, recipient_id=308, storyline="V15")
        penalty = desk.penalty_notice(k131, day=d("2059-03-12"), sender_id=115, recipient_id=293, storyline="V15")
        for number in ("HMX-MSA-2057-02/A6", "HMX-MSA-2057-02/A7"):
            desk.amendment_letters(amendment(number), offer_sender=115, offer_recipient=293, reply_sender=293,
                                   reply_recipient=115, thread=penalty, storyline="V15",
                                   extra_offer=[f"After the late Helium-3 deliveries under {k131['contract_number']} "
                                                "we will source Helium-3 for Halcyon elsewhere."])

    # V16 – Abmahnung und Verzicht auf das Vorkaufsrecht HMX-MSA-2057-01/A5
    k139, a = contract("HMX-CTR-2058-0139"), amendment("HMX-MSA-2057-01/A5")
    k043 = contract("HMX-CTR-2057-0043")
    if not missing("V16", k139, a, k043, k159):
        booking = desk.penalties.get(k139["contract_id"])
        moment = at("2059-03-10", earliest=booking["last_arrival"] if booking else None)
        warning = desk.add(
            moment=moment, letter_type="breach_warning", sender=who(41, "lichtacker", moment, "relations", "V16"),
            recipient=who(332, "helix", moment, "relations", "V16"),
            subject=desk.subject("breach_warning", "de_DE", f"{k139['contract_number']} – Vorkaufsrecht"),
            paragraphs=[f"mit {k139['contract_number']} ist nach {k043['contract_number']} und "
                        f"{k159['contract_number']} bereits der dritte Industriegüter-Abruf aus dem Rahmen "
                        f"{fw1['agreement_number']} verspätet.",
                        "Das Vorkaufsrecht der Helix für Industriegüter halten wir unter diesen Umständen nicht mehr "
                        "für zumutbar und schlagen den Verzicht darauf vor."],
            direction="buyer_to_seller", confidentiality="confidential", refs=desk.contract_refs(k139),
            response_required=1, storyline="V16")
        desk.amendment_letters(a, offer_sender=41, offer_recipient=332, reply_sender=332, reply_recipient=41,
                               thread=warning, storyline="V16")

    # V17 – Baustoffrahmen KHB-RV-2059-01 (Gegenangebot vor der Unterzeichnung 2059-03-02)
    fw = framework("KHB-RV-2059-01")
    if not missing("V17", fw):
        fid = fw["framework_agreement_id"]
        moment = at("2059-02-12", earliest=kuppel_offer.sent_at if kuppel_offer else None)
        offer = desk.framework_letter(fw, "offer", moment, contact("kuppelwerk", moment, "executive", "lichtacker"),
                                      who(41, "lichtacker", moment, "relations", "V17"), storyline="V17",
                                      claim=("fw_thread", fid),
                                      extra=["Die Lieferungen beginnen erst, wenn das Vorkaufsrecht der Helix für "
                                             "Industriegüter entfallen ist."])
        moment = at("2059-02-18")
        counter = desk.framework_letter(fw, "counter_offer", moment, who(41, "lichtacker", moment, "relations", "V17"),
                                        desk.employees.get(offer.sender_employee_id) if offer else None,
                                        reply_to=offer, storyline="V17",
                                        extra=["Wir unterzeichnen unter der Bedingung, dass der Rahmen erst am "
                                               f"{desk.day_text(fw['start_date'], 'de_DE')} beginnt; über die "
                                               "Aufhebung des Vorkaufsrechts verhandeln wir mit der Helix."])
        moment = at(fw["start_date"])
        desk.framework_letter(fw, "contract_confirmation", moment, who(38, "lichtacker", moment, "executive", "V17"),
                              who(fw["seller_signatory_id"], "kuppelwerk", moment, "executive", "V17"),
                              reply_to=counter or offer, storyline="V17", claim=("fw_confirm", fid))
        note("V17: Gegenangebot auf 2059-02-18 vorgezogen (Unterzeichnung 2059-03-02 laut Daten)")

    # V18 – Helium-3-Rahmen EFF-MSA-2059-01 (Angebot vor der Unterzeichnung 2059-03-02)
    fw = framework("EFF-MSA-2059-01")
    if not missing("V18", fw):
        fid = fw["framework_agreement_id"]
        moment = at("2059-02-16")
        offer = desk.framework_letter(fw, "offer", moment, contact("emberline", moment, "executive", "corvane"),
                                      who(123, "corvane", moment, "station", "V18"), storyline="V18",
                                      claim=("fw_thread", fid),
                                      extra=["Deliveries can start once your buyer exclusivity for energy under "
                                             "HMX-MSA-2057-02 ends on March 15, 2059."])
        moment = at(fw["start_date"])
        desk.framework_letter(fw, "contract_confirmation", moment, who(115, "corvane", moment, "executive", "V18"),
                              who(fw["seller_signatory_id"], "emberline", moment, "executive", "V18"),
                              reply_to=offer, storyline="V18", claim=("fw_confirm", fid))
        note("V18: Angebot auf 2059-02-16 vorgezogen (Unterzeichnung 2059-03-02 laut Daten)")

    # V19 – Kaltangebot Kometenpost nach dem Verzug HMX-CTR-2059-0197
    k197 = contract("HMX-CTR-2059-0197")
    if not missing("V19", k197):
        moment = at("2059-05-12")
        desk.add(moment=moment, letter_type="offer", sender=contact("kometenpost", moment, "relations", "lichtacker"),
                 recipient=who(49, "lichtacker", moment, "station", "V19"),
                 subject=desk.subject("offer", "de_DE", "Eilkurier nach Tauvel"),
                 paragraphs=[f"die Lieferung {k197['contract_number']} an den "
                             f"{desk.station_name(k197['destination_station_id'])} kam erst nach Fristablauf an – "
                             "davon war im ganzen Sektor zu hören.",
                             f"Die {desk.name(ids['kometenpost'])} bringt Eilsendungen bis 5 t in unter 48 Stunden zu "
                             "Ihren Stationen, zum Festpreis und mit Haftung für Verzug. Wir würden uns über einen "
                             "Probeauftrag freuen."],
                 direction="seller_to_buyer", confidentiality="public", response_required=1, storyline="V19")

    # V20 – vertraulicher Hinweis Outmark → Slavko Geisel (Vorgeschichte zu Fund 52)
    licence = next((p for p in desk.partnerships.values()
                    if (p["company_id"], p["partner_company_id"]) == (ids["outmark"], ids["feldspat"])), None)
    if not missing("V20", licence):
        moment = at("2059-05-20")
        sender = contact("outmark", moment, "intelligence", "feldspat")
        leaked = sender["employee_id"] if sender and satisfies_leak_rule(sender) else None
        desk.add(moment=moment, letter_type="confidential_tip", sender=sender,
                 recipient=who(16, "feldspat", moment, "relations", "V20"),
                 subject=desk.subject("confidential_tip", "en_US", "survey grid Becker"),
                 paragraphs=["our survey drones charted an unusual quartz anomaly near Becker mining station while "
                             "our licence with Feldspat was still running. The data never reached your board. If you "
                             "want the coordinates, they are yours – for a share of the claim."],
                 direction="lateral", confidentiality="confidential",
                 refs={"partnership_id": licence["partnership_id"]},
                 is_accurate=1, leaked_by=leaked, leaked_to=ids["feldspat"] if leaked else None, storyline="V20")

    # V21 – offenes Gerücht Brandon Jones → Ravenmoor (Geleitschutzbrüche)
    r = rivalry("ravenmoor", "helix")
    hits = escort_breaches(desk, set(desk.world.legacy_company_ids()), "2059-06-10")
    own = [h for h in hits if ids["helix"] in (h["company_id"], h["partner_company_id"])]
    if not missing("V21", r, own[-1] if own else None):
        moment = at("2059-06-10")
        leaker = who(445, "helix", moment, "finance", "V21")
        numbers = ", ".join(h["contract_number"] for h in hits)
        desk.add(moment=moment, letter_type="rumor", sender=leaker,
                 recipient=contact("ravenmoor", moment, "intelligence", "helix"),
                 subject=desk.subject("rumor", "en_US", "escort gaps in Kharon"),
                 paragraphs=[f"between us: {len(hits)} contracts in the core network were breached because freighters "
                             f"sat waiting for escorts ({numbers}), {len(own)} of them on Helix lanes. Finance is "
                             "tallying the penalties; nobody upstairs wants to admit the escort gap."],
                 direction="to_rival", confidentiality="confidential",
                 refs={"rivalry_id": r["rivalry_id"], "contract_id": own[-1]["contract_id"]}, is_accurate=None,
                 leaked_by=leaker["employee_id"] if leaker and satisfies_leak_rule(leaker) else None,
                 leaked_to=ids["ravenmoor"], storyline="V21")
        if len(hits) != 8:
            note(f"V21: {len(hits)} statt 8 Geleitschutzbrüche bis 2059-06-10 (der achte, EKM-VTR-2059-0167, bricht "
                 "erst im Oktober 2059)")

    # V22 – Abnahmerahmen Quantenquarz FSP-RV-2059-01 gegen die Schulden (K10)
    fw = framework("FSP-RV-2059-01")
    if not missing("V22", fw):
        fid = fw["framework_agreement_id"]
        moment = at("2059-06-18")
        debts = overdue_orders(desk, ids["eisenkrone"], ids["feldspat"], moment.date()) if moment else []
        offer = desk.framework_letter(
            fw, "offer", moment, who(4, "feldspat", moment, "relations", "V22"),
            who(170, "eisenkrone", moment, "relations", "V22"), storyline="V22", claim=("fw_thread", fid),
            extra=[f"Zur Verrechnung Ihrer offenen Forderungen gegen uns – derzeit {len(debts)} Rechnungen über "
                   f"{desk.money(sum(o['total_amount'] for o in debts), 'de_DE')} – bieten wir Ihnen Quantenquarz "
                   "Becker bevorzugt an."])
        moment = at(fw["start_date"])
        debts = overdue_orders(desk, ids["eisenkrone"], ids["feldspat"], moment.date()) if moment else []
        desk.framework_letter(
            fw, "contract_confirmation", moment, who(168, "eisenkrone", moment, "executive", "V22"),
            who(1, "feldspat", moment, "executive", "V22"), reply_to=offer, storyline="V22", claim=("fw_confirm", fid),
            extra=[f"Unsere offenen Forderungen aus Lieferungen an Sie belaufen sich heute auf {len(debts)} Rechnungen "
                   f"über {desk.money(sum(o['total_amount'] for o in debts), 'de_DE')}; Quarzlieferungen rechnen wir "
                   "dagegen auf."])
        note("V22: Angebot auf 2059-06-18 vorgezogen (Unterzeichnung 2059-07-02 laut Daten); Schuldenstand je "
             "Schreiben aus den überfälligen Bestellungen berechnet")

    # V23 – Preisnachlass RVF-RV-2058-02/N1 und Tipp Bauer → Koch (Fund 52)
    a, event52 = amendment("RVF-RV-2058-02/N1"), desk.events.get(52)
    if not missing("V23", a, event52):
        desk.amendment_letters(a, offer_sender=175, storyline="V23",
                               extra_offer=[f"Nach dem Rohstofffund an der {desk.station_name(event52['station_id'])} "
                                            f"({desk.day_text(event52['event_date'], 'de_DE')}) fallen die Preise in "
                                            "Brennus; wir erwarten eine entsprechende Anpassung."])
        moment = at("2059-08-20")
        leaker = who(170, "eisenkrone", moment, "relations", "V23")
        desk.add(moment=moment, letter_type="confidential_tip", sender=leaker,
                 recipient=who(4, "feldspat", moment, "relations", "V23"),
                 subject=desk.subject("confidential_tip", "de_DE", "Preise Brennus"),
                 paragraphs=[f"unter uns: Die {desk.name(ids['raureif'])} hat uns nach Ihrem Fund an der "
                             f"{desk.station_name(event52['station_id'])} 6 % Nachlass gewährt "
                             f"({a['amendment_number']}). Im Haus wird schon gerechnet, wie viel günstiger "
                             "Quantenquarz Becker werden könnte – halten Sie Ihre Preise."],
                 direction="lateral", confidentiality="confidential", refs={"event_id": event52["event_id"]},
                 is_accurate=1, leaked_by=leaker["employee_id"] if leaker else None, leaked_to=ids["feldspat"],
                 storyline="V23")

    # V24 – Protest Outmark → Feldspat (Fund 52) und Antwort
    r = rivalry("outmark", "feldspat")
    if not missing("V24", r, event52):
        moment = at("2059-07-28")
        protest = desk.add(
            moment=moment, letter_type="protest", sender=contact("outmark", moment, "executive", "feldspat"),
            recipient=who(1, "feldspat", moment, "executive", "V24"),
            subject=desk.subject("protest", "en_US", f"claim at {desk.station_name(event52['station_id'])}"),
            paragraphs=[f"the “discovery” at {desk.station_name(event52['station_id'])} on "
                        f"{desk.day_text(event52['event_date'], 'en_US')} lies squarely on survey grids charted by "
                        "Outmark under our former licence. We demand a share of the claim and reserve all legal "
                        "steps."],
            direction="to_rival", confidentiality="public",
            refs={"rivalry_id": r["rivalry_id"], "event_id": event52["event_id"]}, response_required=1,
            storyline="V24", claim=("protest", r["rivalry_id"]))
        if protest is not None:
            desk.protest_reply(protest, r, day=d("2059-08-05"), sender_id=1, storyline="V24",
                               extra=["Die Lizenz endete im Juni 2058; der Fund beruht auf eigenen Bohrungen."])

    # V25 – Strafbescheid EKM-VTR-2059-0162
    k = contract("EKM-VTR-2059-0162")
    if not missing("V25", k):
        complaint_first(k)
        desk.penalty_notice(k, day=d("2059-08-05"), sender_id=293, recipient_id=168, storyline="V25")

    # V26 – Tipp vor der Razzia 58, Protest Driftwood, interne Verdachtsnotiz
    r, event58 = rivalry("ravenmoor", "driftwood"), desk.events.get(58)
    if not missing("V26", r, event58):
        moment = at("2059-08-27")
        leaker = who(29, "driftwood", moment, "station", "V26")
        tip = desk.add(moment=moment, letter_type="confidential_tip", sender=leaker,
                       recipient=contact("ravenmoor", moment, "intelligence", "driftwood"),
                       subject=desk.subject("confidential_tip", "en_US", desk.station_name(event58["station_id"])),
                       paragraphs=["next week a load of restricted goods is due at "
                                   f"{desk.station_name(event58['station_id'])}. The security grid will be down for "
                                   "maintenance on the night of September 1. Payment as agreed, via the usual "
                                   "channel."],
                       direction="to_rival", confidentiality="confidential", refs={"rivalry_id": r["rivalry_id"]},
                       is_accurate=1, leaked_by=leaker["employee_id"] if leaker else None, leaked_to=ids["ravenmoor"],
                       storyline="V26")
        moment = at("2059-09-03")
        desk.add(moment=moment, letter_type="protest", sender=who(23, "driftwood", moment, "executive", "V26"),
                 recipient=contact("ravenmoor", moment, "executive", "driftwood"),
                 subject=desk.subject("protest", "en_US", f"raid on {desk.station_name(event58['station_id'])}"),
                 paragraphs=[f"on {desk.day_text(event58['event_date'], 'en_US')} armed units in Ravenmoor's pay "
                             f"raided {desk.station_name(event58['station_id'])} and seized cargo belonging to our "
                             "customers. We protest in the strongest terms and will hold Ravenmoor liable for every "
                             "lost credit."],
                 direction="to_rival", confidentiality="public",
                 refs={"rivalry_id": r["rivalry_id"], "event_id": event58["event_id"]}, response_required=1,
                 storyline="V26", claim=("protest", r["rivalry_id"]))
        moment = at("2059-09-10")
        desk.add(moment=moment, letter_type="internal_memo", sender=who(33, "driftwood", moment, "station", "V26"),
                 recipient=who(23, "driftwood", moment, "executive", "V26"),
                 subject=desk.subject("internal_memo", "en_US", "who knew about the raid"),
                 paragraphs=["word on the docks is that someone tipped off Ravenmoor before the raid. Only a handful "
                             "of people knew the maintenance schedule of the security grid – I suggest we start with "
                             "the station managers."],
                 direction="internal", confidentiality="confidential", refs={"event_id": event58["event_id"]},
                 refers_to=tip, storyline="V26")
        note("V26: Gerücht Hines → Gould als interne Notiz umgesetzt (beide Driftwood; firmenintern nur internal_memo)")

    # V27 – Sammelmahnung 2. Stufe Eisenkrone → Feldspat (K3)
    order = order_no("EKM-BST-2059-01903")
    if not missing("V27", order):
        moment = at("2059-10-14")
        debts = overdue_orders(desk, ids["eisenkrone"], ids["feldspat"], moment.date()) if moment else []
        shipment = desk.shipment_by_order[order["order_id"]]
        due = datetime.fromisoformat(shipment["actual_arrival_date"]).date() + timedelta(days=PAYMENT_TERMS_DAYS)
        total = sum(o["total_amount"] for o in debts)
        listed = ", ".join(o["order_number"] for o in debts[-4:])
        desk.add(moment=moment, letter_type="payment_reminder", sender=who(169, "eisenkrone", moment, "finance", "V27"),
                 recipient=who(2, "feldspat", moment, "finance", "V27"),
                 subject=f"{REMINDER_LABELS[1][0]}: Sammelmahnung {len(debts)} Rechnungen",
                 paragraphs=[f"trotz unserer Erinnerungen sind {len(debts)} Rechnungen über zusammen "
                             f"{desk.money(total, 'de_DE')} offen, zuletzt {listed}. Die Rechnung zu "
                             f"{order['order_number']} ist seit dem {desk.day_text(due, 'de_DE')} fällig.",
                             "Wir bitten um Ausgleich innerhalb von zehn Tagen oder um einen verbindlichen "
                             "Zahlungsplan; Quarzlieferungen aus FSP-RV-2059-01 rechnen wir an."],
                 direction="seller_to_buyer",
                 refs={"order_id": order["order_id"], "shipment_id": shipment["shipment_id"]},
                 amount=total, due_date=fmt_date(due), response_required=1, sentiment="negative", storyline="V27",
                 claim=("reminder", order["order_id"], 1))

    # V28 – Seip: Beschwerde, Leck, neuer Energierahmen, Teilkündigung, abgelehnter Preisnachlass
    k167, fw_old, fw_new = contract("EKM-VTR-2059-0167"), framework("EKM-RV-2057-03"), framework("EFF-MSA-2059-02")
    n6, n7 = amendment("EKM-RV-2057-03/N6"), amendment("EKM-RV-2057-03/N7")
    if not missing("V28", k167, fw_old, fw_new, n6, n7):
        complaint = desk.delay_complaint(desk.late_contract_shipment(k167), day=d("2059-10-11"), sender_id=45,
                                         recipient_id=170, storyline="V28")
        moment = at("2059-10-12", earliest=complaint.sent_at if complaint else None)
        leaker = who(83, "lichtacker", moment, "logistics", "V28")
        tip = desk.add(moment=moment, letter_type="confidential_tip", sender=leaker,
                       recipient=contact("emberline", moment, "intelligence", "lichtacker"),
                       subject=desk.subject("confidential_tip", "de_DE", "Energie für Seip"),
                       paragraphs=[f"Seip hat nach {k167['contract_number']} genug von der Eisenkrone: Die "
                                   "Brennstoffzellen kamen zu spät, der Vorstand denkt über eine Teilkündigung der "
                                   "Energieversorgung nach. Ein Angebot für die Agrarstation Seip kommt jetzt auf den "
                                   "richtigen Tisch."],
                       direction="lateral", confidentiality="confidential", refs={"contract_id": k167["contract_id"]},
                       is_accurate=1, leaked_by=leaker["employee_id"] if leaker else None, leaked_to=ids["emberline"],
                       refers_to=complaint, storyline="V28")
        if tip is not None and complaint is not None:
            complaint.leak_status, complaint.leaked_by = "leaked", tip.sender_employee_id
            complaint.leaked_to = ids["emberline"]
        fid = fw_new["framework_agreement_id"]
        moment = at("2059-10-13", earliest=tip.sent_at if tip else None)
        offer = desk.framework_letter(fw_new, "offer", moment, contact("emberline", moment, "executive", "lichtacker"),
                                      who(45, "lichtacker", moment, "station", "V28"), storyline="V28",
                                      claim=("fw_thread", fid),
                                      extra=["We can take over the energy supply for Seip from mid-November."])
        desk.amendment_letters(n6, offer_sender=38, offer_recipient=168, storyline="V28",
                               extra_offer=[f"Nach den wiederholten Verspätungen (zuletzt {k167['contract_number']}) "
                                            "beziehen wir Energie künftig aus dem Rahmen "
                                            f"{fw_new['agreement_number']}."])
        desk.amendment_letters(n7, offer_sender=170, offer_recipient=41, reply_sender=38, reply_recipient=170,
                               storyline="V28",
                               extra_offer=["Um die Energieversorgung von Seip zu halten, bieten wir einen Nachlass "
                                            "auf alle Energieabrufe an."],
                               extra_reply=[f"Die Energie für Seip ist ab Januar über {fw_new['agreement_number']} "
                                            "gesichert."])
        moment = at(fw_new["start_date"])
        desk.framework_letter(fw_new, "contract_confirmation", moment,
                              who(38, "lichtacker", moment, "executive", "V28"),
                              who(fw_new["seller_signatory_id"], "emberline", moment, "executive", "V28"),
                              reply_to=offer, storyline="V28", claim=("fw_confirm", fid))

    # V29 – Lagebild Isolde und Kaltangebot Morgengrund nach den Ernteausfällen 61/71
    r, event61, event71 = rivalry("lichtacker", "pionierwerk"), desk.events.get(61), desk.events.get(71)
    if not missing("V29", r, event61, event71):
        moment = at("2059-11-05")
        desk.add(moment=moment, letter_type="internal_memo",
                 sender=who(43, "lichtacker", moment, "intelligence", "V29"),
                 recipient=who(38, "lichtacker", moment, "executive", "V29"),
                 subject=desk.subject("internal_memo", "de_DE", "Pionierwerk in Isolde"),
                 paragraphs=[f"die {desk.name(ids['pionierwerk'])} nutzt den Ernteausfall am "
                             f"{desk.station_name(event61['station_id'])} "
                             f"({desk.day_text(event61['event_date'], 'de_DE')}), um Siedler in Isolde mit eigenen "
                             "Rationen zu versorgen und alte Pachtflächen zu belegen. Ich empfehle, die "
                             "Pachtansprüche jetzt schriftlich geltend zu machen."],
                 direction="internal", confidentiality="confidential",
                 refs={"rivalry_id": r["rivalry_id"], "event_id": event61["event_id"]}, storyline="V29")
        moment = at("2059-12-15")
        desk.add(moment=moment, letter_type="offer", sender=contact("morgengrund", moment, "relations", "lichtacker"),
                 recipient=who(49, "lichtacker", moment, "station", "V29"),
                 subject=desk.subject("offer", "de_DE", "Getreide und Konserven aus Isolde"),
                 paragraphs=[f"nach dem erneuten Ernteausfall am {desk.station_name(event71['station_id'])} "
                             f"({desk.day_text(event71['event_date'], 'de_DE')}) bietet die "
                             f"{desk.name(ids['morgengrund'])} Getreide und Konserven aus Isolde an – Lieferung binnen "
                             "drei Wochen."],
                 direction="seller_to_buyer", confidentiality="public", refs={"event_id": event71["event_id"]},
                 response_required=1, storyline="V29")

    # V30 – Quarantäne HMX-CTR-2059-0242: Beschwerde, Erklärung, Strafbescheid
    k242 = contract("HMX-CTR-2059-0242")
    if not missing("V30", k242):
        late = desk.late_contract_shipment(k242)
        complaint = desk.delay_complaint(late, day=d("2059-11-29"), sender_id=174, recipient_id=302, storyline="V30")
        explanation = desk.delay_notice(late, day=d("2059-12-02"), sender_id=302, reply_to=complaint, storyline="V30",
                                        extra=["Medical supplies of this grade require a full sterile check at "
                                               "destination; we apologise for the delay and will absorb the screening "
                                               "fees."])
        if explanation is None:
            note("V30: Lieferung ohne Zwischenfall im Datenstand, Erklärung entfällt")
        desk.penalty_notice(k242, day=d("2059-12-08"), sender_id=169, recipient_id=294, storyline="V30")

    # V31 – Aussetzung CCI-MSA-2057-01 nach Ereignis 70 (9 Schreiben)
    fw, a4, event70 = framework("CCI-MSA-2057-01"), amendment("CCI-MSA-2057-01/A4"), desk.events.get(70)
    fw2, gfw_n4, k66 = framework("GFW-RV-2057-02"), amendment("GFW-RV-2057-02/N4"), contract("CVB-CTR-2059-0066")
    r6 = rivalry("cindervale", "helix")
    if not missing("V31", fw, a4, event70, fw2, gfw_n4, k66, r6):
        memo = desk.event_memo(event70, day=d("2059-12-01"), sender_id=178, recipient_id=168, storyline="V31",
                               extra=["Es ist der dritte Ausfall der Cindervale-Steuerkerne nach Februar und November "
                                      "2058."])
        moment = at("2059-12-02", earliest=memo.sent_at if memo else None)
        warning = desk.add(
            moment=moment, letter_type="breach_warning", sender=who(168, "eisenkrone", moment, "executive", "V31"),
            recipient=contact("cindervale", moment, "executive", "eisenkrone"),
            subject=desk.subject("breach_warning", "de_DE", f"{fw['agreement_number']} – dritter Ausfall"),
            paragraphs=[f"am {desk.day_text(event70['event_date'], 'de_DE')} ist die KI-Leitsteuerung der "
                        f"{desk.station_name(event70['station_id'])} zum dritten Mal ausgefallen. Wir mahnen die "
                        f"zugesicherte Verfügbarkeit aus {fw['agreement_number']} ab.",
                        "Legt die Cindervale bis zum 15.12.2059 keine belastbare Ursachenanalyse vor, setzen wir den "
                        f"Rahmen aus und behalten uns die Kündigung mit {fw['notice_period_days']} Tagen Frist vor."],
            direction="buyer_to_seller", confidentiality="confidential",
            refs=desk.framework_refs(fw, event_id=event70["event_id"]), response_required=1, storyline="V31")
        moment = at("2059-12-03")
        bauer = who(170, "eisenkrone", moment, "relations", "V31")
        desk.add(moment=moment, letter_type="internal_memo",
                 sender=who(171, "eisenkrone", moment, "intelligence", "V31"),
                 recipient=who(172, "eisenkrone", moment, "intelligence", "V31"),
                 subject=desk.subject("internal_memo", "de_DE", "Lagebild Cindervale"),
                 paragraphs=["die Cindervale schichtet Kapazität in die Navigationsplattform mit der "
                             f"{desk.name(ids['graufalk'])} ({fw2['agreement_number']}) um. Eine Kündigung träfe sie "
                             "kaum; eine Aussetzung hält uns Optionen offen.",
                             "Achtung: Unsere Korrespondenz mit Cindervale ist offenbar nicht dicht."],
                 direction="internal", confidentiality="confidential",
                 refs={"framework_agreement_id": fw["framework_agreement_id"]}, storyline="V31",
                 copies=[(bauer["employee_id"], "cc")] if bauer else None)
        moment = at("2059-12-04")
        leaker = who(299, "helix", moment, "intelligence", "V31")
        desk.add(moment=moment, letter_type="rumor", sender=leaker,
                 recipient=contact("cindervale", moment, "intelligence", "helix"),
                 subject=desk.subject("rumor", "en_US", "replacement cores for Förster"),
                 paragraphs=["Eisenkrone has asked our Sol desk for replacement AI control cores for Förster. Nothing "
                             "is signed yet – but if Helix steps in, your framework with Eisenkrone is history."],
                 direction="to_rival", confidentiality="confidential", refs={"rivalry_id": r6["rivalry_id"]},
                 is_accurate=None, leaked_by=leaker["employee_id"] if leaker else None, leaked_to=ids["cindervale"],
                 storyline="V31")
        desk.amendment_letters(a4, offer_sender=168, thread=warning, reply_recipient=170, storyline="V31",
                               extra_offer=["Anlass ist der dritte Ausfall der KI-Leitsteuerung an der "
                                            "Industriestation Förster."],
                               extra_reply=["We accept the suspension under protest and without prejudice; our "
                                            "analysis points to operating errors at Förster."])
        moment = at("2059-12-08", earliest=warning.sent_at if warning else None)
        desk.add(moment=moment, letter_type="breach_warning",
                 sender=desk.employees.get(warning.recipient_employee_id) if warning else None,
                 recipient=who(168, "eisenkrone", moment, "executive", "V31"),
                 subject=desk.subject("breach_warning", "en_US", f"Re: {fw['agreement_number']}"),
                 paragraphs=["we reject the allegation of a warranty breach. The cores at Förster were operated "
                             "outside the agreed cooling parameters, as our telemetry shows."],
                 direction="seller_to_buyer", confidentiality="confidential",
                 refs=desk.framework_refs(fw, event_id=event70["event_id"]), reply_to=warning, storyline="V31")
        moment = at("2059-12-10")
        leaker = who(120, "corvane", moment, "intelligence", "V31")
        desk.add(moment=moment, letter_type="confidential_tip", sender=leaker,
                 recipient=contact("cindervale", moment, "intelligence", "corvane"),
                 subject=desk.subject("confidential_tip", "en_US", "robotics at Hande"),
                 paragraphs=["Eisenkrone is already testing our robotics units at "
                             f"{desk.station_name(k66['destination_station_id'])} ({k66['contract_number']}) as a "
                             "stopgap for your cores. Their partner relations team is pushing for it internally."],
                 direction="lateral", confidentiality="confidential", refs={"contract_id": k66["contract_id"]},
                 is_accurate=1, leaked_by=leaker["employee_id"] if leaker else None, leaked_to=ids["cindervale"],
                 storyline="V31")
        desk.amendment_letters(gfw_n4, storyline="V31",
                               extra_offer=["After recent leaks of our correspondence with Eisenkrone we propose a "
                                            "stricter confidentiality clause for all data exchanged under the "
                                            "alliance."])

    # V32 – 3. Mahnung EKM-BST-2059-01408 (K5)
    order = order_no("EKM-BST-2059-01408")
    if not missing("V32", order):
        desk.payment_reminders(order, days=(None, None, d("2059-03-29")), sender_id=169, recipient_id=118,
                               storyline="V32")

    # V33 – Angebot und Absage zum Entwurf EKM-VTR-2060-0230
    k230 = contract("EKM-VTR-2060-0230")
    if not missing("V33", k230):
        offer = desk.contract_offer(k230, day=d("2059-12-18"), sender_id=170, recipient_id=42, storyline="V33",
                                    extra=["Energie ist ab dem 18.01.2060 nicht mehr Teil des Rahmens EKM-RV-2057-03; "
                                           "wir bieten Ihnen daher einen separaten Dauerliefervertrag an."])
        if offer is not None:
            desk.offer_reply(offer, k230, "offer_rejection", day=d("2059-12-29"), sender_id=42, storyline="V33",
                             extra=["Energie für Seip beziehen wir ab Januar aus dem Rahmen EFF-MSA-2059-02."])

    # V34 – dreiseitiger Vorschlag Geleit und Liegeplätze nach Piratenangriff 74 (K2)
    a2, n7h, event74 = amendment("RCS-MSA-2058-01/A2"), amendment("EKM-RV-2057-02/N7"), desk.events.get(74)
    if not missing("V34", a2, n7h, event74):
        first, _reply = desk.amendment_letters(
            a2, offer_recipient=304, storyline="V34",
            extra_offer=[f"After the pirate attack at {desk.station_name(event74['station_id'])} on "
                         f"{desk.day_text(event74['event_date'], 'en_US')} we propose armed escorts for all convoys in "
                         "the corridor, including Eisenkrone call-offs from Brennus, plus overflow berths at our "
                         "trade station in Kharon for docking congestion."])
        desk.amendment_letters(n7h, offer_sender=304, offer_recipient=170, refers_to=first, storyline="V34",
                               extra_offer=["Forwarded for your review: Ravenmoor's escort proposal. Including the "
                                            "clause in our framework would prevent a repeat of the escort waits on "
                                            "EKM-VTR-2057-0043 and EKM-VTR-2058-0107."])

    # V35 – Lieferavis, Verzögerung und Beschwerde EKM-BST-2059-02343
    order = order_no("EKM-BST-2059-02343")
    if not missing("V35", order):
        desk.delivery_notice(order, day=d("2059-12-26"), sender_id=254, recipient_id=307, storyline="V35")
        desk.delay_notice(order, day=d("2059-12-30"), sender_id=254, recipient_id=307, storyline="V35")
        desk.delay_complaint(order, day=d("2059-12-31"), sender_id=370, recipient_id=170, storyline="V35")

    # V36 – Anfrage Eilabrufe nach zwei Triebwerksschäden (K6), Nachtrag GFW-RV-2057-01/N4
    a, fw = amendment("GFW-RV-2057-01/N4"), framework("GFW-RV-2057-01")
    s1, s2 = desk.shipment_by_number.get("HMX-SHP-2059-01721"), desk.shipment_by_number.get("HMX-SHP-2059-01746")
    if not missing("V36", a, fw, s1, s2):
        o1, o2 = desk.orders[s1["order_id"]], desk.orders[s2["order_id"]]
        moment = at("2059-12-31", earliest=max(datetime.fromisoformat(s1["departure_date"]),
                                               datetime.fromisoformat(s2["departure_date"])))
        desk.add(moment=moment, letter_type="inquiry", sender=who(332, "helix", moment, "relations", "V36"),
                 recipient=contact("graufalk", moment, "relations", "helix"),
                 subject=desk.subject("inquiry", "en_US", f"rush call-offs under {fw['agreement_number']}"),
                 paragraphs=[f"two of our freighters suffered drive failures within a week ({s1['shipment_number']}, "
                             f"+{fmt_number(desk.delay_hours(s1), 'en_US')} h, and {s2['shipment_number']}, orders "
                             f"{o1['order_number']} and {o2['order_number']}).",
                             "We would like to add a rush call-off clause for drive parts to "
                             f"{fw['agreement_number']}: delivery within 72 hours against a surcharge. Draft amendment "
                             f"{a['amendment_number']} is attached."],
                 direction="buyer_to_seller", refs=desk.framework_refs(fw, amendment_id=a["amendment_id"]),
                 response_required=1, storyline="V36", claim=("amend_offer", a["amendment_id"]))

    # V37 – Zahlungserinnerung HMX-ORD-2059-01645
    order = order_no("HMX-ORD-2059-01645")
    if not missing("V37", order):
        desk.payment_reminders(order, days=(d("2059-12-28"), None, None), sender_id=294, recipient_id=118,
                               storyline="V37")

    # V38 – Verzögerungsmeldung FSP-BST-2059-00111 (Quarantäne)
    order = order_no("FSP-BST-2059-00111")
    if not missing("V38", order):
        desk.delay_notice(order, day=d("2059-12-30"), sender_id=9, recipient_id=179, storyline="V38")

    # V39 – Leck Chavez → Cindervale, Abmahnung an Eisenkrone, Antwort Bauer (K1)
    fw = framework("CCI-MSA-2057-01")
    if not missing("V39", k66, fw, event36):
        moment = at("2059-08-28")
        leaker = who(120, "corvane", moment, "intelligence", "V39")
        rumor = desk.add(
            moment=moment, letter_type="rumor", sender=leaker,
            recipient=contact("cindervale", moment, "intelligence", "corvane"),
            subject=desk.subject("rumor", "en_US", f"robotics for {desk.station_name(k66['destination_station_id'])}"),
            paragraphs=[f"heads-up: since {desk.day_text(k66['start_date'], 'en_US')} Corvane has been supplying "
                        f"robotics units to Eisenkrone's {desk.station_name(k66['destination_station_id'])} under an "
                        f"exclusive supply contract ({k66['contract_number']}, {k66['quantity']} units). That is high "
                        "technology for Halcyon – your ground under the Eisenkrone framework."],
            direction="lateral", confidentiality="confidential", refs={"contract_id": k66["contract_id"]},
            is_accurate=1, leaked_by=leaker["employee_id"] if leaker else None, leaked_to=ids["cindervale"],
            storyline="V39")
        moment = at("2059-09-02", earliest=rumor.sent_at if rumor else None)
        bauer = who(170, "eisenkrone", moment, "relations", "V39")
        warning = desk.add(
            moment=moment, letter_type="breach_warning",
            sender=contact("cindervale", moment, "executive", "eisenkrone"),
            recipient=who(168, "eisenkrone", moment, "executive", "V39"),
            subject=desk.subject("breach_warning", "en_US", f"{fw['agreement_number']} – right of first refusal"),
            paragraphs=[f"under framework agreement {fw['agreement_number']} Cindervale holds a right of first refusal "
                        "for high technology supplied to Halcyon. We understand that Eisenkrone has awarded an "
                        "exclusive robotics supply contract to a third party without consulting us.",
                        "We formally object and expect to be consulted before any further award."],
            direction="seller_to_buyer", confidentiality="confidential", refs=desk.framework_refs(fw),
            response_required=1, refers_to=rumor, storyline="V39",
            copies=[(bauer["employee_id"], "cc")] if bauer else None)
        moment = at("2059-09-12", earliest=warning.sent_at if warning else None)
        desk.add(moment=moment, letter_type="breach_warning", sender=who(170, "eisenkrone", moment, "relations", "V39"),
                 recipient=desk.employees.get(warning.sender_employee_id) if warning else None,
                 subject=desk.subject("breach_warning", "de_DE", f"Re: {fw['agreement_number']}"),
                 paragraphs=["Ihr Schreiben weisen wir zurück. Nach den Ausfällen Ihrer Steuerkerne an der "
                             f"{desk.station_name(event36['station_id'])} (Februar und November 2058) mussten wir für "
                             f"die {desk.station_name(k66['destination_station_id'])} eine Ausweichlösung schaffen.",
                             "Ein Vorkaufsrecht verpflichtet uns zur Anfrage, nicht zur Abnahme – und Ihr letztes "
                             "Angebot lag 30 % über dem Markt."],
                 direction="buyer_to_seller", confidentiality="confidential",
                 refs=desk.framework_refs(fw, event_id=event36["event_id"]), reply_to=warning, storyline="V39")

    # V40 – Verdacht gegen Erkan Hesse (das wahre Leck ist Täsche, V14)
    hesse = employee(39)
    if not missing("V40", kuppel_offer, k159, hesse):
        moment = at("2059-06-04")
        desk.add(moment=moment, letter_type="internal_memo", sender=who(38, "lichtacker", moment, "executive", "V40"),
                 recipient=who(40, "lichtacker", moment, "finance", "V40"),
                 subject=desk.subject("internal_memo", "de_DE", f"Weitergabe {k159['contract_number']}"),
                 paragraphs=[f"die Kuppelwerk kannte unseren Strafbescheid zu {k159['contract_number']} schon wenige "
                             "Tage nach Versand. Den Bescheid hatten nur Vorstand und Finanzbuchhaltung.",
                             f"Bitte prüfen Sie die Zugriffe von {hesse['full_name']}; bis zur Klärung ist er von "
                             "vertraulichen Vorgängen auszuschließen."],
                 direction="internal", confidentiality="confidential", refs={"contract_id": k159["contract_id"]},
                 refers_to=kuppel_offer, storyline="V40")

    # V41 – Dörr verrät das Ausfallprotokoll Förster an Graufalk
    r5 = rivalry("graufalk", "eisenkrone")
    if not missing("V41", r5, event36):
        moment = at("2058-11-20")
        leaker = who(235, "eisenkrone", moment, "station", "V41")
        desk.add(moment=moment, letter_type="confidential_tip", sender=leaker,
                 recipient=contact("graufalk", moment, "intelligence", "eisenkrone"),
                 subject=desk.subject("confidential_tip", "de_DE", "Ausfallprotokoll Förster"),
                 paragraphs=[f"das Ausfallprotokoll der {desk.station_name(event36['station_id'])} vom "
                             f"{desk.day_text(event36['event_date'], 'de_DE')} liegt mir vor: Die "
                             "Cindervale-Steuerkerne sind wieder ausgefallen, die Fertigung steht voraussichtlich "
                             f"{event36['duration_days']} Tage. Eisenkrone wird Werftteile nachkaufen müssen."],
                 direction="to_rival", confidentiality="internal",
                 refs={"event_id": event36["event_id"], "rivalry_id": r5["rivalry_id"]}, is_accurate=1,
                 leaked_by=leaker["employee_id"] if leaker else None, leaked_to=ids["graufalk"], storyline="V41")


def generate_correspondence(world: World) -> None:
    """Erzeugt den Schriftverkehr aller 18 Firmen im eigenen Zufallsstrom (nach allen anderen Schritten).

    Reihenfolge: verankerte Vorgänge (nur Seed 42), Rahmenverhandlungen, Nachträge, Einzelverträge,
    Verzug und Vertragsstrafen, Lieferavis, Mahnungen, Ereignisnotizen, Rivalitäten, zuletzt Lecks
    vertraulicher Schreiben. IDs und Nummern werden chronologisch vergeben.
    """
    desk = CorrespondenceDesk(world)
    if world.seed == BASELINE_SEED:
        add_storylines(desk)
    rng = desk.rng
    for framework in sorted(desk.frameworks.values(), key=lambda f: f["framework_agreement_id"]):
        desk.framework_thread(framework)
    for amendment in sorted(desk.amendments.values(), key=lambda a: a["amendment_id"]):
        desk.amendment_letters(amendment)
    contracts = sorted(desk.contracts.values(), key=lambda c: c["contract_id"])
    for contract in contracts:
        if contract["contract_type"] == "exclusive_supply" or (
                contract["contract_type"] in FRAMEWORK_CALLOFF_TYPES and contract["total_value"] >= 10_000_000):
            desk.contract_confirmation(contract)
        if contract["status"] == "draft":
            offer = desk.contract_offer(contract)
            if offer is not None and rng.random() < 0.35:
                desk.offer_reply(offer, contract, "counter_offer" if rng.random() < 0.6 else "offer_rejection")
        elif contract["contract_type"] == "spot" and contract["start_date"] >= "2057-01-15" and rng.random() < 0.2:
            desk.contract_offer(contract, inquiry=True)
        if contract["status"] == "cancelled":
            desk.contract_termination(contract)
    breaches_by_framework: dict[int, int] = defaultdict(int)
    def breach_order(contract: dict[str, Any]) -> tuple[datetime, int]:
        booking = desk.penalties.get(contract["contract_id"])
        return (booking["last_arrival"] if booking else datetime.max, contract["contract_id"])

    for contract in sorted(contracts, key=breach_order):
        late = desk.late_contract_shipment(contract)
        if late is not None:
            desk.delay_complaint(late)
        if contract["status"] != "breached":
            continue
        penalty = desk.penalty_notice(contract)
        if penalty is None:
            penalty = next((letter for letter in desk.letters if letter.letter_type == "penalty_notice"
                            and letter.refs["contract_id"] == contract["contract_id"]), None)
        if penalty is None:
            continue
        if (penalty.amount or 0) > EXECUTIVE_PENALTY_THRESHOLD and penalty.storyline is None:
            desk.penalty_memo(penalty, contract)
        if contract["framework_agreement_id"]:
            breaches_by_framework[contract["framework_agreement_id"]] += 1
            count = breaches_by_framework[contract["framework_agreement_id"]]
            if count % 2 == 0 and penalty.storyline is None:
                desk.repeat_breach_warning(desk.frameworks[contract["framework_agreement_id"]], penalty, count)
    for order in sorted(desk.orders.values(), key=lambda o: o["order_id"]):
        shipment = desk.shipment_by_order.get(order["order_id"])
        if shipment is None or order["customer_company_id"] is None:
            continue
        open_at_reference = order["status"] in ("in_transit", "delayed")
        if open_at_reference or (order["contract_id"] and order["total_amount"] >= DELIVERY_NOTICE_MIN_AMOUNT
                                 and rng.random() < 0.3):
            desk.delivery_notice(order)
        if shipment["risk_incident"] and (order["contract_id"] or rng.random() < 0.35):
            desk.delay_notice(order)
        if (order["contract_id"] is None and order["status"] == "delayed"
                and datetime.fromisoformat(shipment["arrival_date"]) + timedelta(hours=12) < GAME_REFERENCE_DATETIME):
            desk.delay_complaint(order)
    for order in sorted(desk.orders.values(), key=lambda o: o["order_id"]):
        # Firmenkunden werden immer gemahnt, Nicht-Firmenkunden in einer Stichprobe (Mengenbegrenzung)
        if order["payment_status"] == "overdue" and (order["customer_company_id"] or rng.random() < 0.25):
            desk.payment_reminders(order)
    for event in sorted(desk.events.values(), key=lambda e: e["event_id"]):
        if event["severity"] in ("major", "critical"):
            desk.event_memo(event)
    for rivalry in sorted(desk.rivalries.values(), key=lambda r: r["rivalry_id"]):
        desk.rivalry_protest(rivalry)
        desk.rivalry_rumors(rivalry)
    desk.leak_letters()
    desk.finalize()
    world.correspondence_notes = desk.adaptations


# ---------------------------------------------------------------------------
# Datenbankschema und Schreiben
# ---------------------------------------------------------------------------

SCHEMA_STATEMENTS: tuple[str, ...] = (
    """CREATE TABLE companies (
        company_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        slug TEXT NOT NULL UNIQUE,
        language TEXT NOT NULL CHECK(language IN ('de_DE','en_US')),
        size_class TEXT NOT NULL CHECK(size_class IN ('small','medium','large')),
        headquarters_station_id INTEGER NOT NULL
            REFERENCES stations(station_id) DEFERRABLE INITIALLY DEFERRED,
        founded_year INTEGER NOT NULL,
        description TEXT NOT NULL,
        credit_rating TEXT NOT NULL,
        is_player_accessible INTEGER NOT NULL DEFAULT 1 CHECK(is_player_accessible IN (0,1)),
        specialization TEXT NOT NULL,
        network_role TEXT NOT NULL,
        data_window_start TEXT NOT NULL,
        starting_cash REAL NOT NULL CHECK(starting_cash >= 0)
    )""",
    """CREATE TABLE star_systems (
        system_id INTEGER PRIMARY KEY,
        code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL UNIQUE,
        sector_code TEXT NOT NULL,
        x REAL NOT NULL CHECK(x BETWEEN -500 AND 500),
        y REAL NOT NULL CHECK(y BETWEEN -500 AND 500),
        z REAL NOT NULL CHECK(z BETWEEN -500 AND 500),
        unlock_tier INTEGER NOT NULL CHECK(unlock_tier >= 0),
        base_security TEXT NOT NULL CHECK(base_security IN ('high','medium','low','lawless')),
        description_de TEXT NOT NULL,
        description_en TEXT NOT NULL
    )""",
    """CREATE TABLE stations (
        station_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        company_id INTEGER NOT NULL REFERENCES companies(company_id),
        system_id INTEGER NOT NULL REFERENCES star_systems(system_id),
        system_name TEXT NOT NULL,
        sector TEXT NOT NULL,
        x REAL NOT NULL CHECK(x BETWEEN -500 AND 500),
        y REAL NOT NULL CHECK(y BETWEEN -500 AND 500),
        z REAL NOT NULL CHECK(z BETWEEN -500 AND 500),
        population INTEGER NOT NULL CHECK(population >= 0),
        station_type TEXT NOT NULL CHECK(station_type IN ('trade_hub','industrial','mining','research',
            'agricultural','free_port','military','smuggler_haven')),
        security_level TEXT NOT NULL CHECK(security_level IN ('high','medium','low','lawless')),
        description TEXT NOT NULL,
        unlock_tier INTEGER NOT NULL CHECK(unlock_tier >= 0),
        storage_capacity_m3 REAL NOT NULL CHECK(storage_capacity_m3 > 0),
        monthly_upkeep REAL NOT NULL CHECK(monthly_upkeep >= 0),
        docking_fee REAL NOT NULL CHECK(docking_fee >= 0)
    )""",
    """CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        company_id INTEGER NOT NULL REFERENCES companies(company_id),
        sku TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        category_code TEXT NOT NULL CHECK(category_code IN ('raw_materials','energy','industrial_goods',
            'technology','food','medical','luxury','contraband')),
        archetype_code TEXT NOT NULL,
        description TEXT NOT NULL,
        base_price REAL NOT NULL CHECK(base_price > 0),
        base_cost REAL NOT NULL CHECK(base_cost > 0),
        unit TEXT NOT NULL,
        volume_m3 REAL NOT NULL CHECK(volume_m3 > 0),
        mass_kg REAL NOT NULL CHECK(mass_kg > 0),
        legal_status TEXT NOT NULL CHECK(legal_status IN ('legal','restricted','illegal')),
        is_tradeable INTEGER NOT NULL DEFAULT 1 CHECK(is_tradeable IN (0,1)),
        CHECK(base_price > base_cost),
        UNIQUE(company_id, name)
    )""",
    """CREATE TABLE trade_partnerships (
        partnership_id INTEGER PRIMARY KEY,
        company_id INTEGER NOT NULL REFERENCES companies(company_id),
        partner_company_id INTEGER NOT NULL REFERENCES companies(company_id),
        relationship_type TEXT NOT NULL,
        trust_level INTEGER NOT NULL CHECK(trust_level BETWEEN 0 AND 100),
        contract_volume REAL NOT NULL CHECK(contract_volume >= 0),
        start_date TEXT NOT NULL,
        end_date TEXT,
        is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
        CHECK(company_id <> partner_company_id),
        CHECK(end_date IS NULL OR end_date >= start_date),
        UNIQUE(company_id, partner_company_id, relationship_type)
    )""",
    """CREATE TABLE company_rivalries (
        rivalry_id INTEGER PRIMARY KEY,
        company_id INTEGER NOT NULL REFERENCES companies(company_id),
        rival_company_id INTEGER NOT NULL REFERENCES companies(company_id),
        rivalry_type TEXT NOT NULL,
        intensity INTEGER NOT NULL CHECK(intensity BETWEEN 0 AND 100),
        contested_system_id INTEGER NOT NULL REFERENCES star_systems(system_id),
        espionage_risk INTEGER NOT NULL CHECK(espionage_risk BETWEEN 0 AND 100),
        since_date TEXT NOT NULL,
        description TEXT NOT NULL,
        CHECK(company_id <> rival_company_id),
        UNIQUE(company_id, rival_company_id)
    )""",
    """CREATE TABLE framework_agreements (
        framework_agreement_id INTEGER PRIMARY KEY,
        agreement_number TEXT NOT NULL UNIQUE,
        partnership_id INTEGER NOT NULL REFERENCES trade_partnerships(partnership_id),
        company_id INTEGER NOT NULL REFERENCES companies(company_id),
        partner_company_id INTEGER NOT NULL REFERENCES companies(company_id),
        title TEXT NOT NULL,
        language TEXT NOT NULL CHECK(language IN ('de_DE','en_US')),
        signed_date TEXT NOT NULL,
        start_date TEXT NOT NULL,
        term_months INTEGER NOT NULL CHECK(term_months > 0),
        end_date TEXT NOT NULL,
        current_end_date TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('negotiating','active','suspended','expired','terminated')),
        base_volume REAL NOT NULL CHECK(base_volume > 0),
        current_volume_cap REAL NOT NULL CHECK(current_volume_cap > 0),
        price_formula TEXT NOT NULL CHECK(price_formula IN ('fixed','index_linked','cost_plus','market_minus')),
        indexation TEXT NOT NULL CHECK(indexation IN ('none','category_price_index','fuel_index','risk_index')),
        price_index_category TEXT,
        base_discount_pct REAL,
        cost_plus_pct REAL,
        adjustment_cap_pct REAL,
        exclusivity TEXT NOT NULL CHECK(exclusivity IN ('none','right_of_first_refusal','buyer_exclusive',
            'seller_exclusive','mutual','regional_exclusive')),
        exclusivity_system_id INTEGER REFERENCES star_systems(system_id),
        notice_period_days INTEGER NOT NULL CHECK(notice_period_days > 0),
        auto_renewal INTEGER NOT NULL DEFAULT 0 CHECK(auto_renewal IN (0,1)),
        renewal_months INTEGER,
        penalty_rate_pct REAL NOT NULL CHECK(penalty_rate_pct >= 0),
        escort_company_id INTEGER REFERENCES companies(company_id),
        seller_signatory_id INTEGER REFERENCES employees(employee_id) DEFERRABLE INITIALLY DEFERRED,
        buyer_signatory_id INTEGER REFERENCES employees(employee_id) DEFERRABLE INITIALLY DEFERRED,
        description TEXT NOT NULL,
        CHECK(company_id <> partner_company_id),
        CHECK(signed_date < start_date),
        CHECK(end_date > start_date AND current_end_date >= end_date)
    )""",
    """CREATE TABLE trade_routes (
        route_id INTEGER PRIMARY KEY,
        origin_station_id INTEGER NOT NULL REFERENCES stations(station_id),
        destination_station_id INTEGER NOT NULL REFERENCES stations(station_id),
        product_id INTEGER NOT NULL REFERENCES products(product_id),
        company_id INTEGER NOT NULL REFERENCES companies(company_id),
        typical_quantity INTEGER NOT NULL CHECK(typical_quantity > 0),
        base_price_origin REAL NOT NULL CHECK(base_price_origin > 0),
        base_price_destination REAL NOT NULL CHECK(base_price_destination > 0),
        estimated_profit_per_unit REAL NOT NULL,
        travel_time_hours REAL NOT NULL CHECK(travel_time_hours > 0),
        risk_level TEXT NOT NULL CHECK(risk_level IN ('low','medium','high','extreme')),
        is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
        distance_units REAL NOT NULL CHECK(distance_units > 0),
        transport_cost_per_unit REAL NOT NULL CHECK(transport_cost_per_unit >= 0),
        net_profit_per_unit REAL NOT NULL,
        route_scope TEXT NOT NULL CHECK(route_scope IN ('internal','partner')),
        CHECK(origin_station_id <> destination_station_id),
        UNIQUE(origin_station_id, destination_station_id, product_id)
    )""",
    """CREATE TABLE inventory (
        inventory_id INTEGER PRIMARY KEY,
        station_id INTEGER NOT NULL REFERENCES stations(station_id),
        product_id INTEGER NOT NULL REFERENCES products(product_id),
        quantity INTEGER NOT NULL CHECK(quantity >= 0),
        reserved_quantity INTEGER NOT NULL DEFAULT 0 CHECK(reserved_quantity >= 0),
        restock_target INTEGER NOT NULL CHECK(restock_target >= 0),
        last_updated TEXT NOT NULL,
        market_role TEXT NOT NULL CHECK(market_role IN ('supply','demand','internal')),
        local_base_price REAL NOT NULL CHECK(local_base_price > 0),
        CHECK(reserved_quantity <= quantity),
        UNIQUE(station_id, product_id)
    )""",
    """CREATE TABLE contracts (
        contract_id INTEGER PRIMARY KEY,
        contract_number TEXT NOT NULL UNIQUE,
        company_id INTEGER NOT NULL REFERENCES companies(company_id),
        partner_company_id INTEGER NOT NULL REFERENCES companies(company_id),
        origin_station_id INTEGER NOT NULL REFERENCES stations(station_id),
        destination_station_id INTEGER NOT NULL REFERENCES stations(station_id),
        product_id INTEGER NOT NULL REFERENCES products(product_id),
        route_id INTEGER NOT NULL REFERENCES trade_routes(route_id),
        contract_type TEXT NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        agreed_price_per_unit REAL NOT NULL CHECK(agreed_price_per_unit > 0),
        total_value REAL NOT NULL CHECK(total_value > 0),
        start_date TEXT NOT NULL,
        deadline TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('draft','active','completed','breached','cancelled')),
        penalty_per_day REAL NOT NULL DEFAULT 0 CHECK(penalty_per_day >= 0),
        description TEXT NOT NULL,
        framework_agreement_id INTEGER REFERENCES framework_agreements(framework_agreement_id),
        CHECK(company_id <> partner_company_id),
        CHECK(deadline >= start_date)
    )""",
    """CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        company_id INTEGER NOT NULL REFERENCES companies(company_id),
        linked_company_id INTEGER REFERENCES companies(company_id),
        name TEXT NOT NULL,
        customer_type TEXT NOT NULL,
        home_station_id INTEGER NOT NULL REFERENCES stations(station_id),
        contact_name TEXT NOT NULL,
        credit_limit REAL NOT NULL CHECK(credit_limit >= 0),
        since_date TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
        UNIQUE(company_id, name)
    )""",
    """CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        order_number TEXT NOT NULL UNIQUE,
        company_id INTEGER NOT NULL REFERENCES companies(company_id),
        customer_company_id INTEGER REFERENCES companies(company_id),
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        customer_name TEXT NOT NULL,
        contract_id INTEGER REFERENCES contracts(contract_id),
        origin_station_id INTEGER NOT NULL REFERENCES stations(station_id),
        destination_station_id INTEGER NOT NULL REFERENCES stations(station_id),
        order_date TEXT NOT NULL,
        required_delivery_date TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('pending','confirmed','in_transit','delivered','delayed','cancelled')),
        payment_status TEXT NOT NULL CHECK(payment_status IN ('unpaid','invoiced','partially_paid','paid',
            'overdue','void','refunded')),
        subtotal REAL NOT NULL CHECK(subtotal >= 0),
        freight_cost REAL NOT NULL DEFAULT 0 CHECK(freight_cost >= 0),
        insurance_cost REAL NOT NULL DEFAULT 0 CHECK(insurance_cost >= 0),
        handling_fee REAL NOT NULL DEFAULT 0 CHECK(handling_fee >= 0),
        total_amount REAL NOT NULL CHECK(total_amount >= 0),
        currency TEXT NOT NULL,
        notes TEXT,
        CHECK(origin_station_id <> destination_station_id)
    )""",
    """CREATE TABLE order_items (
        order_item_id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
        product_id INTEGER NOT NULL REFERENCES products(product_id),
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        unit_price REAL NOT NULL CHECK(unit_price >= 0),
        line_total REAL NOT NULL CHECK(line_total >= 0),
        UNIQUE(order_id, product_id)
    )""",
    """CREATE TABLE shipments (
        shipment_id INTEGER PRIMARY KEY,
        shipment_number TEXT NOT NULL UNIQUE,
        order_id INTEGER NOT NULL REFERENCES orders(order_id),
        origin_station_id INTEGER NOT NULL REFERENCES stations(station_id),
        destination_station_id INTEGER NOT NULL REFERENCES stations(station_id),
        departure_date TEXT NOT NULL,
        arrival_date TEXT NOT NULL,
        actual_arrival_date TEXT,
        status TEXT NOT NULL CHECK(status IN ('pending','in_transit','delayed','delivered')),
        ship_name TEXT NOT NULL,
        cargo_mass_kg REAL NOT NULL CHECK(cargo_mass_kg >= 0),
        cargo_volume_m3 REAL NOT NULL CHECK(cargo_volume_m3 >= 0),
        fuel_cost REAL NOT NULL CHECK(fuel_cost >= 0),
        insurance_cost REAL NOT NULL CHECK(insurance_cost >= 0),
        risk_incident TEXT,
        CHECK(arrival_date > departure_date),
        CHECK(actual_arrival_date IS NULL OR actual_arrival_date >= arrival_date)
    )""",
    """CREATE TABLE price_history (
        price_history_id INTEGER PRIMARY KEY,
        station_id INTEGER NOT NULL REFERENCES stations(station_id),
        product_id INTEGER NOT NULL REFERENCES products(product_id),
        date TEXT NOT NULL,
        supply_index REAL NOT NULL CHECK(supply_index >= 0),
        demand_index REAL NOT NULL CHECK(demand_index >= 0),
        market_price REAL NOT NULL CHECK(market_price > 0),
        stock_quantity INTEGER NOT NULL CHECK(stock_quantity >= 0),
        UNIQUE(station_id, product_id, date)
    )""",
    """CREATE TABLE employees (
        employee_id INTEGER PRIMARY KEY,
        company_id INTEGER NOT NULL REFERENCES companies(company_id),
        station_id INTEGER NOT NULL REFERENCES stations(station_id),
        full_name TEXT NOT NULL,
        role TEXT NOT NULL,
        role_code TEXT NOT NULL,
        salary REAL NOT NULL CHECK(salary >= 0),
        hire_date TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
        termination_date TEXT,
        influence INTEGER NOT NULL CHECK(influence BETWEEN 0 AND 100),
        loyalty INTEGER NOT NULL CHECK(loyalty BETWEEN 0 AND 100),
        bribe_susceptibility INTEGER NOT NULL CHECK(bribe_susceptibility BETWEEN 0 AND 100),
        intel_access_level INTEGER NOT NULL CHECK(intel_access_level BETWEEN 0 AND 3),
        personality TEXT NOT NULL,
        CHECK((is_active = 1 AND termination_date IS NULL) OR (is_active = 0 AND termination_date IS NOT NULL))
    )""",
    """CREATE TABLE events (
        event_id INTEGER PRIMARY KEY,
        station_id INTEGER NOT NULL REFERENCES stations(station_id),
        event_date TEXT NOT NULL,
        event_type TEXT NOT NULL CHECK(event_type IN ('pirate_attack','asteroid_storm','strike','machine_failure',
            'crop_failure','resource_discovery','customs_inspection','quarantine','black_market_raid','demand_boom')),
        title TEXT NOT NULL,
        severity TEXT NOT NULL CHECK(severity IN ('minor','moderate','major','critical')),
        affected_product_id INTEGER REFERENCES products(product_id),
        description TEXT NOT NULL,
        price_impact REAL NOT NULL,
        supply_impact REAL NOT NULL,
        demand_impact REAL NOT NULL,
        duration_days INTEGER NOT NULL CHECK(duration_days > 0)
    )""",
    """CREATE TABLE event_effects (
        event_effect_id INTEGER PRIMARY KEY,
        event_id INTEGER NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
        station_id INTEGER NOT NULL REFERENCES stations(station_id),
        product_id INTEGER NOT NULL REFERENCES products(product_id),
        supply_impact REAL NOT NULL,
        demand_impact REAL NOT NULL,
        price_impact REAL NOT NULL,
        UNIQUE(event_id, station_id, product_id)
    )""",
    """CREATE TABLE company_financials (
        financial_id INTEGER PRIMARY KEY,
        company_id INTEGER NOT NULL REFERENCES companies(company_id),
        period TEXT NOT NULL,
        orders_delivered INTEGER NOT NULL CHECK(orders_delivered >= 0),
        goods_revenue REAL NOT NULL CHECK(goods_revenue >= 0),
        service_revenue REAL NOT NULL CHECK(service_revenue >= 0),
        cost_of_goods_sold REAL NOT NULL CHECK(cost_of_goods_sold >= 0),
        duties_and_fees REAL NOT NULL CHECK(duties_and_fees >= 0),
        logistics_cost REAL NOT NULL CHECK(logistics_cost >= 0),
        fleet_operations REAL NOT NULL CHECK(fleet_operations >= 0),
        payroll_cost REAL NOT NULL CHECK(payroll_cost >= 0),
        station_upkeep REAL NOT NULL CHECK(station_upkeep >= 0),
        contract_penalties REAL NOT NULL CHECK(contract_penalties >= 0),
        net_income REAL NOT NULL,
        cash_balance REAL NOT NULL,
        UNIQUE(company_id, period)
    )""",
    """CREATE TABLE framework_agreement_amendments (
        amendment_id INTEGER PRIMARY KEY,
        framework_agreement_id INTEGER NOT NULL REFERENCES framework_agreements(framework_agreement_id),
        amendment_no INTEGER NOT NULL CHECK(amendment_no > 0),
        amendment_number TEXT NOT NULL UNIQUE,
        amendment_type TEXT NOT NULL CHECK(amendment_type IN ('volume_increase','volume_reduction',
            'product_addition','product_removal','price_adjustment','term_extension','exclusivity_clause',
            'exclusivity_waiver','penalty_clause','service_level_clause','escort_clause','force_majeure_clause',
            'competition_clause','confidentiality_clause','scope_extension','partial_termination','suspension')),
        status TEXT NOT NULL CHECK(status IN ('proposed','signed','rejected','withdrawn')),
        rule TEXT CHECK(rule IS NULL OR rule IN ('first_contract_of_category','cumulative_over_90pct',
            'calloff_after_end')),
        proposed_date TEXT NOT NULL CHECK(proposed_date <= '2059-12-31'),
        signed_date TEXT,
        effective_date TEXT NOT NULL,
        initiated_by_company_id INTEGER NOT NULL REFERENCES companies(company_id),
        volume_before REAL,
        volume_delta REAL,
        volume_after REAL CHECK(volume_after IS NULL OR volume_after > 0),
        price_change_pct REAL,
        price_factor REAL CHECK(price_factor IS NULL OR price_factor > 0),
        end_date_new TEXT,
        category_code TEXT,
        archetype_code TEXT,
        exclusivity TEXT,
        exclusive_system_id INTEGER REFERENCES star_systems(system_id),
        escort_company_id INTEGER REFERENCES companies(company_id),
        trigger_contract_id INTEGER REFERENCES contracts(contract_id),
        trigger_order_id INTEGER REFERENCES orders(order_id),
        trigger_event_id INTEGER REFERENCES events(event_id),
        description TEXT NOT NULL,
        CHECK((status = 'signed') = (signed_date IS NOT NULL)),
        CHECK(signed_date IS NULL OR (signed_date >= proposed_date AND signed_date <= effective_date)),
        CHECK(effective_date >= proposed_date),
        UNIQUE(framework_agreement_id, amendment_no)
    )""",
    """CREATE TABLE framework_agreement_scope (
        scope_id INTEGER PRIMARY KEY,
        framework_agreement_id INTEGER NOT NULL REFERENCES framework_agreements(framework_agreement_id),
        category_code TEXT NOT NULL CHECK(category_code IN ('raw_materials','energy','industrial_goods',
            'technology','food','medical','luxury','contraband')),
        archetype_code TEXT,
        system_id INTEGER REFERENCES star_systems(system_id),
        entry_kind TEXT NOT NULL CHECK(entry_kind IN ('include','exclude','exclusivity')),
        exclusivity TEXT,
        valid_from TEXT NOT NULL,
        valid_to TEXT,
        added_by_amendment_id INTEGER REFERENCES framework_agreement_amendments(amendment_id),
        removed_by_amendment_id INTEGER REFERENCES framework_agreement_amendments(amendment_id),
        CHECK(valid_to IS NULL OR valid_to >= valid_from)
    )""",
    """CREATE TABLE correspondence (
        correspondence_id INTEGER PRIMARY KEY,
        correspondence_number TEXT NOT NULL UNIQUE,
        correspondence_type TEXT NOT NULL CHECK(correspondence_type IN ('inquiry','offer','counter_offer',
            'offer_rejection','contract_confirmation','amendment_offer','amendment_confirmation','amendment_rejection',
            'delivery_notice','delay_notice','delay_complaint','penalty_notice','payment_reminder','breach_warning',
            'termination_notice','suspension_notice','protest','confidential_tip','rumor','internal_memo')),
        channel TEXT NOT NULL CHECK(channel IN ('letter','email','encrypted_message','holo_call')),
        direction TEXT NOT NULL CHECK(direction IN ('seller_to_buyer','buyer_to_seller','internal','to_rival',
            'lateral')),
        thread_id INTEGER NOT NULL REFERENCES correspondence(correspondence_id) DEFERRABLE INITIALLY DEFERRED,
        in_reply_to_id INTEGER REFERENCES correspondence(correspondence_id) DEFERRABLE INITIALLY DEFERRED,
        refers_to_correspondence_id INTEGER REFERENCES correspondence(correspondence_id) DEFERRABLE INITIALLY DEFERRED,
        sent_at TEXT NOT NULL CHECK(sent_at < '2060-01-01'),
        is_read INTEGER NOT NULL CHECK(is_read IN (0,1)),
        read_at TEXT,
        sender_company_id INTEGER NOT NULL REFERENCES companies(company_id),
        sender_employee_id INTEGER REFERENCES employees(employee_id),
        sender_station_id INTEGER REFERENCES stations(station_id),
        recipient_company_id INTEGER REFERENCES companies(company_id),
        recipient_employee_id INTEGER REFERENCES employees(employee_id),
        recipient_customer_id INTEGER REFERENCES customers(customer_id),
        language TEXT NOT NULL CHECK(language IN ('de_DE','en_US')),
        subject TEXT NOT NULL,
        body TEXT NOT NULL,
        confidentiality TEXT NOT NULL CHECK(confidentiality IN ('public','internal','confidential')),
        min_intel_access_level INTEGER NOT NULL CHECK(min_intel_access_level BETWEEN 0 AND 3),
        sentiment TEXT NOT NULL CHECK(sentiment IN ('positive','neutral','negative','hostile')),
        amount REAL CHECK(amount IS NULL OR amount >= 0),
        due_date TEXT,
        response_required INTEGER NOT NULL DEFAULT 0 CHECK(response_required IN (0,1)),
        status TEXT NOT NULL CHECK(status IN ('sent','read','answered','rejected','escalated','closed')),
        trust_effect INTEGER NOT NULL CHECK(trust_effect BETWEEN -20 AND 10),
        is_accurate INTEGER CHECK(is_accurate IS NULL OR is_accurate IN (0,1)),
        intel_value INTEGER NOT NULL CHECK(intel_value BETWEEN 0 AND 100),
        leak_status TEXT NOT NULL DEFAULT 'none' CHECK(leak_status IN ('none','rumored','leaked')),
        leaked_by_employee_id INTEGER REFERENCES employees(employee_id),
        leaked_to_company_id INTEGER REFERENCES companies(company_id),
        partnership_id INTEGER REFERENCES trade_partnerships(partnership_id),
        rivalry_id INTEGER REFERENCES company_rivalries(rivalry_id),
        framework_agreement_id INTEGER REFERENCES framework_agreements(framework_agreement_id),
        amendment_id INTEGER REFERENCES framework_agreement_amendments(amendment_id),
        contract_id INTEGER REFERENCES contracts(contract_id),
        order_id INTEGER REFERENCES orders(order_id),
        shipment_id INTEGER REFERENCES shipments(shipment_id),
        event_id INTEGER REFERENCES events(event_id),
        storyline_code TEXT,
        CHECK(recipient_company_id IS NOT NULL OR recipient_customer_id IS NOT NULL),
        CHECK(correspondence_type <> 'internal_memo' OR recipient_company_id = sender_company_id),
        CHECK(recipient_company_id IS NULL OR recipient_company_id <> sender_company_id
              OR correspondence_type = 'internal_memo'),
        CHECK(is_accurate IS NULL OR correspondence_type IN ('confidential_tip','rumor')),
        CHECK((is_read = 1) = (read_at IS NOT NULL)),
        CHECK(read_at IS NULL OR read_at >= sent_at),
        CHECK(leak_status = 'none' OR leaked_by_employee_id IS NOT NULL)
    )""",
    """CREATE TABLE correspondence_copies (
        copy_id INTEGER PRIMARY KEY,
        correspondence_id INTEGER NOT NULL REFERENCES correspondence(correspondence_id) ON DELETE CASCADE,
        employee_id INTEGER NOT NULL REFERENCES employees(employee_id),
        copy_type TEXT NOT NULL CHECK(copy_type IN ('cc','bcc','forward')),
        UNIQUE(correspondence_id, employee_id)
    )""",
    "CREATE INDEX idx_stations_company ON stations(company_id)",
    "CREATE INDEX idx_stations_system ON stations(system_id)",
    "CREATE INDEX idx_products_company ON products(company_id)",
    "CREATE INDEX idx_products_category ON products(category_code)",
    "CREATE INDEX idx_inventory_product ON inventory(product_id)",
    "CREATE INDEX idx_routes_origin ON trade_routes(origin_station_id)",
    "CREATE INDEX idx_routes_destination ON trade_routes(destination_station_id)",
    "CREATE INDEX idx_routes_product ON trade_routes(product_id)",
    "CREATE INDEX idx_routes_company ON trade_routes(company_id)",
    "CREATE INDEX idx_partnerships_partner ON trade_partnerships(partner_company_id)",
    "CREATE INDEX idx_contracts_company ON contracts(company_id)",
    "CREATE INDEX idx_contracts_partner ON contracts(partner_company_id)",
    "CREATE INDEX idx_contracts_route ON contracts(route_id)",
    "CREATE INDEX idx_contracts_framework ON contracts(framework_agreement_id)",
    "CREATE INDEX idx_framework_pair ON framework_agreements(company_id, partner_company_id)",
    "CREATE INDEX idx_amendments_framework ON framework_agreement_amendments(framework_agreement_id, amendment_no)",
    "CREATE INDEX idx_scope_framework ON framework_agreement_scope(framework_agreement_id)",
    "CREATE INDEX idx_customers_company ON customers(company_id)",
    "CREATE INDEX idx_orders_company ON orders(company_id)",
    "CREATE INDEX idx_orders_customer ON orders(customer_id)",
    "CREATE INDEX idx_orders_contract ON orders(contract_id)",
    "CREATE INDEX idx_orders_date ON orders(order_date)",
    "CREATE INDEX idx_order_items_product ON order_items(product_id)",
    "CREATE INDEX idx_shipments_order ON shipments(order_id)",
    "CREATE INDEX idx_price_history_product ON price_history(product_id, date)",
    "CREATE INDEX idx_employees_company ON employees(company_id)",
    "CREATE INDEX idx_employees_station ON employees(station_id)",
    "CREATE INDEX idx_events_station ON events(station_id, event_date)",
    "CREATE INDEX idx_event_effects_station ON event_effects(station_id, product_id)",
    "CREATE INDEX idx_correspondence_sender ON correspondence(sender_company_id, sent_at)",
    "CREATE INDEX idx_correspondence_recipient ON correspondence(recipient_company_id, sent_at)",
    "CREATE INDEX idx_correspondence_thread ON correspondence(thread_id)",
    "CREATE INDEX idx_correspondence_contract ON correspondence(contract_id)",
    "CREATE INDEX idx_correspondence_employee ON correspondence(sender_employee_id)",
)


def open_connection(path: Path) -> sqlite3.Connection:
    """Öffnet eine Verbindung mit aktivierten Fremdschlüsseln und expliziter Transaktionssteuerung."""
    connection = sqlite3.connect(path, isolation_level=None)
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def write_database(world: World, output: Path) -> None:
    """Schreibt Schema und alle Daten in genau einer Transaktion."""
    if output.exists():
        output.unlink()
    output.parent.mkdir(parents=True, exist_ok=True)
    connection = open_connection(output)
    try:
        connection.execute("BEGIN;")
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        for table in INSERT_ORDER:
            rows = world.rows.get(table, [])
            if not rows:
                continue
            columns = [info[1] for info in connection.execute(f"PRAGMA table_info({table})")]
            placeholders = ", ".join("?" for _ in columns)
            sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            connection.executemany(sql, (tuple(row[column] for column in columns) for row in rows))
        violations = connection.execute("PRAGMA foreign_key_check;").fetchall()
        if violations:
            raise RuntimeError(f"Fremdschlüsselverletzungen vor dem Commit: {violations[:5]}")
        connection.execute("COMMIT;")
    except Exception:
        connection.execute("ROLLBACK;")
        raise
    finally:
        connection.close()


# ---------------------------------------------------------------------------
# Qualitätsprüfung
# ---------------------------------------------------------------------------


@dataclass
class CheckResult:
    """Ergebnis einer Qualitätsprüfung."""

    name: str
    passed: bool
    detail: str


def query(connection: sqlite3.Connection, sql: str) -> pd.DataFrame:
    """Führt eine Abfrage aus und liefert ein DataFrame."""
    return pd.read_sql_query(sql, connection)


def scalar(connection: sqlite3.Connection, sql: str) -> Any:
    """Führt eine Abfrage mit genau einem Ergebniswert aus."""
    return connection.execute(sql).fetchone()[0]


def zero_check(connection: sqlite3.Connection, name: str, sql: str, ok_detail: str) -> CheckResult:
    """Prüfung, die bestanden ist, wenn die Abfrage 0 liefert."""
    violations = scalar(connection, sql)
    return CheckResult(name, violations == 0, ok_detail if violations == 0 else f"{violations} Verstöße")


def partner_graph(connection: sqlite3.Connection) -> dict[int, set[int]]:
    """Ungerichteter Graph aktiver Partnerschaften."""
    graph: dict[int, set[int]] = {cid: set() for (cid,) in connection.execute("SELECT company_id FROM companies")}
    for company_id, partner_id in connection.execute(
            "SELECT company_id, partner_company_id FROM trade_partnerships WHERE is_active = 1"):
        graph[company_id].add(partner_id)
        graph[partner_id].add(company_id)
    return graph


def reachable_from(graph: dict[int, set[int]], start: int) -> set[int]:
    """Breitensuche: alle über Partnerschaften erreichbaren Firmen."""
    seen = {start}
    queue = deque([start])
    while queue:
        for neighbour in graph[queue.popleft()]:
            if neighbour not in seen:
                seen.add(neighbour)
                queue.append(neighbour)
    return seen


def framework_scope_covers(scope: pd.DataFrame, category: str, archetype: str, system_id: int, day: str) -> bool:
    """Sortimentsprüfung aus der Tabelle framework_agreement_scope (gleiche Regel wie der Generator)."""
    active = scope[(scope["valid_from"] <= day) & (scope["valid_to"].isna() | (scope["valid_to"] >= day))]
    matches = active[((active["archetype_code"].isna() & (active["category_code"] == category))
                      | (active["archetype_code"] == archetype))
                     & (active["system_id"].isna() | (active["system_id"] == system_id))]
    return bool((matches["entry_kind"] == "include").any() and not (matches["entry_kind"] == "exclude").any())


def framework_quality_checks(connection: sqlite3.Connection) -> list[CheckResult]:
    """Prüfungen der Rahmenverträge: Fremdschlüssel, Daten, Nachträge, Zuordnung, Volumen, Sperren."""
    checks: list[CheckResult] = []
    reference = fmt_date(GAME_REFERENCE_DATE)
    frameworks = query(connection, "SELECT * FROM framework_agreements ORDER BY framework_agreement_id")
    amendments = query(connection, "SELECT * FROM framework_agreement_amendments ORDER BY framework_agreement_id, "
                                   "amendment_no")
    scope = query(connection, "SELECT * FROM framework_agreement_scope")
    contracts = query(connection, """
        SELECT k.contract_id, k.contract_number, k.company_id, k.partner_company_id, k.contract_type, k.status,
               k.start_date, k.total_value, k.framework_agreement_id, p.category_code, p.archetype_code,
               s.system_id AS destination_system_id
        FROM contracts k JOIN products p ON p.product_id = k.product_id
        JOIN stations s ON s.station_id = k.destination_station_id ORDER BY k.start_date, k.contract_id""")
    companies = query(connection, "SELECT company_id, name, slug, language FROM companies").set_index("company_id")
    ids_by_slug = {slug: company_id for company_id, slug in companies["slug"].items()}
    keys = {profile.key: ids_by_slug[profile.slug] for profile in COMPANY_PROFILES}

    checks.append(zero_check(connection, "Rahmenverträge: Paar = aktive Vereinbarung, Sprache des Verkäufers", """
        SELECT COUNT(*) FROM framework_agreements f
        LEFT JOIN trade_partnerships p ON p.partnership_id = f.partnership_id
        JOIN companies c ON c.company_id = f.company_id
        WHERE p.partnership_id IS NULL OR p.is_active = 0 OR p.company_id <> f.company_id
           OR p.partner_company_id <> f.partner_company_id OR f.language <> c.language
           OR p.start_date > f.signed_date""",
        f"{len(frameworks)} Rahmenverträge an aktiven Vereinbarungen"))

    bad_dates = []
    for fw in frameworks.itertuples():
        start = date.fromisoformat(fw.start_date)
        expected_end = shift_months(start, fw.term_months) - timedelta(days=1)
        if not (fw.signed_date < fw.start_date and fw.end_date == fmt_date(expected_end)
                and fw.current_end_date >= fw.end_date):
            bad_dates.append(fw.agreement_number)
    checks.append(CheckResult("Rahmenverträge: Unterzeichnung < Beginn, Ende = Beginn + Laufzeit, "
                              "aktuelles Ende ≥ Ende", not bad_dates,
                              "Datumslogik eingehalten" if not bad_dates else ", ".join(bad_dates)))

    bad_order = []
    for fw in frameworks.itertuples():
        own = amendments[amendments["framework_agreement_id"] == fw.framework_agreement_id]
        prefix = AMENDMENT_PREFIX[fw.language]
        numbers_ok = list(own["amendment_no"]) == list(range(1, len(own) + 1)) and all(
            own["amendment_number"] == [f"{fw.agreement_number}/{prefix}{n}" for n in own["amendment_no"]])
        proposed = list(own["proposed_date"])
        chronological = proposed == sorted(proposed)
        within = own.empty or (own["proposed_date"].min() >= fw.signed_date
                               and own["proposed_date"].max() < reference
                               and bool((own["signed_date"].dropna() < reference).all()))
        logical = all((not isinstance(r.signed_date, str) or r.proposed_date <= r.signed_date <= r.effective_date)
                      and r.proposed_date <= r.effective_date and r.effective_date >= fw.start_date
                      for r in own.itertuples())
        if not (numbers_ok and chronological and within and logical):
            bad_order.append(fw.agreement_number)
    checks.append(CheckResult(
        "Nachträge chronologisch nummeriert (Angebot ≤ Unterzeichnung ≤ Wirkung, nach Rahmenunterzeichnung, ≤ 2059)",
        not bad_order, f"{len(amendments)} Nachträge in Reihenfolge" if not bad_order else ", ".join(bad_order)))

    def end_at(fw: Any, own: pd.DataFrame, day: str) -> str:
        extensions = own[(own["amendment_type"] == "term_extension") & own["status"].isin(["signed", "proposed"])
                         & (own["effective_date"] <= day) & own["end_date_new"].notna()]
        return max([fw.end_date, *extensions["end_date_new"]])

    bad_assigned, unassigned, volume_issues, chain_issues = [], [], [], []
    pairs = frameworks.set_index("framework_agreement_id")[["company_id", "partner_company_id"]]
    for k in contracts[contracts["framework_agreement_id"].notna()].itertuples():
        frame_pair = pairs.loc[int(k.framework_agreement_id)]
        if (k.company_id, k.partner_company_id) != (frame_pair["company_id"], frame_pair["partner_company_id"]):
            bad_assigned.append(k.contract_number)
    for fw in frameworks.itertuples():
        own = amendments[amendments["framework_agreement_id"] == fw.framework_agreement_id]
        own_scope = scope[scope["framework_agreement_id"] == fw.framework_agreement_id]
        suspensions = own[(own["amendment_type"] == "suspension") & (own["status"] == "signed")]["effective_date"]
        suspended_from = suspensions.min() if not suspensions.empty else None
        pair = contracts[(contracts["company_id"] == fw.company_id)
                         & (contracts["partner_company_id"] == fw.partner_company_id)]
        for k in pair.itertuples():
            eligible = (k.contract_type in FRAMEWORK_CALLOFF_TYPES and k.start_date >= fw.start_date
                        and (suspended_from is None or k.start_date < suspended_from)
                        and k.start_date <= end_at(fw, own, k.start_date)
                        and framework_scope_covers(own_scope, k.category_code, k.archetype_code,
                                                   k.destination_system_id, k.start_date))
            assigned = k.framework_agreement_id == fw.framework_agreement_id
            if assigned and not eligible:
                bad_assigned.append(k.contract_number)
            elif eligible and not assigned:
                unassigned.append(k.contract_number)
        # Volumen: kumulierte Abrufe (ohne Stornos) nie über der am Vertragsbeginn gültigen Obergrenze
        volume_rows = own[own["amendment_type"].isin(["volume_increase", "volume_reduction"])
                          & own["status"].isin(["signed", "proposed"])].sort_values(["effective_date", "amendment_no"])
        previous = fw.base_volume
        for amendment in volume_rows.itertuples():
            if (abs(amendment.volume_before - previous) > 0.01
                    or abs(amendment.volume_after - amendment.volume_before - amendment.volume_delta) > 0.01):
                chain_issues.append(amendment.amendment_number)
            previous = amendment.volume_after
            if amendment.rule == "cumulative_over_90pct":
                trigger = contracts[contracts["contract_id"] == amendment.trigger_contract_id]
                if (trigger.empty or trigger.iloc[0]["framework_agreement_id"] != fw.framework_agreement_id
                        or amendment.effective_date > trigger.iloc[0]["start_date"]):
                    chain_issues.append(amendment.amendment_number)
        cumulative = 0.0
        for k in contracts[(contracts["framework_agreement_id"] == fw.framework_agreement_id)
                           & (contracts["status"] != "cancelled")].itertuples():
            cumulative += k.total_value
            statuses = ["signed", "proposed"] if k.status == "draft" else ["signed"]
            valid = volume_rows[volume_rows["status"].isin(statuses) & (volume_rows["effective_date"] <= k.start_date)]
            cap = valid.iloc[-1]["volume_after"] if not valid.empty else fw.base_volume
            if cumulative > cap + 0.01:
                volume_issues.append(f"{fw.agreement_number} bei {k.contract_number}")
                break
    checks.append(CheckResult(
        "Zugeordnete Verträge: gleiches Paar, Abruftyp, Beginn in der (verlängerten) Laufzeit, Ware im Sortiment",
        not bad_assigned and contracts["framework_agreement_id"].notna().sum() > 0,
        f"{int(contracts['framework_agreement_id'].notna().sum())} Verträge zugeordnet" if not bad_assigned
        else f"{len(bad_assigned)} Verstöße, z. B. {', '.join(bad_assigned[:5])}"))
    checks.append(CheckResult("Zuordnung vollständig: jeder passende Abrufvertrag gehört zu seinem Rahmen",
                              not unassigned, "deterministisch und vollständig" if not unassigned
                              else f"{len(unassigned)} fehlen, z. B. {', '.join(unassigned[:5])}"))
    checks.append(CheckResult(
        "Rahmenvolumen inkl. Nachträgen nie überschritten; Volumen-Nachträge lückenlos und vor ihrem Auslöser",
        not volume_issues and not chain_issues,
        "Summe der Abrufe ≤ Obergrenze zu jedem Vertragsbeginn" if not volume_issues and not chain_issues
        else "; ".join(volume_issues[:3] + chain_issues[:3])))

    bad_state = []
    for fw in frameworks.itertuples():
        signed = amendments[(amendments["framework_agreement_id"] == fw.framework_agreement_id)
                            & (amendments["status"] == "signed")].sort_values(["effective_date", "amendment_no"])
        volumes = signed[signed["amendment_type"].isin(["volume_increase", "volume_reduction"])]["volume_after"]
        ends = signed[signed["amendment_type"] == "term_extension"]["end_date_new"].dropna()
        cap = volumes.iloc[-1] if not volumes.empty else fw.base_volume
        end = max([fw.end_date, *ends])
        suspended = ((signed["amendment_type"] == "suspension") & (signed["effective_date"] < reference)).any()
        status = "suspended" if suspended else ("expired" if end < reference else
                                                ("negotiating" if fw.start_date > reference else "active"))
        if abs(cap - fw.current_volume_cap) > 0.01 or end != fw.current_end_date or status != fw.status:
            bad_state.append(fw.agreement_number)
    checks.append(CheckResult("Aktuelles Volumen, Ende und Status des Rahmens folgen aus den unterzeichneten "
                              "Nachträgen", not bad_state, "konsistent" if not bad_state else ", ".join(bad_state)))

    checks.append(zero_check(connection, "Unterzeichner am Unterzeichnungstag bei der Vertragspartei beschäftigt", """
        SELECT COUNT(*) FROM framework_agreements f
        LEFT JOIN employees s ON s.employee_id = f.seller_signatory_id
        LEFT JOIN employees b ON b.employee_id = f.buyer_signatory_id
        WHERE s.employee_id IS NULL OR b.employee_id IS NULL
           OR s.company_id <> f.company_id OR b.company_id <> f.partner_company_id
           OR s.hire_date > f.signed_date OR b.hire_date > f.signed_date
           OR (s.termination_date IS NOT NULL AND s.termination_date <= f.signed_date)
           OR (b.termination_date IS NOT NULL AND b.termination_date <= f.signed_date)""",
        "alle Unterschriften gültig"))

    station_types = query(connection, "SELECT company_id, station_type FROM stations")
    types_by_company = station_types.groupby("company_id")["station_type"].agg(set).to_dict()
    consumers_by_category: dict[str, frozenset[str]] = defaultdict(frozenset)
    for archetype in PRODUCT_ARCHETYPES:
        consumers_by_category[archetype.category] |= archetype.consumers
    no_consumer = []
    for entry in scope[scope["entry_kind"] == "include"].itertuples():
        buyer = frameworks.loc[frameworks["framework_agreement_id"] == entry.framework_agreement_id].iloc[0]
        consumers = (ARCHETYPES_BY_CODE[entry.archetype_code].consumers if isinstance(entry.archetype_code, str)
                     else consumers_by_category[entry.category_code])
        if not consumers & types_by_company[buyer["partner_company_id"]]:
            no_consumer.append(f"{buyer['agreement_number']}:{entry.archetype_code or entry.category_code}")
    checks.append(CheckResult("Jede Sortimentsposition hat beim Käufer einen verbrauchenden Stationstyp",
                              not no_consumer, f"{int((scope['entry_kind'] == 'include').sum())} Positionen geprüft"
                              if not no_consumer else ", ".join(no_consumer[:6])))

    # Exklusivitätssperren der neuen Verkäufer (Verträge nach Beginn, Partner-Spotbestellungen nach Datum)
    sales = query(connection, """
        SELECT k.contract_number AS ref, k.company_id, k.partner_company_id AS buyer_id, k.start_date AS day,
               p.category_code, p.archetype_code, s.system_id
        FROM contracts k JOIN products p ON p.product_id = k.product_id
        JOIN stations s ON s.station_id = k.destination_station_id
        UNION ALL
        SELECT o.order_number, o.company_id, o.customer_company_id, substr(o.order_date, 1, 10),
               p.category_code, p.archetype_code, s.system_id
        FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON p.product_id = oi.product_id JOIN stations s ON s.station_id = o.destination_station_id
        WHERE o.contract_id IS NULL""")
    system_ids = dict(query(connection, "SELECT code, system_id FROM star_systems").itertuples(index=False))
    violations = []
    for rule in EXCLUSIVITY_FILTERS:
        hit = sales[sales["company_id"].isin([keys[k] for k in rule["sellers"]])]
        if "categories" in rule:
            hit = hit[hit["category_code"].isin(rule["categories"])]
        if "archetypes" in rule:
            hit = hit[hit["archetype_code"].isin(rule["archetypes"])]
        if "system" in rule:
            hit = hit[hit["system_id"] == system_ids[rule["system"]]]
        if "from" in rule:
            hit = hit[hit["day"] >= rule["from"]]
        if "until" in rule:
            hit = hit[hit["day"] <= rule["until"]]
        if "allowed_buyer" in rule:
            hit = hit[hit["buyer_id"] != keys[rule["allowed_buyer"]]]
        else:
            hit = hit[hit["buyer_id"] == keys[rule["buyer"]]]
        violations += list(hit["ref"])
    checks.append(CheckResult("Keine Exklusivitätsverstöße neuer Verkäufer (Verträge und Spotbestellungen)",
                              not violations, f"{len(EXCLUSIVITY_FILTERS)} Sperren eingehalten" if not violations
                              else f"{len(violations)} Verstöße, z. B. {', '.join(violations[:5])}"))

    employees = query(connection, "SELECT employee_id, company_id, role_code, hire_date, is_active FROM employees "
                                  "ORDER BY employee_id")
    cap_violations = []
    for key, cap in HIRE_DATE_CAPS.items():
        staff = employees[employees["company_id"] == keys[key]]
        for role in HIRE_CAP_ROLES:
            first = staff[staff["role_code"] == role].head(1)
            if not first.empty and (first.iloc[0]["hire_date"] > fmt_date(cap) or not first.iloc[0]["is_active"]):
                cap_violations.append(f"{companies.loc[keys[key], 'name']}: {role}")
    checks.append(CheckResult("Einstellungsgrenzen neuer Firmen (Vorstand, erste Partnerbetreuung/Marktaufklärung)",
                              not cap_violations, f"{len(HIRE_DATE_CAPS)} Firmen geprüft" if not cap_violations
                              else "; ".join(cap_violations)))
    return checks


def correspondence_quality_checks(connection: sqlite3.Connection, seed: int) -> list[CheckResult]:
    """Prüfungen des Schriftverkehrs: Menge, Personen, Fäden, Bezüge, Zeitfolge, Strafen, Mahnungen, Lecks."""
    checks: list[CheckResult] = []
    letters = query(connection, "SELECT * FROM correspondence ORDER BY correspondence_id")
    copies = query(connection, "SELECT * FROM correspondence_copies")
    companies = query(connection, "SELECT company_id, slug, language FROM companies").set_index("company_id")
    employees = query(connection, "SELECT * FROM employees").set_index("employee_id")
    contracts = query(connection, "SELECT * FROM contracts").set_index("contract_id")
    orders = query(connection, "SELECT * FROM orders").set_index("order_id")
    shipments = query(connection, "SELECT * FROM shipments").set_index("shipment_id")
    events = query(connection, "SELECT event_id, event_date FROM events").set_index("event_id")
    frameworks = query(connection, "SELECT * FROM framework_agreements").set_index("framework_agreement_id")
    amendments = query(connection, "SELECT * FROM framework_agreement_amendments").set_index("amendment_id")
    partnerships = query(connection, "SELECT * FROM trade_partnerships").set_index("partnership_id")
    rivalries = query(connection, "SELECT * FROM company_rivalries").set_index("rivalry_id")
    customers = query(connection, "SELECT customer_id, company_id FROM customers").set_index("customer_id")
    legacy_ids = {cid for cid, slug in companies["slug"].items()
                  if slug in {p.slug for p in COMPANY_PROFILES if p.key in LEGACY_COMPANY_KEYS}}
    prefixes = {cid: next(p.sku_prefix for p in COMPANY_PROFILES if p.slug == slug)
                for cid, slug in companies["slug"].items()}

    def ref(value: Any) -> int | None:
        return None if value is None or (isinstance(value, float) and math.isnan(value)) else int(value)

    # 1. Menge und Beteiligung
    involved = set(letters["sender_company_id"]) | {int(c) for c in letters["recipient_company_id"].dropna()}
    legacy_letters = 0
    for row in letters.itertuples():
        contract_id = ref(row.contract_id)
        if (contract_id is not None and row.sender_company_id in legacy_ids
                and ref(row.recipient_company_id) in legacy_ids
                and contracts.loc[contract_id, "company_id"] in legacy_ids
                and contracts.loc[contract_id, "partner_company_id"] in legacy_ids):
            legacy_letters += 1
    types = set(letters["correspondence_type"])
    checks.append(CheckResult(
        "Schriftverkehr: 2.000–6.000 Schreiben, alle 20 Briefarten, alle 18 Firmen, Bestandsfirmen untereinander",
        2000 <= len(letters) <= 6000 and types == set(CORRESPONDENCE_TYPES) and len(involved) == len(companies)
        and legacy_letters >= 100,
        f"{len(letters)} Schreiben, {len(types)} Briefarten, {len(involved)} Firmen, {legacy_letters} zwischen "
        f"Bestandsfirmen zu Bestandsverträgen, {len(copies)} Kopien"))

    # 2. Nummern, Sprache, Parteien
    markers = {"de_DE": ("Mit freundlichen Grüßen", "Gesprächsnotiz", "[Verschlüsselte Nachricht"),
               "en_US": ("Kind regards", "Call note", "[Encrypted message")}
    bad_form = []
    for row in letters.itertuples():
        language = companies.loc[row.sender_company_id, "language"]
        expected = f"{prefixes[row.sender_company_id]}-{CORRESPONDENCE_PREFIX[language]}-{row.sent_at[:4]}-"
        recipient_company = ref(row.recipient_company_id)
        internal = recipient_company == row.sender_company_id
        if (row.language != language or not row.correspondence_number.startswith(expected)
                or len(row.correspondence_number) != len(expected) + 5
                or not any(marker in row.body for marker in markers[language])
                or (row.correspondence_type == "internal_memo") != internal
                or row.channel not in CORRESPONDENCE_CHANNELS or row.direction not in CORRESPONDENCE_DIRECTIONS
                or row.sentiment not in SENTIMENTS or row.status not in CORRESPONDENCE_STATUSES
                or row.confidentiality not in CONFIDENTIALITY_LEVELS
                or (recipient_company is None and ref(row.recipient_customer_id) is None)):
            bad_form.append(row.correspondence_number)
    checks.append(CheckResult("Schriftverkehr: Nummer je Absender und Jahr, Sprache und Text der Absenderfirma, "
                              "Wertelisten, interne Notizen nur firmenintern", not bad_form,
                              "alle Schreiben korrekt" if not bad_form
                              else f"{len(bad_form)} Verstöße, z. B. {bad_form[:3]}"))

    # 3. Personen gehören zur Firma und sind beim Versand beschäftigt
    def employed(employee_id: int | None, company_id: int | None, day: str) -> bool:
        if employee_id is None or employee_id not in employees.index:
            return False
        employee = employees.loc[employee_id]
        return (employee["company_id"] == company_id and employee["hire_date"] <= day
                and (not isinstance(employee["termination_date"], str) or employee["termination_date"] > day))

    bad_people = []
    by_id = letters.set_index("correspondence_id")
    for row in letters.itertuples():
        day = row.sent_at[:10]
        ok = employed(ref(row.sender_employee_id), row.sender_company_id, day)
        if ref(row.recipient_employee_id) is not None:
            ok = ok and employed(ref(row.recipient_employee_id), ref(row.recipient_company_id), day)
        elif ref(row.recipient_customer_id) is not None:
            ok = ok and customers.loc[ref(row.recipient_customer_id), "company_id"] == row.sender_company_id
        else:
            ok = False
        if not ok:
            bad_people.append(row.correspondence_number)
    for copy in copies.itertuples():
        letter = by_id.loc[copy.correspondence_id]
        if copy.copy_type not in COPY_TYPES or not any(employed(copy.employee_id, company, letter["sent_at"][:10])
                   for company in (letter["sender_company_id"], ref(letter["recipient_company_id"]))):
            bad_people.append(f"Kopie {copy.copy_id}")
    checks.append(CheckResult("Absender, Empfänger und Kopien gehören zur jeweiligen Firma und sind am Versandtag "
                              "beschäftigt", not bad_people, f"{len(letters)} Schreiben, {len(copies)} Kopien geprüft"
                              if not bad_people else f"{len(bad_people)} Verstöße, z. B. {bad_people[:3]}"))

    # 4. Gesprächsfäden
    checks.append(zero_check(connection, "Gesprächsfäden: Antworten nach dem Original an dessen Absender, Vorgang "
                                         "beginnt mit dem ersten Schreiben, alles vor dem Stichtag", """
        SELECT COUNT(*) FROM correspondence k
        LEFT JOIN correspondence p ON p.correspondence_id = k.in_reply_to_id
        JOIN correspondence t ON t.correspondence_id = k.thread_id
        LEFT JOIN correspondence q ON q.correspondence_id = k.refers_to_correspondence_id
        WHERE (p.correspondence_id IS NOT NULL AND (p.sent_at >= k.sent_at OR p.thread_id <> k.thread_id
               OR p.sender_company_id IS NOT k.recipient_company_id
               OR p.recipient_company_id IS NOT k.sender_company_id))
           OR t.sent_at > k.sent_at OR t.thread_id <> t.correspondence_id
           OR (q.correspondence_id IS NOT NULL AND q.sent_at >= k.sent_at)
           OR k.sent_at >= '2060-01-01'
           OR (k.read_at IS NOT NULL AND (k.read_at < k.sent_at OR k.read_at >= '2060-01-01'))
           OR (k.status IN ('answered','rejected') AND NOT EXISTS (
               SELECT 1 FROM correspondence a WHERE a.in_reply_to_id = k.correspondence_id))""",
        f"{int(letters['in_reply_to_id'].notna().sum())} Antworten, {letters['thread_id'].nunique()} Vorgänge"))

    # 5. Bezugsobjekte passen zu den Parteien, 6. kein Schreiben vor seinem Bezugsobjekt
    bad_refs, too_early = [], []
    for row in letters.itertuples():
        sender, recipient = row.sender_company_id, ref(row.recipient_company_id)
        parties = {sender, recipient} - {None}
        objects: list[tuple[str, set[int | None]]] = []
        ok = True
        contract_id, order_id, shipment_id = ref(row.contract_id), ref(row.order_id), ref(row.shipment_id)
        framework_id, amendment_id = ref(row.framework_agreement_id), ref(row.amendment_id)
        if contract_id is not None:
            contract = contracts.loc[contract_id]
            objects.append(("contract", {contract["company_id"], contract["partner_company_id"]}))
            if framework_id is not None and ref(contract["framework_agreement_id"]) not in (None, framework_id):
                ok = False
        if shipment_id is not None:
            shipment = shipments.loc[shipment_id]
            ok = ok and (order_id is None or int(shipment["order_id"]) == order_id)
            order_id = order_id or int(shipment["order_id"])
        if order_id is not None:
            order = orders.loc[order_id]
            customer_company = ref(order["customer_company_id"])
            if customer_company is None:
                ok = (ok and order["company_id"] == sender
                      and ref(row.recipient_customer_id) == int(order["customer_id"]))
            else:
                objects.append(("order", {order["company_id"], customer_company}))
            if contract_id is not None and ref(order["contract_id"]) is not None:
                ok = ok and ref(order["contract_id"]) == contract_id
        if amendment_id is not None:
            amendment = amendments.loc[amendment_id]
            ok = ok and (framework_id is None or int(amendment["framework_agreement_id"]) == framework_id)
            framework_id = framework_id or int(amendment["framework_agreement_id"])
        if framework_id is not None:
            framework = frameworks.loc[framework_id]
            objects.append(("framework", {framework["company_id"], framework["partner_company_id"]}))
        if ref(row.partnership_id) is not None:
            partnership = partnerships.loc[ref(row.partnership_id)]
            objects.append(("partnership", {partnership["company_id"], partnership["partner_company_id"]}))
        if ref(row.rivalry_id) is not None:
            rivalry = rivalries.loc[ref(row.rivalry_id)]
            objects.append(("rivalry", {rivalry["company_id"], rivalry["rival_company_id"]}))
        for kind, owners in objects:
            if row.correspondence_type in EXEMPT_PARTY_TYPES or kind == "rivalry":
                ok = ok and bool(owners & parties)
            else:
                ok = ok and owners == parties
        if not ok:
            bad_refs.append(row.correspondence_number)
        sent = row.sent_at
        source = ref(row.refers_to_correspondence_id)
        negotiation = row.correspondence_type in NEGOTIATION_TYPES or (
            row.correspondence_type in ("confidential_tip", "rumor") and source is not None
            and by_id.loc[source, "correspondence_type"] in NEGOTIATION_TYPES)  # Leck eines Angebots
        early = ((order_id is not None and sent < orders.loc[order_id, "order_date"])
                 or (shipment_id is not None and sent < shipments.loc[shipment_id, "departure_date"])
                 or (ref(row.event_id) is not None and sent[:10] < events.loc[ref(row.event_id), "event_date"])
                 or (contract_id is not None and not negotiation
                     and sent[:10] < contracts.loc[contract_id, "start_date"])
                 or (framework_id is not None and not negotiation
                     and sent[:10] < frameworks.loc[framework_id, "signed_date"])
                 or (amendment_id is not None and sent[:10] < amendments.loc[amendment_id, "proposed_date"])
                 or (ref(row.partnership_id) is not None
                     and sent[:10] < partnerships.loc[ref(row.partnership_id), "start_date"]))
        if early:
            too_early.append(row.correspondence_number)
    checks.append(CheckResult("Bezugsobjekte passen zu den Firmen (Vertrag, Bestellung, Lieferung, Rahmen, Nachtrag, "
                              "Vereinbarung = Absender/Empfänger; Tipps/Notizen/Proteste betreffen eine Partei)",
                              not bad_refs, "alle Bezüge stimmig" if not bad_refs
                              else f"{len(bad_refs)} Verstöße, z. B. {bad_refs[:3]}"))
    checks.append(CheckResult("Kein Schreiben vor seinem Bezugsobjekt (Bestellung, Abflug, Ereignis, Vertragsbeginn, "
                              "Unterzeichnung, Nachtragsangebot, Vereinbarung)", not too_early,
                              "Zeitfolge eingehalten" if not too_early
                              else f"{len(too_early)} Verstöße, z. B. {too_early[:3]}"))

    # 7. Vertragsstrafen: Formel und Monatssummen
    penalty_rows = query(connection, """
        SELECT k.contract_id, k.contract_number, k.company_id, k.partner_company_id, k.deadline, k.penalty_per_day,
               MAX(s.actual_arrival_date) AS last_arrival, SUM(s.actual_arrival_date IS NULL) AS open_shipments
        FROM contracts k JOIN orders o ON o.contract_id = k.contract_id JOIN shipments s ON s.order_id = o.order_id
        WHERE k.status = 'breached' GROUP BY k.contract_id""")
    notices = letters[letters["correspondence_type"] == "penalty_notice"]
    expected_sum: dict[tuple[int, str], float] = defaultdict(float)
    bad_penalty = []
    expected_count = 0
    for row in penalty_rows.itertuples():
        last = (GAME_REFERENCE_DATETIME - timedelta(days=1) if row.open_shipments
                else datetime.fromisoformat(row.last_arrival))
        late_days = max(0, (last.date() - date.fromisoformat(row.deadline)).days)
        amount = late_days * row.penalty_per_day
        own = notices[notices["contract_id"] == row.contract_id]
        if amount <= 0:
            if len(own):
                bad_penalty.append(row.contract_number)
            continue
        expected_count += 1
        if (len(own) != 1 or abs(own.iloc[0]["amount"] - amount) > 0.011
                or own.iloc[0]["sender_company_id"] != row.partner_company_id
                or own.iloc[0]["recipient_company_id"] != row.company_id or own.iloc[0]["sent_at"] < fmt_dt(last)):
            bad_penalty.append(row.contract_number)
            continue
        expected_sum[(row.company_id, last.strftime("%Y-%m"))] += float(own.iloc[0]["amount"])
    financials = query(connection, "SELECT company_id, period, contract_penalties FROM company_financials WHERE "
                                   "contract_penalties > 0")
    booked = {(r.company_id, r.period): r.contract_penalties for r in financials.itertuples()}
    month_issues = [f"{c}/{p}" for (c, p) in set(booked) | set(expected_sum)
                    if abs(booked.get((c, p), 0.0) - expected_sum.get((c, p), 0.0)) > 0.05]
    checks.append(CheckResult(
        "Strafbescheide = Verzugstage × penalty_per_day; Summe je Firma und Monat = contract_penalties",
        not bad_penalty and not month_issues and len(notices) == expected_count,
        f"{len(notices)} Bescheide über {fmt_number(notices['amount'].sum(), 'de_DE', 2)} CR, {len(booked)} "
        "Firmenmonate stimmen" if not bad_penalty and not month_issues
        else f"{len(bad_penalty)} Bescheide, {len(month_issues)} Monate abweichend, "
             f"z. B. {(bad_penalty + month_issues)[:4]}"))

    # 8. Mahnungen
    reminders = letters[letters["correspondence_type"] == "payment_reminder"]
    bad_reminders = []
    for order_id, group in reminders.groupby("order_id"):
        order = orders.loc[int(order_id)]
        shipment = shipments[shipments["order_id"] == int(order_id)]
        if (order["payment_status"] != "overdue" or shipment.empty
                or not isinstance(shipment.iloc[0]["actual_arrival_date"], str)):
            bad_reminders.append(order["order_number"])
            continue
        arrival = datetime.fromisoformat(shipment.iloc[0]["actual_arrival_date"]).date()
        due = arrival + timedelta(days=PAYMENT_TERMS_DAYS)
        for stage, row in enumerate(group.sort_values("sent_at").itertuples()):
            offset = (date.fromisoformat(row.sent_at[:10]) - due).days
            low, high = REMINDER_STAGE_DAYS[stage] if stage < len(REMINDER_STAGE_DAYS) else (999, 999)
            if (not low <= offset <= high or row.amount < order["total_amount"] - 0.01
                    or row.sender_company_id != order["company_id"] or row.due_date != fmt_date(due)):
                bad_reminders.append(f"{order['order_number']}#{stage + 1}")
    checks.append(CheckResult("Mahnungen nur bei überfälligen Bestellungen, Stufen Fälligkeit +3..7 / +21 / +45 Tage",
                              not bad_reminders, f"{len(reminders)} Mahnungen zu {reminders['order_id'].nunique()} "
                              "Bestellungen" if not bad_reminders
                              else f"{len(bad_reminders)} Verstöße, z. B. {bad_reminders[:3]}"))

    # 9. Verzugsbeschwerden nur bei echter Verspätung
    complaints = letters[letters["correspondence_type"] == "delay_complaint"]
    bad_complaints = []
    for row in complaints.itertuples():
        shipment_id = ref(row.shipment_id)
        if shipment_id is None:
            bad_complaints.append(row.correspondence_number)
            continue
        shipment = shipments.loc[shipment_id]
        order = orders.loc[int(shipment["order_id"])]
        planned = datetime.fromisoformat(shipment["arrival_date"])
        actual = (datetime.fromisoformat(shipment["actual_arrival_date"])
                  if isinstance(shipment["actual_arrival_date"], str) else None)
        contract_id = ref(order["contract_id"])
        breached = contract_id is not None and contracts.loc[contract_id, "status"] == "breached"
        late = actual is not None and (actual - planned).total_seconds() / 3600 > LATE_COMPLAINT_HOURS
        if (not (late or breached or order["status"] == "delayed")
                or row.sender_company_id != order["customer_company_id"]):
            bad_complaints.append(row.correspondence_number)
    checks.append(CheckResult("Verzugsbeschwerden nur bei > 48 h Verspätung, Vertragsbruch oder Status delayed "
                              "(Käufer an Verkäufer)", not bad_complaints, f"{len(complaints)} Beschwerden"
                              if not bad_complaints else f"{len(bad_complaints)} Verstöße, z. B. {bad_complaints[:3]}"))

    # 10. Rahmen und Nachträge
    bad_frames = []
    for fid, framework in frameworks.iterrows():
        own = letters[letters["framework_agreement_id"] == fid]
        confirmations = own[(own["correspondence_type"] == "contract_confirmation") & own["contract_id"].isna()]
        if framework["start_date"] < fmt_date(GAME_REFERENCE_DATE) and (
                len(confirmations) != 1 or confirmations.iloc[0]["sent_at"][:10] != framework["start_date"]
                or confirmations.iloc[0]["sender_company_id"] != framework["partner_company_id"]):
            bad_frames.append(framework["agreement_number"])
        talks = own[own["correspondence_type"].isin(["inquiry", "offer", "counter_offer"]) & own["contract_id"].isna()
                    & own["amendment_id"].isna()]
        if talks.empty or (talks["sent_at"].str[:10] >= framework["signed_date"]).any():
            bad_frames.append(f"{framework['agreement_number']} (Verhandlung)")
    for aid, amendment in amendments.iterrows():
        own = letters[letters["amendment_id"] == aid]
        framework = frameworks.loc[amendment["framework_agreement_id"]]
        initiator = amendment["initiated_by_company_id"]
        other = framework["partner_company_id"] if initiator == framework["company_id"] else framework["company_id"]
        opening = own[(own["sender_company_id"] == initiator) & (own["sent_at"].str[:10] == amendment["proposed_date"])]
        if amendment["status"] == "signed":
            closing = own[(own["correspondence_type"] == "amendment_confirmation") & (own["sender_company_id"] == other)
                          & (own["sent_at"].str[:10] == amendment["signed_date"])]
        elif amendment["status"] == "rejected":
            closing = own[(own["correspondence_type"] == "amendment_rejection") & (own["sender_company_id"] == other)
                          & (own["sent_at"].str[:10] <= amendment["effective_date"])]
        else:
            closing = own.head(1)
        if opening.empty or closing.empty:
            bad_frames.append(amendment["amendment_number"])
    checks.append(CheckResult("Rahmen: Verhandlung vor der Unterzeichnung, Bestätigung zum Vertragsstart; jeder "
                              "Nachtrag mit Angebot am Angebotsdatum und Bestätigung/Ablehnung der Gegenseite",
                              not bad_frames, f"{len(frameworks)} Rahmen, {len(amendments)} Nachträge belegt"
                              if not bad_frames else f"{len(bad_frames)} Lücken, z. B. {bad_frames[:4]}"))

    # 11. Lecks und Spionage
    bad_leaks = []
    for row in letters[letters["leaked_by_employee_id"].notna()].itertuples():
        leaker_id = int(row.leaked_by_employee_id)
        leaker = employees.loc[leaker_id]
        rule = leaker["bribe_susceptibility"] >= 50 or leaker["loyalty"] <= 50
        if row.correspondence_type in ("confidential_tip", "rumor"):
            ok = rule and ref(row.sender_employee_id) == leaker_id
            original = ref(row.refers_to_correspondence_id)
            if original is not None and by_id.loc[original, "leak_status"] != "none":
                ok = ok and leaker["intel_access_level"] >= by_id.loc[original, "min_intel_access_level"]
        else:
            ok = (rule and row.leak_status != "none" and row.confidentiality != "public"
                  and leaker["intel_access_level"] >= row.min_intel_access_level
                  and any(employed(leaker_id, company, row.sent_at[:10])
                          for company in (row.sender_company_id, ref(row.recipient_company_id)))
                  and not letters[(letters["refers_to_correspondence_id"] == row.correspondence_id)
                                  & (letters["sender_employee_id"] == leaker_id)].empty)
        if not ok:
            bad_leaks.append(row.correspondence_number)
    bad_leaks += list(letters[(letters["leak_status"] != "none") & letters["leaked_by_employee_id"].isna()]
                      ["correspondence_number"])
    tips = letters[letters["correspondence_type"].isin(["confidential_tip", "rumor"])]
    checks.append(CheckResult("Lecks: Leck-Regel (Bestechlichkeit ≥ 50 oder Loyalität ≤ 50), Zugangsstufe, Tipp "
                              "verweist auf das Original; Wahrheitsgehalt nur bei Tipps/Gerüchten", not bad_leaks,
                              f"{len(tips)} Tipps/Gerüchte, {int((letters['leak_status'] != 'none').sum())} geleakte "
                              f"Schreiben, {int((letters['confidentiality'] == 'confidential').sum())} vertraulich"
                              if not bad_leaks else f"{len(bad_leaks)} Verstöße, z. B. {bad_leaks[:3]}"))

    if seed == BASELINE_SEED:
        present = set(letters["storyline_code"].dropna())
        lacking = [code for code in STORYLINE_CODES if code not in present]
        checks.append(CheckResult(f"Verankerte Vorgänge V1–V{len(STORYLINE_CODES)} umgesetzt (Seed 42)", not lacking,
                                  f"{len(present)} Vorgänge mit {int(letters['storyline_code'].notna().sum())} "
                                  "Schreiben"
                                  if not lacking else f"fehlen: {', '.join(lacking)}"))
    return checks


def baseline_quality_checks(connection: sqlite3.Connection, baseline: Path) -> tuple[list[CheckResult], pd.DataFrame]:
    """Bestandsvergleich (Seed 42): Zeilen des alten Datenstands müssen unverändert enthalten sein."""
    connection.execute(f"ATTACH DATABASE '{baseline.as_posix()}' AS baseline")
    rows = []
    try:
        tables = [name for (name,) in connection.execute(
            "SELECT name FROM baseline.sqlite_master WHERE type = 'table' ORDER BY rowid")]
        for table in tables:
            columns = ", ".join(info[1] for info in connection.execute(f"PRAGMA baseline.table_info({table})"))
            old = scalar(connection, f"SELECT COUNT(*) FROM baseline.{table}")
            changed = scalar(connection, f"SELECT COUNT(*) FROM (SELECT {columns} FROM baseline.{table} "
                                         f"EXCEPT SELECT {columns} FROM main.{table})")
            now = scalar(connection, f"SELECT COUNT(*) FROM {table}")
            rows.append({"table": table, "baseline_rows": old, "rows_now": now, "unchanged": old - changed,
                         "changed": changed})
    finally:
        connection.execute("DETACH DATABASE baseline")
    frame = pd.DataFrame(rows)
    master = frame[frame["table"].isin(["companies", "star_systems", "stations", "products", "employees"])]
    movement = frame[~frame["table"].isin(master["table"])]
    checks = [
        CheckResult("Bestandsvergleich: Stammdaten der 6 Bestandsfirmen identisch (Firmen, Systeme, Stationen, "
                    "Produkte, Mitarbeiter)", int(master["changed"].sum()) == 0,
                    f"{int(master['unchanged'].sum())} von {int(master['baseline_rows'].sum())} Zeilen unverändert"),
        CheckResult("Bestandsvergleich: Bewegungsdaten der Bestandsfirmen unverändert (Routen bis Finanzen)",
                    int(movement["changed"].sum()) == 0,
                    f"{int(movement['unchanged'].sum())} von {int(movement['baseline_rows'].sum())} Zeilen unverändert"),
    ]
    assigned = scalar(connection, f"SELECT COUNT(*) FROM contracts WHERE framework_agreement_id IS NOT NULL "
                                  f"AND company_id <= {len(LEGACY_COMPANY_KEYS)}")
    triggers = {number for (number,) in connection.execute("""
        SELECT k.contract_number FROM framework_agreement_amendments a
        JOIN contracts k ON k.contract_id = a.trigger_contract_id
        JOIN framework_agreements f ON f.framework_agreement_id = a.framework_agreement_id
        WHERE a.rule = 'cumulative_over_90pct' AND f.company_id <= ? AND f.partner_company_id <= ?""",
        (len(LEGACY_COMPANY_KEYS), len(LEGACY_COMPANY_KEYS)))}
    checks.append(CheckResult(
        f"Bestandsverträge unter Rahmen: {BASELINE_EXPECTED_ASSIGNED_CONTRACTS} Zuordnungen, "
        f"{len(BASELINE_EXPECTED_VOLUME_TRIGGERS)} Volumen-Auslöser",
        assigned == BASELINE_EXPECTED_ASSIGNED_CONTRACTS and triggers == BASELINE_EXPECTED_VOLUME_TRIGGERS,
        f"{assigned} Zuordnungen, {len(triggers & BASELINE_EXPECTED_VOLUME_TRIGGERS)}/"
        f"{len(BASELINE_EXPECTED_VOLUME_TRIGGERS)} Auslöser getroffen, "
        f"{len(triggers - BASELINE_EXPECTED_VOLUME_TRIGGERS)} zusätzlich"))
    return checks, frame


def run_quality_checks(path: Path, seed: int = DEFAULT_SEED,
                       baseline: Path | None = None) -> tuple[list[CheckResult], dict[str, pd.DataFrame]]:
    """Prüft die erzeugte Datenbank auf Konsistenz und liefert Ergebnisse plus Übersichtstabellen.

    Mit baseline (nur bei Seed 42) wird zusätzlich der Bestandsvergleich mit dem alten Datenstand geprüft.
    """
    connection = open_connection(path)
    checks: list[CheckResult] = []
    tables: dict[str, pd.DataFrame] = {}
    try:
        counts = {table: scalar(connection, f"SELECT COUNT(*) FROM {table}") for table in INSERT_ORDER}
        tables["counts"] = pd.DataFrame({"table": list(counts), "rows": list(counts.values())})

        fk_violations = connection.execute("PRAGMA foreign_key_check;").fetchall()
        checks.append(CheckResult("Fremdschlüssel gültig (PRAGMA foreign_key_check)", not fk_violations,
                                  "keine Verletzungen" if not fk_violations else f"{len(fk_violations)} Verletzungen"))
        integrity = scalar(connection, "PRAGMA integrity_check;")
        checks.append(CheckResult("Datenbankintegrität (PRAGMA integrity_check)", integrity == "ok", integrity))

        companies = query(connection, "SELECT company_id, name, language, size_class FROM companies")
        languages = companies["language"].value_counts()
        per_size = companies.groupby("size_class")["language"].value_counts().unstack(fill_value=0)
        checks.append(CheckResult(
            "18 Firmen: je 6 small, medium, large; je Größenklasse ≥2 de_DE und ≥2 en_US",
            len(companies) == len(COMPANY_PROFILES) == 18
            and all(companies["size_class"].value_counts().get(s, 0) == 6 for s in SIZE_CLASSES)
            and all(per_size.get(language, pd.Series(dtype=int)).get(s, 0) >= 2
                    for s in SIZE_CLASSES for language in LANGUAGES),
            f"de_DE={languages.get('de_DE', 0)}, en_US={languages.get('en_US', 0)}; "
            + ", ".join(f"{s} {per_size.loc[s].get('de_DE', 0)}/{per_size.loc[s].get('en_US', 0)}"
                        for s in SIZE_CLASSES if s in per_size.index)))
        systems = scalar(connection, "SELECT COUNT(*) FROM star_systems")
        checks.append(CheckResult("Mindestens 8 Sternensysteme und 30 Stationen",
                                  systems >= 8 and counts["stations"] >= 30,
                                  f"{systems} Systeme, {counts['stations']} Stationen"))

        # Mengengerüst je Firma
        volume = query(connection, """
            SELECT c.company_id, c.name, c.size_class,
                (SELECT COUNT(*) FROM stations s WHERE s.company_id = c.company_id) AS stations,
                (SELECT COUNT(*) FROM products p WHERE p.company_id = c.company_id) AS products,
                (SELECT COUNT(*) FROM customers k WHERE k.company_id = c.company_id) AS customers,
                (SELECT COUNT(*) FROM contracts k WHERE k.company_id = c.company_id) AS contracts,
                (SELECT COUNT(*) FROM orders o WHERE o.company_id = c.company_id) AS orders,
                (SELECT COUNT(*) FROM employees e WHERE e.company_id = c.company_id) AS employees,
                (SELECT COUNT(*) FROM trade_routes r WHERE r.company_id = c.company_id) AS routes
            FROM companies c ORDER BY c.company_id""")
        out_of_range = []
        for row in volume.itertuples():
            size = SIZE_PROFILES[row.size_class]
            for column, bounds in (("stations", size.stations), ("products", size.products),
                                   ("customers", size.customers), ("contracts", size.contracts),
                                   ("orders", size.orders)):
                value = getattr(row, column)
                if not bounds[0] <= value <= bounds[1]:
                    out_of_range.append(f"{row.name}: {column}={value}")
        tables["volume"] = volume
        checks.append(CheckResult("Mengen je Firma innerhalb der Größenklasse", not out_of_range,
                                  "alle Bereiche eingehalten" if not out_of_range else "; ".join(out_of_range)))

        # Partner je Firma
        partners = query(connection, """
            SELECT c.company_id, c.name, c.size_class,
                (SELECT COUNT(*) FROM trade_partnerships p WHERE p.is_active = 1
                    AND c.company_id IN (p.company_id, p.partner_company_id)) AS active_agreements,
                (SELECT COUNT(DISTINCT CASE WHEN p.company_id = c.company_id THEN p.partner_company_id
                                            ELSE p.company_id END)
                   FROM trade_partnerships p WHERE p.is_active = 1
                    AND c.company_id IN (p.company_id, p.partner_company_id)) AS distinct_partners,
                (SELECT COUNT(*) FROM customers k WHERE k.company_id = c.company_id) AS customer_accounts
            FROM companies c ORDER BY c.company_id""")
        tables["partners"] = partners
        partner_violations = [f"{r.name}: {r.active_agreements}" for r in partners.itertuples()
                              if not SIZE_PROFILES[r.size_class].agreements[0] <= r.active_agreements
                              <= SIZE_PROFILES[r.size_class].agreements[1]]
        checks.append(CheckResult("Partnerzahl (aktive Vereinbarungen) passt zur Größe: small 1–3, medium 3–6, large 6–10",
                                  not partner_violations,
                                  "alle Bereiche eingehalten" if not partner_violations else "; ".join(partner_violations)))
        hub = partners.sort_values(["distinct_partners", "active_agreements", "company_id"],
                                   ascending=[False, False, True], kind="stable").iloc[0]
        checks.append(CheckResult("Zentraler Hub ist eine große Firma", hub["size_class"] == "large",
                                  f"{hub['name']} mit {hub['distinct_partners']} direkten Partnern und "
                                  f"{hub['active_agreements']} Vereinbarungen"))
        checks.append(zero_check(connection, "Jede Firma hat mindestens eine ausgehende Vereinbarung (Verkäufer)", """
            SELECT COUNT(*) FROM companies c WHERE NOT EXISTS (
                SELECT 1 FROM trade_partnerships p WHERE p.is_active = 1 AND p.company_id = c.company_id)""",
            "alle Firmen verkaufen an mindestens einen Partner"))

        graph = partner_graph(connection)
        reachable = reachable_from(graph, next(iter(graph)))
        isolated = [cid for cid, neighbours in graph.items() if not neighbours]
        checks.append(CheckResult("Keine isolierte Firma, Netz zusammenhängend",
                                  not isolated and len(reachable) == len(graph),
                                  f"{len(reachable)}/{len(graph)} Firmen erreichbar"))
        all_pairs = len(graph) * (len(graph) - 1) // 2
        direct_pairs = sum(len(n) for n in graph.values()) // 2
        indirect_only = [(a, b) for a in graph for b in graph if a < b and b not in graph[a]
                         and graph[a] & graph[b]]
        names = dict(zip(companies["company_id"], companies["name"]))
        checks.append(CheckResult(
            "Unvollständiges Netz; ≥2 Firmenpaare nur über Zwischenhändler verbunden",
            direct_pairs < all_pairs and len(indirect_only) >= 2,
            f"{direct_pairs}/{all_pairs} Paare direkt, {len(indirect_only)} nur über einen Zwischenhändler; "
            f"z. B. {names[indirect_only[0][0]]} ↔ {names[indirect_only[0][1]]}" if indirect_only
            else "keine indirekten Paare"))

        # Handelsrouten
        checks.append(zero_check(connection, "Handelsrouten verweisen auf gültige Stationen/Produkte der Firma", """
            SELECT COUNT(*) FROM trade_routes r
            LEFT JOIN stations o ON o.station_id = r.origin_station_id
            LEFT JOIN stations d ON d.station_id = r.destination_station_id
            LEFT JOIN products p ON p.product_id = r.product_id
            WHERE o.station_id IS NULL OR d.station_id IS NULL OR p.product_id IS NULL
               OR o.company_id <> r.company_id OR p.company_id <> r.company_id
               OR NOT EXISTS (SELECT 1 FROM inventory i WHERE i.station_id = r.origin_station_id
                              AND i.product_id = r.product_id AND i.market_role = 'supply'
                              AND i.local_base_price = r.base_price_origin)
               OR NOT EXISTS (SELECT 1 FROM inventory i WHERE i.station_id = r.destination_station_id
                              AND i.product_id = r.product_id AND i.market_role = 'demand'
                              AND i.local_base_price = r.base_price_destination)""",
            "alle Routen konsistent mit Stationen, Produkten und Lagerpreisen"))
        checks.append(zero_check(connection, "estimated_profit_per_unit = Zielpreis − Herkunftspreis", """
            SELECT COUNT(*) FROM trade_routes
            WHERE ABS(estimated_profit_per_unit - ROUND(base_price_destination - base_price_origin, 2)) > 0.011
               OR ABS(net_profit_per_unit - ROUND(estimated_profit_per_unit - transport_cost_per_unit, 2)) > 0.011""",
            "konsistent berechnet"))
        cross = scalar(connection, """
            SELECT COUNT(*) FROM trade_routes r JOIN stations o ON o.station_id = r.origin_station_id
            JOIN stations d ON d.station_id = r.destination_station_id WHERE o.company_id <> d.company_id""")
        checks.append(CheckResult("Mindestens eine Route zwischen zwei verschiedenen Firmen", cross > 0,
                                  f"{cross} firmenübergreifende Routen"))
        checks.append(zero_check(connection, "Firmenübergreifende Routen nur zwischen aktiven Partnern", """
            SELECT COUNT(*) FROM trade_routes r JOIN stations d ON d.station_id = r.destination_station_id
            WHERE d.company_id <> r.company_id AND NOT EXISTS (
                SELECT 1 FROM trade_partnerships p WHERE p.is_active = 1
                AND p.company_id = r.company_id AND p.partner_company_id = d.company_id)""",
            "alle Partnerrouten durch Vereinbarungen gedeckt"))
        travel = query(connection, """
            SELECT r.travel_time_hours, r.distance_units, o.x ox, o.y oy, o.z oz, d.x dx, d.y dy, d.z dz
            FROM trade_routes r JOIN stations o ON o.station_id = r.origin_station_id
            JOIN stations d ON d.station_id = r.destination_station_id""")
        distance = ((travel["ox"] - travel["dx"]) ** 2 + (travel["oy"] - travel["dy"]) ** 2
                    + (travel["oz"] - travel["dz"]) ** 2) ** 0.5
        expected = DOCKING_OVERHEAD_HOURS + distance / CRUISE_SPEED_UNITS_PER_HOUR
        bad_travel = int(((travel["travel_time_hours"] - expected).abs() > 0.02).sum())
        checks.append(CheckResult("Reisezeiten passen zur Koordinatendistanz", bad_travel == 0,
                                  f"Reisezeit = {DOCKING_OVERHEAD_HOURS:g} h + Distanz / "
                                  f"{CRUISE_SPEED_UNITS_PER_HOUR:g}" if bad_travel == 0 else f"{bad_travel} Abweichungen"))

        margins = query(connection, """
            SELECT r.risk_level, p.legal_status,
                   (r.base_price_destination - r.base_price_origin) / r.base_price_origin AS margin
            FROM trade_routes r JOIN products p ON p.product_id = r.product_id""")
        risk_margin = margins.groupby("risk_level")["margin"].agg(["count", "mean"]).reindex(RISK_LEVELS).dropna()
        tables["risk_margin"] = risk_margin.reset_index()
        legal_margin = margins.groupby("legal_status")["margin"].mean()
        risky = margins[margins["risk_level"].isin(["high", "extreme"])]["margin"].mean()
        safe = margins[margins["risk_level"] == "low"]["margin"].mean()
        checks.append(CheckResult(
            "Riskante Routen und illegale Waren haben höhere Margen",
            risky > safe and legal_margin.get("illegal", math.inf) > legal_margin.get("legal", 0),
            f"Marge low {safe:.1%} vs. high/extreme {risky:.1%}; legal {legal_margin.get('legal', 0):.1%} vs. "
            f"illegal {legal_margin.get('illegal', float('nan')):.1%}"))

        # Produkte, Lager, illegale Ware
        checks.append(zero_check(connection, "Verkaufspreis über Einkaufspreis bei allen Produkten",
                                 "SELECT COUNT(*) FROM products WHERE base_price <= base_cost", "alle Produkte"))
        illegal_stations = scalar(connection, """
            SELECT COUNT(DISTINCT i.station_id) FROM inventory i JOIN products p ON p.product_id = i.product_id
            WHERE p.legal_status = 'illegal'""")
        checks.append(zero_check(connection, "Schwarzmarktware nur bei Firmen mit Schwarzmarkt-Station", """
            SELECT COUNT(*) FROM products p WHERE p.legal_status = 'illegal' AND NOT EXISTS (
                SELECT 1 FROM stations s WHERE s.company_id = p.company_id
                AND s.station_type IN ('free_port','smuggler_haven') AND s.security_level IN ('low','lawless'))""",
            "jede Firma mit Schwarzmarktware hat einen Frei- oder Schmugglerhafen mit niedriger Sicherheit"))
        checks.append(zero_check(connection, "Illegale Produkte nur an Stationen mit niedriger Sicherheit", """
            SELECT COUNT(*) FROM inventory i JOIN products p ON p.product_id = i.product_id
            JOIN stations s ON s.station_id = i.station_id
            WHERE p.legal_status = 'illegal' AND (s.security_level NOT IN ('low','lawless')
                  OR s.station_type NOT IN ('free_port','smuggler_haven'))""",
            f"nur {illegal_stations} von {counts['stations']} Stationen führen Schwarzmarktware"))
        checks.append(zero_check(connection, "Reservierungen = offene Bestellungen, nie über Bestand", """
            SELECT COUNT(*) FROM inventory i LEFT JOIN (
                SELECT o.origin_station_id AS station_id, oi.product_id, SUM(oi.quantity) AS reserved
                FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
                WHERE o.status IN ('pending','confirmed') GROUP BY 1, 2) r
              ON r.station_id = i.station_id AND r.product_id = i.product_id
            WHERE i.reserved_quantity <> COALESCE(r.reserved, 0) OR i.reserved_quantity > i.quantity""",
            "Lager und offene Bestellungen stimmen überein"))
        checks.append(zero_check(connection, "Lagerkapazität jeder Station reicht für ihren Bestand", """
            SELECT COUNT(*) FROM stations s JOIN (
                SELECT i.station_id, SUM(i.quantity * p.volume_m3) AS used
                FROM inventory i JOIN products p ON p.product_id = i.product_id GROUP BY i.station_id) u
              ON u.station_id = s.station_id WHERE u.used > s.storage_capacity_m3""", "keine Überbelegung"))

        # Bestellungen
        checks.append(zero_check(connection, "line_total = quantity × unit_price",
                                 "SELECT COUNT(*) FROM order_items WHERE ABS(line_total - ROUND(quantity * unit_price, 2)) > 0.005",
                                 f"{counts['order_items']} Positionen korrekt"))
        checks.append(zero_check(connection, "total_amount = SUM(line_total) + Fracht + Versicherung + Gebühr", """
            SELECT COUNT(*) FROM orders o LEFT JOIN (
                SELECT order_id, ROUND(SUM(line_total), 2) AS items_total, COUNT(*) AS lines
                FROM order_items GROUP BY order_id) i ON i.order_id = o.order_id
            WHERE i.lines IS NULL OR ABS(o.subtotal - i.items_total) > 0.011
               OR ABS(o.total_amount - (o.subtotal + o.freight_cost + o.insurance_cost + o.handling_fee)) > 0.011""",
            f"{counts['orders']} Bestellsummen korrekt"))
        checks.append(zero_check(connection, "Bestellungen nur über aktive Routen bzw. aktive Partnerschaften", """
            SELECT COUNT(*) FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
            WHERE NOT EXISTS (SELECT 1 FROM trade_routes r WHERE r.is_active = 1 AND r.company_id = o.company_id
                    AND r.origin_station_id = o.origin_station_id AND r.destination_station_id = o.destination_station_id
                    AND r.product_id = oi.product_id)
               OR (o.customer_company_id IS NOT NULL AND NOT EXISTS (
                    SELECT 1 FROM trade_partnerships p WHERE p.is_active = 1 AND p.start_date <= o.order_date
                    AND ((p.company_id = o.company_id AND p.partner_company_id = o.customer_company_id)
                      OR (p.partner_company_id = o.company_id AND p.company_id = o.customer_company_id))))""",
            "alle Bestellpositionen auf aktiven Routen, Firmenkunden mit aktiver Partnerschaft"))
        status_pairs = query(connection, "SELECT status, payment_status, COUNT(*) AS n FROM orders GROUP BY 1, 2")
        bad_status = [f"{r.status}/{r.payment_status}" for r in status_pairs.itertuples()
                      if r.payment_status not in ALLOWED_PAYMENT_BY_ORDER_STATUS[r.status]]
        checks.append(CheckResult("Zahlungsstatus passt zum Bestellstatus", not bad_status,
                                  "alle Kombinationen logisch" if not bad_status else ", ".join(bad_status)))
        tables["order_status"] = query(connection, """
            SELECT status, COUNT(*) AS orders, ROUND(SUM(total_amount), 2) AS total_amount
            FROM orders GROUP BY status ORDER BY orders DESC""")

        # Lieferungen
        checks.append(zero_check(connection, "Alle Lieferungen gehören zu gültigen Bestellungen", """
            SELECT COUNT(*) FROM shipments s LEFT JOIN orders o ON o.order_id = s.order_id
            WHERE o.order_id IS NULL OR o.status IN ('pending','cancelled')
               OR s.origin_station_id <> o.origin_station_id OR s.destination_station_id <> o.destination_station_id
               OR (o.status = 'confirmed' AND s.status <> 'pending')
               OR (o.status IN ('in_transit','delayed','delivered') AND s.status <> o.status)
               OR (s.status = 'delivered') <> (s.actual_arrival_date IS NOT NULL)""",
            f"{counts['shipments']} Lieferungen passen zu ihren Bestellungen"))
        checks.append(zero_check(connection, "Jede bestätigte/laufende/gelieferte Bestellung hat genau eine Lieferung", """
            SELECT COUNT(*) FROM orders o WHERE o.status IN ('confirmed','in_transit','delayed','delivered')
              AND (SELECT COUNT(*) FROM shipments s WHERE s.order_id = o.order_id) <> 1""", "vollständig"))
        checks.append(zero_check(connection, "Lieferzeit (Abflug → geplante Ankunft) = Routenreisezeit", """
            SELECT COUNT(*) FROM shipments s JOIN orders o ON o.order_id = s.order_id
            JOIN order_items oi ON oi.order_id = o.order_id
            JOIN trade_routes r ON r.origin_station_id = s.origin_station_id
                 AND r.destination_station_id = s.destination_station_id AND r.product_id = oi.product_id
            WHERE ABS((julianday(s.arrival_date) - julianday(s.departure_date)) * 24 - r.travel_time_hours) > 0.02""",
            "Lieferzeiten entsprechen der Distanz"))
        checks.append(zero_check(connection, "Ladungsmasse/-volumen = Summe der Bestellpositionen", """
            SELECT COUNT(*) FROM shipments s JOIN (
                SELECT oi.order_id, SUM(oi.quantity * p.mass_kg) AS mass, SUM(oi.quantity * p.volume_m3) AS volume
                FROM order_items oi JOIN products p ON p.product_id = oi.product_id GROUP BY oi.order_id) c
              ON c.order_id = s.order_id
            WHERE ABS(s.cargo_mass_kg - c.mass) > 0.01 OR ABS(s.cargo_volume_m3 - c.volume) > 0.01""",
            "Frachtdaten konsistent"))
        delayed_share = scalar(connection, """
            SELECT AVG(CASE WHEN risk_incident IS NOT NULL THEN 1.0 ELSE 0 END) FROM shipments""") or 0.0
        checks.append(CheckResult("Nur kleiner Anteil verzögerter Lieferungen / Zwischenfälle",
                                  0 < delayed_share < 0.15, f"{delayed_share:.1%} mit Zwischenfall"))

        # Verträge
        checks.append(zero_check(connection, "Verträge passen zu Route, Partnerschaft und Abrufen", """
            SELECT COUNT(*) FROM contracts c JOIN trade_routes r ON r.route_id = c.route_id
            LEFT JOIN (SELECT o.contract_id, SUM(oi.quantity) AS ordered,
                              SUM(CASE WHEN o.status = 'delivered' THEN oi.quantity ELSE 0 END) AS delivered,
                              SUM(CASE WHEN o.status NOT IN ('delivered','delayed') THEN 1 ELSE 0 END) AS open_orders
                       FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
                       WHERE o.contract_id IS NOT NULL GROUP BY o.contract_id) x ON x.contract_id = c.contract_id
            WHERE r.origin_station_id <> c.origin_station_id OR r.destination_station_id <> c.destination_station_id
               OR r.product_id <> c.product_id OR r.company_id <> c.company_id
               OR ABS(c.total_value - ROUND(c.quantity * c.agreed_price_per_unit, 2)) > 0.011
               OR COALESCE(x.ordered, 0) > c.quantity
               OR (c.status = 'completed' AND COALESCE(x.delivered, 0) <> c.quantity)
               OR (c.status = 'breached' AND (COALESCE(x.ordered, 0) <> c.quantity OR x.open_orders > 0))
               OR (c.status = 'draft' AND x.contract_id IS NOT NULL)
               OR NOT EXISTS (SELECT 1 FROM trade_partnerships p WHERE p.is_active = 1
                              AND p.company_id = c.company_id AND p.partner_company_id = c.partner_company_id)""",
            f"{counts['contracts']} Verträge konsistent"))
        checks.append(zero_check(connection, "Vertragsvolumen der Partnerschaften = Summe der Verträge", """
            SELECT COUNT(*) FROM trade_partnerships p WHERE p.is_active = 1 AND ABS(p.contract_volume - COALESCE((
                SELECT ROUND(SUM(c.total_value), 2) FROM contracts c WHERE c.company_id = p.company_id
                AND c.partner_company_id = p.partner_company_id AND c.status <> 'cancelled'), 0)) > 0.05""",
            "konsistent"))

        # Preisverläufe
        checks.append(zero_check(connection, "Preisverläufe ohne negative oder Null-Preise",
                                 "SELECT COUNT(*) FROM price_history WHERE market_price <= 0 OR stock_quantity < 0",
                                 f"{counts['price_history']} Preispunkte > 0"))
        checks.append(zero_check(connection, "Jede handelbare Station-Ware-Kombination hat eine Preishistorie", """
            SELECT COUNT(*) FROM inventory i JOIN products p ON p.product_id = i.product_id
            WHERE p.is_tradeable = 1 AND (SELECT COUNT(*) FROM price_history h
                WHERE h.station_id = i.station_id AND h.product_id = i.product_id) < 20""", "vollständig"))
        checks.append(zero_check(connection, "Letzter Preispunkt = aktueller Lagerbestand", """
            SELECT COUNT(*) FROM inventory i JOIN price_history h ON h.station_id = i.station_id
                AND h.product_id = i.product_id AND h.date = substr(i.last_updated, 1, 10)
            WHERE h.stock_quantity <> i.quantity""", "Lager und Historie stimmen überein"))
        history_months = query(connection, """
            SELECT c.size_class, ROUND(AVG(span), 1) AS avg_months FROM (
                SELECT h.station_id, h.product_id,
                       (julianday(MAX(h.date)) - julianday(MIN(h.date))) / 30.44 AS span
                FROM price_history h GROUP BY 1, 2) x
            JOIN products p ON p.product_id = x.product_id JOIN companies c ON c.company_id = p.company_id
            GROUP BY c.size_class""")
        tables["history_months"] = history_months

        # Ereignisse
        checks.append(zero_check(connection, "Ereignisse lokal begrenzt (ein System, ≤3 Stationen)", """
            SELECT COUNT(*) FROM events e WHERE
                (SELECT COUNT(DISTINCT s.system_id) FROM event_effects f JOIN stations s ON s.station_id = f.station_id
                 WHERE f.event_id = e.event_id) <> 1
             OR (SELECT COUNT(DISTINCT f.station_id) FROM event_effects f WHERE f.event_id = e.event_id) > 3""",
            f"{counts['events']} Ereignisse"))
        tables["events"] = query(connection, """
            SELECT event_type, COUNT(*) AS events, ROUND(AVG(price_impact) * 100, 1) AS avg_price_impact_pct
            FROM events GROUP BY event_type ORDER BY events DESC""")
        # Rahmenverträge
        checks.extend(framework_quality_checks(connection))
        tables["frameworks"] = query(connection, """
            SELECT f.agreement_number, f.status, ROUND(f.base_volume / 1e6, 1) AS base_mcr,
                   ROUND(f.current_volume_cap / 1e6, 1) AS cap_mcr,
                   (SELECT COUNT(*) FROM contracts k WHERE k.framework_agreement_id = f.framework_agreement_id)
                       AS contracts,
                   (SELECT ROUND(SUM(k.total_value) / 1e6, 1) FROM contracts k
                     WHERE k.framework_agreement_id = f.framework_agreement_id AND k.status <> 'cancelled') AS used_mcr,
                   (SELECT COUNT(*) FROM framework_agreement_amendments a
                     WHERE a.framework_agreement_id = f.framework_agreement_id) AS amendments,
                   f.current_end_date
            FROM framework_agreements f ORDER BY f.framework_agreement_id""")
        # Schriftverkehr
        checks.extend(correspondence_quality_checks(connection, seed))
        tables["correspondence"] = query(connection, """
            SELECT correspondence_type, COUNT(*) AS letters,
                   SUM(sender_company_id <= 6 AND recipient_company_id <= 6) AS between_legacy,
                   SUM(confidentiality = 'confidential') AS confidential, SUM(leak_status <> 'none') AS leaked,
                   SUM(in_reply_to_id IS NOT NULL) AS replies
            FROM correspondence GROUP BY correspondence_type ORDER BY letters DESC""")
        if baseline is not None and seed == BASELINE_SEED and baseline.exists():
            baseline_checks, tables["baseline"] = baseline_quality_checks(connection, baseline)
            checks.extend(baseline_checks)
        tables["financials"] = query(connection, """
            SELECT c.name, COUNT(*) AS months, ROUND(SUM(f.goods_revenue + f.service_revenue) / 1e6, 2) AS revenue_mcr,
                   ROUND(SUM(f.net_income) / 1e6, 2) AS net_income_mcr,
                   ROUND(SUM(f.net_income) * 100.0 / NULLIF(SUM(f.goods_revenue + f.service_revenue), 0), 1) AS margin_pct
            FROM company_financials f JOIN companies c ON c.company_id = f.company_id
            GROUP BY c.company_id ORDER BY c.company_id""")
    finally:
        connection.close()
    return checks, tables


# ---------------------------------------------------------------------------
# Ablauf und Ausgabe
# ---------------------------------------------------------------------------

PIPELINE: tuple[tuple[str, Callable[[World], None]], ...] = (
    ("1. Firmen", generate_companies),
    ("2. Sternensysteme und Stationen", lambda w: (generate_star_systems(w), generate_stations(w))),
    ("3. Produkte", generate_products),
    ("4. Partnerschaften und Rivalitäten", lambda w: (generate_partnerships(w), generate_rivalries(w))),
    ("5. Rahmenverträge (Grundlage)", generate_framework_agreements),
    ("6. Handelsrouten", generate_trade_routes),
    ("7. Lager", generate_inventory),
    ("8. Verträge", generate_contracts),
    ("9. Kunden, Bestellungen und Bestellpositionen", generate_orders),
    ("10. Lieferungen", generate_shipments),
    ("11. Preisverläufe", generate_price_history),
    ("12. Mitarbeiter", generate_employees),
    ("13. Ereignisse", generate_events),
    ("14. Finanzdaten", generate_financials),
    ("15. Rahmenverträge: Zuordnung, Nachträge, Unterzeichner", finalize_framework_agreements),
    ("16. Schriftverkehr", generate_correspondence),
)


def run_pipeline(world: World) -> None:
    """Führt alle Generierungsschritte in fester Reihenfolge aus."""
    for label, step in PIPELINE:
        started = time.perf_counter()
        step(world)
        print(f"  {label:<56} {time.perf_counter() - started:6.2f} s")


def print_table(title: str, frame: pd.DataFrame) -> None:
    """Gibt ein DataFrame mit Überschrift aus."""
    print(f"\n{title}")
    print("-" * len(title))
    with pd.option_context("display.width", 160, "display.max_columns", 20, "display.max_colwidth", 40):
        print(frame.to_string(index=False))


def print_summary(path: Path, checks: list[CheckResult], tables: dict[str, pd.DataFrame], seed: int,
                  elapsed: float) -> None:
    """Übersichtliche Konsolenzusammenfassung."""
    counts = dict(zip(tables["counts"]["table"], tables["counts"]["rows"]))
    print("\n" + "=" * 78)
    print(" SPACE TRADING GAME – DATENBASIS")
    print("=" * 78)
    print(f" Datei: {path.resolve()}  ({path.stat().st_size / 1_048_576:.1f} MB)")
    print(f" Seed: {seed}   Stichtag: {GAME_REFERENCE_DATE.isoformat()}   Laufzeit: {elapsed:.1f} s")
    print(f" Firmen {counts['companies']} | Systeme {counts['star_systems']} | Stationen {counts['stations']} | "
          f"Produkte {counts['products']} | Routen {counts['trade_routes']}")
    print(f" Verträge {counts['contracts']} | Bestellungen {counts['orders']} | Positionen {counts['order_items']} | "
          f"Lieferungen {counts['shipments']} | Preispunkte {counts['price_history']}")
    print(f" Kunden {counts['customers']} | Mitarbeiter {counts['employees']} | Ereignisse {counts['events']} "
          f"({counts['event_effects']} Wirkungen) | Finanzmonate {counts['company_financials']}")
    print(f" Rahmenverträge {counts['framework_agreements']} | Nachträge {counts['framework_agreement_amendments']} | "
          f"Sortimentseinträge {counts['framework_agreement_scope']}")
    print(f" Schreiben {counts['correspondence']} | Kopien {counts['correspondence_copies']}")

    print_table("Mengengerüst je Firma", tables["volume"].drop(columns=["company_id"]))
    print_table("Handelspartner je Firma", tables["partners"].drop(columns=["company_id"]))
    print_table("Bestellstatus", tables["order_status"])
    risk = tables["risk_margin"].rename(columns={"index": "risk_level", "count": "routes", "mean": "avg_margin"})
    risk["avg_margin"] = (risk["avg_margin"] * 100).round(1).astype(str) + " %"
    print_table("Routenmarge nach Risiko", risk)
    print_table("Preishistorie: mittlere Länge (Monate) nach Größe des Anbieters", tables["history_months"])
    print_table("Ereignisse", tables["events"])
    print_table("Finanzen über den Datenzeitraum (Mio. CR)", tables["financials"])
    print_table("Rahmenverträge (Mio. CR)", tables["frameworks"])
    print_table("Schriftverkehr nach Briefart", tables["correspondence"])
    if "baseline" in tables:
        print_table("Bestandsvergleich mit dem Datenstand vor der Erweiterung", tables["baseline"])

    print("\nQualitätsprüfungen")
    print("------------------")
    for check in checks:
        print(f" [{'OK ' if check.passed else 'FEHLER'}] {check.name}: {check.detail}")
    passed = sum(check.passed for check in checks)
    print(f"\n {passed}/{len(checks)} Prüfungen bestanden.")
    print("=" * 78)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Kommandozeilenargumente."""
    parser = argparse.ArgumentParser(description="Erzeugt die SQLite-Datenbasis für ein Space-Trading-Spiel.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help=f"Zufalls-Seed (Standard: {DEFAULT_SEED})")
    parser.add_argument("--output", type=Path, default=Path(DEFAULT_OUTPUT),
                        help=f"Pfad der SQLite-Datei (Standard: {DEFAULT_OUTPUT})")
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE,
                        help="Bestands-DB für den Bestandsvergleich bei Seed 42 (wird übersprungen, wenn nicht "
                             "vorhanden)")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Einstiegspunkt: generieren, schreiben, prüfen, zusammenfassen."""
    args = parse_args(argv)
    started = time.perf_counter()
    print(f"Erzeuge Space-Trading-Daten (Seed {args.seed}) ...")
    world = build_world(args.seed)
    run_pipeline(world)
    print("  Schreibe SQLite-Datenbank (eine Transaktion) ...")
    write_database(world, args.output)
    checks, tables = run_quality_checks(args.output, args.seed, args.baseline)
    print_summary(args.output, checks, tables, args.seed, time.perf_counter() - started)
    return 0 if all(check.passed for check in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
