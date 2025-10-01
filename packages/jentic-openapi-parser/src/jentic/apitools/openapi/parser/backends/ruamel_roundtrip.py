from jentic.apitools.openapi.parser.backends.ruamel import RuamelParserBackend


__all__ = ["RuamelRoundTripParserBackend"]


class RuamelRoundTripParserBackend(RuamelParserBackend):
    def __init__(self, pure: bool = True):
        super().__init__(typ="rt", pure=pure)
