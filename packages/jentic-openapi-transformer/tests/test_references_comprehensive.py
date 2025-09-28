"""Comprehensive tests for references.py functionality."""

import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urljoin

import pytest
from jentic_openapi_parser import OpenAPIParser
from jentic_openapi_transformer import (
    find_relative_urls,
    rewrite_urls_inplace,
    set_or_replace_top_level_json_id,
    RewriteOptions,
    find_absolute_http_urls,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "openapi" / "references_comprehensive"


class HTTPTestServer:
    """Simple HTTP server for testing HTTP URL loading."""

    def __init__(self, port: int = 0):
        self.port = port
        self.server = None
        self.thread = None
        self.base_url = None

    def start(self):
        """Start the HTTP server in a background thread."""
        # Change to fixtures directory to serve files
        fixtures_dir = FIXTURES_DIR
        fixtures_dir.mkdir(parents=True, exist_ok=True)

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(fixtures_dir), **kwargs)

            def log_message(self, format, *args):
                # Suppress log messages
                pass

        self.server = HTTPServer(("localhost", self.port), Handler)
        self.port = self.server.server_port
        self.base_url = f"http://localhost:{self.port}"

        def run_server():
            assert self.server
            self.server.serve_forever()

        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()

        # Give server time to start
        time.sleep(0.1)

    def stop(self):
        """Stop the HTTP server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=1)


@pytest.fixture(scope="module")
def http_server():
    """Fixture providing an HTTP server for testing."""
    server = HTTPTestServer()
    server.start()
    yield server
    server.stop()


class TestSetOrReplaceTopLevelJsonId:
    """Tests for set_or_replace_top_level_json_id function."""

    def test_create_id_openapi_31(self):
        """Test creating $id on OpenAPI 3.1 document."""
        doc = {"openapi": "3.1.0", "info": {"title": "Test", "version": "1.0.0"}}

        set_or_replace_top_level_json_id(doc, "https://example.com/api.json")

        # Should modify the document and return success indicator
        assert doc["$id"] == "https://example.com/api.json"

    def test_update_existing_id_openapi_31(self):
        """Test updating existing $id on OpenAPI 3.1 document."""
        doc = {
            "openapi": "3.1.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "$id": "https://old.example.com/api.json",
        }

        set_or_replace_top_level_json_id(doc, "https://new.example.com/api.json")

        assert doc["$id"] == "https://new.example.com/api.json"

    def test_no_id_on_openapi_30_by_default(self):
        """Test that $id is not added to OpenAPI 3.0 by default."""
        doc = {"openapi": "3.0.3", "info": {"title": "Test", "version": "1.0.0"}}

        set_or_replace_top_level_json_id(doc, "https://example.com/api.json")

        assert "$id" not in doc

    def test_force_id_on_openapi_30(self):
        """Test forcing $id on OpenAPI 3.0 document."""
        doc = {"openapi": "3.0.3", "info": {"title": "Test", "version": "1.0.0"}}

        set_or_replace_top_level_json_id(doc, "https://example.com/api.json", forse_on_30=True)

        assert doc["$id"] == "https://example.com/api.json"

    def test_non_dict_document(self):
        """Test with non-dictionary document."""
        doc = ["not", "a", "dict"]

        set_or_replace_top_level_json_id(doc, "https://example.com/api.json")

        # Should not modify non-dict documents
        assert doc == ["not", "a", "dict"]


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


class TestWithFileUrls:
    """Tests using file:// URLs to load documents."""

    def test_load_and_process_from_file_url(self):
        """Test loading and processing a document from file:// URL."""
        from jentic_openapi_parser.uri import load_uri

        spec_file = FIXTURES_DIR / "simple.json"
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

        # Set document ID
        set_or_replace_top_level_json_id(spec_doc, spec_uri)
        assert spec_doc["$id"] == spec_uri

    def test_load_complex_document_from_file(self):
        """Test loading and processing complex document from file."""
        from jentic_openapi_parser.uri import load_uri

        spec_file = FIXTURES_DIR / "complex.json"
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
        from jentic_openapi_parser.uri import load_uri

        spec_url = urljoin(http_server.base_url, "simple.json")
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
        from jentic_openapi_parser.uri import load_uri

        spec_url = urljoin(http_server.base_url, "complex.json")
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
        from jentic_openapi_parser.uri import load_uri

        spec_url = urljoin(http_server.base_url, "simple.json")
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
