from typing import Any
from .base import BaseBundlerStrategy


class DefaultOpenAPIBundler(BaseBundlerStrategy):
    def bundle(self, document: str | dict, base_url: str | None = None) -> Any:
        try:
            assert isinstance(document, dict)
            return self._bundle(document, base_url)  # TODO implement real bundler
        except Exception as e:
            # TODO add to parser/validation chain result
            raise e

    def _bundle(self, document: str | dict, base_url: str | None = None) -> str | dict:
        # TODO real native implementation, replace placeholder
        return document

    def accepts(self) -> list[str]:
        return ["dict"]
