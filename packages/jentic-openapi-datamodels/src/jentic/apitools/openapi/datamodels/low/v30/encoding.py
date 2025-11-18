from dataclasses import dataclass, field

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .builders import build_model
from .header import Header
from .reference import Reference


__all__ = ["Encoding", "build"]


@dataclass(frozen=True, slots=True)
class Encoding:
    """
    Encoding Object representation for OpenAPI 3.0.

    A single encoding definition applied to a single schema property.

    Attributes:
        root_node: The top-level node representing the entire Encoding object in the original source file
        contentType: The Content-Type for encoding a specific property. Default value depends on the property type:
                     for string with format being binary – application/octet-stream;
                     for other primitive types – text/plain;
                     for object - application/json;
                     for array – the default is defined based on the inner type.
        headers: A map allowing additional information to be provided as headers. Content-Type is described
                separately and SHALL be ignored if included.
        style: Describes how a specific property value will be serialized depending on its type.
        explode: When this is true, property values of type array or object generate separate parameters
                for each value of the array, or key-value-pair of the map. For other data types this property
                has no effect. Default value is true.
        allowReserved: Determines whether the parameter value SHOULD allow reserved characters, as defined by
                      RFC3986 :/?#[]@!$&'()*+,;= to be included without percent-encoding. The default value is false.
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    contentType: FieldSource[str] | None = fixed_field()
    headers: FieldSource[dict[KeySource[str], "Header | Reference"]] | None = fixed_field()
    style: FieldSource[str] | None = fixed_field()
    explode: FieldSource[bool] | None = fixed_field()
    allowReserved: FieldSource[bool] | None = fixed_field()
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> Encoding | ValueSource[YAMLInvalidValue]:
    """
    Build an Encoding object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        An Encoding object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose('''
        contentType: application/xml
        headers:
          X-Rate-Limit:
            schema:
              type: integer
        ''')
        encoding = build(root)
        assert encoding.contentType.value == 'application/xml'
    """
    return build_model(root, Encoding, context=context)
