"""Tests for rewrite_urls_inplace function."""

from jentic.apitools.openapi.transformer.core.references import (
    RewriteOptions,
    rewrite_urls_inplace,
)


class TestRewriteUrlsInplace:
    """Tests for rewrite_urls_inplace function."""

    def test_rewrite_relative_urls_to_absolute(self):
        """Test rewriting relative URLs to absolute."""
        doc = {
            "openapi": "3.1.0",
            "info": {"title": "Test", "version": "1.0.0", "contact": {"url": "contact.html"}},
            "paths": {
                "/test": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {"schema": {"$ref": "./schemas.json#/User"}}
                                }
                            }
                        }
                    }
                }
            },
        }

        opts = RewriteOptions(base_url="https://api.example.com/v1/")
        changed = rewrite_urls_inplace(doc, opts)

        assert changed == 2
        assert doc["info"]["contact"]["url"] == "https://api.example.com/v1/contact.html"
        assert (
            doc["paths"]["/test"]["get"]["responses"]["200"]["content"]["application/json"][
                "schema"
            ]["$ref"]
            == "https://api.example.com/v1/schemas.json#/User"
        )

    def test_rewrite_root_relative_urls(self):
        """Test rewriting root-relative URLs."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0", "contact": {"url": "/api/contact"}},
            "servers": [{"url": "/api/v1"}],
        }

        opts = RewriteOptions(base_url="https://api.example.com/")
        changed = rewrite_urls_inplace(doc, opts)

        assert changed == 2
        assert doc["info"]["contact"]["url"] == "https://api.example.com/api/contact"
        assert doc["servers"][0]["url"] == "https://api.example.com/api/v1"

    def test_retarget_absolute_urls(self):
        """Test retargeting absolute URLs with prefix replacement."""
        doc = {
            "openapi": "3.1.0",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "contact": {"url": "https://old.example.com/contact"},
            },
            "components": {
                "examples": {
                    "example1": {"externalValue": "https://old.example.com/examples/test.json"}
                }
            },
        }

        opts = RewriteOptions(
            base_url="https://new.example.com/",
            original_base_url="https://old.example.com/",
            include_absolute_urls=True,
        )
        changed = rewrite_urls_inplace(doc, opts)

        assert changed == 2
        assert doc["info"]["contact"]["url"] == "https://new.example.com/contact"
        assert (
            doc["components"]["examples"]["example1"]["externalValue"]
            == "https://new.example.com/examples/test.json"
        )

    def test_preserve_fragment_only_refs(self):
        """Test that fragment-only $ref URLs are preserved."""
        doc = {
            "openapi": "3.1.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/User"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
        }

        opts = RewriteOptions(base_url="https://api.example.com/")
        changed = rewrite_urls_inplace(doc, opts)

        assert changed == 0
        assert (
            doc["paths"]["/test"]["get"]["responses"]["200"]["content"]["application/json"][
                "schema"
            ]["$ref"]
            == "#/components/schemas/User"
        )

    def test_no_changes_when_no_relative_urls(self):
        """Test that no changes are made when there are no relative URLs."""
        doc = {
            "openapi": "3.1.0",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "contact": {"url": "https://example.com/contact"},
            },
        }

        opts = RewriteOptions(base_url="https://api.example.com/")
        changed = rewrite_urls_inplace(doc, opts)

        assert changed == 0
        assert doc["info"]["contact"]["url"] == "https://example.com/contact"
