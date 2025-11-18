from dataclasses import dataclass, field

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .builders import build_model


__all__ = ["XML", "build"]


@dataclass(frozen=True, slots=True)
class XML:
    """
    XML Object representation for OpenAPI 3.0.

    Attributes:
        root_node: The top-level node representing the entire XML object in the original source file
        name: Name of the XML element
        namespace: XML namespace
        prefix: XML namespace prefix
        attribute: Whether property is an attribute (deprecated in OpenAPI 3.2+)
        wrapped: Whether array is wrapped
        extensions: Specification extensions
    """

    root_node: yaml.Node
    name: FieldSource[str] | None = fixed_field()
    namespace: FieldSource[str] | None = fixed_field()
    prefix: FieldSource[str] | None = fixed_field()
    attribute: FieldSource[bool] | None = fixed_field()
    wrapped: FieldSource[bool] | None = fixed_field()
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(root: yaml.Node, context: Context | None = None) -> XML | ValueSource[YAMLInvalidValue]:
    """
    Build an XML object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        An XML object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).
    """
    return build_model(root, XML, context=context)
