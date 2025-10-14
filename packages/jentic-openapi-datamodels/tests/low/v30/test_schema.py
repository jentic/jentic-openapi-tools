"""Tests for Schema model."""

from jentic.apitools.openapi.datamodels.low.v30.discriminator import Discriminator
from jentic.apitools.openapi.datamodels.low.v30.external_documentation import ExternalDocumentation
from jentic.apitools.openapi.datamodels.low.v30.reference import Reference
from jentic.apitools.openapi.datamodels.low.v30.schema import Schema
from jentic.apitools.openapi.datamodels.low.v30.xml import XML


class TestSchema:
    """Tests for Schema model."""

    def test_init_empty(self):
        """Test creating empty schema."""
        schema = Schema()
        assert len(schema) == 0

    def test_init_simple(self):
        """Test creating simple schema."""
        schema = Schema({"type": "string", "minLength": 1})
        assert schema.type == "string"
        assert schema.min_length == 1

    def test_string_properties(self):
        """Test string validation properties."""
        schema = Schema({"type": "string", "minLength": 5, "maxLength": 100, "pattern": "^[a-z]+$"})
        assert schema.type == "string"
        assert schema.min_length == 5
        assert schema.max_length == 100
        assert schema.pattern == "^[a-z]+$"

    def test_numeric_properties(self):
        """Test numeric validation properties."""
        schema = Schema(
            {
                "type": "number",
                "minimum": 0,
                "maximum": 100,
                "exclusiveMinimum": 0,
                "exclusiveMaximum": 100,
                "multipleOf": 5,
            }
        )
        assert schema.type == "number"
        assert schema.minimum == 0
        assert schema.maximum == 100
        assert schema.exclusive_minimum == 0
        assert schema.exclusive_maximum == 100
        assert schema.multiple_of == 5

    def test_array_properties(self):
        """Test array validation properties."""
        schema = Schema(
            {
                "type": "array",
                "minItems": 1,
                "maxItems": 10,
                "uniqueItems": True,
                "items": {"type": "string"},
            }
        )
        assert schema.type == "array"
        assert schema.min_items == 1
        assert schema.max_items == 10
        assert schema.unique_items is True
        assert isinstance(schema.items_, Schema)
        assert schema.items_.type == "string"

    def test_object_properties(self):
        """Test object validation properties."""
        schema = Schema(
            {
                "type": "object",
                "required": ["name"],
                "minProperties": 1,
                "maxProperties": 10,
                "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            }
        )
        assert schema.type == "object"
        assert schema.required == ["name"]
        assert schema.min_properties == 1
        assert schema.max_properties == 10
        assert "name" in schema.properties
        assert "age" in schema.properties
        assert isinstance(schema.properties["name"], Schema)
        assert schema.properties["name"].type == "string"

    def test_all_of_composition(self):
        """Test allOf composition."""
        schema = Schema(
            {"allOf": [{"type": "object"}, {"properties": {"name": {"type": "string"}}}]}
        )
        assert len(schema.all_of) == 2
        assert all(isinstance(s, Schema) for s in schema.all_of)

    def test_one_of_composition(self):
        """Test oneOf composition."""
        schema = Schema({"oneOf": [{"type": "string"}, {"type": "number"}]})
        assert len(schema.one_of) == 2
        assert all(isinstance(s, Schema) for s in schema.one_of)

    def test_any_of_composition(self):
        """Test anyOf composition."""
        schema = Schema({"anyOf": [{"type": "string"}, {"type": "null"}]})
        assert len(schema.any_of) == 2
        assert all(isinstance(s, Schema) for s in schema.any_of)

    def test_not_composition(self):
        """Test not composition."""
        schema = Schema({"not": {"type": "null"}})
        assert isinstance(schema.not_, Schema)
        assert schema.not_.type == "null"

    def test_reference_in_composition(self):
        """Test reference in composition."""
        schema = Schema({"allOf": [{"$ref": "#/components/schemas/Base"}]})
        assert len(schema.all_of) == 1
        assert isinstance(schema.all_of[0], Reference)
        assert schema.all_of[0].ref == "#/components/schemas/Base"

    def test_additional_properties_bool(self):
        """Test additionalProperties as boolean."""
        schema = Schema({"additionalProperties": False})
        assert schema.additional_properties is False

    def test_additional_properties_schema(self):
        """Test additionalProperties as schema."""
        schema = Schema({"additionalProperties": {"type": "string"}})
        assert isinstance(schema.additional_properties, Schema)
        assert schema.additional_properties.type == "string"

    def test_discriminator(self):
        """Test discriminator marshaling."""
        schema = Schema({"discriminator": {"propertyName": "petType"}})
        assert isinstance(schema.discriminator, Discriminator)
        assert schema.discriminator.property_name == "petType"

    def test_xml(self):
        """Test XML marshaling."""
        schema = Schema({"xml": {"name": "animal"}})
        assert isinstance(schema.xml, XML)
        assert schema.xml.name == "animal"

    def test_external_docs(self):
        """Test external documentation marshaling."""
        schema = Schema({"externalDocs": {"url": "https://example.com"}})
        assert isinstance(schema.external_docs, ExternalDocumentation)
        assert schema.external_docs.url == "https://example.com"

    def test_openapi_extensions(self):
        """Test OpenAPI-specific extensions."""
        schema = Schema(
            {
                "type": "string",
                "nullable": True,
                "readOnly": True,
                "writeOnly": False,
                "deprecated": True,
                "example": "example value",
            }
        )
        assert schema.nullable is True
        assert schema.read_only is True
        assert schema.write_only is False
        assert schema.deprecated is True
        assert schema.example == "example value"

    def test_nested_schema_recursion(self):
        """Test deeply nested schemas are marshaled recursively."""
        schema = Schema(
            {
                "type": "object",
                "properties": {
                    "person": {
                        "type": "object",
                        "properties": {
                            "address": {
                                "type": "object",
                                "properties": {"street": {"type": "string"}},
                            }
                        },
                    }
                },
            }
        )
        assert isinstance(schema.properties["person"], Schema)
        assert isinstance(schema.properties["person"].properties["address"], Schema)
        assert isinstance(
            schema.properties["person"].properties["address"].properties["street"], Schema
        )

    def test_to_mapping(self):
        """Test converting schema back to mapping."""
        data = {"type": "object", "properties": {"name": {"type": "string"}}}
        schema = Schema(data)
        result = schema.to_mapping()
        assert result["type"] == "object"
        assert "name" in result["properties"]
        assert result["properties"]["name"]["type"] == "string"

    def test_supports_extensions(self):
        """Test that Schema supports specification extensions."""
        schema = Schema({"type": "string", "x-custom": "value"})
        extensions = schema.get_extensions()
        assert extensions == {"x-custom": "value"}

    def test_property_setters(self):
        """Test property setters."""
        schema = Schema()
        schema.type = "string"
        schema.min_length = 5
        schema.max_length = 100

        assert schema.type == "string"
        assert schema.min_length == 5
        assert schema.max_length == 100
        assert schema["type"] == "string"
        assert schema["minLength"] == 5
        assert schema["maxLength"] == 100

    def test_property_setters_none(self):
        """Test setting properties to None removes them."""
        schema = Schema({"type": "string", "minLength": 5})
        assert "minLength" in schema

        schema.min_length = None
        assert "minLength" not in schema

    def test_enum(self):
        """Test enum property."""
        schema = Schema({"enum": ["red", "green", "blue"]})
        assert schema.enum == ["red", "green", "blue"]

    def test_default(self):
        """Test default property."""
        schema = Schema({"type": "string", "default": "default value"})
        assert schema.default == "default value"

    def test_title_description_format(self):
        """Test metadata properties."""
        schema = Schema(
            {"title": "User Name", "description": "The user's full name", "format": "email"}
        )
        assert schema.title == "User Name"
        assert schema.description == "The user's full name"
        assert schema.format == "email"

    def test_unmarshal_with_sequence_types(self):
        """Test that unmarshaling works with different sequence types."""
        # Simulate ruamel.yaml CommentedSeq behavior with a list
        schema = Schema({"allOf": [{"type": "object"}, {"type": "string"}]})
        assert len(schema.all_of) == 2
        assert all(isinstance(s, Schema) for s in schema.all_of)


class TestSchemaInheritance:
    """Tests for Schema subclassing."""

    def test_subclass_unmarshal_uses_subclass(self):
        """Test that nested schemas use the subclass type."""

        class CustomSchema(Schema):
            def custom_method(self):
                return "custom"

        schema = CustomSchema({"properties": {"name": {"type": "string"}}})

        # Nested schemas should be CustomSchema instances
        assert isinstance(schema.properties["name"], CustomSchema)
        assert schema.properties["name"].custom_method() == "custom"
