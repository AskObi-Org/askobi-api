# Plan: HIPAA/GDPR Auth Architecture for AskObi

**TL;DR**: Implement Reference-Based JWTs with Redis session validation, dual-write to PostgreSQL for device management, step-up auth for sensitive health data, and audit logging for compliance. Enables instant revocation (<1ms) while supporting multi-device sessions and biometric unlock flows.

---

## Current State

| Component                 | Status                      | Location              |
| ------------------------- | --------------------------- | --------------------- |
| JWT/Redis Settings        | ✅ Ready                    | `src/settings.py`     |
| User + UserSession Models | ✅ Ready                    | `src/models/users.py` |
| Auth folder               | ⚠️ Empty                    | `src/auth/`           |
| Redis client              | ❌ Missing                  | —                     |
| Repositories folder       | ❌ Missing                  | —                     |
| Services folder           | ❌ Missing                  | —                     |
| Middleware folder         | ❌ Missing                  | —                     |
| Dependencies              | ⚠️ Missing `redis`, `PyJWT` | `pyproject.toml`      |

**⚠️ HIPAA Risk**: Current `ACCESS_TOKEN_EXPIRE_MINUTES = 11520` (8 days) is too long. Change to 15 minutes.

---

## Steps

### 1. Update settings + add dependencies

In `src/settings.py`, change lines 37-38:

```python
AUTH_JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Short-lived for HIPAA compliance
AUTH_JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
```

Run:

```powershell
poetry add PyJWT "redis[hiredis]"
```

Create folders:

```powershell
New-Item -ItemType Directory -Path src/repositories, src/services, src/middleware -Force
```

---

### 2. Implement Redis session store → `src/utils/redis.py`

- Async Redis client with `redis.asyncio`
- Functions: `store_session`, `get_session`, `delete_session`, `delete_all_sessions_for_user`
- Key pattern: `session:{user_id}:{session_id}` with TTL matching refresh expiry

---

### 3. Implement token utilities → `src/utils/tokens.py`

- `create_access_token(user_id, session_id, auth_time)` — embeds `sid` + `auth_time` claims
- `create_refresh_token(user_id, session_id)` → returns `(raw_token, hashed_token)`
- `decode_token(token)` with JWT error handling
- `hash_refresh_token(token)` using SHA-256 + salt

---

### 4. Add `token_version` to User model → `src/models/users.py`

Add column:

```python
token_version: Mapped[int] = mapped_column(default=0)
```

Enables "log out everywhere" by incrementing version.

---

### 5. Create auth dependencies → `src/auth/dependencies.py`

- `get_current_user`: decode JWT → check Redis for `session:{user_id}:{sid}` → fetch User → validate `token_version`
- `require_active_user`: ensures `user.is_active == True`
- `require_fresh_login(max_age_seconds=300)`: step-up auth checking `auth_time` claim

---

### 6. Create session service → `src/services/session_service.py`

- `create_session(user, device_name, ip, user_agent)`: dual-write to Redis + PostgreSQL
- `refresh_tokens(raw_refresh_token)`: validate hash, rotate token, extend TTL
- `revoke_session(session_id, user_id)`: delete from both stores
- `revoke_all_sessions(user)`: panic button + increment `token_version`
- `list_sessions(user_id)`: for "My Devices" UI

---

### 7. Create audit log → `src/models/audit.py`

`AccessLog` model with:

- `user_id`, `session_id`, `endpoint`, `method`
- `ip_address`, `action_type`, `status_code`
- `timestamp`, `extra` (JSONB)

Immutable table for HIPAA/GDPR compliance.

---

## Post-Implementation

### Migration

After adding `token_version` to `User` and creating `AccessLog`:

```powershell
alembic revision --autogenerate -m "Add token_version to users, create access_logs"
alembic upgrade head
```

---

## Open Questions

1. **Audit middleware**: Auto-log every request, or explicit logging in sensitive endpoints only?

2. **Auth router**: Include example endpoints (`/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/sessions`) in this phase?

3. **Rate limiting for AI endpoints**: Deferred to later phase ✅
