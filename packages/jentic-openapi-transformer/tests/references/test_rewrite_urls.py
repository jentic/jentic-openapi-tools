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


class TestRewriteUrlsInplaceRefsOnly:
    """Tests for rewrite_urls_inplace function with refs_only=True."""

    def test_rewrite_only_refs_to_absolute(self):
        """Test rewriting only $ref fields to absolute, not other URL fields."""
        doc = {
            "openapi": "3.1.0",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "contact": {"url": "contact.html"},  # Should NOT be rewritten
            },
            "externalDocs": {"url": "./docs.html"},  # Should NOT be rewritten
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

        opts = RewriteOptions(base_url="https://api.example.com/v1/", refs_only=True)
        changed = rewrite_urls_inplace(doc, opts)

        # Should only change the $ref field
        assert changed == 1
        assert (
            doc["paths"]["/test"]["get"]["responses"]["200"]["content"]["application/json"][
                "schema"
            ]["$ref"]
            == "https://api.example.com/v1/schemas.json#/User"
        )

        # Other URL fields should remain unchanged
        assert doc["info"]["contact"]["url"] == "contact.html"
        assert doc["externalDocs"]["url"] == "./docs.html"

    def test_rewrite_multiple_refs_ignore_other_urls(self):
        """Test rewriting multiple $refs while ignoring other URL fields."""
        doc = {
            "openapi": "3.0.3",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "contact": {"url": "/api/contact"},  # Should NOT be rewritten
            },
            "servers": [{"url": "/api/v1"}],  # Should NOT be rewritten
            "components": {
                "schemas": {
                    "User": {
                        "$ref": "./schemas/user.json"  # Should be rewritten
                    },
                    "Item": {
                        "$ref": "../common/item.json"  # Should be rewritten
                    },
                },
                "examples": {
                    "example1": {
                        "externalValue": "./example.json"  # Should NOT be rewritten
                    }
                },
            },
        }

        opts = RewriteOptions(base_url="https://api.example.com/", refs_only=True)
        changed = rewrite_urls_inplace(doc, opts)

        # Should only change the 2 $ref fields
        assert changed == 2
        assert (
            doc["components"]["schemas"]["User"]["$ref"]
            == "https://api.example.com/schemas/user.json"
        )
        assert (
            doc["components"]["schemas"]["Item"]["$ref"]
            == "https://api.example.com/common/item.json"
        )

        # Other URL fields should remain unchanged
        assert doc["info"]["contact"]["url"] == "/api/contact"
        assert doc["servers"][0]["url"] == "/api/v1"
        assert doc["components"]["examples"]["example1"]["externalValue"] == "./example.json"

    def test_retarget_only_absolute_refs(self):
        """Test retargeting only absolute $ref URLs with refs_only=True."""
        doc = {
            "openapi": "3.1.0",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "contact": {"url": "https://old.example.com/contact"},  # Should NOT be retargeted
            },
            "components": {
                "schemas": {
                    "User": {
                        "$ref": "https://old.example.com/schemas/user.json"  # Should be retargeted
                    }
                },
                "examples": {
                    "example1": {
                        "externalValue": "https://old.example.com/examples/test.json"  # Should NOT be retargeted
                    }
                },
            },
        }

        opts = RewriteOptions(
            base_url="https://new.example.com/",
            original_base_url="https://old.example.com/",
            include_absolute_urls=True,
            refs_only=True,
        )
        changed = rewrite_urls_inplace(doc, opts)

        # Should only change the $ref field
        assert changed == 1
        assert (
            doc["components"]["schemas"]["User"]["$ref"]
            == "https://new.example.com/schemas/user.json"
        )

        # Other URL fields should remain unchanged
        assert doc["info"]["contact"]["url"] == "https://old.example.com/contact"
        assert (
            doc["components"]["examples"]["example1"]["externalValue"]
            == "https://old.example.com/examples/test.json"
        )

    def test_preserve_fragment_only_refs_with_refs_only(self):
        """Test that fragment-only $refs are preserved with refs_only=True."""
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

        opts = RewriteOptions(base_url="https://api.example.com/", refs_only=True)
        changed = rewrite_urls_inplace(doc, opts)

        assert changed == 0
        assert (
            doc["paths"]["/test"]["get"]["responses"]["200"]["content"]["application/json"][
                "schema"
            ]["$ref"]
            == "#/components/schemas/User"
        )

    def test_no_changes_when_no_refs(self):
        """Test that no changes are made when there are no $ref fields with refs_only=True."""
        doc = {
            "openapi": "3.1.0",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "contact": {"url": "./contact.html"},
            },
            "externalDocs": {"url": "docs/api.html"},
        }

        opts = RewriteOptions(base_url="https://api.example.com/", refs_only=True)
        changed = rewrite_urls_inplace(doc, opts)

        # No $refs, so nothing should change
        assert changed == 0
        assert doc["info"]["contact"]["url"] == "./contact.html"
        assert doc["externalDocs"]["url"] == "docs/api.html"

    def test_mixed_refs_and_urls(self):
        """Test document with both $refs and other URL fields, only $refs should be rewritten."""
        doc = {
            "openapi": "3.1.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0",
                "contact": {"url": "./contact"},
                "license": {"url": "../license.txt"},
            },
            "externalDocs": {"url": "/docs"},
            "servers": [{"url": "https://api.example.com/v1"}],
            "components": {
                "schemas": {
                    "User": {"$ref": "./user.json"},
                    "Item": {"$ref": "./item.json#/Item"},
                }
            },
        }

        opts = RewriteOptions(base_url="https://new-api.example.com/api/", refs_only=True)
        changed = rewrite_urls_inplace(doc, opts)

        # Should change only the 2 $refs
        assert changed == 2

        # Verify $refs were rewritten
        assert (
            doc["components"]["schemas"]["User"]["$ref"]
            == "https://new-api.example.com/api/user.json"
        )
        assert (
            doc["components"]["schemas"]["Item"]["$ref"]
            == "https://new-api.example.com/api/item.json#/Item"
        )

        # Verify other URL fields were NOT rewritten
        assert doc["info"]["contact"]["url"] == "./contact"
        assert doc["info"]["license"]["url"] == "../license.txt"
        assert doc["externalDocs"]["url"] == "/docs"
        assert doc["servers"][0]["url"] == "https://api.example.com/v1"
