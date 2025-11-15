from dataclasses import dataclass, field

from ruamel import yaml

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.extractors import extract_extension_fields
from jentic.apitools.openapi.datamodels.low.sources import (
    KeySource,
    ValueSource,
    YAMLInvalidValue,
    YAMLValue,
)
from jentic.apitools.openapi.datamodels.low.v30.reference import (
    Reference,
)
from jentic.apitools.openapi.datamodels.low.v30.reference import (
    build as build_reference,
)


__all__ = ["Callback", "build", "build_callback_or_reference"]


@dataclass(frozen=True, slots=True)
class Callback:
    """
    Callback Object representation for OpenAPI 3.0.

    A map of possible out-of-band callbacks related to the parent operation. Each value in the map
    is a Path Item Object that describes a set of requests that may be initiated by the API provider
    and the expected responses.

    The key is a runtime expression that identifies a URL to use for the callback operation.

    Attributes:
        root_node: The top-level node representing the entire Callback object in the original source file
        expressions: Map of expression keys to Path Item Objects. Each key is a runtime expression
                    that will be evaluated to determine the callback URL. Since Path Item Object is not
                    yet implemented, values are stored as generic YAML values.
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    expressions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> Callback | ValueSource[YAMLInvalidValue]:
    """
    Build a Callback object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A Callback object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose('''
        '{$request.body#/callbackUrl}':
          post:
            requestBody:
              required: true
              content:
                application/json:
                  schema:
                    type: object
            responses:
              '200':
                description: callback successfully processed
        ''')
        callback = build(root)
        assert len(callback.expressions) > 0
    """
    context = context or Context()

    # Check if root is a MappingNode, if not return ValueSource with invalid data
    if not isinstance(root, yaml.MappingNode):
        value = context.yaml_constructor.construct_object(root, deep=True)
        return ValueSource(value=value, value_node=root)

    # Extract extensions first
    extensions = extract_extension_fields(root, context)
    extension_properties = {k.value for k in extensions.keys()}

    # Process each field to determine if it's an expression (not an extension)
    expressions: dict[KeySource[str], ValueSource[YAMLValue]] = {}

    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        if key not in extension_properties:
            # Expression field (any key that's not an extension)
            # TODO: When Path Item Object is implemented, build it here instead of raw value
            value = context.yaml_constructor.construct_object(value_node, deep=True)
            expressions[KeySource(value=key, key_node=key_node)] = ValueSource(
                value=value, value_node=value_node
            )

    # Create and return the Callback object with collected data
    return Callback(
        root_node=root,
        expressions=expressions,
        extensions=extensions,
    )


def build_callback_or_reference(
    node: yaml.Node, context: Context
) -> Callback | Reference | ValueSource[YAMLInvalidValue]:
    """
    Build either a Callback or Reference from a YAML node.

    This helper handles the polymorphic nature of OpenAPI where many fields
    can contain either a Callback object or a Reference object ($ref).

    Args:
        node: The YAML node to parse
        context: Parsing context

    Returns:
        A Callback, Reference, or ValueSource if the node is invalid
    """
    # Check if it's a reference (has $ref key)
    if isinstance(node, yaml.MappingNode):
        for key_node, _ in node.value:
            key = context.yaml_constructor.construct_yaml_str(key_node)
            if key == "$ref":
                return build_reference(node, context)

    # Otherwise, try to build as Callback
    return build(node, context)
