"""Tests for RedoclyBundlerBackend functionality."""

import os

import pytest

from jentic.apitools.openapi.common.path_security import (
    InvalidExtensionError,
    PathTraversalError,
)
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
        assert bundler.redocly_path == "npx --yes @redocly/cli@2.11.1"
        assert bundler.timeout == 600.0

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


class TestRedoclyBundlerPathSecurity:
    """Test path security features."""

    def test_initialization_with_allowed_base_dir(self, tmp_path):
        """Test RedoclyBundler initialization with allowed_base_dir."""
        bundler = RedoclyBundlerBackend(allowed_base_dir=str(tmp_path))
        assert bundler.allowed_base_dir == str(tmp_path)

    def test_initialization_without_allowed_base_dir(self):
        """Test RedoclyBundler initialization without allowed_base_dir (default None)."""
        bundler = RedoclyBundlerBackend()
        assert bundler.allowed_base_dir is None

    def test_path_validation_disabled_when_allowed_base_dir_is_none(self, tmp_path):
        """Test that path traversal is NOT blocked when allowed_base_dir is None."""
        bundler = RedoclyBundlerBackend(allowed_base_dir=None)

        # Create a test file outside any restricted directory
        test_file = tmp_path / "spec.yaml"
        test_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}")

        # This should not raise PathTraversalError (but may fail for other reasons like missing Redocly)
        try:
            bundler.bundle(str(test_file))
        except PathTraversalError:
            pytest.fail("PathTraversalError should not be raised when allowed_base_dir=None")
        except (SubprocessExecutionError, RuntimeError):
            # Expected if Redocly is not available
            pass

    def test_valid_path_within_allowed_base_dir(self, tmp_path):
        """Test that paths within allowed_base_dir are accepted."""
        test_file = tmp_path / "spec.yaml"
        test_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}")

        bundler = RedoclyBundlerBackend(allowed_base_dir=str(tmp_path))

        # Should not raise PathTraversalError
        try:
            bundler.bundle(str(test_file))
        except PathTraversalError:
            pytest.fail("Valid path should not raise PathTraversalError")
        except (SubprocessExecutionError, RuntimeError):
            # May fail for Redocly-related reasons
            pass

    def test_path_traversal_attempt_blocked(self, tmp_path):
        """Test that path traversal attempts are blocked."""
        # Create a restricted directory
        restricted_dir = tmp_path / "restricted"
        restricted_dir.mkdir()

        # Create a file outside the restricted directory
        outside_file = tmp_path / "outside.yaml"
        outside_file.write_text("openapi: 3.0.0")

        bundler = RedoclyBundlerBackend(allowed_base_dir=str(restricted_dir))

        # Attempt to access file outside allowed directory
        with pytest.raises(PathTraversalError):
            bundler.bundle(str(outside_file))

    def test_invalid_file_extension_rejected(self, tmp_path):
        """Test that files with invalid extensions are rejected."""
        test_file = tmp_path / "malicious.exe"
        test_file.write_text("fake executable")

        bundler = RedoclyBundlerBackend(allowed_base_dir=str(tmp_path))

        with pytest.raises(InvalidExtensionError):
            bundler.bundle(str(test_file))

    def test_http_url_bypasses_path_validation(self):
        """Test that HTTP(S) URLs bypass path validation."""
        bundler = RedoclyBundlerBackend(allowed_base_dir="/restricted/path")

        # HTTP URLs should bypass path validation (though they may fail for other reasons)
        try:
            bundler.bundle("https://example.com/openapi.yaml")
        except PathTraversalError:
            pytest.fail("HTTP URLs should bypass path validation")
        except (SubprocessExecutionError, RuntimeError):
            # Expected - Redocly may fail to fetch the URL
            pass

    def test_file_uri_with_path_validation(self, tmp_path):
        """Test that file:// URIs are validated correctly."""
        test_file = tmp_path / "spec.yaml"
        test_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}")

        bundler = RedoclyBundlerBackend(allowed_base_dir=str(tmp_path))

        # file:// URI should be validated
        try:
            bundler.bundle(test_file.as_uri())
        except PathTraversalError:
            pytest.fail("Valid file URI should not raise PathTraversalError")
        except (SubprocessExecutionError, RuntimeError):
            pass

    def test_valid_yaml_extensions_accepted(self, tmp_path):
        """Test that .yaml, .yml, and .json extensions are all accepted."""
        bundler = RedoclyBundlerBackend(allowed_base_dir=str(tmp_path))

        for ext in [".yaml", ".yml", ".json"]:
            test_file = tmp_path / f"spec{ext}"
            test_file.write_text("openapi: 3.0.0")

            try:
                bundler.bundle(str(test_file))
            except InvalidExtensionError:
                pytest.fail(f"Extension {ext} should be accepted")
            except (SubprocessExecutionError, RuntimeError):
                pass

    def test_relative_path_resolved_and_validated(self, tmp_path):
        """Test that relative paths are resolved before validation."""
        # Create a test file
        test_file = tmp_path / "spec.yaml"
        test_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}")

        bundler = RedoclyBundlerBackend(allowed_base_dir=str(tmp_path))

        # Use relative path - should be resolved and validated (no PathTraversalError)
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            try:
                bundler.bundle("./spec.yaml")
            except (SubprocessExecutionError, RuntimeError):
                # May fail for Redocly reasons, but path validation passed
                pass
        finally:
            os.chdir(original_cwd)
