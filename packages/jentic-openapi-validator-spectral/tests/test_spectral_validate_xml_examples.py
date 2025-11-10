"""Tests for Spectral validation with XML example filtering."""

import json
from pathlib import Path

import pytest
from lsprotocol.types import DiagnosticSeverity

from jentic.apitools.openapi.validator.backends.spectral import SpectralValidatorBackend


# Helper functions for test assertions
def get_error_diagnostics(result):
    """Extract error-level diagnostics from validation result."""
    return [d for d in result.diagnostics if d.severity == DiagnosticSeverity.Error]


def has_errors_in_path(diagnostics, path_substring):
    """Check if any diagnostic has the path substring."""
    return any(d.data and path_substring in str(d.data.get("path", "")) for d in diagnostics)


@pytest.fixture
def xml_filtering_ruleset_path() -> Path:
    """Path to the XML-filtering ruleset."""
    # This points to the actual spectral.mjs ruleset we created
    return (
        Path(__file__).parent.parent
        / "src/jentic/apitools/openapi/validator/backends/spectral/rulesets/spectral.mjs"
    )


@pytest.fixture
def spectral_validator_with_xml_filtering(
    xml_filtering_ruleset_path: Path,
) -> SpectralValidatorBackend:
    """A SpectralValidator instance with XML filtering ruleset."""
    return SpectralValidatorBackend(ruleset_path=str(xml_filtering_ruleset_path))


@pytest.fixture
def openapi_with_xml_and_json_examples(tmp_path: Path) -> Path:
    """Create an OpenAPI document with both XML and JSON examples."""
    openapi_doc = {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                # XML media type with invalid example (should be skipped)
                                "application/xml": {
                                    "schema": {"type": "array", "items": {"type": "string"}},
                                    "examples": {
                                        "invalid": {
                                            "summary": "Invalid XML example",
                                            "value": {
                                                "not": "an array"
                                            },  # Invalid but should be skipped
                                        }
                                    },
                                },
                                # JSON media type with invalid example (should be caught)
                                "application/json": {
                                    "schema": {"type": "array", "items": {"type": "string"}},
                                    "examples": {
                                        "invalid": {
                                            "summary": "Invalid JSON example",
                                            "value": {
                                                "not": "an array"
                                            },  # Invalid and should be caught
                                        }
                                    },
                                },
                            },
                        }
                    },
                }
            }
        },
    }

    file_path = tmp_path / "openapi_xml_json.json"
    file_path.write_text(json.dumps(openapi_doc, indent=2))
    return file_path


@pytest.fixture
def openapi_with_xml_parameter(tmp_path: Path) -> Path:
    """Create an OpenAPI document with a parameter that has xml property in schema."""
    openapi_doc = {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "parameters": [
                        {
                            "name": "filter",
                            "in": "query",
                            "schema": {
                                "type": "object",
                                "xml": {"name": "Filter"},  # Has xml property
                            },
                            "example": {"invalid": "structure"},  # Invalid but should be skipped
                        }
                    ],
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
    }

    file_path = tmp_path / "openapi_xml_parameter.json"
    file_path.write_text(json.dumps(openapi_doc, indent=2))
    return file_path


@pytest.fixture
def openapi_with_json_parameter(tmp_path: Path) -> Path:
    """Create an OpenAPI document with a parameter without xml property."""
    openapi_doc = {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "parameters": [
                        {
                            "name": "filter",
                            "in": "query",
                            "schema": {
                                "type": "object",
                                "properties": {"name": {"type": "string"}},
                            },
                            "example": ["invalid"],  # Invalid and should be caught
                        }
                    ],
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
    }

    file_path = tmp_path / "openapi_json_parameter.json"
    file_path.write_text(json.dumps(openapi_doc, indent=2))
    return file_path


@pytest.fixture
def openapi_with_xml_header(tmp_path: Path) -> Path:
    """Create an OpenAPI document with a header that has xml property in schema."""
    openapi_doc = {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "Success",
                            "headers": {
                                "X-Custom-Header": {
                                    "schema": {
                                        "type": "string",
                                        "xml": {"attribute": True},  # Has xml property
                                    },
                                    "example": 123,  # Invalid but should be skipped
                                }
                            },
                        }
                    },
                }
            }
        },
    }

    file_path = tmp_path / "openapi_xml_header.json"
    file_path.write_text(json.dumps(openapi_doc, indent=2))
    return file_path


@pytest.fixture
def openapi_with_json_header(tmp_path: Path) -> Path:
    """Create an OpenAPI document with a header without xml property."""
    openapi_doc = {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "Success",
                            "headers": {
                                "X-Rate-Limit": {
                                    "schema": {
                                        "type": "integer",
                                    },
                                    "example": "not-an-integer",  # Invalid and should be caught
                                }
                            },
                        }
                    },
                }
            }
        },
    }

    file_path = tmp_path / "openapi_json_header.json"
    file_path.write_text(json.dumps(openapi_doc, indent=2))
    return file_path


@pytest.fixture
def openapi_with_plus_xml_media_type(tmp_path: Path) -> Path:
    """Create an OpenAPI document with +xml media type (e.g., application/atom+xml)."""
    openapi_doc = {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                # +xml media type with invalid example (should be skipped)
                                "application/atom+xml": {
                                    "schema": {"type": "object"},
                                    "examples": {
                                        "invalid": {
                                            "value": [
                                                "not",
                                                "an",
                                                "object",
                                            ],  # Invalid but should be skipped
                                        }
                                    },
                                },
                            },
                        }
                    },
                }
            }
        },
    }

    file_path = tmp_path / "openapi_plus_xml.json"
    file_path.write_text(json.dumps(openapi_doc, indent=2))
    return file_path


@pytest.mark.requires_spectral_cli
class TestXMLExampleFiltering:
    """Integration tests for XML example filtering in Spectral validation."""

    def test_skips_xml_media_type_validation(
        self, spectral_validator_with_xml_filtering, openapi_with_xml_and_json_examples
    ):
        """Test that XML media type examples are skipped but JSON examples are validated."""
        result = spectral_validator_with_xml_filtering.validate(
            openapi_with_xml_and_json_examples.as_uri()
        )

        # Should have errors because JSON example is invalid
        assert not result.valid

        errors = get_error_diagnostics(result)
        assert errors, "Expected validation errors for invalid JSON example"

        # The error should be in the application/json path, not application/xml
        assert has_errors_in_path(errors, "application/json"), (
            "Expected error in application/json path"
        )
        assert not has_errors_in_path(errors, "application/xml"), (
            "Should not have errors for application/xml (XML validation skipped)"
        )

    def test_skips_parameter_with_xml_schema(
        self, spectral_validator_with_xml_filtering, openapi_with_xml_parameter
    ):
        """Test that parameters with xml property in schema are skipped."""
        result = spectral_validator_with_xml_filtering.validate(openapi_with_xml_parameter.as_uri())

        errors = get_error_diagnostics(result)
        assert not has_errors_in_path(errors, "parameters"), (
            "Should not validate parameters with xml schema property"
        )

    def test_validates_parameter_without_xml_schema(
        self, spectral_validator_with_xml_filtering, openapi_with_json_parameter
    ):
        """Test that parameters without xml property are validated."""
        result = spectral_validator_with_xml_filtering.validate(
            openapi_with_json_parameter.as_uri()
        )

        assert not result.valid, "Expected validation to fail for invalid parameter example"

        errors = get_error_diagnostics(result)
        assert has_errors_in_path(errors, "parameters"), (
            "Should validate parameters without xml schema property"
        )

    def test_skips_header_with_xml_schema(
        self, spectral_validator_with_xml_filtering, openapi_with_xml_header
    ):
        """Test that headers with xml property in schema are skipped."""
        result = spectral_validator_with_xml_filtering.validate(openapi_with_xml_header.as_uri())

        errors = get_error_diagnostics(result)
        assert not has_errors_in_path(errors, "headers"), (
            "Should not validate headers with xml schema property"
        )

    def test_validates_header_without_xml_schema(
        self, spectral_validator_with_xml_filtering, openapi_with_json_header
    ):
        """Test that headers without xml property are validated."""
        result = spectral_validator_with_xml_filtering.validate(openapi_with_json_header.as_uri())

        assert not result.valid, "Expected validation to fail for invalid header example"

        errors = get_error_diagnostics(result)
        assert has_errors_in_path(errors, "headers"), (
            "Should validate headers without xml schema property"
        )

    def test_skips_plus_xml_media_types(
        self, spectral_validator_with_xml_filtering, openapi_with_plus_xml_media_type
    ):
        """Test that +xml media types (like application/atom+xml) are skipped."""
        result = spectral_validator_with_xml_filtering.validate(
            openapi_with_plus_xml_media_type.as_uri()
        )

        errors = get_error_diagnostics(result)
        assert not has_errors_in_path(errors, "+xml"), (
            "Should not validate +xml media types (e.g., application/atom+xml)"
        )
