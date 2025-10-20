"""Path security utilities for safe filesystem access."""

from pathlib import Path
from typing import Literal, overload


__all__ = [
    "PathSecurityError",
    "PathTraversalError",
    "InvalidExtensionError",
    "SymlinkSecurityError",
    "validate_path",
]


class PathSecurityError(Exception):
    """Base exception for path security violations."""

    pass


class PathTraversalError(PathSecurityError):
    """Raised when a path attempts to escape the allowed base directory."""

    pass


class InvalidExtensionError(PathSecurityError):
    """Raised when a file has a disallowed extension."""

    pass


class SymlinkSecurityError(PathSecurityError):
    """Raised when a path contains symlinks when not allowed or symlink escapes boundary."""

    pass


@overload
def validate_path(
    path: str | Path,
    *,
    allowed_base: str | Path | None = None,
    allowed_extensions: tuple[str, ...] | None = None,
    resolve_symlinks: bool = True,
    as_string: Literal[True] = True,
) -> str: ...


@overload
def validate_path(
    path: str | Path,
    *,
    allowed_base: str | Path | None = None,
    allowed_extensions: tuple[str, ...] | None = None,
    resolve_symlinks: bool = True,
    as_string: Literal[False],
) -> Path: ...


def validate_path(
    path: str | Path,
    *,
    allowed_base: str | Path | None = None,
    allowed_extensions: tuple[str, ...] | None = None,
    resolve_symlinks: bool = True,
    as_string: bool = True,
) -> str | Path:
    """
    Validate and canonicalize a filesystem path with security checks.

    This function provides defense-in-depth security for filesystem access by:
    1. Converting to absolute path and resolving `.` and `..` components
    2. Optionally resolving symlinks and checking they don't escape boundaries
    3. Enforcing boundary restrictions (path must be within allowed_base)
    4. Validating file extensions against a whitelist

    Args:
        path: The filesystem path to validate (string or Path object)
        allowed_base: Optional base directory that path must be within.
            If None, no boundary checking is performed.
        allowed_extensions: Optional tuple of allowed file extensions (e.g., ('.yaml', '.json')).
            Extensions are case-sensitive. If None, no extension checking is performed.
        resolve_symlinks: If True (default), resolve symlinks using Path.resolve().
            If False, use Path.absolute() to preserve symlinks.
        as_string: If True (default), return str. If False, return Path object.

    Returns:
        Canonicalized path (str by default, or Path if as_string=False) that has passed all security checks.

    Raises:
        PathTraversalError: If the path attempts to escape the allowed_base directory
        InvalidExtensionError: If the file extension is not in allowed_extensions
        SymlinkSecurityError: If symlink resolution reveals a security issue

    Examples:
        >>> # Basic validation with boundary enforcement (returns str by default)
        >>> validate_path("/var/app/data/file.yaml", allowed_base="/var/app")
        '/var/app/data/file.yaml'

        >>> # Return Path object when needed
        >>> validate_path("/var/app/data/file.yaml", allowed_base="/var/app", as_string=False)
        Path('/var/app/data/file.yaml')

        >>> # Prevent directory traversal
        >>> validate_path("/var/app/../etc/passwd", allowed_base="/var/app")
        PathTraversalError: Path '/etc/passwd' is outside allowed base '/var/app'

        >>> # Extension validation
        >>> validate_path("file.txt", allowed_extensions=('.yaml', '.json'))
        InvalidExtensionError: Path 'file.txt' has disallowed extension '.txt'
    """
    if not path:
        raise PathSecurityError("Path cannot be empty or None")

    # Convert to Path object
    path_obj = Path(path)

    # Canonicalize path (resolve . and ..)
    if resolve_symlinks:
        # Fully resolve including symlinks
        try:
            canonical_path = path_obj.resolve(strict=False)
        except (OSError, RuntimeError) as e:
            raise PathSecurityError(f"Failed to resolve path '{path}': {e}") from e
    else:
        # Convert to absolute but preserve symlinks
        canonical_path = path_obj.absolute()

    # Boundary enforcement
    if allowed_base is not None:
        allowed_base_path = Path(allowed_base)
        if resolve_symlinks:
            try:
                canonical_base = allowed_base_path.resolve(strict=False)
            except (OSError, RuntimeError) as e:
                raise PathSecurityError(
                    f"Failed to resolve allowed_base '{allowed_base}': {e}"
                ) from e
        else:
            canonical_base = allowed_base_path.absolute()

        # Check if canonical_path is within canonical_base
        try:
            canonical_path.relative_to(canonical_base)
        except ValueError:
            raise PathTraversalError(
                f"Path '{canonical_path}' is outside allowed base '{canonical_base}'"
            ) from None

        # Additional check: if resolve_symlinks is True, verify that no symlink in the path
        # escapes the boundary. This is already handled by resolve() above, but we add
        # an explicit check for symlinks that might have been followed
        if resolve_symlinks and path_obj.is_symlink():
            # If the original path was a symlink, verify the resolved target is still in bounds
            try:
                canonical_path.relative_to(canonical_base)
            except ValueError:
                raise SymlinkSecurityError(
                    f"Symlink '{path}' resolves to '{canonical_path}' which is outside allowed base '{canonical_base}'"
                ) from None

    # Extension validation
    if allowed_extensions is not None:
        if not canonical_path.suffix:
            raise InvalidExtensionError(
                f"Path '{canonical_path}' has no file extension. Allowed extensions: {allowed_extensions}"
            )
        if canonical_path.suffix not in allowed_extensions:
            raise InvalidExtensionError(
                f"Path '{canonical_path}' has disallowed extension '{canonical_path.suffix}'. "
                f"Allowed extensions: {allowed_extensions}"
            )

    return str(canonical_path) if as_string else canonical_path
