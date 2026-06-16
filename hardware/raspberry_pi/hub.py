#!/usr/bin/env python3
"""hub.py — EWB Ladywood smart bus simulation, FPGA-synced.

Data flow:
  Pi → FPGA  : 0xAA frame  (bus positions, high nibble per stop)
  FPGA → Pi  : 0xBB frame  (demand from ROM low nibble, switches drive scenario/slot)
  Pi → Arduino: UDP broadcast (same 0xAA frame, port 4210)

Pi reads FPGA response demand values, identifies current scenario/timeslot,
and adjusts bus routes to match — FPGA switches are the single source of truth.
"""

import serial
import socket
import threading
import time
import sys
from collections import deque

UART_PORT  = '/dev/serial0'
UART_BAUD  = 9600
UDP_PORT   = 4210
BUS_TICK   = 5      # seconds between bus moves
TX_SYNC    = 0xAA
RX_SYNC    = 0xBB

# ── Demand ROM (mirrors latencyZeroFPGA.sv demand_rom function) ──────────────
# ROM[addr] = 15 demand values (4-bit each), addr = scenario*8 + timeslot
ROM: list[list[int]] = [
    [6,4,5,5,8,8,6,5,5,8,4,4,8,8,8],  #  0 Sunny Early Morning
    [7,5,7,6,9,8,7,6,7,8,6,6,9,8,8],  #  1 Sunny AM Peak
    [7,8,6,6,4,8,7,5,6,8,5,5,8,8,8],  #  2 Sunny Mid Morning
    [7,8,6,5,4,8,6,5,6,8,5,5,8,8,8],  #  3 Sunny Lunch
    [7,8,7,6,4,8,7,6,7,8,6,5,8,8,8],  #  4 Sunny Afternoon
    [7,4,7,6,8,8,7,6,7,8,6,6,8,8,8],  #  5 Sunny PM Peak
    [7,8,7,6,4,8,7,6,7,8,6,5,8,8,8],  #  6 Sunny Evening
    [6,4,5,5,0,0,6,5,5,0,4,4,8,0,0],  #  7 Sunny Night
    [6,8,6,5,4,8,6,5,5,8,5,4,8,8,8],  #  8 Rain Early Morning
    [7,9,7,6,5,9,7,6,7,8,6,6,9,8,9],  #  9 Rain AM Peak
    [7,4,7,6,8,8,7,6,6,8,5,5,8,8,8],  # 10 Rain Mid Morning
    [7,4,6,5,8,8,7,5,6,8,5,5,8,8,8],  # 11 Rain Lunch
    [7,4,7,6,8,8,7,6,7,8,6,6,8,8,8],  # 12 Rain Afternoon
    [7,4,7,6,8,8,7,6,7,8,6,6,8,8,8],  # 13 Rain PM Peak
    [7,8,7,6,4,8,7,6,7,8,6,6,8,8,8],  # 14 Rain Evening
    [6,4,6,5,8,8,6,5,6,0,5,4,8,0,8],  # 15 Rain Night
    [6,8,5,5,4,0,6,4,5,8,4,4,8,0,8],  # 16 Festival Early Morning
    [7,8,7,5,8,8,7,5,6,8,5,5,4,4,4],  # 17 Festival AM Peak
    [7,4,6,5,8,8,7,5,6,8,5,5,8,8,8],  # 18 Festival Mid Morning
    [7,4,7,5,8,8,6,5,6,8,5,5,8,0,0],  # 19 Festival Lunch
    [7,4,7,6,8,8,7,5,7,8,5,5,8,8,8],  # 20 Festival Afternoon
    [7,4,7,6,8,8,7,5,7,8,5,5,8,0,8],  # 21 Festival PM Peak
    [7,8,7,6,4,8,7,5,6,0,5,5,8,0,8],  # 22 Festival Evening
    [7,0,6,5,4,0,6,5,6,0,5,4,8,0,0],  # 23 Festival Night
    [6,4,5,5,8,8,5,5,5,8,4,4,8,8,8],  # 24 Storm Early Morning
    [7,9,7,6,5,8,7,6,7,8,6,6,9,8,8],  # 25 Storm AM Peak
    [6,8,6,5,4,8,6,5,6,8,5,5,8,8,8],  # 26 Storm Mid Morning
    [6,4,6,5,8,8,6,5,6,8,5,5,8,8,8],  # 27 Storm Lunch
    [7,4,7,6,8,8,7,6,6,8,5,5,8,8,8],  # 28 Storm Afternoon
    [7,8,7,6,4,8,7,6,6,8,5,5,8,8,8],  # 29 Storm PM Peak
    [7,4,6,6,8,8,7,6,6,8,5,5,8,8,8],  # 30 Storm Evening
    [5,4,5,4,0,0,5,4,4,0,4,4,4,0,0],  # 31 Storm Night
]

SCENARIO_NAMES = ['Sunny', 'Rain', 'Festival', 'Storm']
SLOT_NAMES = [
    'Early Morning', 'AM Peak', 'Mid Morning', 'Lunch',
    'Afternoon',     'PM Peak', 'Evening',     'Night',
]

# Routes per scenario — stop indices 0-based (S01=0 … S15=14)
# Derived from bus_route.v route_stop_led via LED→stop mapping
ROUTES: dict[int, tuple[list[int], list[int]]] = {
    0: ([0,2,6,7,8,11,10,3,1],            [12,13,14,4,5,9,8]    ),  # Sunny        — S09 interchange
    1: ([0,2,6,7,8,11,10,3,1],            [12,13,14,4,5,9,8]    ),  # Rain +shelter — S09 interchange
    2: ([0,2,4,5,6,7,8,9,10,11,12],       [13,14,1,3,8]         ),  # Festival      — S09 interchange
    3: ([0,2,6,7,8,11],                   [12,13,14,4,5,8]      ),  # Storm reduced — S09 interchange
}
BUS2_ROUTE = list(range(15))


def identify_slot(demands: list[int]) -> tuple[int, int]:
    """Match 15 demand values against ROM; return (scenario, timeslot)."""
    best_addr, best_score = 0, -1
    for addr, row in enumerate(ROM):
        score = sum(1 for i in range(15) if row[i] == demands[i])
        if score > best_score:
            best_score, best_addr = score, addr
    return best_addr >> 3, best_addr & 0x07


class Bus:
    def __init__(self, route: list[int], offset: int = 0) -> None:
        self.route = route
        self.idx   = offset % len(route)

    def step(self) -> None:
        self.idx = (self.idx + 1) % len(self.route)

    def set_route(self, route: list[int]) -> None:
        self.idx  = self.idx % len(route)
        self.route = route

    @property
    def stop(self) -> int:
        return self.route[self.idx]


def build_frame(buses: list['Bus']) -> bytes:
    counts = [0] * 15
    for b in buses:
        counts[b.stop] += 1
    payload  = bytes(min(c, 0xF) << 4 for c in counts)
    checksum = 0
    for byte in payload:
        checksum ^= byte
    return bytes([TX_SYNC]) + payload + bytes([checksum])


def build_udp_frame(buses: list['Bus'], addr: int, demands: list[int] | None) -> bytes:
    """18-byte UDP packet for Arduino: 0xAA | addr | 15 stop bytes | checksum.
    Stop byte high nibble = bus count, low nibble = demand from FPGA.
    addr = scenario*8 + timeslot (0-31).
    """
    counts = [0] * 15
    for b in buses:
        counts[b.stop] += 1
    demand  = demands or [0] * 15
    payload = bytes(((min(counts[i], 0xF) << 4) | (demand[i] & 0xF)) for i in range(15))
    addr_b  = addr & 0x1F
    checksum = addr_b
    for byte in payload:
        checksum ^= byte
    return bytes([TX_SYNC, addr_b]) + payload + bytes([checksum])


def read_fpga_response(uart: serial.Serial) -> list[int] | None:
    """Read 0xBB response frame; return list of 15 demand values or None."""
    uart.reset_input_buffer()
    # wait for FPGA to respond (frame takes ~18ms at 9600 baud)
    time.sleep(0.06)
    raw = uart.read(64)
    if not raw:
        return None
    idx = raw.find(RX_SYNC)
    if idx == -1 or len(raw) - idx < 17:
        return None
    frame = raw[idx : idx + 17]
    checksum = 0
    for b in frame[1:16]:
        checksum ^= b
    if checksum != frame[16]:
        return None
    return [frame[i + 1] & 0x0F for i in range(15)]


def route_display(bus: Bus) -> str:
    if len(bus.route) > 12:
        return f"... [S{bus.stop+1:02d}] ..."
    return ' '.join(
        f"[S{s+1:02d}]" if j == bus.idx else f"S{s+1:02d}"
        for j, s in enumerate(bus.route)
    )


def print_status(tick: int, buses: list['Bus'], sc: int, sl: int,
                 demands: list[int] | None, synced: bool) -> None:
    sync_tag = "FPGA synced" if synced else "no FPGA response"
    print(f"\n{'─'*60}")
    print(f"  Tick {tick:04d} | {SCENARIO_NAMES[sc]} — {SLOT_NAMES[sl]}  [{sync_tag}]")
    print(f"{'─'*60}")

    route_labels = [
        f"{len(buses[0].route)}-stop express",
        f"{len(buses[1].route)}-stop local",
        "all-stops",
    ]
    for i, (bus, label) in enumerate(zip(buses, route_labels)):
        print(f"  Bus {i+1} ({label:18s}): {route_display(bus)}")

    if demands:
        print()
        rows = [f"S{i+1:02d}:{d}" for i, d in enumerate(demands)]
        print("  Demand  " + "  ".join(rows[:8]))
        print("          " + "  ".join(rows[8:]))
        top = sorted(range(15), key=lambda i: demands[i], reverse=True)[:3]
        print(f"  Highest demand: {', '.join(f'S{i+1:02d}({demands[i]})' for i in top)}")


# ── Web dashboard (optional — pip3 install flask) ─────────────────────────────
_state: dict = {}
_state_lock = threading.Lock()
_history: deque = deque(maxlen=20)

_HTML = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ladywood Smart Bus System</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0b0c17;color:#cdd6f4;font-family:'Segoe UI',system-ui,sans-serif;max-width:900px;margin:0 auto;min-height:100vh}
.topbar{height:3px;background:linear-gradient(90deg,#1677d8 0%,#7c3ab0 50%,#2d8a4e 100%)}
.inner{padding:16px}
.hdr{display:flex;align-items:flex-start;justify-content:space-between;padding-bottom:10px;border-bottom:1px solid #1e2030;margin-bottom:14px}
.site-name{font-size:.9rem;font-weight:600;color:#89b4fa;letter-spacing:.04em;margin-bottom:5px}
.sc-name{font-size:1.6rem;font-weight:700;color:#cdd6f4;line-height:1}
.sc-slot{font-size:.82rem;color:#585b70;margin-top:4px}
.hdr-right{text-align:right;font-size:.78rem}
.sig-live{color:#a6e3a1}.sig-stale{color:#f38ba8}
.hdr-time{color:#585b70;margin-top:3px}
.sec{font-size:.64rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#585b70;margin:16px 0 7px;display:flex;align-items:center;gap:8px}
.sec::after{content:'';flex:1;height:1px;background:#1e2030}
.bus-row{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:4px}
.bcard{background:#131420;border:1px solid #1e2030;border-radius:8px;padding:10px;border-top:2px solid var(--a)}
.bcard-0{--a:#1677d8}.bcard-1{--a:#2d8a4e}.bcard-2{--a:#585b70}
.blbl{font-size:.63rem;color:#585b70;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px}
.bstop{font-size:1.25rem;font-weight:700;color:#89b4fa}
.bsub{font-size:.63rem;color:#313244;margin-top:3px}
#net-svg{width:100%;display:block}
.cov-bar{background:#131420;border-left:3px solid #a6e3a1;border-radius:0 4px 4px 0;padding:6px 10px;font-size:.78rem;color:#a6e3a1;margin-bottom:8px}
.cov-bar.warn{border-color:#f38ba8;color:#f38ba8}
.bar-row{display:flex;align-items:center;gap:6px;margin:2px 0}
.blabel{font-size:.65rem;color:#585b70;width:26px;flex-shrink:0}
.btrack{height:10px;background:#1e2030;border-radius:2px;overflow:hidden}
.bfill{height:100%;border-radius:2px;transition:width .5s}
.bwrap{display:flex;flex-direction:column;flex:1;gap:2px}
.strack{height:2px;background:#1e2030;border-radius:1px;overflow:hidden}
.sfill{height:100%;background:rgba(255,255,255,0.22);border-radius:1px;transition:width .5s}
.bnum{font-size:.65rem;width:12px;text-align:right;color:#45475a}
.tick-ok{font-size:.6rem;color:#a6e3a1;margin-left:3px}
.tick-no{font-size:.6rem;color:#f38ba8;margin-left:3px}
.c0{background:#1677d8}.c1{background:#2d8a4e}.c2{background:#7c3ab0}.cn{background:#313244}
.hist-meta{display:flex;gap:16px;font-size:.65rem;color:#585b70;margin-bottom:5px}
.hm-avg{display:inline-block;width:18px;height:2px;background:#89b4fa;vertical-align:middle;margin-right:4px;border-radius:1px}
.hm-pk{display:inline-block;width:18px;height:0;border-top:2px dashed #f9e2af;vertical-align:middle;margin-right:4px}
.hm-sup{display:inline-block;width:18px;height:0;border-top:2px dashed #a6e3a1;vertical-align:middle;margin-right:4px}
#hist-svg{width:100%;display:block}
.hline-avg{fill:none;stroke:#89b4fa;stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
.hline-pk{fill:none;stroke:#f9e2af;stroke-width:1.5;stroke-dasharray:4 3;stroke-linejoin:round;stroke-linecap:round}
.hline-sup{fill:none;stroke:#a6e3a1;stroke-width:1.5;stroke-dasharray:2 2;stroke-linejoin:round;stroke-linecap:round}
.hlbl{font-size:9px;fill:#45475a}
.led-key{display:flex;flex-direction:column;gap:6px;font-size:.72rem;color:#585b70}
.lk{display:flex;align-items:center;gap:9px}
.lk-sq{width:12px;height:12px;border-radius:2px;flex-shrink:0}
.lk-ci{width:12px;height:12px;border-radius:50%;flex-shrink:0;border:1px solid #313244}
#foot{font-size:.64rem;color:#45475a;margin-top:14px;padding-top:8px;border-top:1px solid #1e2030}
</style>
</head>
<body>
<div class="topbar"></div>
<div class="inner">

<div class="hdr">
  <div>
    <div class="site-name">Ladywood Smart Bus System</div>
    <div class="sc-name" id="sc">--</div>
    <div class="sc-slot" id="sl">--</div>
  </div>
  <div class="hdr-right">
    <div id="fpga" class="sig-stale">Connecting to FPGA</div>
    <div class="hdr-time" id="ts"></div>
  </div>
</div>

<div class="bus-row" id="buses"></div>

<div class="sec">Route Network</div>
<svg id="net-svg" viewBox="0 0 400 72" height="72" preserveAspectRatio="none"></svg>

<div class="sec">Stop Demand</div>
<div id="cov" class="cov-bar"></div>
<div id="bars"></div>

<div class="sec">Demand History</div>
<div class="hist-meta">
  <span><span class="hm-avg"></span>Average demand across all stops</span>
  <span><span class="hm-pk"></span>Peak stop demand</span>
  <span><span class="hm-sup"></span>Bus supply capacity</span>
</div>
<svg id="hist-svg" viewBox="0 0 400 80" preserveAspectRatio="none" height="80">
  <text class="hlbl" x="0" y="8">9</text>
  <text class="hlbl" x="0" y="44">5</text>
  <text class="hlbl" x="0" y="79">0</text>
  <line x1="12" y1="0" x2="12" y2="80" stroke="#1e2030" stroke-width="1"/>
  <polyline id="hls" class="hline-sup" points=""/>
  <polyline id="hla" class="hline-avg" points=""/>
  <polyline id="hlp" class="hline-pk"  points=""/>
</svg>

<div class="sec">LED Map Key</div>
<div class="led-key">
  <div class="lk"><div class="lk-sq" style="background:#1677d8"></div><span>Blue — Bus 1 (Express) stops only</span></div>
  <div class="lk"><div class="lk-sq" style="background:#2d8a4e"></div><span>Green — Bus 2 (Local) stops only</span></div>
  <div class="lk"><div class="lk-sq" style="background:#7c3ab0"></div><span>Purple — Interchange stop (both buses serve this stop)</span></div>
  <div class="lk"><div class="lk-sq" style="background:#313244"></div><span>Dim white — Stop not on any current route</span></div>
  <div class="lk"><div class="lk-ci" style="background:#fff"></div><span>White moving dot — Express bus live position</span></div>
  <div class="lk"><div class="lk-ci" style="background:#ff0"></div><span>Yellow moving dot — Local bus live position</span></div>
  <div class="lk"><div class="lk-ci" style="background:#0ff"></div><span>Cyan moving dot — All-stops bus live position</span></div>
</div>

<div id="foot"></div>
</div>
<script>
function p(n){return String(n).padStart(2,'0')}
function bc(r){return r===3?'c2':r===1?'c0':r===2?'c1':'cn'}

function drawNet(routes,rt){
  var svg=document.getElementById('net-svg');
  svg.innerHTML='';
  if(!routes||routes.length<2)return;
  var r0=routes[0],r1=routes[1];
  var W=400,y0=18,y1=54,rad=7;
  function ns(tag,a){var e=document.createElementNS('http://www.w3.org/2000/svg',tag);for(var k in a)e.setAttribute(k,a[k]);return e}
  function sx(arr,i){return 18+(i/(arr.length>1?arr.length-1:1))*(W-36)}
  var r0s={},r1s={};
  r0.forEach(function(s){r0s[s]=1});r1.forEach(function(s){r1s[s]=1});
  if(r0.length>1)svg.appendChild(ns('polyline',{points:r0.map(function(s,i){return sx(r0,i)+','+y0}).join(' '),
    fill:'none',stroke:'#1677d8','stroke-width':'2','stroke-opacity':'.3','stroke-linecap':'round','stroke-linejoin':'round'}));
  if(r1.length>1)svg.appendChild(ns('polyline',{points:r1.map(function(s,i){return sx(r1,i)+','+y1}).join(' '),
    fill:'none',stroke:'#2d8a4e','stroke-width':'2','stroke-opacity':'.3','stroke-linecap':'round','stroke-linejoin':'round'}));
  r1.forEach(function(s,i){
    var x=sx(r1,i),col=r0s[s]?'#7c3ab0':'#2d8a4e';
    if(r0s[s]){var i0=r0.indexOf(s);if(i0>=0){var x0c=sx(r0,i0),y0c=y0,x1c=x,y1c=y1,dx=x1c-x0c,dy=y1c-y0c,dist=Math.sqrt(dx*dx+dy*dy),nx=dx/dist,ny=dy/dist;svg.appendChild(ns('line',{x1:(x0c+rad*nx).toFixed(1),y1:(y0c+rad*ny).toFixed(1),x2:(x1c-rad*nx).toFixed(1),y2:(y1c-rad*ny).toFixed(1),stroke:'#7c3ab0','stroke-width':'1.5','stroke-dasharray':'3 2','stroke-opacity':'.7'}))}}
    svg.appendChild(ns('circle',{cx:x,cy:y1,r:rad,fill:col,'fill-opacity':'.15',stroke:col,'stroke-width':'1.5'}));
    var t=svg.appendChild(ns('text',{x:x,y:y1+3.5,'text-anchor':'middle','font-size':'6.5',fill:col,'font-family':'monospace'}));t.textContent='S'+p(s+1);
  });
  r0.forEach(function(s,i){
    var x=sx(r0,i),col=r1s[s]?'#7c3ab0':'#1677d8';
    svg.appendChild(ns('circle',{cx:x,cy:y0,r:rad,fill:col,'fill-opacity':'.15',stroke:col,'stroke-width':'1.5'}));
    var t=svg.appendChild(ns('text',{x:x,y:y0+3.5,'text-anchor':'middle','font-size':'6.5',fill:col,'font-family':'monospace'}));t.textContent='S'+p(s+1);
  });
  var lb0=svg.appendChild(ns('text',{x:2,y:y0+3.5,'font-size':'7',fill:'#45475a','font-style':'italic'}));lb0.textContent='B1';
  var lb1=svg.appendChild(ns('text',{x:2,y:y1+3.5,'font-size':'7',fill:'#45475a','font-style':'italic'}));lb1.textContent='B2';
}

function upd(){
  fetch('/status').then(function(r){return r.json()}).then(function(d){
    document.getElementById('sc').textContent=d.scenario||'--';
    document.getElementById('sl').textContent=d.timeslot||'--';
    var fp=document.getElementById('fpga');
    fp.className=d.synced?'sig-live':'sig-stale';
    fp.textContent=d.synced?'FPGA Live':'No FPGA signal';
    document.getElementById('ts').textContent=new Date().toLocaleTimeString();
    var lbl=['Express','Local','All-stops'],cls=['bcard-0','bcard-1','bcard-2'];
    document.getElementById('buses').innerHTML=(d.buses||[]).map(function(b,i){
      return '<div class="bcard '+cls[i]+'"><div class="blbl">Bus '+(i+1)+' — '+lbl[i]+'</div>'
        +'<div class="bstop">'+b.stop+'</div><div class="bsub">'+b.route_len+'-stop route</div></div>';
    }).join('');
    drawNet(d.routes_raw,d.stop_routes);
    if(d.demands){
      var rt=d.stop_routes||d.demands.map(function(){return 0});
      var dynStops=rt.filter(function(r){return r>0}).length;
      var cov=document.getElementById('cov');
      cov.className='cov-bar';
      cov.textContent='Optimised routes: '+dynStops+'/15 stops — all-stops bus: 15/15 full network coverage';
      document.getElementById('bars').innerHTML=d.demands.map(function(v,i){
        var spct=[33,67,67,100][Math.min(rt[i],3)];
        return '<div class="bar-row"><span class="blabel">S'+p(i+1)+'</span>'
          +'<div class="bwrap">'
          +'<div class="strack"><div class="sfill" style="width:'+spct+'%"></div></div>'
          +'<div class="btrack"><div class="bfill '+bc(rt[i])+'" style="width:'+(v/9*100).toFixed(1)+'%"></div></div>'
          +'</div>'
          +'<span class="bnum">'+v+'</span></div>';
      }).join('');
    }
    var hist=d.history||[];
    if(hist.length>1){
      var n=hist.length,x0=14,xw=386;
      function xp(i){return(x0+i/(n-1)*xw).toFixed(1)}
      function yp(v){return(80-v/9*76).toFixed(1)}
      document.getElementById('hls').setAttribute('points',hist.map(function(e,i){return xp(i)+','+yp(e.supply||0)}).join(' '));
      document.getElementById('hla').setAttribute('points',hist.map(function(e,i){return xp(i)+','+yp(e.avg)}).join(' '));
      document.getElementById('hlp').setAttribute('points',hist.map(function(e,i){return xp(i)+','+yp(e.peak)}).join(' '));
    }
    var top=(d.demands||[]).map(function(v,i){return{v:v,i:i}}).sort(function(a,b){return b.v-a.v}).slice(0,3);
    document.getElementById('foot').textContent='Tick '+(d.tick||0)
      +(top.length?' — Busiest stops: '+top.map(function(x){return'S'+p(x.i+1)+'('+x.v+')'}).join(', '):'');
  }).catch(function(){});
}
upd();setInterval(upd,3000);
</script>
</body>
</html>
"""

try:
    from flask import Flask as _Flask, jsonify as _jsonify
    _app = _Flask(__name__)

    @_app.route('/')
    def _index():
        return _HTML

    @_app.route('/status')
    def _status():
        with _state_lock:
            return _jsonify(dict(_state))

    def _start_web() -> None:
        import logging
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        _app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

    WEB_OK = True
except Exception:
    WEB_OK = False


def main() -> None:
    no_uart = '--no-uart' in sys.argv

    uart = None
    if not no_uart:
        try:
            uart = serial.Serial(UART_PORT, UART_BAUD, timeout=0.15)
            print(f"UART open: {UART_PORT} @ {UART_BAUD} baud")
        except Exception as e:
            print(f"UART unavailable ({e}) — UDP only")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    scenario, timeslot = 0, 0
    last_demands: list[int] | None = None
    fpga_synced = False

    b0, b1 = ROUTES[scenario]
    buses = [Bus(b0, 0), Bus(b1, 3), Bus(BUS2_ROUTE, 7)]

    if WEB_OK:
        threading.Thread(target=_start_web, daemon=True).start()
        print("Web dashboard : http://10.42.0.1:5000")
    else:
        print("Flask not installed — web dashboard disabled (pip3 install flask)")

    print("Simulation started — FPGA switches drive scenario/timeslot")
    print("Ctrl-C to stop\n")

    tick = 0
    while True:
        for bus in buses:
            bus.step()

        frame = build_frame(buses)

        if uart:
            uart.write(frame)
            demands = read_fpga_response(uart)
            if demands:
                new_sc, new_sl = identify_slot(demands)
                if new_sc != scenario:
                    scenario = new_sc
                    buses[0].set_route(ROUTES[scenario][0])
                    buses[1].set_route(ROUTES[scenario][1])
                timeslot  = new_sl
                last_demands = demands
                fpga_synced  = True

        addr = scenario * 8 + timeslot
        try:
            sock.sendto(build_udp_frame(buses, addr, last_demands), ('10.42.0.255', UDP_PORT))
        except OSError:
            pass  # no Arduino connected yet

        stop_routes = [0] * 15
        for s in ROUTES[scenario][0]:
            stop_routes[s] |= 1
        for s in ROUTES[scenario][1]:
            stop_routes[s] |= 2
        if len(ROUTES[scenario][1]) > 1:
            stop_routes[8] |= 3  # S09 always interchange in non-night slots

        bus_at_stop: list[list[int]] = [[] for _ in range(15)]
        for idx, b in enumerate(buses):
            bus_at_stop[b.stop].append(idx)

        if last_demands:
            n_sup = len(ROUTES[scenario][0]) + len(ROUTES[scenario][1]) + 15
            _history.append({
                'avg':    round(sum(last_demands) / 15, 1),
                'peak':   max(last_demands),
                'supply': round(n_sup / 5, 1),
            })

        with _state_lock:
            _state.update({
                'scenario':    SCENARIO_NAMES[scenario],
                'timeslot':    SLOT_NAMES[timeslot],
                'synced':      fpga_synced,
                'tick':        tick,
                'buses': [
                    {'stop': f'S{b.stop+1:02d}', 'route_len': len(b.route)}
                    for b in buses
                ],
                'demands':     last_demands,
                'stop_routes':  stop_routes,
                'bus_at_stop':  bus_at_stop,
                'routes_raw':   [ROUTES[scenario][0], ROUTES[scenario][1]],
                'history':     list(_history),
            })

        print_status(tick, buses, scenario, timeslot, last_demands, fpga_synced)

        tick += 1
        time.sleep(BUS_TICK)


if __name__ == '__main__':
    main()
