# Hour-of-Day Shape Validation — Modelled vs Observed (TfL BUSTO)

**The result: the project's synthetic weekday demand-shape curves match observed UK urban bus boardings at Pearson r = 0.945 (major stops), 0.942 (medium), 0.796 (minor). Weekend curves correlate more weakly (Saturday r = 0.677, Sunday r = 0.549) — see caveat 5.**

Validated against **2,321,805 observed boardings across 8,261 London stops** — TfL BUSTO, autumn 2023 typical weekday, boardings by stop by quarter-hour (TfL Open Data licence; the only UK open dataset at this resolution). Reproduce: `py -3 validate_shape_vs_busto.py` (data: `../data_mined/tfl_busto/`). Outputs: `shape_validation.png`, `shape_validation.json`.

## Why this matters — the story upgrade

The repo's central honesty disclosure says the hour-of-day demand shape *"is modelled, not observed"*, and reports that the only proxy previously available — GTFS service frequency — correlated at a median Pearson **0.06**. That number was honestly reported and correctly interpreted (timetables are not ridership). But it left the project's most important assumption (A1 in the assumption log) with no positive evidence at all.

This analysis closes that loop with the strongest public evidence that exists:

> *"We could not observe Ladywood's boarding curves — nobody publicly can. So we tested our modelled curves against the best observed data in the country: TfL's per-stop, per-quarter-hour boarding counts. Across 2.3 million boardings at 8,261 stops, our weekday shape correlates at r = 0.94–0.95 for major and medium stops. The shape we modelled is the shape UK cities actually have."*

And there's a poetic symmetry a presenter can use: the shape correlation (≈0.945) happens to equal the model's own temporal-split R² (0.945).

## The honest caveats (state them before anyone asks)

1. **London is not Ladywood.** This validates the *shape family* (UK urban dual-peak weekday), not Ladywood's specific levels or stop ranking. Levels come from the smartcard anchor; ranking sensitivity is separately bounded (±20% → R² spread 0.0004).
2. **The minor-stop curve diverges (r = 0.796) — and the reason is informative.** The project's "minor" curve was deliberately designed asymmetric: residential endpoint stops board heavily in the AM peak and mostly *alight* in the PM (commuters coming home). Observed low-volume London stops show a more symmetric dual peak — many are quiet central stops, not residential endpoints. The divergence is a *tier-taxonomy* difference, not a peak-timing error: observed and modelled peaks still land at 07:00–08:00 and 16:00–17:00.
3. **Tier mapping is by volume tercile.** London stops were assigned major/medium/minor by total boardings (top/middle/bottom third) to mirror the repo's importance tiers. Other mappings are possible; the headline correlations are robust to the obvious alternatives (quartiles, network-wide curve: r = 0.945 vs the major curve).
4. **Autumn 2023, term-time typical day** — consistent with the comparison purpose (the repo's curves are term-time weekday baselines before seasonal multipliers).
5. **Weekend correlations are weak (Saturday r = 0.677, Sunday r = 0.549) — and this is a finding, not a failure.** The repo derives its Saturday/Sunday curves by flattening the weekday major curve (×0.75 with a midday boost and a 0.30 floor for Saturday; ×0.50 with a 0.15 floor for Sunday). Observed London weekend boardings instead show a single broad **midday peak (12:00–15:00)** with no morning commuter spike — flattening a commuter-shaped curve cannot reproduce a genuinely different demand pattern. This is honest evidence that the project's weekend assumption is the *weakest-supported* part of the demand model, and should be logged as an OPEN item in the assumption log: if Ladywood's weekend ridership is dominated by shopping/leisure/hospital-visiting trips (plausible for a hospital-anchored route), a midday-peaked weekend curve would be more defensible than a flattened weekday curve.

## Where to use it

- **Repo:** add this folder as `analysis/shape_validation/` (script + outputs), and update the Caveats section: the gap statement stays, but gains "validated against TfL BUSTO observed boardings as a transferable shape prior, r = 0.94–0.95 (major/medium) on weekdays; weekend curves are flagged as an open assumption pending the same validation."
- **Assumption log:** add a new OPEN entry — "weekend demand-shape curves (Saturday/Sunday) are derived by flattening the weekday curve, not independently modelled; TfL BUSTO weekend data shows a single midday peak (12:00–15:00) rather than a flattened commuter curve, r = 0.677/0.549. Revisit if Ladywood APC weekend data becomes available."
- **Deck:** one line on the honesty slide's speaker notes — or, stronger, on slide 10 (robustness) as a seventh check.
- **Q&A:** when a judge asks "but how do you know your demand curves are right?" — this is now a one-breath answer with a chart.

*Attribution: Powered by TfL Open Data. Contains OS data © Crown copyright and database rights 2016 and Geomni UK Map data © and database rights [2019].*
