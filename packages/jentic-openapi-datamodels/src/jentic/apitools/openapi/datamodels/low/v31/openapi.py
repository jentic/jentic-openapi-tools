from dataclasses import dataclass, field, replace

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .builders import build_field_source, build_model
from .components import Components
from .components import build as build_components
from .external_documentation import ExternalDocumentation
from .info import Info
from .info import build as build_info
from .path_item import PathItem
from .paths import Paths
from .paths import build as build_paths
from .security_requirement import SecurityRequirement
from .server import Server
from .tag import Tag
from .tag import build as build_tag


__all__ = ["OpenAPI31", "build"]


@dataclass(frozen=True, slots=True)
class OpenAPI31:
    """
    OpenAPI Object representation for OpenAPI 3.1.

    This is the root document object of the OpenAPI document.

    Note: This class uses full duplication (not inheritance from OpenAPI30) to enable precise
    version detection via isinstance() checks. This is critical for validators and converters
    that need to distinguish between OpenAPI 3.0 and 3.1 specifications, as the two versions
    have different validation rules (e.g., paths is required in 3.0 but optional in 3.1).

    Attributes:
        root_node: The top-level node representing the entire OpenAPI object in the original source file
        openapi: REQUIRED. The version number of the OpenAPI Specification that the document uses.
                 Must match the specification version (e.g., "3.1.0", "3.1.1", "3.1.2").
        info: REQUIRED. Provides metadata about the API (title, version, description, etc.)
        json_schema_dialect: The default value for the $schema keyword within Schema Objects in this OAS document.
        servers: An array of Server Objects providing connectivity information to target servers
        paths: The available paths and operations for the API. In OpenAPI 3.1, this is no longer strictly
               required if components or webhooks are present.
        webhooks: The incoming webhooks that MAY be received as part of this API and that the API consumer
                  MAY choose to implement. A map of PathItem Objects.
        components: An element to hold reusable objects for different aspects of the OAS
        security: A declaration of which security mechanisms can be used across the API
        tags: A list of tags used by the specification with additional metadata
        external_docs: Additional external documentation
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    openapi: FieldSource[str] | None = fixed_field()
    info: FieldSource[Info] | None = fixed_field()
    json_schema_dialect: FieldSource[str] | None = fixed_field(
        metadata={"yaml_name": "jsonSchemaDialect"}
    )
    servers: FieldSource[list["Server"]] | None = fixed_field()
    paths: FieldSource[Paths] | None = fixed_field()
    webhooks: FieldSource[dict[KeySource[str], "PathItem"]] | None = fixed_field()
    components: FieldSource[Components] | None = fixed_field()
    security: FieldSource[list["SecurityRequirement"]] | None = fixed_field()
    tags: FieldSource[list[Tag]] | None = fixed_field()
    external_docs: FieldSource["ExternalDocumentation"] | None = fixed_field(
        metadata={"yaml_name": "externalDocs"}
    )
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> OpenAPI31 | ValueSource[YAMLInvalidValue]:
    """
    Build an OpenAPI 3.1 object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        An OpenAPI31 object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose('''
        openapi: 3.1.2
        info:
          title: Sample API
          version: 1.0.0
        paths:
          /users:
            get:
              responses:
                '200':
                  description: Success
        webhooks:
          newPet:
            post:
              requestBody:
                description: Pet to add
        ''')
        openapi_doc = build(root)
        assert openapi_doc.openapi.value == '3.1.2'
        assert openapi_doc.info.value.title.value == 'Sample API'
    """
    context = context or Context()

    # Use build_model for initial construction
    openapi_obj = build_model(root, OpenAPI31, context=context)

    # If build_model returned ValueSource (invalid node), return it immediately
    if not isinstance(openapi_obj, OpenAPI31):
        return openapi_obj

    # Manually handle nested complex fields and list fields with custom builders
    replacements = {}
    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        if key == "info":
            # Handle info field - Info object
            replacements["info"] = FieldSource(
                value=build_info(value_node, context), key_node=key_node, value_node=value_node
            )

        elif key == "paths":
            # Handle paths field - Paths object
            replacements["paths"] = FieldSource(
                value=build_paths(value_node, context), key_node=key_node, value_node=value_node
            )

        elif key == "components":
            # Handle components field - Components object
            replacements["components"] = FieldSource(
                value=build_components(value_node, context),
                key_node=key_node,
                value_node=value_node,
            )

        elif key == "tags":
            # Handle tags field - array of Tag objects
            if isinstance(value_node, yaml.SequenceNode):
                tags_list = []
                for tag_node in value_node.value:
                    tag_obj = build_tag(tag_node, context)
                    tags_list.append(tag_obj)
                replacements["tags"] = FieldSource(
                    value=tags_list, key_node=key_node, value_node=value_node
                )
            else:
                # Not a sequence - preserve as-is for validation
                replacements["tags"] = build_field_source(key_node, value_node, context)

    # Apply all replacements at once
    if replacements:
        openapi_obj = replace(openapi_obj, **replacements)

    return openapi_obj
