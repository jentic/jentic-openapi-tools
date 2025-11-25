"""Utilities for introspecting datamodel fields."""

from dataclasses import is_dataclass
from typing import Any

from jentic.apitools.openapi.datamodels.low.fields import fixed_fields, patterned_fields
from jentic.apitools.openapi.datamodels.low.sources import (
    FieldSource,
    KeySource,
    ValueSource,
)


__all__ = [
    "get_traversable_fields",
    "unwrap_value",
    "is_datamodel_node",
    "get_yaml_field_name",
]


def get_yaml_field_name(node_class: type, python_field_name: str) -> str:
    """
    Convert Python field name to YAML field name using metadata.

    Args:
        node_class: Datamodel class type
        python_field_name: Python attribute name (e.g., "external_docs")

    Returns:
        YAML field name from metadata, or python_field_name if not found
        (e.g., "externalDocs")
    """
    fixed = fixed_fields(node_class)
    patterned = patterned_fields(node_class)

    # Try fixed fields first, then patterned
    field_obj = fixed.get(python_field_name) or patterned.get(python_field_name)
    if field_obj:
        return field_obj.metadata.get("yaml_name", python_field_name)

    return python_field_name


# Cache of field names to check per class type
# {Info: ["title", "description", "contact", ...], Operation: [...], ...}
_FIELD_NAMES_CACHE: dict[type, list[str]] = {}


def get_traversable_fields(node):
    """
    Get all fields that should be traversed in a datamodel node.

    Uses field metadata (fixed_field, patterned_field) to identify OpenAPI
    specification fields. This leverages the explicit field marking system
    from the datamodels package.

    Caches field names per class type for performance.

    Args:
        node: Datamodel node (dataclass instance)

    Returns:
        List of (field_name, field_value) tuples
    """
    if not is_dataclass(node):
        return []

    node_class = type(node)

    # Get or compute field names for this class
    if node_class not in _FIELD_NAMES_CACHE:
        # Get all OpenAPI spec fields (fixed + patterned)
        fixed = fixed_fields(node_class)
        patterned = patterned_fields(node_class)
        # Combine and extract field names
        field_names = list(fixed.keys()) + list(patterned.keys())
        _FIELD_NAMES_CACHE[node_class] = field_names

    # Use cached field names
    result = []
    for field_name in _FIELD_NAMES_CACHE[node_class]:
        value = getattr(node, field_name, None)

        # Skip None values
        if value is None:
            continue

        # Check if it's traversable
        unwrapped = unwrap_value(value)

        # Skip scalar primitives
        if isinstance(unwrapped, (str, int, float, bool, type(None))):
            continue

        result.append((field_name, value))

    return result


def unwrap_value(value: Any) -> Any:
    """
    Unwrap FieldSource/ValueSource/KeySource to get actual value.

    Wrapper types (FieldSource, ValueSource, KeySource) are used to preserve
    source location information for field values. This function extracts the
    actual value from these wrappers.

    This excludes datamodel nodes like Example which may have .value field
    but are not wrapper types.

    Args:
        value: Potentially wrapped value

    Returns:
        Unwrapped value, or original if not wrapped
    """
    # Check if it's a wrapper type
    if isinstance(value, (FieldSource, ValueSource, KeySource)):
        return value.value
    return value


def is_datamodel_node(value):
    """
    Check if value is a low-level datamodel object.

    Low-level datamodels are distinguished by having a root_node field,
    which contains the YAML source location information. This excludes
    wrapper types (FieldSource, ValueSource, KeySource) and other dataclasses.

    Args:
        value: Value to check

    Returns:
        True if it's a low-level datamodel node, False otherwise
    """
    return is_dataclass(value) and hasattr(value, "root_node")
