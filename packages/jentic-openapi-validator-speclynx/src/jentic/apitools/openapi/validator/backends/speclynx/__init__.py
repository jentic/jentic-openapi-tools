import json
import logging
import shlex
import tempfile
from collections.abc import Sequence
from importlib.resources import as_file, files
from pathlib import Path
from typing import Literal

from lsprotocol.types import DiagnosticSeverity, Position, Range

from jentic.apitools.openapi.common.path_security import validate_path
from jentic.apitools.openapi.common.subproc import (
    SubprocessExecutionError,
    SubprocessExecutionResult,
    run_subprocess,
)
from jentic.apitools.openapi.common.uri import file_uri_to_path, is_file_uri, is_path
from jentic.apitools.openapi.validator.backends.base import BaseValidatorBackend
from jentic.apitools.openapi.validator.core import JenticDiagnostic, ValidationResult


__all__ = ["SpeclynxValidatorBackend"]


logger = logging.getLogger(__name__)

_TARBALL_NAME = "jentic-openapi-validator-speclynx-0.1.0.tgz"
_DEFAULT_SPECLYNX_PATH = f"npx --yes {_TARBALL_NAME}"

resources_dir = files("jentic.apitools.openapi.validator.backends.speclynx.resources")
tarball_file = resources_dir.joinpath(_TARBALL_NAME)


class SpeclynxValidatorBackend(BaseValidatorBackend):
    def __init__(
        self,
        speclynx_path: str = _DEFAULT_SPECLYNX_PATH,
        timeout: float = 600.0,
        allowed_base_dir: str | Path | None = None,
        plugins_dir: str | Path | None = None,
    ):
        """
        Initialize the SpeclynxValidatorBackend.

        Args:
            speclynx_path: Path to the speclynx CLI executable (default: uses bundled npm tarball via npx).
                Can be a custom path like "/usr/local/bin/speclynx" or an npx command.
                Uses shell-safe parsing to handle quoted arguments properly.
            timeout: Maximum time in seconds to wait for validation execution (default: 600.0)
            allowed_base_dir: Optional base directory for path security validation.
                When set, all document paths will be validated to ensure they
                are within this directory. This provides defense against path traversal attacks
                and is recommended for web services or when processing untrusted input.
                If None (default), only file extension validation is performed (no base directory
                containment check). Extension validation ensures only .yaml, .yml, and .json files
                are processed.
            plugins_dir: Optional directory containing additional validation plugins (.mjs files).
                Plugins are loaded automatically and used to validate the OpenAPI document.
                When specified, custom plugins are merged with the built-in plugins (both are loaded).
                If None (default), only the built-in plugins directory is used (which is empty by default).
                See resources/plugins/example-plugin.mjs.sample for plugin format.
        """
        self.speclynx_path = speclynx_path
        self.timeout = timeout
        self.allowed_base_dir = allowed_base_dir
        self.plugins_dir = Path(plugins_dir) if plugins_dir else None

    @staticmethod
    def accepts() -> Sequence[Literal["uri", "dict"]]:
        """Return the document formats this validator can accept.

        Returns:
            Sequence of supported document format identifiers:
            - "uri": File path or URI pointing to OpenAPI Document
            - "dict": Python dictionary containing OpenAPI Document data
        """
        return ["uri", "dict"]

    def validate(
        self, document: str | dict, *, base_url: str | None = None, target: str | None = None
    ) -> ValidationResult:
        """
        Validate an OpenAPI document using SpecLynx ApiDOM.

        Args:
            document: Path to the OpenAPI document file to validate, or dict containing the document
            base_url: Optional base URL for resolving relative references
            target: Optional target identifier for validation context

        Returns:
            ValidationResult containing any validation issues found

        Raises:
            RuntimeError: If validation execution fails
            SubprocessExecutionError: If validation execution times out or fails to start
            TypeError: If a document type is not supported
            PathTraversalError: Document path attempts to escape allowed_base_dir (only when allowed_base_dir is set)
            InvalidExtensionError: Document path has disallowed file extension (always checked for filesystem paths)
        """
        if isinstance(document, str):
            return self._validate_uri(document, base_url=base_url, target=target)
        elif isinstance(document, dict):
            return self._validate_dict(document, base_url=base_url, target=target)
        else:
            raise TypeError(f"Unsupported document type: {type(document)!r}")

    def _validate_uri(
        self, document: str, *, base_url: str | None = None, target: str | None = None
    ) -> ValidationResult:
        """
        Validate an OpenAPI document using SpecLynx ApiDOM.

        Args:
            document: Path to the OpenAPI document file to validate
            base_url: Optional base URL for resolving relative references
            target: Optional target identifier for validation context

        Returns:
            ValidationResult containing any validation issues found
        """
        result: SubprocessExecutionResult | None = None

        try:
            doc_path = file_uri_to_path(document) if is_file_uri(document) else document

            # Validate document path if it's a filesystem path (skip non-path URIs like HTTP(S))
            validated_doc_path = (
                validate_path(
                    doc_path,
                    allowed_base=self.allowed_base_dir,
                    allowed_extensions=(".yaml", ".yml", ".json"),
                )
                if is_path(doc_path)
                else doc_path
            )

            # Determine output file path
            with tempfile.NamedTemporaryFile() as tmp_output:
                output_path = tmp_output.name

            try:
                cmd = [
                    *shlex.split(self.speclynx_path),
                    validated_doc_path,
                    "-o",
                    output_path,
                ]
                if base_url:
                    cmd.extend(["--base-uri", base_url])
                if self.plugins_dir:
                    cmd.extend(["--plugins", str(self.plugins_dir)])
                if self.allowed_base_dir:
                    cmd.extend(["--allowed-base-dir", str(self.allowed_base_dir)])

                # npx with bundled tarball requires cwd set to resources directory
                if self.speclynx_path == _DEFAULT_SPECLYNX_PATH:
                    with as_file(tarball_file) as tarball_path:
                        resources_path = tarball_path.parent
                        result = run_subprocess(cmd, timeout=self.timeout, cwd=str(resources_path))
                else:
                    result = run_subprocess(cmd, timeout=self.timeout)

                if result is None:
                    raise RuntimeError("SpecLynx validation failed - no result returned")

                # Check for execution errors
                # Exit code 0 = valid, exit code 1 = has validation errors, other = execution error
                if result.returncode not in (0, 1):
                    stderr_msg = result.stderr.strip()
                    custom_diagnostics = self._handle_error(
                        stderr_msg, result, validated_doc_path, target
                    )
                    if custom_diagnostics is not None:
                        return custom_diagnostics

                    # Default error handling
                    msg = stderr_msg or f"SpecLynx exited with code {result.returncode}"
                    raise RuntimeError(msg)

                # Read and parse output file
                try:
                    with open(output_path, encoding="utf-8") as f:
                        diagnostics_data: list[dict] = json.load(f)
                except FileNotFoundError:
                    if result.stderr:
                        raise RuntimeError(
                            f"SpecLynx did not create output file: {result.stderr.strip()}"
                        )
                    logger.warning("SpecLynx output file not found, returning empty diagnostics")
                    return ValidationResult(diagnostics=[])
                except json.JSONDecodeError as e:
                    if result.stderr:
                        raise RuntimeError(
                            f"SpecLynx output is not valid JSON: {result.stderr.strip()}"
                        )
                    logger.warning(
                        f"SpecLynx output is not valid JSON: {e}, returning empty diagnostics"
                    )
                    return ValidationResult(diagnostics=[])
            finally:
                # Clean up the temp output file
                Path(output_path).unlink(missing_ok=True)

        except SubprocessExecutionError as e:
            # only timeout and OS errors, as run_subprocess has a default `fail_on_error = False`
            raise e

        # Convert diagnostics to JenticDiagnostic format (already LSP compatible)
        diagnostics: list[JenticDiagnostic] = []
        for issue in diagnostics_data:
            range_data = issue["range"]
            diagnostic = JenticDiagnostic(
                range=Range(
                    start=Position(**range_data["start"]),
                    end=Position(**range_data["end"]),
                ),
                message=issue["message"],
                severity=DiagnosticSeverity(issue["severity"]),
                code=issue.get("code"),
                source="speclynx-validator",
            )
            diagnostic.set_target(target)
            if "data" in issue and "path" in issue["data"]:
                diagnostic.set_path(issue["data"]["path"])
            diagnostics.append(diagnostic)

        return ValidationResult(diagnostics=diagnostics)

    def _validate_dict(
        self, document: dict, *, base_url: str | None = None, target: str | None = None
    ) -> ValidationResult:
        """Validate a dict document by creating a temporary file and using _validate_uri."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=True, encoding="utf-8"
        ) as temp_file:
            json.dump(document, temp_file)
            temp_file.flush()  # Ensure content is written to disk

            return self._validate_uri(
                Path(temp_file.name).as_uri(), base_url=base_url, target=target
            )

    def _handle_error(
        self,
        stderr_msg: str,
        result: SubprocessExecutionResult,
        document_path: str,
        target: str | None = None,
    ) -> ValidationResult | None:
        """Handle custom error cases from SpecLynx execution.

        This is an extension point for subclasses to provide custom error handling.
        By default, returns None to proceed with standard error handling (raising RuntimeError).

        If this method returns a ValidationResult, that result will be returned to the caller.
        If this method returns None, the default error handling will proceed (raising RuntimeError).

        Args:
            stderr_msg: The stderr output from SpecLynx
            result: The subprocess execution result from SpecLynx
            document_path: The path or URL being validated
            target: Optional target identifier for validation context

        Returns:
            ValidationResult if the error was handled, None to proceed with default handling

        Example:
            Override this method to handle specific errors gracefully:

            def _handle_error(self, stderr_msg, result, document_path, target):
                # Handle fetch errors (403, 404, etc.) by returning diagnostics
                if "Could not parse" in stderr_msg and "://" in document_path:
                    diagnostic = JenticDiagnostic(
                        range=Range(start=Position(line=0, character=0),
                                    end=Position(line=0, character=0)),
                        message=f"Could not fetch document: {document_path}",
                        severity=DiagnosticSeverity.Error,
                        code="document-fetch-error",
                        source="speclynx-validator",
                    )
                    diagnostic.set_target(target)
                    return ValidationResult(diagnostics=[diagnostic])

                # Fall back to default behavior
                return super()._handle_error(stderr_msg, result, document_path, target)
        """
        # Return None to proceed with default error handling (raising RuntimeError)
        return None
