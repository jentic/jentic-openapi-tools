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
            content = resp.text
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
