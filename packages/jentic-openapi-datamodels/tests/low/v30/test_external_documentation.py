"""Tests for ExternalDocumentation model."""

from jentic.apitools.openapi.datamodels.low.v30.external_documentation import ExternalDocumentation


class TestExternalDocumentation:
    """Tests for ExternalDocumentation model."""

    def test_init_empty(self):
        """Test creating empty external documentation."""
        docs = ExternalDocumentation()
        assert len(docs) == 0

    def test_init_with_url(self):
        """Test creating external documentation with URL."""
        docs = ExternalDocumentation({"url": "https://example.com/docs"})
        assert docs.url == "https://example.com/docs"

    def test_init_with_description(self):
        """Test creating external documentation with description."""
        docs = ExternalDocumentation(
            {"description": "Find more info here", "url": "https://example.com/docs"}
        )
        assert docs.description == "Find more info here"
        assert docs.url == "https://example.com/docs"

    def test_url_setter(self):
        """Test setting URL."""
        docs = ExternalDocumentation()
        docs.url = "https://example.com/api"
        assert docs.url == "https://example.com/api"
        assert docs["url"] == "https://example.com/api"

    def test_url_setter_none(self):
        """Test setting URL to None removes it."""
        docs = ExternalDocumentation({"url": "https://example.com"})
        docs.url = None
        assert "url" not in docs

    def test_description_setter(self):
        """Test setting description."""
        docs = ExternalDocumentation({"url": "https://example.com"})
        docs.description = "API Documentation"
        assert docs.description == "API Documentation"

    def test_description_setter_none(self):
        """Test setting description to None removes it."""
        docs = ExternalDocumentation({"description": "Docs", "url": "https://example.com"})
        docs.description = None
        assert "description" not in docs

    def test_supports_extensions(self):
        """Test that ExternalDocumentation supports specification extensions."""
        docs = ExternalDocumentation({"url": "https://example.com", "x-custom": "value"})
        extensions = docs.get_extensions()
        assert extensions == {"x-custom": "value"}

    def test_to_mapping(self):
        """Test converting to mapping."""
        docs = ExternalDocumentation({"description": "More info", "url": "https://example.com"})
        result = docs.to_mapping()
        assert result == {"description": "More info", "url": "https://example.com"}

    def test_from_mapping(self):
        """Test creating from mapping."""
        data = {"description": "User Guide", "url": "https://docs.example.com"}
        docs = ExternalDocumentation.from_mapping(data)
        assert docs.description == "User Guide"
        assert docs.url == "https://docs.example.com"
