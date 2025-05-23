import httpx
import os
from fastapi import HTTPException
from dotenv import load_dotenv
import json
from upstash_redis import Redis
from typing import Any, Dict

load_dotenv()

API_KEY: str = os.getenv("TOMORROW_API_KEY", "")
CACHE_TTL = 600
print(f"API_KEY: {API_KEY}")


async def validate_city_with_geocoding(location: str) -> bool:
 
  url = "https://nominatim.openstreetmap.org/search?<params>"
  params = {
    "q": location,
    "format": "json",
    "addressdetails": 1,
    "limit": 1
  }
  headers = {
    "User-Agent": "WeatherApp/1.0"
  }
  async with httpx.AsyncClient(timeout=10.0) as client:
    response = await client.get(url, params=params, headers=headers)
    response.raise_for_status()
    data = response.json()

    print(f"Geocoding data for {location}:", data)

    valid_types = {"city", "town", "village", "hamlet", "suburb", "state", "country", "administrative", "province", "region", "island", "territory", "county", "municipality"}
    
    if data:
      place_type = data[0].get("type", "")
      address_type = data[0].get("addresstype", "")
      if place_type in valid_types or address_type in valid_types:
        return True
    return False
  

def format_weather_response(location: str, weather_data: dict) -> dict:
  values = weather_data["data"]["values"]
  advice = []

  # Example derived advice
  if values.get("rainIntensity", 0) > 0:
    advice.append("You might want to grab that umbrella just incase ☔")
  if values.get("temperature", 0) > 35:
    advice.append("Drink water, Stay sharp 😎")
  if values.get("temperature", 0) < 10:
    advice.append("Dress warmly or you'll get cold 🥶")
  if values.get("windSpeed", 0) > 10:
    advice.append("It's windy, please don't get blown away 🌬️")

  return {
    "location": location,
    "temperature": values.get("temperature"),
    "humidity": values.get("humidity"),
    "wind_speed": values.get("windSpeed"),
    "rain_intensity": values.get("rainIntensity"),
    "advice": advice or ["No special advice."]
  }

async def get_weather(location: str, redis: Redis) -> Dict[str, Any]:
  is_valid_city = await validate_city_with_geocoding(location)
  if not is_valid_city:
    raise HTTPException(status_code=404, detail=f"Invalid location: '{location}'")

  cache_key = f"weather:{location.lower()}"

  cached_data: str | None = redis.get(cache_key)

  if cached_data:
    print(f"Cache hit for {location}: {cached_data}")
    weather_data = httpx.Response(200, content=cached_data).json()
    return format_weather_response(location, weather_data)
  
  params = {
    "location": location,
    "units": "metric"
  }

  headers = {
    "accept": "application/json",
    "apikey": API_KEY
  }
  
  url = (
    f"https://api.tomorrow.io/v4/weather/realtime"
    f"?location={location}&apikey={API_KEY}"
  )

  try:
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
      response = await client.get(url, params=params, headers=headers)
      response.raise_for_status()
      weather_data: Dict[str, Any] =  response.json()

      if (
          "data" not in weather_data or
          "values" not in weather_data["data"] or
          not weather_data["data"]["values"]
      ):
          raise HTTPException(status_code=404, detail=f"No weather data found for '{location}'")

      # redis.set(cache_key, json.dumps(weather_data), ex=CACHE_TTL)

      redis.set(cache_key, json.dumps(weather_data), ex=CACHE_TTL)

      print(f"Weather data for {location}:", weather_data)

      return format_weather_response(location, weather_data)

  except httpx.RequestError as exc:
    print(f'Request error: {exc}')
    raise HTTPException(status_code=503, detail="Service unavailable")
  
  except httpx.HTTPStatusError as exc:
    print(f'API error: {exc.response.status_code} - {exc.response.text}')
    raise HTTPException(status_code=exc.response.status_code, detail="Error fetching weather data")

  return weather_data
