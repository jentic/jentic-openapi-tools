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
    assert result.minLength is not None
    assert result.minLength.value == 1
    assert result.maxLength is not None
    assert result.maxLength.value == 100
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
    assert result.multipleOf is not None
    assert result.multipleOf.value == 0.5


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
    assert result.exclusiveMaximum is not None
    assert result.exclusiveMaximum.value is True


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
    assert result.exclusiveMinimum is not None
    assert result.exclusiveMinimum.value is True


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
    assert result.minItems is not None
    assert result.minItems.value == 1
    assert result.maxItems is not None
    assert result.maxItems.value == 10
    assert result.uniqueItems is not None
    assert result.uniqueItems.value is True

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
    assert result.minProperties is not None
    assert result.minProperties.value == 1
    assert result.maxProperties is not None
    assert result.maxProperties.value == 10


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
    assert result.allOf is not None
    assert isinstance(result.allOf.value, list)
    assert len(result.allOf.value) == 2
    # Type narrow to Schema before accessing attributes
    assert isinstance(result.allOf.value[0], schema.Schema)
    assert result.allOf.value[0].type is not None
    assert result.allOf.value[0].type.value == "object"
    assert isinstance(result.allOf.value[1], schema.Schema)
    assert result.allOf.value[1].type is not None
    assert result.allOf.value[1].type.value == "object"


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

    assert result.oneOf is not None
    assert isinstance(result.oneOf.value, list)
    assert len(result.oneOf.value) == 2


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

    assert result.anyOf is not None
    assert isinstance(result.anyOf.value, list)
    assert len(result.anyOf.value) == 2


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

    assert result.allOf is not None
    assert isinstance(result.allOf.value, list)
    assert len(result.allOf.value) == 2

    # First element should be a Reference
    assert isinstance(result.allOf.value[0], Schema)  # In 3.1, nested schemas are Schema objects

    # Second element should be a Schema
    assert isinstance(result.allOf.value[1], schema.Schema)
    assert result.allOf.value[1].type is not None
    assert result.allOf.value[1].type.value == "object"


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

    assert result.oneOf is not None
    assert isinstance(result.oneOf.value, list)
    assert len(result.oneOf.value) == 3

    # First two elements should be References
    assert isinstance(result.oneOf.value[0], Schema)  # In 3.1, nested schemas are Schema objects
    assert isinstance(result.oneOf.value[1], Schema)  # In 3.1, nested schemas are Schema objects

    # Third element should be a Schema
    assert isinstance(result.oneOf.value[2], schema.Schema)
    assert result.oneOf.value[2].type is not None
    assert result.oneOf.value[2].type.value == "object"


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

    assert result.anyOf is not None
    assert isinstance(result.anyOf.value, list)
    assert len(result.anyOf.value) == 2

    # Both elements should be References
    assert isinstance(result.anyOf.value[0], Schema)  # In 3.1, nested schemas are Schema objects
    assert isinstance(result.anyOf.value[1], Schema)  # In 3.1, nested schemas are Schema objects


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

    assert result.additionalProperties is not None
    assert isinstance(
        result.additionalProperties.value, Schema
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

    assert result.additionalProperties is not None
    assert result.additionalProperties.value is False


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

    assert result.additionalProperties is not None
    assert isinstance(result.additionalProperties.value, schema.Schema)
    assert result.additionalProperties.value.type is not None
    assert result.additionalProperties.value.type.value == "string"


def test_build_with_nullable():
    """Test building Schema with nullable property."""
    yaml_content = textwrap.dedent(
        """
        type: string
        nullable: true
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = schema.build(root)
    assert isinstance(result, schema.Schema)

    assert result.nullable is not None
    assert result.nullable.value is True


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

    assert result.externalDocs is not None
    assert isinstance(result.externalDocs.value, ExternalDocumentation)
    assert result.externalDocs.value.url is not None
    assert result.externalDocs.value.url.value == "https://example.com/docs/user"


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
    assert result.minLength is not None
    assert result.minLength.value == "not-a-number"
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
