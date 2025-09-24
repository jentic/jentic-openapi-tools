from typing import Any
from urllib.parse import urlparse
from urllib.request import url2pathname

from jentic.apitools.openapi.transformer.strategies.base import BaseBundlerStrategy

from jentic.apitools.openapi.common.subproc import run_subprocess, SubprocessExecutionError


class RedoclyBundler(BaseBundlerStrategy):
    def __init__(self, redocly_path: str = "npx @redocly/cli@^2.1.5"):
        """
        Initialize the RedoclyBundler.

        Args:
            redocly_path: Path to the redocly CLI executable (default: "npx @redocly/cli@^2.1.5")
        """
        self.redocly_path = redocly_path

    def accepts(self) -> list[str]:
        return ["uri"]

    def bundle(self, document: str | dict, base_url: str | None = None) -> Any:
        try:
            assert isinstance(document, str)
            return self._bundle(document, base_url)
        except Exception as e:
            # TODO add to parser/validation chain result
            raise e

    def _bundle(self, document: str, base_url: str | None = None) -> str:
        try:
            parsed_doc_url = urlparse(document)
            doc_path = url2pathname(parsed_doc_url.path)
            # Build redocly command
            cmd = [
                *self.redocly_path.split(),
                "bundle",
                doc_path,
                "--ext",
                "json",
                "--lint-config",
                "off",
                "--force",
                # "--remove-unused-components", # TODO, raises errors in redocly for some reason
            ]
            result = run_subprocess(cmd)
        except SubprocessExecutionError as e:
            # only timeout and OS errors, as run_subprocess has default `fail_on_error = False`
            raise e

        if result.stdout:
            # When using `--force` Redocly tries bundling even on errors
            output_lines = result.stdout.splitlines()
            if output_lines and output_lines[-1].startswith("Created a bundle"):
                output_lines = output_lines[:-1]

            if result.returncode != 0 and result.stderr:
                # TODO we need to add any errors to the parser/validation chain result
                print(f"Error parsing document: {result.stderr}")

            return "\n".join(output_lines)
        else:
            err = (result.stderr or "").strip()
            msg = err or f"Redocly exited with code {result.returncode}"
            raise Exception(msg)
