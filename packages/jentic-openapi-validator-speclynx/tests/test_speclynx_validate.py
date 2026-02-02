import pytest

from jentic.apitools.openapi.common.path_security import (
    InvalidExtensionError,
    PathTraversalError,
)
from jentic.apitools.openapi.common.subproc import SubprocessExecutionError
from jentic.apitools.openapi.validator.backends.speclynx import (
    _DEFAULT_SPECLYNX_PATH,
    SpeclynxValidatorBackend,
)


@pytest.mark.requires_speclynx_cli
class TestSpeclynxValidatorIntegration:
    """Integration tests that require SpecLynx CLI to be available."""

    def test_validate_valid_openapi_document(self, speclynx_validator, valid_openapi_path):
        """Test validation of a valid OpenAPI document."""
        spec_uri = valid_openapi_path.as_uri()
        result = speclynx_validator.validate(spec_uri)
        assert result.valid is True

    def test_validate_invalid_openapi_document(
        self, speclynx_validator_with_plugins, invalid_openapi_path
    ):
        """Test validation of an invalid OpenAPI document with plugins enabled."""
        spec_uri = invalid_openapi_path.as_uri()
        result = speclynx_validator_with_plugins.validate(spec_uri)
        assert result.valid is False
        assert len(result.diagnostics) > 0
        # Check that our version-validator plugin caught the error
        assert any("version" in d.message.lower() for d in result.diagnostics)

    def test_validate_with_long_timeout(
        self, speclynx_validator_with_long_timeout, valid_openapi_path
    ):
        """Test validation with extended timeout still works."""
        spec_uri = valid_openapi_path.as_uri()
        result = speclynx_validator_with_long_timeout.validate(spec_uri)
        assert result.valid is True

    def test_validate_dict_without_base_url(self, speclynx_validator):
        """Test validation of a dict document without base_url."""
        document = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        result = speclynx_validator.validate(document)
        assert result.valid is True

    def test_validate_dict_with_base_url(self, speclynx_validator):
        """Test validation of a dict document with base_url."""
        document = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        result = speclynx_validator.validate(document, base_url="https://example.com/api")
        assert result.valid is True

    def test_validate_swagger_2_0_produces_error(self, speclynx_validator, swagger_2_0_path):
        """Test that Swagger 2.0 documents produce error diagnostics."""
        spec_uri = swagger_2_0_path.as_uri()
        result = speclynx_validator.validate(spec_uri)
        assert result.valid is False
        assert len(result.diagnostics) > 0
        # Check that the error message indicates the document is not recognized as OpenAPI 3.x
        openapi_error = next(
            (d for d in result.diagnostics if "openapi 3" in d.message.lower()), None
        )
        assert openapi_error is not None
        # Verify the path data is set from getPathKeys()
        # ParseResultElement is the root, so path should be empty list
        assert openapi_error.data is not None
        assert "path" in openapi_error.data
        assert openapi_error.data["path"] == []

    def test_validate_swagger_2_0_dict_produces_error(self, speclynx_validator):
        """Test that Swagger 2.0 dict documents produce error diagnostics."""
        document = {
            "swagger": "2.0",
            "info": {"title": "Swagger API", "version": "1.0.0"},
            "paths": {},
        }
        result = speclynx_validator.validate(document)
        assert result.valid is False
        assert len(result.diagnostics) > 0
        assert any("openapi 3" in d.message.lower() for d in result.diagnostics)

    def test_custom_plugins_merged_with_default_plugins(
        self, speclynx_validator_with_plugins, swagger_2_0_path
    ):
        """Test that custom plugins are merged with default plugins, not replacing them.

        When plugins_dir is specified, both default plugins AND custom plugins should be loaded.
        The default openapi-document plugin catches Swagger 2.0 as invalid,
        proving default plugins still run even when custom plugins_dir is specified.
        """
        spec_uri = swagger_2_0_path.as_uri()
        result = speclynx_validator_with_plugins.validate(spec_uri)
        # Default plugin should detect Swagger 2.0 as invalid OpenAPI 3.x
        assert result.valid is False
        assert any("openapi 3" in d.message.lower() for d in result.diagnostics)

    def test_both_default_and_custom_plugins_produce_diagnostics(
        self, speclynx_validator_with_plugins
    ):
        """Test that both default and custom plugins produce diagnostics when applicable.

        Uses an invalid document that triggers both:
        - Default plugin: Document is valid OpenAPI 3.0 (passes)
        - Custom plugin (version-validator): info.version is integer (fails)
        """
        document = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": 1},  # Integer triggers custom plugin
            "paths": {},
        }
        result = speclynx_validator_with_plugins.validate(document)
        assert result.valid is False
        # Custom plugin should detect integer version
        assert any("version" in d.message.lower() for d in result.diagnostics)

    def test_validate_empty_document_produces_error(self, speclynx_validator, tmp_path):
        """Test that empty documents produce validation errors.

        With allowEmpty: true in the parser configuration, empty documents
        parse successfully but result in an empty ParseResult (no api element).
        The openapi-document.mjs plugin then detects this and produces an
        'invalid-openapi-document' diagnostic.
        """
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("")

        result = speclynx_validator.validate(str(empty_file))
        assert result.valid is False
        assert len(result.diagnostics) == 1
        diagnostic = result.diagnostics[0]
        # Empty documents are detected by the openapi-document plugin
        assert diagnostic.code == "invalid-openapi-document"
        assert "openapi 3" in diagnostic.message.lower()
        # Path should be empty list (root of ParseResultElement)
        assert diagnostic.data["path"] == []

    def test_validate_invalid_syntax_produces_invalid_document_error(
        self, speclynx_validator, tmp_path
    ):
        """Test that syntactically invalid documents are detected as invalid OpenAPI.

        With the permissive parser configuration (allowEmpty: true, strict: false),
        malformed JSON/YAML is often parsed successfully by the YAML parser (which
        treats it as a string or simple value). The openapi-document.mjs plugin then
        detects that the result is not a valid OpenAPI document.

        Note: The 'parse-error' code is reserved for cases where all parsers fail
        and throw an exception (e.g., file read errors, encoding issues). In practice,
        the permissive YAML parser handles most malformed input gracefully.
        """
        invalid_json_file = tmp_path / "invalid.json"
        invalid_json_file.write_text("{invalid json syntax")

        result = speclynx_validator.validate(str(invalid_json_file))
        assert result.valid is False
        assert len(result.diagnostics) == 1
        diagnostic = result.diagnostics[0]
        # Invalid syntax is parsed by YAML and caught by openapi-document plugin
        assert diagnostic.code == "invalid-openapi-document"
        assert diagnostic.source == "speclynx-validator"
        assert "openapi 3" in diagnostic.message.lower()


class TestSpeclynxValidatorUnit:
    """Unit tests that don't require external dependencies."""

    def test_initialization_with_defaults(self):
        """Test SpeclynxValidator initialization with default values."""
        validator = SpeclynxValidatorBackend()
        assert validator.speclynx_path == _DEFAULT_SPECLYNX_PATH
        assert validator.timeout == 600.0

    def test_initialization_with_custom_speclynx_path(self):
        """Test SpeclynxValidator with custom speclynx_path."""
        validator = SpeclynxValidatorBackend(speclynx_path="/custom/path/to/speclynx")
        assert validator.speclynx_path == "/custom/path/to/speclynx"

    def test_initialization_with_custom_timeout(self):
        """Test SpeclynxValidator with custom timeout."""
        validator = SpeclynxValidatorBackend(timeout=60.0)
        assert validator.timeout == 60.0

    def test_initialization_with_all_custom_parameters(self, tmp_path):
        """Test SpeclynxValidator with all custom parameters."""
        plugins_path = tmp_path / "plugins"
        plugins_path.mkdir()
        validator = SpeclynxValidatorBackend(
            speclynx_path="/custom/speclynx",
            timeout=45.0,
            allowed_base_dir=str(tmp_path),
            plugins_dir=str(plugins_path),
        )
        assert validator.speclynx_path == "/custom/speclynx"
        assert validator.timeout == 45.0
        assert validator.allowed_base_dir == str(tmp_path)
        assert validator.plugins_dir == plugins_path

    def test_accepts_method(self):
        """Test the accepts method returns correct format identifiers."""
        validator = SpeclynxValidatorBackend()
        accepted = validator.accepts()
        assert isinstance(accepted, list)
        assert "uri" in accepted
        assert "dict" in accepted

    def test_unsupported_document_type(self):
        """Test validation with an unsupported document type."""
        validator = SpeclynxValidatorBackend()

        with pytest.raises(TypeError, match="Unsupported document type"):
            validator.validate(42)  # type: ignore


class TestSpeclynxValidatorPathSecurity:
    """Test path security features."""

    def test_initialization_with_allowed_base_dir(self, tmp_path):
        """Test SpeclynxValidator initialization with allowed_base_dir."""
        validator = SpeclynxValidatorBackend(allowed_base_dir=str(tmp_path))
        assert validator.allowed_base_dir == str(tmp_path)

    def test_initialization_without_allowed_base_dir(self):
        """Test SpeclynxValidator initialization without allowed_base_dir (default None)."""
        validator = SpeclynxValidatorBackend()
        assert validator.allowed_base_dir is None

    def test_path_validation_disabled_when_allowed_base_dir_is_none(self, tmp_path):
        """Test that path traversal is NOT blocked when allowed_base_dir is None."""
        validator = SpeclynxValidatorBackend(allowed_base_dir=None)

        # Create a test file outside any restricted directory
        test_file = tmp_path / "spec.yaml"
        test_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}")

        # This should not raise PathTraversalError (but may fail for other reasons like missing ApiDOM)
        try:
            validator.validate(str(test_file))
        except PathTraversalError:
            pytest.fail("PathTraversalError should not be raised when allowed_base_dir=None")
        except (SubprocessExecutionError, RuntimeError):
            # Expected if ApiDOM is not available
            pass

    def test_valid_path_within_allowed_base_dir(self, tmp_path):
        """Test that paths within allowed_base_dir are accepted."""
        test_file = tmp_path / "spec.yaml"
        test_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}")

        validator = SpeclynxValidatorBackend(allowed_base_dir=str(tmp_path))

        # Should not raise PathTraversalError
        try:
            validator.validate(str(test_file))
        except PathTraversalError:
            pytest.fail("Valid path should not raise PathTraversalError")
        except (SubprocessExecutionError, RuntimeError):
            # May fail for ApiDOM-related reasons
            pass

    def test_valid_yaml_extensions_accepted(self, tmp_path):
        """Test that .yaml, .yml, and .json extensions are all accepted."""
        validator = SpeclynxValidatorBackend(allowed_base_dir=str(tmp_path))

        for ext in [".yaml", ".yml", ".json"]:
            test_file = tmp_path / f"spec{ext}"
            test_file.write_text("openapi: 3.0.0")

            try:
                validator.validate(str(test_file))
            except InvalidExtensionError:
                pytest.fail(f"Extension {ext} should be accepted")
            except (SubprocessExecutionError, RuntimeError):
                pass
