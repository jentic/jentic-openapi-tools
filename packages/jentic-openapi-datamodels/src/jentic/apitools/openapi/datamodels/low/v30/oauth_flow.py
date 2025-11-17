from dataclasses import dataclass, field

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .builders import build_model


__all__ = ["OAuthFlow", "build"]


@dataclass(frozen=True, slots=True)
class OAuthFlow:
    """
    OAuth Flow Object representation for OpenAPI 3.0.

    Configuration details for a supported OAuth Flow.

    Attributes:
        root_node: The top-level node representing the entire OAuth Flow object in the original source file
        authorization_url: The authorization URL to be used for this flow. REQUIRED for implicit and authorization_code flows.
        token_url: The token URL to be used for this flow. REQUIRED for password, client_credentials, and authorization_code flows.
        refresh_url: The URL to be used for obtaining refresh tokens. This MUST be in the form of a URL.
        scopes: The available scopes for the OAuth2 security scheme. A map between the scope name and a short description for it.
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    authorization_url: FieldSource[str] | None = fixed_field(
        metadata={"yaml_name": "authorizationUrl"}
    )
    token_url: FieldSource[str] | None = fixed_field(metadata={"yaml_name": "tokenUrl"})
    refresh_url: FieldSource[str] | None = fixed_field(metadata={"yaml_name": "refreshUrl"})
    scopes: FieldSource[dict[KeySource[str], ValueSource[str]]] | None = fixed_field()
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> OAuthFlow | ValueSource[YAMLInvalidValue]:
    """
    Build an OAuthFlow object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        An OAuthFlow object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose("tokenUrl: https://example.com/oauth/token\\nscopes:\\n  read: Read access")
        oauth_flow = build(root)
        assert oauth_flow.tokenUrl.value == 'https://example.com/oauth/token'
    """
    return build_model(root, OAuthFlow, context=context)
