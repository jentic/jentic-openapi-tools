"""Tests for the core OpenAPIValidator functionality."""


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


def test_validation_result_bool_context(validator, valid_openapi_string):
    """Test that ValidationResult works in boolean context."""
    result = validator.validate(valid_openapi_string)
    assert result  # Should be truthy when valid


def test_validation_result_len(validator, invalid_openapi_string):
    """Test that ValidationResult supports len()."""
    result = validator.validate(invalid_openapi_string)
    assert len(result) > 0


def test_list_backends():
    """Test that list_backends returns available validator backends."""
    from jentic.apitools.openapi.validator.core import OpenAPIValidator

    backends = OpenAPIValidator.list_backends()
    assert isinstance(backends, list)
    assert len(backends) > 0
    assert "default" in backends
