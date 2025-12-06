import asyncio
import inspect
import json
import secrets
import traceback
from collections import defaultdict
from collections.abc import Callable, Sized
from datetime import datetime, timedelta
from decimal import Decimal
from types import TracebackType
from typing import Annotated, Any,Literal , cast, overload

from advanced_alchemy.base import ModelProtocol
# from aiohttp import ClientResponse, ClientSession
from dateutil.parser import isoparse
from fastapi import HTTPException
from pydantic import Field, create_model
from sqlalchemy import ColumnElement
from sqlalchemy.orm import InstrumentedAttribute
from uuid import UUID
from src.utils.time import now as time_now

from src.utils.logging import Logger, get_exception_message, log_errors
from src.schemas.base import Schema
from src.utils.constants import STR_TO_BOOL_MAPPING, TOTP_ALPHABET, TOTP_LENGTH


def get_object_name(obj: object) -> str:
    return obj.__class__.__name__.lower()


def unique_id() -> str:
    return str(UUID())


def unique_verify_code(length: int = TOTP_LENGTH) -> str:
    return "".join(secrets.choice(TOTP_ALPHABET) for _ in range(length))

def get_sqla_attr(
    model: ModelProtocol,
    key: str,
) -> InstrumentedAttribute[Any]:
    return cast("InstrumentedAttribute[Any]", getattr(model, key))

def str_to_bool(s: str) -> bool:
    s = s.lower()

    if s in STR_TO_BOOL_MAPPING:
        return STR_TO_BOOL_MAPPING[s]
    return False

class SearchQuery:
    DATE_FORMATS = {"h": "hours", "d": "days", "w": "weeks", "m": 30, "y": 30 * 12}

    def __init__(self, query: str) -> None:
        self.query = query
        text = []
        self.filters = defaultdict(list)
        self.metadata_filters = defaultdict(list)
        for item in query.split():
            parts = item.split(":")
            is_quoted = item[0] == '"' and item[-1] == '"'
            if len(parts) >= 2 and not is_quoted:
                key = parts[0].lower()
                value = ":".join(parts[1:])
                if key.startswith("metadata."):
                    field_name = key[9:]
                    self.metadata_filters[field_name].append(value)
                else:
                    self.filters[key].append(value)
            else:
                if is_quoted:
                    item = item[1:-1]
                text.append(item)
        self.text = " ".join(text)

    def parse_datetime(self, key: str) -> datetime | None:
        if key not in self.filters:
            return None
        now = time_now()
        date = self.filters.pop(key)[0]
        if len(date) >= 3 and date[0] == "-" and date[-1] in self.DATE_FORMATS and is_int(date[1:-1]):
            val = int(date[1:-1])
            dt_format = date[-1]
            if dt_format in ("m", "y"):
                key = "days"
                val *= cast(int, self.DATE_FORMATS[dt_format])
            else:
                key = cast(str, self.DATE_FORMATS[dt_format])
            return now - timedelta(**{key: val})
        try:
            return isoparse(date)
        except ValueError:
            return None

    def get_created_filter(self, model: type[ModelProtocol], key: str = "created") -> list[ColumnElement[bool]]:
        if getattr(model, key, None) is None:  # pragma: no cover
            return []
        self.filters.pop(key, None)
        start_date = self.parse_datetime("start_date")
        end_date = self.parse_datetime("end_date")
        queries = []
        if start_date:
            queries.append(get_sqla_attr(cast(ModelProtocol, model), "created") >= start_date)
        if end_date:
            queries.append(get_sqla_attr(cast(ModelProtocol, model), "created") <= end_date)
        return queries

    def __bool__(self) -> bool:
        return bool(self.text or self.filters or self.metadata_filters)

def is_int(v: Any) -> bool:
    try:
        int(v)
        return True
    except ValueError:
        return False


def excepthook_handler(
    logger: Logger,
    excepthook: Callable[[type[BaseException], BaseException, TracebackType | None], Any],
) -> Callable[[type[BaseException], BaseException, TracebackType | None], Any]:
    def internal_error_handler(type_: type[BaseException], value: BaseException, tb: TracebackType | None) -> Any:
        if type_ is not KeyboardInterrupt:
            logger.error("\n" + "".join(traceback.format_exception(type_, value, tb)))
        return excepthook(type_, value, tb)

    return internal_error_handler


def handle_event_loop_exception(logger: Logger, loop: asyncio.AbstractEventLoop, context: dict[str, Any]) -> None:
    msg = get_exception_message(context["exception"]) if "exception" in context else context["message"]
    logger.error(msg)