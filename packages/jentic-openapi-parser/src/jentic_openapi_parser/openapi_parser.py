from typing import Any, Mapping, Optional
import requests
import yaml
import json

from .uri import is_uri_like, resolve_to_absolute


class OpenAPIParser:
    def is_uri_like(self, s: Optional[str]) -> bool:
        return is_uri_like(s)

    def load_uri(self, uri: str) -> str:
        resolved_uri = resolve_to_absolute(uri)

        if resolved_uri.startswith("http://") or uri.startswith("https://"):
            content = requests.get(resolved_uri).text
        elif resolved_uri.startswith("file://"):
            with open(resolved_uri, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            # Treat as local file path
            with open(resolved_uri, "r", encoding="utf-8") as f:
                content = f.read()
        return content

    def parse(self, source: str) -> dict[str, Any]:
        text = source
        try:
            if is_uri_like(source):
                text = self.load_uri(source)

            data = self.parse_text(text)
        except Exception:
            msg = f"Unsupported document type: {type(source)!r}"
            raise TypeError(msg)
        return data

    def parse_uri(self, uri: str) -> dict[str, Any]:
        return self.parse_text(self.load_uri(uri))

    def parse_text(self, text: str) -> dict[str, Any]:
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
