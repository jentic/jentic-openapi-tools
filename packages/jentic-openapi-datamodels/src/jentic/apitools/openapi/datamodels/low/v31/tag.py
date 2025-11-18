from dataclasses import dataclass, field

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .builders import build_model
from .external_documentation import ExternalDocumentation


__all__ = ["Tag", "build"]


@dataclass(frozen=True, slots=True)
class Tag:
    """
    Tag Object representation for OpenAPI 3.1.

    Adds metadata to a single tag that is used by the Operation Object. It is not mandatory
    to have a Tag Object per tag defined in the Operation Object instances.

    Attributes:
        root_node: The top-level node representing the entire Tag object in the original source file
        name: The name of the tag. REQUIRED.
        description: A short description for the tag. CommonMark syntax MAY be used for rich text representation.
        external_docs: Additional external documentation for this tag.
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    name: FieldSource[str] | None = fixed_field()
    description: FieldSource[str] | None = fixed_field()
    external_docs: FieldSource["ExternalDocumentation"] | None = fixed_field(
        metadata={"yaml_name": "externalDocs"}
    )
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(root: yaml.Node, context: Context | None = None) -> Tag | ValueSource[YAMLInvalidValue]:
    """
    Build a Tag object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A Tag object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose("name: pet\\ndescription: Everything about your Pets")
        tag = build(root)
        assert tag.name.value == 'pet'
    """
    return build_model(root, Tag, context=context)
