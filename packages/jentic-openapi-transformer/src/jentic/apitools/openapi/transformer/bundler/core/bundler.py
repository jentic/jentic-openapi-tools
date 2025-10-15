import importlib.metadata
import json
import logging
import warnings
from typing import Any, Mapping, Sequence, Type, TypeVar, cast, overload

from jentic.apitools.openapi.parser.core import OpenAPIParser
from jentic.apitools.openapi.transformer.bundler.backends.base import BaseBundlerBackend


__all__ = ["OpenAPIBundler"]

logger = logging.getLogger(__name__)


# Cache entry points at module level for performance
try:
    _BUNDLER_BACKENDS = {
        ep.name: ep
        for ep in importlib.metadata.entry_points(
            group="jentic.apitools.openapi.transformer.bundler.backends"
        )
    }
except Exception as e:
    warnings.warn(f"Failed to load bundler backend entry points: {e}", RuntimeWarning)
    _BUNDLER_BACKENDS = {}

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

        if isinstance(backend, str):
            if backend in _BUNDLER_BACKENDS:
                backend_class = _BUNDLER_BACKENDS[backend].load()  # loads the class
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
        document: str | dict,
        base_url: str | None = None,
        *,
        return_type: type[str],
        strict: bool = False,
    ) -> str: ...

    @overload
    def bundle(
        self,
        document: str | dict,
        base_url: str | None = None,
        *,
        return_type: type[dict[str, Any]],
        strict: bool = False,
    ) -> dict[str, Any]: ...

    @overload
    def bundle(
        self,
        document: str | dict,
        base_url: str | None = None,
        *,
        return_type: type[T],
        strict: bool = False,
    ) -> T: ...

    def bundle(
        self,
        document: str | dict,
        base_url: str | None = None,
        *,
        return_type: type[T] | None = None,
        strict: bool = False,
    ) -> Any:
        raw = self._bundle(document, base_url)

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

    def _bundle(self, document: str | dict, base_url: str | None = None) -> Any:
        text = document
        data = None
        result = None

        if isinstance(document, str):
            is_uri = self.parser.is_uri_like(document)
            is_text = not is_uri

            if is_text:
                data = self.parser.parse(document)

            if is_uri and self.has_non_uri_backend():
                text = self.parser.load_uri(document)
                if not data or data is None:
                    data = self.parser.parse(text)
        else:
            is_uri = False

        data = text if not data or data is None else data

        backend_document = None
        if is_uri and "uri" in self.backend.accepts():
            backend_document = document
        elif is_uri and "text" in self.backend.accepts():
            backend_document = text
        elif is_uri and "dict" in self.backend.accepts():
            backend_document = data
        elif not is_uri and "text" in self.backend.accepts():
            backend_document = text
        elif not is_uri and "dict" in self.backend.accepts():
            backend_document = data

        if backend_document is not None:
            try:
                result = self.backend.bundle(backend_document)
            except Exception:
                # TODO(fracensco@jentic.com): Add to parser/validation chain result
                logger.exception("Error bundling document")
                raise

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

    @staticmethod
    def list_backends() -> list[str]:
        """
        List all available bundler backends registered via entry points.

        This static method discovers and returns the names of all bundler backends
        that have been registered in the 'jentic.apitools.openapi.transformer.bundler.backends'
        entry point group.

        Returns:
            List of backend names that can be used when initializing OpenAPIBundler.

        Example:
            >>> backends = OpenAPIBundler.list_backends()
            >>> print(backends)
            ['default', 'redocly']
        """
        return list(_BUNDLER_BACKENDS.keys())
