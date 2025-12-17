import json
from typing import Any, Optional

import redis.asyncio as redis

from src.settings import Settings
from src.utils.logging import get_logger

settings = Settings()
logger = get_logger("redis")

redis_pool: Optional[redis.ConnectionPool] = None


async def get_redis_client() -> redis.Redis:
    global redis_pool
    if redis_pool is None:
        try:
            redis_pool = redis.ConnectionPool.from_url(
                settings.redis_url,
                decode_responses=True,
                max_connections=10,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            # logger.info("Initialized Redis connection pool", url=settings.redis_url)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Failed to initialize Redis pool", url=settings.redis_url, exc_info=exc
            )
            raise
    client = redis.Redis(connection_pool=redis_pool)
    # Logger debug removed to reduce noise
    # logger.debug("Redis client ready", url=settings.redis_url)
    return client


async def close_redis_client():
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


def _get_session_key(user_id: int | str, session_id: str) -> str:
    return f"session:{user_id}:{session_id}"


async def store_session(
    user_id: int | str, session_id: str, data: dict[str, Any], ttl: int
) -> None:
    """
    Store session data in Redis with a TTL.
    """
    client = await get_redis_client()
    key = _get_session_key(user_id, session_id)
    await client.set(key, json.dumps(data), ex=ttl)


async def get_session(user_id: int | str, session_id: str) -> Optional[dict[str, Any]]:
    try:
        client = await get_redis_client()
        key = _get_session_key(user_id, session_id)
        data = await client.get(key)
        if data:
            return json.loads(data)
    except redis.RedisError as e:
        print(f"Redis error getting session: {e}")
        # logger.error(f"Redis error getting session: {e}")
        # Consider fallback to database or fail gracefully
    return None


async def delete_session(user_id: int | str, session_id: str) -> None:
    """
    Delete a specific session from Redis.
    """
    client = await get_redis_client()
    key = _get_session_key(user_id, session_id)
    await client.delete(key)


async def delete_all_sessions_for_user(user_id: int | str) -> None:
    """
    Delete all sessions for a user from Redis.
    """
    client = await get_redis_client()
    pattern = f"session:{user_id}:*"
    keys = await client.keys(pattern)
    if keys:
        await client.delete(*keys)
