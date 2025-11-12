"""Tests for validating unbundled OpenAPI documents with external references."""

import tempfile
from urllib.parse import urljoin, urlparse
from urllib.request import url2pathname

import pytest

from jentic.apitools.openapi.parser.core import OpenAPIParser, load_uri
from jentic.apitools.openapi.validator.core import OpenAPIValidator


def _print_diagnostics(backend_name: str, result):
    """Helper to print validation results for debugging."""
    print(f"({backend_name}) valid: {result.valid}")
    for d in result.diagnostics:
        print(f"({backend_name}) {d.code}: {d.message}")


class TestValidateUnbundledDefault:
    """Tests for default backend with unbundled documents."""

    def test_validate_unbundled_http_relative_existing_default(self, http_server):
        """Test default backend with HTTP URL and existing relative references."""
        spec_url = urljoin(http_server.base_url, "root-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        # Default backend validates document structure but doesn't validate external references
        validator = OpenAPIValidator(backends=["default"])
        result = validator.validate(spec_url, base_url=spec_url)
        _print_diagnostics("default", result)
        assert result.valid  # Default backend only checks structure, not external refs

    def test_validate_unbundled_http_relative_non_existing_default(self, http_server):
        """Test default backend with HTTP URL and non-existing relative references."""
        spec_url = urljoin(http_server.base_url, "root-invalid-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        # Default backend validates document structure but doesn't validate external references
        validator = OpenAPIValidator(backends=["default"])
        result = validator.validate(spec_url, base_url=spec_url)
        _print_diagnostics("default", result)
        assert result.valid  # Default backend only checks structure, not external refs

    def test_validate_unbundled_file_http_relative_existing_with_baseurl_default(self, http_server):
        """Test default backend with file and HTTP base URL."""
        spec_url = urljoin(http_server.base_url, "root-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        # Write spec to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".spec.json", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(spec_text)
            parsed = urlparse(temp_file.name)
            spec_file_path = url2pathname(parsed.path)

        # Default backend validates document structure but doesn't validate external references
        validator = OpenAPIValidator(backends=["default"])
        result = validator.validate(spec_file_path, base_url=spec_url)
        _print_diagnostics("default", result)
        assert result.valid  # Default backend only checks structure, not external refs


@pytest.mark.requires_spectral_cli
class TestValidateUnbundledSpectral:
    """Tests for spectral backend with unbundled documents."""

    def test_validate_unbundled_http_relative_existing_spectral(self, http_server):
        """Test spectral backend with HTTP URL and existing relative references."""
        spec_url = urljoin(http_server.base_url, "root-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        validator = OpenAPIValidator(backends=["spectral"])
        result = validator.validate(spec_url, base_url=spec_url)
        _print_diagnostics("spectral", result)
        assert not result.valid
        assert len(result.diagnostics) == 3

    def test_validate_unbundled_http_relative_non_existing_spectral(self, http_server):
        """Test spectral backend with HTTP URL and non-existing relative references."""
        spec_url = urljoin(http_server.base_url, "root-invalid-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        validator = OpenAPIValidator(backends=["spectral"])
        result = validator.validate(spec_url, base_url=spec_url)
        _print_diagnostics("spectral", result)
        assert not result.valid
        assert len(result.diagnostics) == 12

    def test_validate_unbundled_file_http_relative_existing_with_baseurl_spectral(
        self, http_server
    ):
        """Test spectral backend with file and HTTP base URL."""
        spec_url = urljoin(http_server.base_url, "root-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        # Write spec to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".spec.json", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(spec_text)
            parsed = urlparse(temp_file.name)
            spec_file_path = url2pathname(parsed.path)

        validator = OpenAPIValidator(backends=["spectral"])
        result = validator.validate(spec_file_path, base_url=spec_url)
        _print_diagnostics("spectral", result)
        assert not result.valid
        assert len(result.diagnostics) == 12
        assert any(diag.code == "invalid-ref" for diag in result.diagnostics)


@pytest.mark.requires_redocly_cli
class TestValidateUnbundledRedocly:
    """Tests for redocly backend with unbundled documents."""

    def test_validate_unbundled_http_relative_existing_redocly(self, http_server):
        """Test redocly backend with HTTP URL and existing relative references."""
        spec_url = urljoin(http_server.base_url, "root-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        validator = OpenAPIValidator(backends=["redocly"])
        result = validator.validate(spec_url, base_url=spec_url)
        _print_diagnostics("redocly", result)
        assert not result.valid
        assert len(result.diagnostics) == 5

    def test_validate_unbundled_http_relative_non_existing_redocly(self, http_server):
        """Test redocly backend with HTTP URL and non-existing relative references."""
        spec_url = urljoin(http_server.base_url, "root-invalid-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        validator = OpenAPIValidator(backends=["redocly"])
        result = validator.validate(spec_url, base_url=spec_url)
        _print_diagnostics("redocly", result)
        assert not result.valid
        assert len(result.diagnostics) == 80

    def test_validate_unbundled_file_http_relative_existing_with_baseurl_redocly(self, http_server):
        """Test redocly backend with file and HTTP base URL."""
        spec_url = urljoin(http_server.base_url, "root-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        # Write spec to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".spec.json", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(spec_text)
            parsed = urlparse(temp_file.name)
            spec_file_path = url2pathname(parsed.path)

        validator = OpenAPIValidator(backends=["redocly"])
        result = validator.validate(spec_file_path, base_url=spec_url)
        _print_diagnostics("redocly", result)
        assert not result.valid
        assert len(result.diagnostics) == 80
        assert any(diag.code == "no-unresolved-refs" for diag in result.diagnostics)


class TestValidateUnbundledOpenAPISpec:
    """Tests for openapi-spec backend with unbundled documents."""

    def test_validate_unbundled_http_without_base_url(self, http_server):
        """Test openapi-spec backend without base_url - should fail to validate relative URLs."""
        spec_url = urljoin(http_server.base_url, "root-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        validator = OpenAPIValidator(backends=["openapi-spec"])
        result = validator.validate(spec_url)
        _print_diagnostics("openapi-spec (no base_url)", result)
        assert not result.valid
        assert len(result.diagnostics) == 1
        assert result.diagnostics[0].code == "openapi-spec-validator-error"

    def test_validate_unbundled_http_with_base_url_and_errors(self, http_server):
        """Test openapi-spec backend with base_url - should detect schema errors."""
        spec_url_with_errors = urljoin(
            http_server.base_url, "root-relative-refs-no-info-valid-and-errors.json"
        )
        validator = OpenAPIValidator(backends=["openapi-spec"])
        result = validator.validate(spec_url_with_errors, base_url=spec_url_with_errors)
        _print_diagnostics("openapi-spec (with base_url)", result)
        assert not result.valid
        assert len(result.diagnostics) == 1
        assert result.diagnostics[0].code == "type"

    def test_validate_unbundled_http_invalid_refs_without_base_url(self, http_server):
        """Test openapi-spec backend with invalid refs and no base_url."""
        spec_url = urljoin(http_server.base_url, "root-invalid-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        validator = OpenAPIValidator(backends=["openapi-spec"])
        result = validator.validate(spec_url)
        _print_diagnostics("openapi-spec (no base_url)", result)
        assert not result.valid
        assert len(result.diagnostics) == 1
        assert result.diagnostics[0].code == "openapi-spec-validator-error"

    def test_validate_unbundled_http_invalid_refs_with_base_url(self, http_server):
        """Test openapi-spec backend with invalid refs and base_url - should still fail."""
        spec_url = urljoin(http_server.base_url, "root-invalid-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        validator = OpenAPIValidator(backends=["openapi-spec"])
        result = validator.validate(spec_url, base_url=spec_url)
        _print_diagnostics("openapi-spec (with base_url)", result)
        assert not result.valid
        assert len(result.diagnostics) == 1
        assert result.diagnostics[0].code == "openapi-spec-validator-error"

    def test_validate_unbundled_file_with_base_url(self, http_server):
        """Test openapi-spec backend with file and HTTP base URL - should be valid."""
        spec_url = urljoin(http_server.base_url, "root-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        # Write spec to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".spec.json", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(spec_text)
            parsed = urlparse(temp_file.name)
            spec_file_path = url2pathname(parsed.path)

        validator = OpenAPIValidator(backends=["openapi-spec"])
        result = validator.validate(spec_file_path, base_url=spec_url)
        _print_diagnostics("openapi-spec (with base_url)", result)
        assert result.valid
