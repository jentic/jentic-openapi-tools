from ruamel.yaml import CommentedMap

from jentic.apitools.openapi.parser.backends.ruamel_safe import RuamelSafeParserBackend


__all__ = [
    "RuamelRoundTripParserBackend",
    # Re-export CommentedMap type for convenience
    "CommentedMap",
]


class RuamelRoundTripParserBackend(RuamelSafeParserBackend):
    def __init__(self, pure: bool = True):
        super().__init__(typ="rt", pure=pure)
