# AskObi API - Development Guide

> A comprehensive guide for developers working on the AskObi API project

---

## Table of Contents

- [Overview](#overview)
- [Poetry Setup & Usage](#poetry-setup--usage)
- [Development Workflow](#development-workflow)
- [Project Architecture](#project-architecture)
- [Database Migrations](#database-migrations)
- [Authentication System](#authentication-system)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Common Tasks](#common-tasks)

---

## Overview

AskObi API is a HIPAA-compliant health intelligence platform built with FastAPI, using modern Python development practices. We use **Poetry** for dependency management and **Taskipy** for task automation.

### Tech Stack

- **Language**: Python 3.13+
- **Framework**: FastAPI
- **Database**: PostgreSQL with asyncpg
- **ORM**: SQLAlchemy 2.0 (async) + Advanced Alchemy
- **Cache/Session**: Redis
- **Authentication**: JWT with reference tokens
- **Migrations**: Alembic
- **Package Manager**: Poetry
- **Task Runner**: Taskipy

---

## Poetry Setup & Usage

### Why Poetry?

Poetry is our dependency management tool that provides:
- **Deterministic builds** - `poetry.lock` ensures consistent dependencies
- **Virtual environment management** - automatic venv creation
- **Dependency resolution** - handles conflicts automatically
- **Project isolation** - each project has its own dependencies

### Installation

```powershell
# Install Poetry (if not already installed)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

# Verify installation
poetry --version
```

### Initial Project Setup

```powershell
# Clone the repository
git clone https://github.com/AskObi-Org/askobi-api.git
cd askobi-api

# Install dependencies (creates virtual environment automatically)
poetry install

# Activate the virtual environment
poetry shell

# Or run commands without activating
poetry run uvicorn src.main:app --reload
```

### Managing Dependencies

```powershell
# Add a new dependency
poetry add package-name

# Add a dev dependency
poetry add --group dev package-name

# Add a test dependency
poetry add --group test package-name

# Update dependencies
poetry update

# Update a specific package
poetry update package-name

# Remove a dependency
poetry remove package-name

# Show installed packages
poetry show

# Show dependency tree
poetry show --tree
```

### Poetry Configuration

Our `pyproject.toml` defines:
- **Project metadata** - name, version, description
- **Dependencies** - production packages
- **Dependency groups** - dev and test packages
- **Taskipy tasks** - automated commands

---

## Development Workflow

### Starting the Development Server

```powershell
# Using Poetry task (recommended)
poetry run task api

# Or directly
poetry run uvicorn src.main:app --reload --port 8015
```

The server will:
- Auto-reload on code changes
- Be available at `http://127.0.0.1:8015`
- Provide Swagger docs at `http://127.0.0.1:8015/docs`
- Provide ReDoc at `http://127.0.0.1:8015/redoc`

### Environment Configuration

Create `src/conf/.env` with required variables:

```env
# Database
DB_USER=askobi_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_DATABASE=askobi_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Authentication
AUTH_JWT_SECRET_KEY=your-super-secret-key-change-in-production
AUTH_PASSWORD_SALT=your-password-salt-change-in-production

# Environment
ASKOBI_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG
```

### Using Docker Compose

```powershell
# Start PostgreSQL and Redis
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f
```

---

## Project Architecture

### Directory Structure

```
askobi-api/
├── src/
│   ├── auth/                    # Authentication module
│   │   ├── dependencies.py      # Auth dependencies (get_current_user, etc.)
│   │   └── router.py            # Auth endpoints (/login, /register, etc.)
│   ├── models/                  # SQLAlchemy models
│   │   ├── users.py             # User and UserSession models
│   │   ├── audit.py             # AccessLog model
│   │   └── utils.py             # Base model classes
│   ├── repositories/            # Database access layer
│   │   └── user_repository.py   # UserRepository, SessionRepository
│   ├── schemas/                 # Pydantic schemas
│   │   ├── auth.py              # Auth request/response schemas
│   │   └── users.py             # User schemas
│   ├── services/                # Business logic layer
│   │   ├── auth_service.py      # AuthService (sessions, tokens)
│   │   └── user_service.py      # UserService (registration, auth)
│   ├── utils/                   # Utility modules
│   │   ├── authorization.py     # Password hashing (pwdlib)
│   │   ├── db.py                # Database setup
│   │   ├── redis.py             # Redis session store
│   │   ├── tokens.py            # JWT creation/validation
│   │   └── logging.py           # Structured logging
│   ├── conf/                    # Configuration
│   │   └── .env                 # Environment variables
│   ├── settings.py              # Pydantic settings
│   └── main.py                  # FastAPI application
├── alembic/                     # Database migrations
│   ├── versions/                # Migration files
│   └── env.py                   # Alembic configuration
├── tests/                       # Test suite
├── pyproject.toml               # Poetry configuration
├── alembic.ini                  # Alembic configuration
└── docker-compose.yml           # Local services
```

### Architecture Patterns

We follow a **layered architecture**:

1. **Router Layer** (`src/auth/router.py`) - HTTP endpoints
   - Handle HTTP requests/responses
   - Call service layer
   - Minimal business logic

2. **Service Layer** (`src/services/`) - Business logic
   - Coordinate between repositories
   - Implement business rules
   - Transaction management

3. **Repository Layer** (`src/repositories/`) - Data access
   - Database queries
   - CRUD operations
   - Abstraction over SQLAlchemy

4. **Model Layer** (`src/models/`) - Data structures
   - SQLAlchemy ORM models
   - Database schema definition

5. **Schema Layer** (`src/schemas/`) - Validation
   - Pydantic models
   - Request/response validation
   - Data serialization

### Example: User Registration Flow

```python
# 1. Router receives request
@router.post("/register")
async def register(user_data: RegisterRequest, db: AsyncSession):
    user_service = UserService(db)
    return await user_service.register_user(user_data)

# 2. Service implements business logic
class UserService:
    async def register_user(self, user_data: RegisterRequest) -> User:
        # Check if email exists
        existing = await self.user_repo.get_by_email(user_data.email)
        if existing:
            raise HTTPException(...)
        
        # Hash password
        hashed = get_password_hash(user_data.password)
        
        # Create user
        user = User(...)
        return await self.user_repo.create(user)

# 3. Repository handles database
class UserRepository:
    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        return user
```

---

## Database Migrations

We use **Alembic** for database schema migrations.

### Creating Migrations

```powershell
# Auto-generate migration from model changes
poetry run task db_migration MESSAGE="add user preferences"

# Or manually
poetry run alembic revision --autogenerate -m "description"
```

### Running Migrations

```powershell
# Apply all pending migrations
poetry run task db_migrate

# Or manually
poetry run alembic upgrade head

# Rollback one migration
poetry run task db_rollback

# Or manually
poetry run alembic downgrade -1
```

### Migration Workflow

1. **Make model changes** in `src/models/`
2. **Generate migration**: `poetry run task db_migration MESSAGE="what changed"`
3. **Review migration** in `alembic/versions/`
4. **Apply migration**: `poetry run task db_migrate`
5. **Commit** both model changes and migration file

---

## Authentication System

### HIPAA-Compliant Design

Our auth system implements **reference-based JWTs** with Redis:

- **15-minute access tokens** (short-lived for HIPAA compliance)
- **7-day refresh tokens** (rotated on each use)
- **Redis session store** (<1ms revocation time)
- **PostgreSQL backup** (device management, audit trail)
- **Token versioning** (instant "logout everywhere")

### How It Works

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ 1. POST /auth/login
       │    { email, password }
       ▼
┌─────────────────┐
│   AuthService   │
└────────┬────────┘
         │ 2. Verify credentials
         │ 3. Create session
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌──────────┐
│ Redis │ │PostgreSQL│
└───────┘ └──────────┘
    │         │
    └────┬────┘
         │ 4. Return tokens
         ▼
   { access_token, refresh_token }
```

### Using Auth Endpoints

```python
# Register
POST /auth/register
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}

# Login
POST /auth/login
{
  "email": "john@example.com",
  "password": "SecurePass123!"
}
# Response: { access_token, refresh_token, token_type: "bearer" }

# Refresh tokens
POST /auth/refresh
{
  "refresh_token": "..."
}

# Get current user
GET /auth/me
Headers: Authorization: Bearer <access_token>

# List sessions (devices)
GET /auth/sessions
Headers: Authorization: Bearer <access_token>

# Logout current device
POST /auth/logout
Headers: Authorization: Bearer <access_token>

# Logout all devices (panic button)
POST /auth/logout-all
Headers: Authorization: Bearer <access_token>
```

### Protected Endpoints

```python
from src.auth.dependencies import get_current_user, require_active_user

@router.get("/protected")
async def protected_route(
    current_user: Annotated[User, Depends(require_active_user)]
):
    return {"user_id": current_user.id}
```

---

## Testing

### Running Tests

```powershell
# Run all tests
poetry run task test

# Run specific test file
poetry run pytest tests/test_auth.py

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run with verbose output
poetry run pytest -v
```

### Writing Tests

```python
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_register_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/auth/register", json={
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password": "SecurePass123!"
        })
        assert response.status_code == 201
        assert response.json()["email"] == "test@example.com"
```

---

## Code Quality

### Linting & Formatting

```powershell
# Format code with Black
poetry run black .

# Sort imports with isort
poetry run isort .

# Run all linters with autofix
poetry run task lint

# Check without fixing
poetry run task lint_check

# Type checking with mypy
poetry run task lint_types
```

### Code Style Guidelines

- **Follow PEP 8** conventions
- **Use type hints** for all function signatures
- **Write docstrings** for public functions
- **Keep functions small** (single responsibility)
- **Use meaningful names** (no abbreviations)

### Example

```python
async def authenticate_user(self, email: str, password: str) -> Optional[User]:
    """
    Authenticate user with email and password.
    
    Args:
        email: User's email address
        password: Plain text password
    
    Returns:
        User object if authenticated, None otherwise
    """
    user = await self.user_repo.get_by_email(email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user
```

---

## Common Tasks

### Add a New Endpoint

1. **Create schema** in `src/schemas/`
2. **Add repository methods** (if needed)
3. **Add service methods** (if needed)
4. **Create router endpoint** in `src/auth/router.py` or new router
5. **Register router** in `src/main.py`
6. **Write tests**

### Add a New Model

1. **Create model** in `src/models/`
2. **Import in** `src/models/__init__.py`
3. **Generate migration**: `poetry run task db_migration MESSAGE="add model"`
4. **Review and apply**: `poetry run task db_migrate`

### Debug Issues

```powershell
# Check logs
poetry run task api  # Watch console output

# Check Redis
redis-cli
> KEYS session:*
> GET session:user_id:session_id

# Check PostgreSQL
psql -U askobi_user -d askobi_db
\dt                    # List tables
SELECT * FROM users;   # Query data
```

### Update Dependencies

```powershell
# Check outdated packages
poetry show --outdated

# Update all
poetry update

# Update specific package
poetry update fastapi

# Lock file only (don't install)
poetry lock --no-update
```

---

## Best Practices

### ✅ DO

- Use async/await for all I/O operations
- Validate input with Pydantic schemas
- Use dependency injection with FastAPI Depends
- Write tests for new features
- Use meaningful commit messages
- Keep secrets in `.env` files
- Run linters before committing

### ❌ DON'T

- Commit `.env` files
- Use blocking I/O operations
- Hardcode configuration values
- Skip migrations
- Push directly to `main` branch
- Ignore type hints
- Leave commented-out code

---

## Useful Commands Cheat Sheet

```powershell
# Development
poetry run task api              # Start dev server
poetry run task db_migrate       # Run migrations
poetry run task db_rollback      # Rollback migration

# Testing
poetry run task test             # Run tests
poetry run pytest -k test_name   # Run specific test

# Code Quality
poetry run task lint             # Format & fix
poetry run task lint_check       # Check only
poetry run task lint_types       # Type check

# Dependencies
poetry add package-name          # Add package
poetry remove package-name       # Remove package
poetry update                    # Update all
poetry show                      # List packages

# Database
poetry run alembic current       # Show current revision
poetry run alembic history       # Show migration history
poetry run alembic upgrade head  # Apply migrations

# Docker
docker-compose up -d             # Start services
docker-compose down              # Stop services
docker-compose logs -f api       # View logs
```

---

## Getting Help

- **API Documentation**: http://127.0.0.1:8015/docs
- **Project Issues**: GitHub Issues
- **Team Communication**: Slack/Discord/Teams

---

**Happy Coding! 🚀**
