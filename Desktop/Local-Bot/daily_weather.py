# Daily Weather Report
import os
import requests
from dotenv import load_dotenv
from slack_sdk import WebClient

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "C0ALKP89QQP")
WEATHER_CITY = os.getenv("WEATHER_CITY", "San Francisco")

slack_client = WebClient(token=SLACK_BOT_TOKEN)


def get_coordinates(city_name: str):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": city_name,
        "count": 1,
        "language": "en",
        "format": "json",
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()

    results = data.get("results", [])
    if not results:
        raise ValueError(f"Could not find city: {city_name}")

    place = results[0]
    return {
        "name": place["name"],
        "state": place.get("admin1", ""),
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "timezone": place.get("timezone", "auto"),
    }


def get_weather(lat: float, lon: float, timezone: str):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min",
        "current": "temperature_2m,apparent_temperature,weather_code",
        "timezone": timezone,
        "forecast_days": 2,
        "temperature_unit": "fahrenheit",
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def weather_code_to_text(code: int) -> str:
    mapping = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        61: "Rain",
        63: "Moderate rain",
        65: "Heavy rain",
        80: "Rain showers",
        95: "Thunderstorm",
    }
    return mapping.get(code, "Unknown")


def build_report(city: str, state: str, weather_data: dict) -> str:
    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})

    current_temp = current.get("temperature_2m")
    feels_like = current.get("apparent_temperature")
    current_code = current.get("weather_code", -1)

    today_high = daily.get("temperature_2m_max", [None])[0]
    today_low = daily.get("temperature_2m_min", [None])[0]

    tomorrow_high = daily.get("temperature_2m_max", [None, None])[1]
    tomorrow_low = daily.get("temperature_2m_min", [None, None])[1]

    outlook = weather_code_to_text(current_code)

    return (
        f"Good morning. Today's weather for *{city}, {state}*:\n"
        f"• Current Temp: {current_temp}°F\n"
        f"• High / Low: {today_high}°F / {today_low}°F\n"
        f"• Feels Like: {feels_like}°F\n"
        f"• Outlook: {outlook}\n\n"
        f"Tomorrow:\n"
        f"• High / Low: {tomorrow_high}°F / {tomorrow_low}°F"
    )


def post_to_slack(message: str):
    slack_client.chat_postMessage(
        channel=SLACK_CHANNEL,
        text=message,
    )


def main():
    place = get_coordinates(WEATHER_CITY)
    weather = get_weather(
        place["latitude"],
        place["longitude"],
        place["timezone"],
    )

    report = build_report(
        place["name"],
        place["state"],
        weather
    )

    post_to_slack(report)
    print("Weather report sent successfully.")


if __name__ == "__main__":
    main()
