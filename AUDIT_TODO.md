# UK2026-82 Grand Finals — Master Audit & Task List

**Finals: Friday 19 June 2026**
**Deck freeze: Wednesday 17 June (morning)**
**Dry-run target: Tuesday 17 June**
**Last updated: Monday 16 June — full repo re-scan after Chris's hardware commit (23d1ce9)**

---

## WHAT CHRIS SHIPPED (hardware commit 23d1ce9, Mon 16 Jun)

All of the following are now live in the repo under `hardware/`:

| File | Status |
|------|--------|
| `hardware/fpga/uart_rx.sv` | Done — correct 2-FF synchroniser + 9600-baud FSM |
| `hardware/fpga/frame_rx.sv` | Done — 0xAA sync, 15-byte double-buffer, XOR checksum |
| `hardware/fpga/uart_tx.sv` | Done — bonus addition |
| `hardware/fpga/latencyZeroFPGA.sv` | Done — top-level with SW9 mux |
| `hardware/raspberry_pi/hub.py` | Done — Pi bridge (see critical note below) |
| `hardware/raspberry_pi/README.md` | Done |
| `hardware/raspberry_pi/SETUP_GUIDE.txt` | Done |
| `hardware/arduino/stop_unit/stop_unit.ino` | Done |
| `docs/radio_signalling_report.md §6 Security` | Done — AES-128-CMAC, replay counter, fail-dark |
| `fpga/README.md` WS2812B outdoors paragraph | Done |
| `docs/design/RUNNING_COSTS.md` maintenance line | Done — £30-50/unit/yr |

---

## WHAT IS CONFIRMED DONE (across both team members)

| Item | Notes |
|------|-------|
| `docs/REFLECTIONS.md` | Fully personalised, all three sections, no DRAFT banner |
| `docs/ASSUMPTION_LOG.md` | 16 assumptions (expanded from 11), all with status/evidence |
| `docs/UNINTENDED_CONSEQUENCES.md` | Complete — covers community, environment, economy |
| `docs/DRIVER_INTERFACE.md` | Complete — incl. Transport Act 1985 compliance pathway |
| `docs/DEMOGRAPHIC_DESIGN_MAP.md` | Complete — 8-row table with real population sources |
| `docs/EMISSIONS_QUANTIFICATION.md` | Complete — 1.95-2.54 t CO2e/yr quantified |
| `docs/EFFECT_SIZE_TRANSLATION.md` | N filled in — 116 route-stop assignments/weekday, ~0.5 extra allocations/day |
| `docs/radio_signalling_report.md §6` | Security section present and complete |
| `docs/design/RUNNING_COSTS.md` | WS2812B maintenance line present |
| XGBoost retrain | Crime feature removed, R² = 0.9421, 263K real-anchored rows |
| `analysis/weekend_curve/` | Empirical weekend curve committed (3 files) |
| Dashboard: scrollable stop panel | Done |
| Dashboard: compact controls | Done |
| Dashboard: POI dash + metric glossary | Done |
| `dashboard/demand.py` pkl guard | Done — existence pre-check before load |
| UART/frame RX hardware | Done — uart_rx.sv, frame_rx.sv correct and clean |

---

## OPEN — ARYA (all small, finals this week)

| ID | Priority | Item |
|----|----------|------|
| SK5 | STAGE-KILLER | **BODS dwell ATCO mapping — Wed 17 morning.** Run `tools/bods_avl/derive_dwell_times.py` on the pilot-week data. Confirm the ATCO codes in `stop_ranking_observed.json` map correctly to S10 (Ladywood Fire Station) and S12 (Summerfield Park) outranking S07 (Five Ways). If the mapping cannot be confirmed, remove the on-stage dwell claim before the deck freezes. |
| QW3 | High | **File TfWM APC FOI — today.** Email foi@tfwm.org.uk. Use Wellington FOI 14028 as template. Once sent, update `docs/MODEL_CARD.md`: change "pathway identified; foi@tfwm.org.uk" to "FOI filed [date]". This turns a Q&A weakness into a strength on stage. |
| BUG-A1 | Medium | **`dashboard/web/index.html` title is still "web".** Change `<title>web</title>` to `<title>Ladywood Predictive Bus Routing</title>`. One line. |
| MT3 | Low | **Deck slide 18 CO2 number** — verify it reads "~2–2.5 t" not "2.4–3.1 tCO2e". The cost model computes 1.95–2.54 t on the 300-day basis. |
| MT5 | All team | **End-to-end dry-run — Tue 17 (Jack owns logistics).** Dashboard at :8000 + Living Twin UART path or replay fallback + deck in order + spoken answers timed. Nothing first-attempted on stage. |

---

## OPEN — CHRIS (two critical checks, one build gap)

### Critical 1 — verify SW9 actually routes live_regs to the display

**`hardware/fpga/latencyZeroFPGA.sv` SW9 semantic needs verification.**

The scrape found SW9 controls auto-cycling of scenario/timeslot (`eff_sc = SW[9] ? auto_sc : SW[1:0]`). Build spec says SW9 should mux between ROM snapshot and live `stop_regs` from `frame_rx`. These are different behaviours. Before the bench test, confirm that `stop_regs` from `frame_rx` actually feed the display colour logic — not just echo back out via `uart_tx`. If `stop_regs` bypass the colour ROM entirely, the live-data path is unconnected on screen even though the UART plumbing is correct.

### Critical 2 — hub.py is a simulation hub, not a BODS poller

**`hardware/raspberry_pi/hub.py` does not poll BODS.**

The committed hub.py is a bidirectional ROM-matching loop: it reads 0xBB demand frames back from the FPGA, matches them to identify the active scenario/timeslot, and repositions bus objects locally. It does not call the BODS SIRI-VM feed, does not haversine-snap real vehicle positions, and does not send real-bus-position 0xAA frames. The "Living Twin" as committed shows the ROM animation with UART echo, not real buses from the live feed.

**Decision for Chris before Tue dry-run:**
- If the demo plan is "UART-bridged ROM animation with UDP broadcast to Arduino" — the committed hub.py is correct and the demo is coherent. Relabel it honestly on stage: "live UART bridge between Pi and FPGA — real BODS integration is the next phase."
- If the demo plan requires showing a real bus on Dudley Road move the LED — hub.py needs the BODS poll + haversine snap added before Mon night.

Either way, the UART architecture is sound. This is a scoping question, not a bug.

### Remaining build items

| ID | Status | Item |
|----|--------|------|
| LT3 | Open | **Replay mode** (`hub.py --replay <file>`) not present. If the demo relies on a pre-recorded fallback, add `--replay` argument to hub.py before dry-run. |
| LT5 | Open | **Bench acceptance test** — hardware test, not a repo artefact. Run the full sequence: Pi → UART → FPGA → LEDs update; pull wire → amber pulse after staleness timeout; SW9 down → ROM. All three must work before Fri. |
| LT6 | Open | **Replay file not committed.** Record a BODS (or simulated) snapshot file and commit to `tools/bods_avl/replay/ladywood_<date>.jsonl` for on-stage fallback. |
| HW3 | Open | **HDL testbench `fpga/tb_bus_route.v` still missing.** If you verified on-hardware by inspection, add one paragraph to `fpga/README.md` explicitly stating this: "Verified on DE1-SoC by visual inspection of WS2812B output — no simulation testbench committed; this is a known gap for Phase 2." This pre-empts the judge question without claiming something that isn't there. |

---

## OPEN — JACK

| ID | Item |
|----|------|
| MT4 | **route_plan.json sanity check** — verify every stop is served or in the unserved list, capacities respected, no broken geometry. Sign off before Tue dry-run. |
| J3 | **Living Twin integration test (today Mon 16)** — help Chris confirm Pi → FPGA path works: LEDs update, pull-wire amber, SW9 ROM fallback. This is the on-stage moment; rehearse it. |
| J4 | **Demo dry-run owner (Tue/Wed)** — run the full flow end-to-end with timing. Nothing first-attempted on stage. |

---

## SPOKEN Q&A — DRILL BEFORE FRI (all team)

| ID | Status | Answer brief |
|----|--------|--------------|
| RH1 | [ ] | **"R² is circular — you trained on synthetic data."** Concede; reframe R² as pipeline capability, not forecast accuracy. Anchor chain: BUSTO shape r=0.945 → smartcard absolute levels → real Open-Meteo weather → weekend divergence we caught and corrected → FOI filed [date]. Script in `beast/hardening/CIRCULARITY_REBUTTAL.md`. |
| RH2 | [ ] | **"Worst-case optimality gap?"** 30.2% on one route. Mean 1.16% — but deflated because brute-force optimal only computed for routes ≤8 stops; harder routes compare to themselves. Honest framing: greedy+2-opt is a practical heuristic, not an exact solver. |
| RH3 | [ ] | **"Why not APC data?"** Not publicly available in UK. TfWM APC is proprietary ETM. FOI filed [date]. Wellington NZ Metlink used for hour-of-day shape validation: r=0.945 on comparable tier stops. |
| RH4 | [ ] | **"Your display can be spoofed."** AES-128-CMAC on every LoRa packet. Monotonic frame counter drops replays. Fail-dark on bad MAC or stale counter — blank display is honest, a lying one is not. People who most depend on it are least able to catch a lie. |
| RH5 | [ ] | **"BODS is down on the day?"** Replay fallback: pre-recorded snapshot at 60x. FPGA staleness watchdog fires after 60 s → amber pulse. Dashboard always shows route_plan.json predictions regardless. |
| RH6 | [ ] | **"Driver hours fall but drivers are stakeholders — you're cutting jobs."** Saving is fuel and dead-mileage on same duties, not headcount. Driver count unchanged; optimisation eliminates unnecessary dead kilometres. Full reconciliation in `docs/DRIVER_INTERFACE.md §3`. |
| RH7 | [ ] | **"This is illegal — Transport Act 1985 s.6."** Correct. Three-phase lawful pathway: within-registration flexibility → s.22 flexible registration → WMCA franchising. Full answer in `docs/DRIVER_INTERFACE.md`. |
| RH8 | [ ] | **"Latent demand — people who stopped using the bus?"** Named in ASSUMPTION_LOG as A5. Model predicts observed demand, not potential. Suppressed demand is invisible. Phase 2 requires survey data. Bounded as out of scope, not ignored. |
| RH9 | [ ] | **"Crime feature — redlining?"** Tested: permutation importance 0.000279, rank 16/20. R² improved after removal. Deleted on principle. See `analysis/crime_ablation/`. |

---

## TRACKER HOUSEKEEPING (update AUDIT_TODO.md in repo)

These items are done in the repo but still marked open in AUDIT_TODO.md — check them off:

- HP1: `radio_signalling_report.md §6` — DONE
- LT1: `uart_rx.sv`, `frame_rx.sv`, SW9 mux — DONE (`hardware/fpga/`)
- LT2: `hub.py` — DONE (`hardware/raspberry_pi/`) with the caveat above
- LT7: WS2812B outdoors paragraph + RUNNING_COSTS.md line — DONE
- MT2: Dashboard commits (scrollable panel, compact controls, POI, glossary) — DONE (code confirmed)
- SK4: REFLECTIONS.md DRAFT banner — DONE

---

## POST-FINALS BACKLOG (do not touch before Fri)

- Add BODS live polling to `hub.py` (haversine snap, real 0xAA frames)
- Fix FPGA timing closure: latch `cur_color` once per LED (−11.24 ns setup slack)
- Write `gen_rom.py` to auto-generate Verilog ROM tables from route_plan.json
- Wire pytest into CI (ci.yml currently runs compileall only)
- Hyperparameter search for XGBoost (all params currently manual)
- SHAP values in `analysis/explainability.py`
- Fix `is_uni_term = is_term` with a real university calendar
- Fix `is_uni_term` toggle missing in ConditionsPanel
