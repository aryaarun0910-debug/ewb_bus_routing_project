# Driver & Operator Interface — How a Route Update Actually Reaches the Cab

> Reviewer ask (verbatim): *"Driver/operator interface — how does a bus driver receive a live route update?"*
> Rubric target: Criterion 2b (implementation + predicted difficulties). This document answers the operational question and names the regulatory difficulty most student teams miss.

## Design principle: updates at the terminus, never mid-route

Dynamic routing does **not** mean a bus diverts while passengers are aboard. The system's cadence is the optimiser's cadence: 8 time windows per day, pre-solved per scenario. A driver's route is fixed for the duration of a window and can only change at a **terminus turnaround**, when the bus is empty. This is a safety, passenger-trust and workload decision before it is a technical one — no passenger ever boards a bus whose destination changes after boarding, and no driver re-plans while driving.

## The three-layer interface

| Layer | What the driver sees | Hardware | Cost |
|---|---|---|---|
| **1 · Pre-shift route card** | Today's scenario (from the day-ahead forecast) and the per-window route sheet, printed or on the depot screen alongside existing duty boards | Existing depot infrastructure | £0 |
| **2 · In-cab window card** | An e-paper display (same family as supermarket shelf labels) on the dash: current window's stop sequence, next-window preview 10 min before turnaround, single ✓/✗ acknowledge button | E-paper module + LoRa receiver — the *same* receiver stack as the stop displays (`docs/radio_signalling_report.md`), one more node on the same 433 MHz broadcast | ~£25/cab |
| **3 · Control-room view** | TfWM/operator control sees the active `route_plan.json` window on the dashboard's existing scenario view; dispatcher approves any scenario switch (storm-day plan ⇄ normal plan) — the system *recommends*, a human *dispatches* | Existing dashboard (`dashboard/web`), zero new code paths — it already renders every scenario/window | £0 |

One artefact drives all three: the same `route_plan.json` that drives the public LED maps. The driver, the dispatcher and the passenger at the stop are looking at the same plan by construction — no version skew between what the cab knows and what the stop displays.

## Driver standing in the governance loop

Drivers are not interface end-points; they are sensors and stakeholders. Governance Phase 3 (`docs/design/STAKEHOLDER_ENGAGEMENT.md`) already gives drivers the standing right to **trigger a cadence review** — if window-to-window changes are too frequent to operate comfortably, the review reduces the cadence. Pilot onboarding includes paid driver consultation sessions; National Express WM 2024 pay scale is already the cost model's labour basis.

## The predicted difficulty no one likes to name: service registration law

UK local bus services must be **registered with the Traffic Commissioner with a fixed timetable** (Transport Act 1985, s.6); deviating from the registered timetable is an offence. Fully dynamic routing therefore cannot be deployed on a registered fixed service as-is. Three lawful pathways, in increasing order of flexibility:

1. **Within-registration optimisation (pilot phase).** Keep the registered timetable; use the system to choose *which* of the registered journey patterns runs in each window where the registration already permits variation, and to optimise dead-running and duty allocation. Zero regulatory change; captures most of the fuel/dead-mileage saving.
2. **Section 22 community bus / flexible service registration.** Registered *flexible services* (the legal instrument behind DRT) explicitly permit demand-responsive routing within a defined zone. CIVIC SQUARE-stewarded operation fits the community-transport pathway naturally.
3. **Franchising (the WMCA trajectory).** The West Midlands is moving toward bus franchising powers (Bus Services Act 2017 / 2024 extension); a franchising authority can specify dynamic service patterns directly. This is the long-term channel and the reason WMCA/TfWM handoff is the named end-state in the sustainability plan.

Naming this constraint is the point: the implementation plan phases deployment so that **phase 1 is legal today**, phase 2 uses an existing legal instrument, and phase 3 rides a policy change already in motion — rather than pretending the law away.
