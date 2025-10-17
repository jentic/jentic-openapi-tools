import os
import re
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlsplit, urlunsplit


__all__ = [
    "URIResolutionError",
    "is_uri_like",
    "is_http_https_url",
    "is_file_uri",
    "is_path",
    "resolve_to_absolute",
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


def is_uri_like(s: str | None) -> bool:
    r"""
    Heuristic check: is `s` a URI-like reference or absolute/relative path?
    - Accepts http(s)://, file://
    - Accepts absolute POSIX (/...) and Windows (\\..., \..., C:\..., C:/...) paths
    - Accepts relative paths (./..., ../..., .\..., ..\...)
    - Must be a single line (no '\\n' or '\\r').
    Leading/trailing whitespace is ignored.
    """
    if not s:
        return False
    s = s.strip()
    # Enforce single line
    if "\n" in s or "\r" in s:
        return False
    return bool(_URI_LIKE_RE.match(s))


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
        return _file_uri_to_path(value)

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


def _guard_single_line(s: str) -> None:
    if not isinstance(s, str) or ("\n" in s or "\r" in s):
        raise URIResolutionError("Input must be a single-line string.")


def _looks_like_windows_path(s: str) -> bool:
    return bool(_WINDOWS_DRIVE_RE.match(s) or _WINDOWS_UNC_RE.match(s))


def is_http_https_url(s: str) -> bool:
    p = urlparse(s)
    return p.scheme in ("http", "https") and bool(p.netloc)


def is_file_uri(s: str) -> bool:
    return urlparse(s).scheme == "file"


def _normalize_url(s: str) -> str:
    import posixpath

    parts = urlsplit(s)
    # Normalize the path component using posixpath (URLs always use forward slashes)
    normalized_path = posixpath.normpath(parts.path) if parts.path else "/"
    # Ensure root path is "/"
    if normalized_path == ".":
        normalized_path = "/"
    return urlunsplit((parts.scheme, parts.netloc, normalized_path, parts.query, parts.fragment))


def _file_uri_to_path(file_uri: str) -> str:
    p = urlparse(file_uri)
    if p.scheme != "file":
        raise URIResolutionError(f"Not a file URI: {file_uri!r}")
    if p.netloc and p.netloc not in ("", "localhost"):
        # UNC: \\server\share\path
        unc = f"//{p.netloc}{p.path}"
        return str(Path(urllib.request.url2pathname(unc)).resolve())
    path = urllib.request.url2pathname(p.path)
    return str(Path(path).resolve())


def _resolve_path_like(value: str, base_uri: str | None) -> str:
    value = os.path.expandvars(os.path.expanduser(value))

    if base_uri:
        if is_file_uri(base_uri):
            base_path = Path(urllib.request.url2pathname(urlparse(base_uri).path))
        elif is_http_https_url(base_uri):
            # Don't silently combine a local path with a URL base
            raise URIResolutionError("Cannot resolve a local path against an HTTP(S) base_uri.")
        else:
            base_path = Path(os.path.expandvars(os.path.expanduser(base_uri)))
    else:
        base_path = Path.cwd()

    p = Path(value)
    return str(p.resolve() if p.is_absolute() else (base_path / p).resolve())
