"""Tests for count_references function."""

from jentic.apitools.openapi.transformer.core.references import count_references


class TestCountReferences:
    """Tests for count_references function with refs_only=False."""

    def test_count_references_simple(self):
        """Test counting references in simple document."""
        doc = {
            "openapi": "3.1.0",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "contact": {"url": "https://example.com/contact"},
            },
            "externalDocs": {"url": "./docs.html"},
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

        total, local_refs, relative_refs, absolute_http_refs = count_references(doc)

        # total should include: contact.url (absolute), externalDocs.url (relative), $ref (local)
        assert total == 3
        assert local_refs == 1  # The fragment-only $ref
        assert relative_refs == 1  # The ./docs.html
        assert absolute_http_refs == 1  # The https:// URL

    def test_count_references_mixed_types(self):
        """Test counting various types of references."""
        doc = {
            "openapi": "3.0.3",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "contact": {"url": "/contact"},  # relative
                "license": {"url": "https://opensource.org/licenses/MIT"},  # absolute HTTP
            },
            "externalDocs": {"url": "./docs.html"},  # relative
            "components": {
                "schemas": {
                    "User": {"$ref": "#/components/schemas/Base"},  # local
                    "Item": {"$ref": "./schemas/item.json"},  # relative
                    "Remote": {
                        "$ref": "https://api.example.com/schemas/remote.json"
                    },  # absolute HTTP
                },
                "examples": {
                    "example1": {"externalValue": "../examples/test.json"}  # relative
                },
            },
        }

        total, local_refs, relative_refs, absolute_http_refs = count_references(doc)

        # total: /contact, license.url, externalDocs.url, 3 $refs, externalValue = 7
        assert total == 7
        assert local_refs == 1  # The fragment-only $ref
        assert (
            relative_refs == 4
        )  # /contact, ./docs.html, ./schemas/item.json, ../examples/test.json
        assert absolute_http_refs == 2  # license.url and Remote $ref

    def test_count_references_empty_document(self):
        """Test counting references in empty document."""
        doc = {}

        total, local_refs, relative_refs, absolute_http_refs = count_references(doc)

        assert total == 0
        assert local_refs == 0
        assert relative_refs == 0
        assert absolute_http_refs == 0

    def test_count_references_no_refs(self):
        """Test document with no references."""
        doc = {
            "openapi": "3.1.0",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "description": "A test API",
            },
            "paths": {},
        }

        total, local_refs, relative_refs, absolute_http_refs = count_references(doc)

        assert total == 0
        assert local_refs == 0
        assert relative_refs == 0
        assert absolute_http_refs == 0

    def test_count_references_only_local(self):
        """Test document with only local (fragment-only) references."""
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
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {"id": {"$ref": "#/components/schemas/Id"}},
                    }
                }
            },
        }

        total, local_refs, relative_refs, absolute_http_refs = count_references(doc)

        assert total == 2
        assert local_refs == 2
        assert relative_refs == 0
        assert absolute_http_refs == 0

    def test_count_references_oauth_urls(self):
        """Test counting OAuth and OpenID Connect URLs."""
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
                            }
                        },
                    },
                    "openid": {
                        "type": "openIdConnect",
                        "openIdConnectUrl": "https://auth.example.com/.well-known/openid-configuration",
                    },
                }
            },
        }

        total, local_refs, relative_refs, absolute_http_refs = count_references(doc)

        assert total == 4
        assert local_refs == 0
        assert relative_refs == 0
        assert absolute_http_refs == 4


class TestCountReferencesRefsOnly:
    """Tests for count_references function with refs_only=True."""

    def test_count_references_refs_only_simple(self):
        """Test counting only $ref fields."""
        doc = {
            "openapi": "3.1.0",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "contact": {"url": "https://example.com/contact"},  # Should NOT be counted
            },
            "externalDocs": {"url": "./docs.html"},  # Should NOT be counted
            "paths": {
                "/test": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/User"
                                        }  # Should be counted
                                    }
                                }
                            }
                        }
                    }
                }
            },
        }

        total, local_refs, relative_refs, absolute_http_refs = count_references(doc, refs_only=True)

        # Should only count the $ref
        assert total == 1
        assert local_refs == 1
        assert relative_refs == 0
        assert absolute_http_refs == 0

    def test_count_references_refs_only_mixed(self):
        """Test counting only $refs in document with mixed URL types."""
        doc = {
            "openapi": "3.0.3",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "contact": {"url": "/contact"},  # Should NOT be counted
                "license": {"url": "https://opensource.org/licenses/MIT"},  # Should NOT be counted
            },
            "externalDocs": {"url": "./docs.html"},  # Should NOT be counted
            "components": {
                "schemas": {
                    "User": {"$ref": "#/components/schemas/Base"},  # local - should be counted
                    "Item": {"$ref": "./schemas/item.json"},  # relative - should be counted
                    "Remote": {
                        "$ref": "https://api.example.com/schemas/remote.json"
                    },  # absolute HTTP - should be counted
                },
                "examples": {
                    "example1": {"externalValue": "../examples/test.json"}  # Should NOT be counted
                },
            },
        }

        total, local_refs, relative_refs, absolute_http_refs = count_references(doc, refs_only=True)

        # Should only count the 3 $refs
        assert total == 3
        assert local_refs == 1  # The fragment-only $ref
        assert relative_refs == 1  # ./schemas/item.json
        assert absolute_http_refs == 1  # Remote $ref

    def test_count_references_refs_only_no_refs(self):
        """Test document with no $refs but other URL fields."""
        doc = {
            "openapi": "3.1.0",
            "info": {
                "title": "Test",
                "version": "1.0.0",
                "contact": {"url": "./contact.html"},
                "license": {"url": "https://opensource.org/licenses/MIT"},
            },
            "externalDocs": {"url": "./docs.html"},
        }

        total, local_refs, relative_refs, absolute_http_refs = count_references(doc, refs_only=True)

        # No $refs, so all counts should be 0
        assert total == 0
        assert local_refs == 0
        assert relative_refs == 0
        assert absolute_http_refs == 0

    def test_count_references_refs_only_ignore_oauth(self):
        """Test that OAuth URLs are not counted with refs_only=True."""
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
                            }
                        },
                    }
                },
                "schemas": {
                    "User": {"$ref": "./user.json"}  # This should be counted
                },
            },
        }

        total, local_refs, relative_refs, absolute_http_refs = count_references(doc, refs_only=True)

        # Should only count the $ref, not the OAuth URLs
        assert total == 1
        assert local_refs == 0
        assert relative_refs == 1
        assert absolute_http_refs == 0

    def test_count_references_refs_only_all_types(self):
        """Test counting all types of $refs with refs_only=True."""
        doc = {
            "openapi": "3.1.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "components": {
                "schemas": {
                    "Local": {"$ref": "#/components/schemas/Base"},  # local
                    "Relative1": {"$ref": "./schemas/user.json"},  # relative
                    "Relative2": {"$ref": "../common/item.json"},  # relative
                    "RootRelative": {
                        "$ref": "/schemas/root.json"
                    },  # root-relative (still relative)
                    "AbsoluteHttp": {
                        "$ref": "https://api.example.com/schemas/remote.json"
                    },  # absolute HTTP
                    "AbsoluteHttps": {
                        "$ref": "https://api.example.com/schemas/other.json"
                    },  # absolute HTTPS
                }
            },
        }

        total, local_refs, relative_refs, absolute_http_refs = count_references(doc, refs_only=True)

        assert total == 6
        assert local_refs == 1  # #/components/schemas/Base
        assert relative_refs == 3  # ./schemas/user.json, ../common/item.json, /schemas/root.json
        assert absolute_http_refs == 2  # The two https:// $refs
