# Unintended Consequences — Structured Analysis

> Rubric target: Criteria 1a/1b/1c, score 4 — *"a structured description of the potential relationships and unintended consequences of the design to the [community / environmental / economic] context"* — and the evidence-based mitigations that score 5 requires.
> Structure per entry: **Mechanism → Who/what is affected → Likelihood/severity → Mitigation already in the design → Residual risk & monitoring.**

## 1 · Community / social

### 1.1 The low-demand spiral (self-fulfilling withdrawal)
**Mechanism.** The optimiser skips stops below `MIN_DEMAND_VISIT`. A stop the model under-predicts gets less service; residents adapt by not waiting there; observed demand falls further; the de-prioritisation entrenches itself.
**Affected.** Precisely the people the project exists for — isolated, elderly, and disabled residents at quiet stops.
**Mitigation in design.** (a) Resident-marked stops become *hard equity constraints* in the optimiser (governance Phase 1 — encoded in `demand_route_optimizer.py`, not a promise); (b) the dynamic plan reallocates a *fixed* fleet rather than cutting total service; (c) quarterly Supper Club equity review with the allocation-mismatch index on the table.
**Residual.** Monitor unserved-stop lists in `route_plan.json` per quarter; a stop appearing in >50% of windows triggers a routing-rule review.

### 1.2 Crime data as a feature can import policing bias
**Mechanism.** `crime_total_2024` (police.uk) is a *recorded-crime* count — it measures police activity as much as crime. If the model learns "high-crime → high demand" from it, service allocation inherits any patrol bias.
**Affected.** Over-policed micro-areas; trust in the system among residents who already distrust data systems.
**Mitigation (done).** We ablated the feature (`analysis/crime_ablation/`): it carried no signal — with 15 stops a static per-stop count is redundant with stop identity — and removing it slightly *improved* out-of-year generalisation (R² 0.9445 → 0.9450). So we **removed `crime_total_2024` from the model entirely**. No policing-derived input remains in the routing model; crime is still surfaced in the dashboard as caveated area context, but it never influences service allocation. *Tested and deleted* — the strongest possible answer to the redlining critique.
**Residual.** Document the ablation; let residents vote the feature in or out at governance Phase 2.

### 1.3 The concessionary anchor over-weights older/disabled travel patterns
**Mechanism.** ENCTS smartcard data (2010–2016) is predominantly 60+ and disabled passengers; anchoring relative demand to it tilts the baseline toward their travel geography.
**Affected.** Younger commuters and shift workers whose stop ranking may be understated.
**Mitigation.** Tier clamping bounds the anchor's influence; ±20% sensitivity shows the model learns *shape*, not anchor scale (R² spread 0.0004). Notably, this is the rare bias that errs *toward* the most transport-dependent groups.
**Residual.** Replace anchor on first APC delivery; until then, named in MODEL_CARD ethics section.

### 1.4 "The algorithm said so" — data-driven service as cover for cuts
**Mechanism.** A demand model built to *add* responsiveness can be repurposed by a cost-cutting operator to *justify* withdrawing service ("the model shows nobody uses the 21:00 run").
**Affected.** Night-shift workers, NHS staff on Dudley Road — exactly the low-volume, high-dependence trips.
**Mitigation.** Governance is the design here: stewardship sits with CIVIC SQUARE and residents, not the operator; the deployment constitution states the model may reallocate but never reduce total service-km without a community review.
**Residual.** This is a contractual/governance risk, not a technical one — name it in the operator MoU at pilot stage.

### 1.5 Surveillance perception
**Mechanism.** A "system that predicts where people are" can read as monitoring, in a ward with 49.3% residents born outside the UK and varied trust in institutions.
**Mitigation.** No personal data anywhere in the pipeline — all inputs are aggregate, open, and listed publicly; the physical LED map displays *outputs*, collects nothing. The Repair-Club maintenance model keeps hardware in community hands.
**Residual.** Communication task: the data-sources poster at each displaying stop.

## 2 · Environmental

### 2.1 Hardware life-cycle vs. operational savings
**Mechanism.** Saving ~2,370 vehicle-km/yr must not be bought with high embodied-carbon electronics churn.
**Numbers.** One-off hardware £1,315 (3 hubs); WS2812B strips, Pi, DE1-SoC are commodity, repairable items. Embodied CO₂ of the full kit (~50–100 kg CO₂e, supplier LCA figures) is repaid by diesel savings in well under a year (12.5% of ~52 km/day at ~1.3 kg CO₂/km).
**Mitigation in design.** `docs/design/END_OF_LIFE.md` (already in repo) covers WEEE routing, battery handling, and the Neighbourhood Repair Club as first-line maintenance — repair before replace.
**Residual.** Solar+battery stop units (proposed LoRa phase) add lithium cells; specify LiFePO₄ and a take-back clause in procurement.

### 2.2 Rebound / induced demand
**Mechanism.** Better-matched service makes bus travel more attractive → more trips. More boardings on the *same* fleet-km is the goal (modal shift from cars, taxis, foregone trips); but if demand growth eventually forces fleet growth, absolute emissions rise.
**Assessment.** In a 57.9% car-free ward, induced bus trips displace walking-in-rain and missed appointments more than car journeys — a welfare gain, not an emissions loss. Fleet-growth decisions remain with the operator and are visible in the cost model.

### 2.3 Empty-running risk
**Mechanism.** Dynamic routing concentrated on predicted demand could increase dead-running (repositioning) km that don't serve passengers.
**Mitigation.** `route_time_min` includes all inter-stop travel; the 12.5% reduction is *measured on total route km, including repositioning*, across all 32 snapshots — not assumed.

## 3 · Economic

### 3.1 Driver hours and jobs
**Mechanism.** 12.5% fewer vehicle-km could be read as 12.5% less driver work.
**Assessment.** The dynamic plan runs the *same number of buses* in service windows; the saving is fuel, maintenance and dead-mileage, not headcount. Driver-triggered cadence reviews (governance Phase 3) give drivers standing in the loop. National Express WM 2024 pay scale is used in the cost model — drivers are a stakeholder, not an externality.
**Residual.** Make this explicit in the operator MoU; unions consulted at pilot.

### 3.2 Maintenance burden lands on the community
**Mechanism.** Grant-funded build → community stewardship could become unpaid labour extraction.
**Mitigation.** Costed honestly: £903/yr annualised deployment cost *includes* maintenance; Repair Club participation is by existing rhythm, not new obligation; WMCA/TfWM handoff is the named exit if stewardship fails (Code for America's Brigade collapse is cited as the cautionary precedent, not wished away).

### 3.3 Operator gaming of the metric
**Mechanism.** Once allocation-mismatch becomes a KPI, an operator can optimise the *index* (small cosmetic reallocations) rather than the *service*.
**Mitigation.** The index is computed from the same `route_plan.json` that actually drives the displays — there is no separate reporting channel to game; residents define additional metrics in Phase 2.

---
*Every mitigation above points at an artefact that already exists in the repo (file named) or a governance step already in the stakeholder plan — this analysis is structural, not rhetorical.*
