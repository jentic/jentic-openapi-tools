import subprocess
import json
from typing import Optional
import tempfile
import os
from urllib.parse import urlparse
from urllib.request import url2pathname

from lsprotocol.types import Diagnostic, DiagnosticSeverity, Range, Position

from jentic_openapi_validator import ValidationResult
from jentic_openapi_validator.strategies.base import BaseValidatorStrategy
from importlib.resources import files


class SpectralValidator(BaseValidatorStrategy):
    def __init__(self, spectral_path: str = "spectral", ruleset_path: Optional[str] = None):
        """
        Initialize the SpectralValidator.

        Args:
            spectral_path: Path to the spectral CLI executable (default: "spectral")
            ruleset_path: Path to a custom ruleset file. If None, uses bundled default ruleset.
        """
        self.spectral_path = spectral_path
        self.ruleset_path = ruleset_path

    def accepts(self) -> list[str]:
        return ["uri"]

    def _get_ruleset_path(self) -> str:
        """Get the path to the ruleset file to use."""
        if self.ruleset_path:
            return self.ruleset_path

        # Use bundled default ruleset
        try:
            ruleset_files = files("jentic_openapi_validator_spectral.rulesets")
            ruleset_content = ruleset_files.joinpath("spectral.yaml").read_text(encoding="utf-8")

            # Write to a temporary file that Spectral can read
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".spectral.yaml", delete=False, encoding="utf-8"
            ) as temp_file:
                temp_file.write(ruleset_content)
                parsed = urlparse(temp_file.name)
                file_path = url2pathname(parsed.path)
                return file_path

        except (ImportError, FileNotFoundError) as e:
            raise RuntimeError(f"Could not load bundled ruleset: {e}")

    def validate(self, document: str | dict) -> ValidationResult:
        """
        Validate an OpenAPI document using Spectral.

        Args:
            document: Path to the OpenAPI document file to validate

        Returns:
            ValidationResult containing any validation issues found
        """
        ruleset_temp_path = None

        try:
            assert isinstance(document, str)
            parsed_doc_url = urlparse(document)
            doc_path = url2pathname(parsed_doc_url.path)

            # Get ruleset path (may create temporary file)
            ruleset_path = self._get_ruleset_path()

            # Keep track of temp file for cleanup if we created one
            if not self.ruleset_path:
                ruleset_temp_path = ruleset_path

            # Build spectral command
            cmd = [
                self.spectral_path,
                "lint",
                doc_path,
                "-r",
                ruleset_path,  # Use the ruleset
                "-f",
                "json",
            ]
            completed = subprocess.run(cmd, check=False, capture_output=True, text=True)

        except FileNotFoundError:
            # Spectral not installed or not in PATH
            err_msg = "Spectral CLI not found. Please install @stoplight/spectral (npm) and ensure 'spectral' is in PATH."
            diagnostic = Diagnostic(
                range=Range(start=Position(line=0, character=0), end=Position(line=0, character=0)),
                message=err_msg,
                severity=DiagnosticSeverity.Error,
                code="0",
                source="spectral-validator",
            )
            return ValidationResult([diagnostic])
        finally:
            # Clean up temporary ruleset file if we created one
            if ruleset_temp_path and os.path.exists(ruleset_temp_path):
                try:
                    os.unlink(ruleset_temp_path)
                except OSError:
                    pass  # Ignore cleanup errors

        if completed.returncode not in (0, 1) or (completed.stderr and not completed.stdout):
            # According to Spectral docs, return code 2 might indicate lint errors found,
            # 0 means no issues, but let's not assume; we'll parse output.
            # If returncode is something else, spectral encountered an execution error.
            err = completed.stderr.strip() or completed.stdout.strip()
            msg = err or f"Spectral exited with code {completed.returncode}"
            raise Exception(msg)
        output = completed.stdout
        try:
            issues = json.loads(output)
        except json.JSONDecodeError:
            # If output isn't JSON (maybe spectral old version or error format), handle gracefully
            issues = []
        # issues is expected to be a list of findings if spectral reported any.
        messages = []
        for issue in issues:
            # Spectral JSON has fields like code, message, severity, path, range, etc.
            severity_code = issue.get("severity")  # e.g. "error" or numeric 0=error,1=warn...
            # Normalize severity to string
            severity = DiagnosticSeverity.Error
            if isinstance(severity_code, int):
                severity = (
                    DiagnosticSeverity.Error
                    if severity_code == 0
                    else DiagnosticSeverity.Warning
                    if severity_code == 1
                    else DiagnosticSeverity.Information
                )
            msg_text = issue.get("message", "")
            # location: combine file and jsonpath if available
            loc = ""
            if issue.get("path"):
                loc = f"path: {'.'.join(str(p) for p in issue['path'])}"

            range_info = issue.get("range", {})
            start_line = range_info.get("start", {}).get("line", 0)
            start_char = range_info.get("start", {}).get("character", 0)
            end_line = range_info.get("end", {}).get("line", start_line)
            end_char = range_info.get("end", {}).get("character", start_char)
            # TODO add jsonpath and other details to message if needed
            diagnostic = Diagnostic(
                range=Range(
                    start=Position(line=start_line, character=start_char),
                    end=Position(line=end_line, character=end_char),
                ),
                message=msg_text + " [" + loc + "]",
                severity=severity,
                code=issue.get("code"),
                source="spectral-validator",
            )

            messages.append(diagnostic)
        return ValidationResult(messages)
