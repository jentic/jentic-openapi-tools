from dataclasses import dataclass, field

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .builders import build_model


__all__ = ["ServerVariable", "build"]


@dataclass(frozen=True, slots=True)
class ServerVariable:
    """
    Server Variable Object representation for OpenAPI 3.1.

    An object representing a Server Variable for server URL template substitution.

    Attributes:
        root_node: The top-level node representing the entire ServerVariable object in the original source file
        enum: An enumeration of string values to be used if the substitution options are from a limited set. The array SHOULD NOT be empty.
        default: REQUIRED. The default value to use for substitution, which SHALL be sent if an alternate value is not supplied. If the enum is defined, the value SHOULD exist in the enum's values.
        description: An optional description for the server variable. CommonMark syntax MAY be used for rich text representation.
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    enum: FieldSource[list[ValueSource[str]]] | None = fixed_field()
    default: FieldSource[str] | None = fixed_field()
    description: FieldSource[str] | None = fixed_field()
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> ServerVariable | ValueSource[YAMLInvalidValue]:
    """
    Build a ServerVariable object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A ServerVariable object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose('''
        default: production
        enum:
          - production
          - staging
          - development
        description: The deployment environment
        ''')
        server_variable = build(root)
        assert server_variable.default.value == 'production'
        assert len(server_variable.enum.value) == 3
        assert server_variable.enum.value[0].value == 'production'
    """
    return build_model(root, ServerVariable, context=context)
