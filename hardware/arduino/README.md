# Arduino Uno R4 WiFi — stop_unit.ino

Drives a 156-LED WS2812B strip forming the physical Ladywood bus map. Connects to the Pi's
hotspot and receives UDP frames to update stop colours, bus positions, and demand animations.

## Files

```
stop_unit/
└── stop_unit.ino    ← Arduino sketch (open this in Arduino IDE)
```

## Hardware

| Connection | Detail |
|---|---|
| WS2812B DIN | Arduino pin 13 (via 300–470 Ω series resistor) |
| WS2812B GND | Arduino GND + external 5V PSU GND (common ground) |
| WS2812B 5V | External 5V PSU only — do not power 156 LEDs from Arduino 5V pin |
| LED count | 156 |
| LED order | GRB (standard WS2812B) |

A 100–470 µF capacitor across the 5V/GND rail at the strip's power input protects against
inrush current on power-up.

## Libraries required

Install via Arduino IDE → Tools → Manage Libraries:

| Library | Version tested | Install name |
|---|---|---|
| **FastLED** | 3.6+ | `FastLED` |

`WiFiS3.h` is included with the Arduino Uno R4 WiFi board package — no separate install needed.
`avr/pgmspace.h` is part of the AVR toolchain — also built in.

## Board setup

1. Tools → Board → Arduino UNO R4 WiFi
2. Tools → Port → `/dev/cu.usbmodem...` (or `COMx` on Windows)
3. Click Upload

## Behaviour

### Status LED (LED 0, onboard)
| Colour | Meaning |
|---|---|
| Red | No WiFi connection — trying to join `LadywoodBus` |
| Yellow | WiFi connected, no UDP packets received yet — running demo cycle |
| Green | Receiving live UDP from hub.py |

### Stop colours
| Colour | Meaning |
|---|---|
| Blue | Stop on Bus 0 route only |
| Cyan | Stop on Bus 1 route only |
| Purple | Interchange stop (both dynamic routes + all-stops bus) |
| White | All-stops bus only (no dynamic route) |
| Dark/dim | Stop not in any route |

Stop brightness scales with demand level (0–9). The highest-demand stop pulses with a
slow breathing animation (`beatsin8` at 20 BPM).

### Bus LEDs
Each bus is shown as a coloured dot moving along its route:
- Bus 0: Yellow
- Bus 1: Cyan  
- Bus 2 (all-stops): White

### Fallback demo mode
If no UDP packet is received for 30 seconds, the sketch cycles through a self-contained
demo using the hardcoded routes — the map stays animated and informative even if hub.py
is not running.

### Smooth transitions
Stop colours fade smoothly between states using per-channel linear interpolation
(step size 5 per frame). Bus position changes apply immediately without affecting
stops mid-transition.

## WiFi credentials

Hardcoded in the sketch:
```cpp
const char* SSID = "LadywoodBus";
const char* PASS = "ewb2026bus";
```

Change these in `stop_unit.ino` if the hotspot credentials change, then re-upload.

## UDP frame format (received from hub.py)

18 bytes:
```
Byte 0:     0xAA (sync)
Byte 1:     0x01 (address — unit 1)
Bytes 2–16: one byte per stop (S01–S15)
              high nibble = buses at this stop (0–3)
              low nibble  = demand level (0–9)
Byte 17:    XOR checksum of bytes 1–16
```
