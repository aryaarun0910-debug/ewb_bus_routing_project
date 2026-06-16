# FPGA — DE1-SoC (Cyclone V)

## Source files

| File | Role |
|---|---|
| `latencyZeroFPGA.sv` | Top-level module: demand ROM, scenario/timeslot logic, UART TX/RX, HEX and LEDR outputs |
| `uart_rx.sv` | UART receiver — 9600-8-N-1 at 50 MHz (divider 5208) |
| `uart_tx.sv` | UART transmitter |
| `frame_rx.sv` | Frame parser: waits for `0xAA` sync, collects 15 payload bytes, verifies XOR checksum, double-buffer latches |

## Compiling (Quartus Prime on Windows/Lenovo)

1. Open Quartus Prime
2. File → New Project Wizard (or open existing `.qpf`)
3. Device: **Cyclone V — 5CSEMA5F31C6**
4. Add all four `.sv` files
5. Processing → Start Compilation

The compiled bitstream lands in `output_files/latencyZeroFPGA.sof`.

A pre-compiled `.sof` is committed to `output_files/` — use it directly if you don't need to recompile.

## Programming (every power cycle — FPGA is volatile)

**Option A — Quartus GUI:**
1. Tools → Programmer → Auto-detect
2. Select the device at `@2` (ID `02D120DD` — the FPGA, not the HPS)
3. Add `output_files/latencyZeroFPGA.sof`
4. Click Start

**Option B — command line:**
```
quartus_pgm -c "DE-SoC [USB-1]" -m JTAG -o "p;output_files/latencyZeroFPGA.sof@2"
```

## Controls

| Control | Function |
|---|---|
| `SW[1:0]` | Scenario select (manual mode): 0=Sunny, 1=Rain, 2=Festival, 3=Storm |
| `SW[4:2]` | Timeslot select (manual): 0=06:00, 1=08:00, …, 7=20:00 |
| `SW[9]` | Auto mode — cycles through all timeslots automatically |
| `SW[8]` | Fast tick (3 s) vs slow tick (30 s) in auto mode |
| `KEY[1]` | Next timeslot |
| `KEY[2]` | Previous timeslot |
| `KEY[3]` | Next scenario |
| `KEY[0]` | Reset |

## Indicators

| Indicator | Meaning |
|---|---|
| `HEX2` | Current scenario (0–3) |
| `HEX1/HEX0` | Time of day (06, 08, 10, 12, 14, 16, 18, 20) |
| `HEX3` | `A` = auto slow, `F` = auto fast, `-` = manual |
| `HEX4` | `L` = Pi connected and sending frames; `-` = idle |
| `LEDR[0–8]` | Demand > 0 for stops S01–S09 |
| `LEDR[9]` | Blinks if no valid Pi frame received for 60 s (staleness watchdog) |

## UART wiring (JP1 header)

```
Pi GPIO14 (TXD)  →  JP1 Pin 1   (GPIO_0[0], FPGA RX)  [RED wire]
Pi GPIO15 (RXD)  →  JP1 Pin 2   (GPIO_0[1], FPGA TX)  [ORANGE wire]
Pi GND           →  JP1 Pin 12  (GND)                  [BROWN wire]
```

## Known timing issue

Setup slack is −11.24 ns (TNS −1847 ns) — the combinational chain through `demand_rom →
stop_color → cur_color` is too deep for one 20 ns clock period. The design works correctly
on the bench (WS2812B timing is observed correct) but timing is not formally closed. Retiming
`cur_color` to latch once per LED rather than recomputing every clock cycle is the documented
fix — it requires simulation verification before committing.
