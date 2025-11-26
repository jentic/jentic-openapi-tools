"""Tests for Schema low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import schema
from jentic.apitools.openapi.datamodels.low.v30.discriminator import Discriminator
from jentic.apitools.openapi.datamodels.low.v30.external_documentation import (
    ExternalDocumentation,
)
from jentic.apitools.openapi.datamodels.low.v30.reference import Reference
from jentic.apitools.openapi.datamodels.low.v30.xml import XML


def test_build_with_primitive_string_schema(parse_yaml):
    """Test building Schema with simple string type."""
    yaml_content = textwrap.dedent(
        """
        type: string
        minLength: 1
        maxLength: 100
        pattern: "^[a-zA-Z0-9]+$"
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.root_node == root

    # Check type field
    assert isinstance(result.type, FieldSource)
    assert result.type.value == "string"

    # Check string validation fields
    assert result.min_length is not None
    assert result.min_length.value == 1
    assert result.max_length is not None
    assert result.max_length.value == 100
    assert result.pattern is not None
    assert result.pattern.value == "^[a-zA-Z0-9]+$"


def test_build_with_primitive_number_schema(parse_yaml):
    """Test building Schema with number type and numeric constraints."""
    yaml_content = textwrap.dedent(
        """
        type: number
        format: float
        minimum: 0
        maximum: 100
        multipleOf: 0.5
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.type is not None
    assert result.type.value == "number"
    assert result.format is not None
    assert result.format.value == "float"
    assert result.minimum is not None
    assert result.minimum.value == 0
    assert result.maximum is not None
    assert result.maximum.value == 100
    assert result.multiple_of is not None
    assert result.multiple_of.value == 0.5


def test_build_with_integer_schema(parse_yaml):
    """Test building Schema with integer type."""
    yaml_content = textwrap.dedent(
        """
        type: integer
        format: int32
        minimum: 1
        maximum: 1000
        exclusiveMaximum: true
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.type is not None
    assert result.type.value == "integer"
    assert result.format is not None
    assert result.format.value == "int32"
    assert result.exclusive_maximum is not None
    assert result.exclusive_maximum.value is True


def test_build_with_exclusive_minimum(parse_yaml):
    """Test building Schema with exclusiveMinimum validation."""
    yaml_content = textwrap.dedent(
        """
        type: integer
        format: int32
        minimum: 0
        maximum: 100
        exclusiveMinimum: true
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.type is not None
    assert result.type.value == "integer"
    assert result.format is not None
    assert result.format.value == "int32"
    assert result.minimum is not None
    assert result.minimum.value == 0
    assert result.maximum is not None
    assert result.maximum.value == 100
    assert result.exclusive_minimum is not None
    assert result.exclusive_minimum.value is True


def test_build_with_array_schema(parse_yaml):
    """Test building Schema with array type."""
    yaml_content = textwrap.dedent(
        """
        type: array
        minItems: 1
        maxItems: 10
        uniqueItems: true
        items:
          type: string
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.type is not None
    assert result.type.value == "array"
    assert result.min_items is not None
    assert result.min_items.value == 1
    assert result.max_items is not None
    assert result.max_items.value == 10
    assert result.unique_items is not None
    assert result.unique_items.value is True

    # items should now be a Schema object
    assert result.items is not None
    assert isinstance(result.items.value, schema.Schema)
    assert result.items.value.type is not None
    assert result.items.value.type.value == "string"


def test_build_with_object_schema(parse_yaml):
    """Test building Schema with object type and properties."""
    yaml_content = textwrap.dedent(
        """
        type: object
        required:
          - name
          - age
        properties:
          name:
            type: string
          age:
            type: integer
            minimum: 0
          email:
            type: string
            format: email
        minProperties: 1
        maxProperties: 10
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.type is not None
    assert result.type.value == "object"

    # Check required array
    assert result.required is not None
    assert [item.value for item in result.required.value] == ["name", "age"]

    # Check properties (should be dict[KeySource, ValueSource])
    assert result.properties is not None
    assert isinstance(result.properties.value, dict)
    assert len(result.properties.value) == 3

    # Check minProperties/maxProperties
    assert result.min_properties is not None
    assert result.min_properties.value == 1
    assert result.max_properties is not None
    assert result.max_properties.value == 10


def test_build_with_enum(parse_yaml):
    """Test building Schema with enum constraint."""
    yaml_content = textwrap.dedent(
        """
        type: string
        enum:
          - pending
          - approved
          - rejected
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.enum is not None
    assert [item.value for item in result.enum.value] == ["pending", "approved", "rejected"]


def test_build_with_allof(parse_yaml):
    """Test building Schema with allOf composition."""
    yaml_content = textwrap.dedent(
        """
        allOf:
          - type: object
            properties:
              name:
                type: string
          - type: object
            properties:
              age:
                type: integer
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # allOf should now be list of Schema objects
    assert result.all_of is not None
    assert isinstance(result.all_of.value, list)
    assert len(result.all_of.value) == 2
    # Type narrow to Schema before accessing attributes
    assert isinstance(result.all_of.value[0], schema.Schema)
    assert result.all_of.value[0].type is not None
    assert result.all_of.value[0].type.value == "object"
    assert isinstance(result.all_of.value[1], schema.Schema)
    assert result.all_of.value[1].type is not None
    assert result.all_of.value[1].type.value == "object"


def test_build_with_oneof(parse_yaml):
    """Test building Schema with oneOf composition."""
    yaml_content = textwrap.dedent(
        """
        oneOf:
          - type: string
          - type: number
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.one_of is not None
    assert isinstance(result.one_of.value, list)
    assert len(result.one_of.value) == 2


def test_build_with_anyof(parse_yaml):
    """Test building Schema with anyOf composition."""
    yaml_content = textwrap.dedent(
        """
        anyOf:
          - type: string
            minLength: 5
          - type: string
            format: email
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.any_of is not None
    assert isinstance(result.any_of.value, list)
    assert len(result.any_of.value) == 2


def test_build_with_not(parse_yaml):
    """Test building Schema with not keyword."""
    yaml_content = textwrap.dedent(
        """
        not:
          type: string
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.not_ is not None
    assert isinstance(result.not_.value, schema.Schema)
    assert result.not_.value.type is not None
    assert result.not_.value.type.value == "string"


def test_build_with_allof_references(parse_yaml):
    """Test building Schema with allOf containing $ref (Reference objects)."""
    yaml_content = textwrap.dedent(
        """
        allOf:
          - $ref: '#/components/schemas/Base'
          - type: object
            properties:
              additionalField:
                type: string
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.all_of is not None
    assert isinstance(result.all_of.value, list)
    assert len(result.all_of.value) == 2

    # First element should be a Reference
    assert isinstance(result.all_of.value[0], Reference)
    assert result.all_of.value[0].ref is not None
    assert result.all_of.value[0].ref.value == "#/components/schemas/Base"

    # Second element should be a Schema
    assert isinstance(result.all_of.value[1], schema.Schema)
    assert result.all_of.value[1].type is not None
    assert result.all_of.value[1].type.value == "object"


def test_build_with_oneof_references(parse_yaml):
    """Test building Schema with oneOf containing $ref (Reference objects)."""
    yaml_content = textwrap.dedent(
        """
        oneOf:
          - $ref: '#/components/schemas/Cat'
          - $ref: '#/components/schemas/Dog'
          - type: object
            properties:
              species:
                type: string
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.one_of is not None
    assert isinstance(result.one_of.value, list)
    assert len(result.one_of.value) == 3

    # First two elements should be References
    assert isinstance(result.one_of.value[0], Reference)
    assert result.one_of.value[0].ref is not None
    assert result.one_of.value[0].ref.value == "#/components/schemas/Cat"
    assert isinstance(result.one_of.value[1], Reference)
    assert result.one_of.value[1].ref is not None
    assert result.one_of.value[1].ref.value == "#/components/schemas/Dog"

    # Third element should be a Schema
    assert isinstance(result.one_of.value[2], schema.Schema)
    assert result.one_of.value[2].type is not None
    assert result.one_of.value[2].type.value == "object"


def test_build_with_anyof_references(parse_yaml):
    """Test building Schema with anyOf containing $ref (Reference objects)."""
    yaml_content = textwrap.dedent(
        """
        anyOf:
          - $ref: '#/components/schemas/StringFormat'
          - $ref: '#/components/schemas/NumberFormat'
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.any_of is not None
    assert isinstance(result.any_of.value, list)
    assert len(result.any_of.value) == 2

    # Both elements should be References
    assert isinstance(result.any_of.value[0], Reference)
    assert result.any_of.value[0].ref is not None
    assert result.any_of.value[0].ref.value == "#/components/schemas/StringFormat"
    assert isinstance(result.any_of.value[1], Reference)
    assert result.any_of.value[1].ref is not None
    assert result.any_of.value[1].ref.value == "#/components/schemas/NumberFormat"


def test_build_with_not_reference(parse_yaml):
    """Test building Schema with not containing $ref (Reference object)."""
    yaml_content = textwrap.dedent(
        """
        not:
          $ref: '#/components/schemas/Forbidden'
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.not_ is not None
    assert isinstance(result.not_.value, Reference)
    assert result.not_.value.ref is not None
    assert result.not_.value.ref.value == "#/components/schemas/Forbidden"


def test_build_with_properties_references(parse_yaml):
    """Test building Schema with properties containing $ref (Reference objects)."""
    yaml_content = textwrap.dedent(
        """
        type: object
        properties:
          user:
            $ref: '#/components/schemas/User'
          address:
            $ref: '#/components/schemas/Address'
          name:
            type: string
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.properties is not None
    assert isinstance(result.properties.value, dict)
    assert len(result.properties.value) == 3

    # Extract properties for easier testing
    properties = {k.value: v for k, v in result.properties.value.items()}

    # user and address should be References
    assert isinstance(properties["user"], Reference)
    assert properties["user"].ref is not None
    assert properties["user"].ref.value == "#/components/schemas/User"
    assert isinstance(properties["address"], Reference)
    assert properties["address"].ref is not None
    assert properties["address"].ref.value == "#/components/schemas/Address"

    # name should be a Schema
    assert isinstance(properties["name"], schema.Schema)
    assert properties["name"].type is not None
    assert properties["name"].type.value == "string"


def test_build_with_additional_properties_reference(parse_yaml):
    """Test building Schema with additionalProperties containing $ref (Reference object)."""
    yaml_content = textwrap.dedent(
        """
        type: object
        additionalProperties:
          $ref: '#/components/schemas/StringValue'
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.additional_properties is not None
    assert isinstance(result.additional_properties.value, Reference)
    assert result.additional_properties.value.ref is not None
    assert result.additional_properties.value.ref.value == "#/components/schemas/StringValue"


def test_build_with_additional_properties_boolean(parse_yaml):
    """Test building Schema with additionalProperties as boolean."""
    yaml_content = textwrap.dedent(
        """
        type: object
        additionalProperties: false
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.additional_properties is not None
    assert result.additional_properties.value is False


def test_build_with_additional_properties_schema(parse_yaml):
    """Test building Schema with additionalProperties as schema."""
    yaml_content = textwrap.dedent(
        """
        type: object
        additionalProperties:
          type: string
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.additional_properties is not None
    assert isinstance(result.additional_properties.value, schema.Schema)
    assert result.additional_properties.value.type is not None
    assert result.additional_properties.value.type.value == "string"


def test_build_with_nullable(parse_yaml):
    """Test building Schema with nullable property."""
    yaml_content = textwrap.dedent(
        """
        type: string
        nullable: true
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.nullable is not None
    assert result.nullable.value is True


def test_build_with_discriminator(parse_yaml):
    """Test building Schema with discriminator."""
    yaml_content = textwrap.dedent(
        """
        oneOf:
          - $ref: '#/components/schemas/Cat'
          - $ref: '#/components/schemas/Dog'
        discriminator:
          propertyName: petType
          mapping:
            cat: '#/components/schemas/Cat'
            dog: '#/components/schemas/Dog'
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.discriminator is not None
    assert isinstance(result.discriminator.value, Discriminator)
    assert result.discriminator.value.property_name is not None
    assert result.discriminator.value.property_name.value == "petType"


def test_build_with_readonly_writeonly(parse_yaml):
    """Test building Schema with readOnly and writeOnly."""
    yaml_content = textwrap.dedent(
        """
        type: object
        properties:
          id:
            type: integer
            readOnly: true
          password:
            type: string
            writeOnly: true
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # The readOnly/writeOnly are on nested properties, not root
    # Let's check that properties are preserved
    assert result.properties is not None
    properties = result.properties.value
    assert "id" in {k.value: v for k, v in properties.items()}


def test_build_with_xml(parse_yaml):
    """Test building Schema with XML object."""
    yaml_content = textwrap.dedent(
        """
        type: object
        xml:
          name: user
          namespace: https://example.com/schema/user
          prefix: usr
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.xml is not None
    assert isinstance(result.xml.value, XML)
    assert result.xml.value.name is not None
    assert result.xml.value.name.value == "user"


def test_build_with_external_docs(parse_yaml):
    """Test building Schema with externalDocs."""
    yaml_content = textwrap.dedent(
        """
        type: object
        externalDocs:
          url: https://example.com/docs/user
          description: User schema documentation
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.external_docs is not None
    assert isinstance(result.external_docs.value, ExternalDocumentation)
    assert result.external_docs.value.url is not None
    assert result.external_docs.value.url.value == "https://example.com/docs/user"


def test_build_with_example(parse_yaml):
    """Test building Schema with example."""
    yaml_content = textwrap.dedent(
        """
        type: object
        properties:
          name:
            type: string
        example:
          name: John Doe
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.example is not None
    assert isinstance(result.example.value, dict)
    assert result.example.value["name"] == "John Doe"


def test_build_with_deprecated(parse_yaml):
    """Test building Schema with deprecated flag."""
    yaml_content = textwrap.dedent(
        """
        type: string
        deprecated: true
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.deprecated is not None
    assert result.deprecated.value is True


def test_build_with_default(parse_yaml):
    """Test building Schema with default value."""
    yaml_content = textwrap.dedent(
        """
        type: string
        default: "N/A"
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.default is not None
    assert result.default.value == "N/A"


def test_build_with_title_and_description(parse_yaml):
    """Test building Schema with title and description."""
    yaml_content = textwrap.dedent(
        """
        type: object
        title: User
        description: |
          A user in the system.

          This represents a registered user with all their details.
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.title is not None
    assert result.title.value == "User"
    assert result.description is not None
    assert "A user in the system" in result.description.value


def test_build_with_extensions(parse_yaml):
    """Test building Schema with specification extensions."""
    yaml_content = textwrap.dedent(
        """
        type: string
        x-internal: true
        x-validation-level: strict
        x-metadata:
          version: "1.0"
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.extensions is not None
    assert len(result.extensions) == 3

    # Extensions should be dict[KeySource, ValueSource]
    keys = list(result.extensions.keys())
    assert all(isinstance(k, KeySource) for k in keys)
    assert all(isinstance(v, ValueSource) for v in result.extensions.values())

    # Check extension values
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-internal"] is True
    assert ext_dict["x-validation-level"] == "strict"


def test_build_with_complex_nested_schema(parse_yaml):
    """Test building Schema with complex nested structure."""
    yaml_content = textwrap.dedent(
        """
        type: object
        required:
          - items
        properties:
          items:
            type: array
            items:
              type: object
              properties:
                id:
                  type: integer
                name:
                  type: string
              required:
                - id
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.type is not None
    assert result.type.value == "object"
    assert result.required is not None
    assert [item.value for item in result.required.value] == ["items"]
    assert result.properties is not None


def test_build_preserves_invalid_types(parse_yaml):
    """Test that build preserves values even with 'wrong' types (low-level model principle)."""
    yaml_content = textwrap.dedent(
        """
        type: 12345
        minLength: "not-a-number"
        enum: not-an-array
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Should preserve the actual values, not convert them
    assert result.type is not None
    assert result.type.value == 12345
    assert result.min_length is not None
    assert result.min_length.value == "not-a-number"
    assert result.enum is not None
    assert result.enum.value == "not-an-array"


def test_build_with_empty_object(parse_yaml):
    """Test building Schema from empty YAML object."""
    yaml_content = "{}"
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.root_node == root
    assert result.type is None
    assert result.properties is None
    # Extensions returns empty dict when no extensions present
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test that build returns ValueSource for non-mapping nodes (preserves invalid data)."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("string-schema")
    result = schema.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "string-schema"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['schema1', 'schema2']")
    result = schema.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["schema1", "schema2"]
    assert result.value_node == sequence_root


def test_build_with_custom_context(parse_yaml):
    """Test building Schema with a custom context."""
    yaml_content = textwrap.dedent(
        """
        type: string
        format: email
        """
    )
    root = parse_yaml(yaml_content)

    custom_context = Context()
    result = schema.build(root, context=custom_context)
    assert isinstance(result, schema.Schema)

    assert result.type is not None
    assert result.type.value == "string"
    assert result.format is not None
    assert result.format.value == "email"


def test_source_tracking(parse_yaml):
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        type: string
        minLength: 1
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.type is not None

    # Check that key_node and value_node are tracked
    assert result.type.key_node is not None
    assert result.type.value_node is not None

    # The key_node should contain "type"
    assert result.type.key_node.value == "type"

    # The value_node should contain "string"
    assert result.type.value_node.value == "string"

    # Check line numbers are available (for error reporting)
    assert hasattr(result.type.key_node.start_mark, "line")
    assert hasattr(result.type.value_node.start_mark, "line")


def test_build_with_self_referential_schema(parse_yaml):
    """Test building Schema with self-referential structure (recursive schema)."""
    yaml_content = textwrap.dedent(
        """
        type: object
        properties:
          name:
            type: string
          children:
            type: array
            items:
              $ref: '#/components/schemas/Node'
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check that the self-referential structure is preserved
    assert result.properties is not None
    properties = {k.value: v for k, v in result.properties.value.items()}
    assert "children" in properties
    # Type narrow to Schema before accessing attributes
    children_value = properties["children"]
    assert isinstance(children_value, schema.Schema)
    assert children_value.type is not None
    assert children_value.type.value == "array"


def test_schema_reference_has_meta(parse_yaml):
    """Test that schema references have metadata indicating referenced_type."""
    yaml_content = textwrap.dedent(
        """
        type: object
        properties:
          user:
            $ref: '#/components/schemas/User'
        """
    )
    root = parse_yaml(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check that properties contains a Reference
    assert result.properties is not None
    properties = {k.value: v for k, v in result.properties.value.items()}
    assert "user" in properties

    user_ref = properties["user"]
    assert isinstance(user_ref, Reference)

    # Verify meta field is set correctly
    assert user_ref.meta is not None
    assert user_ref.meta == {"referenced_type": "Schema"}

    # Verify the $ref value is preserved
    assert user_ref.ref is not None
    assert user_ref.ref.value == "#/components/schemas/User"
