"""Tests for Schema low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v31 import schema
from jentic.apitools.openapi.datamodels.low.v31.discriminator import Discriminator
from jentic.apitools.openapi.datamodels.low.v31.external_documentation import (
    ExternalDocumentation,
)
from jentic.apitools.openapi.datamodels.low.v31.schema import Schema
from jentic.apitools.openapi.datamodels.low.v31.xml import XML


def test_build_with_primitive_string_schema():
    """Test building Schema with simple string type."""
    yaml_content = textwrap.dedent(
        """
        type: string
        minLength: 1
        maxLength: 100
        pattern: "^[a-zA-Z0-9]+$"
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

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


def test_build_with_primitive_number_schema():
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
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

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


def test_build_with_integer_schema():
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
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.type is not None
    assert result.type.value == "integer"
    assert result.format is not None
    assert result.format.value == "int32"
    assert result.exclusive_maximum is not None
    assert result.exclusive_maximum.value is True


def test_build_with_exclusive_minimum():
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
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

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


def test_build_with_array_schema():
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
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

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


def test_build_with_object_schema():
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
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

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


def test_build_with_enum():
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
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.enum is not None
    assert [item.value for item in result.enum.value] == ["pending", "approved", "rejected"]


def test_build_with_allof():
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
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

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


def test_build_with_oneof():
    """Test building Schema with oneOf composition."""
    yaml_content = textwrap.dedent(
        """
        oneOf:
          - type: string
          - type: number
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.one_of is not None
    assert isinstance(result.one_of.value, list)
    assert len(result.one_of.value) == 2


def test_build_with_anyof():
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
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.any_of is not None
    assert isinstance(result.any_of.value, list)
    assert len(result.any_of.value) == 2


def test_build_with_not():
    """Test building Schema with not keyword."""
    yaml_content = textwrap.dedent(
        """
        not:
          type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.not_ is not None
    assert isinstance(result.not_.value, schema.Schema)
    assert result.not_.value.type is not None
    assert result.not_.value.type.value == "string"


def test_build_with_allof_references():
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
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.all_of is not None
    assert isinstance(result.all_of.value, list)
    assert len(result.all_of.value) == 2

    # First element should be a Reference
    assert isinstance(result.all_of.value[0], Schema)  # In 3.1, nested schemas are Schema objects

    # Second element should be a Schema
    assert isinstance(result.all_of.value[1], schema.Schema)
    assert result.all_of.value[1].type is not None
    assert result.all_of.value[1].type.value == "object"


def test_build_with_oneof_references():
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
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.one_of is not None
    assert isinstance(result.one_of.value, list)
    assert len(result.one_of.value) == 3

    # First two elements should be References
    assert isinstance(result.one_of.value[0], Schema)  # In 3.1, nested schemas are Schema objects
    assert isinstance(result.one_of.value[1], Schema)  # In 3.1, nested schemas are Schema objects

    # Third element should be a Schema
    assert isinstance(result.one_of.value[2], schema.Schema)
    assert result.one_of.value[2].type is not None
    assert result.one_of.value[2].type.value == "object"


def test_build_with_anyof_references():
    """Test building Schema with anyOf containing $ref (Reference objects)."""
    yaml_content = textwrap.dedent(
        """
        anyOf:
          - $ref: '#/components/schemas/StringFormat'
          - $ref: '#/components/schemas/NumberFormat'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.any_of is not None
    assert isinstance(result.any_of.value, list)
    assert len(result.any_of.value) == 2

    # Both elements should be References
    assert isinstance(result.any_of.value[0], Schema)  # In 3.1, nested schemas are Schema objects
    assert isinstance(result.any_of.value[1], Schema)  # In 3.1, nested schemas are Schema objects


def test_build_with_not_reference():
    """Test building Schema with not containing $ref (Reference object)."""
    yaml_content = textwrap.dedent(
        """
        not:
          $ref: '#/components/schemas/Forbidden'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.not_ is not None
    assert isinstance(result.not_.value, Schema)  # In 3.1, nested schemas are Schema objects


def test_build_with_properties_references():
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
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.properties is not None
    assert isinstance(result.properties.value, dict)
    assert len(result.properties.value) == 3

    # Extract properties for easier testing
    properties = {k.value: v for k, v in result.properties.value.items()}

    # user and address should be References
    assert isinstance(properties["user"], Schema)  # In 3.1, nested schemas are Schema objects
    assert isinstance(properties["address"], Schema)  # In 3.1, nested schemas are Schema objects

    # name should be a Schema
    assert isinstance(properties["name"], schema.Schema)
    assert properties["name"].type is not None
    assert properties["name"].type.value == "string"


def test_build_with_additional_properties_reference():
    """Test building Schema with additionalProperties containing $ref (Reference object)."""
    yaml_content = textwrap.dedent(
        """
        type: object
        additionalProperties:
          $ref: '#/components/schemas/StringValue'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.additional_properties is not None
    assert isinstance(
        result.additional_properties.value, Schema
    )  # In 3.1, nested schemas are Schema objects


def test_build_with_additional_properties_boolean():
    """Test building Schema with additionalProperties as boolean."""
    yaml_content = textwrap.dedent(
        """
        type: object
        additionalProperties: false
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.additional_properties is not None
    assert result.additional_properties.value is False


def test_build_with_additional_properties_schema():
    """Test building Schema with additionalProperties as schema."""
    yaml_content = textwrap.dedent(
        """
        type: object
        additionalProperties:
          type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.additional_properties is not None
    assert isinstance(result.additional_properties.value, schema.Schema)
    assert result.additional_properties.value.type is not None
    assert result.additional_properties.value.type.value == "string"


def test_build_with_type_array():
    """Test building Schema with type as array (JSON Schema 2020-12 feature for nullable)."""
    yaml_content = textwrap.dedent(
        """
        type:
          - string
          - "null"
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # In JSON Schema 2020-12, type can be an array
    assert result.type is not None
    assert isinstance(result.type.value, list)
    assert len(result.type.value) == 2
    assert result.type.value[0].value == "string"
    assert result.type.value[1].value == "null"


def test_build_with_discriminator():
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
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.discriminator is not None
    assert isinstance(result.discriminator.value, Discriminator)
    assert result.discriminator.value.property_name is not None
    assert result.discriminator.value.property_name.value == "petType"


def test_build_with_readonly_writeonly():
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
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # The readOnly/writeOnly are on nested properties, not root
    # Let's check that properties are preserved
    assert result.properties is not None
    properties = result.properties.value
    assert "id" in {k.value: v for k, v in properties.items()}


def test_build_with_xml():
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
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.xml is not None
    assert isinstance(result.xml.value, XML)
    assert result.xml.value.name is not None
    assert result.xml.value.name.value == "user"


def test_build_with_external_docs():
    """Test building Schema with externalDocs."""
    yaml_content = textwrap.dedent(
        """
        type: object
        externalDocs:
          url: https://example.com/docs/user
          description: User schema documentation
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.external_docs is not None
    assert isinstance(result.external_docs.value, ExternalDocumentation)
    assert result.external_docs.value.url is not None
    assert result.external_docs.value.url.value == "https://example.com/docs/user"


def test_build_with_example():
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
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.example is not None
    assert isinstance(result.example.value, dict)
    assert result.example.value["name"] == "John Doe"


def test_build_with_deprecated():
    """Test building Schema with deprecated flag."""
    yaml_content = textwrap.dedent(
        """
        type: string
        deprecated: true
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.deprecated is not None
    assert result.deprecated.value is True


def test_build_with_default():
    """Test building Schema with default value."""
    yaml_content = textwrap.dedent(
        """
        type: string
        default: "N/A"
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.default is not None
    assert result.default.value == "N/A"


def test_build_with_title_and_description():
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
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.title is not None
    assert result.title.value == "User"
    assert result.description is not None
    assert "A user in the system" in result.description.value


def test_build_with_extensions():
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
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

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


def test_build_with_complex_nested_schema():
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
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.type is not None
    assert result.type.value == "object"
    assert result.required is not None
    assert [item.value for item in result.required.value] == ["items"]
    assert result.properties is not None


def test_build_preserves_invalid_types():
    """Test that build preserves values even with 'wrong' types (low-level model principle)."""
    yaml_content = textwrap.dedent(
        """
        type: 12345
        minLength: "not-a-number"
        enum: not-an-array
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Should preserve the actual values, not convert them
    assert result.type is not None
    assert result.type.value == 12345
    assert result.min_length is not None
    assert result.min_length.value == "not-a-number"
    assert result.enum is not None
    assert result.enum.value == "not-an-array"


def test_build_with_empty_object():
    """Test building Schema from empty YAML object."""
    yaml_content = "{}"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

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


def test_build_with_custom_context():
    """Test building Schema with a custom context."""
    yaml_content = textwrap.dedent(
        """
        type: string
        format: email
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = schema.build(root, context=custom_context)
    assert isinstance(result, schema.Schema)

    assert result.type is not None
    assert result.type.value == "string"
    assert result.format is not None
    assert result.format.value == "email"


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        type: string
        minLength: 1
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

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


def test_build_with_self_referential_schema():
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
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

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


# JSON Schema 2020-12 specific tests


def test_build_with_prefix_items():
    """Test building Schema with prefixItems (tuple validation)."""
    yaml_content = textwrap.dedent(
        """
        type: array
        prefixItems:
          - type: string
          - type: number
          - type: boolean
        items: false
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.prefix_items is not None
    assert isinstance(result.prefix_items.value, list)
    assert len(result.prefix_items.value) == 3

    # Check each prefixItem schema
    assert isinstance(result.prefix_items.value[0], schema.Schema)
    assert result.prefix_items.value[0].type is not None
    assert result.prefix_items.value[0].type.value == "string"

    assert isinstance(result.prefix_items.value[1], schema.Schema)
    assert result.prefix_items.value[1].type is not None
    assert result.prefix_items.value[1].type.value == "number"

    assert isinstance(result.prefix_items.value[2], schema.Schema)
    assert result.prefix_items.value[2].type is not None
    assert result.prefix_items.value[2].type.value == "boolean"

    # items should be false (no additional items allowed)
    assert result.items is not None
    assert result.items.value is False


def test_build_with_prefix_items_nested():
    """Test building Schema with prefixItems containing nested objects."""
    yaml_content = textwrap.dedent(
        """
        type: array
        prefixItems:
          - type: object
            properties:
              name:
                type: string
          - type: array
            items:
              type: integer
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.prefix_items is not None
    assert len(result.prefix_items.value) == 2

    # First item is an object schema with nested properties
    first_item = result.prefix_items.value[0]
    assert isinstance(first_item, schema.Schema)
    assert first_item.type is not None
    assert first_item.type.value == "object"
    assert first_item.properties is not None
    properties_dict = {k.value: v for k, v in first_item.properties.value.items()}
    assert "name" in properties_dict
    assert isinstance(properties_dict["name"], schema.Schema)

    # Second item is an array schema with nested items
    second_item = result.prefix_items.value[1]
    assert isinstance(second_item, schema.Schema)
    assert second_item.type is not None
    assert second_item.type.value == "array"
    assert second_item.items is not None
    assert isinstance(second_item.items.value, schema.Schema)


def test_build_with_if_then_else():
    """Test building Schema with conditional if/then/else."""
    yaml_content = textwrap.dedent(
        """
        type: object
        properties:
          country:
            type: string
          postal_code:
            type: string
        if:
          properties:
            country:
              const: "USA"
        then:
          properties:
            postal_code:
              pattern: "^[0-9]{5}$"
        else:
          properties:
            postal_code:
              minLength: 1
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check if clause
    assert result.if_ is not None
    assert isinstance(result.if_.value, schema.Schema)
    assert result.if_.value.properties is not None

    # Check then clause
    assert result.then_ is not None
    assert isinstance(result.then_.value, schema.Schema)
    assert result.then_.value.properties is not None

    # Check else clause
    assert result.else_ is not None
    assert isinstance(result.else_.value, schema.Schema)
    assert result.else_.value.properties is not None


def test_build_with_if_then_else_nested():
    """Test building Schema with deeply nested conditional schemas."""
    yaml_content = textwrap.dedent(
        """
        if:
          properties:
            type:
              enum: [premium, enterprise]
        then:
          allOf:
            - properties:
                support:
                  type: object
                  properties:
                    level:
                      enum: [priority, dedicated]
            - required: [support]
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check if with nested enum
    assert result.if_ is not None
    if_schema = result.if_.value
    assert isinstance(if_schema, schema.Schema)

    # Check then with allOf containing nested objects
    assert result.then_ is not None
    then_schema = result.then_.value
    assert isinstance(then_schema, schema.Schema)
    assert then_schema.all_of is not None
    assert len(then_schema.all_of.value) == 2


def test_build_with_contains():
    """Test building Schema with contains keyword."""
    yaml_content = textwrap.dedent(
        """
        type: array
        contains:
          type: object
          properties:
            id:
              type: integer
          required: [id]
        minContains: 1
        maxContains: 3
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check contains schema
    assert result.contains is not None
    assert isinstance(result.contains.value, schema.Schema)
    assert result.contains.value.type is not None
    assert result.contains.value.type.value == "object"
    assert result.contains.value.properties is not None

    # Check min/max contains
    assert result.min_contains is not None
    assert result.min_contains.value == 1
    assert result.max_contains is not None
    assert result.max_contains.value == 3


def test_build_with_contains_complex_nested():
    """Test building Schema with contains having deeply nested schemas."""
    yaml_content = textwrap.dedent(
        """
        type: array
        contains:
          oneOf:
            - type: object
              properties:
                name:
                  type: string
            - type: object
              properties:
                id:
                  type: integer
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # contains should be a schema with oneOf
    assert result.contains is not None
    contains_schema = result.contains.value
    assert isinstance(contains_schema, schema.Schema)
    assert contains_schema.one_of is not None
    assert len(contains_schema.one_of.value) == 2


def test_build_with_property_names():
    """Test building Schema with propertyNames keyword."""
    yaml_content = textwrap.dedent(
        """
        type: object
        propertyNames:
          pattern: "^[A-Za-z_][A-Za-z0-9_]*$"
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check propertyNames schema
    assert result.property_names is not None
    assert isinstance(result.property_names.value, schema.Schema)
    assert result.property_names.value.pattern is not None
    assert result.property_names.value.pattern.value == "^[A-Za-z_][A-Za-z0-9_]*$"


def test_build_with_property_names_complex():
    """Test building Schema with complex propertyNames schema."""
    yaml_content = textwrap.dedent(
        """
        type: object
        propertyNames:
          anyOf:
            - pattern: "^[a-z]+$"
            - pattern: "^[A-Z]+$"
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # propertyNames should be a schema with anyOf
    assert result.property_names is not None
    property_names_schema = result.property_names.value
    assert isinstance(property_names_schema, schema.Schema)
    assert property_names_schema.any_of is not None
    assert len(property_names_schema.any_of.value) == 2


def test_build_with_content_schema():
    """Test building Schema with contentSchema keyword."""
    yaml_content = textwrap.dedent(
        """
        type: string
        contentMediaType: application/json
        contentEncoding: base64
        contentSchema:
          type: object
          properties:
            name:
              type: string
            age:
              type: integer
          required: [name]
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check contentSchema
    assert result.content_schema is not None
    assert isinstance(result.content_schema.value, schema.Schema)
    assert result.content_schema.value.type is not None
    assert result.content_schema.value.type.value == "object"
    assert result.content_schema.value.properties is not None
    assert result.content_schema.value.required is not None


def test_build_with_pattern_properties():
    """Test building Schema with patternProperties keyword."""
    yaml_content = textwrap.dedent(
        """
        type: object
        patternProperties:
          "^S_":
            type: string
          "^I_":
            type: integer
          "^O_":
            type: object
            properties:
              value:
                type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check patternProperties
    assert result.pattern_properties is not None
    assert isinstance(result.pattern_properties.value, dict)
    assert len(result.pattern_properties.value) == 3

    # Convert to dict for easier testing
    patterns_dict = {k.value: v for k, v in result.pattern_properties.value.items()}

    # Check string pattern
    assert "^S_" in patterns_dict
    assert isinstance(patterns_dict["^S_"], schema.Schema)
    assert patterns_dict["^S_"].type is not None
    assert patterns_dict["^S_"].type.value == "string"

    # Check integer pattern
    assert "^I_" in patterns_dict
    assert isinstance(patterns_dict["^I_"], schema.Schema)
    assert patterns_dict["^I_"].type is not None
    assert patterns_dict["^I_"].type.value == "integer"

    # Check object pattern with nested properties
    assert "^O_" in patterns_dict
    assert isinstance(patterns_dict["^O_"], schema.Schema)
    assert patterns_dict["^O_"].type is not None
    assert patterns_dict["^O_"].type.value == "object"
    assert patterns_dict["^O_"].properties is not None


def test_build_with_dependent_schemas():
    """Test building Schema with dependentSchemas keyword."""
    yaml_content = textwrap.dedent(
        """
        type: object
        properties:
          creditCard:
            type: string
          billingAddress:
            type: string
        dependentSchemas:
          creditCard:
            required: [billingAddress]
            properties:
              cvv:
                type: string
                pattern: "^[0-9]{3}$"
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check dependentSchemas
    assert result.dependent_schemas is not None
    assert isinstance(result.dependent_schemas.value, dict)

    # Convert to dict
    dep_schemas = {k.value: v for k, v in result.dependent_schemas.value.items()}
    assert "creditCard" in dep_schemas

    # Check the dependent schema
    credit_card_schema = dep_schemas["creditCard"]
    assert isinstance(credit_card_schema, schema.Schema)
    assert credit_card_schema.required is not None
    assert credit_card_schema.properties is not None


def test_build_with_dependent_schemas_complex():
    """Test building Schema with complex nested dependentSchemas."""
    yaml_content = textwrap.dedent(
        """
        type: object
        dependentSchemas:
          premium:
            allOf:
              - properties:
                  support:
                    type: object
                    properties:
                      level:
                        enum: [priority, dedicated]
              - required: [support]
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check dependentSchemas with nested allOf
    assert result.dependent_schemas is not None
    dep_schemas = {k.value: v for k, v in result.dependent_schemas.value.items()}
    assert "premium" in dep_schemas

    premium_schema = dep_schemas["premium"]
    assert isinstance(premium_schema, schema.Schema)
    assert premium_schema.all_of is not None
    assert len(premium_schema.all_of.value) == 2


def test_build_with_dependent_required():
    """Test building Schema with dependentRequired keyword."""
    yaml_content = textwrap.dedent(
        """
        type: object
        properties:
          creditCard:
            type: string
          billingAddress:
            type: string
          cvv:
            type: string
        dependentRequired:
          creditCard:
            - billingAddress
            - cvv
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check dependentRequired
    assert result.dependent_required is not None
    assert isinstance(result.dependent_required.value, dict)

    # Convert to dict
    dep_required = {k.value: v for k, v in result.dependent_required.value.items()}
    assert "creditCard" in dep_required

    # Check the required fields list
    required_fields = dep_required["creditCard"]
    assert isinstance(required_fields, list)
    assert len(required_fields) == 2
    assert all(isinstance(item, ValueSource) for item in required_fields)
    assert [item.value for item in required_fields] == ["billingAddress", "cvv"]


def test_build_with_unevaluated_items():
    """Test building Schema with unevaluatedItems keyword."""
    yaml_content = textwrap.dedent(
        """
        type: array
        prefixItems:
          - type: string
          - type: number
        unevaluatedItems:
          type: boolean
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check prefixItems
    assert result.prefix_items is not None
    assert len(result.prefix_items.value) == 2

    # Check unevaluatedItems as schema
    assert result.unevaluated_items is not None
    assert isinstance(result.unevaluated_items.value, schema.Schema)
    assert result.unevaluated_items.value.type is not None
    assert result.unevaluated_items.value.type.value == "boolean"


def test_build_with_unevaluated_items_boolean():
    """Test building Schema with unevaluatedItems as boolean."""
    yaml_content = textwrap.dedent(
        """
        type: array
        prefixItems:
          - type: string
        unevaluatedItems: false
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check unevaluatedItems as boolean
    assert result.unevaluated_items is not None
    assert result.unevaluated_items.value is False


def test_build_with_unevaluated_properties():
    """Test building Schema with unevaluatedProperties keyword."""
    yaml_content = textwrap.dedent(
        """
        type: object
        properties:
          foo:
            type: string
        patternProperties:
          "^bar":
            type: number
        unevaluatedProperties:
          type: boolean
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check unevaluatedProperties as schema
    assert result.unevaluated_properties is not None
    assert isinstance(result.unevaluated_properties.value, schema.Schema)
    assert result.unevaluated_properties.value.type is not None
    assert result.unevaluated_properties.value.type.value == "boolean"


def test_build_with_unevaluated_properties_boolean():
    """Test building Schema with unevaluatedProperties as boolean."""
    yaml_content = textwrap.dedent(
        """
        type: object
        properties:
          foo:
            type: string
        unevaluatedProperties: false
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check unevaluatedProperties as boolean
    assert result.unevaluated_properties is not None
    assert result.unevaluated_properties.value is False


def test_build_with_defs():
    """Test building Schema with $defs keyword."""
    yaml_content = textwrap.dedent(
        """
        $defs:
          address:
            type: object
            properties:
              street:
                type: string
              city:
                type: string
          person:
            type: object
            properties:
              name:
                type: string
              address:
                $ref: "#/$defs/address"
        type: object
        properties:
          employee:
            $ref: "#/$defs/person"
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check $defs
    assert result.defs is not None
    assert isinstance(result.defs.value, dict)
    assert len(result.defs.value) == 2

    # Convert to dict
    defs_dict = {k.value: v for k, v in result.defs.value.items()}

    # Check address definition
    assert "address" in defs_dict
    address_schema = defs_dict["address"]
    assert isinstance(address_schema, schema.Schema)
    assert address_schema.type is not None
    assert address_schema.type.value == "object"
    assert address_schema.properties is not None

    # Check person definition with nested reference
    assert "person" in defs_dict
    person_schema = defs_dict["person"]
    assert isinstance(person_schema, schema.Schema)
    assert person_schema.properties is not None


def test_build_with_defs_nested_references():
    """Test building Schema with $defs containing circular-like references."""
    yaml_content = textwrap.dedent(
        """
        $defs:
          node:
            type: object
            properties:
              value:
                type: string
              children:
                type: array
                items:
                  $ref: "#/$defs/node"
        type: object
        properties:
          root:
            $ref: "#/$defs/node"
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check $defs with recursive structure
    assert result.defs is not None
    defs_dict = {k.value: v for k, v in result.defs.value.items()}

    assert "node" in defs_dict
    node_schema = defs_dict["node"]
    assert isinstance(node_schema, schema.Schema)
    assert node_schema.properties is not None

    # Check that children property has an array with items reference
    node_props = {k.value: v for k, v in node_schema.properties.value.items()}
    assert "children" in node_props
    children_schema = node_props["children"]
    assert isinstance(children_schema, schema.Schema)
    assert children_schema.items is not None


def test_build_with_boolean_schema_true():
    """Test building Schema with boolean schema (true) in various contexts."""
    yaml_content = textwrap.dedent(
        """
        type: object
        properties:
          acceptAnything: true
        additionalProperties: true
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check property with true schema
    assert result.properties is not None
    props_dict = {k.value: v for k, v in result.properties.value.items()}
    assert "acceptAnything" in props_dict
    # true should be a ValueSource with value True
    accept_anything = props_dict["acceptAnything"]
    assert isinstance(accept_anything, ValueSource)
    assert accept_anything.value is True

    # Check additionalProperties with true
    assert result.additional_properties is not None
    assert result.additional_properties.value is True


def test_build_with_boolean_schema_false():
    """Test building Schema with boolean schema (false) in various contexts."""
    yaml_content = textwrap.dedent(
        """
        type: object
        properties:
          validProp:
            type: string
        additionalProperties: false
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check additionalProperties with false
    assert result.additional_properties is not None
    assert result.additional_properties.value is False


def test_build_with_items_boolean():
    """Test building Schema with items as boolean."""
    yaml_content = textwrap.dedent(
        """
        type: array
        prefixItems:
          - type: string
          - type: number
        items: false
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # items should be boolean false
    assert result.items is not None
    assert result.items.value is False

    # prefixItems should still be schemas
    assert result.prefix_items is not None
    assert len(result.prefix_items.value) == 2


def test_build_with_vocabulary():
    """Test building Schema with $vocabulary keyword."""
    yaml_content = textwrap.dedent(
        """
        $schema: "https://json-schema.org/draft/2020-12/schema"
        $vocabulary:
          "https://json-schema.org/draft/2020-12/vocab/core": true
          "https://json-schema.org/draft/2020-12/vocab/applicator": true
          "https://json-schema.org/draft/2020-12/vocab/validation": true
          "https://example.com/custom-vocab": false
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check $vocabulary
    assert result.vocabulary is not None
    assert isinstance(result.vocabulary.value, dict)
    assert len(result.vocabulary.value) == 4

    # Convert to dict
    vocab_dict = {k.value: v.value for k, v in result.vocabulary.value.items()}

    # Check vocabulary entries
    assert vocab_dict["https://json-schema.org/draft/2020-12/vocab/core"] is True
    assert vocab_dict["https://json-schema.org/draft/2020-12/vocab/applicator"] is True
    assert vocab_dict["https://json-schema.org/draft/2020-12/vocab/validation"] is True
    assert vocab_dict["https://example.com/custom-vocab"] is False


def test_build_with_anchor_and_dynamic_anchor():
    """Test building Schema with $anchor and $dynamicAnchor keywords."""
    yaml_content = textwrap.dedent(
        """
        $anchor: base-schema
        $dynamicAnchor: meta-schema
        type: object
        properties:
          name:
            type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check $anchor
    assert result.anchor is not None
    assert result.anchor.value == "base-schema"

    # Check $dynamicAnchor
    assert result.dynamic_anchor is not None
    assert result.dynamic_anchor.value == "meta-schema"


def test_build_with_dynamic_ref():
    """Test building Schema with $dynamicRef keyword."""
    yaml_content = textwrap.dedent(
        """
        type: object
        properties:
          metadata:
            $dynamicRef: "#meta"
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check that properties contains the $dynamicRef schema
    assert result.properties is not None
    props_dict = {k.value: v for k, v in result.properties.value.items()}
    assert "metadata" in props_dict

    # The property should be a Schema with dynamic_ref
    metadata_schema = props_dict["metadata"]
    assert isinstance(metadata_schema, schema.Schema)
    assert metadata_schema.dynamic_ref is not None
    assert metadata_schema.dynamic_ref.value == "#meta"


def test_build_with_deeply_nested_recursive_schema():
    """Test building Schema with deeply nested recursive structures."""
    yaml_content = textwrap.dedent(
        """
        $defs:
          tree:
            type: object
            properties:
              value:
                type: string
              left:
                anyOf:
                  - $ref: "#/$defs/tree"
                  - type: "null"
              right:
                anyOf:
                  - $ref: "#/$defs/tree"
                  - type: "null"
        type: object
        properties:
          root:
            allOf:
              - $ref: "#/$defs/tree"
              - properties:
                  depth:
                    type: integer
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Check $defs with tree structure
    assert result.defs is not None
    defs_dict = {k.value: v for k, v in result.defs.value.items()}
    assert "tree" in defs_dict

    tree_schema = defs_dict["tree"]
    assert isinstance(tree_schema, schema.Schema)
    assert tree_schema.properties is not None

    # Check tree properties
    tree_props = {k.value: v for k, v in tree_schema.properties.value.items()}
    assert "left" in tree_props
    assert "right" in tree_props

    # Check left with anyOf
    left_schema = tree_props["left"]
    assert isinstance(left_schema, schema.Schema)
    assert left_schema.any_of is not None

    # Check root property with allOf
    assert result.properties is not None
    root_props = {k.value: v for k, v in result.properties.value.items()}
    assert "root" in root_props
    root_schema = root_props["root"]
    assert isinstance(root_schema, schema.Schema)
    assert root_schema.all_of is not None


def test_build_with_complex_composition():
    """Test building Schema combining multiple JSON Schema 2020-12 features."""
    yaml_content = textwrap.dedent(
        """
        $defs:
          positiveInteger:
            type: integer
            minimum: 1
        type: object
        properties:
          items:
            type: array
            prefixItems:
              - type: string
              - $ref: "#/$defs/positiveInteger"
            contains:
              type: object
              required: [id]
            minContains: 1
        patternProperties:
          "^meta_":
            type: string
        unevaluatedProperties: false
        if:
          properties:
            items:
              minItems: 5
        then:
          required: [summary]
          properties:
            summary:
              type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Verify all complex features are present
    assert result.defs is not None
    assert result.properties is not None
    assert result.pattern_properties is not None
    assert result.unevaluated_properties is not None
    assert result.unevaluated_properties.value is False
    assert result.if_ is not None
    assert result.then_ is not None

    # Verify nested prefixItems and contains in items property
    props_dict = {k.value: v for k, v in result.properties.value.items()}
    items_schema = props_dict["items"]
    assert isinstance(items_schema, schema.Schema)
    assert items_schema.prefix_items is not None
    assert items_schema.contains is not None
    assert items_schema.min_contains is not None


def test_build_boolean_schema_at_root():
    """Test building a boolean schema (true/false) at the root level."""
    yaml_parser = YAML()

    # Test with true
    root_true = yaml_parser.compose("true")
    result_true = schema.build(root_true)
    assert isinstance(result_true, ValueSource)
    assert result_true.value is True

    # Test with false
    root_false = yaml_parser.compose("false")
    result_false = schema.build(root_false)
    assert isinstance(result_false, ValueSource)
    assert result_false.value is False


def test_build_with_all_applicator_keywords():
    """Test building Schema with all applicator keywords combined."""
    yaml_content = textwrap.dedent(
        """
        allOf:
          - type: object
        anyOf:
          - required: [name]
          - required: [id]
        oneOf:
          - properties:
              type:
                const: "person"
          - properties:
              type:
                const: "company"
        not:
          properties:
            forbidden:
              type: string
        if:
          properties:
            country:
              const: "USA"
        then:
          required: [state]
        else:
          required: [province]
        properties:
          name:
            type: string
        patternProperties:
          "^ext_":
            type: string
        additionalProperties: false
        propertyNames:
          pattern: "^[a-z_]+$"
        dependentSchemas:
          premium:
            required: [support_level]
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    # Verify all applicator keywords are present
    assert result.all_of is not None
    assert result.any_of is not None
    assert result.one_of is not None
    assert result.not_ is not None
    assert result.if_ is not None
    assert result.then_ is not None
    assert result.else_ is not None
    assert result.properties is not None
    assert result.pattern_properties is not None
    assert result.additional_properties is not None
    assert result.property_names is not None
    assert result.dependent_schemas is not None
