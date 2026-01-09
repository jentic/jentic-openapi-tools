"""Tests for OpenAPISpecValidatorBackend."""

from jentic.apitools.openapi.validator.core import OpenAPIValidator


def test_openapi_spec_backend_discovery():
    """Test that the openapi-spec backend can be discovered via entry points."""
    validator = OpenAPIValidator(backends=["openapi-spec"])
    assert len(validator.backends) == 1

    backend_names = [type(b).__name__ for b in validator.backends]
    assert "OpenAPISpecValidatorBackend" in backend_names


def test_validator_with_valid_string(validator, valid_openapi_string):
    """Test validation with a valid OpenAPI document string."""
    result = validator.validate(valid_openapi_string)
    assert result.valid is True
    assert len(result.diagnostics) == 0


def test_validator_with_invalid_string(validator, invalid_openapi_string):
    """Test validation with an invalid OpenAPI document string (missing paths)."""
    result = validator.validate(invalid_openapi_string)
    assert result.valid is False
    assert len(result.diagnostics) > 0


def test_validator_with_valid_dict(validator, valid_openapi_dict):
    """Test validation with a valid OpenAPI document dictionary."""
    result = validator.validate(valid_openapi_dict)
    assert result.valid is True
    assert len(result.diagnostics) == 0


def test_validator_with_invalid_dict(validator, invalid_openapi_dict):
    """Test validation with an invalid OpenAPI document dictionary."""
    result = validator.validate(invalid_openapi_dict)
    assert result.valid is False
    assert len(result.diagnostics) > 0


def test_validator_ok():
    """Test validation of a valid OpenAPI document with correct version type."""
    val = OpenAPIValidator(["openapi-spec"])
    res = val.validate('{"openapi":"3.1.0","info":{"title":"ok","version":"1"}, "paths": {}}')
    assert res.valid is True


def test_validator_failure():
    """Test validation fails when version is a number instead of string."""
    val = OpenAPIValidator(["openapi-spec"])
    res = val.validate('{"openapi":"3.1.0","info":{"title":"ok","version":1}}')
    assert res.valid is False


def test_openapi_v30_validation():
    """Test validation of OpenAPI 3.0.x documents."""
    val = OpenAPIValidator(["openapi-spec"])
    res = val.validate('{"openapi":"3.0.0","info":{"title":"Test","version":"1.0"}, "paths": {}}')
    assert res.valid is True


def test_openapi_v31_validation():
    """Test validation of OpenAPI 3.1.x documents."""
    val = OpenAPIValidator(["openapi-spec"])
    res = val.validate('{"openapi":"3.1.0","info":{"title":"Test","version":"1.0"}, "paths": {}}')
    assert res.valid is True


def test_missing_required_field():
    """Test validation fails for missing required field (info)."""
    val = OpenAPIValidator(["openapi-spec"])
    res = val.validate('{"openapi":"3.1.0", "paths": {}}')
    assert res.valid is False
    assert len(res.diagnostics) > 0


def test_invalid_openapi_version():
    """Test validation fails for unsupported OpenAPI version."""
    val = OpenAPIValidator(["openapi-spec"])
    res = val.validate('{"openapi":"2.0", "info":{"title":"Test","version":"1.0"}, "paths": {}}')
    assert res.valid is False


def test_accepts_dict_only():
    """Test that OpenAPISpecValidatorBackend only accepts dict format."""
    from jentic.apitools.openapi.validator.backends.openapi_spec import OpenAPISpecValidatorBackend

    backend = OpenAPISpecValidatorBackend()
    accepted = backend.accepts()
    assert "dict" in accepted
    assert "uri" not in accepted
    assert "text" not in accepted


def test_diagnostic_code_never_unset():
    """Test that diagnostic codes are never '<unset>'."""
    val = OpenAPIValidator(["openapi-spec"])
    # Invalid document that will produce diagnostics
    res = val.validate('{"openapi":"3.1.0","info":{"title":"ok","version":1}}')
    assert res.valid is False
    assert len(res.diagnostics) > 0
    for diagnostic in res.diagnostics:
        assert diagnostic.code != "<unset>", (
            f"Diagnostic code should not be '<unset>': {diagnostic.message}"
        )
        assert diagnostic.code is not None, (
            f"Diagnostic code should not be None: {diagnostic.message}"
        )
        assert diagnostic.code != "", f"Diagnostic code should not be empty: {diagnostic.message}"


def test_duplicate_operation_id_code():
    """Test that duplicate operation ID validation produces a meaningful code.

    This test verifies that the code for duplicate operationId errors
    is 'osv-validation-error' rather than '<unset>'.
    """
    val = OpenAPIValidator(["openapi-spec"])
    doc = {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "operationId": "getUser",
                    "responses": {"200": {"description": "Success"}},
                },
                "post": {
                    "operationId": "getUser",  # Duplicate operationId
                    "responses": {"200": {"description": "Success"}},
                },
            }
        },
    }
    res = val.validate(doc)
    assert res.valid is False
    assert len(res.diagnostics) > 0

    # Find the duplicate operationId diagnostic
    duplicate_diag = None
    for diag in res.diagnostics:
        if "operationId" in diag.message.lower() or "operation" in diag.message.lower():
            duplicate_diag = diag
            break

    assert duplicate_diag is not None, "Should find a diagnostic about duplicate operationId"
    assert duplicate_diag.code == "osv-validation-error", (
        f"Duplicate operationId should have code 'osv-validation-error', got '{duplicate_diag.code}'"
    )


def test_all_diagnostics_have_valid_codes():
    """Test that all diagnostics from various validation errors have valid codes."""
    val = OpenAPIValidator(["openapi-spec"])
    # Document with multiple validation issues
    doc = {
        "openapi": "3.1.0",
        "info": {"title": "Test", "version": 1},  # version should be string
        "paths": {
            "/test": {
                "get": {
                    "responses": {}  # Missing required response
                }
            }
        },
    }
    res = val.validate(doc)
    assert res.valid is False
    assert len(res.diagnostics) > 0

    for diagnostic in res.diagnostics:
        # Code should be a non-empty string that's not '<unset>'
        assert isinstance(diagnostic.code, str), f"Code should be string: {diagnostic.code}"
        assert len(diagnostic.code) > 0, f"Code should not be empty: {diagnostic.message}"
        assert diagnostic.code != "<unset>", f"Code should not be '<unset>': {diagnostic.message}"
