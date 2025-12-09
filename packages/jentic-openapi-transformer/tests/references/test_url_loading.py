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


class TestWithFileUrlsRefsOnly:
    """Tests using file:// URLs to load documents with refs_only=True."""

    def test_load_and_process_from_file_url_refs_only(self, references_fixtures_dir):
        """Test loading and processing only $refs from file:// URL."""
        spec_file = references_fixtures_dir / "root-simple.json"
        spec_uri = spec_file.as_uri()
        spec_text = load_uri(spec_uri, 300, 300)

        spec_doc = OpenAPIParser().parse(spec_text)

        # Add some non-$ref URL fields
        spec_doc["info"]["contact"] = {"url": "./contact.html"}

        # Find relative URLs with and without refs_only
        relative_urls_all = find_relative_urls(spec_doc, refs_only=False)
        relative_urls_refs = find_relative_urls(spec_doc, refs_only=True)

        assert len(relative_urls_refs) <= len(relative_urls_all)

        # Rewrite only $refs
        opts = RewriteOptions(base_url=spec_uri, refs_only=True)
        changed = rewrite_urls_inplace(spec_doc, opts)
        assert changed == len(relative_urls_refs)

        # Verify non-$ref fields were not changed
        assert spec_doc["info"]["contact"]["url"] == "./contact.html"

    def test_load_complex_document_from_file_refs_only(self, references_fixtures_dir):
        """Test loading and processing only $refs from complex document."""
        spec_file = references_fixtures_dir / "root-complex.json"
        spec_uri = spec_file.as_uri()
        spec_text = load_uri(spec_uri, 300, 300)

        spec_doc = OpenAPIParser().parse(spec_text)

        # Find relative $refs only
        relative_urls_refs = find_relative_urls(spec_doc, refs_only=True)
        refs_values = [url[2] for url in relative_urls_refs]

        # Should only find $refs, not server URLs
        for value in refs_values:
            assert not value.startswith("/api/"), (
                "Server URLs should not be included with refs_only=True"
            )

        # Rewrite only $refs
        opts = RewriteOptions(base_url=spec_uri, refs_only=True)
        rewrite_urls_inplace(spec_doc, opts)

        # Server URL should still be relative
        assert spec_doc["servers"][1]["url"] == "/api/v2", (
            "Server URL should not be changed with refs_only=True"
        )


class TestWithHttpUrlsRefsOnly:
    """Tests using HTTP URLs to load documents with refs_only=True."""

    def test_load_and_process_from_http_url_refs_only(self, http_server):
        """Test loading and processing only $refs from HTTP URL."""
        spec_url = urljoin(http_server.base_url, "root-simple.json")
        spec_text = load_uri(spec_url, 300, 300)

        spec_doc = OpenAPIParser().parse(spec_text)

        # Add some non-$ref URL fields
        spec_doc["externalDocs"] = {"url": "./docs.html"}

        # Find relative $refs only
        relative_refs = find_relative_urls(spec_doc, refs_only=True)
        assert len(relative_refs) > 0

        # Verify all found items are $refs
        for _, key, _ in relative_refs:
            assert key == "$ref"

        # Rewrite only $refs to be absolute HTTP URLs
        opts = RewriteOptions(base_url=spec_url, refs_only=True)
        changed = rewrite_urls_inplace(spec_doc, opts)
        assert changed == len(relative_refs)

        # Check that $ref was converted to absolute HTTP URL
        schema_ref = spec_doc["paths"]["/users"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]["$ref"]
        expected_ref = urljoin(spec_url, "schemas.json#/User")
        assert schema_ref == expected_ref

        # externalDocs.url should remain unchanged
        assert spec_doc["externalDocs"]["url"] == "./docs.html"

    def test_load_complex_document_from_http_refs_only(self, http_server):
        """Test loading complex document from HTTP server with refs_only=True."""
        spec_url = urljoin(http_server.base_url, "root-complex.json")
        spec_text = load_uri(spec_url, 300, 300)

        spec_doc = OpenAPIParser().parse(spec_text)

        # Process only $refs
        relative_refs = find_relative_urls(spec_doc, refs_only=True)
        assert len(relative_refs) > 0

        opts = RewriteOptions(base_url=spec_url, refs_only=True)
        changed = rewrite_urls_inplace(spec_doc, opts)
        assert changed == len(relative_refs)

        # Root-relative server URL should NOT become absolute with refs_only=True
        assert spec_doc["servers"][1]["url"] == "/api/v2"

    def test_retarget_http_refs_only(self, http_server):
        """Test retargeting only HTTP $refs, not other URL fields."""
        spec_url = urljoin(http_server.base_url, "root-simple.json")
        spec_text = load_uri(spec_url, 300, 300)

        spec_doc = OpenAPIParser().parse(spec_text)

        # Add some absolute URLs in both $ref and non-$ref fields
        spec_doc["info"]["termsOfService"] = urljoin(http_server.base_url, "terms.html")
        spec_doc["info"]["contact"] = {"url": urljoin(http_server.base_url, "contact.html")}

        # First absolutize all $refs
        opts1 = RewriteOptions(base_url=spec_url, refs_only=True)
        rewrite_urls_inplace(spec_doc, opts1)

        # Now add an absolute $ref
        spec_doc["components"] = {
            "schemas": {"Test": {"$ref": urljoin(http_server.base_url, "test-schema.json")}}
        }

        # Retarget only $refs from HTTP server to HTTPS production
        opts2 = RewriteOptions(
            base_url="https://api.production.com/v1/",
            original_base_url=http_server.base_url + "/",
            include_absolute_urls=True,
            refs_only=True,
        )
        changed = rewrite_urls_inplace(spec_doc, opts2)

        # Should have changed $refs only
        assert changed > 0

        # Check that non-$ref URL fields were NOT retargeted
        assert spec_doc["info"]["termsOfService"] == urljoin(http_server.base_url, "terms.html")
        assert spec_doc["info"]["contact"]["url"] == urljoin(http_server.base_url, "contact.html")

        # Check that $ref was retargeted
        assert (
            spec_doc["components"]["schemas"]["Test"]["$ref"]
            == "https://api.production.com/v1/test-schema.json"
        )
