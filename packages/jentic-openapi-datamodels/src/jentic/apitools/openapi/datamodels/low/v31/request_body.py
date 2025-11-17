from dataclasses import dataclass, field

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .builders import build_model
from .media_type import MediaType
from .reference import Reference
from .reference import build as build_reference


__all__ = ["RequestBody", "build", "build_request_body_or_reference"]


@dataclass(frozen=True, slots=True)
class RequestBody:
    """
    Request Body Object representation for OpenAPI 3.1.

    Describes a single request body.

    Attributes:
        root_node: The top-level node representing the entire Request Body object in the original source file
        description: A brief description of the request body. CommonMark syntax MAY be used for rich text representation.
        content: The content of the request body. The key is a media type or media type range and the value describes it.
                For requests that match multiple keys, only the most specific key is applicable.
        required: Determines if the request body is required in the request. Defaults to false.
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    description: FieldSource[str] | None = fixed_field()
    content: FieldSource[dict[KeySource[str], "MediaType"]] | None = fixed_field()
    required: FieldSource[bool] | None = fixed_field()
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> RequestBody | ValueSource[YAMLInvalidValue]:
    """
    Build a RequestBody object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A RequestBody object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose('''
        description: user to add to the system
        required: true
        content:
          application/json:
            schema:
              type: object
        ''')
        request_body = build(root)
        assert request_body.description.value == 'user to add to the system'
    """
    context = context or Context()

    # Use build_model for initial construction
    request_body = build_model(root, RequestBody, context=context)

    # If build_model returned ValueSource (invalid node), return it immediately
    if not isinstance(request_body, RequestBody):
        return request_body

    return request_body


def build_request_body_or_reference(
    node: yaml.Node, context: Context
) -> RequestBody | Reference | ValueSource[YAMLInvalidValue]:
    """
    Build either a RequestBody or Reference from a YAML node.

    This helper handles the polymorphic nature of OpenAPI where many fields
    can contain either a RequestBody object or a Reference object ($ref).

    Args:
        node: The YAML node to parse
        context: Parsing context

    Returns:
        A RequestBody, Reference, or ValueSource if the node is invalid
    """
    # Check if it's a reference (has $ref key)
    if isinstance(node, yaml.MappingNode):
        for key_node, _ in node.value:
            key = context.yaml_constructor.construct_yaml_str(key_node)
            if key == "$ref":
                return build_reference(node, context)

    # Otherwise, try to build as RequestBody
    return build(node, context)
