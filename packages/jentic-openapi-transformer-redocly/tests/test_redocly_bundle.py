"""Tests for RedoclyBundlerBackend functionality."""

import pytest

from jentic.apitools.openapi.common.subproc import SubprocessExecutionError
from jentic.apitools.openapi.transformer.bundler.backends.redocly import RedoclyBundlerBackend


class TestRedoclyBundlerIntegration:
    """Integration tests that require Redocly CLI to be available."""

    @pytest.mark.requires_redocly_cli
    def test_bundle_valid_openapi_document(
        self,
        redocly_bundler: RedoclyBundlerBackend,
        valid_openapi_uri: str,
        expected_bundled_content: str,
    ):
        """Test successful bundling of a valid OpenAPI document."""
        result = redocly_bundler.bundle(valid_openapi_uri)
        assert result == expected_bundled_content

    @pytest.mark.requires_redocly_cli
    def test_bundle_malformed_openapi_document(
        self,
        redocly_bundler: RedoclyBundlerBackend,
        malformed_openapi_uri: str,
    ):
        """Test bundling of a malformed OpenAPI document raises RuntimeError."""
        with pytest.raises(RuntimeError, match="Failed to parse API"):
            redocly_bundler.bundle(malformed_openapi_uri)

    @pytest.mark.requires_redocly_cli
    def test_bundle_with_custom_timeout(
        self,
        redocly_bundler_with_custom_timeout: RedoclyBundlerBackend,
        valid_openapi_uri: str,
        expected_bundled_content: str,
    ):
        """Test bundling with custom timeout configuration."""
        result = redocly_bundler_with_custom_timeout.bundle(valid_openapi_uri)
        assert result == expected_bundled_content

    @pytest.mark.requires_redocly_cli
    def test_bundle_dict_document(
        self,
        redocly_bundler: RedoclyBundlerBackend,
        expected_bundled_content: str,
    ):
        """Test bundling of a dict OpenAPI document."""
        # Simple OpenAPI document as dict
        openapi_dict = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {"/test": {"get": {"responses": {"200": {"description": "OK"}}}}},
        }

        result = redocly_bundler.bundle(openapi_dict)
        # Should return valid JSON (can be parsed)
        import json

        parsed_result = json.loads(result)
        assert parsed_result["openapi"] == "3.0.3"
        assert parsed_result["info"]["title"] == "Test API"


class TestRedoclyBundlerUnit:
    """Unit tests that don't require external dependencies."""

    def test_init_with_defaults(self):
        """Test RedoclyBundlerBackend initialization with default values."""
        bundler = RedoclyBundlerBackend()
        assert bundler.redocly_path == "npx --yes @redocly/cli@^2.1.5"
        assert bundler.timeout == 30.0

    def test_init_with_custom_path(self, redocly_bundler_with_custom_path: RedoclyBundlerBackend):
        """Test RedoclyBundlerBackend initialization with custom redocly path."""
        assert redocly_bundler_with_custom_path.redocly_path == "/custom/path/to/redocly"

    def test_init_with_custom_timeout(
        self, redocly_bundler_with_custom_timeout: RedoclyBundlerBackend
    ):
        """Test RedoclyBundlerBackend initialization with custom timeout."""
        assert redocly_bundler_with_custom_timeout.timeout == 60.0

    def test_accepts_returns_correct_formats(self, redocly_bundler: RedoclyBundlerBackend):
        """Test that accepts() returns the correct supported formats."""
        formats = redocly_bundler.accepts()
        assert formats == ["uri", "dict"]
        assert isinstance(formats, list)

    def test_bundle_with_unsupported_document_type(self, redocly_bundler: RedoclyBundlerBackend):
        """Test that bundle() raises TypeError for unsupported document types."""
        with pytest.raises(TypeError, match="Unsupported document type"):
            redocly_bundler.bundle(42)  # type: ignore

        with pytest.raises(TypeError, match="Unsupported document type"):
            redocly_bundler.bundle(None)  # type: ignore

        with pytest.raises(TypeError, match="Unsupported document type"):
            redocly_bundler.bundle([])  # type: ignore


class TestRedoclyBundlerErrorHandling:
    """Tests for error handling scenarios."""

    def test_bundle_with_nonexistent_cli(self):
        """Test behavior when redocly CLI is not available."""
        bundler = RedoclyBundlerBackend(redocly_path="nonexistent_redocly")

        with pytest.raises(SubprocessExecutionError):
            bundler.bundle("/some/test/file.yaml")

    def test_bundle_with_invalid_file_path(self, redocly_bundler: RedoclyBundlerBackend):
        """Test bundling with invalid file path."""
        with pytest.raises(RuntimeError, match="does not exist"):
            redocly_bundler.bundle("/nonexistent/path/to/file.yaml")

    def test_bundle_with_timeout_configuration(self):
        """Test that timeout is properly configured."""
        bundler = RedoclyBundlerBackend(timeout=1.0)  # Very short timeout
        assert bundler.timeout == 1.0

    def test_bundle_empty_string_input(self, redocly_bundler: RedoclyBundlerBackend):
        """Test bundling with empty string input."""
        with pytest.raises(RuntimeError, match="Path cannot be empty"):
            redocly_bundler.bundle("")

    @pytest.mark.requires_redocly_cli
    def test_bundle_invalid_dict_input(self, redocly_bundler: RedoclyBundlerBackend):
        """Test bundling with invalid dict input."""
        invalid_dict = {"invalid": "not an openapi document"}

        # Should fail because it's not a valid OpenAPI document
        with pytest.raises(RuntimeError):
            redocly_bundler.bundle(invalid_dict)
