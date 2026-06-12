# Demand Shapes Don't Decay — Three Years of Observed Evidence

**The result: hour-of-day bus demand shapes are stable across three consecutive years
at minimum pairwise Pearson r = 0.9984 (weekday 0.9994, Saturday 0.9984, Sunday 0.9985).
The demand model's core input is structurally frozen — its retraining cadence is years,
not weeks.**

Source: TfL BUSTO complete archive, 2023–24 / 2024–25 / 2025–26, boardings per stop per
quarter-hour, Routes 1–149 (TfL Open Data licence). Reproduce:
`py -3 shape_stability_across_years.py`. Outputs: `shape_stability.png`, `.json`.

## Why this matters

The standard failure mode of deployed ML systems is drift: the world changes under the
model. Three years of observed boardings across London's bus network say the *shape* of
urban bus demand barely moves — peak hours are identical across years (weekday PM peak
15:00–17:00; weekend midday 13:00–14:00), and the full 24-hour curves correlate at
r ≥ 0.998 in every pairwise year comparison.

Three consequences:

1. **The system's most important input is its most stable input.** A demand model built
   on shape priors + slowly-varying anchors is the *opposite* of a fragile ML product.
   Structural breaks (the MODEL_CARD's named risk) remain the residual concern — but
   ordinary drift is now empirically bounded at ~nothing per year.
2. **The weekend finding is structural, not a 2023 artefact.** The midday weekend peak
   (13:00–14:00) appears in all three years. Assumption A12 (weekend curves should be
   midday-peaked, not flattened-commuter) is now triple-confirmed; fixing the weekend
   curve is a one-line change with three years of evidence behind it.
3. **Operating cost of staying accurate ≈ zero.** Annual revalidation = re-running one
   script against TfL's yearly release. No data pipeline, no labelling, no vendor.

## Honest caveats

- London, not Ladywood (same transferable-shape-prior argument as SHAPE_VALIDATION.md —
  this measures the stability of the shape *family*, which is exactly what the model uses).
- Network-aggregate shapes (Routes 1–149 group); per-stop stability will be lower, but
  the model consumes tier-level shapes, not per-stop curves.
- Three years is three years: it brackets post-COVID normalisation but not the next
  structural break. That risk stays named in the assumption log (A3), unchanged.

*Attribution: Powered by TfL Open Data.*
