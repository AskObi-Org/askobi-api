# Domain: auth

## What this domain does

This domain controls:

- Who a user is (identity)
- How they prove it (password + tokens)
- How the server remembers their login (per-device sessions)

The design is a hybrid of:

- Stateless JWT access tokens (fast, no DB on each request)
- Stateful session validation (Redis + DB) for security and revocation

## Key files

- `src/utils/tokens.py` (JWT + refresh token hashing)
- `src/auth/dependencies.py` (request-time auth checks)
- `src/services/auth_service.py` (session lifecycle / refresh / revoke)
- `src/utils/authorization.py` (bcrypt password hashing)

## Observed patterns (with exact code)

### Access tokens contain `sub` (user_id) and `sid` (session_id)

From `src/utils/tokens.py`:

```python
def create_access_token(user_id: int | str, session_id: str, auth_time: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.AUTH_JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(user_id),
        "sid": session_id,
        "auth_time": auth_time,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    encoded_jwt = jwt.encode(to_encode, settings.AUTH_JWT_SECRET_KEY, algorithm=settings.AUTH_JWT_ALGORITHM)
    return encoded_jwt
```

### Refresh tokens are opaque + only stored hashed

From `src/utils/tokens.py`:

```python
def create_refresh_token(user_id: int | str, session_id: str) -> Tuple[str, str]:
    raw_token = secrets.token_urlsafe(64)
    hashed_token = hash_refresh_token(raw_token)
    return raw_token, hashed_token
```

### Protected endpoints validate Redis session + token_version

From `src/auth/dependencies.py`:

```python
session_data = await redis.get_session(user_id, session_id)
if not session_data:
    raise credentials_exception

result = await db.execute(select(User).where(User.id == user_id))
user = result.scalars().first()
...
session_token_version = session_data.get("token_version")
if session_token_version is not None and session_token_version != user.token_version:
    raise credentials_exception
```

## How session creation works

The service creates a DB session row and a Redis cache entry.

From `src/services/auth_service.py`:

```python
db_session = UserSession(
    user_id=user.id,
    session_id=session_id,
    refresh_token_hash=hashed_refresh_token,
    device_name=device_name,
    ip_address=ip_address,
    user_agent=user_agent,
    expires_at=expires_at,
    is_active=True,
)
await self.session_repo.create(db_session)

session_data = {
    "user_id": user.id,
    "token_version": user.token_version,
    "device_name": device_name,
    "ip_address": ip_address,
    "user_agent": user_agent,
    "created_at": auth_time,
}
ttl = settings.AUTH_JWT_REFRESH_TOKEN_EXPIRE_MINUTES * 60
await redis.store_session(user.id, session_id, session_data, ttl)
```

## Review Carefully

- `src/services/session_service.py` implements a second, function-based session flow that partially overlaps with `AuthService`. Treat it as legacy/alternate until you confirm which one is authoritative.
- Any changes to token payloads require updating all readers (dependencies, services).
