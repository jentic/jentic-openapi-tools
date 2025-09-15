from abc import ABC, abstractmethod
from typing import Any


class BaseParserStrategy(ABC):
    """Interface that all Parser plugins must implement."""

    @abstractmethod
    def parse(self, source: str) -> Any:
        """Parses an OpenAPI document given by URI or file path or text.
        Returns a dict."""
        pass

    @abstractmethod
    def accepts(self) -> list[str]:
        pass
