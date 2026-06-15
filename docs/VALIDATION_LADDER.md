# The Validation Ladder — Every Rung Points at Ladywood

Ladywood is the project. Every dataset below was mined for one purpose: to test the
Ladywood demand design against observed reality, rung by rung, each one closer to the
data nobody publishes for Ladywood itself.

| Rung | Dataset | What it observes | What it proved about the Ladywood design |
|---|---|---|---|
| 1 | **TfL BUSTO, London** (2.3M boardings/yr, per stop per ¼-hour) | UK urban boarding shapes | Weekday curves match at **r = 0.945 / 0.942 / 0.796** (major/medium/minor) |
| 2 | **BUSTO ×3 years** (2023–26 complete archive) | Year-over-year drift | Shapes frozen at **r ≥ 0.998** across all years and day types — the model's core input doesn't decay |
| 3 | **BUSTO weekend** → empirical curve | The real weekend shape | The flattened-weekday weekend curve (r = 0.677/0.549) replaced by an empirical 3-year curve: **r = 1.000/0.999**. Assumption A12: OPEN → RESOLVED |
| 4 | **Helsinki HSL** (6,708 stops, true stop-level APC totals) | How demand concentrates across stops | Real networks concentrate *more* than the model assumes (top tercile 95.5% vs modelled 73%) → the service-floor guarantee is more load-bearing in reality, not less. (Scale caveat: metro network vs 15-stop corridor) |
| 5 | **Wellington Metlink, NZ** (true hourly per-stop boardings *and alightings*, 862k weekday rows) | Hourly shapes, third country, true APC | **r = 0.963 / 0.956 / 0.809** — better than London. Two countries, two continents, one shape family. The asymmetric-minor-curve rationale is *untestable* here (privacy suppression covers every minor-stop cell) |
| 6 | **Sydney Opal tap-on/tap-off** (17.3M taps, 15-min bins, unsuppressed) | Boarding AND alighting asymmetry — the test Wellington couldn't run | **The minor-curve design is VINDICATED.** AM board/alight ratio rises monotonically down the tiers — major 1.02 (symmetric), medium 1.67, minor **1.87 AM / 0.68 PM**: low-volume locations board in the morning and alight in the evening, exactly as the repo's minor curve deliberately encodes. The ~0.80 minor-tier correlations in rungs 1 and 5 are an artefact of boarding-only data, not a design error. The last open shape question, closed in the design's favour, fourth country |
| 7 | **BODS AVL, Birmingham — LIVE since 2026-06-12** | The actual buses on the actual Ladywood corridors (32 vehicles observed on lines 8A/8C/80/126 at first poll) | Dwell-time fingerprint per stop per hour — the closest legal observable to Ladywood APC. Collector running; pilot-week results land before the deck freezes |
| 8 | **TfWM APC request** (filed; Wellington's fyi.org.nz request 14028 is the exact FOI precedent wording to cite) | The real thing | The gold standard, pending |

## How to say it on stage (one breath)

> "Nobody publishes Ladywood's boarding data — so we built a ladder to it. London says
> our weekday shapes are right. Three years of London says they don't decay. The same
> data fixed our weekend curve. Helsinki says demand concentrates even harder than we
> assume — so our service floor matters more, not less. Wellington — true passenger
> counts, the other side of the planet — says r = 0.96. The next rung is the buses on
> our own corridors, measured through the government's open data feed. And the top rung
> is filed with TfWM."

## What changed in the repo (completed)

1. **Empirical weekend curve adopted** — `EMP_SAT_SHAPE` / `EMP_SUN_SHAPE` in
   `generate_map_dataset.py` are now the 3-year BUSTO mean (`analysis/weekend_curve/`).
   Dataset regenerated and model retrained (R²=0.9421). Note: the weekend shape is
   *derived* from BUSTO data, so r ≈ 1.0 is by construction — the independent check
   is shape stability (r ≥ 0.998 across all three years, rung 2).
2. **Wellington added as shape-validation evidence #2** (rung 5 above; caveat: Jan–Feb
   2020, NZ summer, pre-COVID).
3. **A12 updated to RESOLVED** in `docs/ASSUMPTION_LOG.md`.
4. **BODS collector started** — rung 7 live since 2026-06-12.

*Sources: TfL Open Data; HSL (CC BY 4.0); Greater Wellington Regional Council FOI
release (fyi.org.nz request 14028); DfT BODS (OGL). No registrations, no personal data,
every file re-downloadable by anyone.*
