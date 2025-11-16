from dataclasses import dataclass, field, replace

from ruamel import yaml

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.fields import fixed_field
from jentic.apitools.openapi.datamodels.low.model_builder import build_field_source, build_model
from jentic.apitools.openapi.datamodels.low.sources import (
    FieldSource,
    KeySource,
    ValueSource,
    YAMLInvalidValue,
    YAMLValue,
)
from jentic.apitools.openapi.datamodels.low.v30.header import (
    Header,
)
from jentic.apitools.openapi.datamodels.low.v30.link import (
    Link,
    build_link_or_reference,
)
from jentic.apitools.openapi.datamodels.low.v30.media_type import MediaType
from jentic.apitools.openapi.datamodels.low.v30.reference import Reference
from jentic.apitools.openapi.datamodels.low.v30.reference import (
    build as build_reference,
)


__all__ = ["Response", "build", "build_response_or_reference"]


@dataclass(frozen=True, slots=True)
class Response:
    """
    Response Object representation for OpenAPI 3.0.

    Describes a single response from an API Operation, including design-time, static links
    to operations based on the response.

    Attributes:
        root_node: The top-level node representing the entire Response object in the original source file
        description: A description of the response. CommonMark syntax MAY be used for rich text representation.
        headers: Maps a header name to its definition.
        content: A map containing descriptions of potential response payloads. The key is a media type or media type range
                and the value describes it. For responses that match multiple keys, only the most specific key is applicable.
        links: A map of operations links that can be followed from the response. The key is a short name for the link,
              following the naming constraints of the Components Object.
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    description: FieldSource[str] | None = fixed_field()
    headers: FieldSource[dict[KeySource[str], "Header | Reference"]] | None = fixed_field()
    content: FieldSource[dict[KeySource[str], "MediaType"]] | None = fixed_field()
    links: FieldSource[dict[KeySource[str], Link | Reference]] | None = fixed_field()
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> Response | ValueSource[YAMLInvalidValue]:
    """
    Build a Response object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A Response object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose('''
        description: successful operation
        content:
          application/json:
            schema:
              type: object
        ''')
        response = build(root)
        assert response.description.value == 'successful operation'
    """
    context = context or Context()

    # Use build_model to handle simple fields
    response = build_model(root, Response, context=context)

    # If build_model returned ValueSource (invalid node), return it immediately
    if not isinstance(response, Response):
        return response

    # Manually handle nested complex fields
    replacements = {}
    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        if key == "links":
            # Handle links field - map of Link or Reference objects
            if isinstance(value_node, yaml.MappingNode):
                links_dict: dict[
                    KeySource[str], Link | Reference | ValueSource[YAMLInvalidValue]
                ] = {}
                for link_key_node, link_value_node in value_node.value:
                    link_key = context.yaml_constructor.construct_yaml_str(link_key_node)
                    # Build Link or Reference - child builder handles invalid nodes
                    link_or_reference = build_link_or_reference(link_value_node, context)
                    links_dict[KeySource(value=link_key, key_node=link_key_node)] = (
                        link_or_reference
                    )
                replacements["links"] = FieldSource(
                    value=links_dict, key_node=key_node, value_node=value_node
                )
            else:
                # Not a mapping - preserve as-is for validation
                replacements["links"] = build_field_source(key_node, value_node, context)

    # Apply all replacements at once
    if replacements:
        response = replace(response, **replacements)

    return response


def build_response_or_reference(
    node: yaml.Node, context: Context
) -> Response | Reference | ValueSource[YAMLInvalidValue]:
    """
    Build either a Response or Reference from a YAML node.

    This helper handles the polymorphic nature of OpenAPI where many fields
    can contain either a Response object or a Reference object ($ref).

    Args:
        node: The YAML node to parse
        context: Parsing context

    Returns:
        A Response, Reference, or ValueSource if the node is invalid
    """
    # Check if it's a reference (has $ref key)
    if isinstance(node, yaml.MappingNode):
        for key_node, _ in node.value:
            key = context.yaml_constructor.construct_yaml_str(key_node)
            if key == "$ref":
                return build_reference(node, context)

    # Otherwise, try to build as Response
    return build(node, context)
