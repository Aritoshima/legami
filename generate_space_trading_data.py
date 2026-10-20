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

Aufruf
------
    pip install faker pandas
    python generate_space_trading_data.py
    python generate_space_trading_data.py --seed 42 --output space_trading_game.db

Abhängigkeiten: Python 3.11+, faker, pandas, Standardbibliothek (sqlite3).
Alle Namen von Firmen, Personen und Orten sind fiktiv.
"""

from __future__ import annotations

import argparse
import calendar
import math
import random
import sqlite3
import sys
import time
from collections import defaultdict, deque
from collections.abc import Callable, Hashable, Iterable, Sequence
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
)

SECTOR_LABELS: dict[str, dict[str, str]] = {
    "core": {"de_DE": "Kernsektor", "en_US": "Core Sector"},
    "inner_ring": {"de_DE": "Innerer Ring", "en_US": "Inner Ring"},
    "middle_belt": {"de_DE": "Mittelgürtel", "en_US": "Middle Belt"},
    "outer_rim": {"de_DE": "Äußerer Rand", "en_US": "Outer Rim"},
    "frontier": {"de_DE": "Grenzland", "en_US": "Frontier"},
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
    """Steckbrief einer der sechs Raumhandelsgesellschaften."""

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
)

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
)
OPTIONAL_PARTNERSHIPS: tuple[tuple[str, str, str, float], ...] = (
    ("helix", "corvane", "logistics_partnership", 0.6),
)
# Beendete Beziehung (vor dem Datenzeitraum) – Grundlage für Rivalität und Spionage
HISTORIC_PARTNERSHIPS: tuple[tuple[str, str, str], ...] = (("corvane", "driftwood", "supply_agreement"),)

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
)
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


def _archetype(code: str, category: str, name_de: str, name_en: str, unit: str, base_price: float,
               volume_m3: float, mass_kg: float, legal_status: str = "legal",
               producers: Iterable[str] | None = None,
               extra_consumers: Iterable[str] = ()) -> ProductArchetype:
    """Erzeugt einen Waren-Archetyp mit kategorieabhängigen Erzeuger- und Verbraucherstationen."""
    return ProductArchetype(
        code=code, category=category, name_de=name_de, name_en=name_en, unit=unit, base_price=base_price,
        volume_m3=volume_m3, mass_kg=mass_kg, legal_status=legal_status,
        producers=frozenset(producers) if producers else CATEGORY_PRODUCERS[category],
        consumers=CATEGORY_CONSUMERS[category] | frozenset(extra_consumers),
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
    "company_financials": "financial_id",
}

INSERT_ORDER: tuple[str, ...] = (
    "companies", "star_systems", "stations", "products", "trade_partnerships", "company_rivalries",
    "trade_routes", "inventory", "contracts", "customers", "orders", "order_items", "shipments",
    "price_history", "employees", "events", "event_effects", "company_financials",
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
        """Faker-Instanz in der Sprache der Firma."""
        return self.fakers[self.language(company_id)]


def build_world(seed: int) -> World:
    """Initialisiert Zufallsgeneratoren und Faker-Instanzen reproduzierbar."""
    Faker.seed(seed)
    fakers = {language: Faker(language) for language in LANGUAGES}
    return World(seed=seed, rng=random.Random(seed), fakers=fakers)


# ---------------------------------------------------------------------------
# 1. Firmen
# ---------------------------------------------------------------------------


def generate_companies(world: World) -> None:
    """Legt die sechs Firmen samt Mengenzielen innerhalb der Größenklassen an."""
    rng = world.rng
    for profile in COMPANY_PROFILES:
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
    ensure_minimum_station_count(world)


def ensure_minimum_station_count(world: World) -> None:
    """Erhöht Stationszahlen großer/mittlerer Firmen, bis die Welt mindestens 30 Stationen hat."""
    while sum(target["stations"] for target in world.targets.values()) < MIN_TOTAL_STATIONS:
        expandable = [cid for cid, company in world.companies.items()
                      if company["size_class"] in ("large", "medium")
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
    rng = world.rng
    used_names: set[str] = set()
    for company_id, company in world.companies.items():
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
    """Leitet für jede Firma einen Warenkatalog aus Archetypen und Varianten ab."""
    rng = world.rng
    archetypes_by_category: dict[str, list[ProductArchetype]] = defaultdict(list)
    for archetype in PRODUCT_ARCHETYPES:
        archetypes_by_category[archetype.category].append(archetype)

    for company_id, company in world.companies.items():
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


def generate_partnerships(world: World) -> None:
    """Erzeugt das gerichtete, unvollständige Partnerschaftsnetz (Verkäufer -> Käufer)."""
    rng = world.rng
    blueprint = list(PARTNERSHIP_BLUEPRINT)
    for seller, buyer, relationship, probability in OPTIONAL_PARTNERSHIPS:
        if rng.random() < probability:
            blueprint.append((seller, buyer, relationship))

    for seller_key, buyer_key, relationship in blueprint:
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
            "contract_volume": 0.0,  # Summe der Verträge, wird nach Schritt 7 gesetzt
            "start_date": fmt_date(partnership_start_date(world, seller_id, buyer_id)),
            "end_date": None,
            "is_active": 1,
        })
        world.active_agreements[(seller_id, buyer_id)] = row

    for seller_key, buyer_key, relationship in HISTORIC_PARTNERSHIPS:
        seller_id = world.company_ids_by_key[seller_key]
        buyer_id = world.company_ids_by_key[buyer_key]
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


def generate_rivalries(world: World) -> None:
    """Legt Konkurrenz- und Spionagebeziehungen zwischen Firmen an."""
    rng = world.rng
    intensity_ranges = {"market_dominance": (55, 80), "industrial_espionage": (70, 95),
                        "territorial_claims": (40, 75), "resource_competition": (35, 65)}
    for company_key, rival_key, rivalry_type, system_code in RIVALRY_BLUEPRINT:
        company_id = world.company_ids_by_key[company_key]
        rival_id = world.company_ids_by_key[rival_key]
        language = world.language(company_id)
        system = world.systems[system_code]
        founded = max(world.companies[company_id]["founded_year"], world.companies[rival_id]["founded_year"])
        world.add("company_rivalries", {
            "company_id": company_id,
            "rival_company_id": rival_id,
            "rivalry_type": rivalry_type,
            "intensity": rng.randint(*intensity_ranges[rivalry_type]),
            "contested_system_id": system["system_id"],
            "espionage_risk": rng.randint(50, 95) if rivalry_type == "industrial_espionage" else rng.randint(10, 60),
            "since_date": fmt_date(random_date(rng, date(founded + 1, 1, 1), GAME_REFERENCE_DATE - timedelta(days=90))),
            "description": RIVALRY_TEXTS[rivalry_type][language].format(
                company=world.companies[company_id]["name"], rival=world.companies[rival_id]["name"],
                system=system["name"]),
        })


# ---------------------------------------------------------------------------
# 5. Handelsrouten (inkl. Marktplanung: wer bietet an, wer fragt nach)
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


def plan_markets(world: World) -> dict[int, list[int]]:
    """Legt fest, welche Stationen welche Ware anbieten (supply) bzw. nachfragen (demand)."""
    rng = world.rng
    demand_by_product: dict[int, list[int]] = defaultdict(list)
    for company_id, company in world.companies.items():
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

    # Jede gerichtete Vereinbarung braucht genug Routen für Verträge und Bestellungen.
    for seller_id, buyer_id in world.active_agreements:
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
    return demand_by_product


def generate_trade_routes(world: World) -> None:
    """Erzeugt Handelsrouten von Erzeuger- zu Verbraucherstationen inklusive Preisanker und Risiko."""
    rng = world.rng
    demand_by_product = plan_markets(world)
    for product_id, demand_ids in demand_by_product.items():
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
# 6. Lager
# ---------------------------------------------------------------------------


def generate_inventory(world: World) -> None:
    """Erzeugt Lagerbestände passend zu Marktrolle und typischen Routenmengen."""
    rng = world.rng
    outgoing: dict[tuple[int, int], int] = defaultdict(int)
    incoming: dict[tuple[int, int], int] = defaultdict(int)
    for route in world.rows["trade_routes"]:
        outgoing[(route["origin_station_id"], route["product_id"])] += route["typical_quantity"]
        incoming[(route["destination_station_id"], route["product_id"])] += route["typical_quantity"]

    for (station_id, product_id), market in sorted(world.market.items()):
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
# 7. Verträge
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


def generate_contracts(world: World) -> None:
    """Erzeugt Verträge entlang aktiver Vereinbarungen und plant deren Abrufbestellungen."""
    rng = world.rng
    for company_id, company in world.companies.items():
        language = company["language"]
        profile = world.profiles[company_id]
        buyers = [buyer for (seller, buyer) in world.active_agreements if seller == company_id]
        routes_by_buyer = {buyer: partner_routes_of(world, company_id, buyer) for buyer in buyers}
        buyers = [buyer for buyer in buyers if routes_by_buyer[buyer]]
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
            if start > GAME_REFERENCE_DATETIME:
                status = "draft"
            elif deadline < GAME_REFERENCE_DATETIME:
                status = weighted_choice(rng, {"completed": 0.80, "breached": 0.12, "cancelled": 0.08})
            else:
                status = "cancelled" if rng.random() < 0.07 else "active"
            plan = {
                "route": route, "buyer_id": buyer_id, "contract_type": contract_type, "start": start,
                "deadline": deadline, "status": status,
                "calloffs": plan_calloffs(world, start, duration, route["travel_time_hours"], count,
                                          route["typical_quantity"]),
            }
            if status == "cancelled":
                plan["cancelled_at"] = random_datetime(rng, start, min(deadline, GAME_REFERENCE_DATETIME))
            if status == "breached":
                schedule_breached_calloff(plan, route["travel_time_hours"], rng)
            plans.append(plan)

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
            })
            world.contract_plans[row["contract_id"]] = plan

    # Vertragsvolumen der Partnerschaften = Summe der (nicht stornierten) Verträge in dieser Richtung
    volumes: dict[tuple[int, int], float] = defaultdict(float)
    for contract in world.rows["contracts"]:
        if contract["status"] != "cancelled":
            volumes[(contract["company_id"], contract["partner_company_id"])] += contract["total_value"]
    for key, agreement in world.active_agreements.items():
        agreement["contract_volume"] = round(volumes[key], 2)


# ---------------------------------------------------------------------------
# 8. Kunden, Bestellungen und Bestellpositionen
# ---------------------------------------------------------------------------


def generate_customers(world: World) -> None:
    """Erzeugt Kundenkonten: Partnerfirmen und fiktive Kolonien, Händler und Stationsbetreiber."""
    rng = world.rng
    for company_id, company in world.companies.items():
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
    rng = world.rng
    generate_customers(world)
    contracts_by_company: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for contract in world.rows["contracts"]:
        contracts_by_company[contract["company_id"]].append(contract)

    for company_id in world.companies:
        pending_orders: list[dict[str, Any]] = []
        partner_customers = {c["linked_company_id"]: c for c in world.customers_by_company[company_id]
                             if c["linked_company_id"] is not None}
        routes_by_id = {r["route_id"]: r for r in world.rows["trade_routes"]}
        for contract in contracts_by_company[company_id]:
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

        spot_count = max(0, world.targets[company_id]["orders"] - len(pending_orders))
        for _ in range(spot_count):
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
            pending_orders.append({"order_dt": order_dt, "customer": customer, "lines": lines, "contract": None,
                                   "calloff_index": 0, "calloff_total": 0, "force_late_after": None,
                                   "allow_cancel": True, "allow_delay": True})

        for sequence, spec in enumerate(sorted(pending_orders, key=lambda o: o["order_dt"]), start=1):
            build_order(world, company_id, spec["customer"], spec["lines"], spec["order_dt"], sequence,
                        contract=spec["contract"], calloff_index=spec["calloff_index"],
                        calloff_total=spec["calloff_total"], force_late_after=spec["force_late_after"],
                        allow_cancel=spec["allow_cancel"], allow_delay=spec["allow_delay"])

    book_inventory_reservations(world)
    finalize_station_capacity(world)


def book_inventory_reservations(world: World) -> None:
    """Reserviert Lagerware für noch nicht abgeflogene Bestellungen (pending/confirmed)."""
    rng = world.rng
    reserved: dict[tuple[int, int], int] = defaultdict(int)
    orders = {o["order_id"]: o for o in world.rows["orders"]}
    for item in world.rows["order_items"]:
        order = orders[item["order_id"]]
        if order["status"] in ("pending", "confirmed"):
            reserved[(order["origin_station_id"], item["product_id"])] += item["quantity"]
    for key, quantity in reserved.items():
        inventory = world.inventory[key]
        inventory["reserved_quantity"] = quantity
        if inventory["quantity"] < quantity:
            inventory["quantity"] = quantity + int(inventory["restock_target"] * rng.uniform(0.05, 0.3))


def finalize_station_capacity(world: World) -> None:
    """Setzt die Lagerkapazität jeder Station über das tatsächlich belegte Volumen."""
    rng = world.rng
    used: dict[int, float] = defaultdict(float)
    for inventory in world.rows["inventory"]:
        used[inventory["station_id"]] += inventory["quantity"] * world.products[inventory["product_id"]]["volume_m3"]
    for station in world.rows["stations"]:
        size = SIZE_PROFILES[world.companies[station["company_id"]]["size_class"]]
        nominal = STATION_TYPES[station["station_type"]].base_storage_m3 * size.storage_factor
        station["storage_capacity_m3"] = float(round(max(nominal, used[station["station_id"]] * rng.uniform(1.3, 1.8)), -2))


# ---------------------------------------------------------------------------
# 9. Lieferungen
# ---------------------------------------------------------------------------


def generate_shipments(world: World) -> None:
    """Erzeugt je bestätigter Bestellung eine Lieferung mit Reisezeit passend zur Distanz."""
    rng = world.rng
    counters: dict[int, int] = defaultdict(int)
    shipment_status = {"confirmed": "pending", "in_transit": "in_transit", "delayed": "delayed",
                       "delivered": "delivered"}
    for order in world.rows["orders"]:
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
# 10. Preisverläufe (inkl. Planung der Marktereignisse, die die Kurven prägen)
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
    """Plant lokale Marktereignisse (ein System, max. drei Stationen) als Schocks für die Preiskurven."""
    rng = world.rng
    tradeable_by_station: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for inventory in world.rows["inventory"]:
        if inventory["market_role"] in ("supply", "demand"):
            tradeable_by_station[inventory["station_id"]].append(inventory)
    stations_by_system: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for station in world.rows["stations"]:
        stations_by_system[station["system_id"]].append(station)

    def eligible_inventory(event_type: EventType, station: dict[str, Any], event_date: date) -> list[dict[str, Any]]:
        return [inv for inv in tradeable_by_station[station["station_id"]]
                if event_type.product_filter(world.products[inv["product_id"]], inv)
                and series_start_date(world, inv["station_id"], inv["product_id"]) <= event_date - timedelta(days=14)]

    for station in world.rows["stations"]:
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
                     "supply": supply_base, "demand": demand_base, "effects": effects}
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
        if inventory["market_role"] in ("supply", "demand"):
            build_price_series(world, inventory)


# ---------------------------------------------------------------------------
# 11. Mitarbeiter
# ---------------------------------------------------------------------------


def generate_employees(world: World) -> None:
    """Erzeugt Mitarbeiter mit Rollen, Gehältern und Spielwerten für Beziehungspflege und Spionage."""
    rng = world.rng
    for company_id, company in world.companies.items():
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
# 12. Ereignisse
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
    """Schreibt die geplanten Marktereignisse samt aller betroffenen Stationen und Waren."""
    for planned in sorted(world.planned_events, key=lambda e: e["event_date"]):
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
# 13. Finanzdaten
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

    breached = contracts[contracts["status"] == "breached"]
    penalties: dict[tuple[int, str], float] = defaultdict(float)
    order_by_contract = orders.dropna(subset=["contract_id"]).merge(shipments[["order_id", "actual_arrival_date"]],
                                                                   on="order_id")
    for contract in breached.itertuples():
        arrivals = order_by_contract[order_by_contract["contract_id"] == contract.contract_id]["actual_arrival_date"]
        # Noch verspätet unterwegs: Strafe läuft bis zum Stichtag auf
        last_arrival = (GAME_REFERENCE_DATETIME - timedelta(days=1) if arrivals.isna().any()
                        else datetime.fromisoformat(arrivals.max()))
        late_days = max(0, (last_arrival.date() - date.fromisoformat(contract.deadline)).days)
        penalties[(contract.company_id, last_arrival.strftime("%Y-%m"))] += late_days * contract.penalty_per_day

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


def run_quality_checks(path: Path) -> tuple[list[CheckResult], dict[str, pd.DataFrame]]:
    """Prüft die erzeugte Datenbank auf Konsistenz und liefert Ergebnisse plus Übersichtstabellen."""
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
        checks.append(CheckResult(
            "Sechs Firmen: 2 small, 2 medium, 2 large; ≥2 de_DE und ≥2 en_US",
            len(companies) == 6 and all(companies["size_class"].value_counts().get(s, 0) == 2 for s in SIZE_CLASSES)
            and languages.get("de_DE", 0) >= 2 and languages.get("en_US", 0) >= 2,
            f"de_DE={languages.get('de_DE', 0)}, en_US={languages.get('en_US', 0)}"))
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
        hub = partners.sort_values(["distinct_partners", "active_agreements"], ascending=False).iloc[0]
        checks.append(CheckResult("Zentraler Hub ist eine große Firma", hub["size_class"] == "large",
                                  f"{hub['name']} mit {hub['distinct_partners']} direkten Partnern"))

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
            "Unvollständiges Netz; ≥2 Firmen nur über Zwischenhändler verbunden",
            direct_pairs < all_pairs and len(indirect_only) >= 1,
            f"{direct_pairs}/{all_pairs} Paare direkt; z. B. {names[indirect_only[0][0]]} ↔ "
            f"{names[indirect_only[0][1]]} nur indirekt" if indirect_only else "keine indirekten Paare"))

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
    ("5. Handelsrouten", generate_trade_routes),
    ("6. Lager", generate_inventory),
    ("7. Verträge", generate_contracts),
    ("8. Kunden, Bestellungen und Bestellpositionen", generate_orders),
    ("9. Lieferungen", generate_shipments),
    ("10. Preisverläufe", generate_price_history),
    ("11. Mitarbeiter", generate_employees),
    ("12. Ereignisse", generate_events),
    ("13. Finanzdaten", generate_financials),
)


def run_pipeline(world: World) -> None:
    """Führt alle Generierungsschritte in fester Reihenfolge aus."""
    for label, step in PIPELINE:
        started = time.perf_counter()
        step(world)
        print(f"  {label:<48} {time.perf_counter() - started:6.2f} s")


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

    print_table("Mengengerüst je Firma", tables["volume"].drop(columns=["company_id"]))
    print_table("Handelspartner je Firma", tables["partners"].drop(columns=["company_id"]))
    print_table("Bestellstatus", tables["order_status"])
    risk = tables["risk_margin"].rename(columns={"index": "risk_level", "count": "routes", "mean": "avg_margin"})
    risk["avg_margin"] = (risk["avg_margin"] * 100).round(1).astype(str) + " %"
    print_table("Routenmarge nach Risiko", risk)
    print_table("Preishistorie: mittlere Länge (Monate) nach Größe des Anbieters", tables["history_months"])
    print_table("Ereignisse", tables["events"])
    print_table("Finanzen über den Datenzeitraum (Mio. CR)", tables["financials"])

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
    checks, tables = run_quality_checks(args.output)
    print_summary(args.output, checks, tables, args.seed, time.perf_counter() - started)
    return 0 if all(check.passed for check in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
