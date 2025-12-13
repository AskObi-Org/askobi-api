import json
from typing import Any, Optional
import redis.asyncio as redis
from src.settings import Settings

settings = Settings()

redis_pool: Optional[redis.ConnectionPool] = None


async def get_redis_client() -> redis.Redis:
    global redis_pool
    if redis_pool is None:
        redis_pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            max_connections=10,
            socket_connect_timeout=5,
            socket_keepalive=True,
        )
    return redis.Redis(connection_pool=redis_pool)


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
