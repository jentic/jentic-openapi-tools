"""Document loading utilities for OpenAPI parser."""

import logging

import requests

from jentic.apitools.openapi.common.uri import is_file_uri, is_http_https_url, resolve_to_absolute

from .exceptions import DocumentLoadError


__all__ = ["load_uri"]


def load_uri(
    uri: str, conn_timeout: int, read_timeout: int, logger: logging.Logger | None = None
) -> str:
    logger = logger or logging.getLogger(__name__)
    resolved_uri = resolve_to_absolute(uri)
    content = ""

    try:
        if is_http_https_url(resolved_uri):
            logger.info("Loading URI %s", resolved_uri)
            resp = requests.get(resolved_uri, timeout=(conn_timeout, read_timeout))
            logger.info(
                "Load of URI %s completed, status: %s, content length: %s",
                resolved_uri,
                resp.status_code,
                len(resp.content),
            )
            # Decode as UTF-8 rather than trusting ``resp.text``. For a
            # ``text/*`` response with no ``charset`` parameter, requests
            # follows the legacy RFC 2616 default and decodes as ISO-8859-1;
            # that corrupts UTF-8 multibyte characters (e.g. an em-dash's
            # ``E2 80 94`` becomes chars including U+0080, which the YAML
            # reader rejects with "unacceptable character #x0080"). A YAML
            # stream is UTF-8/16/32 by definition (YAML spec §5.2), so the
            # transport charset must not get a vote. ``utf-8-sig`` also
            # strips a leading UTF-8 BOM if present. This mirrors the
            # ``encoding="utf-8"`` used by the local-file branches below.
            content = resp.content.decode("utf-8-sig")
        elif is_file_uri(resolved_uri):
            logger.info("Loading local file %s", resolved_uri)
            with open(resolved_uri, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            # Treat as local file path
            logger.info("Loading local file %s", resolved_uri)
            with open(resolved_uri, "r", encoding="utf-8") as f:
                content = f.read()
    except Exception as e:
        raise DocumentLoadError(f"Failed to load URI '{uri}': {e}") from e

    return content
