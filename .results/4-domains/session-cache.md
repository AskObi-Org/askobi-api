# Domain: session-cache

## What this domain does

Redis acts as the fast “are you still logged in?” check.

- DB is the source of truth for session listing and device management.
- Redis is the high-speed gatekeeper for API requests.

## Key files

- `src/utils/redis.py`
- `src/auth/dependencies.py`
- `src/services/auth_service.py`

## Observed patterns

### Redis session key format

From `src/utils/redis.py`:

```python
def _get_session_key(user_id: int | str, session_id: str) -> str:
    return f"session:{user_id}:{session_id}"
```

### Values are JSON blobs with TTL

From `src/utils/redis.py`:

```python
await client.set(key, json.dumps(data), ex=ttl)
```

### Auth depends on Redis session presence

From `src/auth/dependencies.py`:

```python
session_data = await redis.get_session(user_id, session_id)
if not session_data:
    raise credentials_exception
```

## Review Carefully

- If Redis is unavailable, the current `get_session` implementation catches Redis errors and returns `None`, which results in authentication failure. That’s generally safer than “fail open”, but it’s operationally important.
