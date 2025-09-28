import subprocess
import pytest
from pathlib import Path

from jentic_openapi_common.subprocess import SubprocessExecutionError
from jentic_openapi_validator_spectral import RedoclyValidator

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "openapi"


@pytest.mark.skipif(
    subprocess.run(
        ["npx", "--yes", "@redocly/cli@latest", "--version"], capture_output=True
    ).returncode
    != 0,
    reason="Redocly CLI not available",
)
def test_redocly_validator_ok():
    spec_file = FIXTURES_DIR / "simple_openapi.json"
    spec_uri = spec_file.as_uri()

    validator = RedoclyValidator()
    assert validator is not None
    assert validator.redocly_path == "npx --yes @redocly/cli@latest"
    result = validator.validate(spec_uri)
    for d in result.diagnostics:
        print(f"{d.code}: {d.message}")
    assert result.valid is False
    assert result.diagnostics[0].code == "operation-summary"
    assert (
        result.diagnostics[0].message
        == "Operation object should contain `summary` field. [path: paths./test.get.summary]"
    )
    # assert "Redocly CLI not found" in str(result.diagnostics[0].message)


@pytest.mark.skipif(
    subprocess.run(
        ["npx", "--yes", "@redocly/cli@latest", "--version"], capture_output=True
    ).returncode
    != 0,
    reason="Redocly CLI not available",
)
def test_redocly_validator_failure():
    spec_file = FIXTURES_DIR / "simple_openapi_invalid.json"
    spec_uri = spec_file.as_uri()

    validator = RedoclyValidator()
    assert validator is not None
    assert validator.redocly_path == "npx --yes @redocly/cli@latest"
    result = validator.validate(spec_uri)
    for d in result.diagnostics:
        print(f"{d.code}: {d.message}")
    assert result.valid is False


def test_redocly_validator_custom_path():
    """Test RedoclyValidator with custom redocly path."""
    validator = RedoclyValidator(redocly_path="/custom/path/to/redocly")
    assert validator.redocly_path == "/custom/path/to/redocly"


def test_redocly_validator_without_cli():
    """Test RedoclyValidator behavior when redocly CLI is not available."""
    validator = RedoclyValidator(redocly_path="nonexistent_redocly")

    with pytest.raises(SubprocessExecutionError, match="'nonexistent_redocly"):
        validator.validate("/some/test/file.yaml")
