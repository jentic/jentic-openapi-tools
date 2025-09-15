from typing import Any, Mapping
import yaml
import json
from .base import BaseParserStrategy
from ..uri import is_uri_like, load_uri


class DefaultOpenAPIParser(BaseParserStrategy):
    def parse(self, source: str) -> Any:
        text = source
        try:
            if is_uri_like(source):
                text = load_uri(source)

            data = self.parse_text(text)
        except Exception:
            msg = f"Unsupported document type: {type(source)!r}"
            raise TypeError(msg)
        return data

    def parse_uri(self, uri: str) -> Any:
        return self.parse_text(load_uri(uri))

    def parse_text(self, text: str) -> Any:
        try:
            data = yaml.safe_load(text)
        except Exception:
            if isinstance(text, (bytes, str)):
                text = text.decode() if isinstance(text, bytes) else text
                data = json.loads(text)
        if isinstance(data, Mapping):
            return dict(data)
        msg = f"Unsupported document type: {type(text)!r}"
        raise TypeError(msg)

    def accepts(self) -> list[str]:
        return ["uri", "text"]
