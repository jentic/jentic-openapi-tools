from dataclasses import dataclass, field

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .builders import build_model


__all__ = ["ExternalDocumentation", "build"]


@dataclass(frozen=True, slots=True)
class ExternalDocumentation:
    """
    External Documentation Object representation for OpenAPI 3.0.

    Allows referencing an external resource for extended documentation.

    Attributes:
        root_node: The top-level node representing the entire External Documentation object in the original source file
        description: A short description of the target documentation. CommonMark syntax MAY be used for rich text representation.
        url: The URL for the target documentation. REQUIRED. Value MUST be in the format of a URL.
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    description: FieldSource[str] | None = fixed_field()
    url: FieldSource[str] | None = fixed_field()
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> ExternalDocumentation | ValueSource[YAMLInvalidValue]:
    """
    Build an ExternalDocumentation object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        An ExternalDocumentation object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose("url: https://example.com\\ndescription: Find more info here")
        external_docs = build(root)
        assert external_docs.url.value == 'https://example.com'
    """
    return build_model(root, ExternalDocumentation, context=context)
