"""Encoding tests for :func:`load_uri` and the HTTP loading path.

Regression coverage for the bug where an OpenAPI document served over HTTP as
``Content-Type: text/yaml`` *without* a ``charset`` parameter was decoded as
ISO-8859-1 (the legacy RFC 2616 default that ``requests`` applies to ``text/*``
responses). That corrupts every UTF-8 multibyte character: an em-dash (``—``,
UTF-8 ``E2 80 94``) becomes the byte sequence ``0xE2 0x80 0x94`` reinterpreted as
three Latin-1 code points, one of which is U+0080. PyYAML's reader then rejects
it with ``unacceptable character #x0080``, which is exactly the user-facing
import failure this suite guards against.

The fix decodes ``resp.content`` as UTF-8 (via ``utf-8-sig`` to also drop a BOM)
rather than trusting the transport charset. A YAML stream is UTF-8/16/32 by
definition (YAML spec §5.2), so the HTTP charset must not decide the codec.

Design notes
------------
* We do not add an HTTP-mocking dependency. Instead we monkeypatch
  ``loader.requests.get`` with a fake response whose ``.content`` (bytes),
  ``.text`` and ``.status_code`` faithfully reproduce how real ``requests``
  behaves for a given ``Content-Type``. The charset-resolution logic is taken
  from ``requests`` itself (``get_encoding_from_headers``) so the fake cannot
  drift from reality.
* Tests exercise the public API (``OpenAPIParser.parse`` /
  ``OpenAPIParser.load_uri``) and ``load_uri`` directly, across every backend
  that routes URI loading through ``load_uri``.
"""

from __future__ import annotations

import logging

import pytest
import requests
from requests.utils import get_encoding_from_headers

from jentic.apitools.openapi.parser.core import OpenAPIParser, load_uri
from jentic.apitools.openapi.parser.core import loader as loader_module
from jentic.apitools.openapi.parser.core.exceptions import (
    DocumentLoadError,
    DocumentParseError,
)


# --------------------------------------------------------------------------- #
# Constants: characters that expose the bug
# --------------------------------------------------------------------------- #

# An em-dash. In UTF-8 this is E2 80 94; decoded as Latin-1 the 0x80 byte
# becomes U+0080, which PyYAML rejects as "unacceptable character #x0080".
EM_DASH = "—"  # —

# Other non-ASCII characters that also survive UTF-8 but corrupt under Latin-1.
NON_ASCII_SAMPLES = {
    "em_dash": "—",  # — (the reported failure)
    "en_dash": "–",  # –
    "curly_quotes": "“quoted”",  # “quoted”
    "accented": "café",  # café
    "emoji": "rocket \U0001f680",  # 🚀 (4-byte UTF-8)
    "cjk": "日本語",  # 日本語
    "ellipsis": "one…two",  # …
}

TEST_URL = "https://docs.example.com/openapi.yaml"

# Backends whose ``parse()`` returns a dict-like mapping we can subscribe with
# ``doc["openapi"]``. datamodel-low is excluded (its text path does OpenAPI
# version detection these minimal specs aren't built for); ruamel-ast is
# excluded from *dict* assertions because it returns a raw YAML ``MappingNode``
# (asserted via string content instead — see ``_assert_marker_present``).
YAML_URL_BACKENDS_DICT = ["pyyaml", "ruamel-safe"]
# All backends that route URI loading through ``load_uri`` (encoding is what we
# actually care about here, independent of the returned representation).
YAML_URL_BACKENDS = ["pyyaml", "ruamel-safe", "ruamel-ast"]


def _assert_marker_present(doc, marker: str, context: str = "") -> None:
    """Assert *marker* survived parsing, tolerant of each backend's return type.

    ``pyyaml``/``ruamel-safe`` return a mapping; ``ruamel-ast`` returns a raw
    YAML node. We only care that the non-ASCII character round-tripped intact,
    so we check the string form of whatever was returned.
    """
    text = str(doc)
    assert marker in text, f"{context}: marker {marker!r} lost after parse"


def _spec_with(marker: str) -> str:
    """A minimal valid OpenAPI 3.1 doc carrying *marker* inside a scalar value."""
    return (
        "openapi: 3.1.0\n"
        "info:\n"
        f"  title: Live Tennis API {marker} data\n"
        "  version: 1.0.0\n"
        "paths: {}\n"
    )


# --------------------------------------------------------------------------- #
# Fake HTTP response that matches real ``requests`` charset behavior
# --------------------------------------------------------------------------- #


class FakeResponse:
    """Minimal stand-in for ``requests.Response``.

    Crucially, ``.text`` is computed exactly the way ``requests`` computes it:
    resolve the encoding from the headers (falling back to ISO-8859-1 for
    ``text/*`` with no charset, as real ``requests`` does) and decode
    ``.content`` with it. This means a test asserting the *old* behavior would
    genuinely reproduce the old bug, and a test asserting the *new* behavior is
    only green because the loader stopped using ``.text``.
    """

    def __init__(self, body: bytes, content_type: str, status_code: int = 200):
        self._content = body
        self.status_code = status_code
        self.headers = {"content-type": content_type} if content_type else {}
        # Mirror requests.Response.encoding resolution.
        self.encoding = get_encoding_from_headers(self.headers)

    @property
    def content(self) -> bytes:
        return self._content

    @property
    def text(self) -> str:
        # requests uses ISO-8859-1 as the *effective* codec when encoding is
        # unresolved for a text/* type; replicate the "text/* default" here so
        # the fake matches production for the header we care about.
        enc = self.encoding or "ISO-8859-1"
        return self._content.decode(enc, errors="replace")

    def raise_for_status(self) -> None:
        if 400 <= self.status_code:
            raise requests.HTTPError(f"HTTP {self.status_code}")


@pytest.fixture
def http_body(monkeypatch: pytest.MonkeyPatch):
    """Patch ``loader.requests.get`` to return a FakeResponse.

    Returns a setter: ``set_body(bytes, content_type=..., status=...)``.
    """

    state: dict = {}

    def _fake_get(url, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        state["last_url"] = url
        state["last_kwargs"] = kwargs
        return FakeResponse(
            state["body"],
            state.get("content_type", "text/yaml"),
            state.get("status", 200),
        )

    monkeypatch.setattr(loader_module.requests, "get", _fake_get)

    def set_body(body: bytes, content_type: str = "text/yaml", status: int = 200):
        state["body"] = body
        state["content_type"] = content_type
        state["status"] = status
        return state

    set_body.state = state  # type: ignore[attr-defined]
    return set_body


# --------------------------------------------------------------------------- #
# 1. Sanity: the fake faithfully reproduces the original bug
# --------------------------------------------------------------------------- #


def test_fake_response_reproduces_latin1_default():
    """``text/yaml`` with no charset must resolve to ISO-8859-1, as in requests."""
    resp = FakeResponse(_spec_with(EM_DASH).encode("utf-8"), "text/yaml")
    assert resp.encoding in (None, "ISO-8859-1")
    # requests treats missing text/* charset as ISO-8859-1 for .text
    assert resp.text != _spec_with(EM_DASH), (
        ".text should be a mis-decode of the UTF-8 bytes, not the original string"
    )
    # The tell-tale U+0080 must be present in the mis-decoded text.
    assert "" in resp.text


def test_declared_utf8_charset_decodes_cleanly_in_fake():
    """When the server declares charset=utf-8, .text is already correct."""
    resp = FakeResponse(
        _spec_with(EM_DASH).encode("utf-8"), "text/yaml; charset=utf-8"
    )
    assert resp.encoding == "utf-8"
    assert resp.text == _spec_with(EM_DASH)


def test_pyyaml_would_reject_the_mis_decoded_text():
    """Prove the mis-decoded ``.text`` is what PyYAML rejects with #x0080.

    This is the "negative control": it demonstrates the bug still exists at the
    library boundary, so the passing loader tests below are meaningful.
    """
    import yaml

    resp = FakeResponse(_spec_with(EM_DASH).encode("utf-8"), "text/yaml")
    with pytest.raises(yaml.YAMLError) as exc:
        yaml.safe_load(resp.text)
    assert "#x0080" in str(exc.value) or "special characters" in str(exc.value)

    # And the correctly decoded bytes parse fine.
    assert yaml.safe_load(resp.content.decode("utf-8"))["openapi"] == "3.1.0"


# --------------------------------------------------------------------------- #
# 2. load_uri: encoding matrix
# --------------------------------------------------------------------------- #


def test_load_uri_returns_str(http_body):
    """The public contract: load_uri returns ``str`` (not bytes)."""
    http_body(_spec_with(EM_DASH).encode("utf-8"), "text/yaml")
    result = load_uri(TEST_URL, 5, 10)
    assert isinstance(result, str)


def test_load_uri_decodes_utf8_when_no_charset(http_body):
    """THE regression: text/yaml, no charset, UTF-8 em-dash -> clean string."""
    http_body(_spec_with(EM_DASH).encode("utf-8"), "text/yaml")
    result = load_uri(TEST_URL, 5, 10)
    assert EM_DASH in result
    assert "" not in result  # no Latin-1 corruption artifact
    assert result == _spec_with(EM_DASH)


@pytest.mark.parametrize("name,marker", sorted(NON_ASCII_SAMPLES.items()))
def test_load_uri_all_non_ascii_survive_missing_charset(http_body, name, marker):
    """Every non-ASCII sample must round-trip when charset is absent."""
    http_body(_spec_with(marker).encode("utf-8"), "text/yaml")
    result = load_uri(TEST_URL, 5, 10)
    assert marker in result, f"{name} corrupted"
    assert result == _spec_with(marker)


@pytest.mark.parametrize(
    "content_type",
    [
        "text/yaml",
        "text/yaml; charset=utf-8",
        "text/plain",
        "text/plain; charset=utf-8",
        "application/yaml",
        "application/x-yaml",
        "application/json",
        "application/openapi+yaml",
        "",  # no Content-Type header at all
    ],
)
def test_load_uri_content_type_matrix(http_body, content_type):
    """UTF-8 bytes decode correctly regardless of the declared media type.

    This is the core property: the transport charset (present, absent, or
    misleading) must never change the decode. All of these carry the same
    UTF-8 bytes and must yield the same clean string.
    """
    http_body(_spec_with(EM_DASH).encode("utf-8"), content_type)
    result = load_uri(TEST_URL, 5, 10)
    assert result == _spec_with(EM_DASH)


def test_load_uri_pure_ascii_unaffected(http_body):
    """Pure-ASCII specs (no charset) are unchanged (ASCII ⊂ UTF-8)."""
    ascii_spec = _spec_with("dash")
    http_body(ascii_spec.encode("utf-8"), "text/yaml")
    assert load_uri(TEST_URL, 5, 10) == ascii_spec


# --------------------------------------------------------------------------- #
# 3. BOM handling (why utf-8-sig, not plain utf-8)
# --------------------------------------------------------------------------- #


def test_load_uri_strips_utf8_bom(http_body):
    """A leading UTF-8 BOM must be stripped, not left as U+FEFF."""
    body = ("﻿" + _spec_with(EM_DASH)).encode("utf-8")  # EF BB BF prefix
    assert body[:3] == b"\xef\xbb\xbf"
    http_body(body, "text/yaml")
    result = load_uri(TEST_URL, 5, 10)
    assert not result.startswith("﻿")
    assert result == _spec_with(EM_DASH)


def test_load_uri_no_bom_still_clean(http_body):
    """Without a BOM, output is identical (utf-8-sig degrades to utf-8)."""
    body = _spec_with(EM_DASH).encode("utf-8")
    assert body[:3] != b"\xef\xbb\xbf"
    http_body(body, "text/yaml")
    assert load_uri(TEST_URL, 5, 10) == _spec_with(EM_DASH)


# --------------------------------------------------------------------------- #
# 4. End-to-end through every URL-loading backend
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("backend", YAML_URL_BACKENDS_DICT)
def test_parse_url_with_em_dash_dict_backends(http_body, backend):
    """Full parse() over HTTP: the exact reported failure, per dict backend.

    Before the fix this raised DocumentParseError wrapping
    'unacceptable character #x0080' for the pyyaml backend.
    """
    http_body(_spec_with(EM_DASH).encode("utf-8"), "text/yaml")
    parser = OpenAPIParser(backend)
    doc = parser.parse(TEST_URL)
    assert doc["openapi"] == "3.1.0"
    assert EM_DASH in doc["info"]["title"]


@pytest.mark.parametrize("backend", YAML_URL_BACKENDS)
def test_parse_url_em_dash_survives_all_url_backends(http_body, backend):
    """The em-dash round-trips through every URL-loading backend.

    Return representations differ (dict vs YAML node), so we assert on content
    survival, which is the property the encoding fix guarantees.
    """
    http_body(_spec_with(EM_DASH).encode("utf-8"), "text/yaml")
    doc = OpenAPIParser(backend).parse(TEST_URL)
    _assert_marker_present(doc, EM_DASH, context=backend)


@pytest.mark.parametrize("backend", YAML_URL_BACKENDS)
@pytest.mark.parametrize("name,marker", sorted(NON_ASCII_SAMPLES.items()))
def test_parse_url_non_ascii_all_backends(http_body, backend, name, marker):
    """Every non-ASCII sample parses via every URL backend, no charset."""
    http_body(_spec_with(marker).encode("utf-8"), "text/yaml")
    doc = OpenAPIParser(backend).parse(TEST_URL)
    _assert_marker_present(doc, marker, context=f"{name} via {backend}")


def test_public_load_uri_method_returns_str(http_body):
    """OpenAPIParser.load_uri() keeps its ``-> str`` public contract."""
    http_body(_spec_with(EM_DASH).encode("utf-8"), "text/yaml")
    parser = OpenAPIParser("pyyaml")
    result = parser.load_uri(TEST_URL)
    assert isinstance(result, str)
    assert result == _spec_with(EM_DASH)


# --------------------------------------------------------------------------- #
# 5. Local-file branches: regression guard (must remain UTF-8)
# --------------------------------------------------------------------------- #


def test_load_uri_local_file_utf8(tmp_path):
    """The file:// branch already decoded UTF-8; ensure it still does."""
    spec = _spec_with(EM_DASH)
    f = tmp_path / "openapi.yaml"
    f.write_text(spec, encoding="utf-8")
    result = load_uri(f.as_uri(), 5, 10)
    assert result == spec
    assert EM_DASH in result


def test_load_uri_local_path_utf8(tmp_path):
    """The bare-path branch (no scheme) also decodes UTF-8."""
    spec = _spec_with(EM_DASH)
    f = tmp_path / "openapi.yaml"
    f.write_text(spec, encoding="utf-8")
    result = load_uri(str(f), 5, 10)
    assert result == spec


def test_parse_local_file_matches_http(http_body, tmp_path):
    """A spec parsed from disk and from HTTP yields the same document."""
    spec = _spec_with(EM_DASH)
    f = tmp_path / "openapi.yaml"
    f.write_text(spec, encoding="utf-8")
    from_file = OpenAPIParser("pyyaml").parse(f.as_uri())

    http_body(spec.encode("utf-8"), "text/yaml")
    from_http = OpenAPIParser("pyyaml").parse(TEST_URL)
    assert from_file == from_http


# --------------------------------------------------------------------------- #
# 6. Error handling: failures still surface, wrapped correctly
# --------------------------------------------------------------------------- #


def test_load_uri_does_not_raise_on_http_error_status(http_body):
    """Document current behavior: the loader does NOT call ``raise_for_status``.

    ``load_uri`` reads ``resp.status_code`` only for a log line; it returns the
    response body regardless of status. A 404 page therefore comes back as
    content (and fails later at parse time, not load time). This test pins that
    behavior so the encoding fix is not confused with a status-handling change.
    Encoding is still correct: the returned body decodes as UTF-8.
    """
    http_body("not found —".encode("utf-8"), "text/plain", status=404)
    result = load_uri(TEST_URL, 5, 10)
    assert result == "not found —"  # decoded UTF-8, no Latin-1 corruption


def test_load_uri_network_error_wrapped(monkeypatch):
    """A transport exception is wrapped in DocumentLoadError."""

    def _boom(*a, **k):  # noqa: ANN002, ANN003
        raise requests.ConnectionError("dns failure")

    monkeypatch.setattr(loader_module.requests, "get", _boom)
    with pytest.raises(DocumentLoadError):
        load_uri(TEST_URL, 5, 10)


def test_load_uri_truly_undecodable_bytes_raise(http_body):
    """Bytes that are not valid UTF-8 at all raise (wrapped), not silently corrupt.

    A genuinely non-UTF-8 payload is not a conformant YAML stream; failing loudly
    is correct. This documents the intended boundary of the fix.
    """
    # 0xFF is never valid as a standalone UTF-8 byte.
    http_body(b"\xff\xfe not utf-8 at all", "text/yaml")
    with pytest.raises(DocumentLoadError):
        load_uri(TEST_URL, 5, 10)


def test_parse_url_undecodable_raises_document_parse_error(http_body):
    """Undecodable HTTP body surfaces as a DocumentParseError through parse()."""
    http_body(b"\xff\xff\xff", "text/yaml")
    with pytest.raises((DocumentParseError, DocumentLoadError)):
        OpenAPIParser("pyyaml").parse(TEST_URL)


# --------------------------------------------------------------------------- #
# 7. The loader does not depend on the response's own charset guess
# --------------------------------------------------------------------------- #


def test_loader_ignores_misleading_charset(http_body):
    """Even a *wrong* declared charset must not corrupt UTF-8 content.

    If a server lied and said charset=iso-8859-1 while sending UTF-8 bytes,
    the old ``.text`` path would corrupt the em-dash. The fix decodes UTF-8
    unconditionally, so the content survives.
    """
    http_body(_spec_with(EM_DASH).encode("utf-8"), "text/yaml; charset=iso-8859-1")
    result = load_uri(TEST_URL, 5, 10)
    assert result == _spec_with(EM_DASH)


def test_loader_reads_content_not_text(http_body, monkeypatch):
    """White-box guard: the loader must consume ``.content``, never ``.text``.

    Accessing ``.text`` is what applies the transport charset. We fail loudly
    if a future refactor reintroduces it on the HTTP path.
    """
    accessed: list[str] = []

    class TrackingResponse(FakeResponse):
        @property
        def text(self) -> str:  # noqa: D401
            accessed.append("text")
            return super().text

        @property
        def content(self) -> bytes:
            accessed.append("content")
            return super().content

    def _fake_get(url, *a, **k):  # noqa: ANN001, ANN002, ANN003
        return TrackingResponse(_spec_with(EM_DASH).encode("utf-8"), "text/yaml")

    monkeypatch.setattr(loader_module.requests, "get", _fake_get)
    load_uri(TEST_URL, 5, 10)
    assert "content" in accessed
    assert "text" not in accessed, "loader must not read resp.text (charset trap)"


# --------------------------------------------------------------------------- #
# 8. Logger plumbing (optional arg) still works
# --------------------------------------------------------------------------- #


def test_load_uri_accepts_explicit_logger(http_body):
    http_body(_spec_with(EM_DASH).encode("utf-8"), "text/yaml")
    logger = logging.getLogger("test.loader")
    result = load_uri(TEST_URL, 5, 10, logger)
    assert result == _spec_with(EM_DASH)
