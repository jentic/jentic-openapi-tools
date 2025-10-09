from collections.abc import Sequence
from typing import Literal

from jentic.apitools.openapi.transformer.bundler.backends.base import BaseBundlerBackend


__all__ = ["DefaultBundlerBackend"]


class DefaultBundlerBackend(BaseBundlerBackend):
    """
    Default bundler backend that performs basic pass-through bundling.

    This is a placeholder implementation that returns the document unchanged.
    In a production implementation, this would perform actual bundling operations
    like reference resolution, component extraction, etc.
    """

    def bundle(self, document: str | dict, *, base_url: str | None = None) -> dict:
        """
        Bundle an OpenAPI document using the default backend.

        Currently, performs no actual bundling - just validates the input
        and returns it unchanged.
        """
        if not isinstance(document, dict):
            raise TypeError(f"Default bundler expects dict input, got {type(document).__name__}")
        return document

    @staticmethod
    def accepts() -> Sequence[Literal["dict"]]:
        """Return supported input formats.

        Returns:
            Sequence of supported document format identifiers:
            - "dict": Python dictionary containing OpenAPI Document data
        """
        return ["dict"]
