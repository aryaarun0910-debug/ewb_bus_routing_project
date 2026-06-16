# Hardware Demo — Ladywood Smart Bus System

Physical demonstration of the route optimisation system, built for the EWB UK Grand Finals 2026.
Three devices communicate over UART and WiFi UDP to animate a 156-LED map of the Ladywood
bus network in real time, driven by demand data from the prediction model.

## System overview

```
┌─────────────────┐   UART 9600-8-N-1   ┌─────────────────┐
│  DE1-SoC FPGA   │◄──────────────────►│  Raspberry Pi 5  │
│  (Cyclone V)    │   17-byte frames    │  hub.py          │
│                 │                     │  Flask dashboard │
│  Demand ROM     │                     │  UDP broadcast   │
│  Scenario logic │                     └────────┬────────┘
│  HEX / LEDR     │                              │ UDP port 4210
└─────────────────┘                              ▼
                                       ┌─────────────────┐
                                       │  Arduino Uno R4  │
                                       │  WiFi            │
                                       │  156-LED strip   │
                                       │  WS2812B map     │
                                       └─────────────────┘
```

## Device roles

| Device | Role |
|---|---|
| **DE1-SoC FPGA** | Stores the demand ROM (32 scenario/timeslot combinations × 15 stops). Switches select scenario and timeslot. Sends demand nibbles to Pi; receives bus-position nibbles back and shows them on HEX displays and LEDRs. |
| **Raspberry Pi 5** | Runs `hub.py`: reads FPGA demand frames, identifies current scenario, simulates three buses moving around their routes, and broadcasts bus+demand state over UDP. Also serves the web dashboard on port 5000. |
| **Arduino Uno R4 WiFi** | Connects to the Pi's hotspot, receives UDP frames, and drives the 156-LED WS2812B strip — colour-coding stops by route and demand, animating bus positions, and breathing-pulsing the highest-demand stop. |

## Wiring

```
Pi GPIO14 (TXD)  →  FPGA JP1 Pin 1  (UART RX)  [RED wire]
Pi GPIO15 (RXD)  →  FPGA JP1 Pin 2  (UART TX)  [ORANGE wire]
Pi GND           →  FPGA JP1 Pin 12 (GND)       [BROWN wire]

Arduino pin 13   →  LED strip DIN  (via 330 Ω resistor)
Arduino GND      →  LED strip GND  (+ external 5V PSU GND)
External 5V PSU  →  LED strip 5V
```

## Frame protocol

**Pi → FPGA** (`0xAA` frame, 17 bytes):
```
Byte 0:    0xAA (sync)
Bytes 1–15: one byte per stop — high nibble = number of buses at stop (0–9)
Byte 16:   XOR checksum of bytes 1–15
```

**FPGA → Pi** (`0xBB` frame, 17 bytes):
```
Byte 0:    0xBB (sync)
Bytes 1–15: one byte per stop — high nibble = bus count (echo), low nibble = demand (0–9)
Byte 16:   XOR checksum of bytes 1–15
```

**Pi → Arduino** (UDP broadcast to 10.42.0.255:4210, 18 bytes):
```
Byte 0:    0xAA (sync)
Byte 1:    address byte (0x01 for stop unit 1)
Bytes 2–16: same stop payload as Pi→FPGA frame
Byte 17:   XOR checksum
```

## Network

The Pi creates a WiFi hotspot. Everything connects to it — no internet required.

| | |
|---|---|
| SSID | `LadywoodBus` |
| Password | `ewb2026bus` |
| Pi IP | `10.42.0.1` |
| Web dashboard | `http://10.42.0.1:5000` |

## Startup sequence

1. Power on FPGA → program via Quartus if power-cycled (FPGA is volatile)
2. Power on Pi → hotspot starts automatically (~20 s)
3. SSH in: `ssh pi@10.42.0.1` → run `python3 ~/hub.py`
4. Power on Arduino + LED map → status LED: red → yellow → green (~15 s)
5. Open `http://10.42.0.1:5000` on any device connected to `LadywoodBus`

**System ready when:** FPGA HEX4 shows `L`, Arduino LED is green, dashboard shows live data.

## Folders

| Folder | Contents |
|---|---|
| [`fpga/`](fpga/) | SystemVerilog source files + compiled `.sof` bitstream |
| [`raspberry_pi/`](raspberry_pi/) | `hub.py` simulation + Flask dashboard + setup guide |
| [`arduino/`](arduino/) | `stop_unit.ino` LED map sketch |

## Relationship to the software model

The hardware demo is a standalone simulation — it does not load `prediction model/route_plan.json`
or call the FastAPI backend at runtime. The demand values are baked into the FPGA ROM
(`latencyZeroFPGA.sv → demand_rom`) from the same source data the model was trained on.
Bus routes in `hub.py` match the optimised output for each of the four weather scenarios.
This means the demo runs entirely offline, which is intentional for competition-day reliability.
