#from redis.asyncio import Redis 
from upstash_redis import Redis
import os
from dotenv import load_dotenv

load_dotenv()

redis_url: str = os.getenv("REDIS_URL")
redis_token: str = os.getenv("REDIS_TOKEN")
print(f"REDIS_TOKEN: {redis_token}")

print(f"REDIS_URL: {redis_url}")

# redis_client: Redis = Redis.from_url(REDIS_URL, decode_responses=True)

redis = Redis(url="redis_url", token="redis_token")
