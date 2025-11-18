from dataclasses import dataclass, field

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .builders import build_model
from .example import Example
from .media_type import MediaType
from .reference import Reference
from .reference import build as build_reference
from .schema import BooleanJSONSchema, Schema


__all__ = ["Parameter", "build", "build_parameter_or_reference"]


@dataclass(frozen=True, slots=True)
class Parameter:
    """
    Parameter Object representation for OpenAPI 3.1.

    Describes a single operation parameter. A unique parameter is defined by a combination
    of a name and location (in).

    Attributes:
        root_node: The top-level node representing the entire Parameter object in the original source file
        name: The name of the parameter (case-sensitive)
        in_: The location of the parameter. Possible values are "query", "header", "path", or "cookie"
        description: A brief description of the parameter (may contain CommonMark syntax)
        required: Determines whether this parameter is mandatory. For path parameters, must be true.
                 Default is false for other parameter types.
        deprecated: Specifies that a parameter is deprecated and should be transitioned out of usage
        allow_empty_value: Sets the ability to pass empty-valued parameters (valid only for query parameters)
        style: Describes how the parameter value will be serialized (default depends on 'in' value)
        explode: When true, parameter values of type array or object generate separate parameters
        allow_reserved: Determines whether reserved characters are allowed without percent-encoding
        schema: The schema defining the type used for the parameter
        example: Example of the parameter's potential value
        examples: Examples of the parameter's potential value (map of Example objects or References)
        content: A map containing the representations for the parameter (must contain only one entry)
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    name: FieldSource[str] | None = fixed_field()
    in_: FieldSource[str] | None = fixed_field(metadata={"yaml_name": "in"})
    description: FieldSource[str] | None = fixed_field()
    required: FieldSource[bool] | None = fixed_field()
    deprecated: FieldSource[bool] | None = fixed_field()
    allow_empty_value: FieldSource[bool] | None = fixed_field(
        metadata={"yaml_name": "allowEmptyValue"}
    )
    style: FieldSource[str] | None = fixed_field()
    explode: FieldSource[bool] | None = fixed_field()
    allow_reserved: FieldSource[bool] | None = fixed_field(metadata={"yaml_name": "allowReserved"})
    schema: FieldSource["Schema | BooleanJSONSchema"] | None = fixed_field()
    example: FieldSource[YAMLValue] | None = fixed_field()
    examples: FieldSource[dict[KeySource[str], "Example | Reference"]] | None = fixed_field()
    content: FieldSource[dict[KeySource[str], "MediaType"]] | None = fixed_field()
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> Parameter | ValueSource[YAMLInvalidValue]:
    """
    Build a Parameter object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A Parameter object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose('''
        name: userId
        in: path
        required: true
        schema:
          type: integer
        ''')
        parameter = build(root)
        assert parameter.name.value == 'userId'
    """
    return build_model(root, Parameter, context=context)


def build_parameter_or_reference(
    node: yaml.Node, context: Context
) -> Parameter | Reference | ValueSource[YAMLInvalidValue]:
    """
    Build either a Parameter or Reference from a YAML node.

    This helper handles the polymorphic nature of OpenAPI where many fields
    can contain either a Parameter object or a Reference object ($ref).

    Args:
        node: The YAML node to parse
        context: Parsing context

    Returns:
        A Parameter, Reference, or ValueSource if the node is invalid
    """
    # Check if it's a reference (has $ref key)
    if isinstance(node, yaml.MappingNode):
        for key_node, _ in node.value:
            key = context.yaml_constructor.construct_yaml_str(key_node)
            if key == "$ref":
                return build_reference(node, context)

    # Otherwise, try to build as Parameter
    return build(node, context)
