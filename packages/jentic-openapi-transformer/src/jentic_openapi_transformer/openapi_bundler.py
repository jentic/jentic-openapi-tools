import importlib.metadata
from typing import Any, TypeVar, cast, overload, Mapping, Sequence
import json

from jentic_openapi_parser import OpenAPIParser
from .strategies.base import BaseBundlerStrategy
from .strategies.default_strategy import DefaultOpenAPIBundler

T = TypeVar("T")


class OpenAPIBundler:
    """
    Provides a bundler for OpenAPI specifications using customizable strategies.

    This class is designed to facilitate the bundling of OpenAPI documents.
    It supports multiple strategies and can be extended through plugins.
    When multiple strategies are used, the returned value is the result from the last strategy of the list that succeeds.
    This mechanism is designed to allow passing multiple strategies to the bundler and concur to the validation process
    by reporting the errors and success status from all strategies.

    Attributes:
        strategies (list[BaseParserStrategy]): List of strategies used by the bundler,
        each implementing the BaseBundlerStrategy interface.
    """

    def __init__(self, strategies: list | None = None, parser: OpenAPIParser | None = None):
        if not parser:
            parser = OpenAPIParser()
        self.parser = parser
        # If no strategies specified, use default
        if not strategies:
            strategies = ["default"]
        self.strategies = []  # list of BaseBundlerStrategy instances

        # Discover entry points for bundler plugins
        # (This could be a one-time load stored at class level to avoid doing it every time)
        eps = importlib.metadata.entry_points(group="jentic.openapi_bundler_strategies")
        plugin_map = {ep.name: ep for ep in eps}

        for strat in strategies:
            if isinstance(strat, str):
                name = strat
                if name == "default":
                    # Use built-in default bundler (TODO NOOP atm)
                    self.strategies.append(DefaultOpenAPIBundler())
                elif name in plugin_map:
                    plugin_class = plugin_map[name].load()  # loads the class
                    self.strategies.append(plugin_class())
                else:
                    raise ValueError(f"No bundler plugin named '{name}' found")
            elif isinstance(strat, BaseBundlerStrategy):
                self.strategies.append(strat)
            elif hasattr(strat, "__call__") and issubclass(strat, BaseBundlerStrategy):
                # if a class (not instance) is passed
                self.strategies.append(strat())
            else:
                raise TypeError("Invalid strategy type: must be name or strategy class/instance")

    @overload
    def bundle(
        self,
        source: str | dict,
        base_url: str | None = None,
        *,
        return_type: type[str],
        strict: bool = False,
    ) -> str: ...

    @overload
    def bundle(
        self,
        source: str | dict,
        base_url: str | None = None,
        *,
        return_type: type[dict[str, Any]],
        strict: bool = False,
    ) -> dict[str, Any]: ...

    @overload
    def bundle(
        self,
        source: str | dict,
        base_url: str | None = None,
        *,
        return_type: type[T],
        strict: bool = False,
    ) -> T: ...

    def bundle(
        self,
        source: str | dict,
        base_url: str | None = None,
        *,
        return_type: type[T] | None = None,
        strict: bool = False,
    ) -> Any:
        raw = self._bundle(source, base_url)

        if return_type is None:
            return self._to_plain(raw)

        # Handle conversion to string type
        if return_type is str and not isinstance(raw, str):
            if isinstance(raw, (dict, list)):
                return cast(T, json.dumps(raw))
            else:
                return cast(T, str(raw))

        # Handle conversion from string to dict type
        if return_type is dict and isinstance(raw, str):
            try:
                return cast(T, json.loads(raw))
            except json.JSONDecodeError:
                if strict:
                    raise ValueError(f"Cannot parse string as JSON: {raw}")
                return cast(T, raw)

        if strict:
            if not isinstance(raw, return_type):
                raise TypeError(
                    f"Expected {getattr(return_type, '__name__', return_type)}, "
                    f"got {type(raw).__name__}"
                )
        return cast(T, raw)

    def _bundle(self, source: str | dict, base_url: str | None = None) -> Any:
        text = source
        data = None
        result = None
        if isinstance(source, str):
            is_uri = self.parser.is_uri_like(source)
            is_text = not is_uri

            if is_text:
                data = self.parser.parse(source)

            if is_uri and self.has_non_uri_strategy():
                text = self.parser.load_uri(source)
                if not data or data is None:
                    data = self.parser.parse(text)
        else:
            is_uri = False
        if not data or data is None:
            data = text

        for strat in self.strategies:
            document = None
            if is_uri and "uri" in strat.accepts():
                document = source
            elif is_uri and "text" in strat.accepts():
                document = text
            elif is_uri and "dict" in strat.accepts():
                document = data
            elif not is_uri and "text" in strat.accepts():
                document = text
            elif not is_uri and "dict" in strat.accepts():
                document = data

            if document is not None:
                try:
                    result = strat.bundle(document)
                except Exception as e:
                    # TODO add to parser/validation chain result
                    print(f"Error parsing document: {e}")
        if result is None:
            raise ValueError("No valid document found")
        return result

    def has_non_uri_strategy(self) -> bool:
        """Check if any strategy accepts 'text' or 'dict' but not 'uri'."""
        for strat in self.strategies:
            accepted = strat.accepts()
            if ("text" in accepted or "dict" in accepted) and "uri" not in accepted:
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
