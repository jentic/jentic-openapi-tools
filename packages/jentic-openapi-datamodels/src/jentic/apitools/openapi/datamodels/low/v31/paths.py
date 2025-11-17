from dataclasses import dataclass, field

from ruamel import yaml

from ..context import Context
from ..extractors import extract_extension_fields
from ..sources import KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .path_item import PathItem
from .path_item import build as build_path_item


__all__ = ["Paths", "build"]


@dataclass(frozen=True, slots=True)
class Paths:
    """
    Paths Object representation for OpenAPI 3.1.

    Holds the relative paths to the individual endpoints and their operations.
    The paths are appended to the server URL to construct the full URL.

    Path field names MUST begin with a forward slash (/). Path templating is supported
    (e.g., /users/{id}). When matching URLs, concrete (non-templated) paths are matched
    before templated paths. Templated paths with the same hierarchy but different templated
    names are not allowed.

    Attributes:
        root_node: The top-level node representing the entire Paths object in the original source file
        paths: Map of path strings to Path Item Objects. Each key is a relative path that MUST begin
               with a forward slash (/). Supports path templating with curly braces.
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    paths: dict[KeySource[str], PathItem] = field(default_factory=dict)
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(root: yaml.Node, context: Context | None = None) -> Paths | ValueSource[YAMLInvalidValue]:
    """
    Build a Paths object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A Paths object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose('''
        /users:
          get:
            summary: Get all users
            responses:
              '200':
                description: Success
        /users/{id}:
          get:
            summary: Get user by ID
            parameters:
              - name: id
                in: path
                required: true
                schema:
                  type: integer
            responses:
              '200':
                description: Success
        ''')
        paths = build(root)
        assert '/users' in {k.value for k in paths.paths.keys()}
    """
    context = context or Context()

    # Check if root is a MappingNode, if not return ValueSource with invalid data
    if not isinstance(root, yaml.MappingNode):
        value = context.yaml_constructor.construct_object(root, deep=True)
        return ValueSource(value=value, value_node=root)

    # Extract extensions first
    extensions = extract_extension_fields(root, context)
    extension_properties = {k.value for k in extensions.keys()}

    # Process each field to determine if it's a path (not an extension)
    paths = {}

    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        if key not in extension_properties and key.startswith("/"):
            # Path field (starts with / and not an extension) - build as Path Item
            paths[KeySource(value=key, key_node=key_node)] = build_path_item(value_node, context)

    # Create and return the Paths object with collected data
    return Paths(
        root_node=root,
        paths=paths,
        extensions=extensions,
    )
