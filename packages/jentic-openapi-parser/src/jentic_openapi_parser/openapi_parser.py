import importlib.metadata
from typing import Any, TypeVar, cast, Optional, overload, Mapping, Sequence

from .uri import is_uri_like, load_uri
from .strategies.base import BaseParserStrategy
from .strategies.default_strategy import DefaultOpenAPIParser
from .strategies.ruamel_strategy import RuamelOpenAPIParser
from .strategies.ruamel_roundtrip_strategy import RuamelRoundTripOpenAPIParser

T = TypeVar("T")


class OpenAPIParser:
    """
    Provides a parser for OpenAPI specifications using customizable strategies.

    This class is designed to facilitate the parsing of OpenAPI documents.
    It supports multiple strategies and can be extended through plugins.
    When multiple strategies are used, the returned value is the result from the last strategy of the list that succeeds.
    This mechanism is designed to allow passing multiple strategies to the parser and concur to the validation process
    by reporting the errors and success status from all strategies.

    Attributes:
        strategies (list[BaseParserStrategy]): List of strategies used by the parser,
        each implementing the BaseParserStrategy interface.
    """

    def __init__(self, strategies: list | None = None):
        # If no strategies specified, use default
        if not strategies:
            strategies = ["default"]
        self.strategies = []  # list of BaseParserStrategy instances

        # Discover entry points for parser plugins
        # (This could be a one-time load stored at class level to avoid doing it every time)
        eps = importlib.metadata.entry_points(group="jentic.openapi_parser_strategies")
        plugin_map = {ep.name: ep for ep in eps}

        for strat in strategies:
            if isinstance(strat, str):
                name = strat
                if name == "default":
                    # Use built-in default parser
                    self.strategies.append(DefaultOpenAPIParser())
                elif name == "ruamel":
                    # Use built-in ruamel parser
                    self.strategies.append(RuamelOpenAPIParser())
                elif name == "ruamel-rt":
                    # Use built-in ruamel roundtrip parser
                    self.strategies.append(RuamelRoundTripOpenAPIParser())
                elif name in plugin_map:
                    plugin_class = plugin_map[name].load()  # loads the class
                    self.strategies.append(plugin_class())
                else:
                    raise ValueError(f"No parser plugin named '{name}' found")
            elif isinstance(strat, BaseParserStrategy):
                self.strategies.append(strat)
            elif hasattr(strat, "__call__") and issubclass(strat, BaseParserStrategy):
                # if a class (not instance) is passed
                self.strategies.append(strat())
            else:
                raise TypeError("Invalid strategy type: must be name or strategy class/instance")

    @overload
    def parse(self, source: str) -> dict[str, Any]: ...

    @overload
    def parse(self, source: str, *, return_type: type[T], strict: bool = False) -> T: ...

    def parse(
        self, source: str, *, return_type: type[T] | None = None, strict: bool = False
    ) -> Any:
        raw = self._parse(source)

        if return_type is None:
            return self._to_plain(raw)

        if strict:
            if not isinstance(raw, return_type):
                raise TypeError(
                    f"Expected {getattr(return_type, '__name__', return_type)}, "
                    f"got {type(raw).__name__}"
                )
        return cast(T, raw)

    def _parse(self, source: str) -> Any:
        text = source
        is_uri = is_uri_like(source)
        result = None
        if is_uri and self.has_non_uri_strategy():
            text = load_uri(source)
        for strat in self.strategies:
            document = None
            if is_uri and "uri" in strat.accepts():
                document = source
            elif is_uri and "text" in strat.accepts():
                document = text
            elif not is_uri and "text" in strat.accepts():
                document = text

            if document is not None:
                try:
                    result = strat.parse(document)
                except Exception as e:
                    # TODO add to parser/validation chain result
                    print(f"Error parsing document: {e}")
        if result is None:
            raise ValueError("No valid document found")
        return result

    def has_non_uri_strategy(self) -> bool:
        """Check if any strategy accepts 'text' but not 'uri'."""
        for strat in self.strategies:
            accepted = strat.accepts()
            if "text" in accepted and "uri" not in accepted:
                return True
        return False

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

    @staticmethod
    def load_uri(uri: str) -> str:
        return load_uri(uri)
