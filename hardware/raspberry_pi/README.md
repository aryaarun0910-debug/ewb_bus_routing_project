# Raspberry Pi 5 — hub.py

`hub.py` is the central simulation and communication hub. It:
- Reads demand frames from the FPGA over UART
- Identifies the current scenario and timeslot from the demand values
- Simulates three buses moving around their optimised routes
- Broadcasts bus position + demand state to the Arduino over UDP
- Serves a live web dashboard on port 5000

## Files

| File | Purpose |
|---|---|
| `hub.py` | Main simulation — run this on the Pi |
| `SETUP_GUIDE.txt` | Full hardware setup and wiring reference |

## First-time Pi setup

### 1. Enable UART (run once)

```bash
sudo nano /boot/firmware/config.txt
# Add at the end:
enable_uart=1
dtoverlay=disable-bt
sudo reboot
```

Or via `sudo raspi-config` → Interface Options → Serial Port → login shell: No, hardware: Yes.

### 2. Install dependencies

```bash
pip3 install pyserial flask
```

If the Pi has no internet (hotspot mode, no upstream), install offline:

```bash
# On a Mac with internet:
pip3 download pyserial flask --dest ~/offline_pkgs
scp -r ~/offline_pkgs pi@<PI_IP>:~/offline_pkgs

# On the Pi:
pip3 install --no-index --find-links=~/offline_pkgs pyserial flask
```

### 3. Copy hub.py to the Pi

```bash
scp hub.py pi@<PI_IP>:~/hub.py
```

### 4. Set up the WiFi hotspot (run once)

```bash
sudo nmcli con add type wifi ifname wlan0 con-name hotspot ssid LadywoodBus
sudo nmcli con modify hotspot \
  wifi.mode ap \
  wifi-sec.key-mgmt wpa-psk \
  wifi-sec.psk ewb2026bus \
  wifi-sec.proto rsn \
  wifi-sec.pairwise ccmp \
  wifi-sec.group ccmp
sudo nmcli con modify hotspot \
  ipv4.method shared \
  ipv4.addresses 10.42.0.1/24 \
  connection.autoconnect yes
sudo nmcli con up hotspot
```

Hotspot starts automatically on every boot after this.

## Running

```bash
# Normal mode (FPGA connected):
python3 ~/hub.py

# Without FPGA (Arduino UDP only, simulated demand):
python3 ~/hub.py --no-uart
```

SSH in from Mac when connected to `LadywoodBus`:
```bash
ssh pi@10.42.0.1
```

Web dashboard: `http://10.42.0.1:5000`

## What hub.py does

### UART sync loop (every 5 s)
1. Sends a 17-byte `0xAA` frame to the FPGA with current bus positions (one byte per stop, high nibble = bus count at that stop)
2. Reads back a `0xBB` frame from the FPGA with demand values (low nibble per stop)
3. Uses the 15 demand values to identify the current scenario and timeslot by matching against the internal ROM (same 32-entry table as the FPGA)
4. If the scenario has changed, repositions idle buses onto the new optimised routes

### Bus simulation
Three buses run concurrently:
- **Bus 0** and **Bus 1** — dynamic routes, change per scenario
- **Bus 2** — all-stops route (S01–S15), runs every scenario

Each bus moves one stop per tick (5 s). State 0 = dwelling at stop, State 1 = moving to next stop.

### UDP broadcast
After each UART sync, hub.py broadcasts an 18-byte frame to `10.42.0.255:4210` with bus positions and demand values for all 15 stops.

### Web dashboard
Flask serves a live auto-refreshing dashboard showing:
- Current scenario and timeslot
- FPGA sync status
- Route network diagram (SVG)
- Stop demand bars with supply capacity indicator
- Demand and supply history chart (last 20 ticks)
- LED map colour key
- Coverage text and busiest-stop ticker

## Troubleshooting

| Symptom | Fix |
|---|---|
| `UART unavailable` | Enable UART in `/boot/firmware/config.txt`; check `ls /dev/serial0` |
| FPGA HEX4 shows `-` | hub.py not running, or UART wired wrong — check GPIO14→JP1 Pin1 |
| Flask not starting | `pip3 install flask`; if no internet, use offline install above |
| Arduino stuck yellow | hub.py not running or Pi not at 10.42.0.1 |
| `Permission denied` on scp | Use `ssh-copy-id pi@<IP>` first, or `scp -o StrictHostKeyChecking=no` |
