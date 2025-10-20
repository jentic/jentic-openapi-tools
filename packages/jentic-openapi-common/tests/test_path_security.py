"""Tests for path security utilities."""

import os
import platform
import tempfile
from pathlib import Path

import pytest

from jentic.apitools.openapi.common.path_security import (
    InvalidExtensionError,
    PathSecurityError,
    PathTraversalError,
    SymlinkSecurityError,
    validate_path,
)


# Basic validation tests


def test_validate_path_accepts_absolute_path():
    """Test that absolute paths are accepted and canonicalized."""
    # Test str return (default)
    result_str = validate_path("/tmp/test.yaml")
    assert os.path.isabs(result_str)
    assert result_str == str(Path("/tmp/test.yaml"))

    # Test Path return
    result_path = validate_path("/tmp/test.yaml", as_string=False)
    assert result_path.is_absolute()
    assert result_path == Path("/tmp/test.yaml")


def test_validate_path_accepts_relative_path():
    """Test that relative paths are converted to absolute."""
    # Test str return (default)
    result_str = validate_path("test.yaml")
    assert os.path.isabs(result_str)
    assert "test.yaml" in result_str

    # Test Path return
    result_path = validate_path("test.yaml", as_string=False)
    assert result_path.is_absolute()
    assert result_path.name == "test.yaml"


def test_validate_path_accepts_path_object():
    """Test that Path objects are accepted."""
    path_obj = Path("/tmp/test.yaml")
    # Test str return (default)
    result_str = validate_path(path_obj)
    assert os.path.isabs(result_str)

    # Test Path return
    result_path = validate_path(path_obj, as_string=False)
    assert result_path.is_absolute()


def test_validate_path_raises_on_empty_string():
    """Test that empty string raises PathSecurityError."""
    with pytest.raises(PathSecurityError, match="Path cannot be empty"):
        validate_path("")


def test_validate_path_resolves_dot_segments():
    """Test that . and .. are resolved."""
    result = validate_path("/tmp/./foo/../bar/test.yaml", as_string=False)
    assert "/." not in str(result)
    assert "/.." not in str(result)
    assert result == Path("/tmp/bar/test.yaml")


# Boundary enforcement tests


def test_validate_path_within_allowed_base():
    """Test that paths within allowed_base are accepted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "subdir" / "test.yaml"
        result = validate_path(test_file, allowed_base=tmpdir, as_string=False)
        assert result.is_absolute()
        # Verify it's within the base
        result.relative_to(tmpdir)  # Should not raise


def test_validate_path_outside_allowed_base_raises():
    """Test that paths outside allowed_base raise PathTraversalError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        outside_path = "/etc/passwd"
        with pytest.raises(PathTraversalError, match="outside allowed base"):
            validate_path(outside_path, allowed_base=tmpdir)


def test_validate_path_traversal_attempt_blocked():
    """Test that directory traversal attempts are blocked."""
    with tempfile.TemporaryDirectory() as tmpdir:
        traversal_path = Path(tmpdir) / ".." / ".." / "etc" / "passwd"
        with pytest.raises(PathTraversalError, match="outside allowed base"):
            validate_path(traversal_path, allowed_base=tmpdir)


def test_validate_path_exact_base_allowed():
    """Test that the allowed_base itself is considered valid."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = validate_path(tmpdir, allowed_base=tmpdir, as_string=False)
        assert result == Path(tmpdir).resolve()


def test_validate_path_no_boundary_check_when_base_is_none():
    """Test that no boundary checking is performed when allowed_base is None."""
    # Should not raise even for sensitive paths
    result = validate_path("/etc/passwd", as_string=False)
    assert result == Path("/etc/passwd")


# Extension validation tests


def test_validate_path_allowed_extension_accepted():
    """Test that files with allowed extensions are accepted."""
    result = validate_path(
        "/tmp/test.yaml", allowed_extensions=(".yaml", ".yml", ".json"), as_string=False
    )
    assert result.suffix == ".yaml"


def test_validate_path_disallowed_extension_raises():
    """Test that files with disallowed extensions raise InvalidExtensionError."""
    with pytest.raises(InvalidExtensionError, match="disallowed extension"):
        validate_path("/tmp/test.txt", allowed_extensions=(".yaml", ".yml", ".json"))


def test_validate_path_no_extension_raises_when_extensions_required():
    """Test that files without extensions raise when extensions are required."""
    with pytest.raises(InvalidExtensionError, match="has no file extension"):
        validate_path("/tmp/test", allowed_extensions=(".yaml", ".yml"))


def test_validate_path_extension_case_sensitive():
    """Test that extension validation is case-sensitive."""
    with pytest.raises(InvalidExtensionError, match="disallowed extension"):
        validate_path("/tmp/test.YAML", allowed_extensions=(".yaml",))


def test_validate_path_no_extension_check_when_none():
    """Test that no extension checking is performed when allowed_extensions is None."""
    result = validate_path("/tmp/test.txt", as_string=False)
    assert result.suffix == ".txt"


# Symlink tests


@pytest.mark.skipif(platform.system() == "Windows", reason="Symlink tests require Unix-like system")
def test_validate_path_resolves_symlinks_by_default():
    """Test that symlinks are resolved by default."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        real_file = tmpdir_path / "real.yaml"
        real_file.touch()
        symlink = tmpdir_path / "link.yaml"
        symlink.symlink_to(real_file)

        result = validate_path(symlink, allowed_base=tmpdir, as_string=False)
        assert result == real_file.resolve()


@pytest.mark.skipif(platform.system() == "Windows", reason="Symlink tests require Unix-like system")
def test_validate_path_preserves_symlinks_when_disabled():
    """Test that symlinks are preserved when resolve_symlinks=False."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        real_file = tmpdir_path / "real.yaml"
        real_file.touch()
        symlink = tmpdir_path / "link.yaml"
        symlink.symlink_to(real_file)

        result = validate_path(
            symlink, allowed_base=tmpdir, resolve_symlinks=False, as_string=False
        )
        # Should be absolute but not resolved
        assert result.is_absolute()


@pytest.mark.skipif(platform.system() == "Windows", reason="Symlink tests require Unix-like system")
def test_validate_path_symlink_escaping_boundary_raises():
    """Test that symlinks pointing outside allowed_base raise SymlinkSecurityError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        # Create symlink pointing outside
        symlink = tmpdir_path / "escape.yaml"
        # Create a target outside the tmpdir
        outside_target = Path("/tmp/outside.yaml")
        try:
            outside_target.touch()
            symlink.symlink_to(outside_target)

            with pytest.raises(
                (PathTraversalError, SymlinkSecurityError), match="outside allowed base"
            ):
                validate_path(symlink, allowed_base=tmpdir)
        finally:
            if outside_target.exists():
                outside_target.unlink()


# Combined validation tests


def test_validate_path_combined_boundary_and_extension():
    """Test validation with both boundary and extension checks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.yaml"
        result = validate_path(
            test_file,
            allowed_base=tmpdir,
            allowed_extensions=(".yaml", ".yml", ".json"),
            as_string=False,
        )
        assert result.is_absolute()
        assert result.suffix == ".yaml"


def test_validate_path_combined_boundary_and_extension_both_fail():
    """Test that both boundary and extension errors can be raised."""
    with tempfile.TemporaryDirectory() as tmpdir:
        outside_file = "/etc/passwd"
        # This should raise PathTraversalError (checked first)
        with pytest.raises(PathTraversalError):
            validate_path(outside_file, allowed_base=tmpdir, allowed_extensions=(".yaml",))


# Edge cases


def test_validate_path_unicode_paths():
    """Test that unicode paths are handled correctly."""
    result = validate_path("/tmp/测试.yaml")
    assert "测试" in str(result)


def test_validate_path_with_spaces():
    """Test that paths with spaces are handled correctly."""
    result = validate_path("/tmp/my file.yaml")
    assert "my file" in str(result)


def test_validate_path_relative_with_allowed_base():
    """Test relative path with allowed_base."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Change to tmpdir and use relative path
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            result = validate_path("test.yaml", allowed_base=tmpdir, as_string=False)
            assert result.is_absolute()
            # Should be within tmpdir
            result.relative_to(tmpdir)
        finally:
            os.chdir(original_cwd)


def test_validate_path_dot_files():
    """Test that hidden files (starting with .) are handled."""
    result = validate_path("/tmp/.hidden.yaml", as_string=False)
    assert result.name == ".hidden.yaml"


def test_validate_path_multiple_extensions():
    """Test files with multiple extensions."""
    result = validate_path("/tmp/test.tar.gz", allowed_extensions=(".gz",), as_string=False)
    assert result.suffix == ".gz"


def test_validate_path_allows_directories():
    """Test that directories can be validated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        subdir = Path(tmpdir) / "subdir"
        result = validate_path(subdir, allowed_base=tmpdir, as_string=False)
        assert result.is_absolute()
