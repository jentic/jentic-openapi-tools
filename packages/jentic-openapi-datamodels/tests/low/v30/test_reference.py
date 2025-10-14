"""Tests for Reference model."""

from jentic.apitools.openapi.datamodels.low.v30.reference import Reference


class TestReference:
    """Tests for Reference model."""

    def test_init_empty(self):
        """Test creating empty reference."""
        ref = Reference()
        assert len(ref) == 0
        assert ref.ref is None

    def test_init_with_ref(self):
        """Test creating reference with $ref field."""
        ref = Reference({"$ref": "#/components/schemas/Pet"})
        assert ref.ref == "#/components/schemas/Pet"
        assert ref["$ref"] == "#/components/schemas/Pet"

    def test_internal_reference(self):
        """Test internal reference to components."""
        ref = Reference({"$ref": "#/components/schemas/User"})
        assert ref.ref == "#/components/schemas/User"

    def test_external_url_reference(self):
        """Test external URL reference."""
        ref = Reference({"$ref": "https://example.com/schemas/Pet.json"})
        assert ref.ref == "https://example.com/schemas/Pet.json"

    def test_relative_file_reference(self):
        """Test relative file reference."""
        ref = Reference({"$ref": "./schemas/Pet.yaml#/Pet"})
        assert ref.ref == "./schemas/Pet.yaml#/Pet"

    def test_ref_property_setter(self):
        """Test setting ref property."""
        ref = Reference()
        ref.ref = "#/components/schemas/Dog"
        assert ref.ref == "#/components/schemas/Dog"
        assert ref["$ref"] == "#/components/schemas/Dog"

    def test_ref_property_setter_none(self):
        """Test setting ref to None removes it."""
        ref = Reference({"$ref": "#/components/schemas/Cat"})
        assert "$ref" in ref

        ref.ref = None
        assert "$ref" not in ref
        assert ref.ref is None

    def test_dict_access(self):
        """Test dictionary-style access to $ref."""
        ref = Reference({"$ref": "#/components/schemas/Bird"})
        assert ref["$ref"] == "#/components/schemas/Bird"

    def test_does_not_support_extensions(self):
        """Test that Reference does not support specification extensions."""
        ref = Reference({"$ref": "#/components/schemas/Pet", "x-custom": "value"})
        extensions = ref.get_extensions()
        # In OpenAPI 3.0.x, Reference objects don't support extensions
        # So x-* fields are treated as regular fields
        assert extensions == {}

    def test_to_mapping(self):
        """Test converting reference to mapping."""
        ref = Reference({"$ref": "#/components/schemas/Pet"})
        result = ref.to_mapping()
        assert result == {"$ref": "#/components/schemas/Pet"}

    def test_from_mapping(self):
        """Test creating from mapping."""
        data = {"$ref": "#/components/parameters/limit"}
        ref = Reference.from_mapping(data)
        assert ref.ref == "#/components/parameters/limit"

    def test_repr(self):
        """Test string representation."""
        ref = Reference({"$ref": "#/components/schemas/Pet"})
        repr_str = repr(ref)
        assert "Reference" in repr_str
        assert "1 field" in repr_str
