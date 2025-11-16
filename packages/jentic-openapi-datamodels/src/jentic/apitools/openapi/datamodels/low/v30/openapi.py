from dataclasses import dataclass, field, replace

from ruamel import yaml

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.fields import fixed_field
from jentic.apitools.openapi.datamodels.low.model_builder import (
    build_field_source,
    build_model,
)
from jentic.apitools.openapi.datamodels.low.sources import (
    FieldSource,
    KeySource,
    ValueSource,
    YAMLInvalidValue,
    YAMLValue,
)
from jentic.apitools.openapi.datamodels.low.v30.components import Components
from jentic.apitools.openapi.datamodels.low.v30.components import build as build_components
from jentic.apitools.openapi.datamodels.low.v30.external_documentation import (
    ExternalDocumentation,
)
from jentic.apitools.openapi.datamodels.low.v30.info import Info
from jentic.apitools.openapi.datamodels.low.v30.info import build as build_info
from jentic.apitools.openapi.datamodels.low.v30.paths import Paths
from jentic.apitools.openapi.datamodels.low.v30.paths import build as build_paths
from jentic.apitools.openapi.datamodels.low.v30.security_requirement import (
    SecurityRequirement,
)
from jentic.apitools.openapi.datamodels.low.v30.server import Server
from jentic.apitools.openapi.datamodels.low.v30.tag import Tag
from jentic.apitools.openapi.datamodels.low.v30.tag import build as build_tag


__all__ = ["OpenAPI30", "build"]


@dataclass(frozen=True, slots=True)
class OpenAPI30:
    """
    OpenAPI Object representation for OpenAPI 3.0.

    This is the root document object of the OpenAPI document.

    Attributes:
        root_node: The top-level node representing the entire OpenAPI object in the original source file
        openapi: REQUIRED. The version number of the OpenAPI Specification that the document uses.
                 Must match the specification version (e.g., "3.0.0", "3.0.1", "3.0.2", "3.0.3", "3.0.4").
        info: REQUIRED. Provides metadata about the API (title, version, description, etc.)
        paths: REQUIRED. The available paths and operations for the API
        servers: An array of Server Objects providing connectivity information to target servers
        components: An element to hold reusable objects for different aspects of the OAS
        security: A declaration of which security mechanisms can be used across the API
        tags: A list of tags used by the specification with additional metadata
        external_docs: Additional external documentation
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    openapi: FieldSource[str] | None = fixed_field()
    info: FieldSource[Info] | None = fixed_field()
    servers: FieldSource[list["Server"]] | None = fixed_field()
    paths: FieldSource[Paths] | None = fixed_field()
    components: FieldSource[Components] | None = fixed_field()
    security: FieldSource[list["SecurityRequirement"]] | None = fixed_field()
    tags: FieldSource[list[Tag]] | None = fixed_field()
    external_docs: FieldSource["ExternalDocumentation"] | None = fixed_field(
        metadata={"yaml_name": "externalDocs"}
    )
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> OpenAPI30 | ValueSource[YAMLInvalidValue]:
    """
    Build an OpenAPI object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        An OpenAPI object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose('''
        openapi: 3.0.4
        info:
          title: Sample API
          version: 1.0.0
        paths:
          /users:
            get:
              responses:
                '200':
                  description: Success
        ''')
        openapi_doc = build(root)
        assert openapi_doc.openapi.value == '3.0.4'
        assert openapi_doc.info.value.title.value == 'Sample API'
    """
    context = context or Context()

    # Use build_model to handle simple fields (openapi, servers, security, external_docs) and extensions
    openapi_obj = build_model(root, OpenAPI30, context=context)

    # If build_model returned ValueSource (invalid node), return it immediately
    if not isinstance(openapi_obj, OpenAPI30):
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
