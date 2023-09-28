import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import click
import openai
import requests


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
            current_time=datetime.now(),
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

    def description(self) -> str:
        return "\n".join(
            [
                f"Local time: {self.current_time}, Sunrise time: {self.sunrise_time}, Sunset time: {self.sunset_time}",
                f"Temperature: {self.temperature_celcius} celcius, feels like {self.temperature_feels_like}",
                f"Pressure {self.pressure} hPa; Humidity: {self.humidity} %",
                f"Clouds: {self.clouds_percent} %",
                f"Wind speed {self.wind_speed_msec} m/sec"
                + (
                    ""
                    if self.wind_gust_msec is None
                    else f" with gusts {self.wind_gust_msec}"
                ),
                (
                    "No rain"
                    if self.rain_volume_mm is None
                    else f"Rain volume {self.rain_volume_mm} mm in last {self.rain_period_hours} hours"
                ),
                (
                    "No snow"
                    if self.snow_volume_mm is None
                    else f"Snow volume {self.snow_volume_mm} mm in last {self.snow_period_hours} hours"
                ),
            ]
        )


def current_weather() -> Weather:
    response = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"lat": latitude, "lon": longitude, "appid": owm_key, "units": "metric"},
    )
    response.raise_for_status()
    return Weather.from_openweathermap(response.json())


def what_to_wear(weather: Weather, activity: str) -> str:
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Be coincise",
            },
            {
                "role": "user",
                "content": "Recommend what to wear.\n"
                + "Current weather:\n"
                + weather.description()
                + "\n"
                + f"Activity: {activity}",
            },
        ],
    )
    return completion["choices"][0]["message"]["content"]


@click.command()
@click.option("-a", "--activity", type=str, default="30 minutes walk in the park")
def cli(activity: Optional[str]):
    weather = current_weather()
    click.echo(weather.description())
    click.echo(what_to_wear(weather, activity))
