import contextlib
import json
import os
import shutil
from typing import Any

from fastapi import HTTPException
from pydantic import ValidationError



def safe_remove(filename: str) -> None:
    with contextlib.suppress(TypeError, OSError):
        os.remove(filename)


def ensure_exists(path: str) -> None:
    os.makedirs(path, exist_ok=True)
