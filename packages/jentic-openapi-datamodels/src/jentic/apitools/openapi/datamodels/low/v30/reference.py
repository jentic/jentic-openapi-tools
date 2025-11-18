from dataclasses import dataclass

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, ValueSource, YAMLInvalidValue
from .builders import build_model


__all__ = ["Reference", "build"]


@dataclass(frozen=True, slots=True)
class Reference:
    """
    Reference Object representation for OpenAPI 3.0.

    A simple object to allow referencing other components in the OpenAPI Description,
    internally and externally.

    Note: In OpenAPI 3.0, Reference Objects only have the $ref field.
    Summary, description, and extensions were added in OpenAPI 3.1.

    Attributes:
        root_node: The top-level node representing the entire Reference object in the original source file
        ref: REQUIRED. The reference string. Must be in the format of a URI.
    """

    root_node: yaml.Node
    ref: FieldSource[str] | None = fixed_field(metadata={"yaml_name": "$ref"})


def build(
    root: yaml.Node, context: Context | None = None
) -> Reference | ValueSource[YAMLInvalidValue]:
    """
    Build a Reference object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A Reference object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose("$ref: '#/components/schemas/Pet'")
        reference = build(root)
        assert reference.ref.value == '#/components/schemas/Pet'
    """
    return build_model(root, Reference, context=context)
