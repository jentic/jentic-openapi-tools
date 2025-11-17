import re
from dataclasses import dataclass, field
from typing import cast

from ruamel import yaml

from ..context import Context
from ..extractors import extract_extension_fields
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .reference import Reference
from .response import Response, build_response_or_reference


__all__ = ["Responses", "build"]


@dataclass(frozen=True, slots=True)
class Responses:
    """
    Responses Object representation for OpenAPI 3.0.

    A container for the expected responses of an operation. The container maps a HTTP response code
    to the expected response.

    Attributes:
        root_node: The top-level node representing the entire Responses object in the original source file
        default: The documentation of responses other than the ones declared for specific HTTP response codes.
                Use this field to cover undeclared responses.
        responses: Maps HTTP status codes to their Response objects. The key is the HTTP status code
                  (e.g., "200", "404", "4XX") and the value is a Response object or Reference.
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    default: FieldSource[Response | Reference] | None = fixed_field()
    responses: dict[KeySource[str], Response | Reference] = field(default_factory=dict)
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> Responses | ValueSource[YAMLInvalidValue]:
    """
    Build a Responses object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A Responses object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose('''
        '200':
          description: successful operation
        '404':
          description: not found
        default:
          description: unexpected error
        ''')
        responses = build(root)
        assert '200' in {k.value for k in responses.responses.keys()}
    """
    context = context or Context()

    # Check if root is a MappingNode, if not return ValueSource with invalid data
    if not isinstance(root, yaml.MappingNode):
        value = context.yaml_constructor.construct_object(root, deep=True)
        return ValueSource(value=value, value_node=root)

    # Process each field to determine if it's default or a status code response
    responses = {}
    default: FieldSource[Response | Reference] | None = None

    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        if key == "default":
            # Handle default response - can be Response or Reference
            response_or_reference = build_response_or_reference(value_node, context)
            default = cast(
                FieldSource[Response | Reference],
                FieldSource(value=response_or_reference, key_node=key_node, value_node=value_node),
            )
        elif _HTTP_STATUS_CODE_PATTERN.match(key):
            # Valid HTTP status code (100-599) or pattern (1XX-5XX)
            response_or_reference = build_response_or_reference(value_node, context)
            responses[KeySource(value=key, key_node=key_node)] = response_or_reference

    # Create and return the Responses object with collected data
    return Responses(
        root_node=root,
        default=default,
        responses=responses,
        extensions=extract_extension_fields(root, context),
    )


# Pattern for valid HTTP status codes: 100-599 or wildcard patterns (1XX-5XX)
_HTTP_STATUS_CODE_PATTERN = re.compile(r"^([1-5]XX|[1-5][0-9]{2})$")
