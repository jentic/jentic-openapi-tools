from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .builders import build_model
from .example import Example
from .reference import Reference
from .reference import build as build_reference
from .schema import Schema


if TYPE_CHECKING:
    from .media_type import MediaType


__all__ = ["Header", "build", "build_header_or_reference"]


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
    schema: FieldSource["Schema | Reference"] | None = fixed_field()
    example: FieldSource[YAMLValue] | None = fixed_field()
    examples: FieldSource[dict[KeySource[str], "Example | Reference"]] | None = fixed_field()
    content: FieldSource[dict[KeySource[str], "MediaType"]] | None = fixed_field()
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
    return build_model(root, Header, context=context)


def build_header_or_reference(
    node: yaml.Node, context: Context
) -> Header | Reference | ValueSource[YAMLInvalidValue]:
    """
    Build either a Header or Reference from a YAML node.

    This helper handles the polymorphic nature of OpenAPI where many fields
    can contain either a Header object or a Reference object ($ref).

    Args:
        node: The YAML node to parse
        context: Parsing context

    Returns:
        A Header, Reference, or ValueSource if the node is invalid
    """
    # Check if it's a reference (has $ref key)
    if isinstance(node, yaml.MappingNode):
        for key_node, _ in node.value:
            key = context.yaml_constructor.construct_yaml_str(key_node)
            if key == "$ref":
                return build_reference(node, context)

    # Otherwise, try to build as Header
    return build(node, context)
