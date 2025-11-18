from dataclasses import dataclass, field

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .builders import build_model
from .reference import Reference
from .reference import build as build_reference


__all__ = ["Example", "build", "build_example_or_reference"]


@dataclass(frozen=True, slots=True)
class Example:
    """
    Example Object representation for OpenAPI 3.0.

    Attributes:
        root_node: The top-level node representing the entire Example object in the original source file
        summary: A short description of the example.
        description: A long description for the example. CommonMark syntax MAY be used for rich text representation.
        value: Embedded literal example. The value field and externalValue field are mutually exclusive.
        external_value: A URL that points to the literal example. This provides the capability to reference
                       examples that cannot be inlined. The value field and externalValue field are mutually exclusive.
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    summary: FieldSource[str] | None = fixed_field()
    description: FieldSource[str] | None = fixed_field()
    value: FieldSource[YAMLValue] | None = fixed_field()
    external_value: FieldSource[str] | None = fixed_field(metadata={"yaml_name": "externalValue"})
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> Example | ValueSource[YAMLInvalidValue]:
    """
    Build an Example object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        An Example object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose("summary: A user example\\nvalue:\\n  id: 1\\n  name: John")
        example = build(root)
        assert example.summary.value == 'A user example'
    """
    return build_model(root, Example, context=context)


def build_example_or_reference(
    node: yaml.Node, context: Context
) -> Example | Reference | ValueSource[YAMLInvalidValue]:
    """
    Build either an Example or Reference from a YAML node.

    This helper handles the polymorphic nature of OpenAPI where many fields
    can contain either an Example object or a Reference object ($ref).

    Args:
        node: The YAML node to parse
        context: Parsing context

    Returns:
        An Example, Reference, or ValueSource if the node is invalid
    """
    # Check if it's a reference (has $ref key)
    if isinstance(node, yaml.MappingNode):
        for key_node, _ in node.value:
            key = context.yaml_constructor.construct_yaml_str(key_node)
            if key == "$ref":
                return build_reference(node, context)

    # Otherwise, try to build as Example
    return build(node, context)
