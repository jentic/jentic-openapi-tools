import json
from typing import Optional, Union, Literal
import tempfile
import os
from urllib.parse import urlparse
from urllib.request import url2pathname

from jentic_openapi_common import run_checked, SubprocessExecutionError
from lsprotocol.types import DiagnosticSeverity, Range, Position

from jentic_openapi_validator import ValidationResult, JenticDiagnostic
from jentic_openapi_validator.strategies.base import BaseValidatorStrategy
from importlib.resources import files


class RedoclyValidator(BaseValidatorStrategy):
    def __init__(
        self,
        redocly_path: str = "npx --yes @redocly/cli@latest",
        ruleset_path: Optional[str] = None,
    ):
        """
        Initialize the RedoclyValidator.

        Args:
            redocly_path: Path to the Redocly CLI executable (default: "npx --yes @redocly/cli@latest")
            ruleset_path: Path to a custom ruleset file. If None, uses bundled default ruleset.
        """
        self.redocly_path = redocly_path
        self.ruleset_path = ruleset_path

    @staticmethod
    def accepts() -> list[Literal["uri", "text", "dict"]]:
        return ["uri"]

    def _get_ruleset_path(self) -> str:
        """Get the path to the ruleset file to use."""
        if self.ruleset_path:
            return self.ruleset_path

        # Use bundled default ruleset
        try:
            ruleset_files = files("jentic_openapi_validator_spectral.rulesets")
            ruleset_content = ruleset_files.joinpath("redocly.yaml").read_text(encoding="utf-8")

            # Write to a temporary file that redocly can read
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".redocly.yaml", delete=False, encoding="utf-8"
            ) as temp_file:
                temp_file.write(ruleset_content)
                parsed = urlparse(temp_file.name)
                file_path = url2pathname(parsed.path)
                return file_path

        except (ImportError, FileNotFoundError) as e:
            raise RuntimeError(f"Could not load bundled ruleset: {e}")

    def validate(
        self, document: str | dict, *, base_url: str | None = None, target: str | None = None
    ) -> ValidationResult:
        """
        Validate an OpenAPI document using Redocly.

        Args:
            document: Path to the OpenAPI document file to validate

        Returns:
            ValidationResult containing any validation issues found
        """
        ruleset_temp_path = None
        try:
            assert isinstance(document, str)
            parsed_doc_url = urlparse(document)
            doc_path = document
            if parsed_doc_url.scheme == "file":
                doc_path = url2pathname(parsed_doc_url.path)

            # Get ruleset path (may create temporary file)
            ruleset_path = self._get_ruleset_path()

            # Keep track of temp file for cleanup if we created one
            if not self.ruleset_path:
                ruleset_temp_path = ruleset_path

            # Build redocly command
            cmd = [
                *self.redocly_path.split(),
                "lint",
                "--config",
                ruleset_path,
                "--format",
                "json",
                doc_path,
            ]
            result = run_checked(cmd)

        except SubprocessExecutionError as e:
            # only timeout and OS errors, as run_checked has default `fail_on_error = False`
            raise e

        finally:
            # Clean up temporary ruleset file if we created one
            if ruleset_temp_path and os.path.exists(ruleset_temp_path):
                try:
                    os.unlink(ruleset_temp_path)
                except OSError:
                    pass  # Ignore cleanup errors
        if result.returncode not in (0, 1) or (result.stderr and not result.stdout):
            # According to Redocly docs, return code 2 means a execution error.
            # 0 means no issues at error level, 1 means issues found at error level.
            err = result.stderr.strip() or result.stdout.strip()
            msg = err or f"redocly exited with code {result.returncode}"
            raise Exception(msg)

        output = result.stdout
        try:
            issues = json.loads(output)
        except json.JSONDecodeError as e:
            print(f"Redocly output is not valid JSON: {output}")
            raise Exception(e)
        # issues is expected to be a list of findings if redocly reported any.
        problems = issues.get("problems") or []

        messages = []
        for issue in problems:
            locations = []
            if issue.get("location") and len(issue.get("location")) > 0:
                location_paths = issue.get("location")
                for location_path in location_paths:
                    pointer = location_path.get("pointer")
                    data = {"fixable": True, "path": []}
                    path = []
                    loc = ""
                    if pointer:
                        path = RedoclyValidator._json_pointer_to_path_list(pointer)
                        loc = f"path: {'.'.join(str(p) for p in path)}"
                        data = {"fixable": True, "path": path}
                    locations.append([path, loc, data])
            if len(locations) == 0:
                locations.append([[], "", {"fixable": True, "path": []}])

            for location in locations:
                # Redocly JSON has fields like code, message, severity, etc.
                severity_code = issue.get("severity")  # e.g. "error"
                # Normalize severity to string
                severity = DiagnosticSeverity.Information
                if isinstance(severity_code, str):
                    severity = (
                        DiagnosticSeverity.Error
                        if severity_code == "error"
                        else DiagnosticSeverity.Warning
                        if severity_code == "warn"
                        else DiagnosticSeverity.Information
                    )
                msg_text = issue.get("message", "")

                diagnostic = JenticDiagnostic(
                    range=Range(
                        start=Position(line=0, character=0),
                        end=Position(line=0, character=0),
                    ),
                    message=msg_text + " [" + location[1] + "]",
                    severity=severity,
                    code=issue.get("ruleId"),
                    source="redocly-validator",
                )
                diagnostic.data = location[2]
                diagnostic.set_target(target)
                messages.append(diagnostic)
        return ValidationResult(messages)

    @staticmethod
    def _json_pointer_to_path_list(
        pointer: str,
        *,
        coerce_indices: bool = True,
    ) -> list[Union[str, int]]:
        """
        Convert a JSON Pointer (RFC 6901) into path array.
        - Accepts an optional leading '#', which will be stripped.
        - Properly unescapes '~1' -> '/' and '~0' -> '~'.
        - If coerce_indices=True, tokens that are canonical non-negative integers
          (no leading zeros, except '0' itself) are returned as int.

        Examples:
            "#/paths/~1pets/get/parameters/0/schema/type"
                -> ["paths", "/pets", "get", "parameters", 0, "schema", "type"]

            ""  -> []          (root)
            "#" -> []          (root as fragment)
            "/a//b" -> ["a", "", "b"]   (empty key supported by JSON Pointer)
        """
        if pointer.startswith("#"):
            pointer = pointer[1:]

        # Root pointer
        if pointer in ["", "/"]:
            return []

        if not pointer.startswith("/"):
            raise ValueError("Invalid JSON Pointer: must start with '/' (or be empty).")

        tokens = pointer.split("/")[1:]  # skip leading empty segment from the initial '/'

        path: list[Union[str, int]] = []
        for raw in tokens:
            seg = RedoclyValidator.unescape_token(raw)

            if coerce_indices:
                # Treat canonical non-negative integers as array indices:
                # '0' or non-zero followed by digits, no leading zeros like '01'.
                if seg == "0" or (seg.isdigit() and not seg.startswith("0")):
                    path.append(int(seg))
                    continue

            path.append(seg)

        return path

    @staticmethod
    def unescape_token(token: str) -> str:
        return token.replace("~1", "/").replace("~0", "~")
