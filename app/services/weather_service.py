import httpx
import os
from fastapi import HTTPException
from dotenv import load_dotenv
import json
from upstash_redis import Redis
from typing import Any, Dict

load_dotenv()

API_KEY: str = os.getenv("TOMORROW_API_KEY", "")
CACHE_TTL = 3600
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
  

async def get_weather(location: str, redis: Redis) -> Dict[str, Any]:
  is_valid_city = await validate_city_with_geocoding(location)
  if not is_valid_city:
    raise HTTPException(status_code=404, detail=f"Invalid location: '{location}'")

  cache_key = f"weather:{location.lower()}"

  cached_data: str | None = redis.get(cache_key)

  if cached_data:
    print(f"Cache hit for {location}: {cached_data}")
    return httpx.Response(200, content=cached_data).json()
  
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

      return weather_data

  except httpx.RequestError as exc:
    print(f'Request error: {exc}')
    raise HTTPException(status_code=503, detail="Service unavailable")
  
  except httpx.HTTPStatusError as exc:
    print(f'API error: {exc.response.status_code} - {exc.response.text}')
    raise HTTPException(status_code=exc.response.status_code, detail="Error fetching weather data")

  return weather_data
