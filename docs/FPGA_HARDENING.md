# FPGA & Display Hardening

Design rationale and verification notes for the DE1-SoC FPGA board and WS2812B display layer.

---

## 1. LoRa link security

The stop unit receives LoRa 433 MHz broadcasts. The security design addresses three attack
vectors, all documented in `docs/radio_signalling_report.md §6 Security`:

- **Payload authentication: AES-128-CMAC on every packet.** LoRaWAN provides this natively
  (network + application session keys); even in a bare point-to-point SX1278 link it requires
  a few hundred bytes of firmware. The hub signs `{stop_id, demand, route_colour, eta, counter}`;
  the stop unit rejects any packet whose MAC does not verify against the pre-shared key.
- **Replay protection: a monotonic frame counter.** Each packet carries an incrementing
  counter; the receiver stores the last-seen value and drops anything at or below it. A captured
  packet cannot be re-broadcast later to freeze the display on stale data.
- **Fail-safe default.** On an invalid MAC, a stale counter, or no packet for N minutes,
  the display shows an explicit "no live data" pattern (all-amber dim, or static timetable
  colours) rather than old or attacker-supplied data. A lying display is worse than a blank
  one — this matters most for the equity argument: the people who depend on the display most
  are the least able to detect a lie.
- **Key management:** keys provisioned at install, rotated on the maintenance schedule
  CIVIC SQUARE already stewards (ties to `STAKEHOLDER_ENGAGEMENT.md`).

---

## 2. WS2812B outdoors — environment, daylight, vandalism

The WS2812B strip on the DE1-SoC bench board is the development stand-in. A deployed stop
unit addresses the following:

| Concern | Reality | Design response |
|---|---|---|
| Weather / ingress | Bare WS2812B are not weatherproof | IP65 polycarbonate enclosure; conformal-coated PCB; outdoor-rated WS2812B-on-PCB modules or SK6812 in potted housings at deployment |
| Daylight readability | RGB LEDs wash out in direct sun | High-brightness (≥ 1000 cd/m²) modules with ambient-light sensor, or e-paper for the static map with LEDs only for the live demand glow |
| Vandalism / theft | Street furniture gets attacked | Polycarbonate over the display, fixings inside the enclosure, solar+battery means no mains to cut; unit cost low enough that loss is tolerable; CIVIC SQUARE stewardship handles replacement |
| Maintenance cost | Not costed beyond unit price | Annual maintenance line in `docs/design/RUNNING_COSTS.md` (inspection + occasional module swap) |
| Power in UK winter | Solar in Birmingham, December | Battery sized for N days autonomy; LoRa duty-cycle (<10%) and e-paper-for-static approach keep average draw low |

---

## 3. HDL verification

The software pipeline has passing pytest cases. The FPGA design does not include a committed
simulation testbench. A self-checking testbench that verifies the WS2812B bit-bang timing
(T0H/T1H/T0L/T1L pulse widths against the datasheet) and the animation FSM state transitions
is documented as a Phase-2 task. See `fpga/README.md` for the verification method used during
development.

---

## 4. ROM generation honesty

The repo explicitly notes that `gen_rom.py` is not committed and the ROM tables were written
directly. This disclosure is intentional. A self-disclosed limitation is more credible than a
reverse-engineered fix that would not byte-match the committed ROM.
