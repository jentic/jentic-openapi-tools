from jentic.apitools.openapi.parser.core import OpenAPIParser


def normalize(source: str) -> dict:
    """
    Parse and perform a trivial 'normalization' to prove the flow works.
    Later: real bundling, $ref deref, component hoisting, etc.
    """
    parse_result = dict(OpenAPIParser().parse(source))
    parse_result.setdefault("x-jentic", {})["transformed"] = True

    return parse_result
