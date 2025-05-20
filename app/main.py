from fastapi import FastAPI, HTTPException, Query, Depends
from redis.asyncio import Redis
from app.services.weather_service import get_weather
from typing import Any, Dict
from .utils.redis_client import redis_client

app = FastAPI(title="Weather API")

# def get_redis_client() -> Redis:
#   return redis_client

@app.get("/weather/")
async def weather(city: str = Query(..., min_length=2)):

  try:
    weather_data = await get_weather(city, redis_client)

    # return {
    #   "location": city,
    #   "data": weather_data.get("data", {})
    # }
    return {
      "city": city,
      "temperature": weather_data["data"]["values"]["temperature"],
      "humidity": weather_data["data"]["values"]["humidity"],
      "wind_speed": weather_data["data"]["values"]["windSpeed"],
      "rainIntensity": weather_data["data"]["values"]["rainIntensity"],
    }
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
                    