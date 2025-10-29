from dataclasses import dataclass, field

from ruamel.yaml import YAML
from ruamel.yaml.constructor import RoundTripConstructor


__all__ = ["Context"]


@dataclass(frozen=True, slots=True)
class Context:
    """
    Context for parsing OpenAPI documents.

    Contains configuration and dependencies used during parsing operations.

    Attributes:
        yaml_constructor: The YAML constructor used to deserialize YAML nodes into Python objects
    """

    yaml_constructor: RoundTripConstructor = field(default=YAML(typ="rt", pure=True).constructor)
