from dataclasses import dataclass

from ruamel import yaml
from ruamel.yaml import MappingNode, SequenceNode

from ..context import Context
from ..fields import patterned_field
from ..sources import KeySource, ValueSource, YAMLInvalidValue


__all__ = ["SecurityRequirement", "build"]


@dataclass(frozen=True, slots=True)
class SecurityRequirement:
    """
    Security Requirement Object representation for OpenAPI 3.0.

    Lists the required security schemes to execute an operation. Each named security scheme
    must correspond to a security scheme declared in the Security Schemes under the Components Object.

    When multiple Security Requirement Objects are specified, only ONE needs to be satisfied
    to authorize a request. Within a single Security Requirement Object, ALL schemes must be satisfied.

    Note: An empty Security Requirement object ({}) makes security optional for the operation.
    Note: Specification extensions (x-* fields) are NOT supported for Security Requirement objects.

    Attributes:
        root_node: The top-level node representing the entire Security Requirement object in the original source file
        requirements: Dictionary mapping security scheme names to arrays of scope strings.
                     For OAuth2 schemes, the array contains required scopes.
                     For other schemes (API key, HTTP), the array is empty.
    """

    root_node: yaml.Node
    requirements: ValueSource[dict[KeySource[str], ValueSource[list[ValueSource[str]]]]] | None = (
        patterned_field()
    )


def build(
    root: yaml.Node, context: Context | None = None
) -> SecurityRequirement | ValueSource[YAMLInvalidValue]:
    """
    Build a SecurityRequirement object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A SecurityRequirement object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose("api_key: []")
        security_req = build(root)
        assert security_req.requirements is not None
    """
    context = context or Context()

    if not isinstance(root, MappingNode):
        # Preserve invalid root data instead of returning None
        value = context.yaml_constructor.construct_object(root, deep=True)
        return ValueSource(value=value, value_node=root)

    requirements_dict: dict[KeySource[str], ValueSource[list[ValueSource[str]]]] = {}

    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        # Skip non-string keys
        if not isinstance(key, str):
            continue

        # Security scheme requirement field
        # For requirements, we need to wrap each scope string in ValueSource
        if isinstance(value_node, SequenceNode):
            # Wrap each scope string in the array with its source node
            scope_list: list[ValueSource[str]] = []
            for item_node in value_node.value:
                item_value = context.yaml_constructor.construct_object(item_node, deep=True)
                scope_list.append(ValueSource(value=item_value, value_node=item_node))

            requirements_dict[KeySource(value=key, key_node=key_node)] = ValueSource(
                value=scope_list, value_node=value_node
            )
        else:
            # Not a sequence - preserve as-is for validation to catch
            value = context.yaml_constructor.construct_object(value_node, deep=True)
            requirements_dict[KeySource(value=key, key_node=key_node)] = ValueSource(
                value=value, value_node=value_node
            )

    return SecurityRequirement(
        root_node=root,
        requirements=(
            ValueSource(value=requirements_dict, value_node=root) if requirements_dict else None
        ),
    )
