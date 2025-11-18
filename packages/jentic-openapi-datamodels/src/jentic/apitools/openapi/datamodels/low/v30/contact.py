from dataclasses import dataclass, field

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .builders import build_model


__all__ = ["Contact", "build"]


@dataclass(frozen=True, slots=True)
class Contact:
    """
    Contact Object representation for OpenAPI 3.0.

    Contact information for the exposed API.

    Attributes:
        root_node: The top-level node representing the entire Contact object in the original source file
        name: The identifying name of the contact person/organization.
        url: The URL pointing to the contact information. Value MUST be in the format of a URL.
        email: The email address of the contact person/organization. Value MUST be in the format of an email address.
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    name: FieldSource[str] | None = fixed_field()
    url: FieldSource[str] | None = fixed_field()
    email: FieldSource[str] | None = fixed_field()
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> Contact | ValueSource[YAMLInvalidValue]:
    """
    Build a Contact object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A Contact object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose("name: API Support\\nemail: support@example.com")
        contact = build(root)
        assert contact.name.value == 'API Support'
    """
    return build_model(root, Contact, context=context)
