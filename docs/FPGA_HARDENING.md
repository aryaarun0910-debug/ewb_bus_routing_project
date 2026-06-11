# FPGA & Display Hardening — for Chris

**Owner: Chris (FPGA / Verilog / hardware).** This is the punch-list of hardware-side
questions a Grand Finals judge can ask that the repo currently has *no written answer*
for. Each section is short on purpose: it is the answer you give on stage, plus the
one-paragraph repo addition that makes it defensible. None of this is a redesign — it
is all additive disclosure on top of the `fpga/bus_route.v` design that already works.

The pattern to remember: **every one of these is the dark side of a strength.** The
novel LED display is the thing reviewers singled out as "interesting and novel" — which
means it is also the thing they will probe hardest. Answer from the strength first.

---

## 1. LoRa link security — the spoofing attack (CURRENTLY UNADDRESSED — highest priority)

**The attack a judge will describe:** "Your stop unit receives an unauthenticated 433 MHz
broadcast. Anyone with a £15 SX1278 transmitter can sit across the road and paint false
demand onto every LED map in Ladywood. You have built a public-information display that
can be made to lie — to the exact people who can't double-check it on a phone."

`docs/radio_signalling_report.md` covers duty cycle and ERP limits but says **nothing**
about authentication, integrity, or replay. That silence is the wound.

**The answer (write this into `radio_signalling_report.md` as a new "§6 Security" section):**

- **Payload authentication: AES-128-CMAC on every packet.** LoRaWAN provides this natively
  (network + application session keys); even in a bare point-to-point SX1278 link it is a
  few hundred bytes of firmware. The hub signs `{stop_id, demand, route_colour, eta, counter}`;
  the stop unit rejects any packet whose MAC doesn't verify against the pre-shared key.
- **Replay protection: a monotonic frame counter.** Each packet carries an incrementing
  counter; the receiver stores the last-seen value and drops anything ≤ it. A captured
  packet can't be re-broadcast later to freeze the display on stale data.
- **Fail-safe default, not fail-dangerous.** On an invalid MAC, a stale counter, or *no
  packet for N minutes*, the display does **not** show old/attacker data — it shows an
  explicit "no live data" pattern (e.g. all-amber dim, or the static timetable colours).
  **A lying display is worse than a blank one.** This is the single most important sentence
  for the equity argument: the people who depend on it most are the least able to detect a lie.
- **Key management:** keys provisioned at install, rotated on the maintenance schedule
  CIVIC SQUARE already stewards (ties to `STAKEHOLDER_ENGAGEMENT.md`).

**Spoken answer (15 seconds):** "Every packet is AES-128 signed with a rolling counter, so
a forged or replayed broadcast is rejected. And critically — if the unit can't verify a
packet or hasn't heard from the hub, it falls back to 'no data', never to attacker-supplied
data. A blank display is honest; a lying one isn't, and the people who rely on this most
are the least able to catch a lie."

---

## 2. WS2812B outdoors — environment, daylight, vandalism (UNADDRESSED)

The isometric render now advertises a physical solar stop-unit, which *invites* the
hardware-reality question. WS2812B ("NeoPixel") are consumer indoor LEDs.

**The gaps and the honest answers:**

| Concern | Reality | The answer |
|---|---|---|
| Weather / ingress | Bare WS2812B are not weatherproof | IP65 polycarbonate enclosure; conformal-coated PCB; the strip is a stand-in for an outdoor-rated equivalent (e.g. IP67 WS2812B-on-PCB modules, or SK6812 in potted housings) at deployment |
| Daylight readability | RGB LEDs wash out in direct sun | Either high-brightness (≥ 1000 cd/m²) modules with an ambient-light sensor dimming at night, **or** an e-paper + LED hybrid: e-paper carries the map (sunlight-readable, zero idle power), LEDs carry only the live-changing demand glow |
| Vandalism / theft | Street furniture gets attacked | Polycarbonate over the display, fixings inside the enclosure, solar+battery means no mains to cut; unit cost low enough that loss is tolerable; CIVIC SQUARE stewardship handles replacement |
| Maintenance cost | Not costed beyond unit price | Add a per-unit annual maintenance line to `RUNNING_COSTS.md` (inspection + occasional module swap); honestly bound it |
| Power in UK winter | Solar in Birmingham, December | Battery sized for N days autonomy; the LoRa duty-cycle (<10%) and e-paper-for-static approach keep average draw tiny; state the assumed panel/battery sizing even if approximate |

**Spoken answer:** "The WS2812B strip is the bench stand-in. A deployed unit is IP65,
daylight-readable — likely e-paper for the static map with LEDs only for the live demand
glow — solar + battery with a few days' autonomy, and inside a polycarbonate enclosure.
We've added a maintenance line to the running-costs model so the lifecycle cost is honest,
not just the bill of materials."

---

## 3. HDL verification — how was the Verilog actually tested? (NO TESTBENCH VISIBLE)

The software side has 16 passing pytest cases. The FPGA side has **no visible testbench or
simulation artefact** in the repo. A judge with any digital-design background asks: "How did
you verify `bus_route.v` — the bit-bang FSM, the WS2812B timing, the animation state machines?"

**What to add (a `fpga/tb_bus_route.v` testbench + a one-paragraph note in the FPGA README):**

- A self-checking testbench that asserts the WS2812B bit-bang timing (the T0H/T1H/T0L/T1L
  pulse widths against the datasheet — this is the classic place a NeoPixel driver is subtly
  wrong) and that walks the FSM through each `SW[1:0]`/`SW[4:2]` ROM-row selection, checking
  `cur_color` resolves correctly.
- If you ran it in ModelSim/Vivado sim, commit the waveform screenshot or the sim log.
- If verification was on-hardware-by-inspection (you watched the real board light correctly),
  **say exactly that** — it's a legitimate answer for a student FPGA project, but it must be
  *stated* rather than left as an implied gap. Honesty is your brand; an undisclosed gap reads
  worse than a disclosed limitation.

**Spoken answer (pick the true one):** Either "we verified the WS2812B timing in a
self-checking testbench — here's the waveform," or "we verified on-hardware by inspection
against the datasheet timing; a formal testbench is the documented next step." Never let it
look like nobody asked the question.

---

## 4. ROM generation honesty (already disclosed — keep it that way)

The repo already honestly notes `gen_rom.py` doesn't exist and the ROM tables are
committed directly. **Leave that disclosure exactly as-is.** A judge who finds a
self-disclosed gap trusts you more, not less. Do not paper over it with a reverse-engineered
script that wouldn't byte-match the committed ROM — that would trade an honest gap for a
dishonest fix.

---

## Chris's punch-list (in priority order)

1. **Write §6 Security into `radio_signalling_report.md`** (AES-128-CMAC + counter + fail-safe). Highest value, lowest effort. ~30 min.
2. **Write the WS2812B-outdoors paragraph** into the FPGA README + add the maintenance line to `RUNNING_COSTS.md`. ~30 min.
3. **Add `fpga/tb_bus_route.v`** (or at minimum the one-paragraph verification-method note). ~1–2 hr if writing the TB; ~10 min if documenting on-hardware verification.
4. Sanity-check the e-paper-hybrid claim is something you'd actually stand behind on stage before committing it — if not, drop to "high-brightness + ambient dimming" only.
