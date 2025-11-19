"""Utilities for introspecting datamodel fields."""

from dataclasses import fields, is_dataclass


__all__ = [
    "get_traversable_fields",
    "unwrap_value",
    "is_datamodel_node",
]


# Cache of field names to check per class type
# {Info: ["title", "description", "contact", ...], Operation: [...], ...}
_FIELD_NAMES_CACHE: dict[type, list[str]] = {}


def get_traversable_fields(node):
    """
    Get all fields that should be traversed in a datamodel node.

    Uses dataclass introspection to discover fields.
    Filters out infrastructure fields and scalar values.

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
        # Compute once per class type
        field_names = [f.name for f in fields(node) if f.name != "root_node"]
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


def unwrap_value(value):
    """
    Unwrap FieldSource/ValueSource/KeySource to get actual value.

    Args:
        value: Potentially wrapped value

    Returns:
        Unwrapped value, or original if not wrapped
    """
    # FieldSource, ValueSource, KeySource all have .value attribute
    if hasattr(value, "value"):
        return value.value
    return value


def is_datamodel_node(value):
    """
    Check if value is a traversable datamodel object.

    Args:
        value: Value to check

    Returns:
        True if it's a dataclass (datamodel node), False otherwise
    """
    if value is None:
        return False

    # Must be a dataclass
    if not is_dataclass(value):
        return False

    # Exclude primitives (though dataclasses of primitives are unlikely)
    if isinstance(value, (str, int, float, bool)):
        return False

    # Note: We do NOT filter out wrapper types or YAML nodes here.
    # If these appear after unwrapping, it indicates a bug:
    # - FieldSource/ValueSource/KeySource: missing unwrap or double-wrapping
    # - ScalarNode/SequenceNode/MappingNode: root_node leaked or invalid data
    # Fail-fast is better than silent failures!

    return True
