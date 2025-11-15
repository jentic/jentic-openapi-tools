from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

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


if TYPE_CHECKING:
    from jentic.apitools.openapi.datamodels.low.v30.callback import Callback

from jentic.apitools.openapi.datamodels.low.v30.external_documentation import (
    build as build_external_docs,
)
from jentic.apitools.openapi.datamodels.low.v30.parameter import Parameter
from jentic.apitools.openapi.datamodels.low.v30.reference import Reference
from jentic.apitools.openapi.datamodels.low.v30.request_body import (
    RequestBody,
    build_request_body_or_reference,
)
from jentic.apitools.openapi.datamodels.low.v30.responses import Responses
from jentic.apitools.openapi.datamodels.low.v30.responses import (
    build as build_responses,
)
from jentic.apitools.openapi.datamodels.low.v30.security_requirement import (
    SecurityRequirement,
)
from jentic.apitools.openapi.datamodels.low.v30.security_requirement import (
    build as build_security_requirement,
)
from jentic.apitools.openapi.datamodels.low.v30.server import Server


__all__ = ["Operation", "build"]


@dataclass(frozen=True, slots=True)
class Operation:
    """
    Operation Object representation for OpenAPI 3.0.

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
    external_docs: FieldSource[ExternalDocumentation] | None = fixed_field(
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
    security: FieldSource[list[SecurityRequirement]] | None = fixed_field()
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

    # Use build_model to handle simple fields
    operation = build_model(root, Operation, context=context)

    # If build_model returned ValueSource (invalid node), return it immediately
    if not isinstance(operation, Operation):
        return operation

    # Manually handle nested complex fields
    replacements = {}
    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        if key == "externalDocs":
            # Handle externalDocs field - ExternalDocumentation object
            external_docs = build_external_docs(value_node, context)
            replacements["external_docs"] = FieldSource(
                value=external_docs, key_node=key_node, value_node=value_node
            )
        elif key == "requestBody":
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
        elif key == "callbacks":
            # Handle callbacks field - map of Callback or Reference objects
            # Lazy import to avoid circular dependency
            from jentic.apitools.openapi.datamodels.low.v30.callback import (
                build_callback_or_reference,
            )

            if isinstance(value_node, yaml.MappingNode):
                callbacks_dict: dict[
                    KeySource[str], Callback | Reference | ValueSource[YAMLInvalidValue]
                ] = {}
                for callback_key_node, callback_value_node in value_node.value:
                    callback_key = context.yaml_constructor.construct_yaml_str(callback_key_node)
                    callback_or_reference = build_callback_or_reference(
                        callback_value_node, context
                    )
                    callbacks_dict[KeySource(value=callback_key, key_node=callback_key_node)] = (
                        callback_or_reference
                    )
                replacements["callbacks"] = FieldSource(
                    value=callbacks_dict, key_node=key_node, value_node=value_node
                )
            else:
                # Not a mapping - preserve as-is for validation
                value = context.yaml_constructor.construct_object(value_node, deep=True)
                replacements["callbacks"] = FieldSource(
                    value=value, key_node=key_node, value_node=value_node
                )
        elif key == "security":
            # Handle security field - array of SecurityRequirement objects
            if isinstance(value_node, yaml.SequenceNode):
                security_list: list[SecurityRequirement | ValueSource[YAMLInvalidValue]] = []
                for item_node in value_node.value:
                    security_req = build_security_requirement(item_node, context)
                    security_list.append(security_req)
                replacements["security"] = FieldSource(
                    value=security_list, key_node=key_node, value_node=value_node
                )
            else:
                # Not a sequence - preserve as-is for validation
                value = context.yaml_constructor.construct_object(value_node, deep=True)
                replacements["security"] = FieldSource(
                    value=value, key_node=key_node, value_node=value_node
                )

    # Apply all replacements at once
    if replacements:
        operation = replace(operation, **replacements)

    return operation
