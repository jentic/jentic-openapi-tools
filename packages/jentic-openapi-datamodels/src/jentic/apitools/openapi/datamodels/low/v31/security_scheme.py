from dataclasses import dataclass, field, replace

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .builders import build_model
from .oauth_flows import OAuthFlows
from .oauth_flows import build as build_oauth_flows
from .reference import Reference
from .reference import build as build_reference


__all__ = ["SecurityScheme", "build", "build_security_scheme_or_reference"]


@dataclass(frozen=True, slots=True)
class SecurityScheme:
    """
    Security Scheme Object representation for OpenAPI 3.1.

    Defines a security scheme that can be used by operations.
    The security scheme type determines which additional fields are required.

    Attributes:
        root_node: The top-level node representing the entire Security Scheme object in the original source file
        type: REQUIRED. The type of the security scheme. Valid values: "apiKey", "http", "oauth2", "openIdConnect"
        description: A short description for the security scheme. CommonMark syntax MAY be used for rich text representation
        name: REQUIRED for apiKey. The name of the header, query or cookie parameter to be used
        in_: REQUIRED for apiKey. The location of the API key. Valid values: "query", "header", "cookie"
        scheme: REQUIRED for http. The name of the HTTP Authorization scheme (e.g., "basic", "bearer")
        bearer_format: A hint to the client to identify how the bearer token is formatted (e.g., "JWT")
        flows: REQUIRED for oauth2. An object containing configuration information for the flow types supported
        openid_connect_url: REQUIRED for openIdConnect. OpenId Connect URL to discover OAuth2 configuration values
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    type: FieldSource[str] | None = fixed_field()
    description: FieldSource[str] | None = fixed_field()
    name: FieldSource[str] | None = fixed_field()
    in_: FieldSource[str] | None = fixed_field(metadata={"yaml_name": "in"})
    scheme: FieldSource[str] | None = fixed_field()
    bearer_format: FieldSource[str] | None = fixed_field(metadata={"yaml_name": "bearerFormat"})
    flows: FieldSource[OAuthFlows] | None = fixed_field()
    openid_connect_url: FieldSource[str] | None = fixed_field(
        metadata={"yaml_name": "openIdConnectUrl"}
    )
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> SecurityScheme | ValueSource[YAMLInvalidValue]:
    """
    Build a SecurityScheme object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A SecurityScheme object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose("type: apiKey\\nname: api_key\\nin: header")
        security_scheme = build(root)
        assert security_scheme.type.value == 'apiKey'
    """
    context = context or Context()

    # Use build_model for initial construction
    security_scheme = build_model(root, SecurityScheme, context=context)

    # If build_model returned ValueSource (invalid node), return it immediately
    if not isinstance(security_scheme, SecurityScheme):
        return security_scheme

    # Manually handle special fields that build_model can't process (nested objects)
    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        if key == "flows":
            # Handle nested OAuthFlows object - child builder handles invalid nodes
            # FieldSource will auto-unwrap ValueSource if child returns it for invalid data
            flows = FieldSource(
                value=build_oauth_flows(value_node, context=context),
                key_node=key_node,
                value_node=value_node,
            )
            security_scheme = replace(security_scheme, flows=flows)
            break

    return security_scheme


def build_security_scheme_or_reference(
    node: yaml.Node, context: Context
) -> SecurityScheme | Reference | ValueSource[YAMLInvalidValue]:
    """
    Build either a SecurityScheme or Reference from a YAML node.

    This helper handles the polymorphic nature of OpenAPI where many fields
    can contain either a SecurityScheme object or a Reference object ($ref).

    Args:
        node: The YAML node to parse
        context: Parsing context

    Returns:
        A SecurityScheme, Reference, or ValueSource if the node is invalid
    """
    # Check if it's a reference (has $ref key)
    if isinstance(node, yaml.MappingNode):
        for key_node, _ in node.value:
            key = context.yaml_constructor.construct_yaml_str(key_node)
            if key == "$ref":
                return build_reference(node, context)

    # Otherwise, try to build as SecurityScheme
    return build(node, context)
