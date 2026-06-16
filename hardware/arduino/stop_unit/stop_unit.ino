// stop_unit.ino -- EWB Ladywood bus map display, Arduino Uno R4 WiFi
// Receives 18-byte UDP from hub.py; drives 156-LED WS2812B strip.
// Falls back to self-cycling demo if no UDP received for 30s.
//
// Wiring:
//   WS2812B DIN -> Pin 13 (through 300-470 ohm resistor)
//   WS2812B GND -> GND
//   WS2812B 5V  -> external 5V supply

#include <WiFiS3.h>
#include <FastLED.h>
#include <avr/pgmspace.h>

// -- WiFi / UDP ---------------------------------------------------------------
const char* SSID     = "LadywoodBus";
const char* PASS     = "ewb2026bus";
const int   UDP_PORT = 4210;
WiFiUDP udp;
bool wifi_ok = false;

// -- LED strip ----------------------------------------------------------------
#define NUM_LEDS    156
#define DATA_PIN     13
#define BRIGHTNESS  200
CRGB leds[NUM_LEDS];

// -- Timing -------------------------------------------------------------------
#define DWELL_MS         2000
#define MOVE_MS           150
#define DEMO_INTERVAL_MS 10000   // fallback demo: 10s per state
#define UDP_TIMEOUT_MS   30000   // fall back to demo after 30s silence

#define N_STOPS        15
#define NUM_PATHS      53
#define TOTAL_PATH_LEN 917
#define MAX_ROUTE_LEN  11

// -- PROGMEM tables (unchanged from original bus_route_arduino.ino) -----------

static const uint8_t PROGMEM stop_leds[N_STOPS] = {
    106, 114, 33, 70, 78, 25, 65, 58, 95, 21, 50, 44, 142, 11, 1
};

static const uint8_t PROGMEM demand_data[32][N_STOPS] = {
    {6, 4, 5, 5, 8, 8, 6, 5, 5, 8, 4, 4, 8, 8, 8},
    {7, 5, 7, 6, 9, 8, 7, 6, 7, 8, 6, 6, 9, 8, 8},
    {7, 8, 6, 6, 4, 8, 7, 5, 6, 8, 5, 5, 8, 8, 8},
    {7, 8, 6, 5, 4, 8, 6, 5, 6, 8, 5, 5, 8, 8, 8},
    {7, 8, 7, 6, 4, 8, 7, 6, 7, 8, 6, 5, 8, 8, 8},
    {7, 4, 7, 6, 8, 8, 7, 6, 7, 8, 6, 6, 8, 8, 8},
    {7, 8, 7, 6, 4, 8, 7, 6, 7, 8, 6, 5, 8, 8, 8},
    {6, 4, 5, 5, 0, 0, 6, 5, 5, 0, 4, 4, 8, 0, 0},
    {6, 8, 6, 5, 4, 8, 6, 5, 5, 8, 5, 4, 8, 8, 8},
    {7, 9, 7, 6, 5, 9, 7, 6, 7, 8, 6, 6, 9, 8, 9},
    {7, 4, 7, 6, 8, 8, 7, 6, 6, 8, 5, 5, 8, 8, 8},
    {7, 4, 6, 5, 8, 8, 7, 5, 6, 8, 5, 5, 8, 8, 8},
    {7, 4, 7, 6, 8, 8, 7, 6, 7, 8, 6, 6, 8, 8, 8},
    {7, 4, 7, 6, 8, 8, 7, 6, 7, 8, 6, 6, 8, 8, 8},
    {7, 8, 7, 6, 4, 8, 7, 6, 7, 8, 6, 6, 8, 8, 8},
    {6, 4, 6, 5, 8, 8, 6, 5, 6, 0, 5, 4, 8, 0, 8},
    {6, 8, 5, 5, 4, 0, 6, 4, 5, 8, 4, 4, 8, 0, 8},
    {7, 8, 7, 5, 8, 8, 7, 5, 6, 8, 5, 5, 4, 4, 4},
    {7, 4, 6, 5, 8, 8, 7, 5, 6, 8, 5, 5, 8, 8, 8},
    {7, 4, 7, 5, 8, 8, 6, 5, 6, 8, 5, 5, 8, 0, 0},
    {7, 4, 7, 6, 8, 8, 7, 5, 7, 8, 5, 5, 8, 8, 8},
    {7, 4, 7, 6, 8, 8, 7, 5, 7, 8, 5, 5, 8, 0, 8},
    {7, 8, 7, 6, 4, 8, 7, 5, 6, 0, 5, 5, 8, 0, 8},
    {7, 0, 6, 5, 4, 0, 6, 5, 6, 0, 5, 4, 8, 0, 0},
    {6, 4, 5, 5, 8, 8, 5, 5, 5, 8, 4, 4, 8, 8, 8},
    {7, 9, 7, 6, 5, 8, 7, 6, 7, 8, 6, 6, 9, 8, 8},
    {6, 8, 6, 5, 4, 8, 6, 5, 6, 8, 5, 5, 8, 8, 8},
    {6, 4, 6, 5, 8, 8, 6, 5, 6, 8, 5, 5, 8, 8, 8},
    {7, 4, 7, 6, 8, 8, 7, 6, 6, 8, 5, 5, 8, 8, 8},
    {7, 8, 7, 6, 4, 8, 7, 6, 6, 8, 5, 5, 8, 8, 8},
    {7, 4, 6, 6, 8, 8, 7, 6, 6, 8, 5, 5, 8, 8, 8},
    {5, 4, 5, 4, 0, 0, 5, 4, 4, 0, 4, 4, 4, 0, 0}
};

static const uint8_t PROGMEM route_stops_pgm[32][2][11] = {
    {{106,33,65,58,95,44,50,70,114,0,0},{142,11,1,78,25,21,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,114,0,0},{142,11,1,78,25,21,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,78,0,0},{142,11,1,114,25,21,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,78,0,0},{142,11,1,114,25,21,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,78,0,0},{142,11,1,114,25,21,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,114,0,0},{142,11,1,78,25,21,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,78,0,0},{142,11,1,114,25,21,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,114,0,0},{142,0,0,0,0,0,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,78,0,0},{142,11,1,114,25,21,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,78,0,0},{142,11,1,21,25,114,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,114,0,0},{142,11,1,78,25,21,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,114,0,0},{142,11,1,78,25,21,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,114,0,0},{142,11,1,78,25,21,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,114,0,0},{142,11,1,78,25,21,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,78,0,0},{142,11,1,114,25,21,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,114,0,0},{142,1,78,25,0,0,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,78,0,0},{142,1,21,114,0,0,0,0,0,0,0}},
    {{65,33,106,70,95,58,44,50,142,11,1},{114,25,21,78,0,0,0,0,0,0,0}},
    {{106,33,65,95,58,44,50,70,114,0,0},{142,11,1,21,25,78,0,0,0,0,0}},
    {{106,33,65,95,58,44,50,70,114,0,0},{142,25,21,78,0,0,0,0,0,0,0}},
    {{106,33,65,95,58,44,50,70,114,0,0},{142,11,1,78,25,21,0,0,0,0,0}},
    {{106,33,65,95,58,44,50,70,114,0,0},{142,1,78,25,21,0,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,78,0,0},{114,142,1,25,0,0,0,0,0,0,0}},
    {{106,33,65,95,58,44,50,70,78,0,0},{142,0,0,0,0,0,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,114,0,0},{142,11,1,21,25,78,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,78,0,0},{142,11,1,21,25,114,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,78,0,0},{142,11,1,21,25,114,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,114,0,0},{142,11,1,78,21,25,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,114,0,0},{142,11,1,78,25,21,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,78,0,0},{142,11,1,114,25,21,0,0,0,0,0}},
    {{106,33,65,58,95,44,50,70,114,0,0},{142,11,1,25,21,78,0,0,0,0,0}},
    {{106,70,33,65,58,95,44,50,142,114,0},{106,0,0,0,0,0,0,0,0,0,0}}
};

static const uint8_t PROGMEM route_lens_pgm[32][2] = {
    {9,6},{9,6},{9,6},{9,6},{9,6},{9,6},{9,6},{9,1},
    {9,6},{9,6},{9,6},{9,6},{9,6},{9,6},{9,6},{9,4},
    {9,4},{11,4},{9,6},{9,4},{9,6},{9,5},{9,4},{9,1},
    {9,6},{9,6},{9,6},{9,6},{9,6},{9,6},{9,6},{10,1}
};

static const uint8_t PROGMEM path_pairs[NUM_PATHS][2] = {
    {1,21},{1,25},{1,65},{1,78},{1,106},{1,114},{11,1},{21,25},{21,50},{21,78},
    {21,114},{21,142},{25,21},{25,65},{25,78},{25,114},{25,142},{33,65},{33,70},
    {33,106},{44,50},{44,142},{50,44},{50,70},{50,142},{58,44},{58,95},{65,33},
    {65,58},{65,95},{70,33},{70,78},{70,95},{70,114},{78,21},{78,25},{78,106},
    {78,114},{78,142},{95,21},{95,44},{95,58},{106,33},{106,70},{106,114},{114,25},
    {114,33},{114,106},{114,142},{142,1},{142,11},{142,25},{142,114}
};

static const uint8_t PROGMEM path_lengths[NUM_PATHS] = {
    21,25,23,29,35,29,11,17,7,29,21,19,17,15,29,9,25,7,21,15,7,13,7,27,15,7,11,
    7,13,15,21,9,13,17,29,29,11,21,29,21,9,11,15,7,11,9,9,11,29,13,13,25,29
};

static const uint16_t PROGMEM path_offsets[NUM_PATHS] = {
    0,21,46,69,98,133,162,173,190,197,226,247,266,283,298,327,336,361,368,389,
    404,411,424,431,458,473,480,491,498,511,526,547,556,569,586,615,644,655,676,
    705,726,735,746,761,768,779,788,797,808,837,850,863,888
};

static const uint8_t PROGMEM path_data[TOTAL_PATH_LEN] = {
    1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,1,153,152,151,150,
    149,148,64,63,62,46,47,48,49,50,131,130,129,128,127,126,22,23,24,25,1,153,
    152,151,150,149,148,64,63,62,46,45,44,43,89,42,41,40,39,68,67,66,65,1,153,
    152,151,150,149,148,64,63,62,46,45,44,43,89,90,91,92,93,94,95,85,84,83,82,
    81,80,79,78,1,153,152,151,150,149,148,64,63,62,46,45,44,43,89,90,91,92,93,
    94,95,96,97,98,99,100,101,102,74,73,72,103,104,105,106,1,153,152,151,150,149,
    148,64,63,62,46,47,48,49,50,131,130,129,128,127,126,125,31,30,29,124,123,122,
    114,11,10,9,8,7,6,5,4,3,2,1,21,20,19,53,52,51,50,131,130,129,128,127,126,22,
    23,24,25,21,20,19,53,52,51,50,21,20,19,53,52,51,50,49,48,47,46,45,44,43,89,
    90,91,92,93,94,95,85,84,83,82,81,80,79,78,21,20,19,53,52,51,50,131,130,129,
    128,127,126,125,31,30,29,124,123,122,114,21,20,19,18,17,16,15,14,13,141,140,
    139,138,137,146,145,144,143,142,25,24,23,22,126,127,128,129,130,131,50,51,52,
    53,19,20,21,25,24,23,22,126,125,31,32,33,34,35,69,67,66,65,25,24,23,22,126,
    127,128,55,56,57,58,59,60,88,89,90,91,92,93,94,95,85,84,83,82,81,80,79,78,25,
    26,27,28,29,124,123,122,114,25,24,23,22,126,127,128,55,56,57,58,59,60,61,46,
    62,63,64,148,147,146,145,144,143,142,33,34,35,69,67,66,65,33,121,120,119,118,
    117,116,113,112,111,110,109,108,107,106,105,104,103,72,71,70,33,121,120,119,
    118,117,116,113,112,111,110,109,108,107,106,44,45,46,47,48,49,50,44,45,46,62,
    63,64,148,147,146,145,144,143,142,50,49,48,47,46,45,44,50,49,48,47,46,45,44,
    43,89,90,91,92,93,94,95,96,97,98,99,100,101,102,74,73,72,71,70,50,49,48,47,
    46,62,63,64,148,147,146,145,144,143,142,58,59,60,61,46,45,44,58,59,60,88,89,
    90,91,92,93,94,95,65,66,67,69,35,34,33,65,66,67,68,39,40,41,42,89,88,60,59,
    58,65,66,67,68,39,40,41,42,89,90,91,92,93,94,95,70,71,72,103,104,105,106,107,
    108,109,110,111,112,113,116,117,118,119,120,121,33,70,71,72,73,74,75,76,77,78,
    70,71,72,73,74,102,101,100,99,98,97,96,95,70,71,72,103,104,105,106,107,108,
    109,110,111,112,113,116,115,114,78,79,80,81,82,83,84,85,95,94,93,92,91,90,89,
    43,44,45,46,47,48,49,50,51,52,53,19,20,21,78,77,76,75,74,73,72,103,104,105,
    106,107,108,109,110,111,112,113,116,115,114,122,123,124,29,28,27,26,25,78,77,
    76,75,74,73,72,103,104,105,106,78,77,76,75,74,73,72,103,104,105,106,107,108,
    109,110,111,112,113,116,115,114,78,79,80,81,82,83,84,85,95,94,93,92,91,90,89,
    43,44,45,46,62,63,64,148,147,146,145,144,143,142,95,94,93,92,91,90,89,43,44,
    45,46,47,48,49,50,51,52,53,19,20,21,95,94,93,92,91,90,89,43,44,95,94,93,92,
    91,90,89,88,60,59,58,106,107,108,109,110,111,112,113,116,117,118,119,120,121,
    33,106,105,104,103,72,71,70,106,107,108,109,110,111,112,113,116,115,114,114,
    122,123,124,29,28,27,26,25,114,115,116,117,118,119,120,121,33,114,115,116,113,
    112,111,110,109,108,107,106,114,122,123,124,29,30,31,125,126,127,128,55,56,57,
    58,59,60,61,46,62,63,64,148,147,146,145,144,143,142,142,143,144,145,146,147,
    148,149,150,151,152,153,1,142,143,144,145,146,137,138,139,140,141,13,12,11,142,
    143,144,145,146,147,148,64,63,62,46,47,48,49,50,131,130,129,128,127,126,22,23,
    24,25,142,143,144,145,146,147,148,64,63,62,46,47,48,49,50,131,130,129,128,127,
    126,125,31,30,29,124,123,122,114
};

// -- PROGMEM helpers (unchanged) ----------------------------------------------

uint8_t get_demand(uint8_t addr, uint8_t stop_idx) {
    return pgm_read_byte(&demand_data[addr][stop_idx]);
}
uint8_t get_route_stop(uint8_t addr, uint8_t bus, uint8_t step) {
    return pgm_read_byte(&route_stops_pgm[addr][bus][step]);
}
uint8_t get_route_len(uint8_t addr, uint8_t bus) {
    return pgm_read_byte(&route_lens_pgm[addr][bus]);
}
uint8_t get_path_id(uint8_t from_led, uint8_t to_led) {
    for (uint8_t i = 0; i < NUM_PATHS; i++) {
        if (pgm_read_byte(&path_pairs[i][0]) == from_led &&
            pgm_read_byte(&path_pairs[i][1]) == to_led) return i;
    }
    return 0;
}
uint8_t get_path_len(uint8_t path_id) {
    return pgm_read_byte(&path_lengths[path_id]);
}
uint8_t path_rom_lookup(uint8_t path_id, uint8_t step) {
    uint16_t offset = pgm_read_word(&path_offsets[path_id]) + step;
    return pgm_read_byte(&path_data[offset]);
}
uint8_t get_stop_led(uint8_t stop_idx) {
    return pgm_read_byte(&stop_leds[stop_idx]);
}
uint8_t stop_in_routes(uint8_t addr, uint8_t stop_led) {
    // LED 95 (S09) is a designated interchange served by both buses
    // except night slots where bus 1 has only 1 stop
    if (stop_led == 95 && get_route_len(addr, 1) > 1) return 3;

    bool in0 = false, in1 = false;
    for (uint8_t i = 0; i < get_route_len(addr, 0) && !in0; i++)
        if (get_route_stop(addr, 0, i) == stop_led) in0 = true;
    for (uint8_t i = 0; i < get_route_len(addr, 1) && !in1; i++)
        if (get_route_stop(addr, 1, i) == stop_led) in1 = true;
    return (in0 ? 1 : 0) | (in1 ? 2 : 0);
}

CRGB get_stop_color(uint8_t addr, uint8_t stop_idx) {
    uint8_t rv = get_demand(addr, stop_idx);
    if (rv == 0) return CRGB(5, 5, 5);
    uint8_t dl = rv & 0x03;
    uint8_t bri;
    switch (dl) {
        case 3: bri = 200; break;
        case 2: bri = 150; break;
        case 1: bri = 100; break;
        default: bri = 60; break;
    }
    uint8_t routes = stop_in_routes(addr, get_stop_led(stop_idx));
    if (routes == 3) return CRGB(bri/2, 0, bri/2);  // purple — both buses
    if (routes == 1) return CRGB(0,     0, bri);      // blue   — bus 0 only
    if (routes == 2) return CRGB(0,  bri,   0);       // green  — bus 1 only
    return CRGB(5, 5, 5);
}

// -- Bus state machine (unchanged) --------------------------------------------

struct Bus {
    uint8_t       state;
    uint8_t       stop_idx;
    uint8_t       path_id;
    uint8_t       path_step;
    uint8_t       path_len;
    unsigned long dwell_start;
    unsigned long move_start;
};

Bus buses[3];
CRGB    stop_current[N_STOPS];
CRGB    stop_target[N_STOPS];
uint8_t top_demand_stop = 0;
uint8_t cur_addr       = 0;
unsigned long last_udp_ms   = 0;
unsigned long demo_last_tick = 0;

void reset_bus(uint8_t b, uint8_t start_stop) {
    buses[b].state       = 0;
    buses[b].stop_idx    = start_stop;
    buses[b].path_id     = 0;
    buses[b].path_step   = 0;
    buses[b].path_len    = 1;
    buses[b].dwell_start = millis();
    buses[b].move_start  = millis();
}

uint8_t get_disp_led(uint8_t b) {
    if (buses[b].state == 0) {
        if (b < 2) return get_route_stop(cur_addr, b, buses[b].stop_idx);
        return get_stop_led(buses[b].stop_idx);
    }
    return path_rom_lookup(buses[b].path_id, buses[b].path_step);
}

uint8_t next_stop(uint8_t b) {
    if (b < 2) {
        uint8_t rlen = get_route_len(cur_addr, b);
        return (buses[b].stop_idx + 1 >= rlen) ? 0 : buses[b].stop_idx + 1;
    }
    return (buses[b].stop_idx == 14) ? 0 : buses[b].stop_idx + 1;
}

void update_bus(uint8_t b) {
    unsigned long now = millis();
    uint8_t cur_s, nxt_s;
    if (b < 2) {
        cur_s = get_route_stop(cur_addr, b, buses[b].stop_idx);
        nxt_s = get_route_stop(cur_addr, b, next_stop(b));
    } else {
        cur_s = get_stop_led(buses[b].stop_idx);
        nxt_s = get_stop_led(next_stop(b));
    }
    uint8_t rlen    = (b < 2) ? get_route_len(cur_addr, b) : 15;
    uint8_t jrn_pid = get_path_id(cur_s, nxt_s);
    uint8_t jrn_len = get_path_len(jrn_pid);

    if (buses[b].state == 0) {
        if (now - buses[b].dwell_start >= DWELL_MS) {
            if (rlen > 1 && jrn_len > 1) {
                buses[b].path_id    = jrn_pid;
                buses[b].path_len   = jrn_len;
                buses[b].path_step  = 1;
                buses[b].stop_idx   = next_stop(b);
                buses[b].state      = 1;
                buses[b].move_start = now;
            } else {
                buses[b].dwell_start = now;
            }
        }
    } else {
        if (now - buses[b].move_start >= MOVE_MS) {
            buses[b].move_start = now;
            if (buses[b].path_step >= buses[b].path_len - 1) {
                buses[b].state       = 0;
                buses[b].dwell_start = now;
                if (b < 2) {
                    uint8_t rlen_now = get_route_len(cur_addr, b);
                    if (buses[b].stop_idx >= rlen_now) buses[b].stop_idx = 0;
                }
            } else {
                buses[b].path_step++;
            }
        }
    }
}

void update_stop_targets() {
    uint8_t top_d = 0;
    top_demand_stop = 0;
    for (uint8_t i = 0; i < N_STOPS; i++) {
        stop_target[i] = get_stop_color(cur_addr, i);
        uint8_t d = get_demand(cur_addr, i);
        if (d > top_d) { top_d = d; top_demand_stop = i; }
    }
}

// -- Setup --------------------------------------------------------------------

void setup() {
    FastLED.addLeds<WS2812B, DATA_PIN, GRB>(leds, NUM_LEDS);
    FastLED.setBrightness(BRIGHTNESS);
    FastLED.clear(true);

    // WiFi connect, 10s timeout
    WiFi.begin(SSID, PASS);
    unsigned long wt = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - wt < 10000) {
        delay(500);
    }
    if (WiFi.status() == WL_CONNECTED) {
        udp.begin(UDP_PORT);
        wifi_ok = true;
    }

    reset_bus(0, 0);
    reset_bus(1, 4);
    reset_bus(2, 9);
    demo_last_tick = millis();
    last_udp_ms    = 0;   // start in demo until UDP arrives
    cur_addr       = 0;
    update_stop_targets();
}

// -- Main loop ----------------------------------------------------------------

void loop() {
    unsigned long now = millis();

    // Retry WiFi every 15s if not connected
    static unsigned long wifi_retry_ms = 0;
    if (!wifi_ok || WiFi.status() != WL_CONNECTED) {
        wifi_ok = false;
        if (now - wifi_retry_ms > 15000) {
            wifi_retry_ms = now;
            WiFi.begin(SSID, PASS);
        }
        if (WiFi.status() == WL_CONNECTED) {
            udp.begin(UDP_PORT);
            wifi_ok = true;
        }
    }

    // Receive UDP from Pi hub.py
    // Packet: [0xAA][addr][15 stop bytes][checksum] = 18 bytes
    if (wifi_ok) {
        int pkt = udp.parsePacket();
        if (pkt >= 18) {
            uint8_t buf[18];
            udp.read(buf, 18);
            if (buf[0] == 0xAA) {
                // Verify checksum (XOR of bytes 1-16)
                uint8_t chk = 0;
                for (int i = 1; i < 17; i++) chk ^= buf[i];
                if (chk == buf[17]) {
                    last_udp_ms = now;
                    uint8_t new_addr = buf[1] & 0x1F;
                    if (new_addr != cur_addr) {
                        uint8_t n0 = get_route_len(new_addr, 0);
                        uint8_t n1 = get_route_len(new_addr, 1);
                        uint8_t o0 = get_route_len(cur_addr, 0);
                        uint8_t o1 = get_route_len(cur_addr, 1);
                        // only reposition buses already at a stop; mid-transit ones
                        // finish their current path then clamp in update_bus
                        if (buses[0].state == 0) {
                            buses[0].stop_idx = min((uint8_t)((buses[0].stop_idx * n0) / o0), (uint8_t)(n0-1));
                            buses[0].dwell_start = millis();
                        }
                        if (buses[1].state == 0) {
                            buses[1].stop_idx = min((uint8_t)((buses[1].stop_idx * n1) / o1), (uint8_t)(n1-1));
                            buses[1].dwell_start = millis();
                        }
                        cur_addr = new_addr;
                        update_stop_targets();
                    }
                }
            }
        }
    }

    // Fallback demo mode when no UDP for UDP_TIMEOUT_MS
    if (now - last_udp_ms > UDP_TIMEOUT_MS) {
        if (now - demo_last_tick >= DEMO_INTERVAL_MS) {
            demo_last_tick = now;
            uint8_t new_addr = (cur_addr + 1) & 0x1F;
            uint8_t n0 = get_route_len(new_addr, 0);
            uint8_t n1 = get_route_len(new_addr, 1);
            uint8_t o0 = get_route_len(cur_addr, 0);
            uint8_t o1 = get_route_len(cur_addr, 1);
            if (buses[0].state == 0) {
                buses[0].stop_idx = min((uint8_t)((buses[0].stop_idx * n0) / o0), (uint8_t)(n0-1));
                buses[0].dwell_start = millis();
            }
            if (buses[1].state == 0) {
                buses[1].stop_idx = min((uint8_t)((buses[1].stop_idx * n1) / o1), (uint8_t)(n1-1));
                buses[1].dwell_start = millis();
            }
            cur_addr = new_addr;
            update_stop_targets();
        }
    }

    update_bus(0);
    update_bus(1);
    update_bus(2);

    FastLED.clear();

    uint8_t breath = beatsin8(20, 80, 255);  // 20 BPM (~3s pulse), 80-255 range
    for (uint8_t i = 0; i < N_STOPS; i++) {
        for (uint8_t c = 0; c < 3; c++) {
            int16_t diff = (int16_t)stop_target[i].raw[c] - (int16_t)stop_current[i].raw[c];
            if      (diff >  5) stop_current[i].raw[c] += 5;
            else if (diff < -5) stop_current[i].raw[c] -= 5;
            else                stop_current[i].raw[c]  = stop_target[i].raw[c];
        }
        CRGB col = stop_current[i];
        if (i == top_demand_stop) col.nscale8(breath);
        uint8_t led = get_stop_led(i);
        if (led < NUM_LEDS) leds[led] = col;
    }

    uint8_t d2 = get_disp_led(2);
    uint8_t d1 = get_disp_led(1);
    uint8_t d0 = get_disp_led(0);
    if (d2 < NUM_LEDS) leds[d2] = CRGB::Cyan;
    if (d1 < NUM_LEDS) leds[d1] = CRGB::Yellow;
    if (d0 < NUM_LEDS) leds[d0] = CRGB::White;

    // LED 0 (back of board): connection status
    if (!wifi_ok)
        leds[0] = CRGB(40, 0, 0);      // red   — no WiFi
    else if (now - last_udp_ms > UDP_TIMEOUT_MS)
        leds[0] = CRGB(40, 40, 0);     // yellow — WiFi ok, demo mode (no UDP)
    else
        leds[0] = CRGB(0, 40, 0);      // green  — live UDP from Pi

    FastLED.show();
    delay(20);
}
