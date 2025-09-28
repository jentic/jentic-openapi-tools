import importlib.metadata

from jentic_openapi_parser import OpenAPIParser
from .strategies.openapi_spec_validator_strategy import OpenAPISpecValidator
from .diagnostics import ValidationResult
from .strategies.base import BaseValidatorStrategy
from .strategies.default.default_strategy import DefaultOpenAPIValidator


class OpenAPIValidator:
    def __init__(self, strategies: list | None = None, parser: OpenAPIParser | None = None):
        if not parser:
            parser = OpenAPIParser()
        self.parser = parser
        # If no strategies specified, use default
        if not strategies:
            strategies = ["default"]
        self.strategies = []  # list of BaseValidatorStrategy instances

        # Discover entry points for validator plugins
        # (This could be a one-time load stored at class level to avoid doing it every time)
        eps = importlib.metadata.entry_points(group="jentic.openapi_validator_strategies")
        plugin_map = {ep.name: ep for ep in eps}

        for strat in strategies:
            if isinstance(strat, str):
                name = strat
                if name == "default":
                    # Use built-in default validator
                    self.strategies.append(DefaultOpenAPIValidator())
                elif name == "openapi-spec-validator":
                    self.strategies.append(OpenAPISpecValidator())
                elif name in plugin_map:
                    plugin_class = plugin_map[name].load()  # loads the class
                    self.strategies.append(plugin_class())
                else:
                    raise ValueError(f"No validator plugin named '{name}' found")
            elif isinstance(strat, BaseValidatorStrategy):
                self.strategies.append(strat)
            elif hasattr(strat, "__call__") and issubclass(strat, BaseValidatorStrategy):
                # if a class (not instance) is passed
                self.strategies.append(strat())
            else:
                raise TypeError("Invalid strategy type: must be name or strategy class/instance")

    def validate(
        self, source: str | dict, *, base_url: str | None = None, target: str | None = None
    ) -> ValidationResult:
        text = source
        all_messages = []
        data = None
        if isinstance(source, str):
            is_uri = self.parser.is_uri_like(source)
            is_text = not is_uri

            if is_text:
                data = self.parser.parse(source)

            if is_uri and self.has_non_uri_strategy():
                text = self.parser.load_uri(source)
                if not data or data is None:
                    data = self.parser.parse(text)
        else:
            is_uri = False
            is_text = False
        if not data or data is None:
            data = text

        for strat in self.strategies:
            document = None
            if is_uri and "uri" in strat.accepts():
                document = source
            elif is_uri and "text" in strat.accepts():
                document = text
            elif is_uri and "dict" in strat.accepts():
                document = data
            elif not is_uri and "text" in strat.accepts():
                document = text
            elif not is_uri and "dict" in strat.accepts():
                document = data

            if document is not None:
                result = strat.validate(document, base_url=base_url, target=target)
                all_messages.extend(result.diagnostics)

        return ValidationResult(all_messages)

    def has_non_uri_strategy(self) -> bool:
        """Check if any strategy accepts 'text' or 'dict' but not 'uri'."""
        for strat in self.strategies:
            accepted = strat.accepts()
            if ("text" in accepted or "dict" in accepted) and "uri" not in accepted:
                return True
        return False

    @staticmethod
    def list_strategies() -> list[str]:
        strategies = ["default", "openapi-spec-validator"]
        eps = importlib.metadata.entry_points(group="jentic.openapi_validator_strategies")
        plugin_map = {ep.name: ep for ep in eps}
        for plugin_name, entry_point in plugin_map.items():
            strategies.append(plugin_name)
        return strategies
