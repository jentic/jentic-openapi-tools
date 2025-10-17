import importlib.metadata
import logging
import warnings
from typing import Any, Mapping, Optional, Sequence, Type, TypeVar, cast, overload

from jentic.apitools.openapi.common.uri import is_uri_like
from jentic.apitools.openapi.parser.backends.base import BaseParserBackend

from .exceptions import (
    BackendNotFoundError,
    DocumentParseError,
    InvalidBackendError,
    OpenAPIParserError,
    TypeConversionError,
)
from .loader import load_uri


__all__ = ["OpenAPIParser"]


# Cache entry points at module level for performance
try:
    _PARSER_BACKENDS = {
        ep.name: ep
        for ep in importlib.metadata.entry_points(group="jentic.apitools.openapi.parser.backends")
    }
except Exception as e:
    warnings.warn(f"Failed to load parser backend entry points: {e}", RuntimeWarning)
    _PARSER_BACKENDS = {}

T = TypeVar("T")


class OpenAPIParser:
    """
    Provides a parser for OpenAPI specifications using customizable backends.

    This class is designed to facilitate the parsing of OpenAPI documents.
    It supports one backend at a time and can be extended through backends.

    Attributes:
        backend: Backend used by the parser implementing the BaseParserBackend interface.
        logger: Logger instance.
        conn_timeout: Connection timeout in seconds.
        read_timeout: Read timeout in seconds.
    """

    def __init__(
        self,
        backend: str | BaseParserBackend | Type[BaseParserBackend] | None = None,
        *,
        logger: logging.Logger | None = None,
        conn_timeout: int = 5,
        read_timeout: int = 10,
    ):
        logger = logger or logging.getLogger(__name__)
        backend = backend if backend else "pyyaml"
        self.backend: BaseParserBackend
        self.logger = logger
        self.conn_timeout = conn_timeout
        self.read_timeout = read_timeout

        if isinstance(backend, str):
            try:
                if backend in _PARSER_BACKENDS:
                    try:
                        logger.debug(f"using parser backend '{backend}'")
                        backend_class = _PARSER_BACKENDS[backend].load()  # loads the class
                        self.backend = backend_class()
                    except Exception as e:
                        raise InvalidBackendError(
                            f"Failed to load parser backend '{backend}': {e}"
                        ) from e
                else:
                    logger.error(f"No parser backend named '{backend}' found")
                    raise BackendNotFoundError(f"No parser backend named '{backend}' found")
            except OpenAPIParserError:
                raise
            except Exception as e:
                raise InvalidBackendError(f"Error initializing backend '{backend}': {e}") from e

        elif isinstance(backend, BaseParserBackend):
            logger.debug(f"using parser backend '{type[backend]}'")
            self.backend = backend
        elif isinstance(backend, type) and issubclass(backend, BaseParserBackend):
            try:
                # class (not instance) is passed
                self.backend = backend()
                logger.debug(f"using parser backend '{type[backend]}'")
            except Exception as e:
                raise InvalidBackendError(
                    f"Failed to instantiate backend class '{backend.__name__}': {e}"
                ) from e

        else:
            logger.error("Invalid backend type: must be name or backend class/instance")
            raise InvalidBackendError(
                "Invalid backend type: must be a backend name (str), "
                "BaseParserBackend instance, or BaseParserBackend class"
            )

    @overload
    def parse(self, document: str) -> dict[str, Any]: ...

    @overload
    def parse(self, document: str, *, return_type: type[T], strict: bool = False) -> T: ...

    def parse(
        self, document: str, *, return_type: type[T] | None = None, strict: bool = False
    ) -> Any:
        try:
            raw = self._parse(document)
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

    def _parse(self, document: str) -> Any:
        document_is_uri = is_uri_like(document)
        backend_document: str | None = None

        self.logger.debug(f"parsing a '{'uri' if document_is_uri else 'text'}'")

        if document_is_uri and "uri" in self.backend.accepts():
            backend_document = document  # Delegate loading to backend
        elif document_is_uri and "text" in self.backend.accepts():
            backend_document = self.load_uri(document)
        elif not document_is_uri and "text" in self.backend.accepts():
            backend_document = document

        if backend_document is None:
            accepted_formats = ", ".join(self.backend.accepts())
            document_type = "URI" if document_is_uri else "text"
            raise DocumentParseError(
                f"Backend '{type(self.backend).__name__}' does not accept {document_type} format. "
                f"Accepted formats: {accepted_formats}"
            )

        try:
            parse_result = self.backend.parse(backend_document, logger=self.logger)
        except Exception as e:
            # Log the original error and wrap it
            msg = f"Failed to parse document with backend '{type(self.backend).__name__}': {e}"
            self.logger.error(msg)
            raise DocumentParseError(msg) from e

        if parse_result is None:
            msg = "No valid document found"
            self.logger.error(msg)
            raise DocumentParseError(msg)

        return parse_result

    def has_non_uri_backend(self) -> bool:
        """Check if any backend accepts 'text' but not 'uri'."""
        accepted = self.backend.accepts()
        return "text" in accepted and "uri" not in accepted

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
    def is_uri_like(s: Optional[str]) -> bool:
        return is_uri_like(s)

    def load_uri(self, uri: str) -> str:
        return load_uri(uri, self.conn_timeout, self.read_timeout, self.logger)

    @staticmethod
    def list_backends() -> list[str]:
        """
        List all available parser backends registered via entry points.

        This static method discovers and returns the names of all parser backends
        that have been registered in the 'jentic.apitools.openapi.parser.backends'
        entry point group.

        Returns:
            List of backend names that can be used when initializing OpenAPIParser.

        Example:
            >>> backends = OpenAPIParser.list_backends()
            >>> print(backends)
            ['pyyaml', 'ruamel']
        """
        return list(_PARSER_BACKENDS.keys())
