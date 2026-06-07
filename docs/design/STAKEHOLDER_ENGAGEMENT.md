# Stakeholder Engagement & Co-Design

How the community and other stakeholders could actively shape this system —
not just receive it. An equity-monitoring dashboard is a welcome gesture, but
it falls short of its potential if the community it protects isn't centred in
defining what it measures and how the system behaves. This document makes
participation concrete.

## Principle

Residents are **co-designers and governors**, not data points. Ladywood
already has the civic infrastructure for this — CIVIC SQUARE's Neighbourhood
Public Square, the Floating Front Room, Neighbourhood Network Schemes — so
engagement plugs into existing, trusted spaces rather than inventing new ones.

> **Note on ethics**: per the Design Challenge rules, we did **not** contact
> Ladywood residents directly. Everything below is a *designed* participation
> plan, intended to be run by CIVIC SQUARE / the local authority — not
> something we conducted ourselves.

## Who, and what power they hold

| Stakeholder | Role in the system | Real decision power |
|---|---|---|
| Residents (riders, incl. elderly, shift workers) | Define which stops/journeys matter | Set the equity rules the optimiser must respect |
| Bus drivers / union | Operate re-allocated routes | Veto unsafe change cadences; approve the route-variant set |
| Operator (National Express West Midlands) | Run the service, see load-factor gains | Commit vehicles; fund running cost (see [Running Costs](RUNNING_COSTS.md)) |
| WMCA / Birmingham City Council | Fund, align with transport plan | Capital + air-quality funding; data sharing |
| CIVIC SQUARE | Steward, convene, maintain | Host hardware, run workshops, hold the map in trust |

## Participation across the phases

**Phase 1 — Define (co-design workshops).**
Run at the Neighbourhood Public Square: residents mark on a map the stops and
times that matter to *them* — school runs, shift starts, health appointments.
These become explicit **equity constraints** fed into the optimiser — e.g.
"the Health Centre stop is always served mid-morning," encoded as a hard
constraint in `demand_route_optimizer.py` rather than left to the demand
prediction alone (which, per the [Model Card](../MODEL_CARD.md), is anchored
to real data but still has a modelled temporal shape — exactly the kind of gap
that lived local knowledge can directly correct).

**Phase 2 — Monitor (participatory, not top-down).**
The equity dashboard ([`analysis/equity.py`](../../analysis/equity.py),
surfaced in the web dashboard's IMD overlay) is co-owned: residents agree
which metrics it tracks (e.g. worst-served stop, elderly-stop coverage,
early-shift reliability) and review them at a regular rhythm — mirroring the
existing Neighbourhood Supper Club cadence. The dashboard reports *to* the
community, and the community can change what it measures, not just view it.

**Phase 3 — Govern (stewardship).**
Legal/operational stewardship of the physical FPGA LED map and its routing
rules sits with a neighbourhood body — the CIVIC SQUARE model of assets "held
by the neighbourhood in perpetuity." Residents can trigger a review of routing
rules; drivers can trigger a review of change cadence (see
[User Journeys → Dan](USER_JOURNEYS.md#3--dan--bus-driver-receiving-a-live-updated-route)).

## Feedback loops (post-deployment)

- **At the stop**: a simple "was your bus useful today?" tap/QR code at the
  LED map, plus an analogue option (a marble jar / tally box) for residents
  without a smartphone — consistent with the [User Journeys](USER_JOURNEYS.md)
  finding that a meaningful share of the ward has no reliable internet access.
- **Quarterly review**: realised coverage vs. resident-defined equity rules,
  presented at an existing community gathering, using the same
  `analysis/equity.py` allocation-mismatch metric reported in the
  [README](../../README.md#equity).
- **Change log**: every routing-rule change published in plain language, so
  residents see cause → effect rather than a black box.

## What this changes about the design

Engagement is not a wrapper around a finished system — it **edits the
optimiser**. Resident-defined equity constraints and agreed monitoring metrics
become inputs to the routing logic, which is consistent with why the
capacity-aware optimiser already refuses to abandon medium/low-demand
residential stops in favour of chasing the single busiest hub (see
`MIN_DEMAND_VISIT` and `BUS_CAPACITY` in
[`demand_route_optimizer.py`](../../prediction%20model/demand_route_optimizer.py)).
Co-design would extend that principle from "encoded by the project team" to
"defined by the people the routes serve."
