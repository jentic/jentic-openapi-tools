from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from uuid import UUID
import json
from typing import Any
import attrs


def dump_json(data: Any, indent: int | None = None) -> str:
    return json.dumps(
        data, indent=indent, ensure_ascii=False, allow_nan=False, sort_keys=True, cls=CustomEncoder
    )


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):  # type: ignore[override]
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, (UUID, Path)):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, Enum):
            return obj.value
        if attrs.has(obj):
            return attrs.asdict(obj)
        return super().default(obj)
