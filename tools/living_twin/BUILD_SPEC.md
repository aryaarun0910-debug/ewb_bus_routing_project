# The Living Twin — Build Spec (Chris)

**What it is:** the upgrade `docs/radio_signalling_report.md` §5 proposes, made real on
the demo table: the existing DE1-SoC LED map, with its ROM row selection replaced — via
one switch — by a **live UART register feed** carrying the real positions of the actual
buses on lines 8A/8C/80/126, polled from the DfT Bus Open Data Service by a Raspberry
Pi 5. The WS2812B driving logic does not change. The FPGA stays the solver and the star.

**The on-stage sentence:** *"Same board, same Verilog, one switch — and now that light
is the number 80, on Dudley Road, right now."*

**The honest framing:** the Pi's UART wire stands in for the LoRa receiver — same
register, same payload; the radio swaps in at deployment. This is §7's bench prototype,
one level better: on the production display.

**Timeline:** HDL Fri 13 – Sun 15 · Pi integration Mon 16 · freeze + record the replay
file Tue 17. SW9 fallback means the existing demo is never at risk.

---

## Architecture

```
BODS API (SIRI-VM, ~10 s refresh)
        │  HTTPS poll every 30 s  (reuses tools/bods_avl poll() + .bods_key)
        ▼
Raspberry Pi 5 — hub.py: poll → snap vehicles to the 15 stops → 17-byte frame
        │  UART 9600-8-N-1, Pi GPIO14 TX (3.3 V) ──► DE1-SoC GPIO RX  + common GND
        ▼                                             (both 3.3 V — no level shifter)
DE1-SoC — NEW: uart_rx + frame parser/register bank + mux (SW9: ROM ◄► LIVE)
        ▼  UNCHANGED: cur_color logic, bit-bang FSM, WS2812B timing
156-LED Ladywood map (the existing display)

Optional second receiver (only if everything above works by Sunday night):
Arduino R4 UNO WiFi as a mini stop-unit listening to the same frame relayed by the
Pi over the hotspot — one packet, two receivers: the one-to-many broadcast, physical.
```

## The frame: 17 bytes (this number is a talking point — use it)

| Byte | Meaning |
|---|---|
| 0 | sync `0xAA` |
| 1–15 | one byte per stop S01–S15: `(buses_present << 4) \| demand_level` — high nibble = live vehicles snapped to that stop (0–9), low nibble = demand tier level from route_plan (0–3) |
| 16 | checksum: XOR of bytes 1–15 |

Sent every 5 s. **Seventeen bytes is exactly the "tiny periodic packet" the radio
report's duty-cycle maths assumes** — at 9600 baud it occupies ~18 ms of airtime, which
is the live proof that the <10% LoRa duty-cycle constraint is comfortable. Say that.

## FPGA work (the real task — ~3 modules, all testbench-able)

1. **`uart_rx.sv`** — standard 8-N-1 receiver at 9600 baud from the 50 MHz clock
   (divider 5208; oversample or 16x tick, your call). This is a stock pattern.
2. **`frame_rx.sv`** — byte-level FSM: wait `0xAA` → shift 15 payload bytes → verify
   XOR → on success, latch all 15 into a register bank **atomically** (double-buffer:
   never let the display read a half-frame); on checksum fail, drop silently.
3. **Mux into the existing data path** — where the design currently selects a ROM row
   via `SW[1:0]`/`SW[4:2]`: `SW9 ? live_regs : rom_row`. Colour mapping for live mode:
   low nibble (demand) → the existing tier colours, dimmed; high nibble ≠ 0 → bright
   "bus here" colour on that stop's LED, brightness stepping with the count.
4. **Staleness watchdog** (the fail-safe beat): a counter reset on every valid frame;
   if no valid frame for 60 s in live mode, drive the slow amber "no live data"
   pulse — never hold stale data. This is `docs/FPGA_HARDENING.md` §1's fail-safe,
   implemented, demonstrable.
5. **Testbench:** drive `uart_rx` with a recorded byte stream (the Pi can dump frames
   to a file) and assert the register bank matches — which conveniently also produces
   the HDL-verification evidence the hardening punch-list asks for. Two birds.

Pin notes: any 3.3 V GPIO header pin for RX; Pi GPIO14 is 3.3 V — direct wire + GND,
no level shifter. Constrain the pin in the .qsf and treat RX as asynchronous (2-FF
synchroniser before the UART FSM).

## Pi side — `hub.py` (~60 lines, mostly reuse)

1. Copy `poll()` from `tools/bods_avl/collect_avl.py` (it already filters the four
   lines and uses `.bods_key` — Chris: register your own free key, 2 min, see
   `tools/bods_avl/BODS_AVL_PIPELINE.md`; don't share keys).
2. Snap each vehicle to the nearest stop in `data/gtfs/ladywood_stops.json`
   (haversine, 250 m radius). Demand nibble per stop from the active route_plan
   window (or hardcode the current window's levels — it's a demo, say so).
3. `pyserial` on `/dev/serial0` → write the 17 bytes every 5 s.
4. **Replay mode is not optional:** append every frame + timestamp to a log file as
   you run; `hub.py --replay <file>` steps through a recorded day at 60× with the same
   UART output. If the hotspot/BODS dies on stage: real data, honestly labelled
   "recorded Tuesday", demo survives. And **SW9 down** is always the final fallback —
   the ROM snapshot demo you already trust.

## Bench acceptance test (Monday)

Watch a real 80 move S06 → S07 on the physical map within ~60 s of it happening on
Dudley Road (cross-check the dashboard or BODS map). Then pull the UART wire: amber
pulse within 60 s. Then SW9 down: ROM snapshot returns. All three behaviours = ship.

## Stage choreography (60 seconds)

1. SW9 down: "This is the build we submitted — demand baked into ROM, honestly static."
2. SW9 up, live: "This is the same board, same Verilog, one new register — live. That
   light is the number 80 on Dudley Road, right now."
3. Pull the UART wire. Amber pulse. "And when the link dies it tells the truth — it
   never shows a bus that isn't there." Reconnect.
4. Hand the nearest judge the printed driver duty card while it resyncs.

Beat 3 — failing safely, on purpose, in front of them — is the most persuasive ten
seconds available to this project. Rehearse it until it's boring.

## Priority order for the weekend (so this never eats the critical path)

Reflection (Sunday, blocks the team) → `uart_rx` + `frame_rx` + mux (Fri–Sun) →
LoRa security paragraph from FPGA_HARDENING (30 min) → Pi integration (Mon) →
Arduino second receiver (only if bored) → freeze Tue 17.
