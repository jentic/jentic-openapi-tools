from dataclasses import dataclass
from typing import Generic, TypeAlias, TypeVar

from ruamel import yaml
from ruamel.yaml.comments import CommentedMap, CommentedSeq


__all__ = ["FieldSource", "KeySource", "ValueSource", "YAMLValue", "YAMLInvalidValue"]

# Type alias for any deserialized YAML value (including mappings)
YAMLValue: TypeAlias = str | int | float | bool | None | CommentedSeq | CommentedMap

# Type alias for invalid YAML values (subset of YAMLValue, excludes CommentedMap)
# Used when builders receive non-mapping nodes to preserve data for validation
YAMLInvalidValue: TypeAlias = str | int | float | bool | None | CommentedSeq

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class FieldSource(Generic[T]):
    """
    A field value with associated YAML source location information.

    Used for fixed OpenAPI specification fields to track both the key and value
    nodes in the original YAML source, enabling precise error reporting.

    Automatically unwraps ValueSource instances passed as the value parameter,
    allowing child builders to return ValueSource for invalid data while keeping
    parent code clean.

    Attributes:
        value: The actual field value of type T
        key_node: The YAML node containing the field name/key
        value_node: The YAML node containing the field value (can be None for keys without values)
    """

    value: T
    key_node: yaml.Node
    value_node: yaml.Node | None = None

    def __post_init__(self) -> None:
        """
        Auto-unwrap ValueSource if passed as value parameter.

        This allows child builders to return ValueSource[YAMLInvalidValue] for invalid root nodes
        while parent code can transparently wrap the result in FieldSource without
        special handling.

        Note: We don't need to update value_node since parent and child work with
        the same YAML node.
        """
        if isinstance(self.value, ValueSource):
            # Extract the raw value from ValueSource wrapper
            object.__setattr__(self, "value", self.value.value)


@dataclass(frozen=True, slots=True)
class KeySource(Generic[T]):
    """
    A dictionary key with associated YAML source location information.

    Used in extension and unknown field dictionaries to track where keys
    appear in the original YAML source.

    Attributes:
        value: The key value of type T
        key_node: The YAML node that holds this key
    """

    value: T
    key_node: yaml.Node


@dataclass(frozen=True, slots=True)
class ValueSource(Generic[T]):
    """
    A dictionary value / array item with associated YAML source location information.

    Used in extension and unknown field dictionaries to track where values
    appear in the original YAML source.

    Attributes:
        value: The value of type T
        value_node: The YAML node that holds this value
    """

    value: T
    value_node: yaml.Node
