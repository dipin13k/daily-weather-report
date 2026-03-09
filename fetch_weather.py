import urllib.request
import json
from datetime import datetime, timezone, timedelta

# Cities with coordinates and UTC offsets
CITIES = [
    {"name": "Kathmandu", "country": "Nepal",     "emoji": "🇳🇵", "lat": 27.7172,  "lon": 85.3240,   "tz_offset": 5.75,  "tz_name": "NPT"},
    {"name": "New Delhi", "country": "India",     "emoji": "🇮🇳", "lat": 28.6139,  "lon": 77.2090,   "tz_offset": 5.5,   "tz_name": "IST"},
    {"name": "New York",  "country": "USA",        "emoji": "🇺🇸", "lat": 40.7128,  "lon": -74.0060,  "tz_offset": -4.0,  "tz_name": "EDT"},
    {"name": "Sydney",    "country": "Australia",  "emoji": "🇦🇺", "lat": -33.8688, "lon": 151.2093,  "tz_offset": 10.0,  "tz_name": "AEST"},
    {"name": "Lagos",     "country": "Nigeria",    "emoji": "🇳🇬", "lat": 6.5244,   "lon": 3.3792,    "tz_offset": 1.0,   "tz_name": "WAT"},
]

WMO_CODES = {
    0: "Clear Sky ☀️", 1: "Mainly Clear 🌤️", 2: "Partly Cloudy ⛅", 3: "Overcast ☁️",
    45: "Foggy 🌫️", 48: "Icy Fog 🌫️",
    51: "Light Drizzle 🌦️", 53: "Drizzle 🌦️", 55: "Heavy Drizzle 🌧️",
    61: "Light Rain 🌧️", 63: "Rain 🌧️", 65: "Heavy Rain 🌧️",
    71: "Light Snow 🌨️", 73: "Snow 🌨️", 75: "Heavy Snow ❄️",
    80: "Rain Showers 🌦️", 81: "Rain Showers 🌦️", 82: "Violent Showers ⛈️",
    95: "Thunderstorm ⛈️", 96: "Thunderstorm + Hail ⛈️", 99: "Thunderstorm + Hail ⛈️",
}

def get_local_time(tz_offset):
    offset = timedelta(hours=tz_offset)
    local_dt = datetime.now(timezone.utc) + offset
    return local_dt.strftime("%I:%M %p"), local_dt.strftime("%A, %b %d %Y")

def get_time_of_day(tz_offset):
    offset = timedelta(hours=tz_offset)
    local_dt = datetime.now(timezone.utc) + offset
    hour = local_dt.hour
    if 5 <= hour < 12:  return "🌅 Morning"
    elif 12 <= hour < 17: return "☀️ Afternoon"
    elif 17 <= hour < 21: return "🌇 Evening"
    else:               return "🌙 Night"

def fetch_weather(city):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={city['lat']}&longitude={city['lon']}"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,"
        f"apparent_temperature,precipitation,weathercode,uv_index"
        f"&wind_speed_unit=kmh&timezone=auto"
    )
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode())

def build_report():
    now_utc = datetime.now(timezone.utc)
    utc_str = now_utc.strftime("%Y-%m-%d %H:%M UTC")
    slot    = "🌅 Morning" if now_utc.hour < 12 else "🌆 Evening"

    lines = []
    lines.append("# 🌍 Live World Weather Report\n")
    lines.append(f"> **{slot} Update** — {utc_str}\n")
    lines.append("> Auto-updated twice daily via GitHub Actions • Powered by [Open-Meteo](https://open-meteo.com/)\n")
    lines.append("---\n")

    # Summary table
    lines.append("## 📊 Quick Overview\n")
    lines.append("| # | City | Country | 🕐 Local Time | 🌡️ Temp | 🌤️ Condition |")
    lines.append("|---|------|---------|--------------|--------|-------------|")

    city_data = []
    for city in CITIES:
        try:
            data   = fetch_weather(city)
            cur    = data["current"]
            temp   = cur["temperature_2m"]
            feels  = cur["apparent_temperature"]
            humid  = cur["relative_humidity_2m"]
            wind   = cur["wind_speed_10m"]
            precip = cur["precipitation"]
            wcode  = cur.get("weathercode", 0)
            uv     = cur.get("uv_index", "N/A")
            cond   = WMO_CODES.get(wcode, "Unknown")
            unit   = data["current_units"]["temperature_2m"]
            t_time, t_date = get_local_time(city["tz_offset"])
            tod    = get_time_of_day(city["tz_offset"])

            city_data.append({**city, "temp": temp, "feels": feels, "humid": humid,
                               "wind": wind, "precip": precip, "cond": cond,
                               "unit": unit, "t_time": t_time, "t_date": t_date,
                               "tod": tod, "uv": uv})

            lines.append(f"| {city['emoji']} | **{city['name']}** | {city['country']} | {t_time} {city['tz_name']} | {temp}{unit} | {cond} |")
        except Exception as e:
            lines.append(f"| {city['emoji']} | **{city['name']}** | {city['country']} | — | — | ⚠️ Error |")
            city_data.append(None)

    lines.append("")
    lines.append("---\n")

    # Detailed cards
    lines.append("## 🗺️ Detailed Weather Cards\n")
    for cd in city_data:
        if not cd:
            continue
        lines.append(f"### {cd['emoji']} {cd['name']}, {cd['country']}\n")
        lines.append(f"**{cd['tod']} &nbsp;|&nbsp; 🕐 {cd['t_time']} {cd['tz_name']} &nbsp;|&nbsp; 📅 {cd['t_date']}**\n")
        lines.append(f"| 🌡️ Temperature | 🤔 Feels Like | 💧 Humidity | 💨 Wind | 🌧️ Precipitation | 🔆 UV Index |")
        lines.append(f"|--------------|--------------|------------|--------|-----------------|------------|")
        lines.append(f"| **{cd['temp']}{cd['unit']}** | {cd['feels']}{cd['unit']} | {cd['humid']}% | {cd['wind']} km/h | {cd['precip']} mm | {cd['uv']} |")
        lines.append(f"\n> {cd['cond']}\n")
        lines.append("")

    lines.append("---")
    lines.append("\n<div align='center'>\n")
    lines.append(f"⏱️ *Next update in ~12 hours &nbsp;•&nbsp; Last run: {utc_str}*\n")
    lines.append("</div>")

    return "\n".join(lines)

if __name__ == "__main__":
    print("⏳ Fetching weather data...")
    report = build_report()
    with open("weather/WEATHER.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("✅ Report written to weather/WEATHER.md")
