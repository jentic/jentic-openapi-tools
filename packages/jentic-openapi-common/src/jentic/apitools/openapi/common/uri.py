import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlsplit, urlunsplit
from urllib.request import url2pathname


__all__ = [
    "URIResolutionError",
    "is_uri_like",
    "is_http_https_url",
    "is_file_uri",
    "is_scheme_relative_uri",
    "is_absolute_uri",
    "is_fragment_only_uri",
    "is_path",
    "resolve_to_absolute",
    "file_uri_to_path",
]


_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")
_WINDOWS_UNC_RE = re.compile(r"^(?:\\\\|//)[^\\/]+[\\/][^\\/]+")

# Matches:
# - http://... or https://...
# - file://...
# - POSIX absolute: /path or just "/"
# - Windows UNC: \\server\share\...
# - Windows root-relative: \path\to (current drive root)
# - Windows drive-absolute: C:\path\to or C:/path/to
# - Relative paths: ./path, ../path, .\path, ..\path, or plain relative paths
_URI_LIKE_RE = re.compile(
    r"""^(?:
            https?://[^\r\n]+ |
            file://[^\r\n]+   |
            /[^\r\n]*         |
            \\\\[^\r\n]+      |
            \\[^\r\n]+        |
            [A-Za-z]:\\[^\r\n]+ |
            [A-Za-z]:/[^\r\n]+ |
            \./[^\r\n]*       |
            \.\\/[^\r\n]*     |
            \.\.[/\\][^\r\n]* |
            \.\.\\[^\r\n]*    |
            [a-zA-Z_][a-zA-Z0-9_.-]*(?:[/\\][a-zA-Z0-9_.-]+)+ |
            [a-zA-Z_][a-zA-Z0-9_.-]*\.[a-zA-Z0-9]+(?![}\])])
        )$""",
    re.VERBOSE,
)


class URIResolutionError(ValueError):
    pass


def is_uri_like(uri: str | None) -> bool:
    r"""
    Heuristic check: is `s` a URI-like reference or absolute/relative path?
    - Accepts http(s)://, file://
    - Accepts absolute POSIX (/...) and Windows (\\..., \..., C:\..., C:/...) paths
    - Accepts relative paths (./..., ../..., .\..., ..\...)
    - Must be a single line (no '\\n' or '\\r').
    Leading/trailing whitespace is ignored.
    """
    if not uri:
        return False
    uri = uri.strip()
    # Enforce single line
    if "\n" in uri or "\r" in uri:
        return False
    return bool(_URI_LIKE_RE.match(uri))


def is_path(s: str | None) -> bool:
    """
    Check if `s` is a filesystem path (not a URL or URI).

    Returns True for:
    - Absolute POSIX paths: /home/file.txt
    - Absolute Windows paths: C:\\Windows\\file.txt, \\\\server\\share\\path
    - Relative paths: ./config.yaml, ../parent/file.txt

    Returns False for:
    - HTTP(S) URLs: http://example.com
    - File URIs: file:///home/file.txt
    - Other URIs: mailto:test@example.com, data:text/plain, ftp://ftp.example.com
    - Empty or None strings
    """
    if not s:
        return False

    s = s.strip()

    # Must match the URI-like pattern first
    if not is_uri_like(s):
        return False

    # Exclude HTTP(S) URLs
    if is_http_https_url(s):
        return False

    # Exclude file:// URIs
    if is_file_uri(s):
        return False

    # Exclude any other URI schemes (mailto:, data:, ftp:, etc.)
    parsed = urlparse(s)
    if parsed.scheme:  # Has a scheme
        return False

    # It's a path!
    return True


def is_http_https_url(url: str) -> bool:
    p = urlparse(url)
    return p.scheme in ("http", "https") and bool(p.netloc)


def is_file_uri(uri: str) -> bool:
    return urlparse(uri).scheme == "file"


def is_scheme_relative_uri(uri: str) -> bool:
    """
    Check if `uri` is a scheme-relative URI (also called protocol-relative URI).

    A scheme-relative URI starts with "//" followed by an authority component (netloc),
    inheriting the scheme from the context (e.g., "//cdn.example.com/path").

    This is defined in RFC 3986 section 4.2 as a network-path reference.
    Per RFC 3986, a valid network-path reference must have an authority component.

    Examples:
        - "//cdn.example.com/x.yaml" -> True
        - "//example.com/api" -> True
        - "http://example.com" -> False (has scheme)
        - "/path/to/file" -> False (single slash)
        - "./relative" -> False (relative path)
        - "//" -> False (no authority component)
        - "///path" -> False (no authority component)

    Args:
        uri: The string to check

    Returns:
        True if the string is a valid scheme-relative URI with authority, False otherwise
    """
    if not uri.startswith("//"):
        return False
    p = urlparse(uri)
    return bool(p.netloc)


def is_absolute_uri(uri: str) -> bool:
    """
    Check if `uri` is an absolute URI according to RFC 3986.

    An absolute URI is defined as having a scheme (e.g., "http:", "https:", "ftp:", "file:").

    Note: Scheme-relative URIs (starting with "//") are NOT considered absolute URIs.
    According to RFC 3986 section 4.2, scheme-relative URIs are classified as
    "relative references" (specifically, "network-path references").
    Use `is_scheme_relative_uri()` to check for those separately.

    Examples:
        - "http://example.com" -> True
        - "https://example.com/path" -> True
        - "ftp://ftp.example.com" -> True
        - "file:///path/to/file" -> True
        - "//cdn.example.com/x.yaml" -> False (scheme-relative, use is_scheme_relative_uri)
        - "/path/to/file" -> False (absolute path, not URI)
        - "./relative" -> False
        - "#fragment" -> False

    Args:
        uri: The string to check

    Returns:
        True if the string is an absolute URI (has a scheme), False otherwise
    """
    p = urlparse(uri)
    return bool(p.scheme)


def is_fragment_only_uri(uri: str) -> bool:
    """
    Check if `uri` is a fragment-only reference.

    A fragment-only reference consists solely of a fragment identifier (starts with "#").
    These are used in JSON References and OpenAPI to refer to parts within the same document.

    Note: This checks if the ENTIRE string is a fragment reference, not whether
    a URI contains a fragment. For example, "http://example.com#section" would
    return False because it's a full URI with a fragment, not fragment-only.

    Examples:
        - "#/definitions/User" -> True
        - "#fragment" -> True
        - "#" -> True (empty fragment identifier)
        - "##" -> True (fragment identifier is "#")
        - "http://example.com#section" -> False (full URI with fragment)
        - "/path/to/file" -> False
        - "./relative" -> False
        - "" -> False

    Args:
        uri: The string to check

    Returns:
        True if the string is a fragment-only reference, False otherwise
    """
    return uri.startswith("#")


def resolve_to_absolute(value: str, base_uri: str | None = None) -> str:
    """
    Resolve `value` to either:
      - an absolute URL (with scheme), OR
      - an absolute filesystem path (no scheme)

    • If `base_uri` is None AND `value` has no scheme (i.e., relative URI or path),
    return an **absolute filesystem path** resolved against CWD.

    Other rules:
      • Absolute http(s) URLs ⇒ return absolute URL.
      • file:// URIs ⇒ return absolute filesystem path.
      • If `base_uri` is an http(s) URL, relative inputs resolve to absolute URLs.
      • If `base_uri` is a path or file://, relative inputs resolve to absolute paths.
      • Mixing a path-like `value` with an http(s) `base_uri` raises (ambiguous).
      • Scheme-relative (“//host/path”) without a URL base ⇒ raises.
    """
    _guard_single_line(value)

    if is_http_https_url(value):
        return _normalize_url(value)

    if is_file_uri(value):
        return file_uri_to_path(value)

    if _looks_like_windows_path(value):
        return _resolve_path_like(value, base_uri)

    parsed = urlparse(value)
    # Scheme-relative without URL base is ambiguous
    if value.startswith("//"):
        if base_uri and is_http_https_url(base_uri):
            return _normalize_url(urljoin(base_uri, value))
        raise URIResolutionError("Scheme-relative URLs require a URL base_uri.")

    # Any other explicit scheme (mailto:, data:, ftp:, etc.) → accept as-is
    if parsed.scheme:
        if parsed.scheme in ("http", "https"):
            if not parsed.netloc:
                raise URIResolutionError(f"Malformed URL (missing host): {value!r}")
            return _normalize_url(value)
        if parsed.scheme == "file":
            # handled above
            raise AssertionError("unreachable")
        return value  # leave non-file, non-http schemes untouched

    # --- No scheme: relative URI or path ---
    if base_uri:
        if is_http_https_url(base_uri):
            # Relative URI against URL base → absolute URL
            return _normalize_url(urljoin(base_uri, value))
        # base is file path or file:// → absolute path
        return _resolve_path_like(value, base_uri)

    # **Your rule**: no base + no scheme ⇒ absolute filesystem path
    return _resolve_path_like(value, None)


def file_uri_to_path(file_uri: str) -> str:
    """
    Convert a file:// URI to an absolute filesystem path.

    Args:
        file_uri: A file:// URI string (e.g., "file:///path/to/file" or "file://server/share/path")

    Returns:
        Absolute filesystem path as a string

    Raises:
        URIResolutionError: If the input is not a valid file:// URI

    Examples:
        >>> file_uri_to_path("file:///home/user/doc.yaml")
        '/home/user/doc.yaml'
        >>> file_uri_to_path("file://localhost/etc/config.yaml")
        '/etc/config.yaml'
    """
    parsed_uri = urlparse(file_uri)
    if parsed_uri.scheme != "file":
        raise URIResolutionError(f"Not a file URI: {file_uri!r}")
    if parsed_uri.netloc and parsed_uri.netloc not in ("", "localhost"):
        # UNC: \\server\share\path
        unc = f"//{parsed_uri.netloc}{parsed_uri.path}"
        return str(Path(url2pathname(unc)).resolve())
    path = url2pathname(parsed_uri.path)
    return str(Path(path).resolve())


def _guard_single_line(s: str) -> None:
    if not isinstance(s, str) or ("\n" in s or "\r" in s):
        raise URIResolutionError("Input must be a single-line string.")


def _looks_like_windows_path(s: str) -> bool:
    return bool(_WINDOWS_DRIVE_RE.match(s) or _WINDOWS_UNC_RE.match(s))


def _normalize_url(s: str) -> str:
    import posixpath

    parts = urlsplit(s)
    # Normalize the path component using posixpath (URLs always use forward slashes)
    normalized_path = posixpath.normpath(parts.path) if parts.path else "/"
    # Ensure root path is "/"
    if normalized_path == ".":
        normalized_path = "/"
    return urlunsplit((parts.scheme, parts.netloc, normalized_path, parts.query, parts.fragment))


def _resolve_path_like(value: str, base_uri: str | None) -> str:
    value = os.path.expandvars(os.path.expanduser(value))

    if base_uri:
        if is_file_uri(base_uri):
            base_path = Path(url2pathname(urlparse(base_uri).path))
        elif is_http_https_url(base_uri):
            # Don't silently combine a local path with a URL base
            raise URIResolutionError("Cannot resolve a local path against an HTTP(S) base_uri.")
        else:
            base_path = Path(os.path.expandvars(os.path.expanduser(base_uri)))
    else:
        base_path = Path.cwd()

    p = Path(value)
    return str(p.resolve() if p.is_absolute() else (base_path / p).resolve())
