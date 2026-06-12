# The Living Twin — Build Spec (Chris)

**What it is:** the live architecture from `docs/radio_signalling_report.md`, physically
on the demo table at Grand Finals. A Raspberry Pi 5 (the hub) polls the DfT Bus Open
Data Service for the real vehicles on lines 8A/8C/80/126, and pushes their positions to
an Arduino R4 UNO WiFi (the stop unit) driving a WS2812B strip/matrix — next to the
existing DE1-SoC running the ROM snapshot. Yesterday's build and tomorrow's build, side
by side, both real.

**The on-stage sentence:** *"That light is the number 80, on Dudley Road, right now."*

**The honest framing (say it before anyone asks):** WiFi stands in for the LoRa link —
same hub, same packet, same payload; the radio swaps in at deployment. This is exactly
the bench prototype §7 of the radio report proposes.

**Timeline:** build Fri 13 – Sun 15 · integrate with Pi Mon 16 · freeze + record the
replay file Tue 17. Nothing in this build touches the deck's critical path.

---

## Architecture

```
BODS API (SIRI-VM, ~10s refresh)
        │  HTTPS poll every 30 s  (reuses tools/bods_avl logic + .bods_key)
        ▼
Raspberry Pi 5  ──  hub.py: poll → snap vehicles to stops → build frame
        │  HTTP GET /frame every 5 s over WiFi (phone hotspot, not venue WiFi)
        ▼
Arduino R4 UNO WiFi  ──  living_twin.ino: parse frame → drive LEDs
        ▼
WS2812B strip (one LED per stop, 15 used; matrix fine too)

(optional stretch: Pi UART → DE1-SoC GPIO at 3.3 V, feeding the same frame to a
 UART register in place of the ROM row — the exact upgrade the radio report names.
 Only attempt after the Arduino path works end-to-end.)
```

## The frame format (keep it dumb)

Plain text, one line, newline-terminated — trivially parseable on the Arduino and
trivially loggable for the replay file:

```
F;S01:0;S02:2;S03:1;S04:0;S05:0;S06:3;S07:0;S08:1;S09:0;S10:0;S11:1;S12:0;S13:0;S14:0;S15:2
```

`stop_id:n` where n = number of live vehicles currently nearest that stop (0–9).
Colour mapping on the Arduino: 0 = dim base colour from the stop's demand tier
(the route_plan layer), 1+ = bright "bus here" colour with brightness scaling by n.
Result: the demand map glows softly underneath, and actual buses ride on top of it.

## Pi side — `hub.py` (~50 lines, reuse what exists)

1. Copy `tools/bods_avl/collect_avl.py`'s `poll()` — it already returns
   line/vehicle/lat/lon for the four corridors using `.bods_key`.
2. Snap each vehicle to the nearest of the 15 stops (haversine vs
   `data/gtfs/ladywood_stops.json`, 250 m radius; ignore vehicles between stops or
   light the nearer one — pick one rule and keep it).
3. Serve the frame:

```python
from flask import Flask
app = Flask(__name__)
FRAME = "F;" + ";".join(f"S{i:02d}:0" for i in range(1, 16))

@app.get("/frame")
def frame():
    return FRAME + "\n"

# background thread: every 30 s -> poll() -> snap -> rebuild FRAME
# replay mode:  python hub.py --replay avl_20260616.csv  (same endpoint,
# steps through a recorded day at 60x speed - label it "recorded" on stage)
```

4. **Replay mode is not optional.** Record Tuesday's frames to a file as you go
   (append each FRAME with a timestamp). If the hotspot dies on stage, run
   `--replay` — real data, honestly labelled, demo survives.

## Arduino side — `living_twin.ino` (~40 lines)

- Libraries: `WiFiS3` (built into the R4 core) + `Adafruit_NeoPixel`.
- Loop: every 5 s, `GET http://<pi-ip>:5000/frame`, parse the line, set pixels, `show()`.
- LED index = stop number − 1 (S01 → pixel 0). If using a longer strip/matrix, put the
  15 stop pixels wherever matches your physical map and keep a lookup table.
- Brightness: cap at ~80/255 — LEDs read better on camera and don't blind the front row.
- Failure behaviour mirrors the FPGA hardening doc: if no frame for 60 s, switch to a
  slow amber pulse — the "no live data" pattern, never stale data. Saying "watch what
  it does when I kill the link" is a *demo feature*: it proves the fail-safe design live.

## DE1-SoC stretch goal (only if the above is done by Sunday night)

Pi TX (GPIO14, 3.3 V) → DE1-SoC GPIO RX. 9600-8-N-1, same frame text. A small UART
receiver + register bank in place of the SW-selected ROM row, feeding the existing
`cur_color` logic untouched. This is precisely the "additive next phase, no redesign"
claim in the radio report — demonstrating even a single stop's colour changing live on
the FPGA makes that claim physical. If timing is tight, skip it: the Arduino unit
already proves the architecture, and the ROM-snapshot FPGA next to it tells the
yesterday/tomorrow story.

## Practicalities

- **Network:** phone hotspot only. Test the full chain on the hotspot before Tuesday.
  BODS polling needs internet; the Pi↔Arduino link is local to the hotspot.
- **Power:** Pi on its PSU; Arduino + ≤15 active LEDs is fine over USB. If you use a
  bigger strip, inject 5 V separately and share ground.
- **The key:** `.bods_key` lives on the Pi only. Never in git (already ignored).
- **Bench test acceptance:** watch the real 80 move S06→S07 on the strip within ~60 s
  of it happening on Dudley Road (cross-check against the BODS map or the dashboard).

## Stage choreography (60 seconds, after the FPGA snapshot is shown)

1. "This board is the snapshot we built — demand baked into ROM, honestly static."
2. "This one is what the report proposed next. It's live." *(point)* "That light is the
   number 80 on Dudley Road — now."
3. Kill the hotspot. The unit drops to the amber no-data pulse. "And when the link
   dies, it tells the truth — it never shows a bus that isn't there." Restore link.
4. Hand the duty card to the nearest judge while the LEDs reconnect behind you.

That third beat — failing safely, on purpose, in front of them — is the most
persuasive ten seconds available to this project. Rehearse it.
