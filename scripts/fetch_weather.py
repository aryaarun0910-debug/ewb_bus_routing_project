"""
fetch_weather.py
================
Pulls real historical hourly weather for Birmingham from Open-Meteo (free, no API key).
Covers 2023-01-01 to 2024-12-31 -- two full years of observed data.

Variables fetched
-----------------
  temperature_2m          degrees C
  precipitation           mm/hr
  windspeed_10m           km/h
  weathercode             WMO code (maps to sunny/cloudy/rain/storm)

Output
------
  data/weather/birmingham_hourly_2023_2024.csv
  data/weather/birmingham_daily_summary_2023_2024.csv

The hourly CSV can directly replace synthetic weather columns in the
demand dataset. The daily summary gives season/month aggregates.

Usage
-----
  python scripts/fetch_weather.py

No dependencies beyond requests (in requirements.txt).
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path

import requests

_REPO = Path(__file__).parent.parent
OUT_DIR = _REPO / "data" / "weather"
OUT_HOURLY = OUT_DIR / "birmingham_hourly_2023_2024.csv"
OUT_DAILY  = OUT_DIR / "birmingham_daily_summary_2023_2024.csv"

# Birmingham city centre coordinates
LAT = 52.4814
LON = -1.8998

# WMO weather code -> our model's weather_type categories
WMO_TO_WEATHER: dict[int, str] = {
    0:  "sunny",   # Clear sky
    1:  "sunny",   # Mainly clear
    2:  "cloudy",  # Partly cloudy
    3:  "cloudy",  # Overcast
    45: "cloudy",  # Fog
    48: "cloudy",  # Icy fog
    51: "light_rain", 53: "light_rain", 55: "light_rain",
    61: "light_rain", 63: "heavy_rain", 65: "heavy_rain",
    71: "light_rain", 73: "heavy_rain", 75: "heavy_rain",
    77: "heavy_rain",
    80: "light_rain", 81: "heavy_rain", 82: "heavy_rain",
    85: "heavy_rain", 86: "heavy_rain",
    95: "storm",   # Thunderstorm
    96: "storm",   97: "storm", 98: "storm", 99: "storm",
}

YEARS = [("2023-01-01", "2023-12-31"), ("2024-01-01", "2024-12-31")]


def fetch_year(start: str, end: str) -> dict:
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude":        LAT,
        "longitude":       LON,
        "start_date":      start,
        "end_date":        end,
        "hourly":          "temperature_2m,precipitation,windspeed_10m,weathercode",
        "timezone":        "Europe/London",
        "wind_speed_unit": "kmh",
    }
    print(f"  Fetching {start} to {end}...")
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def wmo_to_weather(code: int) -> str:
    return WMO_TO_WEATHER.get(int(code), "cloudy")


def is_storm(code: int) -> int:
    return 1 if int(code) >= 95 else 0


def season(month: int) -> str:
    if month in (12, 1, 2):  return "winter"
    if month in (3, 4, 5):   return "spring"
    if month in (6, 7, 8):   return "summer"
    return "autumn"


def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict] = []

    for start, end in YEARS:
        data = fetch_year(start, end)
        h = data["hourly"]
        times      = h["time"]
        temps      = h["temperature_2m"]
        precips    = h["precipitation"]
        winds      = h["windspeed_10m"]
        wmo_codes  = h["weathercode"]

        for i, ts in enumerate(times):
            # ts format: "2023-01-01T00:00"
            date_part, time_part = ts.split("T")
            year, month, day = date_part.split("-")
            hour = int(time_part.split(":")[0])

            wmo  = wmo_codes[i] if wmo_codes[i] is not None else 0
            temp = temps[i]     if temps[i]     is not None else 10.0
            prec = precips[i]   if precips[i]   is not None else 0.0
            wind = winds[i]     if winds[i]      is not None else 10.0

            all_rows.append({
                "date":          date_part,
                "year":          int(year),
                "month":         int(month),
                "day":           int(day),
                "hour":          hour,
                "season":        season(int(month)),
                "temperature_c": round(float(temp), 1),
                "precipitation_mm": round(float(prec), 2),
                "wind_kmh":      round(float(wind), 1),
                "wmo_code":      int(wmo),
                "weather_type":  wmo_to_weather(wmo),
                "is_storm":      is_storm(wmo),
            })

        time.sleep(1)  # be polite to the API

    # Write hourly CSV
    fieldnames = [
        "date", "year", "month", "day", "hour", "season",
        "temperature_c", "precipitation_mm", "wind_kmh",
        "wmo_code", "weather_type", "is_storm",
    ]
    with open(OUT_HOURLY, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nWrote {len(all_rows):,} hourly rows -> {OUT_HOURLY}")

    # Daily summary
    from collections import defaultdict
    daily: dict[str, list] = defaultdict(list)
    for r in all_rows:
        daily[r["date"]].append(r)

    daily_rows = []
    for date, rows in sorted(daily.items()):
        temps  = [r["temperature_c"]    for r in rows]
        precip = [r["precipitation_mm"] for r in rows]
        winds  = [r["wind_kmh"]         for r in rows]
        # Most common weather type
        from collections import Counter
        weather_counts = Counter(r["weather_type"] for r in rows)
        dominant_weather = weather_counts.most_common(1)[0][0]

        daily_rows.append({
            "date":            date,
            "year":            rows[0]["year"],
            "month":           rows[0]["month"],
            "season":          rows[0]["season"],
            "temp_mean_c":     round(sum(temps) / len(temps), 1),
            "temp_max_c":      round(max(temps), 1),
            "temp_min_c":      round(min(temps), 1),
            "precip_total_mm": round(sum(precip), 1),
            "wind_max_kmh":    round(max(winds), 1),
            "dominant_weather": dominant_weather,
            "storm_hours":     sum(r["is_storm"] for r in rows),
        })

    daily_fields = [
        "date", "year", "month", "season",
        "temp_mean_c", "temp_max_c", "temp_min_c",
        "precip_total_mm", "wind_max_kmh", "dominant_weather", "storm_hours",
    ]
    with open(OUT_DAILY, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=daily_fields)
        writer.writeheader()
        writer.writerows(daily_rows)

    print(f"Wrote {len(daily_rows):,} daily rows -> {OUT_DAILY}")

    # Quick summary stats
    bus_weather = {}
    for wt in ["sunny", "cloudy", "light_rain", "heavy_rain", "storm"]:
        count = sum(1 for r in all_rows if r["weather_type"] == wt)
        bus_weather[wt] = round(100 * count / len(all_rows), 1)

    print("\nBirmingham weather distribution (2023-2024):")
    for wt, pct in bus_weather.items():
        bar = "#" * int(pct / 2)
        print(f"  {wt:<12} {pct:>5.1f}%  {bar}")


if __name__ == "__main__":
    run()
