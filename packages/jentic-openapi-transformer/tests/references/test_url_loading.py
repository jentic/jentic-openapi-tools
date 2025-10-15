"""Tests for loading and processing OpenAPI documents from file:// and HTTP URLs."""

from urllib.parse import urljoin

from jentic.apitools.openapi.parser.core import OpenAPIParser, load_uri
from jentic.apitools.openapi.transformer.core.references import (
    RewriteOptions,
    find_relative_urls,
    rewrite_urls_inplace,
)


class TestWithFileUrls:
    """Tests using file:// URLs to load documents."""

    def test_load_and_process_from_file_url(self, references_fixtures_dir):
        """Test loading and processing a document from file:// URL."""
        spec_file = references_fixtures_dir / "root-simple.json"
        spec_uri = spec_file.as_uri()
        spec_text = load_uri(spec_uri, 300, 300)

        spec_doc = OpenAPIParser().parse(spec_text)

        # Find relative URLs
        relative_urls = find_relative_urls(spec_doc)
        assert len(relative_urls) > 0

        # Rewrite URLs
        opts = RewriteOptions(base_url=spec_uri)
        changed = rewrite_urls_inplace(spec_doc, opts)
        assert changed > 0

    def test_load_complex_document_from_file(self, references_fixtures_dir):
        """Test loading and processing complex document from file."""
        spec_file = references_fixtures_dir / "root-complex.json"
        spec_uri = spec_file.as_uri()
        spec_text = load_uri(spec_uri, 300, 300)

        spec_doc = OpenAPIParser().parse(spec_text)

        # Should find several relative URLs
        relative_urls = find_relative_urls(spec_doc)
        relative_values = [url[2] for url in relative_urls]

        assert "/api/v2" in relative_values  # root-relative server URL
        assert "schemas/item.json#/Item" in relative_values  # relative $ref


class TestWithHttpUrls:
    """Tests using HTTP URLs to load documents."""

    def test_load_and_process_from_http_url(self, http_server):
        """Test loading and processing a document from HTTP URL."""
        spec_url = urljoin(http_server.base_url, "root-simple.json")
        spec_text = load_uri(spec_url, 300, 300)

        spec_doc = OpenAPIParser().parse(spec_text)

        # Find relative URLs
        relative_urls = find_relative_urls(spec_doc)
        assert len(relative_urls) > 0

        # Rewrite URLs to be absolute HTTP URLs
        opts = RewriteOptions(base_url=spec_url)
        changed = rewrite_urls_inplace(spec_doc, opts)
        assert changed > 0

        # Check that relative URLs were converted to absolute HTTP URLs
        schema_ref = spec_doc["paths"]["/users"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]["$ref"]
        expected_ref = urljoin(spec_url, "schemas.json#/User")
        assert schema_ref == expected_ref

    def test_load_complex_document_from_http(self, http_server):
        """Test loading complex document from HTTP server."""
        spec_url = urljoin(http_server.base_url, "root-complex.json")
        spec_text = load_uri(spec_url, 300, 300)

        spec_doc = OpenAPIParser().parse(spec_text)

        # Process the document
        relative_urls = find_relative_urls(spec_doc)
        assert len(relative_urls) > 0

        opts = RewriteOptions(base_url=spec_url)
        changed = rewrite_urls_inplace(spec_doc, opts)
        assert changed > 0

        # Root-relative server URL should become absolute
        assert spec_doc["servers"][1]["url"] == urljoin(spec_url, "/api/v2")

    def test_retarget_http_urls(self, http_server):
        """Test retargeting HTTP URLs from one base to another."""
        spec_url = urljoin(http_server.base_url, "root-simple.json")
        spec_text = load_uri(spec_url, 300, 300)

        spec_doc = OpenAPIParser().parse(spec_text)

        # Add some absolute URLs that match the original base
        spec_doc["info"]["termsOfService"] = urljoin(http_server.base_url, "terms.html")

        # Retarget from HTTP server to HTTPS production
        opts = RewriteOptions(
            base_url="https://api.production.com/v1/",
            original_base_url=http_server.base_url + "/",
            include_absolute_urls=True,
        )
        changed = rewrite_urls_inplace(spec_doc, opts)

        # Should have changed URLs
        assert changed > 0

        # Check that absolute URL was retargeted
        assert spec_doc["info"]["termsOfService"] == "https://api.production.com/v1/terms.html"
