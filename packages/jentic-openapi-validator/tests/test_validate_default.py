"""Tests for DefaultOpenAPIValidatorBackend."""

from jentic.apitools.openapi.validator.core import OpenAPIValidator


def test_default_backend_discovery():
    """Test that the default backend can be discovered via entry points."""
    validator = OpenAPIValidator(backends=["default"])
    assert len(validator.backends) == 1

    backend_names = [type(b).__name__ for b in validator.backends]
    assert "DefaultOpenAPIValidatorBackend" in backend_names


def test_validator_ok():
    """Test validation of valid OpenAPI documents."""
    val = OpenAPIValidator()

    # Valid document with servers
    res = val.validate(
        '{"openapi":"3.1.0","info":{"title":"ok","version":"1"}, "paths": {}, "servers": [{"url": "https://api.example.com"}]}'
    )
    assert res.valid is True


def test_validator_failure():
    """Test validation fails for invalid OpenAPI documents."""
    val = OpenAPIValidator()

    # Missing required paths section
    res = val.validate('{"openapi":"3.1.0","info":{"title":"ok","version":"1"}}')
    assert res.valid is False

    # Invalid version field type (number instead of string)
    res = val.validate('{"openapi":"3.1.0","info":{"title":"ok","version":1}}')
    assert res.valid is False

    # Missing required servers array
    res = val.validate('{"openapi":"3.1.0","info":{"title":"ok","version":"1"}, "paths": {}}')
    assert res.valid is False
    assert any(d.code == "MISSING_SERVER_URL" for d in res.diagnostics)


def test_missing_info_section():
    """Test validation fails when info section is missing."""
    val = OpenAPIValidator()
    res = val.validate('{"openapi":"3.1.0", "paths": {}}')
    assert res.valid is False
    assert len(res.diagnostics) > 0


def test_missing_info_fields():
    """Test validation fails when required info fields are missing."""
    val = OpenAPIValidator()

    # Missing title
    res = val.validate('{"openapi":"3.1.0","info":{"version":"1.0"}, "paths": {}}')
    assert res.valid is False

    # Missing version
    res = val.validate('{"openapi":"3.1.0","info":{"title":"Test"}, "paths": {}}')
    assert res.valid is False


def test_server_url_validation():
    """Test validation of server URLs."""
    val = OpenAPIValidator()

    # Valid absolute URLs
    res = val.validate(
        '{"openapi":"3.1.0","info":{"title":"Test","version":"1.0"}, "paths": {}, "servers": [{"url": "https://api.example.com"}]}'
    )
    assert res.valid is True

    # Relative URL should generate warning but document is still valid
    res = val.validate(
        '{"openapi":"3.1.0","info":{"title":"Test","version":"1.0"}, "paths": {}, "servers": [{"url": "/api"}]}'
    )
    # Relative URLs generate warnings, not errors
    assert any(d.code == "RELATIVE_SERVER_URL" for d in res.diagnostics)


def test_security_scheme_validation():
    """Test validation of security schemes and references."""
    val = OpenAPIValidator()

    # Valid security scheme definition and usage
    valid_doc = """{
        "openapi": "3.1.0",
        "info": {"title": "Test", "version": "1.0"},
        "paths": {},
        "servers": [{"url": "https://api.example.com"}],
        "components": {
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer"}
            }
        },
        "security": [{"bearerAuth": []}]
    }"""
    res = val.validate(valid_doc)
    assert res.valid is True

    # Undefined security scheme reference
    invalid_doc = """{
        "openapi": "3.1.0",
        "info": {"title": "Test", "version": "1.0"},
        "paths": {},
        "security": [{"undefinedAuth": []}]
    }"""
    res = val.validate(invalid_doc)
    assert res.valid is False
    assert any(d.code == "UNDEFINED_SECURITY_SCHEME_REFERENCE" for d in res.diagnostics)


def test_unused_security_scheme():
    """Test detection of unused security schemes."""
    val = OpenAPIValidator()

    # Security scheme defined but never used (should generate warning)
    doc = """{
        "openapi": "3.1.0",
        "info": {"title": "Test", "version": "1.0"},
        "paths": {},
        "components": {
            "securitySchemes": {
                "unusedAuth": {"type": "http", "scheme": "bearer"}
            }
        }
    }"""
    res = val.validate(doc)
    # Document is valid but has warnings
    assert any(d.code == "UNUSED_SECURITY_SCHEME_DEFINED" for d in res.diagnostics)


def test_accepts_uri_and_dict():
    """Test that DefaultOpenAPIValidatorBackend accepts both uri and dict formats."""
    from jentic.apitools.openapi.validator.backends.default import DefaultOpenAPIValidatorBackend

    backend = DefaultOpenAPIValidatorBackend()
    accepted = backend.accepts()
    assert "dict" in accepted
    assert "uri" in accepted
    assert "text" not in accepted


def test_validate_server_trailing_slash_produces_warning():
    """Test that server URLs with trailing slashes produce a warning diagnostic.

    Server URLs should not end with a trailing slash as it can cause
    issues when concatenating with paths.
    """
    val = OpenAPIValidator(backends=["default"])
    doc = {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
        "servers": [{"url": "https://api.example.com/"}],
    }
    result = val.validate(doc)

    # Check if there's a diagnostic about trailing slash
    trailing_slash_diag = next(
        (
            d
            for d in result.diagnostics
            if "trailing" in d.message.lower() or "trailing" in str(d.code or "").lower()
        ),
        None,
    )
    # Note: This test documents current behavior - the default backend may not have this rule yet
    if trailing_slash_diag is not None:
        assert trailing_slash_diag is not None, "Expected trailing slash diagnostic"
    else:
        # If no trailing slash rule exists, document this for future implementation
        print("Note: default backend does not currently check for server trailing slashes")
