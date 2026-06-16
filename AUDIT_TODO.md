# Grand Finals Audit — Fix Tracker

Audited: 2026-06-16 (5 agents, full repo scan).  
Deck freeze: **Wed 17 Jun**. Grand Finals: **Fri 19 Jun**.  
Claude updates this file each session — check off items as they land.

---

## STAGE-KILLERS (block the presentation if not fixed)

- [x] **SK1** — `crime_total_2024` removed from `docs/ARCHITECTURE.md` Layer 2, `README.md` From-Synthetic table and Data Sources table, and `README.md` Caveats paragraph. Parenthetical ablation note added in each place.

- [x] **SK2** — `docs/MODEL_CARD.md` line 79 changed to "pathway identified — foi@tfwm.org.uk." `docs/ASSUMPTION_LOG.md` A13 changed to "pathway identified — not yet filed."

- [x] **SK3** — `docs/MODEL_CARD.md` updated to "median Pearson 0.38 across 15 weekday stops (range −0.04 to 0.66; outliers S05/S14 at r≈0.06 explained)." `docs/ASSUMPTION_LOG.md` A1 updated to match and now includes BUSTO positive evidence (r=0.945/0.942). `docs/REFLECTIONS.md` Arya's narrative clarified: 0.06 is the S05 outlier she noticed, not the overall median.

- [x] **SK4** — `docs/REFLECTIONS.md` draft-caveat blockquote (lines 1–9 of old header block) deleted. File now opens directly with the first section header.

- [ ] **SK5** — BODS dwell claim not verified from committed data. `VALIDATION_LADDER.md` stage script says "Ladywood Fire Station and Summerfield Park showing higher observed dwell than Five Ways Station." `beast/beyond/bods_avl/stop_ranking_observed.json` is keyed by raw ATCO codes, not S01–S15. Nobody has confirmed the mapping. Fix: run ATCO→stop lookup, verify S10/S12 actually outrank S07, add verified stop names to VALIDATION_LADDER.md rung 7. Arya owns this — Wed 17 morning.

- [x] **SK6** — `VALIDATION_LADDER.md` on-stage script changed from "124,000 clean observations" to "Around 82,000 observations a day."

---

## CODE BLOCKERS (analysis scripts, not in live demo path — still fix)

- [x] **CB1** — `analysis/explainability.py`: `_DATA_DIR` and `_MODEL_PKL` paths fixed to `"prediction model" / "demand_model.pkl"` and `"prediction model" / "map_demand_dataset.csv"`.

- [x] **CB2** — `analysis/gtfs_validate.py` line 99: path fixed to `"prediction model" / "map_demand_dataset.csv"`. Error message updated to match.

---

## HIGH PRIORITY (before Wed 17 freeze)

- [ ] **HP1** — `radio_signalling_report.md` has no §6 Security section. `tools/living_twin/FPGA_HARDENING.md` §1 flags this as "CURRENTLY UNADDRESSED — highest priority." Content exists in FPGA_HARDENING.md (AES-128-CMAC + monotonic counter + fail-safe blank on bad packet). Chris owns this (~30 min). Must be in the public repo before deck freeze.

- [ ] **HP2** — `docs/EFFECT_SIZE_TRANSLATION.md`: the `[ ]` TODO action "Compute visits_per_day from route_plan.json, fill N in" is still open. The "N extra bus arrivals/day at the hospital corridor" number is missing from the doc and the deck. Arya owns this (~15 min one-liner on route_plan.json).

- [x] **HP3** — `docs/FAILURE_MODES_AND_SERVICE_FLOOR.md` §4: broken `ASSUMPTION_LOG_ADDITIONS.md` reference replaced with "(see A15, A16 in `docs/ASSUMPTION_LOG.md`)".

- [x] **HP4** — `docs/ASSUMPTION_LOG.md` A1 Evidence column: BUSTO positive evidence (r=0.945/0.942 for major/medium) added alongside the GTFS median (now corrected to 0.38).

- [x] **HP5** — `docs/MODEL_CARD.md`: `stop_importance_enc` reworded to "highest-importance design variable (0.735) — behind only the temporal index `hour` (0.946)". `data/osm/ladywood_stop_pois.json` `__note__` updated to match.

---

## QUICK WINS (~30 min total)

- [ ] **QW1** — `tools/living_twin/EVERYONE_TASKS.md` references `beast/hardening/CIRCULARITY_REBUTTAL.md` (local only, not in repo). Note the path is local; inline the key bullet points or commit the file to the repo.

- [x] **QW2** — `analysis/cost_model.py` line 64: comment changed to "passengers per vehicle (single-decker capacity)" — removed false claim of matching the optimizer's 320 window budget.

- [ ] **QW3** — File the TfWM APC data request (foi@tfwm.org.uk, Wellington FOI 14028 as template). Once filed, update SK2/ASSUMPTION_LOG.md A13/MODEL_CARD.md to say "filed." 10 minutes. Target: Wed 17 before deck freeze so "filed" is literally true on Fri 19.

---

## LIVING TWIN — Chris owns these (Mon 16 → Tue 17)

- [ ] **LT1** — `fpga/uart_rx.sv` + `fpga/frame_rx.sv` + SW9 mux do not exist in the repo. Must be written. Spec: 9600-8-N-1 at 50 MHz (divider 5208); byte FSM wait `0xAA` → 15 bytes → XOR verify → double-buffer latch; SW9 mux live_regs vs rom_row. Resolve SW9 semantic conflict with existing demo-cycle logic in `fpga/bus_route.v` line 51. Staleness watchdog: no valid frame for 60 s → amber "no data" pulse.

- [ ] **LT2** — `hub.py` (Pi side) does not exist in the repo. Must be written and committed. Reads `prediction model/route_plan.json` (demand nibble) + snaps BODS positions to `data/gtfs/ladywood_stops.json` (haversine). Sends 17-byte UART frame every 5 s (byte 0: 0xAA; bytes 1–15: [high nibble = vehicles at stop 0–9, low nibble = demand tier 0–3]; byte 16: XOR checksum).

- [ ] **LT3** — Implement replay mode in `hub.py` (`--replay <file>` at 60× speed, same UART output). Not optional — this is the on-stage fallback if BODS/hotspot drops.

- [ ] **LT4** — Register BODS key in `.bods_key` (gitignored) on the Pi before running `hub.py`.

- [ ] **LT5** — Bench acceptance test (Mon 16 tonight): real bus move S06→S07 lights correctly; pull wire → amber pulse after 60 s; SW9 down → ROM snapshot demo. Chris + Jack integration test.

- [ ] **LT6** — Record a replay file from live Tuesday data; commit it (or note path). On-stage label: "recorded Tuesday 17 Jun — replay mode, honest label."

- [ ] **LT7** — WS2812B outdoors suitability paragraph → `fpga/README.md`; maintenance cost line → `docs/design/RUNNING_COSTS.md`. (Chris §5 in EVERYONE_TASKS, not yet in tracker.)

> **ROM snapshot**: does NOT need regeneration. Stop importance tiers (major/medium/minor in `dashboard/ladywood_display.py`) did not change during the retrain — the ROM encodes colour tiers, not raw demand numbers. Raw demand numbers changed (weekend retrain) but those are read dynamically by `hub.py` from `route_plan.json`, not baked into the FPGA ROM.
> **demand_model.pkl**: Pi does NOT load the pkl at runtime for the Living Twin — it reads the pre-computed `route_plan.json`. The pkl change is irrelevant to Chris's hardware.
> **ladywood_stop_pois.json `__note__`**: hub.py does not read this file. No action.

---

## MISSING FROM TRACKER (surfaced in second audit pass)

- [ ] **MT1** — `README.md` docs index: add a link to `docs/REFLECTIONS.md` once SK4 (banner delete) is confirmed. (EVERYONE_TASKS shared item.)

- [ ] **MT2** — Dashboard commits push: day-lit map, compact controls, scrollable stop panel, metric-scale definitions, POI dash. (Arya §2 in EVERYONE_TASKS — not tracked here.)

- [ ] **MT3** — Deck slide 18 CO₂ number: change "2.4–3.1 tCO₂e" to "~2–2.5 t" (model output is 1.95–2.54 tCO₂e/yr). `docs/EMISSIONS_QUANTIFICATION.md` is already correct; deck sync needed. (Arya §5 in EVERYONE_TASKS.)

- [ ] **MT4** — Jack: sanity-check `prediction model/route_plan.json` after retrain: every stop served or in unserved list, capacities respected, no broken geometry. (Jack §2 in EVERYONE_TASKS.)

- [ ] **MT5** — Jack + full team: end-to-end dry-run (dashboard + Living Twin + deck + replay-mode fallback). Target Tue 17. (Jack §4 in EVERYONE_TASKS.)

- [ ] **MT6** — Dashboard crime tooltip in `StopPanel.tsx`: current text says "Used cautiously (see the crime-feature ablation)" — add "displayed as context only; excluded from the routing model" to close the live-demo attack vector. (See RH5.)

---

## REHEARSAL (no code change needed — spoken answers)

- [ ] **RH1** — README honestly reports 30.2% worst-case optimality gap. Prepare 10-second answer: "1.16% mean gap is the deployment metric; 30.2% is the worst-case upper bound on any single route in the largest scenario — the system average is what drives fuel savings."

- [ ] **RH2** — FPGA timing not closed (−11.24 ns setup slack in fpga/README.md). Chris answer: "It works on the bench — the WS2812B timing is observed correct. Retiming the `cur_color` chain is the documented next step. Bench test is the proof."

- [ ] **RH3** — Jack must answer the *current* Pi→FPGA UART single-point-of-failure question, not the legacy Unity serial bridge. Answer: "SW9 down is always the fallback — the ROM snapshot we already trust. If BODS drops on stage, we have a replay file of real Tuesday data, honestly labelled. We designed for this failure on purpose."

- [ ] **RH4** — Latent demand attack ("if night buses are unreliable, your model can't see the suppressed demand"). Point to ASSUMPTION_LOG.md A5 (no induced-demand feedback loop — named, bounded, out of scope for Phase 1).

- [ ] **RH5** — Dashboard crime tooltip: confirm the crime data in the UI explicitly says "displayed as context only — does not influence routing." Prevents a live demo attack on SK1.

- [ ] **RH6** — CIRCULARITY_REBUTTAL script: if it still cites r=0.945 anywhere, update to R²=0.9421 (the post-retrain figure) so what you say on stage matches the deck exactly.

---

## COMPLETED

- [x] Fix #1–#15 (LSOA rederivation, service floor, model retrain, equity, BODS pipeline, accessibility, crime ablation, weekend curve, ASSUMPTION_LOG, CRIME_ABLATION, SHAPE_VALIDATION, MODEL_COMPARISON, SCALABILITY, EFFECT_SIZE_TRANSLATION scaffolding)
- [x] Fix #16 — `tools/living_twin/EVERYONE_TASKS.md` + `BUILD_SPEC.md`: stale metric corrected (R² 0.9418→0.9421); FPGA = "display/edge device" not "solver"
- [x] Fix #17 — `data/osm/ladywood_stop_pois.json`: `__note__` key added; `docs/MODEL_CARD.md`: stop_importance row added distinguishing operational tier from derived_tier
- [x] BODS field-name bug — `tools/bods_avl/derive_dwell_times.py`: `s["id"]`→`s.get("id") or s["stop_id"]`, `s["lon"]`→`s.get("lon") or s["lng"]` (both repo copy and live beast copy)
- [x] `docs/VALIDATION_LADDER.md` rung 7 updated to real numbers (~82k/day, ~330k/4 days); rung 8 changed to "pathway identified, not yet filed"
- [x] `docs/FAILURE_MODES_AND_SERVICE_FLOOR.md`: BODS reference updated to 4-day archive path
- [x] `docs/REFLECTIONS.md`: Arya, Jack, and Chris sections all finalised (pending personal sign-off)
