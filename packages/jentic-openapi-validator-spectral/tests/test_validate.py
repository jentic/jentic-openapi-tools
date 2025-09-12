import subprocess
from pathlib import Path

import pytest
from jentic_openapi_validator_spectral import SpectralValidator

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "openapi"


@pytest.mark.skipif(
    subprocess.run(["spectral", "--version"], capture_output=True).returncode != 0,
    reason="Spectral CLI not available",
)
def test_spectral_validator_ok():
    spec_file = FIXTURES_DIR / "simple_openapi.json"
    spec_uri = spec_file.as_uri()

    validator = SpectralValidator()
    assert validator is not None
    assert validator.spectral_path == "spectral"
    result = validator.validate(spec_uri)
    assert result.valid is True
    # assert "Spectral CLI not found" in str(result.diagnostics[0].message)


@pytest.mark.skipif(
    subprocess.run(["spectral", "--version"], capture_output=True).returncode != 0,
    reason="Spectral CLI not available",
)
def test_spectral_validator_failure():
    spec_file = FIXTURES_DIR / "simple_openapi_invalid.json"
    spec_uri = spec_file.as_uri()

    validator = SpectralValidator()
    assert validator is not None
    assert validator.spectral_path == "spectral"
    result = validator.validate(spec_uri)
    assert result.valid is False


def test_spectral_validator_custom_path():
    """Test SpectralValidator with custom spectral path."""
    validator = SpectralValidator(spectral_path="/custom/path/to/spectral")
    assert validator.spectral_path == "/custom/path/to/spectral"


def test_spectral_validator_without_cli():
    """Test SpectralValidator behavior when spectral CLI is not available."""
    validator = SpectralValidator(spectral_path="nonexistent_spectral")

    # This would need a file path, not a dict - the current implementation
    # expects a file path to pass to spectral CLI
    result = validator.validate("/some/test/file.yaml")
    assert "Spectral CLI not found" in str(result.diagnostics[0].message)
    pass
