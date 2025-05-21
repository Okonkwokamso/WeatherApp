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

async def get_weather(city: str, redis: Redis) -> Dict[str, Any]:

  cache_key = f"weather:{city.lower()}"

  cached_data: str | None = redis.get(cache_key)

  if cached_data:
    return httpx.Response(200, content=cached_data).json()
  
  params = {
    "location": city,
    "units": "metric"
  }

  headers = {
    "accept": "application/json",
    "apikey": API_KEY
  }
  
  url = (
    f"https://api.tomorrow.io/v4/weather/realtime"
    f"?location={city}&apikey={API_KEY}"
  )

  try:
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
      response = await client.get(url, params=params, headers=headers)
      response.raise_for_status()
      weather_data: Dict[str, Any] =  response.json()

      values = weather_data.get("data", {}).get("values")
      if not values:
        raise HTTPException(status_code=404, detail=f"No weather data found for '{city}'")

      # redis.set(cache_key, json.dumps(weather_data), ex=CACHE_TTL)

      redis.set(cache_key, json.dumps(weather_data), ex=CACHE_TTL)

      print(f"Weather data for {city}:", weather_data)

      return weather_data

  except httpx.RequestError as exc:
    print(f'Request error: {exc}')
    raise HTTPException(status_code=503, detail="Service unavailable")
  
  except httpx.HTTPStatusError as exc:
    print(f'API error: {exc.response.status_code} - {exc.response.text}')
    raise HTTPException(status_code=exc.response.status_code, detail="Error fetching weather data")







  return weather_data
