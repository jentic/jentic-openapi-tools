import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, cast
from uuid import UUID

import attrs


__all__ = ["json_dumps", "CustomEncoder"]


class CustomEncoder(json.JSONEncoder):
    """JSON encoder with extended type support for OpenAPI documents.

    Extends the standard json.JSONEncoder to handle additional Python types
    commonly found in OpenAPI documents and related data structures.

    Supported types:
        - datetime/date: Serialized using ISO 8601 format
        - UUID: Converted to string representation
        - Path: Converted to string representation
        - Decimal: Converted to float
        - Enum: Serialized using the enum value
        - attrs classes: Converted to dictionaries using attrs.asdict()
    """

    def default(self, o):
        """Serialize special types not handled by the default JSON encoder.

        Args:
            o: Object to serialize

        Returns:
            JSON-serializable representation of the object

        Raises:
            TypeError: If the object type is not supported
        """
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, (UUID, Path)):
            return str(o)
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, Enum):
            return o.value
        if attrs.has(o):
            return attrs.asdict(cast(Any, o))
        return super().default(o)


def json_dumps(
    data: Any,
    indent: int | None = None,
    *,
    sort_keys: bool = False,
    cls: type[json.JSONEncoder] = CustomEncoder,
) -> str:
    """Serialize data to a JSON string with extended type support.

    This function provides JSON serialization with automatic handling of
    datetime, Path, UUID, Decimal, Enum, and attrs-decorated classes.
    The output is UTF-8 compatible with sorted keys for consistency.

    Args:
        data: The data to serialize (dict, list, or any JSON-compatible type)
        indent: Number of spaces for indentation. None for compact output.
        sort_keys: Whether to sort keys in the output. Defaults to False.
        cls: Custom JSON encoder class. Defaults to CustomEncoder.

    Returns:
        A JSON string representation of the data

    Raises:
        TypeError: If the data contains unsupported types

    Example:
        >>> from datetime import datetime
        >>> data = {"timestamp": datetime.now(), "count": 42}
        >>> json_str = json_dumps(data, indent=2)
    """
    return json.dumps(
        data,
        indent=indent,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=sort_keys,
        separators=(",", ":") if indent is None else (",", ": "),
        cls=cls,
    )
