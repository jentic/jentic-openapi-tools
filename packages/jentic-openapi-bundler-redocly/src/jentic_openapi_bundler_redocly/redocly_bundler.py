from typing import Any
from urllib.parse import urlparse
from urllib.request import url2pathname

from jentic_openapi_transformer.strategies.base import BaseBundlerStrategy

from .subprocess import run_checked


class RedoclyBundler(BaseBundlerStrategy):
    def __init__(self, redocly_path: str = "redocly"):
        """
        Initialize the RedoclyBundler.

        Args:
            redocly_path: Path to the redocly CLI executable (default: "redocly")
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
        parsed_doc_url = urlparse(document)
        doc_path = url2pathname(parsed_doc_url.path)
        # Build redocly command
        cmd = [
            self.redocly_path,
            "bundle",
            doc_path,
            "--ext",
            "json",
            # "--remove-unused-components", # TODO, raises errors in redocly for some reason
        ]
        result = run_checked(cmd)
        output_lines = result[0].splitlines()
        if output_lines and output_lines[-1].startswith("Created a bundle"):
            output_lines = output_lines[:-1]

        return "\n".join(output_lines)
