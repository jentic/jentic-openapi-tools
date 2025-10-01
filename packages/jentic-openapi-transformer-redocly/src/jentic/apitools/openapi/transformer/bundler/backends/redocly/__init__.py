import json
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

from jentic.apitools.openapi.transformer.bundler.backends.base import BaseBundlerBackend
from jentic.apitools.openapi.common.subproc import run_subprocess


__all__ = ["RedoclyBundlerBackend"]


class RedoclyBundlerBackend(BaseBundlerBackend):
    def __init__(self, redocly_path: str = "npx --yes @redocly/cli@^2.1.5", timeout: float = 30.0):
        """
        Initialize the RedoclyBundler.

        Args:
            redocly_path: Path to the redocly CLI executable (default: "npx --yes @redocly/cli@^2.1.5")
            timeout: Maximum time in seconds to wait for Redocly CLI execution (default: 30.0)
        """
        self.redocly_path = redocly_path
        self.timeout = timeout

    def accepts(self) -> list[str]:
        """Return the document formats this bundler can accept.

        Returns:
            List of supported document format identifiers:
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
        """
        if isinstance(document, str):
            return self._bundle_uri(document, base_url)
        elif isinstance(document, dict):
            return self._bundle_dict(document, base_url)
        else:
            raise TypeError(f"Unsupported document type: {type(document)!r}")

    def _bundle_uri(self, document: str, base_url: str | None = None) -> str:
        parsed_doc_url = urlparse(document)
        doc_path = url2pathname(parsed_doc_url.path)

        # Create a temporary output file path
        temp_output_path = tempfile.mktemp(suffix=".json")
        try:
            # Build redocly command
            cmd = [
                *self.redocly_path.split(),
                "bundle",
                doc_path,
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
            if result.returncode not in (0, 1):
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
            temp_file.flush()  # Ensure content is written to a disk

            return self._bundle_uri(Path(temp_file.name).as_uri(), base_url)
