from dataclasses import dataclass, field, replace

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .builders import build_model
from .contact import Contact
from .contact import build as build_contact
from .license import License
from .license import build as build_license


__all__ = ["Info", "build"]


@dataclass(frozen=True, slots=True)
class Info:
    """
    Info Object representation for OpenAPI 3.1.

    Provides metadata about the API. The metadata MAY be used by the clients if needed,
    and MAY be presented in editing or documentation generation tools for convenience.

    Attributes:
        root_node: The top-level node representing the entire Info object in the original source file
        title: REQUIRED. The title of the API.
        summary: A short summary of the API (new in OpenAPI 3.1).
        description: A description of the API. CommonMark syntax MAY be used for rich text representation.
        termsOfService: A URL to the Terms of Service for the API. This MUST be in the form of a URL.
        contact: The contact information for the exposed API.
        license: The license information for the exposed API.
        version: REQUIRED. The version of the OpenAPI document (which is distinct from the OpenAPI Specification version or the API implementation version).
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    title: FieldSource[str] | None = fixed_field()
    summary: FieldSource[str] | None = fixed_field()
    description: FieldSource[str] | None = fixed_field()
    termsOfService: FieldSource[str] | None = fixed_field()
    contact: FieldSource[Contact] | None = fixed_field()
    license: FieldSource[License] | None = fixed_field()
    version: FieldSource[str] | None = fixed_field()
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(root: yaml.Node, context: Context | None = None) -> Info | ValueSource[YAMLInvalidValue]:
    """
    Build an Info object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        An Info object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose('''
        title: Sample Pet Store App
        version: 1.0.1
        description: This is a sample server for a pet store.
        contact:
          name: API Support
          email: support@example.com
        license:
          name: Apache 2.0
          url: https://www.apache.org/licenses/LICENSE-2.0.html
        ''')
        info = build(root)
        assert info.title.value == 'Sample Pet Store App'
        assert info.version.value == '1.0.1'
        assert info.contact.value.name.value == 'API Support'
    """
    context = context or Context()

    # Use build_model for initial construction
    info = build_model(root, Info, context=context)

    # If build_model returned ValueSource (invalid node), return it immediately
    if not isinstance(info, Info):
        return info

    # Manually handle nested objects (contact, license)
    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        if key == "contact":
            # Handle nested Contact object - child builder handles invalid nodes
            # FieldSource will auto-unwrap ValueSource if child returns it for invalid data
            contact = FieldSource(
                value=build_contact(value_node, context=context),
                key_node=key_node,
                value_node=value_node,
            )
            info = replace(info, contact=contact)
        elif key == "license":
            # Handle nested License object - child builder handles invalid nodes
            # FieldSource will auto-unwrap ValueSource if child returns it for invalid data
            license_obj = FieldSource(
                value=build_license(value_node, context=context),
                key_node=key_node,
                value_node=value_node,
            )
            info = replace(info, license=license_obj)

    return info
