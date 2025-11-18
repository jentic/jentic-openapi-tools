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
    Reference Object representation for OpenAPI 3.1.

    Allows for a reference to another document.

    Attributes:
        root_node: The top-level node representing the entire Reference object in the original source file
        ref: REQUIRED. The reference identifier. This MUST be in the form of a URI.
        summary: A short summary which by default SHOULD override that of the referenced component. If the referenced object-type does not allow a summary field, then this field has no effect.
        description: A description which by default SHOULD override that of the referenced component. CommonMark syntax MAY be used for rich text representation. If the referenced object-type does not allow a description field, then this field has no effect.
    """

    root_node: yaml.Node
    ref: FieldSource[str] | None = fixed_field(metadata={"yaml_name": "$ref"})
    summary: FieldSource[str] | None = fixed_field()
    description: FieldSource[str] | None = fixed_field()


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
        root = yaml.compose('''
        $ref: '#/components/schemas/Pet'
        summary: A Pet reference
        description: Reference to the Pet schema in components
        ''')
        reference = build(root)
        assert reference.ref.value == '#/components/schemas/Pet'
        assert reference.summary.value == 'A Pet reference'
        assert reference.description.value == 'Reference to the Pet schema in components'
    """
    return build_model(root, Reference, context=context)
