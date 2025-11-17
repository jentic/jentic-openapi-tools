from ruamel import yaml

from .context import Context
from .fields import fixed_fields
from .sources import KeySource, ValueSource, YAMLValue


__all__ = ["extract_extension_fields", "extract_unknown_fields"]


def extract_extension_fields(
    node: yaml.MappingNode, context: Context | None = None
) -> dict[KeySource[str], ValueSource[YAMLValue]]:
    """
    Extract OpenAPI specification extension fields from a YAML mapping node.

    Specification extension fields are any fields that start with "x-" and allow
    users to add custom properties to OpenAPI definitions.

    Args:
        node: The YAML mapping node to extract extension fields from
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A dictionary mapping extension field names to their values, or empty dict if no extension fields found

    Example:
        Given YAML like:
            name: id
            x-custom: value
            x-internal: true

        Returns:
            {
                KeySource(value="x-custom", key_node=...): ValueSource(value="value", value_node=...),
                KeySource(value="x-internal", key_node=...): ValueSource(value=True, value_node=...)
            }
    """
    if not isinstance(node, yaml.MappingNode):
        return {}

    if context is None:
        context = Context()

    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = {}

    for key_node, value_node in node.value:
        # Construct the key as a Python object (should be a string)
        py_key = context.yaml_constructor.construct_yaml_str(key_node)

        # Check if it's an extension (starts with "x-")
        if isinstance(py_key, str) and py_key.startswith("x-"):
            # Construct the actual Python value from the YAML node
            py_value = context.yaml_constructor.construct_object(value_node, deep=True)

            key_ref = KeySource[str](value=py_key, key_node=key_node)
            value_ref = ValueSource[YAMLValue](value=py_value, value_node=value_node)
            extensions[key_ref] = value_ref

    return extensions


def extract_unknown_fields(
    node: yaml.MappingNode, dataclass_type: type, context: Context | None = None
) -> dict[KeySource[str], ValueSource[YAMLValue]]:
    """
    Extract unknown fields from a YAML mapping node.

    Unknown fields are fields that are not part of the OpenAPI specification
    (not fixed fields of the dataclass) and are not extensions (don't start with "x-").
    These are typically typos or fields from a different specification version.

    Args:
        node: The YAML mapping node to extract unknown fields from
        dataclass_type: The dataclass type to get valid field names from
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A dictionary mapping unknown field names to their values, or empty dict if no unknown fields found

    Example:
        Given YAML like:
            name: id
            namspace: http://example.com  # typo - should be "namespace"
            customField: value             # unknown field
            x-custom: value                # extension - not unknown

        With dataclass_type=XML (which has fixed fields: name, namespace, prefix, attribute, wrapped)
        Returns:
            {
                KeySource(value="namspace", key_node=...): ValueSource(value="http://example.com", value_node=...),
                KeySource(value="customField", key_node=...): ValueSource(value="value", value_node=...)
            }
    """
    if not isinstance(node, yaml.MappingNode):
        return {}

    if context is None:
        context = Context()

    # Get valid YAML field names from the dataclass (considering yaml_name metadata)
    _fixed_fields = fixed_fields(dataclass_type)
    yaml_field_names = {
        field.metadata.get("yaml_name", fname) for fname, field in _fixed_fields.items()
    }

    unknown_fields: dict[KeySource[str], ValueSource[YAMLValue]] = {}

    for key_node, value_node in node.value:
        # Construct the key as a Python object (should be a string)
        py_key = context.yaml_constructor.construct_yaml_str(key_node)

        # Check if it's an unknown field (not in valid YAML field names and not an extension)
        if (
            isinstance(py_key, str)
            and py_key not in yaml_field_names
            and not py_key.startswith("x-")
        ):
            # Construct the actual Python value from the YAML node
            py_value = context.yaml_constructor.construct_object(value_node, deep=True)

            key_ref = KeySource[str](value=py_key, key_node=key_node)
            value_ref = ValueSource[YAMLValue](value=py_value, value_node=value_node)
            unknown_fields[key_ref] = value_ref

    return unknown_fields
