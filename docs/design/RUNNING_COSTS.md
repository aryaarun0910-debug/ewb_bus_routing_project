# Running Costs & Economic Sustainability

How much does this system cost to run, who benefits, and is it sustainable
without a commercial revenue model? All figures below are produced by
[`analysis/cost_model.py`](../../analysis/cost_model.py) — run
`python analysis/cost_model.py --json` to reproduce them. They are
**order-of-magnitude estimates for a Ladywood-scale pilot** (the three real
routes 8A/8C, 80, 126; 3 vehicles), intended to frame viability, not serve as
a costed tender.

## 1. Sources and rates used

| Constant | Value | Source |
|---|---|---|
| Vehicle operating cost | £4.47/vehicle-km | [DfT Bus Statistics, Table BUS0404](https://www.gov.uk/government/statistical-data-sets/bus04-costs-and-revenues) — English metropolitan operators, 2022/23 |
| Driver wage | £14.42/hr (×1.28 NI/pension overhead = £18.46/hr effective) | National Express West Midlands 2024 driver pay scale |
| Value of passenger time | £9.80/hr (2023 prices) | [DfT TAG Unit A1.3, "User and Provider Impacts"](https://www.gov.uk/government/publications/tag-data-book) — low-income working value |
| Ladywood median wage | £13.86/hr | ONS ASHE 2023, Ladywood Parliamentary Constituency (£28,837/yr ÷ 2,080 hrs) |
| Car-free households | 57.9% | ONS Census 2021, Ladywood Ward |
| Fuel poverty rate | 26.6% | CIVIC SQUARE Neighbourhood Doughnut Portrait 2022 |
| Average journey length | 22.0 min | TfWM Journey Planner, 2024 |
| Dynamic vehicle-km reduction | 12.5% (conservative mid-estimate) | Empirically observed 11–14% reduction from the 2-opt optimiser vs. fixed corridors across all scenario/window combinations in `route_plan.json` |
| Operating days/year | 300 | Excludes bank holidays + reduced Sunday service |

## 2. Capital / deployment cost (one-off + amortised)

| Item | Cost |
|---|---|
| Terasic DE1-SoC FPGA (×3 hubs) | £450 |
| WS2812B LED display modules (×3 hubs) | £180 |
| Edge compute (Raspberry Pi 5 ×1) | £85 |
| Cabling + enclosure | £320 |
| Installation labour (8 hrs × £35/hr) | £280 |
| **Total hardware (one-off)** | **£1,315** |
| Server hosting (annual) | £240 |
| TfWM GTFS data subscription | £0 (open licence) |
| Maintenance contingency (annual) | £400 |
| **Annualised deployment cost** (hardware ÷ 5-yr amortisation + annual software) | **£903/yr** |

A screen-free LED map is deliberately the cheap, robust option vs. a
commercial digital-signage screen (typically £800–2,000 installed per unit),
and incurs no licensing cost.

## 3. Operating cost: fixed schedule vs. dynamic routing

| | Fixed schedule | Dynamic routing | Saving |
|---|---|---|---|
| Total vehicle-km/day | 52.0 | 45.5 | −12.5% |
| Vehicle-km cost/day | £232.44 | £203.39 | |
| Driver-hours/day | 8.67 | 7.58 | |
| Driver cost/day | £159.97 | £139.97 | |
| **Total operating cost/yr** | **£117,722** | **£103,007** | **£14,715/yr (gross opex saving)** |

Net of the £903/yr annualised deployment cost, the **net annual saving is
£13,812/yr**, which against the £1,315 one-off hardware spend gives a
**break-even of ~1.1 months**. (This is fast because the operating-cost
saving — driven by a 12.5% cut in vehicle-km — dwarfs the modest one-off
hardware cost; the binding constraint on real-world viability is *prediction
accuracy*, not capital cost — see [Model Card → Known
Limitations](../MODEL_CARD.md#known-limitations--the-honest-gap).)

## 4. Social value (DfT TAG methodology)

Demand-aware allocation serves an estimated **48 additional passengers/day**
(of which ~27.8/day are from car-free households — 57.9% of Ladywood). At an
average 22-minute journey and £9.80/hr value of time (DfT TAG, low-income
working rate):

```
social value/day = 48 passengers × (22/60) hr × £9.80/hr  = £172.48
social value/yr  = £172.48 × 300 operating days            = £51,744/yr
```

## 5. Who benefits, and how

**Bus operator (National Express West Midlands)**
- A 12.5% cut in vehicle-km for the *same* fleet and routes served means lower
  fuel/maintenance/driver-hour cost per passenger — fewer near-empty "ghost
  bus" runs on low-demand windows, more capacity steered to where it's needed.
- Higher load factor on the same fleet → more fare revenue without buying
  more vehicles.

**Local authority / WMCA**
- Higher patronage strengthens the case against further service cuts (the
  Ladywood bus network has already shrunk significantly over the past
  decade).
- Reduced vehicle-kilometres on low-demand windows directly cuts NO₂/PM
  emissions in a ward where a meaningful share of residents report
  respiratory conditions.

**Residents**
- A more reliable service where demand actually concentrates → better access
  to work, healthcare, and education for the 57.9% of Ladywood households with
  no car — particularly shift workers, carers, and students whose travel
  patterns don't match a fixed peak-hours timetable.

## 6. Sustaining an open-source release without a commercial model

> The figures above cover *running* costs. For what happens to the physical
> hardware at the end of its life — WEEE compliance, named local recycling
> partners, and modular/repairable design — see
> [`docs/design/END_OF_LIFE.md`](END_OF_LIFE.md).

1. **Civic stewardship, not vendor lock-in.** CIVIC SQUARE's Neighbourhood
   Public Square already runs a Microfactory and a Library of Things; a
   community-owned, community-repaired LED map (their existing Neighbourhood
   Repair Club already fixes electronics) fits that model directly.
2. **Grant + in-kind funding, not subscription revenue.** Capital
   (~£1,315/hub) is small enough for a single WMCA active-travel/air-quality
   grant or operator-sponsorship line; the ~£903/yr running cost is well
   within reach of a community group or single-line council budget item.
3. **Low maintenance surface by design.** All data sources are open
   (£0 licensing — see the rates table above), road geometry is cached rather
   than queried per-request, and the hardware is commodity-grade
   (Raspberry Pi / FPGA / WS2812B) with the controller logic documented in
   [`fpga/README.md`](../../fpga/README.md) so any competent maker can rebuild
   or repair a unit.
4. **Forkable, not dependent.** The stack is entirely standard
   (Python/FastAPI, React, GTFS, NetworkX road-graph routing) — no single
   vendor, API key, or maintainer is a single point of failure.

### Named precedents — and an honest reckoning with how they've struggled

A reviewer specifically pushed us to go deeper here: "elaborate on the
long-term sustainability of the open-source release without a commercial
revenue model." The honest answer starts by admitting this is a genuinely
hard, industry-wide problem — not a gap unique to us. The **2024 Open Source
Software Funding Report** found that **86% of open-source contributors are
unpaid**, and that funders systematically prefer paying for shiny new
features over the unglamorous work of keeping something already-built alive
([opensourcefundingsurvey2024.com](https://opensourcefundingsurvey2024.com/);
[Digital Public Goods Alliance on the "free-rider problem" in open
infrastructure](https://www.digitalpublicgoods.net/blog/digital-commons-and-digital-public-goods-finding-common-ground-for-policymakers)).
Even the **OpenStreetMap Foundation** — arguably the most successful open
geodata project in the world — runs on an annual fundraising target of
**~£521,000** for not much more than servers and a single paid engineer
([OSMF](https://supporting.openstreetmap.org/)), and **Code for America
formally ended its 25,000-volunteer Brigade network in 2023**, citing that
"it has become increasingly difficult to raise and sustain multi-year
investment for a national [volunteer] network" — a direct, citable warning
against assuming volunteer goodwill alone is a sustainability plan
([Code for America](https://codeforamerica.org/news/reflections-on-the-brigade-networks-next-chapter/)).

The model that *has* worked at our scale is **mySociety** (FixMyStreet,
TheyWorkForYou) — the closest UK precedent to what we're proposing. They
combine charitable grants (JRCT, Open Society, Hewlett, MacArthur), individual
donations, **and** a trading subsidiary, **SocietyWorks**, which licenses and
hosts paid versions of their open-source tools for local councils — generating
commercial-style income *without* compromising the free, open community
release ([mySociety](https://www.mysociety.org/about/funding/)). **Digital
Matatus** — the Nairobi transit-mapping project that is the closest mission
analogue to ours — followed exactly the path we'd realistically take: a
university-consortium build seeded by a philanthropic grant (Rockefeller
Foundation), later expanded via a second grant (Expo 2020 Dubai)
([MIT Civic Data Design Lab](https://civicdatadesignlab.mit.edu/Digital-Matatus)).

**Concrete funding routes that exist, named, for a project at exactly this
stage and scale:**

| Source | What it offers |
|---|---|
| National Lottery Community Fund (Awards for All) | £300–£20,000, up to 2 years, for community-benefit pilots ([tnlcommunityfund.org.uk](https://www.tnlcommunityfund.org.uk/funding/funding-programmes/national-lottery-awards-for-all-england)) |
| West Midlands Combined Authority / TfWM | Ran a £22m Future Transport Zone trialling demand-responsive services; the West Midlands Innovation Accelerator is a live regional channel for match-funding ([WMCA](https://www.wmca.org.uk/what-we-do/economy-and-innovation/west-midlands-innovation/west-midlands-innovation-accelerator/)) |
| Innovate UK / UKRI | The standard UK public route from pilot to scale-up; a recent policy proposal explicitly recommends ring-fencing **£7.5m/yr of a £12.5m UK open-source fund specifically for *maintenance*, not just innovation** — evidence that this exact problem is now recognised at national policy level ([British Progress](https://britishprogress.org/uk-day-one/a-uk-open-source-fund-to-support-software-innovati)) |
| GDS Local (DSIT, launched Nov 2025) | A new government unit working directly with councils on everyday digital services — a live channel for a council adoption/hosting handoff ([GOV.UK](https://www.gov.uk/government/news/people-across-uk-to-benefit-from-easier-access-to-local-services-as-councils-get-digital-boost)) |

**Our actual proposed model**, synthesising the above rather than inventing
something untested: **grant-seeded build → proven pilot → handoff to a local
institutional host** (Birmingham City Council / TfWM, mirroring how
SocietyWorks operationalised mySociety's tools for councils), governed by a
small open steering committee in the spirit of OSMF's membership board —
university, council, and **community representatives with real decision-making
power**, specifically to avoid the volunteer-burnout failure mode that ended
Code for America's Brigade network. This is deliberately a *modest, named,
precedented* plan rather than an invented commercial model — which is, we'd
argue, the more credible thing to put in front of reviewers who have seen a
hundred teams promise revenue streams that don't materialise.

## 7. The honest bottom line

The economics here are favourable enough (≈1.1-month break-even, ~£13.8k/yr
net operating saving, ~£51.7k/yr social value) that **cost is not the
limiting factor** on whether a system like this should be built. The limiting
factor is **prediction accuracy against real, observed ridership data** — see
the [Model Card](../MODEL_CARD.md) for the full, honest accounting of where
the demand model's anchor is real and where its temporal shape is still
modelled. That is deliberately where the project's remaining effort, and any
follow-on funding, should be directed first.
