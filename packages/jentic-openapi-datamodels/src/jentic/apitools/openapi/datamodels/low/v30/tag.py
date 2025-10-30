from dataclasses import dataclass, field, replace

from ruamel import yaml

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.fields import fixed_field
from jentic.apitools.openapi.datamodels.low.model_builder import build_model
from jentic.apitools.openapi.datamodels.low.sources import (
    FieldSource,
    KeySource,
    ValueSource,
    YAMLInvalidValue,
    YAMLValue,
)
from jentic.apitools.openapi.datamodels.low.v30.external_documentation import (
    ExternalDocumentation,
)
from jentic.apitools.openapi.datamodels.low.v30.external_documentation import (
    build as build_external_documentation,
)


__all__ = ["Tag", "build"]


@dataclass(frozen=True, slots=True)
class Tag:
    """
    Tag Object representation for OpenAPI 3.0.

    Adds metadata to a single tag that is used by the Operation Object. It is not mandatory
    to have a Tag Object per tag defined in the Operation Object instances.

    Attributes:
        root_node: The top-level node representing the entire Tag object in the original source file
        name: The name of the tag. REQUIRED.
        description: A short description for the tag. CommonMark syntax MAY be used for rich text representation.
        external_docs: Additional external documentation for this tag.
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    name: FieldSource[str] | None = fixed_field()
    description: FieldSource[str] | None = fixed_field()
    external_docs: FieldSource[ExternalDocumentation] | None = fixed_field(
        metadata={"yaml_name": "externalDocs"}
    )
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(root: yaml.Node, context: Context | None = None) -> Tag | ValueSource[YAMLInvalidValue]:
    """
    Build a Tag object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A Tag object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose("name: pet\\ndescription: Everything about your Pets")
        tag = build(root)
        assert tag.name.value == 'pet'
    """
    # Initialize context once at the beginning
    if context is None:
        context = Context()

    if not isinstance(root, yaml.MappingNode):
        # Preserve invalid root data instead of returning None
        value = context.yaml_constructor.construct_object(root, deep=True)
        return ValueSource(value=value, value_node=root)

    # Use build_model to handle most fields
    tag = build_model(root, Tag, context=context)

    # Manually handle special fields that build_model can't process (nested objects)
    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        if key == "externalDocs":
            # Handle nested ExternalDocumentation object - child builder handles invalid nodes
            # FieldSource will auto-unwrap ValueSource if child returns it for invalid data
            external_docs = FieldSource(
                value=build_external_documentation(value_node, context=context),
                key_node=key_node,
                value_node=value_node,
            )
            tag = replace(tag, external_docs=external_docs)
            break

    return tag
