import json
import shlex
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from jentic.apitools.openapi.common.path_security import validate_path
from jentic.apitools.openapi.common.subproc import run_subprocess
from jentic.apitools.openapi.common.uri import file_uri_to_path, is_file_uri, is_path
from jentic.apitools.openapi.transformer.bundler.backends.base import BaseBundlerBackend


__all__ = ["RedoclyBundlerBackend"]


class RedoclyBundlerBackend(BaseBundlerBackend):
    def __init__(
        self,
        redocly_path: str = "npx --yes @redocly/cli@^2.4.0",
        timeout: float = 600.0,
        allowed_base_dir: str | Path | None = None,
    ):
        """
        Initialize the RedoclyBundler.

        Args:
            redocly_path: Path to the redocly CLI executable (default: "npx --yes @redocly/cli@^2.4.0").
                Uses shell-safe parsing to handle quoted arguments properly.
            timeout: Maximum time in seconds to wait for Redocly CLI execution (default: 600.0)
            allowed_base_dir: Optional base directory for path security validation.
                When set, all document paths will be validated to ensure they
                are within this directory. This provides defense against path traversal attacks
                and is recommended for web services or when processing untrusted input.
                If None (default), only file extension validation is performed (no base directory
                containment check). Extension validation ensures only .yaml, .yml, and .json files
                are processed.
        """
        self.redocly_path = redocly_path
        self.timeout = timeout
        self.allowed_base_dir = allowed_base_dir

    @staticmethod
    def accepts() -> Sequence[Literal["uri", "dict"]]:
        """Return the document formats this bundler can accept.

        Returns:
            Sequence of supported document format identifiers:
            - "uri": File path or URI pointing to OpenAPI Document
            - "dict": Python dictionary containing OpenAPI Document data
        """
        return ["uri", "dict"]

    def bundle(self, document: str | dict, *, base_url: str | None = None) -> str:
        """
        Bundle an OpenAPI document using Redocly CLI.

        Args:
            document: Path to the OpenAPI document file to bundle, or dict containing the document
            base_url: Base URL for resolving relative references (currently unused)

        Returns:
            Bundled OpenAPI document as a JSON string

        Raises:
            TypeError: If a document type is not supported
            SubprocessExecutionError: If Redocly execution times out or fails to start
            RuntimeError: If Redocly execution fails
            PathTraversalError: Document path attempts to escape allowed_base_dir (only when allowed_base_dir is set)
            InvalidExtensionError: Document path has disallowed file extension (always checked for filesystem paths)
        """
        if isinstance(document, str):
            return self._bundle_uri(document, base_url)
        elif isinstance(document, dict):
            return self._bundle_dict(document, base_url)
        else:
            raise TypeError(f"Unsupported document type: {type(document)!r}")

    def _bundle_uri(self, document: str, base_url: str | None = None) -> str:
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

        # Create a temporary output file path
        temp_output_path = tempfile.mktemp(suffix=".json")
        try:
            # Build redocly command
            cmd = [
                *shlex.split(self.redocly_path),
                "bundle",
                validated_doc_path,
                "-o",
                temp_output_path,
                "--ext",
                "json",
                "--lint-config",
                "off",
                "--force",
                # TODO(francesco@jentic.com): raises errors in redocly for unknown reason
                # "--remove-unused-components",
            ]
            result = run_subprocess(cmd, timeout=self.timeout)

            # Check if bundling was successful based on return code
            if result.returncode != 0:
                err = (result.stderr or "").strip()
                msg = err or f"Redocly exited with code {result.returncode}"
                raise RuntimeError(msg)

            # Verify an output file was created
            output_path = Path(temp_output_path)
            if not output_path.exists():
                # Return code was OK but no output file - unexpected failure
                err = (result.stderr or "").strip()
                msg = err or "Redocly exited successfully but produced no output file"
                raise RuntimeError(msg)

            return output_path.read_text(encoding="utf-8")
        finally:
            # Clean up the temporary file if it was created
            output_path = Path(temp_output_path)
            if output_path.exists():
                output_path.unlink()

    def _bundle_dict(self, document: dict, base_url: str | None = None) -> str:
        """Bundle a dict document by creating a temporary file and using _bundle_uri."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=True, encoding="utf-8"
        ) as temp_file:
            json.dump(document, temp_file)
            temp_file.flush()  # Ensure content is written to disk

            return self._bundle_uri(Path(temp_file.name).as_uri(), base_url)
