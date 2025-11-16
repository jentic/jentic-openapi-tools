from dataclasses import dataclass, field

from ruamel import yaml

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.extractors import extract_extension_fields
from jentic.apitools.openapi.datamodels.low.fields import fixed_field
from jentic.apitools.openapi.datamodels.low.model_builder import build_field_source
from jentic.apitools.openapi.datamodels.low.sources import (
    FieldSource,
    KeySource,
    ValueSource,
    YAMLInvalidValue,
    YAMLValue,
)
from jentic.apitools.openapi.datamodels.low.v30.callback import (
    Callback,
    build_callback_or_reference,
)
from jentic.apitools.openapi.datamodels.low.v30.example import (
    Example,
    build_example_or_reference,
)
from jentic.apitools.openapi.datamodels.low.v30.header import (
    Header,
    build_header_or_reference,
)
from jentic.apitools.openapi.datamodels.low.v30.link import Link, build_link_or_reference
from jentic.apitools.openapi.datamodels.low.v30.parameter import (
    Parameter,
    build_parameter_or_reference,
)
from jentic.apitools.openapi.datamodels.low.v30.reference import Reference
from jentic.apitools.openapi.datamodels.low.v30.request_body import (
    RequestBody,
    build_request_body_or_reference,
)
from jentic.apitools.openapi.datamodels.low.v30.response import (
    Response,
    build_response_or_reference,
)
from jentic.apitools.openapi.datamodels.low.v30.schema import (
    Schema,
    build_schema_or_reference,
)
from jentic.apitools.openapi.datamodels.low.v30.security_scheme import (
    SecurityScheme,
    build_security_scheme_or_reference,
)


__all__ = ["Components", "build"]


@dataclass(frozen=True, slots=True)
class Components:
    r"""
    Components Object representation for OpenAPI 3.0.

    Holds reusable objects for different aspects of the OAS. All objects defined within
    the components object have no effect on the API unless they are explicitly referenced
    from properties outside the components object.

    All component keys MUST match the regex pattern: ^[a-zA-Z0-9\.\-_]+$
    (Note: This is a validation concern and not enforced by this low-level model)

    Attributes:
        root_node: The top-level node representing the entire Components object in the original source file
        schemas: Reusable Schema Objects or Reference Objects
        responses: Reusable Response Objects or Reference Objects
        parameters: Reusable Parameter Objects or Reference Objects
        examples: Reusable Example Objects or Reference Objects
        request_bodies: Reusable Request Body Objects or Reference Objects
        headers: Reusable Header Objects or Reference Objects
        security_schemes: Reusable Security Scheme Objects or Reference Objects
        links: Reusable Link Objects or Reference Objects
        callbacks: Reusable Callback Objects or Reference Objects
        extensions: Specification extensions (x-* fields)
    """

    root_node: yaml.Node
    schemas: FieldSource[dict[KeySource[str], Schema | Reference]] | None = fixed_field()
    responses: FieldSource[dict[KeySource[str], Response | Reference]] | None = fixed_field()
    parameters: FieldSource[dict[KeySource[str], Parameter | Reference]] | None = fixed_field()
    examples: FieldSource[dict[KeySource[str], Example | Reference]] | None = fixed_field()
    request_bodies: FieldSource[dict[KeySource[str], RequestBody | Reference]] | None = fixed_field(
        metadata={"yaml_name": "requestBodies"}
    )
    headers: FieldSource[dict[KeySource[str], Header | Reference]] | None = fixed_field()
    security_schemes: FieldSource[dict[KeySource[str], SecurityScheme | Reference]] | None = (
        fixed_field(metadata={"yaml_name": "securitySchemes"})
    )
    links: FieldSource[dict[KeySource[str], Link | Reference]] | None = fixed_field()
    callbacks: FieldSource[dict[KeySource[str], Callback | Reference]] | None = fixed_field()
    extensions: dict[KeySource[str], ValueSource[YAMLValue]] = field(default_factory=dict)


def build(
    root: yaml.Node, context: Context | None = None
) -> Components | ValueSource[YAMLInvalidValue]:
    """
    Build a Components object from a YAML node.

    Preserves all source data as-is, regardless of type. This is a low-level/plumbing
    model that provides complete source fidelity for inspection and validation.

    Args:
        root: The YAML node to parse (should be a MappingNode)
        context: Optional parsing context. If None, a default context will be created.

    Returns:
        A Components object if the node is valid, or a ValueSource containing
        the invalid data if the root is not a MappingNode (preserving the invalid data
        and its source location for validation).

    Example:
        from ruamel.yaml import YAML
        yaml = YAML()
        root = yaml.compose('''
        schemas:
          User:
            type: object
            properties:
              id:
                type: integer
              name:
                type: string
        responses:
          NotFound:
            description: Entity not found
        ''')
        components = build(root)
        assert 'User' in {k.value for k in components.schemas.value.keys()}
    """
    context = context or Context()

    # Check if root is a MappingNode, if not return ValueSource with invalid data
    if not isinstance(root, yaml.MappingNode):
        value = context.yaml_constructor.construct_object(root, deep=True)
        return ValueSource(value=value, value_node=root)

    # Extract extensions first
    extensions = extract_extension_fields(root, context)
    extension_properties = {k.value for k in extensions.keys()}

    # Initialize all component fields
    schemas = None
    responses = None
    parameters = None
    examples = None
    request_bodies = None
    headers = None
    security_schemes = None
    links = None
    callbacks = None

    # Process each field in single pass
    for key_node, value_node in root.value:
        key = context.yaml_constructor.construct_yaml_str(key_node)

        # Skip extensions - already processed
        if key in extension_properties:
            continue

        if key == "schemas":
            # Handle schemas field - map of Schema or Reference objects
            if isinstance(value_node, yaml.MappingNode):
                schemas_dict = {}
                for schema_key_node, schema_value_node in value_node.value:
                    schema_key = context.yaml_constructor.construct_yaml_str(schema_key_node)
                    schema_or_reference = build_schema_or_reference(schema_value_node, context)
                    schemas_dict[KeySource(value=schema_key, key_node=schema_key_node)] = (
                        schema_or_reference
                    )
                schemas = FieldSource(value=schemas_dict, key_node=key_node, value_node=value_node)
            else:
                # Not a mapping - preserve as-is for validation
                schemas = build_field_source(key_node, value_node, context)

        elif key == "responses":
            # Handle responses field - map of Response or Reference objects
            if isinstance(value_node, yaml.MappingNode):
                responses_dict = {}
                for response_key_node, response_value_node in value_node.value:
                    response_key = context.yaml_constructor.construct_yaml_str(response_key_node)
                    response_or_reference = build_response_or_reference(
                        response_value_node, context
                    )
                    responses_dict[KeySource(value=response_key, key_node=response_key_node)] = (
                        response_or_reference
                    )
                responses = FieldSource(
                    value=responses_dict, key_node=key_node, value_node=value_node
                )
            else:
                # Not a mapping - preserve as-is for validation
                responses = build_field_source(key_node, value_node, context)

        elif key == "parameters":
            # Handle parameters field - map of Parameter or Reference objects
            if isinstance(value_node, yaml.MappingNode):
                parameters_dict = {}
                for parameter_key_node, parameter_value_node in value_node.value:
                    parameter_key = context.yaml_constructor.construct_yaml_str(parameter_key_node)
                    parameter_or_reference = build_parameter_or_reference(
                        parameter_value_node, context
                    )
                    parameters_dict[KeySource(value=parameter_key, key_node=parameter_key_node)] = (
                        parameter_or_reference
                    )
                parameters = FieldSource(
                    value=parameters_dict, key_node=key_node, value_node=value_node
                )
            else:
                # Not a mapping - preserve as-is for validation
                parameters = build_field_source(key_node, value_node, context)

        elif key == "examples":
            # Handle examples field - map of Example or Reference objects
            if isinstance(value_node, yaml.MappingNode):
                examples_dict = {}
                for example_key_node, example_value_node in value_node.value:
                    example_key = context.yaml_constructor.construct_yaml_str(example_key_node)
                    example_or_reference = build_example_or_reference(example_value_node, context)
                    examples_dict[KeySource(value=example_key, key_node=example_key_node)] = (
                        example_or_reference
                    )
                examples = FieldSource(
                    value=examples_dict, key_node=key_node, value_node=value_node
                )
            else:
                # Not a mapping - preserve as-is for validation
                examples = build_field_source(key_node, value_node, context)

        elif key == "requestBodies":
            # Handle requestBodies field - map of RequestBody or Reference objects
            if isinstance(value_node, yaml.MappingNode):
                request_bodies_dict = {}
                for request_body_key_node, request_body_value_node in value_node.value:
                    request_body_key = context.yaml_constructor.construct_yaml_str(
                        request_body_key_node
                    )
                    request_body_or_reference = build_request_body_or_reference(
                        request_body_value_node, context
                    )
                    request_bodies_dict[
                        KeySource(value=request_body_key, key_node=request_body_key_node)
                    ] = request_body_or_reference
                request_bodies = FieldSource(
                    value=request_bodies_dict, key_node=key_node, value_node=value_node
                )
            else:
                # Not a mapping - preserve as-is for validation
                request_bodies = build_field_source(key_node, value_node, context)

        elif key == "headers":
            # Handle headers field - map of Header or Reference objects
            if isinstance(value_node, yaml.MappingNode):
                headers_dict = {}
                for header_key_node, header_value_node in value_node.value:
                    header_key = context.yaml_constructor.construct_yaml_str(header_key_node)
                    header_or_reference = build_header_or_reference(header_value_node, context)
                    headers_dict[KeySource(value=header_key, key_node=header_key_node)] = (
                        header_or_reference
                    )
                headers = FieldSource(value=headers_dict, key_node=key_node, value_node=value_node)
            else:
                # Not a mapping - preserve as-is for validation
                headers = build_field_source(key_node, value_node, context)

        elif key == "securitySchemes":
            # Handle securitySchemes field - map of SecurityScheme or Reference objects
            if isinstance(value_node, yaml.MappingNode):
                security_schemes_dict = {}
                for security_scheme_key_node, security_scheme_value_node in value_node.value:
                    security_scheme_key = context.yaml_constructor.construct_yaml_str(
                        security_scheme_key_node
                    )
                    security_scheme_or_reference = build_security_scheme_or_reference(
                        security_scheme_value_node, context
                    )
                    security_schemes_dict[
                        KeySource(value=security_scheme_key, key_node=security_scheme_key_node)
                    ] = security_scheme_or_reference
                security_schemes = FieldSource(
                    value=security_schemes_dict, key_node=key_node, value_node=value_node
                )
            else:
                # Not a mapping - preserve as-is for validation
                security_schemes = build_field_source(key_node, value_node, context)

        elif key == "links":
            # Handle links field - map of Link or Reference objects
            if isinstance(value_node, yaml.MappingNode):
                links_dict = {}
                for link_key_node, link_value_node in value_node.value:
                    link_key = context.yaml_constructor.construct_yaml_str(link_key_node)
                    link_or_reference = build_link_or_reference(link_value_node, context)
                    links_dict[KeySource(value=link_key, key_node=link_key_node)] = (
                        link_or_reference
                    )
                links = FieldSource(value=links_dict, key_node=key_node, value_node=value_node)
            else:
                # Not a mapping - preserve as-is for validation
                links = build_field_source(key_node, value_node, context)

        elif key == "callbacks":
            # Handle callbacks field - map of Callback or Reference objects
            if isinstance(value_node, yaml.MappingNode):
                callbacks_dict = {}
                for callback_key_node, callback_value_node in value_node.value:
                    callback_key = context.yaml_constructor.construct_yaml_str(callback_key_node)
                    callback_or_reference = build_callback_or_reference(
                        callback_value_node, context
                    )
                    callbacks_dict[KeySource(value=callback_key, key_node=callback_key_node)] = (
                        callback_or_reference
                    )
                callbacks = FieldSource(
                    value=callbacks_dict, key_node=key_node, value_node=value_node
                )
            else:
                # Not a mapping - preserve as-is for validation
                callbacks = build_field_source(key_node, value_node, context)

    # Create and return the Components object with collected data
    return Components(
        root_node=root,
        schemas=schemas,
        responses=responses,
        parameters=parameters,
        examples=examples,
        request_bodies=request_bodies,
        headers=headers,
        security_schemes=security_schemes,
        links=links,
        callbacks=callbacks,
        extensions=extensions,
    )
