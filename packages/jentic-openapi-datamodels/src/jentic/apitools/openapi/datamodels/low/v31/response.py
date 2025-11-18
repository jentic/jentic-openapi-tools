from dataclasses import dataclass, field

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .builders import build_model
from .header import Header
from .link import Link
from .media_type import MediaType
from .reference import Reference
from .reference import build as build_reference


__all__ = ["Response", "build", "build_response_or_reference"]


@dataclass(frozen=True, slots=True)
class Response:
    """
    Response Object representation for OpenAPI 3.1.

    Describes a single response from an API Operation, including design-time, static links
    to operations based on the response.

    Attributes:
        root_node: The top-level node representing the entire Response object in the original source file
        description: A description of the response. CommonMark syntax MAY be used for rich text representation.
        headers: Maps a header name to its definition.
        content: A map containing descriptions of potential response payloads. The key is a media type or media type range
                and the value describes it. For responses that match multiple keys, only the most specific key is applicable.
        links: A map of operations links that can be followed from the response. The key is a short name for the link,
              following the naming constraints of the Components Object.
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    description: FieldSource[str] | None = fixed_field()
    headers: FieldSource[dict[KeySource[str], "Header | Reference"]] | None = fixed_field()
    content: FieldSource[dict[KeySource[str], "MediaType"]] | None = fixed_field()
    links: FieldSource[dict[KeySource[str], "Link | Reference"]] | None = fixed_field()
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> Response | ValueSource[YAMLInvalidValue]:
    """
    Build a Response object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A Response object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose('''
        description: successful operation
        content:
          application/json:
            schema:
              type: object
        ''')
        response = build(root)
        assert response.description.value == 'successful operation'
    """
    return build_model(root, Response, context=context)


def build_response_or_reference(
    node: yaml.Node, context: Context
) -> Response | Reference | ValueSource[YAMLInvalidValue]:
    """
    Build either a Response or Reference from a YAML node.

    This helper handles the polymorphic nature of OpenAPI where many fields
    can contain either a Response object or a Reference object ($ref).

    Args:
        node: The YAML node to parse
        context: Parsing context

    Returns:
        A Response, Reference, or ValueSource if the node is invalid
    """
    # Check if it's a reference (has $ref key)
    if isinstance(node, yaml.MappingNode):
        for key_node, _ in node.value:
            key = context.yaml_constructor.construct_yaml_str(key_node)
            if key == "$ref":
                return build_reference(node, context)

    # Otherwise, try to build as Response
    return build(node, context)
