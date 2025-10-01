import importlib.metadata
import json
from typing import Type

from lsprotocol.types import Diagnostic

from jentic.apitools.openapi.parser.core import OpenAPIParser
from jentic.apitools.openapi.validator.backends.base import BaseValidatorBackend

from .diagnostics import ValidationResult


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
                - str: Name of a backend registered via entry points (e.g., "default", "spectral")
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

        # Discover entry points for validator backends
        eps = importlib.metadata.entry_points(group="jentic.apitools.openapi.validator.backends")
        available_backends = {ep.name: ep for ep in eps}

        for backend in backends:
            if isinstance(backend, str):
                if backend in available_backends:
                    backend_class = available_backends[backend].load()  # loads the class
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

    def validate(self, source: str | dict) -> ValidationResult:
        """
        Validate an OpenAPI document using all configured backends.

        This method accepts OpenAPI documents in multiple formats and automatically
        converts them to the format(s) required by each backend. All diagnostics
        from all backends are aggregated into a single ValidationResult.

        Args:
            source: OpenAPI document in one of the following formats:
                - File URI (e.g., "file:///path/to/openapi.yaml")
                - JSON/YAML string representation
                - Python dictionary

        Returns:
            ValidationResult containing aggregated diagnostics from all backends.
            The result's `valid` property indicates if validation passed.

        Raises:
            TypeError: If source is not a str or dict
        """

        diagnostics: list[Diagnostic] = []
        source_is_uri: bool = False
        source_text: str = ""
        source_dict: dict | None = None

        # Determine an input type and prepare different representations
        if isinstance(source, str):
            source_is_uri = self.parser.is_uri_like(source)

            if source_is_uri:
                # Load URI content if any backend needs non-URI format
                source_text = self.parser.load_uri(source) if self.has_non_uri_backend() else source
                source_dict = self.parser.parse(source_text) if self.has_non_uri_backend() else None
            else:
                # Plain text (JSON/YAML)
                source_text = source
                source_dict = self.parser.parse(source)
        elif isinstance(source, dict):
            source_is_uri = False
            source_text = json.dumps(source)
            source_dict = source
        else:
            raise TypeError(
                f"Unsupported document type: {type(source).__name__!r}. "
                f"Expected str (URI or JSON/YAML) or dict."
            )

        # Run validation through all backends
        for backend in self.backends:
            accepted = backend.accepts()
            document = None

            # Determine which format to pass to this backend
            if source_is_uri and "uri" in accepted:
                document = source
            elif "dict" in accepted and source_dict is not None:
                document = source_dict
            elif "text" in accepted:
                document = source_text

            if document is not None:
                result = backend.validate(document)
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
