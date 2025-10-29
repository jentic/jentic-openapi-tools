from dataclasses import fields
from typing import Any, TypeVar, cast, get_args

from ruamel import yaml

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.extractors import extract_extension_fields
from jentic.apitools.openapi.datamodels.low.fields import fixed_fields
from jentic.apitools.openapi.datamodels.low.sources import (
    FieldSource,
    KeySource,
    ValueSource,
    YAMLInvalidValue,
)


__all__ = ["build_model"]


T = TypeVar("T")


def build_model(
    root: yaml.Node, dataclass_type: type[T], *, context: Context | None = None
) -> T | ValueSource[YAMLInvalidValue]:
    """
    Generic builder for OpenAPI low model.

    Builds any dataclass that follows the pattern:
    - Has a required `root_node: yaml.Node` field
    - Has an optional `extensions: dict[...]` field
    - Has spec fields marked with `fixed_field()`

    Args:
        root: The YAML node to parse (should be a MappingNode)
        dataclass_type: The dataclass type to build
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        An instance of dataclass_type if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        xml = build_model(root_node, XML, context=context)
    """
    # Initialize context once at the beginning
    if context is None:
        context = Context()

    if not isinstance(root, yaml.MappingNode):
        # Preserve invalid root data instead of returning None
        value = context.yaml_constructor.construct_object(root, deep=True)
        return ValueSource(value=value, value_node=root)

    # Get fixed specification fields for this dataclass type
    _fixed_fields = fixed_fields(dataclass_type)

    # Build YAML name to Python field name mapping
    yaml_to_field = {
        field.metadata.get("yaml_name", fname): fname for fname, field in _fixed_fields.items()
    }

    # Extract field values in a single pass (non-recursive, single layer only)
    field_values: dict[str, Any] = {}
    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        # Map YAML key to Python field name
        field_name = yaml_to_field.get(key)
        if field_name:
            field = _fixed_fields[field_name]
            field_type_args = set(get_args(field.type))

            if field_type_args & {FieldSource[str], FieldSource[bool], FieldSource[int]}:
                value = context.yaml_constructor.construct_object(value_node, deep=True)
                field_values[field_name] = FieldSource(
                    value=value, key_node=key_node, value_node=value_node
                )
            elif field_type_args & {FieldSource[dict[KeySource[str], ValueSource[str]]]}:
                # Handle dict with KeySource/ValueSource wrapping
                if isinstance(value_node, yaml.MappingNode):
                    mapping_dict: dict[KeySource[str], ValueSource[str]] = {}
                    for map_key_node, map_value_node in value_node.value:
                        map_key = context.yaml_constructor.construct_yaml_str(map_key_node)
                        map_value = context.yaml_constructor.construct_object(
                            map_value_node, deep=True
                        )
                        mapping_dict[KeySource(value=map_key, key_node=map_key_node)] = ValueSource(
                            value=map_value, value_node=map_value_node
                        )
                    field_values[field_name] = FieldSource(
                        value=mapping_dict, key_node=key_node, value_node=value_node
                    )
                else:
                    # Not a mapping - preserve as-is for validation
                    value = context.yaml_constructor.construct_object(value_node, deep=True)
                    field_values[field_name] = FieldSource(
                        value=value, key_node=key_node, value_node=value_node
                    )

    # Build and return the dataclass instance
    # Conditionally include extensions field if dataclass supports it
    # Cast to Any to work around generic type constraints
    has_extensions = any(f.name == "extensions" for f in fields(cast(Any, dataclass_type)))
    return cast(
        T,
        dataclass_type(
            root_node=root,  # type: ignore[call-arg]
            **field_values,
            **({"extensions": extract_extension_fields(root, context)} if has_extensions else {}),
        ),
    )
