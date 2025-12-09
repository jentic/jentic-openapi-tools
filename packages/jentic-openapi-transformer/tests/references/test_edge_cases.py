"""Tests for edge cases and error conditions in reference handling."""

from jentic.apitools.openapi.transformer.core.references import (
    RewriteOptions,
    find_relative_urls,
    rewrite_urls_inplace,
)


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_nested_arrays_and_objects(self):
        """Test finding URLs in deeply nested structures."""
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
                                        "schema": {
                                            "oneOf": [
                                                {"$ref": "./schema1.json#/Type1"},
                                                {"$ref": "./schema2.json#/Type2"},
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
        }

        relative_urls = find_relative_urls(doc)
        assert len(relative_urls) == 2

        values = [url[2] for url in relative_urls]
        assert "./schema1.json#/Type1" in values
        assert "./schema2.json#/Type2" in values

    def test_url_like_strings_in_descriptions(self):
        """Test that URL-like strings in descriptions are not processed."""
        doc = {
            "openapi": "3.1.0",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "description": "See ./docs/api.md for more info",  # Not a URL field
            },
            "paths": {
                "/test": {
                    "get": {
                        "summary": "Check ../examples/test.json",  # Not a URL field
                        "externalDocs": {
                            "url": "./real-docs.html"  # This IS a URL field
                        },
                    }
                }
            },
        }

        relative_urls = find_relative_urls(doc)

        # Should only find the real URL field, not the description strings
        assert len(relative_urls) == 1
        assert relative_urls[0][2] == "./real-docs.html"

    def test_empty_and_whitespace_urls(self):
        """Test handling of empty and whitespace-only URL values."""
        doc = {
            "openapi": "3.1.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "externalDocs": {
                "url": ""  # Empty string
            },
            "components": {
                "examples": {
                    "example1": {
                        "externalValue": "   "  # Whitespace only
                    }
                }
            },
        }

        relative_urls = find_relative_urls(doc)

        # Empty and whitespace-only URLs should be ignored
        assert len(relative_urls) == 0

    def test_non_string_values_in_url_fields(self):
        """Test that non-string values in URL fields are ignored."""
        doc = {
            "openapi": "3.1.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "externalDocs": {
                "url": 123  # Number instead of string
            },
            "components": {
                "examples": {
                    "example1": {
                        "externalValue": None  # None instead of string
                    }
                }
            },
        }

        relative_urls = find_relative_urls(doc)
        assert len(relative_urls) == 0

        # rewrite_urls_inplace should not crash and should not change anything
        opts = RewriteOptions(base_url="https://example.com/")
        changed = rewrite_urls_inplace(doc, opts)
        assert changed == 0


class TestEdgeCasesRefsOnly:
    """Tests for edge cases and error conditions with refs_only=True."""

    def test_nested_arrays_and_objects_refs_only(self):
        """Test finding URLs in deeply nested structures with refs_only=True."""
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
                                        "schema": {
                                            "oneOf": [
                                                {"$ref": "./schema1.json#/Type1"},
                                                {"$ref": "./schema2.json#/Type2"},
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
        }

        relative_urls = find_relative_urls(doc, refs_only=True)
        assert len(relative_urls) == 2

        values = [url[2] for url in relative_urls]
        assert "./schema1.json#/Type1" in values
        assert "./schema2.json#/Type2" in values

    def test_url_like_strings_in_descriptions_refs_only(self):
        """Test that only $ref fields are processed with refs_only=True."""
        doc = {
            "openapi": "3.1.0",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "description": "See ./docs/api.md for more info",  # Not a URL field
            },
            "paths": {
                "/test": {
                    "get": {
                        "summary": "Check ../examples/test.json",  # Not a URL field
                        "externalDocs": {
                            "url": "./real-docs.html"  # This is a URL field but NOT $ref
                        },
                    }
                }
            },
        }

        relative_urls = find_relative_urls(doc, refs_only=True)

        # Should NOT find any URLs since there are no $ref fields
        assert len(relative_urls) == 0

    def test_refs_and_other_urls_refs_only(self):
        """Test that with refs_only=True, only $ref fields are found, not other URL fields."""
        doc = {
            "openapi": "3.1.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "externalDocs": {
                "url": "./docs.html"  # URL field but NOT $ref
            },
            "components": {
                "schemas": {
                    "User": {
                        "$ref": "./user-schema.json#/User"  # This is $ref
                    }
                },
                "examples": {
                    "example1": {
                        "externalValue": "./example.json"  # URL field but NOT $ref
                    }
                },
            },
        }

        relative_urls = find_relative_urls(doc, refs_only=True)

        # Should only find the $ref field
        assert len(relative_urls) == 1
        assert relative_urls[0][1] == "$ref"
        assert relative_urls[0][2] == "./user-schema.json#/User"

    def test_empty_and_whitespace_urls_refs_only(self):
        """Test handling of empty and whitespace-only $ref values with refs_only=True."""
        doc = {
            "openapi": "3.1.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "components": {
                "schemas": {
                    "Empty": {
                        "$ref": ""  # Empty string
                    },
                    "Whitespace": {
                        "$ref": "   "  # Whitespace only
                    },
                }
            },
        }

        relative_urls = find_relative_urls(doc, refs_only=True)

        # Empty and whitespace-only $refs should be ignored
        assert len(relative_urls) == 0

    def test_non_string_values_in_ref_fields_refs_only(self):
        """Test that non-string values in $ref fields are ignored with refs_only=True."""
        doc = {
            "openapi": "3.1.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "components": {
                "schemas": {
                    "Number": {
                        "$ref": 123  # Number instead of string
                    },
                    "NullRef": {
                        "$ref": None  # None instead of string
                    },
                }
            },
        }

        relative_urls = find_relative_urls(doc, refs_only=True)
        assert len(relative_urls) == 0

        # rewrite_urls_inplace should not crash and should not change anything
        opts = RewriteOptions(base_url="https://example.com/", refs_only=True)
        changed = rewrite_urls_inplace(doc, opts)
        assert changed == 0

    def test_rewrite_urls_refs_only(self):
        """Test that rewrite_urls_inplace with refs_only=True only rewrites $ref fields."""
        doc = {
            "openapi": "3.1.0",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "contact": {"url": "./contact.html"},  # Should NOT be rewritten
            },
            "externalDocs": {"url": "./docs.html"},  # Should NOT be rewritten
            "components": {
                "schemas": {
                    "User": {
                        "$ref": "./user.json#/User"  # Should be rewritten
                    }
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

        # Should only change the $ref field
        assert changed == 1
        assert (
            doc["components"]["schemas"]["User"]["$ref"]
            == "https://api.example.com/user.json#/User"
        )

        # Other URL fields should remain unchanged
        assert doc["info"]["contact"]["url"] == "./contact.html"
        assert doc["externalDocs"]["url"] == "./docs.html"
        assert doc["components"]["examples"]["example1"]["externalValue"] == "./example.json"
