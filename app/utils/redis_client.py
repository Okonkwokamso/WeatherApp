from redis.asyncio import Redis 
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL: str = os.getenv("REDIS_URL")

print(f"REDIS_URL: {REDIS_URL}")

redis_client: Redis = Redis.from_url(REDIS_URL, decode_responses=True)
