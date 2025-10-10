"""Tests for the core OpenAPIValidator functionality."""


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
    assert "openapi-spec" in backends
