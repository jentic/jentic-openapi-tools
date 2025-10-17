import logging
from collections.abc import Sequence
from typing import Literal, Mapping

from ruamel.yaml import YAML, CommentedMap

from jentic.apitools.openapi.common.uri import is_uri_like
from jentic.apitools.openapi.parser.backends.base import BaseParserBackend
from jentic.apitools.openapi.parser.core.loader import load_uri


__all__ = ["RuamelSafeParserBackend"]


class RuamelSafeParserBackend(BaseParserBackend):
    def __init__(self, typ: str = "safe", pure: bool = True):
        self.yaml = YAML(typ=typ, pure=pure)
        self.yaml.default_flow_style = False

    def parse(self, document: str, *, logger: logging.Logger | None = None) -> CommentedMap:
        logger = logger or logging.getLogger(__name__)
        if is_uri_like(document):
            return self._parse_uri(document, logger)
        return self._parse_text(document, logger)

    @staticmethod
    def accepts() -> Sequence[Literal["uri", "text"]]:
        """Return supported input formats.

        Returns:
            Sequence of supported document format identifiers:
            - "uri": File path or URI pointing to OpenAPI Document
            - "text": String (JSON/YAML) representation
        """
        return ["uri", "text"]

    def _parse_uri(self, uri: str, logger: logging.Logger) -> CommentedMap:
        logger.debug("Starting download of %s", uri)
        return self._parse_text(load_uri(uri, 5, 10, logger), logger)

    def _parse_text(self, text: str, logger: logging.Logger) -> CommentedMap:
        if not isinstance(text, (bytes, str)):
            raise TypeError(f"Unsupported document type: {type(text)!r}")

        if isinstance(text, bytes):
            text = text.decode()

        data: CommentedMap = self.yaml.load(text)
        logger.debug("YAML document successfully parsed")

        if not isinstance(data, Mapping):
            raise TypeError(f"Parsed YAML document is not a mapping: {type(data)!r}")

        return data
