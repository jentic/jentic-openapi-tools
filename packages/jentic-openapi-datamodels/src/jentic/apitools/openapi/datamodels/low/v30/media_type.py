from dataclasses import dataclass, field, replace

from ruamel import yaml

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.fields import fixed_field
from jentic.apitools.openapi.datamodels.low.model_builder import build_model
from jentic.apitools.openapi.datamodels.low.sources import (
    FieldSource,
    KeySource,
    ValueSource,
    YAMLInvalidValue,
    YAMLValue,
)
from jentic.apitools.openapi.datamodels.low.v30.encoding import Encoding
from jentic.apitools.openapi.datamodels.low.v30.encoding import build as build_encoding
from jentic.apitools.openapi.datamodels.low.v30.example import (
    Example,
    build_example_or_reference,
)
from jentic.apitools.openapi.datamodels.low.v30.reference import Reference
from jentic.apitools.openapi.datamodels.low.v30.schema import (
    Schema,
    build_schema_or_reference,
)


__all__ = ["MediaType", "build"]


@dataclass(frozen=True, slots=True)
class MediaType:
    """
    Media Type Object representation for OpenAPI 3.0.

    Each Media Type Object provides schema and examples for the media type identified by its key.

    Attributes:
        root_node: The top-level node representing the entire Media Type object in the original source file
        schema: The schema defining the content of the request, response, or parameter.
        example: Example of the media type. The example SHOULD match the specified schema and encoding properties if present.
        examples: Examples of the media type. Each example SHOULD contain a value in the correct format as specified in the parameter encoding.
        encoding: A map between a property name and its encoding information. The key, being the property name,
                 MUST exist in the schema as a property. The encoding object SHALL only apply to requestBody objects
                 when the media type is multipart or application/x-www-form-urlencoded.
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    schema: FieldSource[Schema | Reference] | None = fixed_field()
    example: FieldSource[YAMLValue] | None = fixed_field()
    examples: FieldSource[dict[KeySource[str], Example | Reference]] | None = fixed_field()
    encoding: FieldSource[dict[KeySource[str], Encoding]] | None = fixed_field()
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> MediaType | ValueSource[YAMLInvalidValue]:
    """
    Build a MediaType object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A MediaType object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose('''
        schema:
          type: string
        examples:
          user:
            value: John Doe
        ''')
        media_type = build(root)
        assert media_type.schema.value.type.value == 'string'
    """
    context = context or Context()

    # Use build_model to handle simple fields
    media_type = build_model(root, MediaType, context=context)

    # If build_model returned ValueSource (invalid node), return it immediately
    if not isinstance(media_type, MediaType):
        return media_type

    # Manually handle nested complex fields
    replacements = {}
    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        if key == "schema":
            # Handle schema field - can be Schema or Reference
            schema_or_reference = build_schema_or_reference(value_node, context)
            replacements["schema"] = FieldSource(
                value=schema_or_reference, key_node=key_node, value_node=value_node
            )
        elif key == "examples":
            # Handle examples field - map of Example or Reference objects
            if isinstance(value_node, yaml.MappingNode):
                examples_dict: dict[
                    KeySource[str], Example | Reference | ValueSource[YAMLInvalidValue]
                ] = {}
                for example_key_node, example_value_node in value_node.value:
                    example_key = context.yaml_constructor.construct_yaml_str(example_key_node)
                    # Build Example or Reference - child builder handles invalid nodes
                    example_or_reference = build_example_or_reference(example_value_node, context)
                    examples_dict[KeySource(value=example_key, key_node=example_key_node)] = (
                        example_or_reference
                    )
                replacements["examples"] = FieldSource(
                    value=examples_dict, key_node=key_node, value_node=value_node
                )
            else:
                # Not a mapping - preserve as-is for validation
                value = context.yaml_constructor.construct_object(value_node, deep=True)
                replacements["examples"] = FieldSource(
                    value=value, key_node=key_node, value_node=value_node
                )
        elif key == "encoding":
            # Handle encoding field - map of Encoding objects
            if isinstance(value_node, yaml.MappingNode):
                encoding_dict: dict[KeySource[str], Encoding | ValueSource[YAMLInvalidValue]] = {}
                for encoding_key_node, encoding_value_node in value_node.value:
                    encoding_key = context.yaml_constructor.construct_yaml_str(encoding_key_node)
                    # Build Encoding - child builder handles invalid nodes
                    encoding_obj = build_encoding(encoding_value_node, context)
                    encoding_dict[KeySource(value=encoding_key, key_node=encoding_key_node)] = (
                        encoding_obj
                    )
                replacements["encoding"] = FieldSource(
                    value=encoding_dict, key_node=key_node, value_node=value_node
                )
            else:
                # Not a mapping - preserve as-is for validation
                value = context.yaml_constructor.construct_object(value_node, deep=True)
                replacements["encoding"] = FieldSource(
                    value=value, key_node=key_node, value_node=value_node
                )

    # Apply all replacements at once
    if replacements:
        media_type = replace(media_type, **replacements)

    return media_type
