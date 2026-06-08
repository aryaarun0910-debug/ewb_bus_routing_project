# Why XGBoost — A Real Comparison, Not a Justification After the Fact

We chose XGBoost (gradient-boosted decision trees) for the demand model
(see [`MODEL_CARD.md`](../MODEL_CARD.md)). Rather than assert that was the
right call, here is the comparison against the alternatives — with published
figures, including ones that *don't* favour us — so the choice can be judged
on evidence rather than taken on faith.

## 1. Classical time-series methods (ARIMA / SARIMA)

Highly interpretable and cheap to fit, but built for single-variable,
roughly-linear, stationary series — they cannot natively absorb the
**seven heterogeneous covariate families** (weather, IMD deprivation,
population, crime, elevation, day-type, special events) that are central to
both our prediction *and* our equity argument; that would require manual
feature engineering into a SARIMAX form, at which point you've built
something less capable than a tree ensemble for more effort. Published
figures bear this out on comparable problems:

| Study | Result |
|---|---|
| LRT Ampang Line ridership, SARIMA | MAPE ≈ 9.78% ([source](https://www.academia.edu/145841122/Forecasting_Daily_LRT_Ampang_Line_Ridership_Using_SARIMA_Model)) |
| Transjakarta BRT ridership | SARIMAX MAPE ≈ 33.3% vs. neural-net MAPE ≈ 8.5% ([source](https://library.acadlore.com/MITS/2026/5/1/MITS_05.01_03.pdf)) |

Classical time-series models were never a serious contender for this dataset
— not because they're "old", but because the problem we're solving is
fundamentally a multi-feature tabular one, not a single-series one.

## 2. Deep learning (LSTM / GNN / Transformers)

This is where the comparison gets genuinely interesting — and where we want
to be honest that the literature is **mixed**, not one-sided:

| Domain | Result |
|---|---|
| Transport energy forecasting | XGBoost R²=0.951 (test) vs. LSTM R²=0.201 ([MDPI](https://www.mdpi.com/1996-1073/18/7/1685)) |
| Bike-sharing demand | XGBoost RMSE 15.1/R²=0.734 vs. LSTM RMSE 16.1/R²=0.695 ([arXiv:2203.10961](https://arxiv.org/pdf/2203.10961)) |
| Traffic flow forecasting | **LSTM RMSE 3.45/R²=0.727 *beat* XGBoost RMSE 4.65/R²=0.626** ([arXiv:2510.23668](https://arxiv.org/pdf/2510.23668)) |
| Bike-sharing, graph-structured (GCN-UP) | GNN ≈ 5.7% lower RMSE than XGBoost, ≈ 7.8% lower than LSTM — explicitly *because* it exploits station-to-station graph structure ([arXiv:1712.04997](https://arxiv.org/pdf/1712.04997)) |

We're including the result that goes against us (traffic flow) deliberately:
it shows the real pattern is not "trees always win" but **"deep learning and
graph models pull ahead specifically when the prediction problem is
fundamentally about spatial structure across a network of interconnected
locations."** Our problem — predicting demand at 15 stops individually, each
driven primarily by *local* conditions (weather, time, deprivation, events) —
is not that kind of problem. If we were predicting how demand at one stop
*propagates* to its neighbours across the network, a GNN would likely be the
better tool, and we'd say so.

There's also a peer-reviewed structural reason this pattern holds at our
scale specifically: **Grinsztajn, Oyallon & Varoquaux (NeurIPS 2022)**
benchmarked tree ensembles against modern deep nets across 45 tabular
datasets and found tree-based models remain state-of-the-art on
medium-sized (~10K-row and up) heterogeneous tabular data — tracing this to
neural networks' inductive biases (smoothness, rotation-invariance) actively
working *against* them on data with mixed categorical/numerical, partially
uninformative features ([arXiv:2207.08815](https://arxiv.org/pdf/2207.08815)).
Our 263,160-row dataset, with its mix of weather codes, deprivation deciles,
population counts and binary term flags, sits squarely inside the regime that
paper describes — this isn't us picking a result that flatters our choice,
it's a direct application of a peer-reviewed finding to data of exactly the
shape and scale we have.

## 3. Other tree ensembles (Random Forest, LightGBM, CatBoost)

We're not pretending XGBoost is the *only* tree-based option that would have
worked — being honest about the runner-up makes the comparison credible:

- **Random Forest** is a strong, robust baseline, but boosting (iteratively
  correcting residual errors) typically edges it out on structured tabular
  benchmarks.
- **CatBoost** has genuinely *better* native handling of categorical features
  (ordered boosting) than XGBoost, which requires explicit encoding of our
  day-type/weather/event categories
  ([arXiv:1706.09516](https://arxiv.org/pdf/1706.09516)). This is a real,
  small disadvantage of our choice — we're naming it rather than hiding it.
- **LightGBM** trains fastest at scale via leaf-wise growth and sampling
  ([comparison summary](https://createbytes.com/insights/xgboost-lightgbm-catboost-gradient-boosting)).

XGBoost won on a different axis: **ecosystem maturity** — the largest
community, the most worked examples, the most mature SHAP/feature-importance
tooling, and the most predictable behaviour for a small student team that
needed to get this right on a fixed timeline without a dedicated MLOps
function. That's a legitimate engineering reason to choose a slightly less
"technically optimal" tool — and it's the honest one.

## 4. The deciding factor for *this* project specifically: explainability

This is, in our view, the strongest reason XGBoost was right for *this*
project rather than just "a good model in general": the project's central
ethical commitment (see [`MODEL_CARD.md` — Ethical
considerations](../MODEL_CARD.md#ethical-considerations)) is that predicted
demand directly drives which neighbourhoods get more bus service — an
under- or over-prediction has a real equity consequence. XGBoost ships with
mature, standard tools (built-in feature importances, SHAP decomposition)
that let us show **exactly which factor** — IMD decile, weather, time of day,
school-term status — is driving a high-demand prediction at a specific stop.
A deep net would make that conversation with the Ladywood community
dramatically harder to have honestly. For a project whose entire premise is
*"we will not let an opaque algorithm decide who gets a bus,"* the
interpretability of the model is not a nice-to-have — it's the same kind of
non-negotiable as the [equity check](../../analysis/equity.py) we already run
on the optimiser's output.

## Summary

We didn't choose XGBoost because it's fashionable, and the literature above
shows it isn't even universally the most *accurate* option — deep
spatio-temporal models beat it when the problem is graph-structured, which
ours isn't. We chose it because, for a ~263K-row heterogeneous tabular
dataset (the regime where peer-reviewed benchmarks show trees genuinely
dominate), with a hard requirement to *explain* every prediction to the
community it affects, and a small team with a fixed deadline and no
dedicated ML infrastructure — it was the model that let us be both accurate
**and** accountable. That combination, not raw leaderboard performance, is
what this project actually needed.
