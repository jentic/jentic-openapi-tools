import logging
from collections.abc import Sequence
from typing import Literal

from ruamel.yaml import MappingNode

from jentic.apitools.openapi.common.uri import is_uri_like
from jentic.apitools.openapi.datamodels.low.sources import ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import build as build_v30
from jentic.apitools.openapi.datamodels.low.v30.openapi import OpenAPI30
from jentic.apitools.openapi.datamodels.low.v31 import build as build_v31
from jentic.apitools.openapi.datamodels.low.v31.openapi import OpenAPI31
from jentic.apitools.openapi.parser.backends.base import BaseParserBackend
from jentic.apitools.openapi.parser.backends.ruamel_ast import RuamelASTParserBackend
from jentic.apitools.openapi.parser.core.loader import load_uri


__all__ = ["DatamodelLowParserBackend"]


class DatamodelLowParserBackend(BaseParserBackend):
    """Parser backend that returns low-level OpenAPI datamodels.

    This backend uses the RuamelASTParserBackend to parse YAML documents into
    AST nodes, then automatically detects the OpenAPI version and builds the
    appropriate low-level datamodel (OpenAPI 3.0 or 3.1).

    The returned datamodels preserve all source location information from the
    original YAML document, enabling precise error reporting and validation.

    Supported versions:
    - OpenAPI 3.0.x → returns OpenAPI30 datamodel
    - OpenAPI 3.1.x → returns OpenAPI31 datamodel

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

    def parse(
        self, document: str, *, logger: logging.Logger | None = None
    ) -> OpenAPI30 | OpenAPI31 | ValueSource:
        """Parse an OpenAPI document and return the appropriate datamodel.

        Args:
            document: URI/path to OpenAPI document, or YAML/JSON string
            logger: Optional logger for diagnostic messages

        Returns:
            OpenAPI30 or OpenAPI31 datamodel depending on document version,
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

    def _parse_uri(self, uri: str, logger: logging.Logger) -> OpenAPI30 | OpenAPI31 | ValueSource:
        """Parse an OpenAPI document from a URI."""
        logger.debug("Starting download of %s", uri)
        return self._parse_text(load_uri(uri, 5, 10, logger), logger)

    def _parse_text(self, text: str, logger: logging.Logger) -> OpenAPI30 | OpenAPI31 | ValueSource:
        """Parse an OpenAPI document from text."""
        # Parse to AST first
        ast_node: MappingNode = self._ast_backend.parse(text, logger=logger)

        # Detect version
        try:
            major, minor = self._detect_version(ast_node)
        except ValueError as e:
            logger.error("Failed to detect OpenAPI version: %s", e)
            raise

        # Route to appropriate builder
        if major == "3" and minor == "0":
            logger.debug("Building OpenAPI 3.0.x datamodel")
            return build_v30(ast_node)
        elif major == "3" and minor == "1":
            logger.debug("Building OpenAPI 3.1.x datamodel")
            return build_v31(ast_node)
        else:
            raise ValueError(
                f"Unsupported OpenAPI version: {major}.{minor}.x. Supported versions: 3.0.x, 3.1.x"
            )

    def _detect_version(self, node: MappingNode) -> tuple[str, str]:
        """Detect OpenAPI version from AST node.

        Args:
            node: The root MappingNode of the parsed document

        Returns:
            Tuple of (major, minor) version strings, e.g. ("3", "0")

        Raises:
            ValueError: If openapi field is missing or has invalid format
        """
        # Find openapi field in root node
        for key_node, value_node in node.value:
            if key_node.value == "openapi":
                version_str = value_node.value

                if not isinstance(version_str, str):
                    raise ValueError(
                        f"Invalid openapi field type: {type(version_str).__name__}. "
                        f"Expected string."
                    )

                # Handle version suffixes like "3.0.0-rc1" or "3.1.2-beta"
                base_version = version_str.split("-")[0]

                # Parse major.minor.patch
                parts = base_version.split(".")
                if len(parts) < 2:
                    raise ValueError(
                        f"Invalid openapi version format: '{version_str}'. "
                        f"Expected format: 'major.minor.patch'"
                    )

                return (parts[0], parts[1])

        # openapi field not found
        raise ValueError(
            "Missing required 'openapi' field in document. "
            "This does not appear to be a valid OpenAPI document."
        )
