from dataclasses import MISSING, field, fields
from typing import Any


__all__ = ["fixed_field", "fixed_fields", "patterned_field", "patterned_fields"]


def fixed_field(*, default: Any = None, metadata: dict[str, Any] | None = None) -> Any:
    """Mark a field as a fixed OpenAPI specification field."""
    return field(default=default, metadata={**(metadata or {}), "fixed_field": True})


def fixed_fields(dataclass_type: type) -> dict[str, Any]:
    """
    Get all fixed specification fields from a dataclass.

    Args:
        dataclass_type: The dataclass type to inspect

    Returns:
        A dictionary mapping field names to field objects for all fields marked with fixed_field()
    """
    return {f.name: f for f in fields(dataclass_type) if f.metadata.get("fixed_field")}


def patterned_field(
    *, default=MISSING, default_factory=MISSING, metadata: dict[str, Any] | None = None
) -> Any:
    """
    Mark a field as containing OpenAPI patterned fields.

    Patterned fields have dynamic names that follow a specific pattern (e.g., security scheme names,
    path patterns, callback expressions, HTTP status codes).

    Args:
        default: Default value for the field
        default_factory: Callable that returns default value
        metadata: Additional metadata for the field
    """
    merged_metadata = {**(metadata or {}), "patterned_field": True}
    if default_factory is not MISSING:
        return field(default_factory=default_factory, metadata=merged_metadata)
    else:
        return field(default=default, metadata=merged_metadata)


def patterned_fields(dataclass_type: type) -> dict[str, Any]:
    """
    Get all patterned fields from a dataclass.

    Args:
        dataclass_type: The dataclass type to inspect

    Returns:
        A dictionary mapping field names to field objects for all fields marked with patterned_field()
    """
    return {f.name: f for f in fields(dataclass_type) if f.metadata.get("patterned_field")}
