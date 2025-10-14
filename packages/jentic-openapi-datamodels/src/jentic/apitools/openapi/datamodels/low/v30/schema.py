"""
OpenAPI 3.0.4 Schema Object model.

The Schema Object allows the definition of input and output data types.
These types can be objects, but also primitives and arrays.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from jentic.apitools.openapi.datamodels.low.v30.discriminator import Discriminator
from jentic.apitools.openapi.datamodels.low.v30.external_documentation import (
    ExternalDocumentation,
)
from jentic.apitools.openapi.datamodels.low.v30.reference import Reference
from jentic.apitools.openapi.datamodels.low.v30.specification_object import SpecificationObject
from jentic.apitools.openapi.datamodels.low.v30.xml import XML


__all__ = ["Schema"]


class Schema(SpecificationObject):
    """
    Represents a Schema Object from OpenAPI 3.0.4.

    The Schema Object allows the definition of input and output data types.
    Based on a subset of JSON Schema Draft 4/5 with OpenAPI-specific extensions.

    Supports specification extensions (x-* fields).

    Example:
        >>> # String schema with constraints
        >>> schema = Schema({
        ...     "type": "string",
        ...     "minLength": 1,
        ...     "maxLength": 100
        ... })
        >>> schema.type
        'string'

        >>> # Object schema with properties
        >>> schema = Schema({
        ...     "type": "object",
        ...     "required": ["name"],
        ...     "properties": {
        ...         "name": {"type": "string"},
        ...         "age": {"type": "integer"}
        ...     }
        ... })
        >>> schema.required
        ['name']

        >>> # Schema with discriminator
        >>> schema = Schema({
        ...     "discriminator": {
        ...         "propertyName": "petType"
        ...     }
        ... })
        >>> schema.discriminator.property_name
        'petType'
    """

    _supports_extensions: bool = True
    _fixed_fields: frozenset[str] = frozenset(
        {
            # JSON Schema Core
            "title",
            "multipleOf",
            "maximum",
            "exclusiveMaximum",
            "minimum",
            "exclusiveMinimum",
            "maxLength",
            "minLength",
            "pattern",
            "maxItems",
            "minItems",
            "uniqueItems",
            "maxProperties",
            "minProperties",
            "required",
            "enum",
            # JSON Schema Type
            "type",
            "allOf",
            "oneOf",
            "anyOf",
            "not",
            "items",
            "properties",
            "additionalProperties",
            # JSON Schema Metadata
            "description",
            "format",
            "default",
            # OpenAPI Extensions
            "nullable",
            "discriminator",
            "readOnly",
            "writeOnly",
            "xml",
            "externalDocs",
            "example",
            "deprecated",
        }
    )

    def __init__(self, data: Mapping[str, Any] | None = None):
        """
        Initialize a Schema object.

        Automatically marshals nested objects (discriminator, xml, externalDocs, and nested schemas).

        Args:
            data: Optional mapping to initialize the object with
        """
        super().__init__()
        if data:
            for key, value in data.items():
                # Marshal specific nested objects
                if (
                    key == "discriminator"
                    and isinstance(value, Mapping)
                    and not isinstance(value, Discriminator)
                ):
                    self[key] = Discriminator(value)
                elif key == "xml" and isinstance(value, Mapping) and not isinstance(value, XML):
                    self[key] = XML(value)
                elif (
                    key == "externalDocs"
                    and isinstance(value, Mapping)
                    and not isinstance(value, ExternalDocumentation)
                ):
                    self[key] = ExternalDocumentation(value)
                # Unmarshal schema composition lists (allOf, oneOf, anyOf)
                elif (
                    key in ("allOf", "oneOf", "anyOf")
                    and isinstance(value, Sequence)
                    and not isinstance(value, str)
                ):
                    self[key] = [self._unmarshal_schema_or_reference(item) for item in value]
                # Unmarshal single schema fields (not, items)
                elif key in ("not", "items") and isinstance(value, Mapping):
                    self[key] = self._unmarshal_schema_or_reference(value)
                # Unmarshal properties dict
                elif key == "properties" and isinstance(value, Mapping):
                    self[key] = {
                        k: self._unmarshal_schema_or_reference(v) for k, v in value.items()
                    }
                # Unmarshal additionalProperties (can be bool or schema)
                elif key == "additionalProperties":
                    if isinstance(value, bool):
                        self[key] = value
                    elif isinstance(value, Mapping):
                        self[key] = self._unmarshal_schema_or_reference(value)
                    else:
                        self[key] = self._copy_value(value)
                else:
                    # Store as-is (with defensive copy)
                    self[key] = self._copy_value(value)

    # JSON Schema Core - Metadata
    @property
    def title(self) -> str | None:
        """A title for the schema."""
        return self.get("title")

    @title.setter
    def title(self, value: str | None) -> None:
        if value is None:
            self.pop("title", None)
        else:
            self["title"] = value

    # JSON Schema Core - Numeric validation
    @property
    def multiple_of(self) -> float | int | None:
        """Value must be multiple of this number."""
        return self.get("multipleOf")

    @multiple_of.setter
    def multiple_of(self, value: float | int | None) -> None:
        if value is None:
            self.pop("multipleOf", None)
        else:
            self["multipleOf"] = value

    @property
    def maximum(self) -> float | int | None:
        """Maximum value (inclusive)."""
        return self.get("maximum")

    @maximum.setter
    def maximum(self, value: float | int | None) -> None:
        if value is None:
            self.pop("maximum", None)
        else:
            self["maximum"] = value

    @property
    def exclusive_maximum(self) -> float | int | None:
        """Maximum value (exclusive)."""
        return self.get("exclusiveMaximum")

    @exclusive_maximum.setter
    def exclusive_maximum(self, value: float | int | None) -> None:
        if value is None:
            self.pop("exclusiveMaximum", None)
        else:
            self["exclusiveMaximum"] = value

    @property
    def minimum(self) -> float | int | None:
        """Minimum value (inclusive)."""
        return self.get("minimum")

    @minimum.setter
    def minimum(self, value: float | int | None) -> None:
        if value is None:
            self.pop("minimum", None)
        else:
            self["minimum"] = value

    @property
    def exclusive_minimum(self) -> float | int | None:
        """Minimum value (exclusive)."""
        return self.get("exclusiveMinimum")

    @exclusive_minimum.setter
    def exclusive_minimum(self, value: float | int | None) -> None:
        if value is None:
            self.pop("exclusiveMinimum", None)
        else:
            self["exclusiveMinimum"] = value

    # String validation properties
    @property
    def max_length(self) -> int | None:
        """Maximum string length."""
        return self.get("maxLength")

    @max_length.setter
    def max_length(self, value: int | None) -> None:
        if value is None:
            self.pop("maxLength", None)
        else:
            self["maxLength"] = value

    @property
    def min_length(self) -> int | None:
        """Minimum string length."""
        return self.get("minLength")

    @min_length.setter
    def min_length(self, value: int | None) -> None:
        if value is None:
            self.pop("minLength", None)
        else:
            self["minLength"] = value

    @property
    def pattern(self) -> str | None:
        """Regular expression pattern for string validation."""
        return self.get("pattern")

    @pattern.setter
    def pattern(self, value: str | None) -> None:
        if value is None:
            self.pop("pattern", None)
        else:
            self["pattern"] = value

    # Array validation properties
    @property
    def max_items(self) -> int | None:
        """Maximum number of array items."""
        return self.get("maxItems")

    @max_items.setter
    def max_items(self, value: int | None) -> None:
        if value is None:
            self.pop("maxItems", None)
        else:
            self["maxItems"] = value

    @property
    def min_items(self) -> int | None:
        """Minimum number of array items."""
        return self.get("minItems")

    @min_items.setter
    def min_items(self, value: int | None) -> None:
        if value is None:
            self.pop("minItems", None)
        else:
            self["minItems"] = value

    @property
    def unique_items(self) -> bool | None:
        """Whether array items must be unique."""
        return self.get("uniqueItems")

    @unique_items.setter
    def unique_items(self, value: bool | None) -> None:
        if value is None:
            self.pop("uniqueItems", None)
        else:
            self["uniqueItems"] = value

    # JSON Schema Core - Object validation
    @property
    def max_properties(self) -> int | None:
        """Maximum number of object properties."""
        return self.get("maxProperties")

    @max_properties.setter
    def max_properties(self, value: int | None) -> None:
        if value is None:
            self.pop("maxProperties", None)
        else:
            self["maxProperties"] = value

    @property
    def min_properties(self) -> int | None:
        """Minimum number of object properties."""
        return self.get("minProperties")

    @min_properties.setter
    def min_properties(self, value: int | None) -> None:
        if value is None:
            self.pop("minProperties", None)
        else:
            self["minProperties"] = value

    @property
    def required(self) -> list[str] | None:
        """List of required property names (for object types)."""
        return self.get("required")

    @required.setter
    def required(self, value: list[str] | None) -> None:
        if value is None:
            self.pop("required", None)
        else:
            self["required"] = value

    @property
    def enum(self) -> list[Any] | None:
        """Allowed values."""
        return self.get("enum")

    @enum.setter
    def enum(self, value: list[Any] | None) -> None:
        if value is None:
            self.pop("enum", None)
        else:
            self["enum"] = value

    # JSON Schema Type
    @property
    def type(self) -> str | None:
        """Type of the schema (string, number, integer, boolean, array, object, null)."""
        return self.get("type")

    @type.setter
    def type(self, value: str | None) -> None:
        if value is None:
            self.pop("type", None)
        else:
            self["type"] = value

    @property
    def all_of(self) -> list[Schema | Reference] | None:
        """Schemas that must all be valid (list of Schema or Reference objects)."""
        return self.get("allOf")

    @all_of.setter
    def all_of(self, value: list[Schema | Reference] | None) -> None:
        if value is None:
            self.pop("allOf", None)
        else:
            self["allOf"] = value

    @property
    def one_of(self) -> list[Schema | Reference] | None:
        """Schemas where exactly one must be valid (list of Schema or Reference objects)."""
        return self.get("oneOf")

    @one_of.setter
    def one_of(self, value: list[Schema | Reference] | None) -> None:
        if value is None:
            self.pop("oneOf", None)
        else:
            self["oneOf"] = value

    @property
    def any_of(self) -> list[Schema | Reference] | None:
        """Schemas where at least one must be valid (list of Schema or Reference objects)."""
        return self.get("anyOf")

    @any_of.setter
    def any_of(self, value: list[Schema | Reference] | None) -> None:
        if value is None:
            self.pop("anyOf", None)
        else:
            self["anyOf"] = value

    @property
    def not_(self) -> Schema | Reference | None:
        """Schema that must NOT be valid."""
        return self.get("not")

    @not_.setter
    def not_(self, value: Schema | Reference | None) -> None:
        if value is None:
            self.pop("not", None)
        else:
            self["not"] = value

    @property
    def items_(self) -> Schema | Reference | None:
        """
        Schema for array items (Schema or Reference object).

        Note: Property named 'items_' (with underscore) to avoid conflict with
        MutableMapping.items() method. Dict access still uses the standard field name:
        schema["items"].
        """
        return self.get("items")

    @items_.setter
    def items_(self, value: Schema | Reference | None) -> None:
        if value is None:
            self.pop("items", None)
        else:
            self["items"] = value

    @property
    def properties(self) -> dict[str, Schema | Reference] | None:
        """Object properties (map of property name to Schema or Reference)."""
        return self.get("properties")

    @properties.setter
    def properties(self, value: Mapping[str, Schema | Reference] | None) -> None:
        if value is None:
            self.pop("properties", None)
        else:
            self["properties"] = dict(value) if isinstance(value, Mapping) else value

    @property
    def additional_properties(self) -> bool | Schema | Reference | None:
        """Schema for additional properties (bool or Schema or Reference object)."""
        return self.get("additionalProperties")

    @additional_properties.setter
    def additional_properties(self, value: bool | Schema | Reference | None) -> None:
        if value is None:
            self.pop("additionalProperties", None)
        else:
            self["additionalProperties"] = value

    # JSON Schema Metadata
    @property
    def description(self) -> str | None:
        """A description of the schema."""
        return self.get("description")

    @description.setter
    def description(self, value: str | None) -> None:
        if value is None:
            self.pop("description", None)
        else:
            self["description"] = value

    @property
    def format(self) -> str | None:
        """Format hint for the type (e.g., date-time, email, uuid)."""
        return self.get("format")

    @format.setter
    def format(self, value: str | None) -> None:
        if value is None:
            self.pop("format", None)
        else:
            self["format"] = value

    @property
    def default(self) -> Any:
        """Default value."""
        return self.get("default")

    @default.setter
    def default(self, value: Any) -> None:
        if value is None:
            self.pop("default", None)
        else:
            self["default"] = value

    # OpenAPI Extensions
    @property
    def nullable(self) -> bool | None:
        """Whether the value can be null (OpenAPI extension)."""
        return self.get("nullable")

    @nullable.setter
    def nullable(self, value: bool | None) -> None:
        if value is None:
            self.pop("nullable", None)
        else:
            self["nullable"] = value

    @property
    def discriminator(self) -> Discriminator | None:
        """Discriminator for polymorphism (OpenAPI extension)."""
        return self.get("discriminator")

    @discriminator.setter
    def discriminator(self, value: Discriminator | None) -> None:
        if value is None:
            self.pop("discriminator", None)
        else:
            self["discriminator"] = value

    @property
    def read_only(self) -> bool | None:
        """Whether the property is read-only (OpenAPI extension)."""
        return self.get("readOnly")

    @read_only.setter
    def read_only(self, value: bool | None) -> None:
        if value is None:
            self.pop("readOnly", None)
        else:
            self["readOnly"] = value

    @property
    def write_only(self) -> bool | None:
        """Whether the property is write-only (OpenAPI extension)."""
        return self.get("writeOnly")

    @write_only.setter
    def write_only(self, value: bool | None) -> None:
        if value is None:
            self.pop("writeOnly", None)
        else:
            self["writeOnly"] = value

    @property
    def xml(self) -> XML | None:
        """XML representation metadata (OpenAPI extension)."""
        return self.get("xml")

    @xml.setter
    def xml(self, value: XML | None) -> None:
        if value is None:
            self.pop("xml", None)
        else:
            self["xml"] = value

    @property
    def external_docs(self) -> ExternalDocumentation | None:
        """External documentation (OpenAPI extension)."""
        return self.get("externalDocs")

    @external_docs.setter
    def external_docs(self, value: ExternalDocumentation | None) -> None:
        if value is None:
            self.pop("externalDocs", None)
        else:
            self["externalDocs"] = value

    @property
    def example(self) -> Any:
        """Example value (OpenAPI extension)."""
        return self.get("example")

    @example.setter
    def example(self, value: Any) -> None:
        if value is None:
            self.pop("example", None)
        else:
            self["example"] = value

    @property
    def deprecated(self) -> bool | None:
        """Whether the schema is deprecated (OpenAPI extension)."""
        return self.get("deprecated")

    @deprecated.setter
    def deprecated(self, value: bool | None) -> None:
        if value is None:
            self.pop("deprecated", None)
        else:
            self["deprecated"] = value

    # Helper methods
    @classmethod
    def _unmarshal_schema_or_reference(cls, value: Any) -> Schema | Reference | Any:
        """
        Unmarshal a value into Schema or Reference if it's a Mapping.

        Converts raw data (dict/Mapping) into Schema or Reference objects during construction.
        Uses the actual class (or subclass) for creating Schema instances.

        Args:
            value: Value to unmarshal

        Returns:
            Schema or Reference instance, or value as-is
        """
        if not isinstance(value, Mapping):
            return value

        # Already unmarshaled
        if isinstance(value, (Schema, Reference)):
            return value

        # Check if it's a reference (has $ref field)
        if "$ref" in value:
            return Reference(value)
        else:
            # Otherwise treat as Schema (or subclass)
            return cls(value)
