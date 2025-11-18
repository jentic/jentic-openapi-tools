from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from ruamel import yaml

from ..context import Context
from ..fields import fixed_field
from ..sources import FieldSource, KeySource, ValueSource, YAMLInvalidValue, YAMLValue
from .builders import build_model
from .external_documentation import ExternalDocumentation
from .parameter import Parameter
from .reference import Reference
from .request_body import RequestBody, build_request_body_or_reference
from .responses import Responses
from .responses import build as build_responses
from .security_requirement import SecurityRequirement
from .server import Server


if TYPE_CHECKING:
    from .callback import Callback


__all__ = ["Operation", "build"]


@dataclass(frozen=True, slots=True)
class Operation:
    """
    Operation Object representation for OpenAPI 3.1.

    Describes a single API operation on a path.

    Attributes:
        root_node: The top-level node representing the entire Operation object in the original source file
        tags: List of tags for API documentation control
        summary: Short summary of what the operation does
        description: Verbose explanation of the operation behavior (may contain CommonMark syntax)
        external_docs: Additional external documentation for this operation
        operation_id: Unique string used to identify the operation
        parameters: List of parameters that are applicable for this operation
        request_body: Request body applicable for this operation
        responses: REQUIRED. The list of possible responses as they are returned from executing this operation
        callbacks: Map of possible out-of-band callbacks related to the parent operation
        deprecated: Declares this operation to be deprecated
        security: Declaration of which security mechanisms can be used for this operation
        servers: Alternative server array to service this operation
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    tags: FieldSource[list[ValueSource[str]]] | None = fixed_field()
    summary: FieldSource[str] | None = fixed_field()
    description: FieldSource[str] | None = fixed_field()
    external_docs: FieldSource["ExternalDocumentation"] | None = fixed_field(
        metadata={"yaml_name": "externalDocs"}
    )
    operation_id: FieldSource[str] | None = fixed_field(metadata={"yaml_name": "operationId"})
    parameters: FieldSource[list["Parameter | Reference"]] | None = fixed_field()
    request_body: FieldSource[RequestBody | Reference] | None = fixed_field(
        metadata={"yaml_name": "requestBody"}
    )
    responses: FieldSource[Responses] | None = fixed_field()
    callbacks: FieldSource[dict[KeySource[str], "Callback | Reference"]] | None = fixed_field()
    deprecated: FieldSource[bool] | None = fixed_field()
    security: FieldSource[list["SecurityRequirement"]] | None = fixed_field()
    servers: FieldSource[list["Server"]] | None = fixed_field()
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> Operation | ValueSource[YAMLInvalidValue]:
    """
    Build an Operation object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        An Operation object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose('''
        summary: List users
        operationId: listUsers
        responses:
          '200':
            description: successful operation
        ''')
        operation = build(root)
        assert operation.summary.value == 'List users'
    """
    context = context or Context()

    # Use build_model for initial construction
    operation = build_model(root, Operation, context=context)

    # If build_model returned ValueSource (invalid node), return it immediately
    if not isinstance(operation, Operation):
        return operation

    # Manually handle nested complex fields
    replacements = {}
    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        if key == "requestBody":
            # Handle requestBody field - RequestBody or Reference
            request_body_or_reference = build_request_body_or_reference(value_node, context)
            replacements["request_body"] = FieldSource(
                value=request_body_or_reference, key_node=key_node, value_node=value_node
            )
        elif key == "responses":
            # Handle responses field - Responses object
            responses_obj = build_responses(value_node, context)
            replacements["responses"] = FieldSource(
                value=responses_obj, key_node=key_node, value_node=value_node
            )

    # Apply all replacements at once
    if replacements:
        operation = replace(operation, **replacements)

    return operation
