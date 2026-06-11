# Emissions Quantification — Putting Numbers on the 12.5%

> Gap (Agent A finding): the headline environmental benefit — 12.5% fewer vehicle-km — has a full financial model (`analysis/cost_model.py`) but the CO₂/NOₓ conversion was never computed. Rubric 1b score 5 requires an *evidence-based approach to justify the desired positive environmental impact*. This is that one multiplication, done in the project's own honest-ranges style.

## The arithmetic

| Quantity | Value | Source |
|---|---|---|
| Fixed-schedule route distance | 52.0 km/day | `analysis/cost_model.py` |
| Dynamic-optimiser distance | 45.5 km/day | same — measured across all 32 scenario/window snapshots, not assumed |
| Saved distance | **6.5 km/day → 2,372 km/yr** | 365-day service |
| CO₂e factor, diesel local bus | 1.0 – 1.3 kg CO₂e / vehicle-km | DESNZ GHG Conversion Factors (local bus) low end; DfT TAG / LowCVP real-world duty-cycle figures upper end — *verify against the current-year DESNZ release before submission* |
| **Annual CO₂e avoided** | **≈ 2.4 – 3.1 tonnes CO₂e/yr** | 2,372 km × factor |

## NOₓ and particulates — fleet-dependent, so say so

| Fleet case | NOₓ factor | Annual NOₓ avoided |
|---|---|---|
| Euro VI (National Express WM core fleet) | ~0.3–0.5 g/km real-world | ~0.7–1.2 kg/yr |
| Older Euro V vehicles, if deployed | ~4–8 g/km | ~9–19 kg/yr |

Tailpipe PM is near-zero for Euro VI; **brake- and tyre-wear PM scales directly with vehicle-km**, so the 12.5% reduction applies to non-exhaust PM regardless of engine standard — worth stating, because non-exhaust PM is the pollutant the Clean Air Zone does *not* regulate.

## Context that makes the number honest (and stronger)

- **2.4–3.1 tCO₂e/yr is small in national terms and significant in local ones.** Say exactly that. The claim is not "we solve transport emissions"; it is "the same fleet, better deployed, stops burning fuel on empty runs through the streets where 6% of residents have a respiratory disease."
- **Embodied-carbon payback:** the full hardware kit (~50–100 kg CO₂e embodied, supplier LCA basis) is repaid by avoided diesel in **under a month** of operation — the environmental break-even mirrors the 1.1-month financial break-even, a parallelism judges will remember.
- **Where it happens matters more than how much:** the avoided km are concentrated on the A4540 corridor — the CAZ boundary road — so the marginal exposure reduction lands on the highest-exposure residents. (Agent B's air-quality mining provides the measured NO₂ levels to cite here.)

## Recommended repo change (for the team to make — not made by this analysis)
Add ~10 lines to `analysis/cost_model.py` computing the table above from the same `route_plan.json` distances, so the environmental claim becomes script-traceable exactly like every economic claim. Print both the central estimate and the range.
