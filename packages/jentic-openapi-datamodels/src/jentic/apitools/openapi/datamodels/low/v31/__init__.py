"""OpenAPI 3.1.x Low-Level Data Models.

This module provides low-level/plumbing data models for OpenAPI 3.1 specification objects.
These models preserve complete source fidelity for inspection and validation.
"""

# Main entry point for parsing OpenAPI documents
# All dataclasses for type hints and isinstance checks
from .callback import Callback
from .components import Components
from .contact import Contact
from .discriminator import Discriminator
from .encoding import Encoding
from .example import Example
from .external_documentation import ExternalDocumentation
from .header import Header
from .info import Info
from .license import License
from .link import Link
from .media_type import MediaType
from .oauth_flow import OAuthFlow
from .oauth_flows import OAuthFlows
from .openapi import OpenAPI31, build
from .operation import Operation
from .parameter import Parameter
from .path_item import PathItem
from .paths import Paths
from .reference import Reference
from .request_body import RequestBody
from .response import Response
from .responses import Responses
from .schema import BooleanJSONSchema, Schema
from .security_requirement import SecurityRequirement
from .security_scheme import SecurityScheme
from .server import Server
from .server_variable import ServerVariable
from .tag import Tag
from .xml import XML


__all__ = [
    # Main entry point
    "build",
    # Root object
    "OpenAPI31",
    # All dataclasses (alphabetically sorted)
    "Callback",
    "Components",
    "Contact",
    "Discriminator",
    "Encoding",
    "Example",
    "ExternalDocumentation",
    "Header",
    "Info",
    "License",
    "Link",
    "MediaType",
    "OAuthFlow",
    "OAuthFlows",
    "Operation",
    "Parameter",
    "PathItem",
    "Paths",
    "Reference",
    "RequestBody",
    "Response",
    "Responses",
    "Schema",
    "BooleanJSONSchema",
    "SecurityRequirement",
    "SecurityScheme",
    "Server",
    "ServerVariable",
    "Tag",
    "XML",
]
