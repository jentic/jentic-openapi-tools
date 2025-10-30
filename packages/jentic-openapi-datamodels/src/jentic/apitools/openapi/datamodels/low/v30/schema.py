from dataclasses import dataclass, field
from typing import Any, TypeAlias, get_args

from ruamel import yaml

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.extractors import extract_extension_fields
from jentic.apitools.openapi.datamodels.low.fields import fixed_field, fixed_fields
from jentic.apitools.openapi.datamodels.low.sources import (
    FieldSource,
    KeySource,
    ValueSource,
    YAMLInvalidValue,
    YAMLValue,
)
from jentic.apitools.openapi.datamodels.low.v30.discriminator import Discriminator
from jentic.apitools.openapi.datamodels.low.v30.discriminator import build as build_discriminator
from jentic.apitools.openapi.datamodels.low.v30.external_documentation import (
    ExternalDocumentation,
)
from jentic.apitools.openapi.datamodels.low.v30.external_documentation import (
    build as build_external_documentation,
)
from jentic.apitools.openapi.datamodels.low.v30.reference import Reference
from jentic.apitools.openapi.datamodels.low.v30.reference import build as build_reference
from jentic.apitools.openapi.datamodels.low.v30.xml import XML
from jentic.apitools.openapi.datamodels.low.v30.xml import build as build_xml


__all__ = ["Schema", "NestedSchema", "build"]


# Type alias for nested schema references
# A schema node that can be nested within another schema, representing:
# - Schema: A valid schema object
# - Reference: A $ref reference to another schema
# - ValueSource[YAMLInvalidValue]: Invalid/malformed data preserved for validation
NestedSchema: TypeAlias = "Schema | Reference | ValueSource[YAMLInvalidValue]"


@dataclass(frozen=True, slots=True)
class Schema:
    """
    Schema Object representation for OpenAPI 3.0.

    The Schema Object allows the definition of input and output data types. These types can be
    objects, but also primitives and arrays. This object is an extended subset of the JSON Schema
    Specification Wright Draft 00.

    Attributes:
        root_node: The top-level node representing the entire Schema object in the original source file

        # JSON Schema Core validation keywords
        title: A title for the schema
        multipleOf: A numeric instance is valid only if division by this value results in an integer
        maximum: Upper limit for a numeric instance
        exclusiveMaximum: If true, the value must be strictly less than maximum
        minimum: Lower limit for a numeric instance
        exclusiveMinimum: If true, the value must be strictly greater than minimum
        maxLength: Maximum length of a string instance
        minLength: Minimum length of a string instance
        pattern: A string instance is valid if the regular expression matches the instance successfully
        maxItems: Maximum number of items in an array instance
        minItems: Minimum number of items in an array instance
        uniqueItems: If true, array items must be unique
        maxProperties: Maximum number of properties in an object instance
        minProperties: Minimum number of properties in an object instance
        required: List of required property names
        enum: Fixed set of allowed values

        # JSON Schema Type and Structure
        type: Value type (string, number, integer, boolean, array, object)
        allOf: Must be valid against all of the subschemas
        oneOf: Must be valid against exactly one of the subschemas
        anyOf: Must be valid against any of the subschemas
        not_: Must not be valid against the given schema
        items: Schema for array items (or array of schemas for tuple validation)
        properties: Property name to schema mappings
        additionalProperties: Schema for properties not defined in properties, or boolean to allow/disallow

        # JSON Schema Metadata
        description: A short description. CommonMark syntax MAY be used for rich text representation.
        format: Additional format hint for the type (e.g., "email", "uuid", "uri", "date-time")
        default: Default value

        # OpenAPI-specific extensions
        nullable: Allows sending a null value
        discriminator: Adds support for polymorphism
        readOnly: Relevant only for Schema "properties" definitions - sent in response but not in request
        writeOnly: Relevant only for Schema "properties" definitions - sent in request but not in response
        xml: Additional metadata for XML representations
        externalDocs: Additional external documentation
        example: Example of the media type
        deprecated: Specifies that the schema is deprecated

        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node

    # JSON Schema Core validation keywords
    title: FieldSource[str] | None = fixed_field()
    multipleOf: FieldSource[int | float] | None = fixed_field()
    maximum: FieldSource[int | float] | None = fixed_field()
    exclusiveMaximum: FieldSource[bool] | None = fixed_field()
    minimum: FieldSource[int | float] | None = fixed_field()
    exclusiveMinimum: FieldSource[bool] | None = fixed_field()
    maxLength: FieldSource[int] | None = fixed_field()
    minLength: FieldSource[int] | None = fixed_field()
    pattern: FieldSource[str] | None = fixed_field()
    maxItems: FieldSource[int] | None = fixed_field()
    minItems: FieldSource[int] | None = fixed_field()
    uniqueItems: FieldSource[bool] | None = fixed_field()
    maxProperties: FieldSource[int] | None = fixed_field()
    minProperties: FieldSource[int] | None = fixed_field()
    required: FieldSource[list[str]] | None = fixed_field()
    enum: FieldSource[list[YAMLValue]] | None = fixed_field()

    # JSON Schema Type and Structure (nested schemas)
    type: FieldSource[str] | None = fixed_field()
    allOf: FieldSource[list[NestedSchema]] | None = fixed_field()
    oneOf: FieldSource[list[NestedSchema]] | None = fixed_field()
    anyOf: FieldSource[list[NestedSchema]] | None = fixed_field()
    not_: FieldSource[NestedSchema] | None = fixed_field(metadata={"yaml_name": "not"})
    items: FieldSource[NestedSchema] | None = fixed_field()
    properties: FieldSource[dict[KeySource[str], ValueSource[NestedSchema]]] | None = fixed_field()
    additionalProperties: FieldSource["bool | NestedSchema"] | None = fixed_field()

    # JSON Schema Metadata
    description: FieldSource[str] | None = fixed_field()
    format: FieldSource[str] | None = fixed_field()
    default: FieldSource[YAMLValue] | None = fixed_field()

    # OpenAPI-specific extensions
    nullable: FieldSource[bool] | None = fixed_field()
    discriminator: FieldSource[Discriminator] | None = fixed_field()
    readOnly: FieldSource[bool] | None = fixed_field()
    writeOnly: FieldSource[bool] | None = fixed_field()
    xml: FieldSource[XML] | None = fixed_field()
    externalDocs: FieldSource[ExternalDocumentation] | None = fixed_field()
    example: FieldSource[YAMLValue] | None = fixed_field()
    deprecated: FieldSource[bool] | None = fixed_field()

    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> "Schema | ValueSource[YAMLInvalidValue]":
    """
    Build a Schema object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Note: Schema is self-referential (can contain other Schema objects in allOf, oneOf, anyOf, not,
    items, properties, additionalProperties). The builder handles nested Schema objects by preserving
    them as raw YAML values, letting validation layers interpret them.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A Schema object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose("type: string\\nminLength: 1\\nmaxLength: 100")
        schema = build(root)
        assert schema.type.value == 'string'
        assert schema.minLength.value == 1
    """
    # Initialize context once at the beginning
    if context is None:
        context = Context()

    if not isinstance(root, yaml.MappingNode):
        # Preserve invalid root data instead of returning None
        value = context.yaml_constructor.construct_object(root, deep=True)
        return ValueSource(value=value, value_node=root)

    # Build YAML name to Python field name mapping
    _fixed_fields = fixed_fields(Schema)
    yaml_to_field = {
        f.metadata.get("yaml_name", fname): fname for fname, f in _fixed_fields.items()
    }

    # Accumulate all field values in a single pass
    field_values: dict[str, Any] = {}

    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        # Skip extension fields - handled separately at the end
        if key.startswith("x-"):
            continue

        # Map YAML key to Python field name
        field_name = yaml_to_field.get(key)
        if not field_name:
            continue

        # Get field metadata
        field_info = _fixed_fields[field_name]
        field_type_args = set(get_args(field_info.type))

        # Simple scalar fields (handled like build_model does)
        if field_type_args & {
            FieldSource[str],
            FieldSource[bool],
            FieldSource[int],
            FieldSource[int | float],
            FieldSource[YAMLValue],
            FieldSource[list[str]],
            FieldSource[list[YAMLValue]],
        }:
            value = context.yaml_constructor.construct_object(value_node, deep=True)
            field_values[field_name] = FieldSource(
                value=value, key_node=key_node, value_node=value_node
            )

        # Recursive schema list fields (allOf, oneOf, anyOf)
        elif key in ("allOf", "oneOf", "anyOf"):
            if isinstance(value_node, yaml.SequenceNode):
                schemas = []
                for item_node in value_node.value:
                    schema_or_ref = _build_schema_or_reference(item_node, context)
                    schemas.append(schema_or_ref)
                field_values[field_name] = FieldSource(
                    value=schemas, key_node=key_node, value_node=value_node
                )
            else:
                # Not a sequence - preserve as-is for validation
                value = context.yaml_constructor.construct_object(value_node, deep=True)
                field_values[field_name] = FieldSource(
                    value=value, key_node=key_node, value_node=value_node
                )
        # Recursive schema single fields (not, items)
        elif key in ("not", "items"):
            schema_or_ref = _build_schema_or_reference(value_node, context)
            field_values[field_name] = FieldSource(
                value=schema_or_ref, key_node=key_node, value_node=value_node
            )
        # additionalProperties (boolean | schema | reference)
        elif key == "additionalProperties":
            # Check if it's a boolean or a schema/reference
            if (
                isinstance(value_node, yaml.ScalarNode)
                and value_node.tag == "tag:yaml.org,2002:bool"
            ):
                value = context.yaml_constructor.construct_object(value_node)
                field_values[field_name] = FieldSource(
                    value=value, key_node=key_node, value_node=value_node
                )
            else:
                # It's a schema or reference
                schema_or_ref = _build_schema_or_reference(value_node, context)
                field_values[field_name] = FieldSource(
                    value=schema_or_ref, key_node=key_node, value_node=value_node
                )
        # properties (dict[KeySource[str], ValueSource[NestedSchema]])
        elif key == "properties":
            if isinstance(value_node, yaml.MappingNode):
                properties_dict: dict[KeySource[str], ValueSource[NestedSchema]] = {}
                for prop_key_node, prop_value_node in value_node.value:
                    prop_key = context.yaml_constructor.construct_yaml_str(prop_key_node)
                    # Recursively build each property schema
                    prop_schema_or_ref = _build_schema_or_reference(prop_value_node, context)
                    properties_dict[KeySource(value=prop_key, key_node=prop_key_node)] = (
                        ValueSource(value=prop_schema_or_ref, value_node=prop_value_node)
                    )
                field_values[field_name] = FieldSource(
                    value=properties_dict, key_node=key_node, value_node=value_node
                )
            else:
                # Not a mapping - preserve as-is for validation
                value = context.yaml_constructor.construct_object(value_node, deep=True)
                field_values[field_name] = FieldSource(
                    value=value, key_node=key_node, value_node=value_node
                )
        # Nested objects (discriminator, xml, externalDocs)
        elif key == "discriminator":
            field_values[field_name] = FieldSource(
                value=build_discriminator(value_node, context=context),
                key_node=key_node,
                value_node=value_node,
            )
        elif key == "xml":
            field_values[field_name] = FieldSource(
                value=build_xml(value_node, context=context),
                key_node=key_node,
                value_node=value_node,
            )
        elif key == "externalDocs":
            field_values[field_name] = FieldSource(
                value=build_external_documentation(value_node, context=context),
                key_node=key_node,
                value_node=value_node,
            )

    # Build and return the Schema instance (single constructor call)
    return Schema(
        root_node=root,
        **field_values,
        extensions=extract_extension_fields(root, context),
    )


def _build_schema_or_reference(node: yaml.Node, context: Context) -> NestedSchema:
    """
    Build either a Schema or Reference from a YAML node.

    This helper handles the polymorphic nature of OpenAPI where many fields
    can contain either a Schema object or a Reference object ($ref).

    Args:
        node: The YAML node to parse
        context: Parsing context

    Returns:
        A Schema, Reference, or ValueSource if the node is invalid
    """
    # Check if it's a reference (has $ref key)
    if isinstance(node, yaml.MappingNode):
        for key_node, _ in node.value:
            key = context.yaml_constructor.construct_yaml_str(key_node)
            if key == "$ref":
                return build_reference(node, context)

    # Otherwise, try to build as Schema (which may be recursive)
    return build(node, context)
