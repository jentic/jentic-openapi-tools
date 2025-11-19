import logging
from collections.abc import Sequence
from typing import Literal, TypeAlias

from ruamel.yaml import Node

from jentic.apitools.openapi.common.uri import is_uri_like
from jentic.apitools.openapi.common.version_detection import is_openapi_30, is_openapi_31
from jentic.apitools.openapi.datamodels.low.sources import ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import build as build_v30
from jentic.apitools.openapi.datamodels.low.v30.openapi import OpenAPI30
from jentic.apitools.openapi.datamodels.low.v31 import build as build_v31
from jentic.apitools.openapi.datamodels.low.v31.openapi import OpenAPI31
from jentic.apitools.openapi.parser.backends.base import BaseParserBackend
from jentic.apitools.openapi.parser.backends.ruamel_ast import RuamelASTParserBackend
from jentic.apitools.openapi.parser.core.loader import load_uri


# Type alias for the datamodel-low return type
DataModelLow: TypeAlias = OpenAPI30 | OpenAPI31 | ValueSource


__all__ = ["DataModelLowParserBackend", "DataModelLow"]


class DataModelLowParserBackend(BaseParserBackend):
    """Parser backend that returns low-level OpenAPI datamodels.

    This backend uses the RuamelASTParserBackend to parse YAML documents into
    AST nodes, then automatically detects the OpenAPI version and builds the
    appropriate low-level data model (OpenAPI 3.0 or 3.1).

    The returned datamodels preserve all source location information from the
    original YAML document, enabling precise error reporting and validation.

    Supported versions:
    - OpenAPI 3.0.x → returns OpenAPI30 data model
    - OpenAPI 3.1.x → returns OpenAPI31 data model

    Unsupported versions (raises ValueError):
    - OpenAPI 2.0 (Swagger)
    - OpenAPI 3.2.x (not yet released/supported)
    - Any other version
    """

    def __init__(self, pure: bool = True):
        """Initialize the datamodel-low parser backend.

        Args:
            pure: Whether to use pure Python YAML implementation (default: True).
                  Set to False to use libyaml if available for better performance.
        """
        self._ast_backend = RuamelASTParserBackend(pure=pure)

    def parse(self, document: str, *, logger: logging.Logger | None = None) -> DataModelLow:
        """Parse an OpenAPI document and return the appropriate data model.

        Args:
            document: URI/path to OpenAPI document, or YAML/JSON string
            logger: Optional logger for diagnostic messages

        Returns:
            OpenAPI30 or OpenAPI31 data model depending on document version,
            or ValueSource if the document is invalid

        Raises:
            ValueError: If OpenAPI version is unsupported (2.0, 3.2, etc.)
        """
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

    def _parse_uri(self, uri: str, logger: logging.Logger) -> DataModelLow:
        """Parse an OpenAPI document from a URI."""
        logger.debug("Starting download of %s", uri)
        return self._parse_text(load_uri(uri, 5, 10, logger), logger)

    def _parse_text(self, text: str, logger: logging.Logger) -> DataModelLow:
        """Parse an OpenAPI document from text."""
        if is_openapi_30(text):
            logger.debug("Building OpenAPI 3.0.x data model")
            ast_node: Node = self._ast_backend.parse(text, logger=logger)
            return build_v30(ast_node)
        elif is_openapi_31(text):
            logger.debug("Building OpenAPI 3.1.x data model")
            ast_node: Node = self._ast_backend.parse(text, logger=logger)
            return build_v31(ast_node)
        else:
            raise ValueError("Unsupported OpenAPI version. Supported versions: 3.0.x, 3.1.x")
