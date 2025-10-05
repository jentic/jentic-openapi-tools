import importlib.metadata
from typing import Any, TypeVar, cast, overload, Mapping, Sequence, Type
import json

from jentic_openapi_parser import OpenAPIParser
from .strategies.base import BaseBundlerStrategy
from .strategies.default_strategy import DefaultOpenAPIBundler

T = TypeVar("T")


class OpenAPIBundler:
    """
    Provides a bundler for OpenAPI specifications using customizable strategies.

    This class is designed to facilitate the bundling of OpenAPI documents.
    It supports one strategy at a time and can be extended through plugins.

    Attributes:
        strategy: Strategy used by the parser implementing the BaseBundlerStrategy interface.
    """

    def __init__(
        self,
        strategy: str | BaseBundlerStrategy | Type[BaseBundlerStrategy] | None = None,
        parser: OpenAPIParser | None = None,
    ):
        if not parser:
            parser = OpenAPIParser()
        self.parser = parser
        # If no strategy specified, use default
        if not strategy:
            strategy = "default"

        # Discover entry points for bundler plugins
        # (This could be a one-time load stored at class level to avoid doing it every time)
        eps = importlib.metadata.entry_points(group="jentic.openapi_bundler_strategies")
        plugin_map = {ep.name: ep for ep in eps}

        if isinstance(strategy, str):
            name = strategy
            if name == "default":
                # Use built-in default bundler (TODO NOOP atm)
                self.strategy = DefaultOpenAPIBundler()
            elif name in plugin_map:
                plugin_class = plugin_map[name].load()  # loads the class
                self.strategy = plugin_class()
            else:
                raise ValueError(f"No bundler plugin named '{name}' found")
        elif isinstance(strategy, BaseBundlerStrategy):
            self.strategy = strategy
        elif hasattr(strategy, "__call__") and issubclass(strategy, BaseBundlerStrategy):
            # if a class (not instance) is passed
            self.strategy = strategy()
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

        document = None
        if is_uri and "uri" in self.strategy.accepts():
            document = source
        elif is_uri and "text" in self.strategy.accepts():
            document = text
        elif is_uri and "dict" in self.strategy.accepts():
            document = data
        elif not is_uri and "text" in self.strategy.accepts():
            document = text
        elif not is_uri and "dict" in self.strategy.accepts():
            document = data

        if document is not None:
            try:
                result = self.strategy.bundle(document, base_url)
            except Exception as e:
                print(f"Error parsing document: {e}")
                raise e

        if result is None:
            raise ValueError("No valid document found")
        return result

    def has_non_uri_strategy(self) -> bool:
        """Check if any strategy accepts 'text' or 'dict' but not 'uri'."""
        accepted = self.strategy.accepts()
        return ("text" in accepted or "dict" in accepted) and "uri" not in accepted

    def _to_plain(self, obj: Any) -> Any:
        # Mapping?
        if isinstance(obj, Mapping):
            return {k: self._to_plain(v) for k, v in obj.items()}

        # Sequence but NOT str/bytes
        if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray)):
            return [self._to_plain(x) for x in obj]

        # Scalar
        return obj
