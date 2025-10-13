import importlib.metadata
import json
import warnings
from typing import Type

from jentic.apitools.openapi.parser.core import OpenAPIParser
from jentic.apitools.openapi.validator.backends.base import BaseValidatorBackend

from .diagnostics import JenticDiagnostic, ValidationResult


__all__ = ["OpenAPIValidator"]


# Cache entry points at module level for performance
try:
    _VALIDATOR_BACKENDS = {
        ep.name: ep
        for ep in importlib.metadata.entry_points(
            group="jentic.apitools.openapi.validator.backends"
        )
    }
except Exception as e:
    warnings.warn(f"Failed to load validator backend entry points: {e}", RuntimeWarning)
    _VALIDATOR_BACKENDS = {}


class OpenAPIValidator:
    """
    Validates OpenAPI documents using pluggable validator backends.

    This class provides a flexible validation framework that can use multiple
    validator backends simultaneously. Backends can be specified by name (via
    entry points), as class instances, or as class types.

    Attributes:
        parser: OpenAPIParser instance for parsing and loading documents
        backends: List of validator backend instances to use for validation
    """

    def __init__(
        self,
        backends: list[str | BaseValidatorBackend | Type[BaseValidatorBackend]] | None = None,
        parser: OpenAPIParser | None = None,
    ):
        """
        Initialize the OpenAPI validator.

        Args:
            backends: List of validator backends to use. Each item can be:
                - str: Name of a backend registered via entry points (e.g., "default", "openapi-spec", "spectral")
                - BaseValidatorBackend: Instance of a validator backend
                - Type[BaseValidatorBackend]: Class of a validator backend (will be instantiated)
                Defaults to ["default"] if None.
            parser: Custom OpenAPIParser instance. If None, creates a default parser.

        Raises:
            ValueError: If a backend name is not found in registered entry points
            TypeError: If a backend is not a valid type (str, instance, or class)
        """
        self.parser = parser if parser else OpenAPIParser()
        self.backends: list[BaseValidatorBackend] = []
        backends = ["default"] if not backends else backends

        for backend in backends:
            if isinstance(backend, str):
                if backend in _VALIDATOR_BACKENDS:
                    backend_class = _VALIDATOR_BACKENDS[backend].load()  # loads the class
                    self.backends.append(backend_class())
                else:
                    raise ValueError(f"No validator backend named '{backend}' found")
            elif isinstance(backend, BaseValidatorBackend):
                self.backends.append(backend)
            elif isinstance(backend, type) and issubclass(backend, BaseValidatorBackend):
                # Class (not instance) is passed
                self.backends.append(backend())
            else:
                raise TypeError("Invalid backend type: must be name or backend class/instance")

    def validate(
        self, document: str | dict, *, base_url: str | None = None, target: str | None = None
    ) -> ValidationResult:
        """
        Validate an OpenAPI document using all configured backends.

        This method accepts OpenAPI documents in multiple formats and automatically
        converts them to the format(s) required by each backend. All diagnostics
        from all backends are aggregated into a single ValidationResult.

        Args:
            document: OpenAPI document in one of the following formats:
                - File URI (e.g., "file:///path/to/openapi.yaml")
                - JSON/YAML string representation
                - Python dictionary
            base_url: Optional base URL for resolving relative references in the document
            target: Optional target identifier for validation context

        Returns:
            ValidationResult containing aggregated diagnostics from all backends.
            The result's `valid` property indicates if validation passed.

        Raises:
            TypeError: If document is not a str or dict
        """

        diagnostics: list[JenticDiagnostic] = []
        document_is_uri: bool = False
        document_text: str = ""
        document_dict: dict | None = None

        # Determine an input type and prepare different representations
        if isinstance(document, str):
            document_is_uri = self.parser.is_uri_like(document)

            if document_is_uri:
                # Load URI content if any backend needs non-URI format
                document_text = (
                    self.parser.load_uri(document) if self.has_non_uri_backend() else document
                )
                document_dict = (
                    self.parser.parse(document_text) if self.has_non_uri_backend() else None
                )
            else:
                # Plain text (JSON/YAML)
                document_text = document
                document_dict = self.parser.parse(document)
        elif isinstance(document, dict):
            document_is_uri = False
            document_text = json.dumps(document)
            document_dict = document
        else:
            raise TypeError(
                f"Unsupported document type: {type(document).__name__!r}. "
                f"Expected str (URI or JSON/YAML) or dict."
            )

        # Run validation through all backends
        for backend in self.backends:
            accepted = backend.accepts()
            backend_document = None

            # Determine which format to pass to this backend
            if document_is_uri and "uri" in accepted:
                backend_document = document
            elif "dict" in accepted and document_dict is not None:
                backend_document = document_dict
            elif "text" in accepted:
                backend_document = document_text

            if backend_document is not None:
                result = backend.validate(backend_document, base_url=base_url, target=target)
                diagnostics.extend(result.diagnostics)

        return ValidationResult(diagnostics=diagnostics)

    def has_non_uri_backend(self) -> bool:
        """
        Check if any configured backend requires non-URI document format.

        This helper method determines whether document content needs to be loaded
        and parsed from a URI. If all backends accept URIs directly, the loading
        step can be skipped for better performance.

        Returns:
            True if at least one backend accepts 'text' or 'dict' but not 'uri'.
            False if all backends can handle URIs directly.
        """
        for backend in self.backends:
            accepted = backend.accepts()
            if ("text" in accepted or "dict" in accepted) and "uri" not in accepted:
                return True
        return False

    @staticmethod
    def list_backends() -> list[str]:
        """
        List all available validator backends registered via entry points.

        This static method discovers and returns the names of all validator backends
        that have been registered in the 'jentic.apitools.openapi.validator.backends'
        entry point group.

        Returns:
            List of backend names that can be used when initializing OpenAPIValidator.

        Example:
            >>> backends = OpenAPIValidator.list_backends()
            >>> print(backends)
            ['default', 'spectral']
        """
        return list(_VALIDATOR_BACKENDS.keys())
