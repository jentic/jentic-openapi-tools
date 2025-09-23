from __future__ import annotations
from typing import Any

from jentic.apitools.openapi.parser.core import OpenAPIParser


# from jentic_openapi_parser import Parser


def normalize(obj: Any) -> dict:
    """
    Parse and perform a trivial 'normalization' to prove the flow works.
    Later: real bundling, $ref deref, component hoisting, etc.
    """
    data = OpenAPIParser().parse(obj)
    out = dict(data)
    out.setdefault("x-jentic", {})["transformed"] = True
    return out
