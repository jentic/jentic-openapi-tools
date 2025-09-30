import json
import importlib.metadata
from typing import Any, TypeVar, cast, overload, Mapping, Sequence, Type

from jentic.apitools.openapi.parser.core import OpenAPIParser
from jentic.apitools.openapi.transformer.bundler.backends.base import BaseBundlerBackend

T = TypeVar("T")


class OpenAPIBundler:
    """
    Provides a bundler for OpenAPI specifications using customizable backends.

    This class is designed to facilitate the bundling of OpenAPI documents.
    It supports one backend at a time and can be extended through backends.

    Attributes:
        backend: Backend used by the parser implementing the BaseBundlerBackend interface.
    """

    def __init__(
        self,
        backend: str | BaseBundlerBackend | Type[BaseBundlerBackend] | None = None,
        parser: OpenAPIParser | None = None,
    ):
        self.parser = parser if parser else OpenAPIParser()
        backend = backend if backend else "default"

        # Discover entry points for bundler backends
        eps = importlib.metadata.entry_points(
            group="jentic.apitools.openapi.transformer.bundler.backends"
        )
        backends = {ep.name: ep for ep in eps}

        if isinstance(backend, str):
            if backend in backends:
                backend_class = backends[backend].load()  # loads the class
                self.backend = backend_class()
            else:
                raise ValueError(f"No bundler backend named '{backend}' found")
        elif isinstance(backend, BaseBundlerBackend):
            self.backend = backend
        elif isinstance(backend, type) and issubclass(backend, BaseBundlerBackend):
            # if a class (not instance) is passed
            self.backend = backend()
        else:
            raise TypeError("Invalid backend type: must be name or backend class/instance")

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

        # Handle conversion to a string type
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

            if is_uri and self.has_non_uri_backend():
                text = self.parser.load_uri(source)
                if not data or data is None:
                    data = self.parser.parse(text)
        else:
            is_uri = False

        data = text if not data or data is None else data

        document = None
        if is_uri and "uri" in self.backend.accepts():
            document = source
        elif is_uri and "text" in self.backend.accepts():
            document = text
        elif is_uri and "dict" in self.backend.accepts():
            document = data
        elif not is_uri and "text" in self.backend.accepts():
            document = text
        elif not is_uri and "dict" in self.backend.accepts():
            document = data

        if document is not None:
            try:
                result = self.backend.bundle(document)
            except Exception as e:
                # TODO(fracensco@jentic.com): Add to parser/validation chain result
                print(f"Error parsing document: {e}")

        if result is None:
            raise ValueError("No valid document found")
        return result

    def has_non_uri_backend(self) -> bool:
        """Check if any backend accepts 'text' or 'dict' but not 'uri'."""
        accepted = self.backend.accepts()
        return ("text" in accepted or "dict" in accepted) and "uri" not in accepted

    def _to_plain(self, value: Any) -> Any:
        # Mapping
        if isinstance(value, Mapping):
            return {k: self._to_plain(v) for k, v in value.items()}

        # Sequence but NOT str/bytes
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return [self._to_plain(x) for x in value]

        # Scalar
        return value
