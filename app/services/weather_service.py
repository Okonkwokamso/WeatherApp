import httpx
import os
from dotenv import load_dotenv
import json
from upstash_redis import Redis
from typing import Any, Dict

load_dotenv()

API_KEY: str = os.getenv("TOMORROW_API_KEY", "")
print(f"API_KEY: {API_KEY}")

async def get_weather(city: str, redis: Redis) -> Dict[str, Any]:
  cache_key = f"weather:{city.lower()}"

  cached_data: str | None = await redis.get(cache_key)

  if cached_data:
    return json.loads(cached_data)
  
  url = (
    f"https://api.tomorrow.io/v4/weather/realtime"
    f"?location={city}&apikey={API_KEY}"
  )

  async with httpx.AsyncClient() as client:
    response = await client.get(url)
    response.raise_for_status()
    weather_data: Dict[str, Any] =  response.json()

  await redis.set(cache_key, json.dumps(weather_data), ex=600)

  print(f"Weather data for {city}:", weather_data)

  return weather_data
