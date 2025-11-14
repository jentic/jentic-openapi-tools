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
from jentic.apitools.openapi.datamodels.low.v30.example import (
    Example,
    build_example_or_reference,
)
from jentic.apitools.openapi.datamodels.low.v30.reference import Reference
from jentic.apitools.openapi.datamodels.low.v30.schema import (
    Schema,
    build_schema_or_reference,
)


__all__ = ["Header", "build"]


@dataclass(frozen=True, slots=True)
class Header:
    """
    Header Object representation for OpenAPI 3.0.

    The Header Object follows the structure of the Parameter Object, including determining its
    serialization strategy based on whether schema or content is present, with the following changes:
    - name MUST NOT be specified, it is given in the corresponding headers map.
    - in MUST NOT be specified, it is implicitly in header.
    - All traits that are affected by the location MUST be applicable to a location of header
      (for example, style). This means that allowEmptyValue and allowReserved MUST NOT be used,
      and style, if used, MUST be limited to "simple".

    Attributes:
        root_node: The top-level node representing the entire Header object in the original source file
        description: A brief description of the header. CommonMark syntax MAY be used for rich text representation.
        required: Determines whether this header is mandatory. Default value is false.
        deprecated: Specifies that a header is deprecated and SHOULD be transitioned out of usage. Default value is false.
        style: Describes how the header value will be serialized depending on the type of the header value.
               If used, MUST be limited to "simple".
        explode: When this is true, header values of type array or object generate separate parameters for each value of the array or key-value pair of the map. Default value is false.
        schema: The schema defining the type used for the header.
        example: Example of the header's potential value. The example SHOULD match the specified schema and encoding properties if present.
        examples: Examples of the header's potential value. Each example SHOULD contain a value in the correct format as specified in the header encoding.
        content: A map containing the representations for the header. The key is the media type and the value describes it.
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    description: FieldSource[str] | None = fixed_field()
    required: FieldSource[bool] | None = fixed_field()
    deprecated: FieldSource[bool] | None = fixed_field()
    style: FieldSource[str] | None = fixed_field()
    explode: FieldSource[bool] | None = fixed_field()
    schema: FieldSource[Schema | Reference] | None = fixed_field()
    example: FieldSource[YAMLValue] | None = fixed_field()
    examples: (
        FieldSource[dict[KeySource[str], Example | Reference | ValueSource[YAMLInvalidValue]]]
        | None
    ) = fixed_field()
    content: FieldSource[dict[KeySource[str], ValueSource[YAMLValue]]] | None = fixed_field()
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> Header | ValueSource[YAMLInvalidValue]:
    """
    Build a Header object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A Header object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose('''
        description: The number of allowed requests in the current period
        schema:
          type: integer
        ''')
        header = build(root)
        assert header.description.value == 'The number of allowed requests in the current period'
    """
    context = context or Context()

    # Use build_model to handle simple fields
    header = build_model(root, Header, context=context)

    # If build_model returned ValueSource (invalid node), return it immediately
    if not isinstance(header, Header):
        return header

    # Manually handle nested complex fields
    replacements = {}
    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        if key == "schema":
            # Handle schema field - can be Schema or Reference
            schema_or_ref = build_schema_or_reference(value_node, context)
            replacements["schema"] = FieldSource(
                value=schema_or_ref, key_node=key_node, value_node=value_node
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
                    examples_dict[KeySource(value=example_key, key_node=example_key_node)] = (
                        build_example_or_reference(example_value_node, context)
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
        elif key == "content":
            # Handle content field - map of media types (not yet fully modeled)
            if isinstance(value_node, yaml.MappingNode):
                content_dict: dict[KeySource[str], ValueSource[YAMLValue]] = {}
                for content_key_node, content_value_node in value_node.value:
                    content_key = context.yaml_constructor.construct_yaml_str(content_key_node)
                    content_value = context.yaml_constructor.construct_object(
                        content_value_node, deep=True
                    )
                    content_dict[KeySource(value=content_key, key_node=content_key_node)] = (
                        ValueSource(value=content_value, value_node=content_value_node)
                    )
                replacements["content"] = FieldSource(
                    value=content_dict, key_node=key_node, value_node=value_node
                )
            else:
                # Not a mapping - preserve as-is for validation
                value = context.yaml_constructor.construct_object(value_node, deep=True)
                replacements["content"] = FieldSource(
                    value=value, key_node=key_node, value_node=value_node
                )

    # Apply all replacements at once
    if replacements:
        header = replace(header, **replacements)

    return header
