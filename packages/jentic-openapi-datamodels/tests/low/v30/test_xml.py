"""Tests for XML model."""

from jentic.apitools.openapi.datamodels.low.v30.xml import XML


class TestXML:
    """Tests for XML model."""

    def test_init_empty(self):
        """Test creating empty XML object."""
        xml = XML()
        assert len(xml) == 0

    def test_init_with_name(self):
        """Test creating XML with name."""
        xml = XML({"name": "animal"})
        assert xml.name == "animal"

    def test_init_with_namespace(self):
        """Test creating XML with namespace."""
        xml = XML({"name": "Pet", "namespace": "http://example.com/schema/pet"})
        assert xml.name == "Pet"
        assert xml.namespace == "http://example.com/schema/pet"

    def test_init_with_prefix(self):
        """Test creating XML with prefix."""
        xml = XML({"name": "Pet", "namespace": "http://example.com/schema", "prefix": "sample"})
        assert xml.name == "Pet"
        assert xml.namespace == "http://example.com/schema"
        assert xml.prefix == "sample"

    def test_init_with_attribute(self):
        """Test creating XML with attribute flag."""
        xml = XML({"name": "id", "attribute": True})
        assert xml.name == "id"
        assert xml.attribute is True

    def test_init_with_wrapped(self):
        """Test creating XML with wrapped flag."""
        xml = XML({"name": "pets", "wrapped": True})
        assert xml.name == "pets"
        assert xml.wrapped is True

    def test_init_full_example(self):
        """Test creating XML with all properties."""
        xml = XML(
            {
                "name": "animals",
                "namespace": "http://example.com/schema/sample",
                "prefix": "sample",
                "attribute": False,
                "wrapped": True,
            }
        )
        assert xml.name == "animals"
        assert xml.namespace == "http://example.com/schema/sample"
        assert xml.prefix == "sample"
        assert xml.attribute is False
        assert xml.wrapped is True

    def test_name_setter(self):
        """Test setting name."""
        xml = XML()
        xml.name = "Pet"
        assert xml.name == "Pet"
        assert xml["name"] == "Pet"

    def test_name_setter_none(self):
        """Test setting name to None removes it."""
        xml = XML({"name": "Pet"})
        xml.name = None
        assert "name" not in xml

    def test_namespace_setter(self):
        """Test setting namespace."""
        xml = XML()
        xml.namespace = "http://example.com"
        assert xml.namespace == "http://example.com"

    def test_prefix_setter(self):
        """Test setting prefix."""
        xml = XML()
        xml.prefix = "ex"
        assert xml.prefix == "ex"

    def test_attribute_setter(self):
        """Test setting attribute flag."""
        xml = XML()
        xml.attribute = True
        assert xml.attribute is True

    def test_wrapped_setter(self):
        """Test setting wrapped flag."""
        xml = XML()
        xml.wrapped = True
        assert xml.wrapped is True

    def test_property_setters_none(self):
        """Test setting properties to None removes them."""
        xml = XML(
            {
                "name": "Pet",
                "namespace": "http://example.com",
                "prefix": "ex",
                "attribute": True,
                "wrapped": True,
            }
        )

        xml.name = None
        assert "name" not in xml

        xml.namespace = None
        assert "namespace" not in xml

        xml.prefix = None
        assert "prefix" not in xml

        xml.attribute = None
        assert "attribute" not in xml

        xml.wrapped = None
        assert "wrapped" not in xml

    def test_supports_extensions(self):
        """Test that XML supports specification extensions."""
        xml = XML({"name": "Pet", "x-custom": "value"})
        extensions = xml.get_extensions()
        assert extensions == {"x-custom": "value"}

    def test_to_mapping(self):
        """Test converting to mapping."""
        xml = XML({"name": "animals", "namespace": "http://example.com/schema", "wrapped": True})
        result = xml.to_mapping()
        assert result == {
            "name": "animals",
            "namespace": "http://example.com/schema",
            "wrapped": True,
        }

    def test_from_mapping(self):
        """Test creating from mapping."""
        data = {"name": "Pet", "attribute": True}
        xml = XML.from_mapping(data)
        assert xml.name == "Pet"
        assert xml.attribute is True

    def test_array_wrapping_example(self):
        """Test XML configuration for wrapped arrays."""
        # Example: wrapping an array of animals in an <animals> element
        xml = XML({"name": "animals", "wrapped": True})
        assert xml.name == "animals"
        assert xml.wrapped is True

    def test_attribute_serialization_example(self):
        """Test XML configuration for attribute serialization."""
        # Example: serializing a property as XML attribute instead of element
        xml = XML({"name": "id", "attribute": True})
        assert xml.name == "id"
        assert xml.attribute is True
