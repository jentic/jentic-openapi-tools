from dataclasses import field, fields


__all__ = ["fixed_field", "fixed_fields", "patterned_field", "patterned_fields"]


def fixed_field(default=None, metadata=None):
    """Mark a field as a fixed OpenAPI specification field."""
    return field(default=default, metadata={**(metadata or {}), "fixed_field": True})


def fixed_fields(dataclass_type):
    """
    Get all fixed specification fields from a dataclass.

    Args:
        dataclass_type: The dataclass type to inspect

    Returns:
        A dictionary mapping field names to field objects for all fields marked with fixed_field()
    """
    return {f.name: f for f in fields(dataclass_type) if f.metadata.get("fixed_field")}


def patterned_field(default=None, metadata=None):
    """
    Mark a field as containing OpenAPI patterned fields.

    Patterned fields have dynamic names that follow a specific pattern (e.g., security scheme names,
    path patterns, callback expressions, HTTP status codes).
    """
    return field(default=default, metadata={**(metadata or {}), "patterned_field": True})


def patterned_fields(dataclass_type):
    """
    Get all patterned fields from a dataclass.

    Args:
        dataclass_type: The dataclass type to inspect

    Returns:
        A dictionary mapping field names to field objects for all fields marked with patterned_field()
    """
    return {f.name: f for f in fields(dataclass_type) if f.metadata.get("patterned_field")}
