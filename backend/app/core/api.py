from __future__ import annotations

import dataclasses
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Iterable, Mapping

from fastapi import Query
from sqlalchemy import inspect as sa_inspect

DEFAULT_PAGE_LIMIT = 50
MAX_PAGE_LIMIT = 200


@dataclass(frozen=True)
class Page:
    limit: int
    offset: int


def page_params(
    limit: int = Query(DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT),
    offset: int = Query(0, ge=0),
) -> Page:
    return Page(limit=limit, offset=offset)


def jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [jsonable(v) for v in value]
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: jsonable(getattr(value, f.name)) for f in dataclasses.fields(value)}
    return value


def serialize(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, Mapping):
        return jsonable(obj)
    if hasattr(obj.__class__, "__table__"):
        mapper = sa_inspect(obj.__class__)
        return {col.key: jsonable(getattr(obj, col.key)) for col in mapper.column_attrs}
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return jsonable(obj)
    if hasattr(obj, "__dict__"):
        return {
            k: jsonable(v)
            for k, v in vars(obj).items()
            if not k.startswith("_")
        }
    return jsonable(obj)


def paginated(items: Iterable[Any], page: Page) -> dict[str, Any]:
    rows = list(items)
    window = rows[page.offset : page.offset + page.limit]
    return {
        "items": [serialize(item) for item in window],
        "total": len(rows),
        "limit": page.limit,
        "offset": page.offset,
    }
