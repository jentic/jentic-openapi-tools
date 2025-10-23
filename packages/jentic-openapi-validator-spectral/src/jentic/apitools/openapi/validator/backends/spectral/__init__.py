import json
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


__all__ = ["SpectralValidatorBackend"]


rulesets_files_dir = files("jentic.apitools.openapi.validator.backends.spectral.rulesets")
ruleset_file = rulesets_files_dir.joinpath("spectral.yaml")


class SpectralValidatorBackend(BaseValidatorBackend):
    def __init__(
        self,
        spectral_path: str = "npx --yes @stoplight/spectral-cli@^6.15.0",
        ruleset_path: str | None = None,
        timeout: float = 600.0,
        allowed_base_dir: str | Path | None = None,
    ):
        """
        Initialize the SpectralValidatorBackend.

        Args:
            spectral_path: Path to the spectral CLI executable (default: "npx --yes @stoplight/spectral-cli@^6.15.0").
                Uses shell-safe parsing to handle quoted arguments properly.
            ruleset_path: Path to a custom ruleset file. If None, uses bundled default ruleset.
            timeout: Maximum time in seconds to wait for Spectral CLI execution (default: 600.0)
            allowed_base_dir: Optional base directory for path security validation.
                When set, all document and ruleset paths will be validated to ensure they
                are within this directory. This provides defense against path traversal attacks
                and is recommended for web services or when processing untrusted input.
                If None (default), only file extension validation is performed (no base directory
                containment check). Extension validation ensures only .yaml, .yml, and .json files
                are processed.
        """
        self.spectral_path = spectral_path
        self.ruleset_path = ruleset_path if isinstance(ruleset_path, str) else None
        self.timeout = timeout
        self.allowed_base_dir = allowed_base_dir

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
        Validate an OpenAPI document using Spectral.

        Args:
            document: Path to the OpenAPI document file to validate, or dict containing the document
            base_url: Optional base URL for resolving relative references (currently unused)
            target: Optional target identifier for validation context (currently unused)

        Returns:
            ValidationResult containing any validation issues found

        Raises:
            FileNotFoundError: If a custom ruleset file doesn't exist
            RuntimeError: If Spectral execution fails
            SubprocessExecutionError: If Spectral execution times out or fails to start
            TypeError: If a document type is not supported
            PathTraversalError: Document or ruleset path attempts to escape allowed_base_dir (only when allowed_base_dir is set)
            InvalidExtensionError: Document or ruleset path has disallowed file extension (always checked for filesystem paths)
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
        Validate an OpenAPI document using Spectral.

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

            with as_file(ruleset_file) as default_ruleset_path:
                # Build spectral command
                cmd = [
                    *shlex.split(self.spectral_path),
                    "lint",
                    "-r",
                    validated_ruleset_path or default_ruleset_path,
                    "-f",
                    "json",
                    validated_doc_path,
                ]
                result = run_subprocess(cmd, timeout=self.timeout)

        except SubprocessExecutionError as e:
            # only timeout and OS errors, as run_subprocess has a default `fail_on_error = False`
            raise e

        if result is None:
            raise RuntimeError("Spectral validation failed - no result returned")

        if result.returncode not in (0, 1) or (result.stderr and not result.stdout):
            # According to Spectral docs, return code 2 might indicate lint errors found,
            # 0 means no issues, but let's not assume this; we'll parse output.
            # If returncode is something else, spectral encountered an execution error.
            err = result.stderr.strip() or result.stdout.strip()
            msg = err or f"Spectral exited with code {result.returncode}"
            raise RuntimeError(msg)

        output = result.stdout.replace("No results with a severity of 'error' found!", "")

        try:
            issues: list[dict] = json.loads(output)
        except json.JSONDecodeError:
            # If an output isn't JSON (maybe spectral old version or error format), handle gracefully
            return ValidationResult(diagnostics=[])

        diagnostics: list[JenticDiagnostic] = []
        for issue in issues:
            # Spectral JSON has fields like code, message, severity, path, range, etc.
            try:
                severity_code = issue.get(
                    "severity", DiagnosticSeverity.Error
                )  # e.g. "error" or numeric 0=error,1=warn...
                severity = DiagnosticSeverity(severity_code + 1)
            except (ValueError, TypeError):
                severity = DiagnosticSeverity.Error

            msg_text = issue.get("message", "")
            # location: combine file and jsonpath if available
            loc = f"path: {'.'.join(str(p) for p in issue['path'])}" if issue.get("path") else ""
            range_info = issue.get("range", {})
            start_line = range_info.get("start", {}).get("line", 0)
            start_char = range_info.get("start", {}).get("character", 0)
            end_line = range_info.get("end", {}).get("line", start_line)
            end_char = range_info.get("end", {}).get("character", start_char)
            # TODO(francesco@jentic.com): add jsonpath and other details to message if needed
            diagnostic = JenticDiagnostic(
                range=Range(
                    start=Position(line=start_line, character=start_char),
                    end=Position(line=end_line, character=end_char),
                ),
                message=msg_text + " [" + loc + "]",
                severity=severity,
                code=issue.get("code"),
                source="spectral-validator",
            )
            diagnostic.set_target(target)
            diagnostic.set_path(issue.get("path"))
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
