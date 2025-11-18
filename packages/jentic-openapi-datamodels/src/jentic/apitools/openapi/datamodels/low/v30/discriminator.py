from dataclasses import dataclass

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue
from .builders import build_model


__all__ = ["Discriminator", "build"]


@dataclass(frozen=True, slots=True)
class Discriminator:
    """
    Discriminator Object representation for OpenAPI 3.0.

    When request bodies or response payloads may be one of a number of different schemas,
    a discriminator object can be used to aid in serialization, deserialization, and validation.

    Note: In OpenAPI 3.0.x, the Discriminator Object does not support Specification Extensions.
    This changes in OpenAPI 3.1.x where extensions are permitted.

    Attributes:
        root_node: The top-level node representing the entire Discriminator object in the original source file
        property_name: REQUIRED. The name of the property in the payload that will hold the discriminator value
        mapping: An optional mapping of discriminator values to schema names or references
    """

    root_node: yaml.Node
    property_name: FieldSource[str] | None = fixed_field(metadata={"yaml_name": "propertyName"})
    mapping: FieldSource[dict[KeySource[str], ValueSource[str]]] | None = fixed_field()


def build(
    root: yaml.Node, context: Context | None = None
) -> Discriminator | ValueSource[YAMLInvalidValue]:
    """
    Build a Discriminator object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A Discriminator object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose("propertyName: petType\\nmapping:\\n  dog: Dog\\n  cat: Cat")
        discriminator = build(root)
        assert discriminator.property_name.value == 'petType'
    """
    return build_model(root, Discriminator, context=context)
