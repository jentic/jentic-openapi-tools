from dataclasses import dataclass, field
from typing import Any, TypeAlias, get_args

from ruamel import yaml
from ruamel.yaml.comments import CommentedSeq

from ..context import Context
from ..extractors import extract_extension_fields
from ..fields import fixed_field, fixed_fields
from ..sources import FieldSource, KeySource, ValueSource, YAMLValue
from .builders import build_field_source
from .discriminator import Discriminator
from .discriminator import build as build_discriminator
from .external_documentation import ExternalDocumentation
from .external_documentation import build as build_external_documentation
from .xml import XML
from .xml import build as build_xml


__all__ = ["Schema", "BooleanJSONSchema", "NestedSchema", "build"]


BooleanJSONSchema: TypeAlias = ValueSource[bool]


# Type alias for nested schema references
# A schema node that can be nested within another schema, representing:
# - Schema: A valid schema object
# - Boolean JSON Schema: True or False
# - ValueSource[str | int | float | None | CommentedSeq]: Invalid/malformed data preserved for validation

NestedSchema: TypeAlias = (
    "Schema | BooleanJSONSchema | ValueSource[str | int | float | None | CommentedSeq]"
)


@dataclass(frozen=True, slots=True)
class Schema:
    """
    Schema Object representation for OpenAPI 3.1.

    In OpenAPI 3.1, the Schema Object is a full JSON Schema 2020-12 vocabulary with OpenAPI extensions.
    This represents a complete JSON Schema with additional OpenAPI-specific fields.

    Attributes:
        root_node: The top-level node representing the entire Schema object in the original source file

        # JSON Schema Core Keywords (2020-12)
        schema_: The $schema keyword - URI of the meta-schema
        id_: The $id keyword - URI that identifies the schema resource
        ref_: The $ref keyword - URI reference to another schema
        anchor: The $anchor keyword - Plain name fragment for identification
        dynamic_ref: The $dynamicRef keyword - Dynamic reference to another schema
        dynamic_anchor: The $dynamicAnchor keyword - Dynamic anchor for identification
        vocabulary: The $vocabulary keyword - Available vocabularies and their usage
        comment: The $comment keyword - Comments for schema authors
        defs: The $defs keyword - Schema definitions for reuse

        # JSON Schema Validation Keywords (2020-12)
        # Validation - Any Type
        type: The type keyword - Value type(s): string, number, integer, boolean, array, object, null
        enum: The enum keyword - Fixed set of allowed values
        const: The const keyword - Single allowed value

        # Validation - Numeric
        multiple_of: A numeric instance is valid only if division by this value results in an integer
        maximum: Upper limit for a numeric instance (inclusive)
        exclusive_maximum: Upper limit for a numeric instance (exclusive)
        minimum: Lower limit for a numeric instance (inclusive)
        exclusive_minimum: Lower limit for a numeric instance (exclusive)

        # Validation - String
        max_length: Maximum length of a string instance
        min_length: Minimum length of a string instance
        pattern: A string instance is valid if the regular expression matches the instance successfully

        # Validation - Array
        max_items: Maximum number of items in an array instance
        min_items: Minimum number of items in an array instance
        unique_items: If true, array items must be unique
        max_contains: Maximum number of items that must match the contains schema
        min_contains: Minimum number of items that must match the contains schema

        # Validation - Object
        max_properties: Maximum number of properties in an object instance
        min_properties: Minimum number of properties in an object instance
        required: List of required property names
        dependent_required: Dependencies between properties (property-based requirements)

        # JSON Schema Applicator Keywords (2020-12)
        # Schema Composition
        all_of: Must be valid against all of the subschemas
        any_of: Must be valid against any of the subschemas
        one_of: Must be valid against exactly one of the subschemas
        not_: Must not be valid against the given schema

        # Conditional Application
        if_: Conditional schema - if this validates, then/else is applied
        then_: Schema to apply if 'if' validates
        else_: Schema to apply if 'if' does not validate

        # Array Applicators
        prefix_items: Array of schemas for validating tuple-like arrays (positional items)
        items: Schema for array items (all items or items after prefix_items)
        contains: Schema that at least one array item must validate against

        # Object Applicators
        properties: Property name to schema mappings
        pattern_properties: Property patterns to schema mappings
        additional_properties: Schema for properties not defined in properties/pattern_properties, or boolean
        property_names: Schema that all property names must validate against

        # Dependent Schemas
        dependent_schemas: Schemas that must validate when specific properties are present

        # Unevaluated Locations
        unevaluated_items: Schema for array items not evaluated by other keywords
        unevaluated_properties: Schema for object properties not evaluated by other keywords

        # JSON Schema Meta-Data Keywords (2020-12)
        title: A title for the schema
        description: A description of the schema. CommonMark syntax MAY be used for rich text representation.
        default: Default value for the schema
        deprecated: Specifies that the schema is deprecated
        read_only: Indicates the value should not be modified (sent in response but not in request)
        write_only: Indicates the value should only be sent in requests (not in responses)
        examples: Array of example values

        # JSON Schema Format Keywords (2020-12)
        format: Additional format hint for the type (e.g., "email", "uuid", "uri", "date-time")

        # JSON Schema Content Keywords (2020-12)
        content_encoding: Content encoding for string instances (e.g., "base64")
        content_media_type: Media type of string instance contents (e.g., "application/json")
        content_schema: Schema for validating the decoded content

        # OpenAPI-specific extensions (not in JSON Schema 2020-12)
        discriminator: Adds support for polymorphism
        xml: Additional metadata for XML representations
        external_docs: Additional external documentation
        example: A single example value (OpenAPI extension, use examples for standard JSON Schema)

        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node

    # Core Keywords
    id_: FieldSource[str] | None = fixed_field(metadata={"yaml_name": "$id"})
    schema_: FieldSource[str] | None = fixed_field(metadata={"yaml_name": "$schema"})
    ref_: FieldSource[str] | None = fixed_field(metadata={"yaml_name": "$ref"})
    comment: FieldSource[str] | None = fixed_field(metadata={"yaml_name": "$comment"})
    defs: FieldSource[dict[KeySource[str], NestedSchema]] | None = fixed_field(
        metadata={"yaml_name": "$defs"}
    )
    anchor: FieldSource[str] | None = fixed_field(metadata={"yaml_name": "$anchor"})
    dynamic_anchor: FieldSource[str] | None = fixed_field(metadata={"yaml_name": "$dynamicAnchor"})
    dynamic_ref: FieldSource[str] | None = fixed_field(metadata={"yaml_name": "$dynamicRef"})
    vocabulary: FieldSource[dict[KeySource[str], ValueSource[bool]]] | None = fixed_field(
        metadata={"yaml_name": "$vocabulary"}
    )

    # JSON Schema Applicator Keywords
    all_of: FieldSource[list[NestedSchema]] | None = fixed_field(metadata={"yaml_name": "allOf"})
    any_of: FieldSource[list[NestedSchema]] | None = fixed_field(metadata={"yaml_name": "anyOf"})
    one_of: FieldSource[list[NestedSchema]] | None = fixed_field(metadata={"yaml_name": "oneOf"})
    if_: FieldSource[NestedSchema] | None = fixed_field(metadata={"yaml_name": "if"})
    then_: FieldSource[NestedSchema] | None = fixed_field(metadata={"yaml_name": "then"})
    else_: FieldSource[NestedSchema] | None = fixed_field(metadata={"yaml_name": "else"})
    not_: FieldSource[NestedSchema] | None = fixed_field(metadata={"yaml_name": "not"})
    properties: FieldSource[dict[KeySource[str], NestedSchema]] | None = fixed_field()
    additional_properties: FieldSource[NestedSchema] | None = fixed_field(
        metadata={"yaml_name": "additionalProperties"}
    )
    pattern_properties: FieldSource[dict[KeySource[str], NestedSchema]] | None = fixed_field(
        metadata={"yaml_name": "patternProperties"}
    )
    dependent_schemas: FieldSource[dict[KeySource[str], NestedSchema]] | None = fixed_field(
        metadata={"yaml_name": "dependentSchemas"}
    )
    property_names: FieldSource[NestedSchema] | None = fixed_field(
        metadata={"yaml_name": "propertyNames"}
    )
    contains: FieldSource[NestedSchema] | None = fixed_field()
    items: FieldSource[NestedSchema] | None = fixed_field()
    prefix_items: FieldSource[list[NestedSchema]] | None = fixed_field(
        metadata={"yaml_name": "prefixItems"}
    )

    # Validation Keywords
    type: FieldSource[str | list[ValueSource[str]]] | None = fixed_field()
    enum: FieldSource[list[ValueSource[YAMLValue]]] | None = fixed_field()
    const: FieldSource[YAMLValue] | None = fixed_field()
    max_length: FieldSource[int] | None = fixed_field(metadata={"yaml_name": "maxLength"})
    min_length: FieldSource[int] | None = fixed_field(metadata={"yaml_name": "minLength"})
    pattern: FieldSource[str] | None = fixed_field()
    exclusive_maximum: FieldSource[int | float] | None = fixed_field(
        metadata={"yaml_name": "exclusiveMaximum"}
    )
    exclusive_minimum: FieldSource[int | float] | None = fixed_field(
        metadata={"yaml_name": "exclusiveMinimum"}
    )
    minimum: FieldSource[int | float] | None = fixed_field()
    maximum: FieldSource[int | float] | None = fixed_field()
    multiple_of: FieldSource[int | float] | None = fixed_field(metadata={"yaml_name": "multipleOf"})
    dependent_required: FieldSource[dict[KeySource[str], list[ValueSource[str]]]] | None = (
        fixed_field(metadata={"yaml_name": "dependentRequired"})
    )
    max_properties: FieldSource[int] | None = fixed_field(metadata={"yaml_name": "maxProperties"})
    min_properties: FieldSource[int] | None = fixed_field(metadata={"yaml_name": "minProperties"})
    required: FieldSource[list[ValueSource[str]]] | None = fixed_field()
    max_items: FieldSource[int] | None = fixed_field(metadata={"yaml_name": "maxItems"})
    min_items: FieldSource[int] | None = fixed_field(metadata={"yaml_name": "minItems"})
    max_contains: FieldSource[int] | None = fixed_field(metadata={"yaml_name": "maxContains"})
    min_contains: FieldSource[int] | None = fixed_field(metadata={"yaml_name": "minContains"})
    unique_items: FieldSource[bool] | None = fixed_field(metadata={"yaml_name": "uniqueItems"})

    # Meta Data Keywords
    title: FieldSource[str] | None = fixed_field()
    description: FieldSource[str] | None = fixed_field()
    default: FieldSource[YAMLValue] | None = fixed_field()
    deprecated: FieldSource[bool] | None = fixed_field()
    examples: FieldSource[list[ValueSource[YAMLValue]]] | None = fixed_field()
    read_only: FieldSource[bool] | None = fixed_field(metadata={"yaml_name": "readOnly"})
    write_only: FieldSource[bool] | None = fixed_field(metadata={"yaml_name": "writeOnly"})

    # Format Annotation Keywords
    format: FieldSource[str] | None = fixed_field()

    # Content Keywords
    content_encoding: FieldSource[str] | None = fixed_field(
        metadata={"yaml_name": "contentEncoding"}
    )
    content_media_type: FieldSource[str] | None = fixed_field(
        metadata={"yaml_name": "contentMediaType"}
    )
    content_schema: FieldSource[NestedSchema] | None = fixed_field(
        metadata={"yaml_name": "contentSchema"}
    )

    # Unevaluated Keywords
    unevaluated_items: FieldSource[NestedSchema] | None = fixed_field(
        metadata={"yaml_name": "unevaluatedItems"}
    )
    unevaluated_properties: FieldSource[NestedSchema] | None = fixed_field(
        metadata={"yaml_name": "unevaluatedProperties"}
    )

    # OpenAPI base vocabulary Keywords (not in JSON Schema 2020-12)
    discriminator: FieldSource[Discriminator] | None = fixed_field()
    xml: FieldSource[XML] | None = fixed_field()
    external_docs: FieldSource[ExternalDocumentation] | None = fixed_field(
        metadata={"yaml_name": "externalDocs"}
    )
    example: FieldSource[YAMLValue] | None = fixed_field()

    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> "Schema | BooleanJSONSchema | ValueSource[str | int | float | None | CommentedSeq]":
    """
    Build a Schema object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Note: Schema is self-referential (can contain other Schema objects in all_of, one_of, any_of, not_,
    items, properties, additional_properties). The builder handles nested Schema objects by preserving
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
        assert schema.min_length.value == 1
    """
    context = context or Context()

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
        }:
            field_values[field_name] = build_field_source(key_node, value_node, context)

        # Handle list with ValueSource wrapping for each item (e.g., required, enum fields)
        elif field_type_args & {
            FieldSource[list[ValueSource[str]]],
            FieldSource[list[ValueSource[YAMLValue]]],
        }:
            if isinstance(value_node, yaml.SequenceNode):
                value_list: list[ValueSource[Any]] = []
                for item_node in value_node.value:
                    item_value = context.yaml_constructor.construct_object(item_node, deep=True)
                    value_list.append(ValueSource(value=item_value, value_node=item_node))
                field_values[field_name] = FieldSource(
                    value=value_list, key_node=key_node, value_node=value_node
                )
            else:
                # Not a sequence - preserve as-is for validation
                field_values[field_name] = build_field_source(key_node, value_node, context)

        # Recursive schema list fields (allOf, oneOf, anyOf, prefixItems)
        elif key in ("allOf", "oneOf", "anyOf", "prefixItems"):
            if isinstance(value_node, yaml.SequenceNode):
                schemas = []
                for item_node in value_node.value:
                    schema = build(item_node, context)
                    schemas.append(schema)
                field_values[field_name] = FieldSource(
                    value=schemas, key_node=key_node, value_node=value_node
                )
            else:
                # Not a sequence - preserve as-is for validation
                field_values[field_name] = build_field_source(key_node, value_node, context)
        # Recursive schema single fields (not, if, then, else, contains, propertyNames, contentSchema)
        elif key in ("not", "if", "then", "else", "contains", "propertyNames", "contentSchema"):
            schema = build(value_node, context)
            field_values[field_name] = FieldSource(
                value=schema, key_node=key_node, value_node=value_node
            )
        # items (boolean | schema in JSON Schema 2020-12)
        elif key == "items":
            # Check if it's a boolean or a schema
            if (
                isinstance(value_node, yaml.ScalarNode)
                and value_node.tag == "tag:yaml.org,2002:bool"
            ):
                field_values[field_name] = build_field_source(key_node, value_node, context)
            else:
                # It's a schema
                schema = build(value_node, context)
                field_values[field_name] = FieldSource(
                    value=schema, key_node=key_node, value_node=value_node
                )
        # Boolean | schema fields (additionalProperties, unevaluatedItems, unevaluatedProperties)
        elif key in ("additionalProperties", "unevaluatedItems", "unevaluatedProperties"):
            # Check if it's a boolean or a schema
            if (
                isinstance(value_node, yaml.ScalarNode)
                and value_node.tag == "tag:yaml.org,2002:bool"
            ):
                field_values[field_name] = build_field_source(key_node, value_node, context)
            else:
                # It's a schema
                schema = build(value_node, context)
                field_values[field_name] = FieldSource(
                    value=schema, key_node=key_node, value_node=value_node
                )
        # Dict of schemas (properties, $defs, patternProperties, dependentSchemas)
        elif key in ("properties", "$defs", "patternProperties", "dependentSchemas"):
            if isinstance(value_node, yaml.MappingNode):
                schemas_dict: dict[KeySource[str], NestedSchema] = {}
                for map_key_node, map_value_node in value_node.value:
                    map_key = context.yaml_constructor.construct_yaml_str(map_key_node)
                    # Recursively build each schema
                    nested_schema: NestedSchema = build(map_value_node, context)
                    schemas_dict[KeySource(value=map_key, key_node=map_key_node)] = nested_schema
                field_values[field_name] = FieldSource(
                    value=schemas_dict, key_node=key_node, value_node=value_node
                )
            else:
                # Not a mapping - preserve as-is for validation
                field_values[field_name] = build_field_source(key_node, value_node, context)
        # $vocabulary (dict[KeySource[str], ValueSource[bool]])
        elif key == "$vocabulary":
            if isinstance(value_node, yaml.MappingNode):
                vocabulary_dict: dict[KeySource[str], ValueSource[bool]] = {}
                for vocab_key_node, vocab_value_node in value_node.value:
                    vocab_key = context.yaml_constructor.construct_yaml_str(vocab_key_node)
                    vocab_value = context.yaml_constructor.construct_object(
                        vocab_value_node, deep=True
                    )
                    vocabulary_dict[KeySource(value=vocab_key, key_node=vocab_key_node)] = (
                        ValueSource(value=vocab_value, value_node=vocab_value_node)
                    )
                field_values[field_name] = FieldSource(
                    value=vocabulary_dict, key_node=key_node, value_node=value_node
                )
            else:
                # Not a mapping - preserve as-is for validation
                field_values[field_name] = build_field_source(key_node, value_node, context)
        # dependentRequired (dict[KeySource[str], list[ValueSource[str]]])
        elif key == "dependentRequired":
            if isinstance(value_node, yaml.MappingNode):
                dependent_required_dict: dict[KeySource[str], list[ValueSource[str]]] = {}
                for dep_key_node, dep_value_node in value_node.value:
                    dep_key = context.yaml_constructor.construct_yaml_str(dep_key_node)
                    if isinstance(dep_value_node, yaml.SequenceNode):
                        dep_list: list[ValueSource[str]] = []
                        for item_node in dep_value_node.value:
                            item_value = context.yaml_constructor.construct_object(
                                item_node, deep=True
                            )
                            dep_list.append(ValueSource(value=item_value, value_node=item_node))
                        dependent_required_dict[KeySource(value=dep_key, key_node=dep_key_node)] = (
                            dep_list
                        )
                    else:
                        # Not a sequence - preserve as invalid for validation
                        invalid_value = context.yaml_constructor.construct_object(
                            dep_value_node, deep=True
                        )
                        dependent_required_dict[KeySource(value=dep_key, key_node=dep_key_node)] = (
                            invalid_value  # type: ignore
                        )
                field_values[field_name] = FieldSource(
                    value=dependent_required_dict, key_node=key_node, value_node=value_node
                )
            else:
                # Not a mapping - preserve as-is for validation
                field_values[field_name] = build_field_source(key_node, value_node, context)
        # type field (can be string or list of strings in JSON Schema 2020-12)
        elif key == "type":
            if isinstance(value_node, yaml.SequenceNode):
                # It's a list of types
                type_list: list[ValueSource[str]] = []
                for item_node in value_node.value:
                    item_value = context.yaml_constructor.construct_object(item_node, deep=True)
                    type_list.append(ValueSource(value=item_value, value_node=item_node))
                field_values[field_name] = FieldSource(
                    value=type_list, key_node=key_node, value_node=value_node
                )
            else:
                # It's a single type string
                field_values[field_name] = build_field_source(key_node, value_node, context)
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
