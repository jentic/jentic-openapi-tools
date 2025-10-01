import logging
from abc import ABC, abstractmethod
from typing import Any

__all__ = ["BaseParserBackend"]


class BaseParserBackend(ABC):
    """Interface that all Parser backends must implement."""

    @abstractmethod
    def parse(self, source: str, *, logger: logging.Logger | None = None) -> Any:
        """Parses an OpenAPI document given by URI or file path or text.
        Returns a dict."""
        ...

    @abstractmethod
    def accepts(self) -> list[str]: ...
