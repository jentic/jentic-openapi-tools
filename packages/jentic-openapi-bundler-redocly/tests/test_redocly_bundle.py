import subprocess
import pytest
from pathlib import Path

from jentic_openapi_bundler_redocly import RedoclyBundler
from jentic_openapi_common import SubprocessExecutionError

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "openapi"
SNAPSHOTS_DIR = Path(__file__).parent / "fixtures" / "snapshots"


@pytest.mark.skipif(
    subprocess.run(
        ["npx", "--yes", "@redocly/cli@^2.1.5", "--version"], capture_output=True
    ).returncode
    != 0,
    reason="Redocly CLI not available",
)
def test_redocly_bundler_ok():
    spec_file = FIXTURES_DIR / "openapi.yaml"
    spec_uri = spec_file.as_uri()

    expected = (SNAPSHOTS_DIR / "openapi-bundled.json").read_text(encoding="utf-8")

    bundler = RedoclyBundler()
    assert bundler is not None
    assert bundler.redocly_path == "npx --yes @redocly/cli@^2.1.5"
    result = bundler.bundle(spec_uri)
    assert result == expected
    # assert "Redocly CLI not found" in str(result.diagnostics[0].message)


@pytest.mark.skipif(
    subprocess.run(
        ["npx", "--yes", "@redocly/cli@^2.1.5", "--version"], capture_output=True
    ).returncode
    != 0,
    reason="Redocly CLI not available",
)
def test_redocly_bundler_failure():
    spec_file = FIXTURES_DIR / "simple_openapi_not_well_formed.json"
    spec_uri = spec_file.as_uri()

    bundler = RedoclyBundler()
    assert bundler is not None
    assert bundler.redocly_path == "npx --yes @redocly/cli@^2.1.5"
    with pytest.raises(Exception, match="Failed to parse API"):
        bundler.bundle(spec_uri)


def test_redocly_bundler_custom_path():
    """Test RedoclyBundler with custom redocly path."""
    bundler = RedoclyBundler(redocly_path="/custom/path/to/redocly")
    assert bundler.redocly_path == "/custom/path/to/redocly"


def test_redocly_bundler_without_cli():
    """Test RedoclyBundler behavior when redocly CLI is not available."""
    bundler = RedoclyBundler(redocly_path="nonexistent_redocly")
    # This would need a file path, not a dict - the current implementation
    # expects a file path to pass to redocly CLI
    try:
        bundler.bundle("/some/test/file.yaml")
    except SubprocessExecutionError as e:
        assert "[Errno 2] No such file or directory: 'nonexistent_redocly'" in str(e.stderr)
