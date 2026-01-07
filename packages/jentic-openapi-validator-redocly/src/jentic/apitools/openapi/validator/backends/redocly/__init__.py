import json
import logging
import os
import shlex
import tempfile
from collections.abc import Sequence
from importlib.resources import as_file, files
from pathlib import Path
from typing import Literal

from jsonpointer import JsonPointer
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


__all__ = ["RedoclyValidatorBackend"]


logger = logging.getLogger(__name__)

rulesets_files_dir = files("jentic.apitools.openapi.validator.backends.redocly.rulesets")
ruleset_file = rulesets_files_dir.joinpath("redocly.yaml")


class RedoclyValidatorBackend(BaseValidatorBackend):
    def __init__(
        self,
        redocly_path: str = "npx --yes @redocly/cli@2.14.3",
        ruleset_path: str | None = None,
        timeout: float = 600.0,
        allowed_base_dir: str | Path | None = None,
        max_problems: int = 1000000,
    ):
        """
        Initialize the RedoclyValidatorBackend.

        Args:
            redocly_path: Path to the redocly CLI executable (default: "npx --yes @redocly/cli@2.14.3").
                Uses shell-safe parsing to handle quoted arguments properly.
            ruleset_path: Path to a custom ruleset file. If None, uses bundled default ruleset.
            timeout: Maximum time in seconds to wait for Redocly CLI execution (default: 600.0)
            allowed_base_dir: Optional base directory for path security validation.
                When set, all document and ruleset paths will be validated to ensure they
                are within this directory. This provides defense against path traversal attacks
                and is recommended for web services or when processing untrusted input.
                If None (default), only file extension validation is performed (no base directory
                containment check). Extension validation ensures only .yaml, .yml, and .json files
                are processed.
            max_problems: Maximum number of validation problems to report (default: 1000000).
                This limits the number of issues returned by Redocly to prevent memory/performance
                issues when validating large documents with many errors.
        """
        self.redocly_path = redocly_path
        self.ruleset_path = ruleset_path if isinstance(ruleset_path, str) else None
        self.timeout = timeout
        self.allowed_base_dir = allowed_base_dir
        self.max_problems = max_problems

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
        Validate an OpenAPI document using Redocly.

        Args:
            document: Path to the OpenAPI document file to validate, or dict containing the document
            base_url: Optional base URL for resolving relative references (currently unused)
            target: Optional target identifier for validation context (currently unused)

        Returns:
            ValidationResult containing any validation issues found

        Raises:
            FileNotFoundError: If a custom ruleset file doesn't exist
            RuntimeError: If Redocly execution fails
            SubprocessExecutionError: If Redocly execution times out or fails to start
            TypeError: If a document type is not supported
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
        Validate an OpenAPI document using Redocly.

        Args:
            document: Path to the OpenAPI document file to validate, or dict containing the document

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

            # Validate ruleset path if it's a filesystem path (skip non-path URIs)
            validated_ruleset_path = (
                validate_path(
                    self.ruleset_path,
                    allowed_base=self.allowed_base_dir,
                    allowed_extensions=(".yaml", ".yml"),
                )
                if self.ruleset_path is not None and is_path(self.ruleset_path)
                else self.ruleset_path
            )

            # Create a temporary file to capture Redocly output
            # This avoids stdout buffer size limitations (65536 bytes)
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8"
            ) as tmp_output:
                output_path = tmp_output.name

            try:
                with as_file(ruleset_file) as default_ruleset_path:
                    # Build redocly command
                    cmd = [
                        *shlex.split(self.redocly_path),
                        "lint",
                        "--config",
                        validated_ruleset_path or default_ruleset_path,
                        "--format",
                        "json",
                        "--max-problems",
                        str(self.max_problems),
                        validated_doc_path,
                    ]
                    env = os.environ.copy()
                    env.update(
                        {
                            "REDOCLY_TELEMETRY": "off",
                            "REDOCLY_SUPPRESS_UPDATE_NOTICE": "true",
                        }
                    )

                    # Open the temp output file for writing and redirect stdout to it
                    with open(output_path, "w", encoding="utf-8") as output_file:
                        result = run_subprocess(
                            cmd, env=env, timeout=self.timeout, stdout=output_file
                        )

                if result is None:
                    raise RuntimeError("Redocly validation failed - no result returned")

                # Check for execution errors
                if result.returncode not in (0, 1):
                    # Redocly returns 0 (no errors) or 1 (validation errors found).
                    # Exit code 2 or higher indicates command-line/configuration errors.
                    stderr_msg = result.stderr.strip()

                    # Try custom error handling (can be overridden in subclasses)
                    custom_diagnostics = self._handle_error(
                        stderr_msg, result, validated_doc_path, target
                    )
                    if custom_diagnostics is not None:
                        return custom_diagnostics

                    # Default error handling
                    msg = stderr_msg or f"Redocly exited with code {result.returncode}"
                    raise RuntimeError(msg)

                # Read and parse JSON output
                try:
                    with open(output_path, mode="r", encoding="utf-8") as f:
                        output_data = json.load(f)
                        problems: list[dict] = output_data.get("problems", [])
                except FileNotFoundError:
                    if result.stderr:
                        raise RuntimeError(
                            f"Redocly did not create output file: {result.stderr.strip()}"
                        )
                    logger.warning("Redocly output file not found, returning empty diagnostics")
                    return ValidationResult(diagnostics=[])
                except json.JSONDecodeError as e:
                    if result.stderr:
                        raise RuntimeError(
                            f"Redocly output is not valid JSON: {result.stderr.strip()}"
                        )
                    logger.warning(
                        f"Redocly output is not valid JSON: {e}, returning empty diagnostics"
                    )
                    return ValidationResult(diagnostics=[])
            finally:
                # Clean up temp output file
                Path(output_path).unlink(missing_ok=True)

        except SubprocessExecutionError as e:
            # only timeout and OS errors, as run_subprocess has a default `fail_on_error = False`
            raise e

        diagnostics: list[JenticDiagnostic] = []
        for problem in problems:
            locations = []
            for location_path in problem.get("location", [{}]):
                pointer_uri_fragment_ident_rep = location_path.get("pointer")
                if pointer_uri_fragment_ident_rep:
                    pointer = pointer_uri_fragment_ident_rep.lstrip("#")
                    path = JsonPointer(pointer).get_parts()
                    loc = f"path: {'.'.join(path)}"
                    data = {"fixable": True, "path": path}
                else:
                    loc = ""
                    data = {"fixable": True, "path": []}
                locations.append((loc, data))

            for loc, data in locations:
                # Map Redocly severity to LSP DiagnosticSeverity
                severity_map: dict[str, DiagnosticSeverity] = {
                    "error": DiagnosticSeverity.Error,
                    "warn": DiagnosticSeverity.Warning,
                }
                severity = severity_map.get(problem.get("severity"), DiagnosticSeverity.Information)  # type: ignore[arg-type]

                diagnostic = JenticDiagnostic(
                    range=Range(
                        start=Position(line=0, character=0),
                        end=Position(line=0, character=0),
                    ),
                    message=problem.get("message", "") + " [" + loc + "]",
                    severity=severity,
                    code=problem.get("ruleId"),
                    source="redocly-validator",
                )
                diagnostic.data = data
                diagnostic.set_target(target)
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
        """Handle custom error cases from Redocly execution.

        This is an extension point for subclasses to provide custom error handling.
        By default, returns None to proceed with standard error handling (raising RuntimeError).

        If this method returns a ValidationResult, that result will be returned to the caller.
        If this method returns None, the default error handling will proceed (raising RuntimeError).

        Args:
            stderr_msg: The stderr output from Redocly
            result: The subprocess execution result from Redocly
            document_path: The path or URL being validated
            target: Optional target identifier for validation context

        Returns:
            ValidationResult if the error was handled, None to proceed with default handling

        Example:
            Override this method to handle specific errors gracefully:

            def _handle_error(self, stderr_msg, result, document_path, target):
                # Handle fetch errors (403, 404, etc.) by returning diagnostics
                if "ENOTFOUND" in stderr_msg or "ETIMEDOUT" in stderr_msg:
                    diagnostic = JenticDiagnostic(
                        range=Range(start=Position(line=0, character=0),
                                    end=Position(line=0, character=0)),
                        message=f"Could not fetch document: {document_path}",
                        severity=DiagnosticSeverity.Error,
                        code="document-fetch-error",
                        source="redocly-validator",
                    )
                    diagnostic.set_target(target)
                    return ValidationResult(diagnostics=[diagnostic])

                # Fall back to default behavior
                return super()._handle_error(stderr_msg, result, document_path, target)
        """
        # Return None to proceed with default error handling (raising RuntimeError)
        return None
