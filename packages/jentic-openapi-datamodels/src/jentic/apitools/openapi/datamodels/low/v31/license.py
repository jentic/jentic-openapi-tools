from dataclasses import dataclass, field

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .builders import build_model


__all__ = ["License", "build"]


@dataclass(frozen=True, slots=True)
class License:
    """
    License Object representation for OpenAPI 3.1.

    License information for the exposed API.

    Attributes:
        root_node: The top-level node representing the entire License object in the original source file
        name: REQUIRED. The license name used for the API.
        identifier: An SPDX license expression for the API. Mutually exclusive with the url field (new in OpenAPI 3.1).
        url: A URL to the license used for the API. Value MUST be in the format of a URL. Mutually exclusive with the identifier field.
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    name: FieldSource[str] | None = fixed_field()
    identifier: FieldSource[str] | None = fixed_field()
    url: FieldSource[str] | None = fixed_field()
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> License | ValueSource[YAMLInvalidValue]:
    """
    Build a License object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A License object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose("name: MIT\\nurl: https://opensource.org/licenses/MIT")
        license = build(root)
        assert license.name.value == 'MIT'
    """
    return build_model(root, License, context=context)
