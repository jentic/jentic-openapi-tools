from dataclasses import dataclass, field

from ruamel import yaml

from ..context import Context
from ..extractors import extract_extension_fields
from ..sources import KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .path_item import PathItem
from .path_item import build as build_path_item
from .reference import Reference
from .reference import build as build_reference


__all__ = ["Callback", "build", "build_callback_or_reference"]


@dataclass(frozen=True, slots=True)
class Callback:
    """
    Callback Object representation for OpenAPI 3.1.

    A map of possible out-of-band callbacks related to the parent operation. Each value in the map
    is a Path Item Object that describes a set of requests that may be initiated by the API provider
    and the expected responses.

    The key is a runtime expression that identifies a URL to use for the callback operation.

    Attributes:
        root_node: The top-level node representing the entire Callback object in the original source file
        path_items: Map of expression keys to Path Item Objects. Each key is a runtime expression
                    that will be evaluated to determine the callback URL.
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    path_items: dict[KeySource[str], PathItem] = field(default_factory=dict)
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
        assert len(callback.path_items) > 0
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
    path_items: dict[KeySource[str], PathItem | ValueSource[YAMLInvalidValue]] = {}

    for key_node, value_node in root.value:
        expression = context.yaml_constructor.construct_yaml_str(key_node)

        if expression not in extension_properties:
            # Expression field (any key that's not an extension) - build as Path Item
            path_item_obj = build_path_item(value_node, context)
            path_items[KeySource(value=expression, key_node=key_node)] = path_item_obj

    # Create and return the Callback object with collected data
    return Callback(
        root_node=root,
        path_items=path_items,  # type: ignore[arg-type]
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
