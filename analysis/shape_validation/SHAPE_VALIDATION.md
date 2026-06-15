# Hour-of-Day Shape Validation — Modelled vs Observed (TfL BUSTO)

**The result: the project's synthetic weekday demand-shape curves match observed UK urban bus boardings at Pearson r = 0.945 (major stops), 0.942 (medium), 0.796 (minor). The original flattened-weekday weekend curves correlated only weakly (Saturday r = 0.677, Sunday r = 0.549) — a finding that directly led to A12 being resolved: the weekend curves are now derived from TfL BUSTO data, not independently validated against it (see caveat 5).**

Validated against **2,321,805 observed boardings across 8,261 London stops** — TfL BUSTO, autumn 2023 typical weekday, boardings by stop by quarter-hour (TfL Open Data licence; the only UK open dataset at this resolution). Reproduce: `py -3 validate_shape_vs_busto.py` (data: `../data_mined/tfl_busto/`). Outputs: `shape_validation.png`, `shape_validation.json`.

## Why this matters — the story upgrade

The repo's central honesty disclosure says the hour-of-day demand shape *"is modelled, not observed"*, and reports that the only proxy previously available — GTFS service frequency — correlated at a median Pearson **0.06**. That number was honestly reported and correctly interpreted (timetables are not ridership). But it left the project's most important assumption (A1 in the assumption log) with no positive evidence at all.

This analysis closes that loop with the strongest public evidence that exists:

> *"We could not observe Ladywood's boarding curves — nobody publicly can. So we tested our modelled curves against the best observed data in the country: TfL's per-stop, per-quarter-hour boarding counts. Across 2.3 million boardings at 8,261 stops, our weekday shape correlates at r = 0.94–0.95 for major and medium stops. The shape we modelled is the shape UK cities actually have."*

And there's a useful symmetry a presenter can use: the shape correlation (0.94–0.95 for major/medium) and the model's own temporal-split R² (0.9421) land in the same band — the demand model's accuracy and the shape prior it was built on are mutually reinforcing, even though the two numbers are no longer expected to coincide exactly after retrains.

## The honest caveats (state them before anyone asks)

1. **London is not Ladywood.** This validates the *shape family* (UK urban dual-peak weekday), not Ladywood's specific levels or stop ranking. Levels come from the smartcard anchor; ranking sensitivity is separately bounded (±20% → R² spread 0.0002).
2. **The minor-stop curve diverges (r = 0.796) — and the reason is informative.** The project's "minor" curve was deliberately designed asymmetric: residential endpoint stops board heavily in the AM peak and mostly *alight* in the PM (commuters coming home). Observed low-volume London stops show a more symmetric dual peak — many are quiet central stops, not residential endpoints. The divergence is a *tier-taxonomy* difference, not a peak-timing error: observed and modelled peaks still land at 07:00–08:00 and 16:00–17:00.
3. **Tier mapping is by volume tercile.** London stops were assigned major/medium/minor by total boardings (top/middle/bottom third) to mirror the repo's importance tiers. Other mappings are possible; the headline correlations are robust to the obvious alternatives (quartiles, network-wide curve: r = 0.945 vs the major curve).
4. **Autumn 2023, term-time typical day** — consistent with the comparison purpose (the repo's curves are term-time weekday baselines before seasonal multipliers).
5. **Weekend curve: a derivation, not an independent validation (A12 RESOLVED).** The old flattened-weekday weekend curves scored r = 0.677 (Sat) / 0.549 (Sun) against BUSTO — diagnosing that flattening a commuter-shaped curve cannot reproduce the real UK weekend pattern (a single broad midday peak, 12:00–15:00, with no morning spike). This finding directly drove the resolution of A12: `EMP_SAT_SHAPE` / `EMP_SUN_SHAPE` in `generate_map_dataset.py` are now computed as the 3-year mean of TfL BUSTO Saturday/Sunday boardings (`analysis/weekend_curve/derive_empirical_weekend_curve.py`). Because the current weekend shape **is derived from** the same BUSTO data it would be tested against, reporting r ≈ 1.0 as a "validation" would be circular — it holds by construction. The independent robustness check for the weekend shape is the shape-stability analysis (`analysis/shape_stability/`): the empirical midday peak is consistent at r ≥ 0.998 across all three years (2023–24, 2024–25, 2025–26), confirming it is a stable structural feature of the data, not a one-year artefact.

## Where to use it

- **Repo:** this folder is committed as `analysis/shape_validation/`. The Caveats section in docs references r = 0.94–0.95 (major/medium weekday); weekend curves are documented as derived (not independently validated) — see caveat 5 above.
- **Assumption log:** A12 is marked RESOLVED. The weekend shape is now empirically derived from TfL BUSTO (analysis/weekend_curve/); A12 was originally OPEN when this doc was first drafted.
- **Deck:** one line on the honesty slide's speaker notes — or, stronger, on slide 10 (robustness) as a seventh check.
- **Q&A:** when a judge asks "but how do you know your demand curves are right?" — this is now a one-breath answer with a chart.

*Attribution: Powered by TfL Open Data. Contains OS data © Crown copyright and database rights 2016 and Geomni UK Map data © and database rights [2019].*
