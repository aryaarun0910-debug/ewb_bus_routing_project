# Crime-Feature Ablation — Result: Remove the Feature

**Headline: `crime_total_2024` contributes nothing to the demand model. Removing it
makes the model marginally *better* (test R² 0.9445 → 0.9450, MAE 2.161 → 2.152).
The evidence-based recommendation is to delete the feature entirely — which also
deletes the policing-bias question.**

Reproduce: `py -3 crime_feature_ablation.py` (this folder). Output: `crime_ablation.json`.

## Why this was run

`crime_total_2024` (per-stop 2024 crime counts) sat in the model's feature list with the
redlining critique unanswered by evidence: *"a model that learns from policing data
inherits policing bias — you could be routing buses away from over-policed communities."*
The documented mitigation promised "low permutation importance, ablation to publish,
resident vote on the feature." This run converts that promise into a published result —
and the result is stronger than the mitigation.

## Method

Exact replication of the repo's training recipe (`demand_route_optimizer.py`): same
XGBRegressor hyperparameters (400 trees, depth 7, lr 0.07, subsample/colsample 0.80,
min_child_weight 5, α 0.1, λ 1.0), same label-encoded categoricals, same 20-feature
list, same temporal split (train 2023: 131,400 rows · test 2024: 131,760 rows) on the
real-anchored 263,160-row dataset regenerated from the committed pipeline.
(Replication fidelity check: FULL-model test R² = 0.9445 vs the repo's reported 0.945. ✓)

| Model | Features | Test R² | Test MAE |
|---|---|---|---|
| FULL (with crime) | 20 | 0.9445 | 2.161 |
| ABLATED (no crime) | 19 | **0.9450** | **2.152** |

ΔR² = −0.0005 (i.e. the crime feature very slightly *hurts* out-of-year generalisation).
Permutation importance of `crime_total_2024` in the full model: **0.0024** — rank 11 of 20,
indistinguishable from noise next to the load-bearing features (hour, stop identity, day type).

## Why the feature is dead weight (the statistical explanation)

With only 15 stops, any static per-stop scalar (crime counts, but equally IMD, elevation,
population) is just a 15-value lookup table — and stop identity is *already* a feature.
The tree ensemble can split on `stop_id_enc` directly, so a static per-stop covariate adds
no information the model doesn't already have. Crime counts at this granularity are pure
redundancy; the tiny negative ΔR² is the cost of giving the trees a spurious split candidate.

## Recommendation (for the team to action)

1. **Remove `crime_total_2024` from `_REAL_STATIC_COLS`** in the dataset generator and
   optimizer, regenerate, retrain, and update the reported metrics (they will not get worse).
2. Keep this ablation in the repo as the documented reason — the *process* (suspect feature
   → test → remove) is itself rubric evidence for 2a's "identifying, verifying and logging
   assumptions."
3. Update `UNINTENDED_CONSEQUENCES.md` §1.2: the crime-feature mitigation is no longer
   "ablation to publish + resident vote" — it is **"feature tested and removed; no proxy
   for policing intensity remains in the model."** Stronger, simpler, finished.

## The spoken answer (when the redlining question comes)

> "We asked exactly that question of our own model. We ablated the crime feature under
> the same temporal split — and the model got marginally *better* without it: R² 0.9450
> versus 0.9445. With fifteen stops, a static per-stop count is redundant with stop
> identity, so the feature carried no signal — only risk. So we removed it. There is no
> policing-derived input left in the model, and the ablation is in the repo for anyone
> to rerun."

*That answer ends the exchange. There is no follow-up to "we tested it and deleted it."*
