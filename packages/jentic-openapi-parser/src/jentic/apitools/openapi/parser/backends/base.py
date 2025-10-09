import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any


__all__ = ["BaseParserBackend"]


class BaseParserBackend(ABC):
    """Interface that all Parser backends must implement."""

    @abstractmethod
    def parse(self, document: str, *, logger: logging.Logger | None = None) -> Any:
        """Parses an OpenAPI document given by URI or file path or text.
        Returns a dict."""
        ...

    @staticmethod
    @abstractmethod
    def accepts() -> Sequence[str]:
        """Return a sequence of input formats this backend can handle.

        Returns:
            Sequence of supported input formats. Common values:
            - "uri": Accepts URI/file path references
            - "text": Accepts string (JSON/YAML) representation
        """
        ...
