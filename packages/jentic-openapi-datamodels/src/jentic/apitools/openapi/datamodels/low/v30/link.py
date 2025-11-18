from dataclasses import dataclass, field, replace

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .builders import build_field_source, build_model
from .reference import Reference
from .reference import build as build_reference
from .server import Server
from .server import build as build_server


__all__ = ["Link", "build", "build_link_or_reference"]


@dataclass(frozen=True, slots=True)
class Link:
    """
    Link Object representation for OpenAPI 3.0.

    The Link Object represents a possible design-time link for a response.

    Attributes:
        root_node: The top-level node representing the entire Link object in the original source file
        operation_ref: A relative or absolute URI reference to an OAS operation.
        operation_id: The name of an existing, resolvable OAS operation.
        parameters: A map representing parameters to pass to an operation as specified with operationId
                   or identified via operationRef.
        request_body: A literal value or {expression} to use as a request body when calling the target operation.
        description: A description of the link. CommonMark syntax MAY be used for rich text representation.
        server: A server object to be used by the target operation.
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    operation_ref: FieldSource[str] | None = fixed_field(metadata={"yaml_name": "operationRef"})
    operation_id: FieldSource[str] | None = fixed_field(metadata={"yaml_name": "operationId"})
    parameters: FieldSource[dict[KeySource[str], ValueSource[YAMLValue]]] | None = fixed_field()
    request_body: FieldSource[YAMLValue] | None = fixed_field(metadata={"yaml_name": "requestBody"})
    description: FieldSource[str] | None = fixed_field()
    server: FieldSource[Server] | None = fixed_field()
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(root: yaml.Node, context: Context | None = None) -> Link | ValueSource[YAMLInvalidValue]:
    """
    Build a Link object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A Link object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose("operationId: getUserById\\nparameters:\\n  userId: $response.body#/id")
        link = build(root)
        assert link.operation_id.value == 'getUserById'
    """
    context = context or Context()

    # Use build_model for initial construction
    link = build_model(root, Link, context=context)

    # If build_model returned ValueSource (invalid node), return it immediately
    if not isinstance(link, Link):
        return link

    # Manually handle nested server object and parameters dict
    replacements = {}
    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        if key == "server":
            # Handle nested Server object - child builder handles invalid nodes
            replacements["server"] = FieldSource(
                value=build_server(value_node, context=context),
                key_node=key_node,
                value_node=value_node,
            )
        elif key == "parameters":
            # Handle parameters map with KeySource/ValueSource wrapping
            if isinstance(value_node, yaml.MappingNode):
                params_dict: dict[KeySource[str], ValueSource[YAMLValue]] = {}
                for param_key_node, param_value_node in value_node.value:
                    param_key = context.yaml_constructor.construct_yaml_str(param_key_node)
                    param_value = context.yaml_constructor.construct_object(
                        param_value_node, deep=True
                    )
                    params_dict[KeySource(value=param_key, key_node=param_key_node)] = ValueSource(
                        value=param_value, value_node=param_value_node
                    )
                replacements["parameters"] = FieldSource(
                    value=params_dict, key_node=key_node, value_node=value_node
                )
            else:
                # Not a mapping - preserve as-is for validation
                replacements["parameters"] = build_field_source(key_node, value_node, context)

    # Apply all replacements at once
    if replacements:
        link = replace(link, **replacements)

    return link


def build_link_or_reference(
    node: yaml.Node, context: Context
) -> Link | Reference | ValueSource[YAMLInvalidValue]:
    """
    Build either a Link or Reference from a YAML node.

    This helper handles the polymorphic nature of OpenAPI where many fields
    can contain either a Link object or a Reference object ($ref).

    Args:
        node: The YAML node to parse
        context: Parsing context

    Returns:
        A Link, Reference, or ValueSource if the node is invalid
    """
    # Check if it's a reference (has $ref key)
    if isinstance(node, yaml.MappingNode):
        for key_node, _ in node.value:
            key = context.yaml_constructor.construct_yaml_str(key_node)
            if key == "$ref":
                return build_reference(node, context)

    # Otherwise, try to build as Link
    return build(node, context)
