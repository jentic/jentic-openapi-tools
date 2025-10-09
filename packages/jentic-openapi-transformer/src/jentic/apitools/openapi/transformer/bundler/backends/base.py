from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any


__all__ = ["BaseBundlerBackend"]


class BaseBundlerBackend(ABC):
    """
    Base interface that all bundler backends must implement.

    Bundler backends are responsible for taking OpenAPI documents and transforming
    them through various operations like bundling, reference resolution, component
    extraction, etc.
    """

    @abstractmethod
    def bundle(self, document: str | dict, *, base_url: str | None = None) -> Any:
        """
        Bundle an OpenAPI document.

        Args:
            document: The OpenAPI document to bundle. Can be a string (JSON/YAML)
                     or a dict representation.
            base_url: Optional base URI for resolving relative references.

        Returns:
            The bundled OpenAPI document. Type conversion is handled by the main bundler class.

        Raises:
            Exception: If bundling fails for any reason.
        """
        ...

    @staticmethod
    @abstractmethod
    def accepts() -> Sequence[str]:
        """
        Return a sequence of input formats this backend can handle.

        Returns:
            Sequence of supported input formats. Common values:
            - "dict": Accepts dictionary/object representation
            - "text": Accepts string (JSON/YAML) representation
            - "uri": Accepts URI/file path references
        """
        ...
