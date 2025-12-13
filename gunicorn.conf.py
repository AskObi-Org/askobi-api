"""Gunicorn configuration for running the FastAPI ASGI app with uvicorn workers."""

from __future__ import annotations

import multiprocessing
import os


def _env(key: str, default: str) -> str:
    value = os.getenv(key)
    return value if value else default


def _env_int(key: str, default: int) -> int:
    try:
        return int(_env(key, str(default)))
    except ValueError:
        return default


def _default_workers() -> int:
    # Free tiers often give ~512MB; prefer a single worker to avoid OOM.
    cpu_based = multiprocessing.cpu_count() * 2 + 1
    return min(1, cpu_based)


bind = _env("GUNICORN_BIND", "0.0.0.0:8000")
worker_class = "uvicorn.workers.UvicornWorker"
workers = _env_int("WEB_CONCURRENCY", _default_workers())
threads = _env_int("GUNICORN_THREADS", 1)
timeout = _env_int("GUNICORN_TIMEOUT", 60)
graceful_timeout = _env_int("GUNICORN_GRACEFUL_TIMEOUT", 30)
keepalive = _env_int("GUNICORN_KEEPALIVE", 5)
max_requests = _env_int("GUNICORN_MAX_REQUESTS", 200)
max_requests_jitter = _env_int("GUNICORN_MAX_REQUESTS_JITTER", 20)
accesslog = _env("GUNICORN_ACCESSLOG", "-")
errorlog = _env("GUNICORN_ERRORLOG", "-")
loglevel = _env("GUNICORN_LOGLEVEL", "info")
capture_output = True
preload_app = False  # Lower memory footprint on small free-tier dynos
forwarded_allow_ips = "*"
proxy_allow_ips = "*"
wsgi_app = "src.main:app"
