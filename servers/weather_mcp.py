from fastmcp import FastMCP
import httpx

mcp = FastMCP("weather")

@mcp.tool()
async def get_weather(city: str) -> str:
    """Get current weather and today's forecast for a city."""
    
    # Step 1: get coordinates for the city
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    async with httpx.AsyncClient() as client:
        geo = await client.get(geo_url)
        geo_data = geo.json()

    if not geo_data.get("results"):
        return f"Could not find city: {city}"

    result = geo_data["results"][0]
    lat = result["latitude"]
    lon = result["longitude"]
    name = result["name"]
    country = result.get("country", "")

    # Step 2: get weather for those coordinates
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,weathercode,windspeed_10m"
        f"&daily=temperature_2m_max,temperature_2m_min,weathercode"
        f"&timezone=auto&forecast_days=1"
    )
    async with httpx.AsyncClient() as client:
        weather = await client.get(weather_url)
        w = weather.json()

    current = w["current"]
    daily = w["daily"]

    code = current["weathercode"]
    condition = weather_code_to_text(code)

    return (
        f"Weather in {name}, {country}:\n"
        f"Now: {current['temperature_2m']}°C, {condition}\n"
        f"Wind: {current['windspeed_10m']} km/h\n"
        f"Today: Low {daily['temperature_2m_min'][0]}°C / High {daily['temperature_2m_max'][0]}°C"
    )

def weather_code_to_text(code: int) -> str:
    codes = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Foggy", 48: "Icy fog", 51: "Light drizzle", 53: "Drizzle",
        61: "Light rain", 63: "Rain", 65: "Heavy rain",
        71: "Light snow", 73: "Snow", 75: "Heavy snow",
        80: "Rain showers", 81: "Showers", 82: "Heavy showers",
        95: "Thunderstorm"
    }
    return codes.get(code, f"Code {code}")

if __name__ == "__main__":
    mcp.run()
