import logging
from collections.abc import Sequence
from typing import Literal

from ruamel.yaml import MappingNode, ScalarNode, SequenceNode

from jentic.apitools.openapi.common.uri import is_uri_like
from jentic.apitools.openapi.parser.backends.ruamel_roundtrip import RuamelRoundTripParserBackend
from jentic.apitools.openapi.parser.core.loader import load_uri


__all__ = [
    "RuamelASTParserBackend",
    # Re-export common YAML node types for convenience
    "MappingNode",
    "ScalarNode",
    "SequenceNode",
]


class RuamelASTParserBackend(RuamelRoundTripParserBackend):
    def parse(self, document: str, *, logger: logging.Logger | None = None) -> MappingNode:  # type: ignore[override]
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

    def _parse_uri(self, uri: str, logger: logging.Logger) -> MappingNode:  # type: ignore[override]
        logger.debug("Starting download of %s", uri)
        return self._parse_text(load_uri(uri, 5, 10, logger), logger)

    def _parse_text(self, text: str, logger: logging.Logger) -> MappingNode:  # type: ignore[override]
        if not isinstance(text, (bytes, str)):
            raise TypeError(f"Unsupported document type: {type(text)!r}")

        if isinstance(text, bytes):
            text = text.decode()

        node: MappingNode = self.yaml.compose(text)
        logger.debug("YAML document successfully parsed")

        if not isinstance(node, MappingNode):
            raise TypeError(f"Parsed YAML document is not a mapping: {type(node)!r}")

        return node
