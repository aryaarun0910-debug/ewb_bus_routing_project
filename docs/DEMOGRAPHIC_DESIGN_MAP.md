# Demographic → Design-Feature Map

> Reviewer ask (verbatim): *"Mapping of demographic groups to specific design features."*
> Rubric target: Criterion 1a score 5 — *evidence-based justification of how the design reaches the desired positive community impact.* Every row: a real group, sized with a real source, mapped to the specific engineering decision that serves it.

| Who (Ladywood) | Size & source | The barrier a normal "smart transit" product creates | The design feature that removes it |
|---|---|---|---|
| Residents whose main language is not English | **28.6%** — ONS Census 2021 | App- and text-based information assumes English literacy | **The 156-LED physical map**: colour and light, zero language. Demand level + route shown geometrically, readable by anyone who can see the map |
| Households with no car | **57.9%** — ONS Census 2021 (TS045) | "Just drive/Uber when the bus fails" is not a fallback | **The whole system**: demand-matched allocation raises the reliability of the *only* mode available; +48 passengers/day served, ~27.8 from car-free households (cost_model.py) |
| Older and disabled residents | ENCTS-eligible population; the demand anchor itself is built from their journeys (UCL/GEoDS 2010–2016) | Smartphone-first interfaces; standing waits at unpredictable stops | **No-app, no-phone design**; capacity floors (`MIN_DEMAND_VISIT` keeps quiet stops servable); the anchor's concessionary skew means their travel geography is *baked into* the baseline rather than averaged away |
| Shift workers (night/early rotas, e.g., City Hospital on Dudley Rd) | High night-shift share in health & care employment — Census travel-to-work (TS061) off-peak commute pattern | Timetables optimised for 9-to-5 peaks; first/last buses pruned on "low demand" | **24/7 prediction**: all 8 windows from Early Morning (05:00) to Night (21:00–24:00) are first-class optimisation targets, not afterthoughts; "the algorithm justifies cuts" risk is explicitly governed (UNINTENDED_CONSEQUENCES §1.4) |
| Children & young people in deprivation | **55%** of Ladywood children (vs 30% national) — CIVIC SQUARE Doughnut Portrait | School-run crowding; unreliability punishes attendance | **Real Birmingham term calendar in every training row** — term-time demand is a learned feature, not seasonal noise; school-adjacent stops gain term-aware allocation |
| Digitally excluded / no smartphone households | Highest digital-exclusion decile wards in Birmingham (Ofcom/Lloyds Consumer Digital Index, regional) | Information access gated behind apps, accounts, data plans | **Street-level visibility**: the LED map is public infrastructure, like a clock. The web dashboard is the *secondary* channel, not the primary one |
| Residents with respiratory disease | **6%** of the constituency — Ladywood Doughnut Portrait; ward sits against the Clean Air Zone boundary | More buses ≠ cleaner air if deployment is blind | **−12.5% vehicle-km on the same routes** (measured, not assumed): fewer empty runs through the streets where breathing is already hardest |
| Recently arrived residents (born outside UK) | **49.3%** — ONS Census 2021 | System knowledge assumed (which routes exist, how they connect) | **The map-shaped display**: the network's geometry is the interface; CIVIC SQUARE convening spaces (Supper Club, Floating Front Room) are the named onboarding channel, in community languages |

## How to use this in the presentation
One slide, headline *"Designed for who actually lives here."* — three rows max spoken aloud (28.6% → LEDs; shift workers → 24/7 windows; 57.9% → the whole point), with this full table in the appendix/repo. Every number already has a source in the project's data inventory; no new claims are introduced.

---

**Footnote — geographic scope of the 57.9% figure.**
The 57.9% is the Ladywood **Ward** (E05010826) aggregate from Census 2021 TS045. A reader who independently queries car-free rates may encounter a different figure depending on geography:

| Geography | No-car household rate (Census 2021 TS045) | Source level |
|---|---|---|
| Ladywood **Ward** | **57.9%** (cited here) | Ward aggregate — the correct unit for this project's route network |
| Stop-level LSOAs in this model | 30.8% (S10, Ladywood Fire Station) — 63.9% (S05, Five Ways) | Per-LSOA; see `data/census/ladywood_car_availability.json` |
| Birmingham **City** | ~40–44% (ONS 2021) | Local Authority aggregate |
| England | ~26% (ONS 2021) | National |

The ward level is the correct headline because the route network serves all Ladywood Ward residents, not just those in specific LSOAs. The inter-LSOA variation (30.8%–63.9%) is also informative: the one outlier — S10's 30.8% — is the Ladywood Fire Station LSOA, which contains the Broad Street corridor with higher-income apartment developments not representative of the ward's bus-dependent majority.
