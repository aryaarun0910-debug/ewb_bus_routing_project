# UK2026-82 — Everyone's Task List

**Team:** Arya Arun · Chris Legge · Jack Booth
**Calendar:** today Sat 13 Jun · team meeting **Sun 14** · deck freeze **Wed 17** · Grand Finals **Fri 19**.

Ordered so nothing blocks the team. The 🔴 items are the ones that, if missed, cost
rubric points or risk the demo. Tick them off.

---

## ⭐ SHARED — at Sunday's meeting (all three, together)

- 🔴 **Write your individual reflections** in `docs/REFLECTIONS.md` (one each — see
  per-person sections below). The file is **live on the public repo right now still
  carrying its "DRAFT — judges can smell ghost-written reflection" banner**; it stays
  there until all three sections are real. This is the cheapest rubric gain in the
  competition (criterion 3a) and **two reviewers flagged missing individual reflections**.
  When done, delete every `*(DRAFT — personalise)*` tag and the banner at the top.
- 🔴 **Decide the retrain** (Arya executes — see Arya §1): adopt the empirical weekend
  curve + remove the `crime_total_2024` feature + re-fetch the Jewellery Quarter POI gap,
  then regenerate + retrain and update the quoted metrics. One retrain, three fixes.
- 🔴 **Rehearse the two killer Q&A answers** (whoever speaks them):
  1. **Circularity** — "your model trained on your own synthetic data" → concede,
     reframe R² as *pipeline capability not forecast accuracy*, walk the anchor chain
     (BUSTO shape r=0.94–0.95 → smartcard levels → real weather → weekend divergence we
     found ourselves → filed APC request). Script in `beast/hardening/CIRCULARITY_REBUTTAL.md`.
  2. **Crime feature** — "policing-bias redlining?" → "we tested it, it carried no signal,
     we deleted it." (`analysis/crime_ablation/`).
- **Agree the "field device, not solver" wording** — the FPGA is the *display/edge device*;
  the XGBoost + CVRP *solving* happens offline. Don't call the FPGA the "solver" on stage.
- **File the TfWM APC data request** so "filed" is literally true on the 19th. Use the
  Wellington FOI as the exact template (fyi.org.nz request 14028).
- **Add the `REFLECTIONS.md` link to the README** docs index once the real reflections are in.

---

## 🟦 ARYA — ML / demand model / analysis / dashboard / deck

1. 🔴 **Execute the Sunday retrain** (after the team signs off):
   - Adopt the empirical weekend curve → replace the weekend factors in `PROFILE_FN`
     (`prediction model/generate_map_dataset.py`) with those in
     `analysis/weekend_curve/empirical_weekend_curve.json` (r jumps 0.677/0.549 → 1.000/0.999).
   - Remove `crime_total_2024` from `_REAL_STATIC_COLS` (model improved without it — R²
     0.9445 → 0.9450).
   - Re-fetch the **Jewellery Quarter (S03) POI** via OSM Overpass (currently all -1 = a
     "no data" sentinel summing to -8) and regenerate `data/osm/ladywood_stop_pois.json`.
   - Regenerate dataset → retrain → update quoted metrics everywhere (they won't get worse).
2. 🔴 **Push the pending dashboard commits** (day-lit map, auto-play, compact controls,
   scrollable stop panel, metric-scale definitions + POI dash). Blocks are in chat;
   `git restore dashboard/web/package-lock.json` first so npm churn stays out.
3. **Your reflection** (Sunday) — anchors: the synthetic→real data pivot; the Gini that
   returned 0.0 and choosing the dissimilarity index instead; deprecating the Unity
   prototype; what "state your limits before anyone asks" taught you. First person, ~300 words.
4. **Fill the one open number** in `docs/EFFECT_SIZE_TRANSLATION.md` — compute
   `visits_per_day` from `route_plan.json` and write N ("~N extra bus arrivals/day at the
   hospital corridor"); use N in the deck's speaker notes instead of the raw 0.011.
5. **Deck slide 18 number** — change any "2.4–3.1 tCO₂e" to "~2–2.5 t" (the cost model now
   computes 1.95–2.54 t on the 300-day operating basis).
6. **Rehearse** the circularity + crime-ablation answers (lead speaker).
7. **Wed 17 morning** — run `tools/bods_avl/derive_dwell_times.py` on the pilot-week data,
   drop the stop-ranking + dwell chart into the deck, then freeze.
8. **Keep the laptop on + charger in** — the BODS collector must keep running across the
   weekend (it captures the weekend dwell data, the model's weakest case).

---

## 🟥 CHRIS — hardware / FPGA / Verilog

1. 🔴 **Your reflection** (Sunday) — `docs/REFLECTIONS.md`. Anchors already in the file:
   the WS2812B timing-closure lesson ("compiles" vs "proven"), the ROM-snapshot honesty
   call, designing for a viewer with no phone/no English, the Repair-Club component
   philosophy, what you'd do differently (the LoRa link-budget survey). ~300 words, your
   voice. Delete the `*(DRAFT — personalise)*` tag when done.
2. 🔴 **The LoRa security paragraph — ~30 min, highest value-per-effort.** Write a "§6
   Security" section into `docs/radio_signalling_report.md` (guidance in
   `docs/FPGA_HARDENING.md` §1): AES-128-CMAC packet signing + monotonic frame counter +
   fail-safe "no data" fallback. Closes the last unanswered Tier-1 Q&A attack (the
   spoofable display).
3. ⭐ **The Living Twin — the showstopper build (Fri/Sat/Sun).** Full doc:
   `tools/living_twin/BUILD_SPEC.md`. Three modules on the DE1-SoC (none touch the
   WS2812B driver): `uart_rx.sv` (9600-8-N-1), `frame_rx.sv` (parse the 17-byte frame +
   XOR + double-buffer), and an **SW9 mux** between the ROM snapshot and the live UART
   feed, plus a staleness watchdog (no frame 60 s → amber "no data" pulse).
   **SW9 down = the ROM snapshot you already trust, so the deadline is never at risk** —
   start it now and let it breathe.
4. **The HDL testbench** — `fpga/tb_bus_route.v` (or a one-paragraph "how we verified"
   note). Driving `uart_rx` with a recorded byte stream and checking the WS2812B pulse
   timings **also produces the verification evidence the hardening punch-list asks for.**
5. **WS2812B outdoors + a maintenance cost line** — a paragraph into the FPGA README
   (`FPGA_HARDENING.md` §2: IP65, daylight readability, vandalism) + one line into
   `docs/design/RUNNING_COSTS.md`.
6. **Mon 16 — wire the Pi to your board.** Pi (`hub.py`, reusing
   `tools/bods_avl/collect_avl.py`) → UART → FPGA. Bench test: watch a real 80 move
   S06→S07 on the board within ~60 s of it happening on Dudley Rd; pull the wire → amber
   pulse; SW9 down → ROM snapshot. **Register your own free BODS key** (link in
   `tools/bods_avl/BODS_AVL_PIPELINE.md`) — don't share keys.

---

## 🟩 JACK — simulation / systems / validation / integration

1. 🔴 **Your reflection** (Sunday) — `docs/REFLECTIONS.md`. Anchors: building the
   multi-agent simulation that proved the routing logic before hardware existed; what it
   felt like when it moved to `legacy/` and why you agreed (or argued) with the call;
   what "my work was scaffolding that let others build" means for engineering ego; the
   Arduino serial-bridge / early integration lessons that survived into the final system;
   what you'd do differently. First person, ~300 words. Delete the `*(DRAFT)*` tag.
2. **Route-plan verification** — sanity-check `route_plan.json` after Arya's retrain:
   every stop served or in the unserved list, capacities respected, no broken geometry.
   You own "does the plan actually hold together."
3. **Living Twin integration support (Mon)** — help Chris bench-test the Pi→FPGA path:
   confirm a real bus moving on Dudley Rd shows on the board, and that the fail-safe
   (pull the wire → amber pulse) works. This is the on-stage moment; rehearse it.
4. **Demo dry-run owner (Tue/Wed)** — run the full presentation flow end-to-end
   (dashboard + Living Twin + deck) at least once before the freeze, with the replay-mode
   fallback tested, so nothing is first-attempted on stage.

---

## ⚙️ STANDING / always-on

- **BODS collector** keeps running on Arya's laptop through the weekend (charger in, no
  sleep on AC). Health check: today's `tools/bods_avl/avl_raw/avl_*.csv` should be growing.
- **Integrity:** never modify the GitHub repo's history during judging beyond these
  agreed commits; the `.bods_key` is personal and gitignored — never commit it.

---

## The 10-second version per person
- **Arya:** push dashboard commits, run the Sunday retrain (weekend curve + drop crime +
  fix S03 POI), your reflection, rehearse circularity. Wed: dwell results → freeze.
- **Chris:** your reflection; LoRa security paragraph (30 min); build the Living Twin HDL
  (SW9 = safe fallback); testbench; Mon wire the Pi.
- **Jack:** your reflection; verify the route plan after retrain; own the Living Twin
  integration test and the full demo dry-run before Wed.
