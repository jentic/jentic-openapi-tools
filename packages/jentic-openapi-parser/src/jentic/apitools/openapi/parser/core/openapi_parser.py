import importlib.metadata
import logging
from typing import Any, TypeVar, cast, Optional, overload, Mapping, Sequence, Type

from .uri import is_uri_like, load_uri
from .exceptions import (
    OpenAPIParserError,
    DocumentParseError,
    InvalidStrategyError,
    StrategyNotFoundError,
    TypeConversionError,
)
from ..strategies.base import BaseParserStrategy
from ..strategies.default_strategy import DefaultOpenAPIParser
from ..strategies.ruamel_strategy import RuamelOpenAPIParser
from ..strategies.ruamel_roundtrip_strategy import RuamelRoundTripOpenAPIParser

T = TypeVar("T")


class OpenAPIParser:
    """
    Provides a parser for OpenAPI specifications using customizable strategies.

    This class is designed to facilitate the parsing of OpenAPI documents.
    It supports one strategy at a time and can be extended through plugins.

    Attributes:
        strategy: Strategy used by the parser implementing the BaseParserStrategy interface.
        logger: Logger instance.
        conn_timeout: Connection timeout in seconds.
        read_timeout: Read timeout in seconds.
    """

    def __init__(
        self,
        strategy: str | BaseParserStrategy | Type[BaseParserStrategy] | None = None,
        *,
        logger: logging.Logger | None = None,
        conn_timeout: int = 5,
        read_timeout: int = 10,
    ):
        logger = logger or logging.getLogger(__name__)
        # If no strategy specified, use default
        if not strategy:
            strategy = "default"
        self.logger = logger
        self.conn_timeout = conn_timeout
        self.read_timeout = read_timeout

        try:
            # Discover entry points for parser plugins
            # TODO(francesco@jentic.com): This could be a one-time load stored at class level to avoid doing it every time
            eps = importlib.metadata.entry_points(group="jentic.apitools.openapi.parser.strategies")
            plugin_map = {ep.name: ep for ep in eps}
        except Exception as e:
            self.logger.warning(f"Failed to load plugin entry points: {e}")
            plugin_map = {}

        if isinstance(strategy, str):
            name = strategy

            try:
                if name == "default":
                    # Use built-in default parser
                    logger.debug("using default parser")
                    self.strategy = DefaultOpenAPIParser()
                elif name == "ruamel":
                    # Use built-in ruamel parser
                    logger.debug("using ruamel parser")
                    self.strategy = RuamelOpenAPIParser()
                elif name == "ruamel-rt":
                    # Use built-in ruamel roundtrip parser
                    logger.debug("using ruamel roundtrip parser")
                    self.strategy = RuamelRoundTripOpenAPIParser()
                elif name in plugin_map:
                    try:
                        logger.debug(f"using parser plugin '{name}'")
                        plugin_class = plugin_map[name].load()  # loads the class
                        self.strategy = plugin_class()
                    except Exception as e:
                        raise InvalidStrategyError(
                            f"Failed to load parser plugin '{name}': {e}"
                        ) from e
                else:
                    logger.error(f"No parser plugin named '{name}' found")
                    raise StrategyNotFoundError(f"No parser plugin named '{name}' found")
            except OpenAPIParserError:
                raise
            except Exception as e:
                raise InvalidStrategyError(f"Error initializing strategy '{name}': {e}") from e

        elif isinstance(strategy, BaseParserStrategy):
            logger.debug(f"using strategy '{type[strategy]}'")
            self.strategy = strategy
        elif hasattr(strategy, "__call__") and issubclass(strategy, BaseParserStrategy):
            try:
                # if a class (not instance) is passed
                self.strategy = strategy()
                logger.debug(f"using strategy '{type[strategy]}'")
            except Exception as e:
                raise InvalidStrategyError(
                    f"Failed to instantiate strategy class '{strategy.__name__}': {e}"
                ) from e

        else:
            logger.error("Invalid strategy type: must be name or strategy class/instance")
            raise InvalidStrategyError(
                "Invalid strategy type: must be a strategy name (str), "
                "BaseParserStrategy instance, or BaseParserStrategy class"
            )

    @overload
    def parse(self, source: str) -> dict[str, Any]: ...

    @overload
    def parse(self, source: str, *, return_type: type[T], strict: bool = False) -> T: ...

    def parse(
        self, source: str, *, return_type: type[T] | None = None, strict: bool = False
    ) -> Any:
        try:
            raw = self._parse(source)
        except OpenAPIParserError:
            raise
        except Exception as e:
            raise DocumentParseError(f"Unexpected error during parsing: {e}") from e

        if return_type is None:
            return self._to_plain(raw)

        if strict:
            if not isinstance(raw, return_type):
                msg = f"Expected {getattr(return_type, '__name__', return_type)}, got {type(raw).__name__}"
                self.logger.error(msg)
                raise TypeConversionError(msg)
        return cast(T, raw)

    def _parse(self, source: str) -> Any:
        text = source
        is_uri = is_uri_like(source)
        self.logger.debug(f"parsing a '{'uri' if is_uri else 'text'}'")
        result = None
        if is_uri and self.has_non_uri_strategy():
            text = self.load_uri(source)

        document = None
        if is_uri and "uri" in self.strategy.accepts():
            document = source
        elif is_uri and "text" in self.strategy.accepts():
            document = text
        elif not is_uri and "text" in self.strategy.accepts():
            document = text

        if document is None:
            accepted_formats = ", ".join(self.strategy.accepts())
            source_type = "URI" if is_uri else "text"
            raise DocumentParseError(
                f"Strategy '{type(self.strategy).__name__}' does not accept {source_type} format. "
                f"Accepted formats: {accepted_formats}"
            )

        try:
            result = self.strategy.parse(document, self.logger)
        except Exception as e:
            # Log the original error and wrap it
            msg = f"Failed to parse document with strategy '{type(self.strategy).__name__}': {e}"
            self.logger.error(msg)
            raise DocumentParseError(msg) from e

        if result is None:
            msg = "No valid document found"
            self.logger.error(msg)
            raise DocumentParseError(msg)
        return result

    def has_non_uri_strategy(self) -> bool:
        """Check if any strategy accepts 'text' but not 'uri'."""
        accepted = self.strategy.accepts()
        return "text" in accepted and "uri" not in accepted

    def _to_plain(self, obj: Any) -> Any:
        # Mapping?
        if isinstance(obj, Mapping):
            return {k: self._to_plain(v) for k, v in obj.items()}

        # Sequence but NOT str/bytes
        if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray)):
            return [self._to_plain(x) for x in obj]

        # Scalar
        return obj

    @staticmethod
    def is_uri_like(s: Optional[str]) -> bool:
        return is_uri_like(s)

    def load_uri(self, uri: str) -> str:
        return load_uri(uri, self.conn_timeout, self.read_timeout, self.logger)
