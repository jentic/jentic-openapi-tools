"""Shared test fixtures for jentic-openapi-traverse."""

import pytest


@pytest.fixture
def simple_openapi_doc():
    """A minimal OpenAPI 3.1.0 document structure."""
    return {"openapi": "3.1.0", "info": {"title": "Test API", "version": "1.0.0"}, "paths": {}}


@pytest.fixture
def nested_openapi_doc():
    """A more complex OpenAPI document with nested paths and operations."""
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Complex API",
            "version": "2.0.0",
            "description": "An API with nested structures",
        },
        "paths": {
            "/users": {
                "get": {
                    "summary": "List users",
                    "parameters": [
                        {"name": "limit", "in": "query"},
                        {"name": "offset", "in": "query"},
                    ],
                    "responses": {
                        "200": {"description": "Success"},
                        "400": {"description": "Bad Request"},
                    },
                },
                "post": {
                    "summary": "Create user",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "email": {"type": "string"},
                                    },
                                }
                            }
                        },
                    },
                },
            },
            "/users/{id}": {
                "get": {
                    "summary": "Get user by ID",
                    "parameters": [{"name": "id", "in": "path", "required": True}],
                }
            },
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {"id": {"type": "integer"}, "name": {"type": "string"}},
                }
            }
        },
    }
