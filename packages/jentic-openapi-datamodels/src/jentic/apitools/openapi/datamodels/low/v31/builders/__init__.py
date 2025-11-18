"""Builders for OpenAPI 3.1.x specification objects."""

from dataclasses import fields
from typing import TYPE_CHECKING, Any, TypeVar, cast, get_args

from ruamel import yaml

from ...context import Context
from ...extractors import extract_extension_fields
from ...fields import fixed_fields
from ...sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue


if TYPE_CHECKING:
    from ..callback import Callback  # noqa: F401
    from ..example import Example  # noqa: F401
    from ..external_documentation import ExternalDocumentation  # noqa: F401
    from ..header import Header  # noqa: F401
    from ..link import Link  # noqa: F401
    from ..media_type import MediaType  # noqa: F401
    from ..parameter import Parameter  # noqa: F401
    from ..path_item import PathItem  # noqa: F401
    from ..reference import Reference  # noqa: F401
    from ..schema import BooleanJSONSchema, Schema  # noqa: F401
    from ..security_requirement import SecurityRequirement  # noqa: F401
    from ..server import Server  # noqa: F401


__all__ = ["build_model", "build_field_source"]


T = TypeVar("T")


def build_model(
    root: yaml.Node, dataclass_type: type[T], *, context: Context | None = None
) -> T | ValueSource[YAMLInvalidValue]:
    """
    Generic builder for OpenAPI 3.1 low model.

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
    field_values: dict[str, FieldSource[Any]] = {}
    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        # Map YAML key to Python field name
        field_name = yaml_to_field.get(key)
        if field_name:
            field = _fixed_fields[field_name]
            field_type_args = set(get_args(field.type))

            if field_type_args & {
                FieldSource[str],
                FieldSource[bool],
                FieldSource[int],
                FieldSource[YAMLValue],
            }:
                field_values[field_name] = build_field_source(key_node, value_node, context)
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
                    field_values[field_name] = build_field_source(key_node, value_node, context)
            elif field_type_args & {FieldSource[list[ValueSource[str]]]}:
                # Handle list with ValueSource wrapping for each item
                if isinstance(value_node, yaml.SequenceNode):
                    value_list: list[ValueSource[str]] = []
                    for item_node in value_node.value:
                        item_value = context.yaml_constructor.construct_object(item_node, deep=True)
                        value_list.append(ValueSource(value=item_value, value_node=item_node))
                    field_values[field_name] = FieldSource(
                        value=value_list, key_node=key_node, value_node=value_node
                    )
                else:
                    # Not a sequence - preserve as-is for validation
                    field_values[field_name] = build_field_source(key_node, value_node, context)
            elif field_type_args & {FieldSource[list["Server"]]}:
                # Handle list[Server] with lazy import
                from ..server import build as build_server

                if isinstance(value_node, yaml.SequenceNode):
                    servers_list = []
                    for item_node in value_node.value:
                        server_obj = build_server(item_node, context)
                        servers_list.append(server_obj)
                    field_values[field_name] = FieldSource(
                        value=servers_list, key_node=key_node, value_node=value_node
                    )
                else:
                    # Not a sequence - preserve as-is for validation
                    field_values[field_name] = build_field_source(key_node, value_node, context)
            elif field_type_args & {FieldSource[list["SecurityRequirement"]]}:
                # Handle list[SecurityRequirement] with lazy import
                from ..security_requirement import build as build_security_requirement

                if isinstance(value_node, yaml.SequenceNode):
                    security_list = []
                    for item_node in value_node.value:
                        security_req = build_security_requirement(item_node, context)
                        security_list.append(security_req)
                    field_values[field_name] = FieldSource(
                        value=security_list, key_node=key_node, value_node=value_node
                    )
                else:
                    # Not a sequence - preserve as-is for validation
                    field_values[field_name] = build_field_source(key_node, value_node, context)
            elif field_type_args & {FieldSource[list["Parameter | Reference"]]}:
                # Handle list[Parameter | Reference] with lazy import
                from ..parameter import build_parameter_or_reference

                if isinstance(value_node, yaml.SequenceNode):
                    parameters_list = []
                    for item_node in value_node.value:
                        parameter_or_reference = build_parameter_or_reference(item_node, context)
                        parameters_list.append(parameter_or_reference)
                    field_values[field_name] = FieldSource(
                        value=parameters_list, key_node=key_node, value_node=value_node
                    )
                else:
                    # Not a sequence - preserve as-is for validation
                    field_values[field_name] = build_field_source(key_node, value_node, context)
            elif field_type_args & {FieldSource[dict[KeySource[str], "Example | Reference"]]}:
                # Handle dict[KeySource[str], Example | Reference] with lazy import
                from ..example import build_example_or_reference

                if isinstance(value_node, yaml.MappingNode):
                    examples_dict = {}
                    for map_key_node, map_value_node in value_node.value:
                        map_key = context.yaml_constructor.construct_yaml_str(map_key_node)
                        example_or_reference = build_example_or_reference(map_value_node, context)
                        examples_dict[KeySource(value=map_key, key_node=map_key_node)] = (
                            example_or_reference
                        )
                    field_values[field_name] = FieldSource(
                        value=examples_dict, key_node=key_node, value_node=value_node
                    )
                else:
                    # Not a mapping - preserve as-is for validation
                    field_values[field_name] = build_field_source(key_node, value_node, context)
            elif field_type_args & {FieldSource[dict[KeySource[str], "MediaType"]]}:
                # Handle dict[KeySource[str], MediaType] with lazy import
                from ..media_type import build as build_media_type

                if isinstance(value_node, yaml.MappingNode):
                    content_dict = {}
                    for map_key_node, map_value_node in value_node.value:
                        map_key = context.yaml_constructor.construct_yaml_str(map_key_node)
                        media_type_obj = build_media_type(map_value_node, context)
                        content_dict[KeySource(value=map_key, key_node=map_key_node)] = (
                            media_type_obj
                        )
                    field_values[field_name] = FieldSource(
                        value=content_dict, key_node=key_node, value_node=value_node
                    )
                else:
                    # Not a mapping - preserve as-is for validation
                    field_values[field_name] = build_field_source(key_node, value_node, context)
            elif field_type_args & {FieldSource[dict[KeySource[str], "Header | Reference"]]}:
                # Handle dict[KeySource[str], Header | Reference] with lazy import
                from ..header import build_header_or_reference

                if isinstance(value_node, yaml.MappingNode):
                    headers_dict = {}
                    for map_key_node, map_value_node in value_node.value:
                        map_key = context.yaml_constructor.construct_yaml_str(map_key_node)
                        header_or_reference = build_header_or_reference(map_value_node, context)
                        headers_dict[KeySource(value=map_key, key_node=map_key_node)] = (
                            header_or_reference
                        )
                    field_values[field_name] = FieldSource(
                        value=headers_dict, key_node=key_node, value_node=value_node
                    )
                else:
                    # Not a mapping - preserve as-is for validation
                    field_values[field_name] = build_field_source(key_node, value_node, context)
            elif field_type_args & {FieldSource["ExternalDocumentation"]}:
                # Handle ExternalDocumentation with lazy import
                from ..external_documentation import build as build_external_docs

                field_values[field_name] = FieldSource(
                    value=build_external_docs(value_node, context),
                    key_node=key_node,
                    value_node=value_node,
                )
            elif field_type_args & {FieldSource["Schema | BooleanJSONSchema"]}:
                # Handle Schema | Reference union with lazy import
                from ..schema import build as build_schema

                field_values[field_name] = FieldSource(
                    value=build_schema(value_node, context),
                    key_node=key_node,
                    value_node=value_node,
                )
            elif field_type_args & {FieldSource[dict[KeySource[str], "PathItem"]]}:
                # Handle dict[KeySource[str], PathItem] with lazy import
                from ..path_item import build as build_path_item

                if isinstance(value_node, yaml.MappingNode):
                    path_items_dict = {}
                    for map_key_node, map_value_node in value_node.value:
                        map_key = context.yaml_constructor.construct_yaml_str(map_key_node)
                        path_item = build_path_item(map_value_node, context)
                        path_items_dict[KeySource(value=map_key, key_node=map_key_node)] = path_item
                    field_values[field_name] = FieldSource(
                        value=path_items_dict, key_node=key_node, value_node=value_node
                    )
                else:
                    # Not a mapping - preserve as-is for validation
                    field_values[field_name] = build_field_source(key_node, value_node, context)
            elif field_type_args & {FieldSource[dict[KeySource[str], "Callback | Reference"]]}:
                # Handle dict[KeySource[str], Callback | Reference] with lazy import
                from ..callback import build_callback_or_reference

                if isinstance(value_node, yaml.MappingNode):
                    callbacks_dict = {}
                    for map_key_node, map_value_node in value_node.value:
                        map_key = context.yaml_constructor.construct_yaml_str(map_key_node)
                        callback_or_reference = build_callback_or_reference(map_value_node, context)
                        callbacks_dict[KeySource(value=map_key, key_node=map_key_node)] = (
                            callback_or_reference
                        )
                    field_values[field_name] = FieldSource(
                        value=callbacks_dict, key_node=key_node, value_node=value_node
                    )
                else:
                    # Not a mapping - preserve as-is for validation
                    field_values[field_name] = build_field_source(key_node, value_node, context)
            elif field_type_args & {FieldSource[dict[KeySource[str], "Header | Reference"]]}:
                # Handle dict[KeySource[str], Header | Reference] with lazy import
                from ..header import build_header_or_reference

                if isinstance(value_node, yaml.MappingNode):
                    headers_dict = {}
                    for map_key_node, map_value_node in value_node.value:
                        map_key = context.yaml_constructor.construct_yaml_str(map_key_node)
                        header_or_reference = build_header_or_reference(map_value_node, context)
                        headers_dict[KeySource(value=map_key, key_node=map_key_node)] = (
                            header_or_reference
                        )
                    field_values[field_name] = FieldSource(
                        value=headers_dict, key_node=key_node, value_node=value_node
                    )
                else:
                    # Not a mapping - preserve as-is for validation
                    field_values[field_name] = build_field_source(key_node, value_node, context)
            elif field_type_args & {FieldSource[dict[KeySource[str], "Link | Reference"]]}:
                # Handle dict[KeySource[str], Link | Reference] with lazy import
                from ..link import build_link_or_reference

                if isinstance(value_node, yaml.MappingNode):
                    links_dict = {}
                    for map_key_node, map_value_node in value_node.value:
                        map_key = context.yaml_constructor.construct_yaml_str(map_key_node)
                        link_or_reference = build_link_or_reference(map_value_node, context)
                        links_dict[KeySource(value=map_key, key_node=map_key_node)] = (
                            link_or_reference
                        )
                    field_values[field_name] = FieldSource(
                        value=links_dict, key_node=key_node, value_node=value_node
                    )
                else:
                    # Not a mapping - preserve as-is for validation
                    field_values[field_name] = build_field_source(key_node, value_node, context)

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


def build_field_source(
    key_node: yaml.Node,
    value_node: yaml.Node,
    context: Context,
) -> FieldSource[Any]:
    """
    Build a FieldSource from a YAML node.

    Constructs the Python value from the YAML node and wraps it in a FieldSource
    that preserves the original node locations for error reporting.

    Args:
        key_node: The YAML node for the field key
        value_node: The YAML node for the field value
        context: Parsing context

    Returns:
        A FieldSource containing the constructed value and node references
    """
    value = context.yaml_constructor.construct_object(value_node, deep=True)
    return FieldSource(value=value, key_node=key_node, value_node=value_node)
