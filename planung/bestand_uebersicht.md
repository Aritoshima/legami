# Bestandsübersicht (Seed 42, vor der Erweiterung)

Vollständige Datenbank: `/home/user/bestand/space_trading_game_bestand.db` (nicht im Repo). Aggregierte Dashboard-Datensätze als JSON im selben Ordner.

## Zeilen je Tabelle
| t             |     n |
|:--------------|------:|
| companies     |     6 |
| stations      |    33 |
| products      |   504 |
| trade_routes  |   936 |
| contracts     |   743 |
| orders        |  5518 |
| employees     |   491 |
| price_history | 93648 |
| events        |    74 |

## Stationen je System
| code    | name    |   unlock_tier | base_security   |   stations | types                                            | operators                                                 |
|:--------|:--------|--------------:|:----------------|-----------:|:-------------------------------------------------|:----------------------------------------------------------|
| sol     | Sol     |             0 | high            |          6 | research,industrial,trade_hub,free_port,military | corvane-biomedical,eisenkrone-montan,helix-meridian       |
| halcyon | Halcyon |             1 | high            |          5 | research,industrial,mining,military              | corvane-biomedical,eisenkrone-montan,helix-meridian       |
| tauvel  | Tauvel  |             1 | high            |          3 | agricultural,research                            | lichtacker-agrarsysteme                                   |
| aurelis | Aurelis |             2 | medium          |          5 | agricultural,research,free_port                  | lichtacker-agrarsysteme,corvane-biomedical,helix-meridian |
| myrrhen | Myrrhen |             2 | medium          |          3 | agricultural,mining                              | lichtacker-agrarsysteme,eisenkrone-montan                 |
| orrin   | Orrin   |             2 | medium          |          0 | nan                                              | nan                                                       |
| brennus | Brennus |             3 | low             |          5 | mining,trade_hub,industrial                      | feldspat-orbitalbergbau,eisenkrone-montan                 |
| isolde  | Isolde  |             3 | medium          |          0 | nan                                              | nan                                                       |
| kharon  | Kharon  |             4 | low             |          5 | free_port,smuggler_haven,trade_hub               | driftwood-salvage,helix-meridian                          |
| nyx     | Nyx     |             4 | lawless         |          1 | smuggler_haven                                   | driftwood-salvage                                         |

## Angebot (supply) und Nachfrage (demand) je Warenkategorie
| category_code    |   supply_listings |   demand_listings |   products |
|:-----------------|------------------:|------------------:|-----------:|
| contraband       |                18 |                27 |         16 |
| medical          |                57 |                90 |         52 |
| energy           |                61 |                94 |         50 |
| food             |                79 |               133 |         76 |
| luxury           |                80 |               125 |         70 |
| technology       |                89 |               125 |         71 |
| industrial_goods |               101 |               126 |         77 |
| raw_materials    |               109 |               164 |         92 |

## Aktive Vereinbarungen
| seller                  | buyer                   | relationship_type      |   trust_level |   volume_mcr |   is_active |
|:------------------------|:------------------------|:-----------------------|--------------:|-------------:|------------:|
| eisenkrone-montan       | helix-meridian          | supply_agreement       |            72 |        324.8 |           1 |
| helix-meridian          | eisenkrone-montan       | strategic_alliance     |            81 |        484   |           1 |
| helix-meridian          | lichtacker-agrarsysteme | distribution_agreement |            80 |        530   |           1 |
| lichtacker-agrarsysteme | helix-meridian          | supply_agreement       |            50 |         82.8 |           1 |
| corvane-biomedical      | helix-meridian          | licensing              |            73 |         74.7 |           1 |
| feldspat-orbitalbergbau | helix-meridian          | consignment            |            49 |          3   |           1 |
| driftwood-salvage       | helix-meridian          | consignment            |            27 |         12.1 |           1 |
| feldspat-orbitalbergbau | eisenkrone-montan       | supply_agreement       |            82 |          6   |           1 |
| eisenkrone-montan       | feldspat-orbitalbergbau | supply_agreement       |            67 |        290.8 |           1 |
| eisenkrone-montan       | lichtacker-agrarsysteme | supply_agreement       |            59 |        205.5 |           1 |
| corvane-biomedical      | eisenkrone-montan       | supply_agreement       |            60 |         71.7 |           1 |
| eisenkrone-montan       | corvane-biomedical      | joint_venture          |            84 |        459.6 |           1 |
| lichtacker-agrarsysteme | corvane-biomedical      | supply_agreement       |            64 |         69.7 |           1 |
| helix-meridian          | corvane-biomedical      | logistics_partnership  |            75 |        602.1 |           1 |
| corvane-biomedical      | driftwood-salvage       | supply_agreement       |            13 |          2.3 |           0 |

## Mitarbeiter mit Schlüsselrollen (Auswahl)
| slug                    | full_name               | role_code    |   intel_access_level |   loyalty |   bribe_susceptibility |
|:------------------------|:------------------------|:-------------|---------------------:|----------:|-----------------------:|
| feldspat-orbitalbergbau | Theodor Krause          | executive    |                    3 |        80 |                     54 |
| feldspat-orbitalbergbau | Albertine Süßebier      | relations    |                    2 |        62 |                     60 |
| feldspat-orbitalbergbau | Aleksandra Koch         | relations    |                    2 |        78 |                     43 |
| feldspat-orbitalbergbau | Slavko Geisel           | relations    |                    2 |        55 |                     96 |
| driftwood-salvage       | Tina Gould              | executive    |                    3 |        49 |                     56 |
| driftwood-salvage       | Erin Cisneros           | relations    |                    2 |        60 |                     37 |
| lichtacker-agrarsysteme | Reimar Rörricht         | executive    |                    3 |        66 |                     63 |
| lichtacker-agrarsysteme | Hülya Matthäi           | relations    |                    2 |        78 |                     18 |
| lichtacker-agrarsysteme | Heinz Dieter Schmidtke  | relations    |                    2 |        72 |                     33 |
| lichtacker-agrarsysteme | Kaspar Täsche           | intelligence |                    3 |        55 |                     61 |
| corvane-biomedical      | Jason Armstrong         | executive    |                    3 |        56 |                     57 |
| corvane-biomedical      | John Aguirre            | relations    |                    2 |        89 |                     21 |
| corvane-biomedical      | Richard Chavez          | intelligence |                    3 |        53 |                     76 |
| eisenkrone-montan       | Roswitha van der Dussen | executive    |                    3 |        56 |                     51 |
| eisenkrone-montan       | Esther Bauer            | relations    |                    2 |        53 |                     76 |
| eisenkrone-montan       | Dolores Mühle           | intelligence |                    3 |        96 |                     49 |
| eisenkrone-montan       | Josip Sölzer            | intelligence |                    3 |        87 |                     31 |
| helix-meridian          | Elizabeth Lopez         | executive    |                    3 |        85 |                     31 |
| helix-meridian          | Stephanie Turner        | relations    |                    2 |        69 |                     25 |
| helix-meridian          | Jennifer Smith          | relations    |                    2 |        68 |                     59 |
| helix-meridian          | Desiree Schwartz        | intelligence |                    3 |        58 |                     78 |
| helix-meridian          | Bryan Wilson            | intelligence |                    3 |        54 |                     68 |
| helix-meridian          | Darren Harris           | intelligence |                    3 |        35 |                     69 |
| helix-meridian          | Melvin Brown            | intelligence |                    3 |        63 |                     35 |
| helix-meridian          | Kayla Cannon            | relations    |                    2 |        57 |                     55 |
| helix-meridian          | Amber Valdez            | relations    |                    2 |        43 |                     91 |
| helix-meridian          | Ronald Simpson          | intelligence |                    3 |        57 |                     54 |
| helix-meridian          | Edward Bennett          | relations    |                    2 |        77 |                     66 |
| helix-meridian          | Kathleen Ramsey         | relations    |                    2 |        60 |                     50 |
| helix-meridian          | Tyler Garcia            | relations    |                    2 |        55 |                     71 |
| helix-meridian          | Robert Hernandez        | intelligence |                    3 |        25 |                     39 |
| helix-meridian          | Tracy Jackson           | relations    |                    2 |        53 |                     63 |
| helix-meridian          | Kathy Gutierrez         | relations    |                    2 |        54 |                     42 |
| helix-meridian          | Christine Estrada       | relations    |                    2 |        33 |                     58 |
| helix-meridian          | Francisco Allen         | relations    |                    2 |        48 |                     87 |
| helix-meridian          | Michael Pugh            | intelligence |                    3 |        46 |                     55 |
| helix-meridian          | Donna Miller            | relations    |                    2 |        44 |                     97 |
| helix-meridian          | Paul Miller             | relations    |                    2 |        49 |                     72 |

## Finanzen über den Datenzeitraum
| slug                    |   revenue_mcr |   net_mcr |
|:------------------------|--------------:|----------:|
| corvane-biomedical      |         353.6 |      61.3 |
| driftwood-salvage       |          61.6 |      25.9 |
| eisenkrone-montan       |        3676.6 |     722.5 |
| feldspat-orbitalbergbau |          32.3 |       4.6 |
| helix-meridian          |        3012.2 |     405.7 |
| lichtacker-agrarsysteme |         337.3 |      51.2 |
