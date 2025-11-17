from dataclasses import dataclass, field, replace

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .builders import build_field_source, build_model
from .server_variable import ServerVariable
from .server_variable import build as build_server_variable


__all__ = ["Server", "build"]


@dataclass(frozen=True, slots=True)
class Server:
    """
    Server Object representation for OpenAPI 3.0.

    An object representing a Server.

    Attributes:
        root_node: The top-level node representing the entire Server object in the original source file
        url: REQUIRED. A URL to the target host. This URL supports Server Variables and MAY be relative, to indicate that the host location is relative to the location where the OpenAPI document is being served. Variable substitutions will be made when a variable is named in {brackets}.
        description: An optional string describing the host designated by the URL. CommonMark syntax MAY be used for rich text representation.
        variables: A map between a variable name and its value. The value is used for substitution in the server's URL template.
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    url: FieldSource[str] | None = fixed_field()
    description: FieldSource[str] | None = fixed_field()
    variables: FieldSource[dict[KeySource[str], ServerVariable]] | None = fixed_field()
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> Server | ValueSource[YAMLInvalidValue]:
    """
    Build a Server object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A Server object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose('''
        url: https://{environment}.example.com/api/v1
        description: Production API server
        variables:
          environment:
            default: production
            enum:
              - production
              - staging
              - development
            description: The deployment environment
        ''')
        server = build(root)
        assert server.url.value == 'https://{environment}.example.com/api/v1'
        assert server.description.value == 'Production API server'
        assert 'environment' in {k.value for k in server.variables.value.keys()}
    """
    context = context or Context()

    # Use build_model for initial construction
    server = build_model(root, Server, context=context)

    # If build_model returned ValueSource (invalid node), return it immediately
    if not isinstance(server, Server):
        return server

    # Manually handle nested variables field
    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        if key == "variables":
            # Handle variables field - map of ServerVariable objects
            if isinstance(value_node, yaml.MappingNode):
                variables_dict: dict[
                    KeySource[str], ServerVariable | ValueSource[YAMLInvalidValue]
                ] = {}
                for var_key_node, var_value_node in value_node.value:
                    var_key = context.yaml_constructor.construct_yaml_str(var_key_node)
                    # Build ServerVariable for each variable - child builder handles invalid nodes
                    variables_dict[KeySource(value=var_key, key_node=var_key_node)] = (
                        build_server_variable(var_value_node, context=context)
                    )
                variables = FieldSource(
                    value=variables_dict, key_node=key_node, value_node=value_node
                )
                server = replace(server, variables=variables)
            else:
                # Not a mapping - preserve as-is for validation
                variables = build_field_source(key_node, value_node, context)
                server = replace(server, variables=variables)
            break

    return server
