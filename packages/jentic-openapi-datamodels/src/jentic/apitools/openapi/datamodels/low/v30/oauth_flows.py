from dataclasses import dataclass, field
from typing import Any

from ruamel import yaml

from ..context import Context
from ..extractors import extract_extension_fields
from ..fields import fixed_field, fixed_fields
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .oauth_flow import OAuthFlow
from .oauth_flow import build as build_oauth_flow


__all__ = ["OAuthFlows", "build"]


@dataclass(frozen=True, slots=True)
class OAuthFlows:
    """
    OAuth Flows Object representation for OpenAPI 3.0.

    A container for the list of possible OAuth 2.0 authorization flows.
    Used within Security Scheme Objects when type is set to "oauth2".

    Attributes:
        root_node: The top-level node representing the entire OAuth Flows object in the original source file
        implicit: Configuration for the OAuth Implicit flow
        password: Configuration for the OAuth Resource Owner Password flow
        client_credentials: Configuration for the OAuth Client Credentials flow (application flow)
        authorization_code: Configuration for the OAuth Authorization Code flow (three-legged OAuth)
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    implicit: FieldSource[OAuthFlow] | None = fixed_field()
    password: FieldSource[OAuthFlow] | None = fixed_field()
    client_credentials: FieldSource[OAuthFlow] | None = fixed_field(
        metadata={"yaml_name": "clientCredentials"}
    )
    authorization_code: FieldSource[OAuthFlow] | None = fixed_field(
        metadata={"yaml_name": "authorizationCode"}
    )
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> OAuthFlows | ValueSource[YAMLInvalidValue]:
    """
    Build an OAuthFlows object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        An OAuthFlows object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose("implicit:\\n  authorizationUrl: https://example.com/auth\\n  scopes: {}")
        flows = build(root)
        assert flows.implicit.value.authorization_url.value == 'https://example.com/auth'
    """
    context = context or Context()

    if not isinstance(root, yaml.MappingNode):
        # Preserve invalid root data instead of returning None
        value = context.yaml_constructor.construct_object(root, deep=True)
        return ValueSource(value=value, value_node=root)

    # Get fixed specification fields for this dataclass type
    _fixed_fields = fixed_fields(OAuthFlows)

    # Build YAML name to Python field name mapping
    yaml_to_field = {
        field.metadata.get("yaml_name", fname): fname for fname, field in _fixed_fields.items()
    }

    # Extract field values in a single pass
    field_values: dict[str, Any] = {}
    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        # Map YAML key to Python field name
        field_name = yaml_to_field.get(key)
        if field_name:
            # Build OAuthFlow for this field - child builder handles invalid nodes
            # FieldSource will auto-unwrap ValueSource if child returns it for invalid data
            oauth_flow = build_oauth_flow(value_node, context=context)
            field_values[field_name] = FieldSource(
                value=oauth_flow, key_node=key_node, value_node=value_node
            )

    return OAuthFlows(
        root_node=root,
        implicit=field_values.get("implicit"),
        password=field_values.get("password"),
        client_credentials=field_values.get("client_credentials"),
        authorization_code=field_values.get("authorization_code"),
        extensions=extract_extension_fields(root, context),
    )
