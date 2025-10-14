"""Tests for Tag model."""

from jentic.apitools.openapi.datamodels.low.v30.external_documentation import ExternalDocumentation
from jentic.apitools.openapi.datamodels.low.v30.tag import Tag


class TestTag:
    """Tests for Tag model."""

    def test_init_empty(self):
        """Test creating empty tag."""
        tag = Tag()
        assert len(tag) == 0

    def test_init_with_name(self):
        """Test creating tag with name."""
        tag = Tag({"name": "pet"})
        assert tag.name == "pet"

    def test_init_with_description(self):
        """Test creating tag with description."""
        tag = Tag({"name": "pet", "description": "Everything about your Pets"})
        assert tag.name == "pet"
        assert tag.description == "Everything about your Pets"

    def test_init_with_external_docs(self):
        """Test creating tag with external documentation."""
        tag = Tag(
            {
                "name": "store",
                "description": "Access to Petstore orders",
                "externalDocs": {"description": "Find out more", "url": "http://example.com"},
            }
        )
        assert tag.name == "store"
        assert isinstance(tag.external_docs, ExternalDocumentation)
        assert tag.external_docs.url == "http://example.com"

    def test_external_docs_marshaling(self):
        """Test that externalDocs are marshaled to ExternalDocumentation."""
        tag = Tag({"name": "user", "externalDocs": {"url": "https://example.com/docs"}})
        assert isinstance(tag.external_docs, ExternalDocumentation)
        assert tag.external_docs.url == "https://example.com/docs"

    def test_external_docs_no_double_wrapping(self):
        """Test that ExternalDocumentation instances aren't double-wrapped."""
        docs = ExternalDocumentation({"url": "https://example.com"})
        tag = Tag({"name": "tag", "externalDocs": docs})
        assert tag.external_docs is docs

    def test_name_setter(self):
        """Test setting name."""
        tag = Tag()
        tag.name = "pet"
        assert tag.name == "pet"
        assert tag["name"] == "pet"

    def test_name_setter_none(self):
        """Test setting name to None removes it."""
        tag = Tag({"name": "pet"})
        tag.name = None
        assert "name" not in tag

    def test_description_setter(self):
        """Test setting description."""
        tag = Tag({"name": "pet"})
        tag.description = "Pet operations"
        assert tag.description == "Pet operations"

    def test_description_setter_none(self):
        """Test setting description to None removes it."""
        tag = Tag({"name": "pet", "description": "Pets"})
        tag.description = None
        assert "description" not in tag

    def test_external_docs_setter(self):
        """Test setting external docs."""
        tag = Tag({"name": "pet"})
        docs = ExternalDocumentation({"url": "https://example.com"})
        tag.external_docs = docs
        assert tag.external_docs is docs

    def test_external_docs_setter_none(self):
        """Test setting external docs to None removes them."""
        tag = Tag({"name": "pet", "externalDocs": {"url": "https://example.com"}})
        tag.external_docs = None
        assert "externalDocs" not in tag

    def test_supports_extensions(self):
        """Test that Tag supports specification extensions."""
        tag = Tag({"name": "pet", "x-custom": "value"})
        extensions = tag.get_extensions()
        assert extensions == {"x-custom": "value"}

    def test_to_mapping(self):
        """Test converting to mapping."""
        tag = Tag(
            {
                "name": "store",
                "description": "Store operations",
                "externalDocs": {"url": "https://example.com"},
            }
        )
        result = tag.to_mapping()
        assert result["name"] == "store"
        assert result["description"] == "Store operations"
        assert result["externalDocs"]["url"] == "https://example.com"

    def test_from_mapping(self):
        """Test creating from mapping."""
        data = {"name": "user", "description": "User operations"}
        tag = Tag.from_mapping(data)
        assert tag.name == "user"
        assert tag.description == "User operations"
