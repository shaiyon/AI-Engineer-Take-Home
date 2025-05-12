import os

from dotenv import load_dotenv
from redis.asyncio import Redis

load_dotenv()

_redis_client: Redis | None = None


def get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis(
            host=os.getenv("REDIS_HOST"),
            decode_responses=True,
        )
    return _redis_client
