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

## 7. The honest bottom line

The economics here are favourable enough (≈1.1-month break-even, ~£13.8k/yr
net operating saving, ~£51.7k/yr social value) that **cost is not the
limiting factor** on whether a system like this should be built. The limiting
factor is **prediction accuracy against real, observed ridership data** — see
the [Model Card](../MODEL_CARD.md) for the full, honest accounting of where
the demand model's anchor is real and where its temporal shape is still
modelled. That is deliberately where the project's remaining effort, and any
follow-on funding, should be directed first.
