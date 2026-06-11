# Failure Modes, Safe Defaults & the Service Floor

**Where this goes:** a new section in `docs/ARCHITECTURE.md` ("Failure modes and safe
defaults") plus a short constraint note in the optimiser docs. This closes three of the
four Tier-1 stage-killers from the Achilles audit: the stranded-passenger attack, the
no-degradation-story gap, and the point-prediction-without-uncertainty worry.

The governing principle, stated once and then everywhere: **the system can only ever
degrade to the status quo. Its worst failure mode is "today."** That sentence is your
shield. Today, Ladywood has a static timetable and a dark bus stop. If our model server
dies, the LoRa hub loses power, or `route_plan.json` corrupts, the passenger sees exactly
that — a static timetable and a dark stop. Never *worse* than the baseline we're improving.

---

## 1. The stranded-passenger problem (the equity attack on an equity project)

**The attack:** "You reroute buses toward predicted demand. A pensioner waits at a stop
your model deprioritised. The prediction was wrong. She waits an hour in the rain. Dynamic
routing punishes exactly the people who can't check a dashboard."

This is the dark mirror of your own best argument, and the rubric's "unintended
consequences" cells invite the judge to go looking for it. You need **two** structural
defences on record, not rhetoric:

### 1a. Terminus-only rerouting → mid-route passengers are never abandoned
Route changes are applied **only at the terminus**, between journeys — never mid-trip.
A bus that has started a journey completes it as planned. Nobody already waiting on a
committed route is stranded by a re-optimisation. (This is also why the driver interface
is feasible — see `DRIVER_INTERFACE.md`.)

### 1b. A minimum-service floor as a hard constraint in the optimiser
Add an explicit constraint: **every stop is visited at least once every `T_max` minutes,
regardless of predicted demand.** The optimiser is allowed to *add* service where demand
is predicted, but never to drop a stop below the floor. In CVRP terms this is a maximum
inter-visit-interval constraint per stop — one line in the problem formulation, and it
converts "dynamic routing might abandon a quiet stop" into "dynamic routing tops up busy
stops above a guaranteed baseline."

> **Repo action:** state the floor explicitly in the optimiser docs and, if feasible,
> encode it in `demand_route_optimizer.py` as a documented constraint (even as a
> post-hoc feasibility check that rejects any plan violating the floor). A judge asking
> "what's your minimum service guarantee?" should get a number, not a philosophy.

**Spoken answer:** "Two things stop that. First, we only ever change routes at the
terminus, so no one mid-journey is ever stranded. Second, the optimiser has a hard service
floor — every stop is guaranteed a bus at least every T minutes whatever the prediction
says. We don't *remove* service from quiet stops; we *add* it to busy ones, on top of a
floor nobody falls below. The prediction can only make things better than the guarantee,
never worse."

---

## 2. Graceful degradation — the full failure-mode table

| Component fails | What the passenger sees | Why it's safe |
|---|---|---|
| ML model / prediction server down | Static timetable routing (last known good `route_plan.json`, or the published timetable) | Degrades to status quo — never worse than today |
| LoRa hub loses power | Stop display shows "no live data" pattern; buses run last-pushed plan | Display is honest about being offline; service continues on last plan |
| `route_plan.json` corrupt / missing | System refuses the bad plan, falls back to published timetable | Fail-closed: a corrupt plan is never executed |
| Stop unit (solar/battery) dies | That one display dark; buses unaffected | Single-unit failure is isolated; no network effect |
| Forecast wildly wrong (OOD weather/event) | Service floor still guarantees baseline; CQR interval (when implemented) flags low confidence | Bounded blast radius: one terminus cycle, floored |
| Spoofed LoRa packet | Rejected by AES-MAC + counter; "no data" fallback | See `FPGA_HARDENING.md` §1 |

**The one-liner for ARCHITECTURE.md:** "Every failure path in this system terminates in the
status quo — a static timetable and the published schedule. The system is designed so its
worst day is an ordinary day on the current network."

---

## 3. Point predictions without uncertainty (CQR is promised, not built)

`MODEL_CARD.md` lists Conformalised Quantile Regression as next-step #1 but it isn't
implemented. The honest framing that defuses "you route real buses on point predictions
with no confidence intervals?":

- **The cadence bounds the cost of being wrong.** Because updates are terminus-only and per
  time-window, a single wrong prediction costs at most one cycle before the next
  re-optimisation corrects it — not cascading chaos.
- **The service floor bounds the downside.** Even a confidently-wrong prediction can't push
  any stop below the guaranteed baseline (§1b).
- **CQR is the named, scoped next step**, not hand-waving: it produces per-prediction
  intervals; low-confidence (wide-interval) predictions would defer to the floor + last
  known good plan rather than acting aggressively. Honest disclosure of a planned mitigation,
  with the interim safety argument, beats silence.

---

## 4. Static travel times / no congestion model (disclose, don't hide)

The CVRP edge costs are static — they don't model within-window congestion, which is
ironic for a Birmingham-traffic project. The honest answer:

- Route plans are **recomputed per time-window** (peak vs off-peak differ structurally), so
  congestion *is* captured at the coarse band level even though it isn't modelled
  continuously.
- Live within-window congestion is a **named Phase-2 input**: BODS live vehicle feeds (already
  snapshotted in `data/bods/`) are the data source for dynamic edge costs.
- State it as a bounded limitation in the assumption log, not an undisclosed gap.

---

## 5. Driver-hours / legal duty constraints not in the optimiser (disclose)

EU/UK drivers'-hours and break rules are hard constraints on real duties; the CVRP doesn't
encode them. The defence is genuinely strong but currently lives nobody-knows-where:

- The optimised routes are **shorter than the duties they replace** — that shortening *is*
  the fuel/dead-mileage saving (NOT a headcount or pay cut; see `UNINTENDED_CONSEQUENCES.md`).
  So existing, already-legal duty cards still envelope the optimised routes.
- Encoding drivers'-hours explicitly is a named next step for the franchised/at-scale phase.
- One sentence in the assumption log closes it.

---

## Repo action summary (each = one commit)

1. New "Failure modes and safe defaults" section + the table → `ARCHITECTURE.md`.
2. Service-floor constraint stated in optimiser docs (and ideally a feasibility check in `demand_route_optimizer.py`).
3. CQR interim-safety paragraph → `MODEL_CARD.md`.
4. Static-travel-time + driver-hours limitations → assumption log (see `ASSUMPTION_LOG_ADDITIONS.md`).
