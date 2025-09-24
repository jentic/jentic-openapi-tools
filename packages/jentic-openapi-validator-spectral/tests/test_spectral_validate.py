import subprocess
import pytest
from pathlib import Path

from jentic.apitools.openapi.common.subproc import SubprocessExecutionError
from jentic.apitools.openapi.validator.spectral import SpectralValidator

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "openapi"


@pytest.mark.skipif(
    subprocess.run(
        ["npx", "@stoplight/spectral-cli@^6.15.0", "--version"], capture_output=True
    ).returncode
    != 0,
    reason="Spectral CLI not available",
)
def test_spectral_validator_ok():
    spec_file = FIXTURES_DIR / "simple_openapi.json"
    spec_uri = spec_file.as_uri()

    validator = SpectralValidator()
    assert validator is not None
    assert validator.spectral_path == "npx @stoplight/spectral-cli@^6.15.0"
    result = validator.validate(spec_uri)
    assert result.valid is True
    # assert "Spectral CLI not found" in str(result.diagnostics[0].message)


@pytest.mark.skipif(
    subprocess.run(
        ["npx", "@stoplight/spectral-cli@^6.15.0", "--version"], capture_output=True
    ).returncode
    != 0,
    reason="Spectral CLI not available",
)
def test_spectral_validator_failure():
    spec_file = FIXTURES_DIR / "simple_openapi_invalid.json"
    spec_uri = spec_file.as_uri()

    validator = SpectralValidator()
    assert validator is not None
    assert validator.spectral_path == "npx @stoplight/spectral-cli@^6.15.0"
    result = validator.validate(spec_uri)
    assert result.valid is False


def test_spectral_validator_custom_path():
    """Test SpectralValidator with custom spectral path."""
    validator = SpectralValidator(spectral_path="/custom/path/to/spectral")
    assert validator.spectral_path == "/custom/path/to/spectral"


def test_spectral_validator_without_cli():
    """Test SpectralValidator behavior when spectral CLI is not available."""
    validator = SpectralValidator(spectral_path="nonexistent_spectral")

    with pytest.raises(SubprocessExecutionError, match="'nonexistent_spectral"):
        validator.validate("/some/test/file.yaml")
