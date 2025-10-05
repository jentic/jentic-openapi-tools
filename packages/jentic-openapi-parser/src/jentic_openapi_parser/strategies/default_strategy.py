import logging
from typing import Any, Mapping
import yaml
import json
from .base import BaseParserStrategy
from ..uri import is_uri_like, load_uri


class DefaultOpenAPIParser(BaseParserStrategy):
    def parse(self, source: str, logger: logging.Logger | None = None) -> Any:
        logger = logger or logging.getLogger(__name__)
        text = source
        try:
            if is_uri_like(source):
                logger.debug("Starting download of %s", source)
                text = load_uri(source, 5, 10, logger)

            data = self.parse_text(text)
        except Exception as e:
            src = f"{type(source)!r}" if not is_uri_like(source) else source
            msg = f"Error parsing with default strategy type: {src}"
            logger.exception(msg)
            raise e

        return data

    def parse_uri(self, uri: str, logger: logging.Logger | None = None) -> Any:
        return self.parse_text(load_uri(uri, 5, 10, logger))

    def parse_text(self, text: str, logger: logging.Logger | None = None) -> Any:
        logger = logger or logging.getLogger(__name__)
        try:
            logger.debug("loading YAML")
            data = yaml.safe_load(text)
            logger.debug("loaded YAML")
        except Exception:
            if isinstance(text, (bytes, str)):
                logger.debug("decoding JSON")
                text = text.decode() if isinstance(text, bytes) else text
                logger.debug("loading JSON")
                data = json.loads(text)
                logger.debug("loaded JSON")
        if isinstance(data, Mapping):
            return dict(data)
        msg = f"Unsupported document type: {type(text)!r}"
        raise TypeError(msg)

    def accepts(self) -> list[str]:
        return ["uri", "text"]
