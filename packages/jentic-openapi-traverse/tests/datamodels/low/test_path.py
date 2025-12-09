"""Tests for NodePath path formatting."""

import textwrap

import pytest

from jentic.apitools.openapi.datamodels.low.v30 import OpenAPI30
from jentic.apitools.openapi.datamodels.low.v31 import OpenAPI31
from jentic.apitools.openapi.parser.core import OpenAPIParser
from jentic.apitools.openapi.traverse.datamodels.low import traverse


@pytest.fixture
def openapi30_doc():
    """Real OpenAPI 3.0 document for testing."""
    yaml_text = textwrap.dedent("""
        openapi: 3.0.4
        info:
          title: Test API
          version: 1.0.0
        paths:
          /users:
            get:
              operationId: getUsers
              parameters:
                - name: limit
                  in: query
              responses:
                '200':
                  description: Success
          /pets/{id}:
            get:
              operationId: getPet
              responses:
                '200':
                  description: Success
        components:
          schemas:
            User:
              type: object
              properties:
                name:
                  type: string
    """)
    parser = OpenAPIParser("datamodel-low")
    return parser.parse(yaml_text, return_type=OpenAPI30)


@pytest.fixture
def openapi31_doc():
    """Real OpenAPI 3.1 document for testing."""
    yaml_text = textwrap.dedent("""
        openapi: 3.1.2
        info:
          title: Test API
          version: 1.0.0
        paths:
          /posts:
            get:
              operationId: getPosts
              responses:
                '200':
                  description: Success
    """)
    parser = OpenAPIParser("datamodel-low")
    return parser.parse(yaml_text, return_type=OpenAPI31)


class TestFormatPathJSONPointer:
    """Test format_path with JSONPointer format (RFC 6901)."""

    def test_root_node(self, openapi30_doc):
        """Root node should return empty string."""

        class RootCapture:
            def __init__(self):
                self.root_path = None

            def visit_OpenAPI30(self, path):
                self.root_path = path
                return False  # Skip children

        visitor = RootCapture()
        traverse(openapi30_doc, visitor)

        assert visitor.root_path is not None
        assert visitor.root_path.format_path() == ""
        assert visitor.root_path.format_path(path_format="jsonpointer") == ""

    def test_single_field(self, openapi30_doc):
        """Single field should return /field."""

        class InfoCapture:
            def __init__(self):
                self.info_path = None

            def visit_Info(self, path):
                self.info_path = path

        visitor = InfoCapture()
        traverse(openapi30_doc, visitor)

        assert visitor.info_path is not None
        assert visitor.info_path.format_path() == "/info"

    def test_nested_path(self, openapi30_doc):
        """Nested path should return full path."""

        class OperationCapture:
            def __init__(self):
                self.operation_paths = []

            def visit_Operation(self, path):
                self.operation_paths.append(path)

        visitor = OperationCapture()
        traverse(openapi30_doc, visitor)

        # Should have two operations: /users GET and /pets/{id} GET
        assert len(visitor.operation_paths) == 2

        # First operation: /paths/~1users/get
        assert visitor.operation_paths[0].format_path() == "/paths/~1users/get"

        # Second operation: /paths/~1pets~1{id}/get (escapes /)
        assert visitor.operation_paths[1].format_path() == "/paths/~1pets~1{id}/get"

    def test_response_path(self, openapi30_doc):
        """Response path should include full path from root."""

        class ResponseCapture:
            def __init__(self):
                self.response_paths = []

            def visit_Response(self, path):
                self.response_paths.append(path)

        visitor = ResponseCapture()
        traverse(openapi30_doc, visitor)

        # Should have responses for both operations
        assert len(visitor.response_paths) == 2

        # First response: /paths/~1users/get/responses/200
        assert visitor.response_paths[0].format_path() == "/paths/~1users/get/responses/200"

    def test_array_index_parameter(self, openapi30_doc):
        """Array index in path should be formatted correctly."""

        class ParameterCapture:
            def __init__(self):
                self.parameter_paths = []

            def visit_Parameter(self, path):
                self.parameter_paths.append(path)

        visitor = ParameterCapture()
        traverse(openapi30_doc, visitor)

        # Should have one parameter at /paths/~1users/get/parameters/0
        assert len(visitor.parameter_paths) == 1
        assert visitor.parameter_paths[0].format_path() == "/paths/~1users/get/parameters/0"

    def test_schema_property(self, openapi30_doc):
        """Schema property path should be complete."""

        class SchemaCapture:
            def __init__(self):
                self.property_schemas = []

            def visit_Schema(self, path):
                # Check if this is a property schema by examining the path
                # Properties are schemas that are nested under another schema's properties dict
                if path.parent and path.parent.__class__.__name__ == "Schema":
                    self.property_schemas.append(path)

        visitor = SchemaCapture()
        traverse(openapi30_doc, visitor)

        # Should have name property at /components/schemas/User/properties/name
        assert len(visitor.property_schemas) == 1
        assert (
            visitor.property_schemas[0].format_path() == "/components/schemas/User/properties/name"
        )


class TestFormatPathJSONPath:
    """Test format_path with JSONPath format (RFC 9535 Normalized Path)."""

    def test_root_node(self, openapi30_doc):
        """Root node should return $."""

        class RootCapture:
            def __init__(self):
                self.root_path = None

            def visit_OpenAPI30(self, path):
                self.root_path = path
                return False

        visitor = RootCapture()
        traverse(openapi30_doc, visitor)

        assert visitor.root_path is not None
        assert visitor.root_path.format_path(path_format="jsonpath") == "$"

    def test_single_field(self, openapi30_doc):
        """Single field should return $['field']."""

        class InfoCapture:
            def __init__(self):
                self.info_path = None

            def visit_Info(self, path):
                self.info_path = path

        visitor = InfoCapture()
        traverse(openapi30_doc, visitor)

        assert visitor.info_path is not None
        assert visitor.info_path.format_path(path_format="jsonpath") == "$['info']"

    def test_nested_path(self, openapi30_doc):
        """Nested path should return full JSONPath."""

        class OperationCapture:
            def __init__(self):
                self.operation_paths = []

            def visit_Operation(self, path):
                self.operation_paths.append(path)

        visitor = OperationCapture()
        traverse(openapi30_doc, visitor)

        # First operation: $['paths']['/users']['get']
        assert (
            visitor.operation_paths[0].format_path(path_format="jsonpath")
            == "$['paths']['/users']['get']"
        )

        # Second operation: $['paths']['/pets/{id}']['get'] (no escaping needed in JSONPath)
        assert (
            visitor.operation_paths[1].format_path(path_format="jsonpath")
            == "$['paths']['/pets/{id}']['get']"
        )

    def test_response_path(self, openapi30_doc):
        """Response path should include full JSONPath from root."""

        class ResponseCapture:
            def __init__(self):
                self.response_paths = []

            def visit_Response(self, path):
                self.response_paths.append(path)

        visitor = ResponseCapture()
        traverse(openapi30_doc, visitor)

        # First response: $['paths']['/users']['get']['responses']['200']
        assert (
            visitor.response_paths[0].format_path(path_format="jsonpath")
            == "$['paths']['/users']['get']['responses']['200']"
        )

    def test_array_index_parameter(self, openapi30_doc):
        """Array index in JSONPath should use [index] notation."""

        class ParameterCapture:
            def __init__(self):
                self.parameter_paths = []

            def visit_Parameter(self, path):
                self.parameter_paths.append(path)

        visitor = ParameterCapture()
        traverse(openapi30_doc, visitor)

        # Parameter at $['paths']['/users']['get']['parameters'][0]
        assert (
            visitor.parameter_paths[0].format_path(path_format="jsonpath")
            == "$['paths']['/users']['get']['parameters'][0]"
        )

    def test_schema_property(self, openapi30_doc):
        """Schema property JSONPath should be complete."""

        class SchemaCapture:
            def __init__(self):
                self.property_schemas = []

            def visit_Schema(self, path):
                # Check if this is a property schema by examining the path
                if path.parent and path.parent.__class__.__name__ == "Schema":
                    self.property_schemas.append(path)

        visitor = SchemaCapture()
        traverse(openapi30_doc, visitor)

        # Property at $['components']['schemas']['User']['properties']['name']
        assert len(visitor.property_schemas) == 1
        assert (
            visitor.property_schemas[0].format_path(path_format="jsonpath")
            == "$['components']['schemas']['User']['properties']['name']"
        )


class TestFormatPathWebhooksAndCallbacks:
    """Test format_path with webhooks and callbacks (OpenAPI 3.1 features)."""

    def test_webhook_operation(self):
        """Webhook operations should have correct paths."""
        yaml_text = textwrap.dedent("""
            openapi: 3.1.0
            info:
              title: Test API
              version: 1.0.0
            webhooks:
              userCreated:
                post:
                  operationId: userCreatedWebhook
                  responses:
                    '200':
                      description: Success
              userDeleted:
                post:
                  operationId: userDeletedWebhook
                  responses:
                    '200':
                      description: Success
        """)
        parser = OpenAPIParser("datamodel-low")
        doc = parser.parse(yaml_text, return_type=OpenAPI31)

        class WebhookCapture:
            def __init__(self):
                self.webhook_paths = []

            def visit_Operation(self, path):
                self.webhook_paths.append(path)

        visitor = WebhookCapture()
        traverse(doc, visitor)

        # Should have two webhook operations
        assert len(visitor.webhook_paths) == 2

        # First webhook: /webhooks/userCreated/post
        assert visitor.webhook_paths[0].format_path() == "/webhooks/userCreated/post"
        assert (
            visitor.webhook_paths[0].format_path(path_format="jsonpath")
            == "$['webhooks']['userCreated']['post']"
        )

        # Second webhook: /webhooks/userDeleted/post
        assert visitor.webhook_paths[1].format_path() == "/webhooks/userDeleted/post"
        assert (
            visitor.webhook_paths[1].format_path(path_format="jsonpath")
            == "$['webhooks']['userDeleted']['post']"
        )

    def test_callback_operation(self):
        """Callback operations should have correct paths."""
        yaml_text = textwrap.dedent("""
            openapi: 3.1.0
            info:
              title: Test API
              version: 1.0.0
            paths:
              /users:
                post:
                  operationId: createUser
                  responses:
                    '201':
                      description: Created
                  callbacks:
                    statusUpdate:
                      '{$request.body#/callbackUrl}':
                        post:
                          operationId: statusCallback
                          responses:
                            '200':
                              description: Success
        """)
        parser = OpenAPIParser("datamodel-low")
        doc = parser.parse(yaml_text, return_type=OpenAPI31)

        class CallbackCapture:
            def __init__(self):
                self.operations = []

            def visit_Operation(self, path):
                self.operations.append(
                    (
                        path.node.operation_id.value if path.node.operation_id else None,
                        path.format_path(),
                        path.format_path(path_format="jsonpath"),
                    )
                )

        visitor = CallbackCapture()
        traverse(doc, visitor)

        # Should have two operations: main + callback
        assert len(visitor.operations) == 2

        # Main operation
        assert visitor.operations[0][0] == "createUser"
        assert visitor.operations[0][1] == "/paths/~1users/post"

        # Callback operation
        assert visitor.operations[1][0] == "statusCallback"
        assert (
            visitor.operations[1][1]
            == "/paths/~1users/post/callbacks/statusUpdate/{$request.body#~1callbackUrl}/post"
        )
        assert (
            visitor.operations[1][2]
            == "$['paths']['/users']['post']['callbacks']['statusUpdate']['{$request.body#/callbackUrl}']['post']"
        )

    def test_multiple_callbacks(self):
        """Multiple callbacks should all have correct paths."""
        yaml_text = textwrap.dedent("""
            openapi: 3.1.0
            info:
              title: Test API
              version: 1.0.0
            paths:
              /orders:
                post:
                  operationId: createOrder
                  responses:
                    '201':
                      description: Created
                  callbacks:
                    onStatusChange:
                      '{$request.body#/statusUrl}':
                        post:
                          operationId: statusChangeCallback
                          responses:
                            '200':
                              description: OK
                    onPayment:
                      '{$request.body#/paymentUrl}':
                        post:
                          operationId: paymentCallback
                          responses:
                            '200':
                              description: OK
        """)
        parser = OpenAPIParser("datamodel-low")
        doc = parser.parse(yaml_text, return_type=OpenAPI31)

        class CallbackCapture:
            def __init__(self):
                self.callback_paths = []

            def visit_Operation(self, path):
                op_id = path.node.operation_id.value if path.node.operation_id else None
                if "Callback" in (op_id or ""):
                    self.callback_paths.append(path.format_path())

        visitor = CallbackCapture()
        traverse(doc, visitor)

        # Should have two callback operations
        assert len(visitor.callback_paths) == 2
        assert (
            "/paths/~1orders/post/callbacks/onStatusChange/{$request.body#~1statusUrl}/post"
            in visitor.callback_paths
        )
        assert (
            "/paths/~1orders/post/callbacks/onPayment/{$request.body#~1paymentUrl}/post"
            in visitor.callback_paths
        )

    def test_callback_with_multiple_operations(self):
        """Callbacks with multiple HTTP methods should all have correct paths."""
        yaml_text = textwrap.dedent("""
            openapi: 3.1.0
            info:
              title: Test API
              version: 1.0.0
            paths:
              /subscribe:
                post:
                  operationId: subscribe
                  responses:
                    '201':
                      description: Subscribed
                  callbacks:
                    notification:
                      '{$request.body#/notifyUrl}':
                        post:
                          operationId: notifyPost
                          responses:
                            '200':
                              description: OK
                        put:
                          operationId: notifyPut
                          responses:
                            '200':
                              description: OK
        """)
        parser = OpenAPIParser("datamodel-low")
        doc = parser.parse(yaml_text, return_type=OpenAPI31)

        class OperationCapture:
            def __init__(self):
                self.operations = {}

            def visit_Operation(self, path):
                op_id = path.node.operation_id.value if path.node.operation_id else None
                if op_id:
                    self.operations[op_id] = path.format_path()

        visitor = OperationCapture()
        traverse(doc, visitor)

        # Main operation
        assert visitor.operations["subscribe"] == "/paths/~1subscribe/post"
        # Callback operations
        assert (
            visitor.operations["notifyPost"]
            == "/paths/~1subscribe/post/callbacks/notification/{$request.body#~1notifyUrl}/post"
        )
        assert (
            visitor.operations["notifyPut"]
            == "/paths/~1subscribe/post/callbacks/notification/{$request.body#~1notifyUrl}/put"
        )


class TestToParts:
    """Test to_parts method returning path parts as list."""

    def test_root_node(self, openapi30_doc):
        """Root node should return empty list."""

        class RootCapture:
            def __init__(self):
                self.root_path = None

            def visit_OpenAPI30(self, path):
                self.root_path = path
                return False  # Skip children

        visitor = RootCapture()
        traverse(openapi30_doc, visitor)

        assert visitor.root_path is not None
        assert visitor.root_path.to_parts() == []

    def test_single_field(self, openapi30_doc):
        """Single field should return single-element list."""

        class InfoCapture:
            def __init__(self):
                self.info_path = None

            def visit_Info(self, path):
                self.info_path = path

        visitor = InfoCapture()
        traverse(openapi30_doc, visitor)

        assert visitor.info_path is not None
        assert visitor.info_path.to_parts() == ["info"]

    def test_nested_path(self, openapi30_doc):
        """Nested path should return full path parts list."""

        class OperationCapture:
            def __init__(self):
                self.operation_paths = []

            def visit_Operation(self, path):
                self.operation_paths.append(path)

        visitor = OperationCapture()
        traverse(openapi30_doc, visitor)

        # Should have two operations
        assert len(visitor.operation_paths) == 2

        # First operation: ["paths", "/users", "get"]
        assert visitor.operation_paths[0].to_parts() == ["paths", "/users", "get"]

        # Second operation: ["paths", "/pets/{id}", "get"]
        assert visitor.operation_paths[1].to_parts() == ["paths", "/pets/{id}", "get"]

    def test_array_index(self, openapi30_doc):
        """Array index should be integer in list."""

        class ParameterCapture:
            def __init__(self):
                self.parameter_paths = []

            def visit_Parameter(self, path):
                self.parameter_paths.append(path)

        visitor = ParameterCapture()
        traverse(openapi30_doc, visitor)

        # Should have one parameter
        assert len(visitor.parameter_paths) == 1
        assert visitor.parameter_paths[0].to_parts() == [
            "paths",
            "/users",
            "get",
            "parameters",
            0,
        ]

    def test_schema_property(self, openapi30_doc):
        """Schema property should return complete path parts list."""

        class SchemaCapture:
            def __init__(self):
                self.property_schemas = []

            def visit_Schema(self, path):
                # Check if this is a property schema
                if path.parent and path.parent.__class__.__name__ == "Schema":
                    self.property_schemas.append(path)

        visitor = SchemaCapture()
        traverse(openapi30_doc, visitor)

        # Should have name property
        assert len(visitor.property_schemas) == 1
        assert visitor.property_schemas[0].to_parts() == [
            "components",
            "schemas",
            "User",
            "properties",
            "name",
        ]

    def test_consistency_with_format_path(self, openapi30_doc):
        """to_parts() should be consistent with format_path() output."""
        from jsonpointer import JsonPointer

        class AllPathsCapture:
            def __init__(self):
                self.paths = []

            def visit_Info(self, path):
                self.paths.append(path)

            def visit_Operation(self, path):
                self.paths.append(path)

            def visit_Response(self, path):
                self.paths.append(path)

            def visit_Parameter(self, path):
                self.paths.append(path)

        visitor = AllPathsCapture()
        traverse(openapi30_doc, visitor)

        # Verify that to_parts() is consistent with format_path()
        for path in visitor.paths:
            parts = path.to_parts()
            formatted = path.format_path(path_format="jsonpointer")
            reconstructed = JsonPointer.from_parts(parts).path

            assert formatted == reconstructed, (
                f"Inconsistency for {path.node.__class__.__name__}: "
                f"format_path()={formatted!r} vs to_parts()={reconstructed!r}"
            )


class TestFormatPathEdgeCases:
    """Test edge cases for format_path."""

    def test_openapi31_document(self, openapi31_doc):
        """Should work with OpenAPI 3.1 documents."""

        class OperationCapture:
            def __init__(self):
                self.operation_path = None

            def visit_Operation(self, path):
                self.operation_path = path

        visitor = OperationCapture()
        traverse(openapi31_doc, visitor)

        assert visitor.operation_path is not None
        assert visitor.operation_path.format_path() == "/paths/~1posts/get"
        assert (
            visitor.operation_path.format_path(path_format="jsonpath")
            == "$['paths']['/posts']['get']"
        )

    def test_parent_and_ancestors_properties(self, openapi30_doc):
        """Computed properties for parent and ancestors should work."""

        class PathInspector:
            def __init__(self):
                self.operation_path = None

            def visit_Operation(self, path):
                self.operation_path = path
                return False  # Stop after first

        visitor = PathInspector()
        traverse(openapi30_doc, visitor)

        assert visitor.operation_path is not None
        # Parent should be PathItem
        assert visitor.operation_path.parent is not None
        assert visitor.operation_path.parent.__class__.__name__ == "PathItem"

        # Ancestors should be (OpenAPI30, Paths, PathItem)
        ancestors = visitor.operation_path.ancestors
        assert len(ancestors) == 3
        assert ancestors[0].__class__.__name__ == "OpenAPI30"
        assert ancestors[1].__class__.__name__ == "Paths"
        assert ancestors[2].__class__.__name__ == "PathItem"

    def test_get_root(self, openapi30_doc):
        """get_root should return the OpenAPI document."""

        class DeepNodeCapture:
            def __init__(self):
                self.deep_path = None

            def visit_Response(self, path):
                self.deep_path = path
                return False  # Stop after first

        visitor = DeepNodeCapture()
        traverse(openapi30_doc, visitor)

        assert visitor.deep_path is not None
        root = visitor.deep_path.get_root()
        assert root.__class__.__name__ == "OpenAPI30"
        assert root is openapi30_doc

    def test_yaml_field_names_in_paths(self):
        """Paths should use YAML field names (e.g., externalDocs not external_docs)."""
        yaml_text = textwrap.dedent("""
            openapi: 3.1.0
            info:
              title: Test API
              version: 1.0.0
            externalDocs:
              url: https://example.com/docs
              description: API Documentation
        """)
        parser = OpenAPIParser("datamodel-low")
        doc = parser.parse(yaml_text, return_type=OpenAPI31)

        class ExternalDocsCapture:
            def __init__(self):
                self.path = None

            def visit_ExternalDocumentation(self, path):
                self.path = path

        visitor = ExternalDocsCapture()
        traverse(doc, visitor)

        assert visitor.path is not None
        # Should use YAML name "externalDocs" not Python name "external_docs"
        assert visitor.path.format_path() == "/externalDocs"
        assert visitor.path.format_path(path_format="jsonpath") == "$['externalDocs']"
