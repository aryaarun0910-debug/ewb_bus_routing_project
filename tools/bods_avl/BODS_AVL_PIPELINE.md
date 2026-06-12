# The Birmingham APC-Proxy — BODS AVL Dwell-Time Pipeline

**The closest legal, open thing to Ladywood APC data that exists — and it's specific
to the actual buses on the actual Ladywood corridors.**

## The idea

True APC (boarding counts) for West Midlands buses is private. But the DfT **Bus Open
Data Service (BODS)** publishes **SIRI-VM live vehicle locations for every English bus,
including every National Express West Midlands vehicle on routes 8A/8C, 80 and 126** —
free, open licence, refreshed every ~10 seconds.

From a few weeks of archived AVL you can derive **dwell time at each stop** (arrival→
departure gap). Dwell time is a published, literature-standard proxy for
boarding+alighting activity (dwell ≈ door time + passengers × marginal board time —
see TCQSM Ch.6). It is not APC — but it is *observed, Ladywood-specific, per-stop,
per-trip data*, which is precisely the category the project has zero of today.

**What it would give Ladywood:**
1. A per-stop, per-hour dwell-time profile for the actual modelled corridors → direct
   shape check of PROFILE_FN against *Birmingham* reality (today's best check is London).
2. Stop ranking validation: do S06/S02/S01 actually show the longest dwells?
3. The on-stage sentence: *"We don't have Birmingham's passenger counts — TfWM does.
   But we measured every bus on our corridors for N weeks, and the dwell-time
   fingerprint at City Hospital matches the demand curve we modelled."*

## The one thing only you can do (5 minutes)

BODS requires a **free account** (name + email, instant, no payment, OGL data):
1. Register: https://data.bus-data.dft.gov.uk/account/signup/
2. Confirm email → log in → Account → API key (it's shown on your profile page)
3. Put the key in: `beast/beyond/bods_avl/.bods_key` (one line, just the key)

## Then the pipeline runs itself

`collect_avl.py` (this folder):
- Polls the BODS SIRI-VM datafeed for a West Midlands bounding box every 30 s
- Filters to the modelled corridors' line refs (8A, 8C, 80, 126)
- Appends one CSV row per vehicle observation: timestamp, line, vehicle ref, lat/lon,
  bearing — **no passenger data, no personal data; vehicle positions only**
- Run it for 2–4 weeks (a Raspberry Pi or an always-on PC is fine; ~10–30 MB/day)

`derive_dwell_times.py` (this folder):
- Snaps observations to the repo's stop coordinates (50 m radius)
- Dwell = last-seen-stationary − first-seen-stationary per vehicle per stop visit
- Aggregates to stop × hour × day-type dwell profiles + correlates against PROFILE_FN

## Honest limits (state them first, as always)

- Dwell conflates boarding, alighting, traffic holds and driver breaks; we mitigate by
  median-filtering, excluding terminus stands, and flagging signal-adjacent stops.
- 10-second polling quantises short dwells; counts of *stops-made* (vs skipped) are
  robust even when durations are noisy. A skipped stop = zero demand observed — itself
  a signal the model can be scored against.
- It validates **shape and ranking**, not absolute volumes. The TfWM APC request
  remains the gold standard; this is the bridge evidence while it's pending.

## Why this wins points

Reviewer 2 asked for "feedback loops from existing technologies." This *is* one —
built from the same open feed (BODS) that the rollout pathway already cites, costing
nothing, violating nothing, and pointed directly at the project's #1 disclosed gap.
