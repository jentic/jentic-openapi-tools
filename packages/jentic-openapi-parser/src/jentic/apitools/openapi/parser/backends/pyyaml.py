import json
import logging
from typing import Any, Mapping

import yaml
from jentic.apitools.openapi.parser.backends.base import BaseParserBackend
from jentic.apitools.openapi.parser.core.uri import is_uri_like, load_uri

__all__ = ["PyYAMLParserBackend"]


class PyYAMLParserBackend(BaseParserBackend):
    def parse(self, source: str, *, logger: logging.Logger | None = None) -> Any:
        logger = logger or logging.getLogger(__name__)
        text = source
        try:
            if is_uri_like(source):
                logger.debug("Starting download of %s", source)
                text = load_uri(source, 5, 10, logger)

            data = self.parse_text(text)
        except Exception:
            msg = f"Unsupported document type: {type(source)!r}"
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

    def accepts(self) -> list[str]:
        return ["uri", "text"]
