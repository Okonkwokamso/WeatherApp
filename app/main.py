from fastapi import FastAPI, HTTPException, Query, Depends
from app.services.weather_service import get_weather
from typing import Any, Dict
from .utils.redis_client import redis_client

app = FastAPI(title="Weather API")

@app.get("/")
async def welcome():
  return {
    "message": "Welcome to your weather buddy",
    "status": "success",
    "documentation": "Visit /docs for API documentation."
  }

@app.get("/weather/")
async def weather(location: str = Query(..., min_length=2)):

  try:
    weather_data = await get_weather(location, redis_client)

    return weather_data

  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
                    