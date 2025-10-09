import json
import logging
from collections.abc import Sequence
from typing import Any, Literal, Mapping

import yaml

from jentic.apitools.openapi.parser.backends.base import BaseParserBackend
from jentic.apitools.openapi.parser.core.uri import is_uri_like, load_uri


__all__ = ["PyYAMLParserBackend"]


class PyYAMLParserBackend(BaseParserBackend):
    def parse(self, document: str, *, logger: logging.Logger | None = None) -> Any:
        logger = logger or logging.getLogger(__name__)
        text = document
        try:
            if is_uri_like(document):
                logger.debug("Starting download of %s", document)
                text = load_uri(document, 5, 10, logger)

            data = self.parse_text(text)
        except Exception:
            msg = f"Unsupported document type: {type(document)!r}"
            logger.exception(msg)
            raise TypeError(msg)
        return data

    def parse_uri(self, uri: str, logger: logging.Logger | None = None) -> Any:
        return self.parse_text(load_uri(uri, 5, 10, logger))

    def parse_text(self, text: str, logger: logging.Logger | None = None) -> Any:
        logger = logger or logging.getLogger(__name__)
        try:
            data = yaml.safe_load(text)
            logger.debug("loaded YAML")
        except Exception:
            if isinstance(text, (bytes, str)):
                text = text.decode() if isinstance(text, bytes) else text
                data = json.loads(text)
                logger.debug("loaded JSON")
        if isinstance(data, Mapping):
            return dict(data)
        msg = f"Unsupported document type: {type(text)!r}"
        raise TypeError(msg)

    @staticmethod
    def accepts() -> Sequence[Literal["uri", "text"]]:
        """Return supported input formats.

        Returns:
            Sequence of supported document format identifiers:
            - "uri": File path or URI pointing to OpenAPI Document
            - "text": String (JSON/YAML) representation
        """
        return ["uri", "text"]
