import secrets
from datetime import datetime
from typing import Any

from advanced_alchemy.base import SQLQuery
import secrets
from datetime import datetime
from typing import Any

from advanced_alchemy.base import SQLQuery
from sqlalchemy import (
    TIMESTAMP, 
    MetaData,inspect,Text
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declared_attr, mapped_column
from sqlalchemy.ext.mutable import MutableDict


from src.schemas.base import Schema
from src.utils.time import now as time_now
from src.utils.common import unique_id


"""Database model helpers and shared Model base.

This module contains the project's base ORM model (`Model`) and related
helpers used by concrete model classes. The code intentionally keeps a
small, framework-agnostic surface so that plugins or other modules can
subclass `Model` and gain consistent behavior (table naming, registration,
and some small convenience methods for working with JSON fields backed by
Pydantic `Schema` instances).

Key concepts for junior devs:
- `my_metadata`: a SQLAlchemy `MetaData` instance that defines naming
  conventions for generated constraints/indexes. Keeping conventions
  consistent helps with migrations and predictable DB object names.
- `all_tables`: a registry of concrete model classes discovered via
  `Model.__init_subclass__`. Useful for reflection/registration tasks.
- `Model`: the shared base class that plugins and app models should
  inherit from. It sets naming conventions, optional table prefixing,
  and provides small helpers like `set_json_key` to update JSON/Schema
  attributes safely.

NOTES / GOTCHAS:
- The `set_json_key` helper expects that the attribute at `key` is
  itself a Pydantic `Schema` (or similar) instance and will replace it
  with a copy updated from another `Schema` instance. This is handy
  when working with JSONB columns mapped to Pydantic models.
- Converting/mapping rules (e.g. table name prefixing) happen in
  `__init_subclass__`, so changes only apply when classes are defined.
  If you dynamically alter class attributes later you may need to
  re-create the class for the change to take effect.
"""


my_metadata = MetaData(
    # NOTE: the key is intentionally `nameing_convention` because this
    # project historically used that spelling. If you change it to the
    # correct `naming_convention`, ensure downstream code (migrations,
    # and any bootstrap logic) still behaves as expected.
    naming_convention={
        "ix": "%(column_0_label)s",
        "uq": "%(table_name)s_%(column_0_name)s_key",
        "ck": "%(table_name)s_%(column_0_name)s_check",
        "fk": "%(table_name)s_%(column_0_name)s_%(referred_table_name)s_fk",
        "pk": "%(table_name)s_pk"
    }
)


# Registry of discovered concrete model classes keyed by class name.
# Populated automatically from `Model.__init_subclass__`.
all_tables: dict[str, type["Model"]] = {}


class Model(SQLQuery):
    """Base class for all ORM models in the app.

    Subclass this for any table-backed model. The base class behavior
    includes:
    - Automatic registration of concrete subclasses into `all_tables`.
    - Optional table name prefixing using `TABLE_PREFIX` to avoid
      collisions when loading multiple plugins.
    - If the subclass defines `PUBLIC`, the class will set
      `__table_args__ = {"extend_existing": True}` allowing existing
      tables to be reflected/extended rather than redefined.

    The class purpose is to centralize small but important conventions
    so that downstream classes stay consistent. Keep this class small;
    complex business logic belongs in services, not the model base.
    """

    __abstract__ = True
    __allow_unmapped__ = True

    def __init_subclass__(cls, **kwargs: Any) -> None:  # pragma: no cover
        # Called when a new subclass is created. We use it to apply
        # project-specific naming rules and to register the class.
        if hasattr(cls, "__tablename__"):
            is_public = hasattr(cls, "PUBLIC")
            # Optional table prefixing: useful for plugins or namespacing
            # tables to avoid collisions when multiple modules register
            # tables with similar logical names.
            if hasattr(cls, "TABLE_PREFIX"):
                cls.__tablename__ = f"plugin_{cls.TABLE_PREFIX}_{cls.__tablename__}"
            if is_public:
                # When a model is declared public, allow SQLAlchemy to
                # extend an existing table definition instead of failing
                # if the table already exists in metadata.
                cls.__table_args__ = {"extend_existing": True}
            # Register the concrete model class for easy lookup later
            all_tables[cls.__name__] = cls
        super().__init_subclass__(**kwargs)

    # Use the shared metadata instance so naming conventions are applied
    # consistently across all models that inherit from this base.
    metadata = my_metadata

    async def set_json_key(self, key: str, scheme: Schema) -> None:
        """Update an attribute that stores a Pydantic `Schema`.

        This helper reads the current attribute at `key` (expected to be
        a Pydantic model instance), creates a copy updated with the
        values from `scheme` (using `exclude_unset=True` so that only
        provided values are applied), and replaces the attribute.

        Use this when you store structured JSON (e.g. `JSONB`) on a model
        and want to apply partial updates expressed as Pydantic schemas.
        """
        current_model = getattr(self, key)
        updated_model = current_model.model_copy(update=scheme.model_dump(exclude_unset=True))
        setattr(self, key, updated_model)

    def update(self, **data: Any) -> None:
        """Shallow update: set attributes based on provided keyword args.

        This is a convenience used by some service layers; it simply sets
        attributes directly on the instance. It does not perform
        validation or type coercion — that should be handled by higher
        level logic or by using Pydantic schemas before calling this.
        """
        for key, value in data.items():
            setattr(self, key, value)


def utc_now() -> datetime:
    """Return the current UTC time using the project's time helper.

    Keeping this wrapper ensures a single import site for the time
    helper and makes tests easier when you need to monkeypatch the
    project's `time_now` function.
    """
    return time_now()

class TimestampedModel(Model):
    __abstract__ = True

    created: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=utc_now)
    updated: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), onupdate=utc_now, default=None)


class IDModel(TimestampedModel):
    __abstract__ = True

    @staticmethod
    def id_generator() -> str:

        return unique_id()

    @declared_attr
    def id(cls) -> Mapped[str]:
        return mapped_column(Text, primary_key=True, index=True, default=lambda: cls.id_generator())

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, self.__class__) and self.id == __value.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        # We do this complex thing because we might be outside a session with
        # an expired object; typically when Sentry tries to serialize the object for
        # error reporting.
        # But basically, we want to show the ID if we have it.
        insp = inspect(self)
        if insp.identity is not None:
            id_value = insp.identity[0]
            return f"{self.__class__.__name__}(id={id_value!r})"
        return f"{self.__class__.__name__}(id=None)"

    @classmethod
    def generate_id(cls) -> str:

        return unique_id()


class MetadataMixin:
    __abstract__ = True

    meta: Mapped[dict[str, Any]] = mapped_column("metadata", MutableDict.as_mutable(JSONB()), default=dict)


class RecordModel(IDModel, MetadataMixin):
    __abstract__ = True