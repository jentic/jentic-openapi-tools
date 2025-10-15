"""Tests for URL finding functions."""

from jentic.apitools.openapi.transformer.core.references import (
    find_absolute_http_urls,
    find_relative_urls,
)


class TestFindAbsoluteHttpUrls:
    """Tests for find_absolute_http_urls function."""

    def test_find_absolute_http_urls_simple(self):
        """Test finding absolute HTTP/HTTPS URLs in simple document."""
        doc = {
            "openapi": "3.1.0",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "contact": {"url": "https://example.com/contact"},
                "license": {"url": "https://opensource.org/licenses/MIT"},
            },
            "externalDocs": {"url": "https://docs.example.com/api"},
        }

        absolute_urls = find_absolute_http_urls(doc)

        assert len(absolute_urls) == 3
        values = [url[2] for url in absolute_urls]
        assert "https://example.com/contact" in values
        assert "https://opensource.org/licenses/MIT" in values
        assert "https://docs.example.com/api" in values

    def test_find_absolute_http_urls_mixed(self):
        """Test finding absolute HTTP URLs while ignoring relative and fragment-only URLs."""
        doc = {
            "openapi": "3.0.3",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "contact": {
                    "url": "https://example.com/contact"  # absolute HTTP - should be found
                },
                "termsOfService": "http://example.com/terms",  # absolute HTTP - should be found
            },
            "externalDocs": {
                "url": "./docs/api.html"  # relative - should be ignored
            },
            "paths": {
                "/test": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/User"  # fragment-only - should be ignored
                                        }
                                    }
                                }
                            },
                            "404": {
                                "$ref": "./common.json#/NotFound"  # relative - should be ignored
                            },
                        }
                    }
                }
            },
            "components": {
                "examples": {
                    "example1": {
                        "externalValue": "https://api.example.com/examples/test.json"  # absolute HTTP - should be found
                    }
                }
            },
        }

        absolute_urls = find_absolute_http_urls(doc)

        # Should find 3 absolute HTTP URLs
        assert len(absolute_urls) == 3

        values = [url[2] for url in absolute_urls]
        assert "https://example.com/contact" in values
        assert "http://example.com/terms" in values
        assert "https://api.example.com/examples/test.json" in values

        # Should not include relative or fragment-only URLs
        assert "./docs/api.html" not in values
        assert "#/components/schemas/User" not in values
        assert "./common.json#/NotFound" not in values

    def test_find_absolute_http_urls_oauth(self):
        """Test finding absolute HTTP URLs in OAuth security schemes."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "components": {
                "securitySchemes": {
                    "oauth": {
                        "type": "oauth2",
                        "flows": {
                            "authorizationCode": {
                                "authorizationUrl": "https://auth.example.com/oauth/authorize",
                                "tokenUrl": "https://auth.example.com/oauth/token",
                                "refreshUrl": "https://auth.example.com/oauth/refresh",
                            },
                            "implicit": {
                                "authorizationUrl": "http://auth.example.com/oauth/implicit"
                            },
                        },
                    },
                    "openid": {
                        "type": "openIdConnect",
                        "openIdConnectUrl": "https://auth.example.com/.well-known/openid-configuration",
                    },
                }
            },
        }

        absolute_urls = find_absolute_http_urls(doc)

        assert len(absolute_urls) == 5
        values = [url[2] for url in absolute_urls]
        assert "https://auth.example.com/oauth/authorize" in values
        assert "https://auth.example.com/oauth/token" in values
        assert "https://auth.example.com/oauth/refresh" in values
        assert "http://auth.example.com/oauth/implicit" in values
        assert "https://auth.example.com/.well-known/openid-configuration" in values

    def test_find_absolute_http_urls_ignore_non_http(self):
        """Test that non-HTTP absolute URLs are ignored."""
        doc = {
            "openapi": "3.1.0",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "contact": {
                    "url": "https://example.com/contact"  # HTTP - should be found
                },
                "license": {
                    "url": "file:///usr/share/licenses/MIT"  # file:// - should be ignored
                },
            },
            "components": {
                "examples": {
                    "example1": {
                        "externalValue": "ftp://files.example.com/test.json"  # FTP - should be ignored
                    },
                    "example2": {
                        "externalValue": "mailto:support@example.com"  # mailto - should be ignored
                    },
                    "example3": {
                        "externalValue": "http://api.example.com/data.json"  # HTTP - should be found
                    },
                }
            },
        }

        absolute_urls = find_absolute_http_urls(doc)

        # Should only find HTTP/HTTPS URLs
        assert len(absolute_urls) == 2
        values = [url[2] for url in absolute_urls]
        assert "https://example.com/contact" in values
        assert "http://api.example.com/data.json" in values

        # Should not include non-HTTP schemes
        assert "file:///usr/share/licenses/MIT" not in values
        assert "ftp://files.example.com/test.json" not in values
        assert "mailto:support@example.com" not in values

    def test_find_absolute_http_urls_ignore_scheme_relative(self):
        """Test that scheme-relative URLs are ignored."""
        doc = {
            "openapi": "3.1.0",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "contact": {
                    "url": "https://example.com/contact"  # absolute HTTP - should be found
                },
                "termsOfService": "//cdn.example.com/terms.html",  # scheme-relative - should be ignored
            },
            "externalDocs": {
                "url": "//docs.example.com/api"  # scheme-relative - should be ignored
            },
        }

        absolute_urls = find_absolute_http_urls(doc)

        # Should only find the absolute HTTP URL, not scheme-relative ones
        assert len(absolute_urls) == 1
        assert absolute_urls[0][2] == "https://example.com/contact"

    def test_find_absolute_http_urls_empty_document(self):
        """Test with empty document."""
        doc = {}
        absolute_urls = find_absolute_http_urls(doc)
        assert len(absolute_urls) == 0

    def test_find_absolute_http_urls_no_absolute_urls(self):
        """Test document with no absolute HTTP URLs."""
        doc = {
            "openapi": "3.1.0",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "contact": {
                    "url": "./contact.html"  # relative
                },
            },
            "paths": {
                "/test": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/User"  # fragment-only
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
        }

        absolute_urls = find_absolute_http_urls(doc)
        assert len(absolute_urls) == 0

    def test_find_absolute_http_urls_nested_structures(self):
        """Test finding absolute HTTP URLs in deeply nested structures."""
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
                                                {
                                                    "type": "object",
                                                    "properties": {
                                                        "link": {"type": "string", "format": "uri"}
                                                    },
                                                }
                                            ]
                                        },
                                        "examples": {
                                            "nested_example": {
                                                "externalValue": "https://api.example.com/nested/test.json"
                                            }
                                        },
                                    }
                                }
                            }
                        },
                        "externalDocs": {"url": "http://docs.example.com/test-endpoint"},
                    }
                }
            },
        }

        absolute_urls = find_absolute_http_urls(doc)

        assert len(absolute_urls) == 2
        values = [url[2] for url in absolute_urls]
        assert "https://api.example.com/nested/test.json" in values
        assert "http://docs.example.com/test-endpoint" in values

    def test_find_absolute_http_urls_ignore_non_string_values(self):
        """Test that non-string values in URL fields are ignored."""
        doc = {
            "openapi": "3.1.0",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "contact": {
                    "url": "https://example.com/contact"  # valid string - should be found
                },
            },
            "externalDocs": {
                "url": 12345  # number instead of string - should be ignored
            },
            "components": {
                "examples": {
                    "example1": {
                        "externalValue": None  # None instead of string - should be ignored
                    },
                    "example2": {
                        "externalValue": [
                            "https://example.com/list"
                        ]  # array instead of string - should be ignored
                    },
                }
            },
        }

        absolute_urls = find_absolute_http_urls(doc)

        # Should only find the valid string URL
        assert len(absolute_urls) == 1
        assert absolute_urls[0][2] == "https://example.com/contact"


class TestFindRelativeUrls:
    """Tests for find_relative_urls function."""

    def test_find_relative_refs_simple(self):
        """Test finding relative $ref URLs in simple document."""
        doc = {
            "openapi": "3.1.0",
            "info": {"title": "Test", "version": "1.0.0"},
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

        relative_urls = find_relative_urls(doc)

        assert len(relative_urls) == 1
        path, key, value = relative_urls[0]
        assert key == "$ref"
        assert value == "./schemas.json#/User"
        assert path == (
            "paths",
            "/test",
            "get",
            "responses",
            "200",
            "content",
            "application/json",
            "schema",
            "$ref",
        )

    def test_find_various_url_types(self):
        """Test finding various types of relative URLs."""
        doc = {
            "openapi": "3.0.3",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "contact": {
                    "url": "/contact"  # root-relative
                },
            },
            "externalDocs": {
                "url": "docs/api.html"  # relative
            },
            "components": {
                "examples": {
                    "example1": {
                        "externalValue": "../examples/test.json"  # relative
                    }
                },
                "securitySchemes": {
                    "oauth": {
                        "type": "oauth2",
                        "flows": {
                            "authorizationCode": {
                                "authorizationUrl": "/oauth/auth",  # root-relative
                                "tokenUrl": "https://example.com/token",  # absolute - should be ignored
                            }
                        },
                    }
                },
            },
        }

        relative_urls = find_relative_urls(doc)

        # Should find 4 relative URLs (contact.url, externalDocs.url, externalValue, authorizationUrl)
        assert len(relative_urls) == 4

        values = [url[2] for url in relative_urls]
        assert "/contact" in values
        assert "docs/api.html" in values
        assert "../examples/test.json" in values
        assert "/oauth/auth" in values
        # Absolute URL should not be included
        assert "https://example.com/token" not in values

    def test_ignore_fragment_only_refs(self):
        """Test that fragment-only $ref URLs are ignored."""
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
                                            "$ref": "#/components/schemas/User"  # fragment-only
                                        }
                                    }
                                }
                            },
                            "404": {
                                "$ref": "./common.json#/NotFound"  # relative
                            },
                        }
                    }
                }
            },
        }

        relative_urls = find_relative_urls(doc)

        assert len(relative_urls) == 1
        _, key, value = relative_urls[0]
        assert key == "$ref"
        assert value == "./common.json#/NotFound"

    def test_empty_document(self):
        """Test with empty document."""
        doc = {}
        relative_urls = find_relative_urls(doc)
        assert len(relative_urls) == 0

    def test_no_relative_urls(self):
        """Test document with no relative URLs."""
        doc = {
            "openapi": "3.1.0",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "contact": {
                    "url": "https://example.com/contact"  # absolute
                },
            },
            "paths": {
                "/test": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/User"  # fragment-only
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
        assert len(relative_urls) == 0
