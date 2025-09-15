from .ruamel_strategy import RuamelOpenAPIParser


class RuamelRoundTripOpenAPIParser(RuamelOpenAPIParser):
    def __init__(self, pure: bool = True):
        super().__init__(typ="rt", pure=pure)
