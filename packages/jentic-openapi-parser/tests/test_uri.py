import os
from pathlib import Path
from urllib.parse import urlparse

import pytest

from jentic.apitools.openapi.parser.core import UriResolutionError, resolve_to_absolute


# -----------------------
# Utilities
# -----------------------


def cwd(tmp_path: Path):
    """Context manager to temporarily chdir to tmp_path."""

    class _Cwd:
        def __enter__(self):
            self._old = Path.cwd()
            os.chdir(tmp_path)
            return tmp_path

        def __exit__(self, exc_type, exc, tb):
            os.chdir(self._old)

    return _Cwd()


# -----------------------
# URL cases
# -----------------------


def test_absolute_https_url_returns_url_and_is_normalized():
    out = resolve_to_absolute("https://example.com/a/./b/../c")
    # urljoin normalization should collapse dot segments to /a/c
    assert out == "https://example.com/a/c"
    assert urlparse(out).scheme == "https"


def test_absolute_http_url_with_empty_path_gets_slash():
    out = resolve_to_absolute("http://example.com")
    assert out == "http://example.com/"
    assert urlparse(out).path == "/"


def test_malformed_http_missing_host_raises():
    with pytest.raises(UriResolutionError):
        resolve_to_absolute("https:///nohost")


# -----------------------
# file:// URI cases
# -----------------------


def test_file_uri_to_absolute_path(tmp_path: Path):
    file_path = tmp_path / "spec.yaml"
    file_path.write_text("openapi: 3.1.0\n", encoding="utf-8")
    file_uri = file_path.as_uri()  # file:///... absolute
    out = resolve_to_absolute(file_uri)
    assert Path(out).is_absolute()
    assert Path(out).exists()
    assert not urlparse(out).scheme  # no scheme for file paths


@pytest.mark.skipif(os.name != "nt", reason="UNC path parsing is Windows-specific")
def test_file_uri_unc_to_windows_path():
    # We can't guarantee the UNC exists, but we can ensure it parses and returns a path-like string.
    # Example UNC: file://server/share/folder/file.txt  → \\server\share\folder\file.txt
    out = resolve_to_absolute("file://server/share/folder/file.txt")
    # On Windows, absolute paths either start with drive-letter or UNC prefix \\server\share
    assert out.startswith("\\\\server\\share\\folder\\file.txt")


# -----------------------
# Path cases without base (must return absolute path)
# -----------------------


def test_relative_path_without_base_resolves_against_cwd(tmp_path: Path):
    with cwd(tmp_path):
        (tmp_path / "a").mkdir()
        (tmp_path / "a" / "spec.yaml").write_text("x", encoding="utf-8")
        out = resolve_to_absolute("a/spec.yaml")
        assert Path(out).is_absolute()
        assert Path(out) == tmp_path / "a" / "spec.yaml"


def test_absolute_posix_path_without_base_is_returned_absolute(tmp_path: Path):
    # Use tmp_path which is absolute
    out = resolve_to_absolute(str(tmp_path))
    assert Path(out).is_absolute()
    # On non-Windows, the scheme should be empty
    if os.name != "nt":
        assert not urlparse(out).scheme


@pytest.mark.skipif(os.name != "nt", reason="Windows drive-letter path test")
def test_windows_drive_letter_path_without_base_is_returned_absolute(tmp_path: Path, monkeypatch):
    # Simulate Windows CWD and resolve relative "C:\\foo\\bar"
    # We can't assume C: exists in CI paths, so we create a path on the same drive as tmp_path
    drive = Path(tmp_path.drive or "C:")
    target = drive / "some" / "folder"
    # We only check that it parses to an absolute path string.
    out = resolve_to_absolute(str(target))
    assert Path(out).is_absolute()
    # On Windows, parsed scheme is empty for filesystem paths
    assert not urlparse(out).scheme


@pytest.mark.skipif(os.name != "nt", reason="UNC path test requires Windows")
def test_windows_unc_path_without_base_is_returned_absolute():
    # Non-existing UNC still should be treated as a path-like string, not a URL
    out = resolve_to_absolute(r"\\server\share\folder\file.txt")
    assert out.startswith(r"\\server\share\folder\file.txt")
    assert not urlparse(out).scheme


# -----------------------
# Relative against URL base → URL
# -----------------------


def test_relative_against_url_base_yields_absolute_url():
    out = resolve_to_absolute("users.yaml", base_uri="https://api.example.com/openapi/")
    assert out == "https://api.example.com/openapi/users.yaml"
    assert urlparse(out).scheme == "https"


def test_scheme_relative_needs_url_base():
    out = resolve_to_absolute("//example.com/path")
    assert out == "/example.com/path"
    # With a URL base, it should fail
    with pytest.raises(UriResolutionError):
        out = resolve_to_absolute("//example.com/path", base_uri="https://base.example")


# -----------------------
# Relative against path or file:// base → absolute path
# -----------------------


def test_relative_against_path_base_yields_absolute_path(tmp_path: Path):
    base_dir = tmp_path / "specs"
    base_dir.mkdir()
    out = resolve_to_absolute("users.yaml", base_uri=str(base_dir))
    assert Path(out).is_absolute()
    assert Path(out) == base_dir / "users.yaml"


def test_relative_against_file_uri_base_yields_absolute_path(tmp_path: Path):
    base_dir = tmp_path / "oai"
    base_dir.mkdir()
    base_uri = (base_dir).as_uri()  # file:///...
    out = resolve_to_absolute("a/b.yaml", base_uri=base_uri)
    assert Path(out).is_absolute()
    assert Path(out) == base_dir / "a" / "b.yaml"


def test_resolve_local_path_against_http_base():
    out = resolve_to_absolute("local/file.yaml", base_uri="https://example.com/base/")
    assert out == "https://example.com/base/local/file.yaml"


# -----------------------
# Disallow mixing local path with HTTP base
# -----------------------


@pytest.mark.skipif(os.name != "nt", reason="Windows path literal in URL mixing")
def test_cannot_resolve_windows_drive_path_against_http_base_windows():
    with pytest.raises(UriResolutionError):
        resolve_to_absolute(r"C:\folder\file.yaml", base_uri="https://example.com/base/")


# -----------------------
# Non-HTTP schemes (allowed and passed through)
# -----------------------


@pytest.mark.parametrize(
    "value",
    [
        "mailto:devnull@example.com",
        "data:text/plain;base64,SGVsbG8=",
        "ftp://ftp.example.com/pub/file.txt",
    ],
)
def test_other_schemes_are_returned_as_is(value: str):
    out = resolve_to_absolute(value)
    assert out == value
    assert urlparse(out).scheme == urlparse(value).scheme


# -----------------------
# Guards and edge cases
# -----------------------


def test_multiline_input_raises():
    with pytest.raises(UriResolutionError):
        resolve_to_absolute("a\nb")


def test_empty_string_without_base_resolves_to_cwd(tmp_path: Path):
    # Edge: treat empty string like "." → absolute cwd
    # If you prefer to treat empty string as error, change the impl & update this test.
    with cwd(tmp_path):
        out = resolve_to_absolute("")
        assert Path(out).is_absolute()
        assert Path(out) == tmp_path


def test_dot_and_dotdot_paths(tmp_path: Path):
    base = tmp_path / "root"
    (base / "a" / "b").mkdir(parents=True)
    with cwd(base):
        assert resolve_to_absolute(".") == str(base.resolve())
        assert resolve_to_absolute("a/./b/..") == str((base / "a").resolve())


def test_url_normalization_collapses_dot_segments_in_join():
    out = resolve_to_absolute("x/../y/./z", base_uri="https://ex.com/a/b/")
    assert out == "https://ex.com/a/b/y/z"
