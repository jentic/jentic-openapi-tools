from dataclasses import dataclass, field, replace

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .builders import build_model
from .operation import Operation
from .operation import build as build_operation
from .parameter import Parameter
from .reference import Reference
from .server import Server


__all__ = ["PathItem", "build"]


@dataclass(frozen=True, slots=True)
class PathItem:
    """
    Path Item Object representation for OpenAPI 3.1.

    Describes the operations available on a single path. A Path Item may be empty,
    due to ACL constraints.

    Attributes:
        root_node: The top-level node representing the entire Path Item object in the original source file
        ref: Allows referencing an external definition of this path item
        summary: Optional string summary intended to apply to all operations in this path
        description: Optional string description (may contain CommonMark syntax)
        get: Definition of a GET operation on this path
        put: Definition of a PUT operation on this path
        post: Definition of a POST operation on this path
        delete: Definition of a DELETE operation on this path
        options: Definition of an OPTIONS operation on this path
        head: Definition of a HEAD operation on this path
        patch: Definition of a PATCH operation on this path
        trace: Definition of a TRACE operation on this path
        servers: Alternative server array to service all operations in this path
        parameters: List of parameters that are applicable for all operations in this path
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    ref: FieldSource[str] | None = fixed_field(metadata={"yaml_name": "$ref"})
    summary: FieldSource[str] | None = fixed_field()
    description: FieldSource[str] | None = fixed_field()
    get: FieldSource[Operation] | None = fixed_field()
    put: FieldSource[Operation] | None = fixed_field()
    post: FieldSource[Operation] | None = fixed_field()
    delete: FieldSource[Operation] | None = fixed_field()
    options: FieldSource[Operation] | None = fixed_field()
    head: FieldSource[Operation] | None = fixed_field()
    patch: FieldSource[Operation] | None = fixed_field()
    trace: FieldSource[Operation] | None = fixed_field()
    servers: FieldSource[list["Server"]] | None = fixed_field()
    parameters: FieldSource[list["Parameter | Reference"]] | None = fixed_field()
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> PathItem | ValueSource[YAMLInvalidValue]:
    """
    Build a PathItem object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A PathItem object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose('''
        summary: User operations
        get:
          summary: List users
          responses:
            '200':
              description: successful operation
        post:
          summary: Create user
          responses:
            '201':
              description: user created
        ''')
        path_item = build(root)
        assert path_item.get is not None
        assert path_item.post is not None
    """
    context = context or Context()

    # Use build_model for initial construction
    path_item = build_model(root, PathItem, context=context)

    # If build_model returned ValueSource (invalid node), return it immediately
    if not isinstance(path_item, PathItem):
        return path_item

    # Manually handle nested complex fields
    replacements = {}
    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        # Handle HTTP method operation fields
        if key in ("get", "put", "post", "delete", "options", "head", "patch", "trace"):
            operation_obj = build_operation(value_node, context)
            replacements[key] = FieldSource(
                value=operation_obj, key_node=key_node, value_node=value_node
            )

    # Apply all replacements at once
    if replacements:
        path_item = replace(path_item, **replacements)

    return path_item
