from abc import ABC, abstractmethod
from typing import Any


class BaseBundlerStrategy(ABC):
    """Interface that all Bundler plugins must implement."""

    @abstractmethod
    def bundle(self, document: str | dict, base_url: str | None = None) -> Any:
        """Bundle an OpenAPI document given by URI or file path or text.
        Returns a BundlerResult."""
        pass

    @abstractmethod
    def accepts(self) -> list[str]:
        pass
