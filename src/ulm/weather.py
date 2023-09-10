import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import click
import dotenv
import requests

dotenv.load_dotenv()

latitude = os.environ["LOCATION_LATITUDE"]
longitude = os.environ["LOCATION_LONGITUDE"]
owm_key = os.environ["OPENWEATHERMAP_KEY"]


@dataclass
class Weather:
    current_time: datetime
    datapoint_time: datetime
    sunrise_time: datetime
    sunset_time: datetime

    temperature_celcius: float
    temperature_feels_like: float
    pressure: int
    humidity: int

    wind_speed_msec: float
    wind_gust_msec: Optional[float]

    clouds_percent: int

    rain_volume_mm: Optional[float]
    rain_period_hours: Optional[int]

    snow_volume_mm: Optional[float]
    snow_period_hours: Optional[int]

    @classmethod
    def from_openweathermap(cls, vals: dict) -> "Weather":
        rain_1h = vals.get("rain", {}).get("1h")
        rain_3h = vals.get("rain", {}).get("3h")
        if "rain" in vals:
            rain_period_hours = {"1h": 1, "3h": 3}.get(max(vals.get("rain", {}).keys()))
        else:
            rain_period_hours = None

        snow_1h = vals.get("snow", {}).get("1h")
        snow_3h = vals.get("snow", {}).get("3h")
        if "snow" in vals:
            snow_period_hours = {"1h": 1, "3h": 3}.get(max(vals.get("snow", {}).keys()))
        else:
            snow_period_hours = None

        return cls(
            current_time=datetime.utcnow(),
            datapoint_time=datetime.fromtimestamp(vals["dt"]),
            sunrise_time=datetime.fromtimestamp(vals["sys"]["sunrise"]),
            sunset_time=datetime.fromtimestamp(vals["sys"]["sunset"]),
            temperature_celcius=vals["main"]["temp"],
            temperature_feels_like=vals["main"]["feels_like"],
            pressure=vals["main"]["pressure"],
            humidity=vals["main"]["humidity"],
            wind_speed_msec=vals["wind"]["speed"],
            wind_gust_msec=vals["wind"].get("gust"),
            clouds_percent=vals["clouds"]["all"],
            rain_volume_mm=rain_1h or rain_3h,
            rain_period_hours=rain_period_hours,
            snow_volume_mm=snow_1h or snow_3h,
            snow_period_hours=snow_period_hours,
        )


def current_weather() -> Weather:
    response = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"lat": latitude, "lon": longitude, "appid": owm_key, "units": "metric"},
    )
    response.raise_for_status()
    return Weather.from_openweathermap(response.json())


@click.command()
def cli():
    click.echo(current_weather())
