import importlib.metadata
import json
import multiprocessing
import os
import warnings
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from contextlib import ExitStack
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
        backends: Sequence[str | BaseValidatorBackend | Type[BaseValidatorBackend]] | None = None,
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
        self,
        document: str | dict,
        *,
        base_url: str | None = None,
        target: str | None = None,
        parallel: bool = False,
        max_workers: int | None = None,
        max_process_workers: int | None = None,
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
            parallel: If True and multiple backends are configured, schedule
                backends in three tiers based on each backend's
                ``execution_type()`` method:
                - ``"io"`` backends run in parallel via ``ThreadPoolExecutor``.
                - ``"cpu"`` backends run sequentially in the main thread.
                - ``"cpu-heavy"`` backends run in separate processes via
                  ``ProcessPoolExecutor`` (``spawn`` start method).
                All three tiers execute simultaneously. Defaults to False.
            max_workers: Maximum number of worker threads for I/O-bound backends.
                If None, defaults to the ThreadPoolExecutor default.
                Only used when parallel=True.
            max_process_workers: Maximum number of worker processes for
                cpu-heavy backends. If None, defaults to
                ``min(num_cpu_heavy_backends, os.cpu_count())``.
                Only used when parallel=True.

        Returns:
            ValidationResult containing aggregated diagnostics from all backends.
            The result's `valid` property indicates if validation passed.

        Raises:
            TypeError: If document is not a str or dict
            ValueError: If max_workers or max_process_workers is not a
                positive integer
        """
        if max_workers is not None and max_workers < 1:
            raise ValueError(f"max_workers must be a positive integer, got {max_workers}")
        if max_process_workers is not None and max_process_workers < 1:
            raise ValueError(
                f"max_process_workers must be a positive integer, got {max_process_workers}"
            )

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

        diagnostics: list[JenticDiagnostic] = []

        # Build the common arguments tuple for _validate_single_backend
        validate_args = (document, document_dict, document_text, document_is_uri, base_url, target)

        # Run validation through all backends
        if parallel and len(self.backends) > 1:
            # Three-tier scheduling based on execution_type():
            # - "io": release the GIL (subprocess/network) → ThreadPoolExecutor
            # - "cpu": fast pure Python → sequential in main thread
            # - "cpu-heavy": long-running pure Python → ProcessPoolExecutor (spawn)
            io_backends: list[BaseValidatorBackend] = []
            cpu_backends: list[BaseValidatorBackend] = []
            cpu_heavy_backends: list[BaseValidatorBackend] = []
            for b in self.backends:
                et = b.execution_type()
                if et == "io":
                    io_backends.append(b)
                elif et == "cpu":
                    cpu_backends.append(b)
                elif et == "cpu-heavy":
                    cpu_heavy_backends.append(b)
                else:
                    warnings.warn(
                        f"Unknown execution_type() {et!r} for backend {type(b).__name__}; "
                        f"treating it as 'cpu'. Expected one of 'io', 'cpu', 'cpu-heavy'.",
                        RuntimeWarning,
                    )
                    cpu_backends.append(b)

            if io_backends or cpu_heavy_backends:
                with ExitStack() as stack:
                    futures: list = []

                    if io_backends:
                        thread_exec = stack.enter_context(
                            ThreadPoolExecutor(max_workers=max_workers)
                        )
                        futures.extend(
                            thread_exec.submit(_validate_single_backend, b, *validate_args)
                            for b in io_backends
                        )

                    if cpu_heavy_backends:
                        process_workers = (
                            max_process_workers
                            if max_process_workers is not None
                            else min(len(cpu_heavy_backends), os.cpu_count() or 1)
                        )
                        process_exec = stack.enter_context(
                            ProcessPoolExecutor(
                                max_workers=process_workers,
                                mp_context=multiprocessing.get_context("spawn"),
                            )
                        )
                        futures.extend(
                            process_exec.submit(_validate_single_backend, b, *validate_args)
                            for b in cpu_heavy_backends
                        )

                    # Fast CPU backends run sequentially in the main thread
                    # while I/O and heavy CPU backends execute in background
                    for b in cpu_backends:
                        diagnostics.extend(_validate_single_backend(b, *validate_args))

                    for future in as_completed(futures):
                        diagnostics.extend(future.result())
            else:
                # All backends are fast CPU-bound: run sequentially
                for b in cpu_backends:
                    diagnostics.extend(_validate_single_backend(b, *validate_args))
        else:
            # Sequential execution (default, or single backend)
            for backend in self.backends:
                diagnostics.extend(_validate_single_backend(backend, *validate_args))

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


def _validate_single_backend(
    backend: BaseValidatorBackend,
    document: str | dict,
    document_dict: dict | None,
    document_text: str,
    document_is_uri: bool,
    base_url: str | None,
    target: str | None,
) -> list[JenticDiagnostic]:
    """
    Validate document with a single backend.

    This is a module-level function (not a method) so it can be submitted to
    both ThreadPoolExecutor and ProcessPoolExecutor (picklable).  Backends
    declaring ``execution_type() == "cpu-heavy"`` must be picklable since they
    are dispatched to a ProcessPoolExecutor with the ``spawn`` start method.

    Note:
        This function may be called from multiple threads concurrently
        (via ThreadPoolExecutor for I/O backends). All document arguments
        are shared across threads and must be treated as read-only.
        Backends returning ``execution_type() == "io"`` must also ensure
        their own ``validate()`` implementation is thread-safe (i.e. does
        not mutate shared instance state without synchronization).

    Args:
        backend: The validator backend to use
        document: The original document (URI or text)
        document_dict: Parsed document as dict (if available)
        document_text: Document as text string
        document_is_uri: Whether document is a URI
        base_url: Optional base URL for resolving references
        target: Optional target identifier

    Returns:
        List of diagnostics from the backend
    """
    accepted = backend.accepts()
    backend_document: str | dict | None = None

    if document_is_uri and "uri" in accepted:
        backend_document = document
    elif "dict" in accepted and document_dict is not None:
        backend_document = document_dict
    elif "text" in accepted:
        backend_document = document_text

    if backend_document is not None:
        result = backend.validate(backend_document, base_url=base_url, target=target)
        return list(result.diagnostics)
    return []
