"""Tests for Spectral validation with XML example filtering."""

import json
from pathlib import Path

import pytest

from jentic.apitools.openapi.validator.backends.spectral import SpectralValidatorBackend


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
        spec_uri = openapi_with_xml_and_json_examples.as_uri()
        result = spectral_validator_with_xml_filtering.validate(spec_uri)

        # Should have errors because JSON example is invalid
        assert result.valid is False

        # Check that the error is for the JSON example, not XML
        errors = [d for d in result.diagnostics if d.severity == 1]  # 1 = Error in LSP
        assert len(errors) > 0

        # The error should be in the application/json path
        json_errors = [
            e for e in errors if e.data and "application/json" in str(e.data.get("path", ""))
        ]
        assert len(json_errors) > 0

        # Should NOT have errors for application/xml
        xml_errors = [
            e for e in errors if e.data and "application/xml" in str(e.data.get("path", ""))
        ]
        assert len(xml_errors) == 0

    def test_skips_parameter_with_xml_schema(
        self, spectral_validator_with_xml_filtering, openapi_with_xml_parameter
    ):
        """Test that parameters with xml property in schema are skipped."""
        spec_uri = openapi_with_xml_parameter.as_uri()
        result = spectral_validator_with_xml_filtering.validate(spec_uri)

        # Should not have errors for the parameter example (it's XML-related)
        errors = [d for d in result.diagnostics if d.severity == 1]  # 1 = Error
        parameter_errors = [
            e
            for e in errors
            if e.data
            and "parameters" in str(e.data.get("path", ""))
            and "example" in str(e.data.get("path", ""))
        ]
        assert len(parameter_errors) == 0

    def test_validates_parameter_without_xml_schema(
        self, spectral_validator_with_xml_filtering, openapi_with_json_parameter
    ):
        """Test that parameters without xml property are validated."""
        spec_uri = openapi_with_json_parameter.as_uri()
        result = spectral_validator_with_xml_filtering.validate(spec_uri)

        # Should have errors because the parameter example is invalid
        assert result.valid is False

        errors = [d for d in result.diagnostics if d.severity == 1]  # 1 = Error
        parameter_errors = [
            e for e in errors if e.data and "parameters" in str(e.data.get("path", ""))
        ]
        assert len(parameter_errors) > 0

    def test_skips_header_with_xml_schema(
        self, spectral_validator_with_xml_filtering, openapi_with_xml_header
    ):
        """Test that headers with xml property in schema are skipped."""
        spec_uri = openapi_with_xml_header.as_uri()
        result = spectral_validator_with_xml_filtering.validate(spec_uri)

        # Should not have errors for the header example (it's XML-related)
        errors = [d for d in result.diagnostics if d.severity == 1]  # 1 = Error
        header_errors = [
            e
            for e in errors
            if e.data
            and "headers" in str(e.data.get("path", ""))
            and "example" in str(e.data.get("path", ""))
        ]
        assert len(header_errors) == 0

    def test_validates_header_without_xml_schema(
        self, spectral_validator_with_xml_filtering, openapi_with_json_header
    ):
        """Test that headers without xml property are validated."""
        spec_uri = openapi_with_json_header.as_uri()
        result = spectral_validator_with_xml_filtering.validate(spec_uri)

        # Should have errors because the header example is invalid
        assert result.valid is False

        errors = [d for d in result.diagnostics if d.severity == 1]  # 1 = Error
        header_errors = [e for e in errors if e.data and "headers" in str(e.data.get("path", ""))]
        assert len(header_errors) > 0

    def test_skips_plus_xml_media_types(
        self, spectral_validator_with_xml_filtering, openapi_with_plus_xml_media_type
    ):
        """Test that +xml media types (like application/atom+xml) are skipped."""
        spec_uri = openapi_with_plus_xml_media_type.as_uri()
        result = spectral_validator_with_xml_filtering.validate(spec_uri)

        # Should not have errors for the +xml media type
        errors = [d for d in result.diagnostics if d.severity == 1]  # 1 = Error
        xml_errors = [e for e in errors if e.data and "+xml" in str(e.data.get("path", ""))]
        assert len(xml_errors) == 0
