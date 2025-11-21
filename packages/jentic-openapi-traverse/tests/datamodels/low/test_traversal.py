"""Comprehensive tests for traversal.py functionality."""

import textwrap

import pytest

from jentic.apitools.openapi.datamodels.low.v30 import OpenAPI30
from jentic.apitools.openapi.parser.core import OpenAPIParser
from jentic.apitools.openapi.traverse.datamodels.low import (
    BREAK,
    DataModelLowVisitor,
    traverse,
)


@pytest.fixture
def simple_doc():
    """Simple OpenAPI document for testing."""
    yaml_text = textwrap.dedent("""
        openapi: 3.0.4
        info:
          title: Test API
          version: 1.0.0
        paths:
          /users:
            get:
              operationId: getUsers
              responses:
                '200':
                  description: Success
    """)
    parser = OpenAPIParser("datamodel-low")
    return parser.parse(yaml_text, return_type=OpenAPI30)


@pytest.fixture
def multi_operation_doc():
    """OpenAPI document with multiple operations for testing."""
    yaml_text = textwrap.dedent("""
        openapi: 3.0.4
        info:
          title: Test API
          version: 1.0.0
        paths:
          /users:
            get:
              operationId: getUsers
              responses:
                '200':
                  description: Success
            post:
              operationId: createUser
              responses:
                '201':
                  description: Created
          /posts:
            get:
              operationId: getPosts
              responses:
                '200':
                  description: Success
    """)
    parser = OpenAPIParser("datamodel-low")
    return parser.parse(yaml_text, return_type=OpenAPI30)


class TestBasicTraversal:
    """Test basic traversal functionality."""

    def test_traverse_visits_root_node(self, simple_doc):
        """Should visit the root OpenAPI30 node."""

        class RootVisitor:
            def __init__(self):
                self.visited_root = False

            def visit_OpenAPI30(self, path):
                self.visited_root = True

        visitor = RootVisitor()
        traverse(simple_doc, visitor)

        assert visitor.visited_root is True

    def test_traverse_visits_nested_nodes(self, simple_doc):
        """Should visit nested nodes automatically."""

        class NodeCollector:
            def __init__(self):
                self.node_types = []

            def visit_Info(self, path):
                self.node_types.append("Info")

            def visit_Paths(self, path):
                self.node_types.append("Paths")

            def visit_PathItem(self, path):
                self.node_types.append("PathItem")

            def visit_Operation(self, path):
                self.node_types.append("Operation")

        visitor = NodeCollector()
        traverse(simple_doc, visitor)

        assert "Info" in visitor.node_types
        assert "Paths" in visitor.node_types
        assert "PathItem" in visitor.node_types
        assert "Operation" in visitor.node_types

    def test_traverse_visits_all_operations(self, multi_operation_doc):
        """Should visit all operations in the document."""

        class OperationCounter:
            def __init__(self):
                self.count = 0

            def visit_Operation(self, path):
                self.count += 1

        visitor = OperationCounter()
        traverse(multi_operation_doc, visitor)

        assert visitor.count == 3  # getUsers, createUser, getPosts

    def test_traverse_without_visit_methods(self, simple_doc):
        """Should not crash when visitor has no visit methods."""

        class EmptyVisitor:
            pass

        visitor = EmptyVisitor()
        # Should not raise
        traverse(simple_doc, visitor)


class TestVisitorHooks:
    """Test visitor hook methods."""

    def test_visit_enter_hook_fires_for_all_nodes(self, simple_doc):
        """visit_enter should fire for every node."""

        class EnterCounter:
            def __init__(self):
                self.count = 0

            def visit_enter(self, path):
                self.count += 1

        visitor = EnterCounter()
        traverse(simple_doc, visitor)

        # Should visit OpenAPI30, Info, Paths, PathItem, Operation, Responses, Response
        assert visitor.count > 5

    def test_visit_leave_hook_fires_for_all_nodes(self, simple_doc):
        """visit_leave should fire for every node."""

        class LeaveCounter:
            def __init__(self):
                self.count = 0

            def visit_leave(self, path):
                self.count += 1

        visitor = LeaveCounter()
        traverse(simple_doc, visitor)

        # Should visit same nodes as enter
        assert visitor.count > 5

    def test_visit_enter_classname_hook(self, simple_doc):
        """visit_enter_ClassName should fire before visit_ClassName."""

        class HookOrder:
            def __init__(self):
                self.order = []

            def visit_enter_Operation(self, path):
                self.order.append("enter_Operation")

            def visit_Operation(self, path):
                self.order.append("visit_Operation")

        visitor = HookOrder()
        traverse(simple_doc, visitor)

        assert visitor.order == ["enter_Operation", "visit_Operation"]

    def test_visit_leave_classname_hook(self, simple_doc):
        """visit_leave_ClassName should fire after children."""

        class HookOrder:
            def __init__(self):
                self.order = []

            def visit_Operation(self, path):
                self.order.append("visit_Operation")

            def visit_leave_Operation(self, path):
                self.order.append("leave_Operation")

            def visit_Response(self, path):
                self.order.append("visit_Response")

        visitor = HookOrder()
        traverse(simple_doc, visitor)

        # Response is child of Operation, so should be: Operation, Response, leave Operation
        assert "visit_Operation" in visitor.order
        assert "visit_Response" in visitor.order
        assert "leave_Operation" in visitor.order
        # leave should be after Response
        assert visitor.order.index("visit_Response") < visitor.order.index("leave_Operation")


class TestDispatchOrder:
    """Test the complete hook dispatch order."""

    def test_full_dispatch_order(self, simple_doc):
        """Test all hooks fire in correct order: enter, enter_Class, visit_Class, [children], leave_Class, leave."""

        class FullOrderTracker:
            def __init__(self):
                self.order = []

            def visit_enter(self, path):
                if path.node.__class__.__name__ == "Operation":
                    self.order.append("1_enter")

            def visit_enter_Operation(self, path):
                self.order.append("2_enter_Operation")

            def visit_Operation(self, path):
                self.order.append("3_visit_Operation")

            def visit_Response(self, path):
                self.order.append("4_child_Response")

            def visit_leave_Operation(self, path):
                self.order.append("5_leave_Operation")

            def visit_leave(self, path):
                if path.node.__class__.__name__ == "Operation":
                    self.order.append("6_leave")

        visitor = FullOrderTracker()
        traverse(simple_doc, visitor)

        expected = [
            "1_enter",
            "2_enter_Operation",
            "3_visit_Operation",
            "4_child_Response",
            "5_leave_Operation",
            "6_leave",
        ]
        assert visitor.order == expected


class TestControlFlowNone:
    """Test control flow when returning None."""

    def test_none_continues_traversal(self, simple_doc):
        """Returning None should continue to children."""

        class NodeCounter:
            def __init__(self):
                self.operation_count = 0
                self.response_count = 0

            def visit_Operation(self, path):
                self.operation_count += 1
                return None  # Explicit None

            def visit_Response(self, path):
                self.response_count += 1

        visitor = NodeCounter()
        traverse(simple_doc, visitor)

        assert visitor.operation_count == 1
        assert visitor.response_count == 1  # Child was visited

    def test_no_return_continues_traversal(self, simple_doc):
        """Not returning anything (implicit None) should continue to children."""

        class NodeCounter:
            def __init__(self):
                self.operation_count = 0
                self.response_count = 0

            def visit_Operation(self, path):
                self.operation_count += 1
                # No return (implicit None)

            def visit_Response(self, path):
                self.response_count += 1

        visitor = NodeCounter()
        traverse(simple_doc, visitor)

        assert visitor.operation_count == 1
        assert visitor.response_count == 1  # Child was visited


class TestControlFlowFalse:
    """Test control flow when returning False (skip children)."""

    def test_false_skips_children(self, simple_doc):
        """Returning False should skip children of that node."""

        class SkipOperationChildren:
            def __init__(self):
                self.operation_count = 0
                self.response_count = 0

            def visit_Operation(self, path):
                self.operation_count += 1
                return False  # Skip children

            def visit_Response(self, path):
                self.response_count += 1

        visitor = SkipOperationChildren()
        traverse(simple_doc, visitor)

        assert visitor.operation_count == 1
        assert visitor.response_count == 0  # Children skipped!

    def test_false_from_enter_hook_skips_everything(self, simple_doc):
        """Returning False from enter hook should skip main visit and children."""

        class SkipFromEnter:
            def __init__(self):
                self.visit_called = False
                self.leave_called = False
                self.response_count = 0

            def visit_enter_Operation(self, path):
                return False  # Skip everything (main visit, children, leave)

            def visit_Operation(self, path):
                self.visit_called = True

            def visit_leave_Operation(self, path):
                self.leave_called = True

            def visit_Response(self, path):
                self.response_count += 1

        visitor = SkipFromEnter()
        traverse(simple_doc, visitor)

        assert visitor.visit_called is False  # Main visit NOT called
        assert visitor.leave_called is False  # Leave NOT called
        assert visitor.response_count == 0  # Children NOT visited

    def test_false_still_calls_leave_hooks(self, simple_doc):
        """Returning False should still call leave hooks."""

        class LeaveStillCalled:
            def __init__(self):
                self.leave_called = False

            def visit_Operation(self, path):
                return False  # Skip children

            def visit_leave_Operation(self, path):
                self.leave_called = True

        visitor = LeaveStillCalled()
        traverse(simple_doc, visitor)

        assert visitor.leave_called is True

    def test_false_continues_sibling_traversal(self, multi_operation_doc):
        """Returning False should only skip that node's children, not siblings."""

        class SkipFirstOperation:
            def __init__(self):
                self.operation_count = 0
                self.response_count = 0
                self.skip_first = True

            def visit_Operation(self, path):
                self.operation_count += 1
                if self.skip_first:
                    self.skip_first = False
                    return False  # Skip first operation's children
                return None

            def visit_Response(self, path):
                self.response_count += 1

        visitor = SkipFirstOperation()
        traverse(multi_operation_doc, visitor)

        assert visitor.operation_count == 3  # All operations visited
        assert visitor.response_count == 2  # Only 2nd and 3rd operation's responses


class TestControlFlowBreak:
    """Test control flow when returning BREAK (stop traversal)."""

    def test_break_stops_traversal(self, multi_operation_doc):
        """Returning BREAK should stop entire traversal."""

        class BreakOnFirstOperation:
            def __init__(self):
                self.operation_count = 0
                self.info_visited = False

            def visit_Info(self, path):
                self.info_visited = True

            def visit_Operation(self, path):
                self.operation_count += 1
                return BREAK  # Stop everything

        visitor = BreakOnFirstOperation()
        traverse(multi_operation_doc, visitor)

        assert visitor.info_visited is True  # Info comes before operations
        assert visitor.operation_count == 1  # Stopped after first

    def test_break_from_enter_hook_stops_traversal(self, multi_operation_doc):
        """Returning BREAK from enter hook should stop traversal."""

        class BreakFromEnter:
            def __init__(self):
                self.operation_count = 0

            def visit_enter_Operation(self, path):
                return BREAK

            def visit_Operation(self, path):
                self.operation_count += 1  # Never called

        visitor = BreakFromEnter()
        traverse(multi_operation_doc, visitor)

        assert visitor.operation_count == 0  # Never reached

    def test_break_from_leave_hook_stops_traversal(self, multi_operation_doc):
        """Returning BREAK from leave hook should stop traversal."""

        class BreakFromLeave:
            def __init__(self):
                self.operation_count = 0

            def visit_Operation(self, path):
                self.operation_count += 1

            def visit_leave_Operation(self, path):
                return BREAK  # Stop after leaving first operation

        visitor = BreakFromLeave()
        traverse(multi_operation_doc, visitor)

        assert visitor.operation_count == 1  # Only first operation

    def test_break_stops_before_siblings(self, multi_operation_doc):
        """BREAK should prevent visiting siblings."""

        class BreakBeforeSiblings:
            def __init__(self):
                self.visited_nodes = []

            def visit_PathItem(self, path):
                self.visited_nodes.append("PathItem")
                # After visiting first PathItem, break
                if len(self.visited_nodes) == 1:
                    return BREAK

        visitor = BreakBeforeSiblings()
        traverse(multi_operation_doc, visitor)

        assert visitor.visited_nodes == ["PathItem"]  # Only one


class TestNodePath:
    """Test NodePath context passed to visitors."""

    def test_path_has_node_reference(self, simple_doc):
        """Path should contain reference to current node."""

        class PathInspector:
            def __init__(self):
                self.found_operation = False

            def visit_Operation(self, path):
                assert path.node is not None
                assert path.node.__class__.__name__ == "Operation"
                self.found_operation = True

        visitor = PathInspector()
        traverse(simple_doc, visitor)
        assert visitor.found_operation

    def test_path_tracks_parent_field(self, simple_doc):
        """Path should track parent field name."""

        class PathInspector:
            def __init__(self):
                self.operation_parent_field = None

            def visit_Operation(self, path):
                self.operation_parent_field = path.parent_field

        visitor = PathInspector()
        traverse(simple_doc, visitor)

        assert visitor.operation_parent_field == "get"  # PathItem.get

    def test_path_tracks_parent_key_for_dicts(self, simple_doc):
        """Path should track parent key for dict items."""

        class PathInspector:
            def __init__(self):
                self.path_item_parent_key = None

            def visit_PathItem(self, path):
                self.path_item_parent_key = path.parent_key

        visitor = PathInspector()
        traverse(simple_doc, visitor)

        assert visitor.path_item_parent_key == "/users"  # Key in paths dict

    def test_root_has_no_parent(self, simple_doc):
        """Root node should have no parent."""

        class PathInspector:
            def __init__(self):
                self.root_parent = "not_checked"

            def visit_OpenAPI30(self, path):
                self.root_parent = path.parent

        visitor = PathInspector()
        traverse(simple_doc, visitor)

        assert visitor.root_parent is None


class TestInheritance:
    """Test DataModelLowVisitor base class usage."""

    def test_can_inherit_from_base_class(self, simple_doc):
        """Should be able to inherit from DataModelLowVisitor."""

        class MyVisitor(DataModelLowVisitor):
            def __init__(self):
                self.count = 0

            def visit_Operation(self, path):
                self.count += 1

        visitor = MyVisitor()
        traverse(simple_doc, visitor)

        assert visitor.count == 1

    def test_duck_typing_works_without_inheritance(self, simple_doc):
        """Should work without inheriting (duck typing)."""

        class DuckVisitor:  # No inheritance
            def __init__(self):
                self.count = 0

            def visit_Operation(self, path):
                self.count += 1

        visitor = DuckVisitor()
        traverse(simple_doc, visitor)

        assert visitor.count == 1


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_visitor_method_returns_true(self, simple_doc):
        """Returning True should be treated like None (continue)."""

        class ReturnsTrue:
            def __init__(self):
                self.response_count = 0

            def visit_Operation(self, path):
                return True  # Not False or BREAK

            def visit_Response(self, path):
                self.response_count += 1

        visitor = ReturnsTrue()
        traverse(simple_doc, visitor)

        assert visitor.response_count == 1  # Children visited

    def test_visitor_method_returns_arbitrary_value(self, simple_doc):
        """Returning arbitrary values should be treated like None."""

        class ReturnsString:
            def __init__(self):
                self.response_count = 0

            def visit_Operation(self, path):
                return "some_string"  # Not False or BREAK

            def visit_Response(self, path):
                self.response_count += 1

        visitor = ReturnsString()
        traverse(simple_doc, visitor)

        assert visitor.response_count == 1  # Children visited

    def test_multiple_hooks_same_visitor(self, simple_doc):
        """Visitor can have multiple hook types for same node."""

        class MultiHookVisitor:
            def __init__(self):
                self.hooks_called = []

            def visit_enter_Operation(self, path):
                self.hooks_called.append("enter")

            def visit_Operation(self, path):
                self.hooks_called.append("main")

            def visit_leave_Operation(self, path):
                self.hooks_called.append("leave")

        visitor = MultiHookVisitor()
        traverse(simple_doc, visitor)

        assert visitor.hooks_called == ["enter", "main", "leave"]

    def test_empty_document_traversal(self):
        """Should handle minimal OpenAPI document."""
        yaml_text = textwrap.dedent("""
            openapi: 3.0.4
            info:
              title: Minimal
              version: 1.0.0
        """)
        parser = OpenAPIParser("datamodel-low")
        doc = parser.parse(yaml_text, return_type=OpenAPI30)

        class CounterVisitor:
            def __init__(self):
                self.count = 0

            def visit_Info(self, path):
                self.count += 1

        visitor = CounterVisitor()
        traverse(doc, visitor)

        assert visitor.count == 1
