"""Tests for visitor merging functionality (ApiDOM semantics)."""

import textwrap

import pytest

from jentic.apitools.openapi.datamodels.low.v30 import OpenAPI30
from jentic.apitools.openapi.parser.core import OpenAPIParser
from jentic.apitools.openapi.traverse.datamodels.low import (
    BREAK,
    DataModelLowVisitor,
    merge_visitors,
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
def multi_path_doc():
    """OpenAPI document with multiple paths for testing."""
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
          /posts:
            post:
              operationId: createPost
              responses:
                '201':
                  description: Created
    """)
    parser = OpenAPIParser("datamodel-low")
    return parser.parse(yaml_text, return_type=OpenAPI30)


class TestBasicMerging:
    """Test basic visitor merging functionality."""

    def test_merge_empty_visitors(self, simple_doc):
        """Merging with no visitors should work."""
        merged = merge_visitors()
        # Should not raise
        traverse(simple_doc, merged)

    def test_merge_single_visitor(self, simple_doc):
        """Merging single visitor should work."""

        class CounterVisitor:
            def __init__(self):
                self.count = 0

            def visit_Operation(self, path):
                self.count += 1

        visitor = CounterVisitor()
        merged = merge_visitors(visitor)
        traverse(simple_doc, merged)

        assert visitor.count == 1

    def test_merge_two_visitors(self, simple_doc):
        """Both visitors should be called."""

        class Visitor1:
            def __init__(self):
                self.visited = []

            def visit_Operation(self, path):
                self.visited.append("v1")

        class Visitor2:
            def __init__(self):
                self.visited = []

            def visit_Operation(self, path):
                self.visited.append("v2")

        v1 = Visitor1()
        v2 = Visitor2()
        merged = merge_visitors(v1, v2)
        traverse(simple_doc, merged)

        assert v1.visited == ["v1"]
        assert v2.visited == ["v2"]

    def test_visitors_called_in_order(self, simple_doc):
        """Visitors should be called in the order provided."""

        class OrderTracker:
            def __init__(self):
                self.order = []

        tracker = OrderTracker()

        class Visitor1:
            def visit_Operation(self, path):
                tracker.order.append(1)

        class Visitor2:
            def visit_Operation(self, path):
                tracker.order.append(2)

        class Visitor3:
            def visit_Operation(self, path):
                tracker.order.append(3)

        merged = merge_visitors(Visitor1(), Visitor2(), Visitor3())
        traverse(simple_doc, merged)

        assert tracker.order == [1, 2, 3]

    def test_visitors_with_different_methods(self, simple_doc):
        """Visitors with different methods should work independently."""

        class InfoVisitor:
            def __init__(self):
                self.count = 0

            def visit_Info(self, path):
                self.count += 1

        class OperationVisitor:
            def __init__(self):
                self.count = 0

            def visit_Operation(self, path):
                self.count += 1

        info_v = InfoVisitor()
        op_v = OperationVisitor()
        merged = merge_visitors(info_v, op_v)
        traverse(simple_doc, merged)

        assert info_v.count == 1
        assert op_v.count == 1


class TestPerVisitorSkip:
    """Test per-visitor skip semantics (ApiDOM pattern)."""

    def test_one_visitor_skips_other_continues(self, simple_doc):
        """When one visitor skips, other visitors continue."""

        class SkipperVisitor:
            def __init__(self):
                self.visited = []

            def visit_enter(self, path):
                node_type = path.node.__class__.__name__
                self.visited.append(node_type)
                if node_type == "PathItem":
                    return False  # Skip children

        class NormalVisitor:
            def __init__(self):
                self.visited = []

            def visit_enter(self, path):
                node_type = path.node.__class__.__name__
                self.visited.append(node_type)

        skipper = SkipperVisitor()
        normal = NormalVisitor()
        merged = merge_visitors(skipper, normal)
        traverse(simple_doc, merged)

        # Skipper should not see Operation (child of PathItem)
        assert "Operation" not in skipper.visited
        # Normal should see Operation
        assert "Operation" in normal.visited

    def test_skip_affects_only_skipping_visitor(self, multi_path_doc):
        """Skip should only affect the visitor that returns False."""

        class SelectiveSkipper:
            def __init__(self):
                self.operations = []
                self.path_items_seen = 0

            def visit_PathItem(self, path):
                self.path_items_seen += 1
                # Skip first PathItem only
                if self.path_items_seen == 1:
                    return False

            def visit_Operation(self, path):
                self.operations.append(path.node)

        class FullVisitor:
            def __init__(self):
                self.operations = []

            def visit_Operation(self, path):
                self.operations.append(path.node)

        skipper = SelectiveSkipper()
        full = FullVisitor()
        merged = merge_visitors(skipper, full)
        traverse(multi_path_doc, merged)

        # Skipper skipped first PathItem, so saw only 1 operation
        assert len(skipper.operations) == 1
        # Full visitor saw both operations
        assert len(full.operations) == 2

    def test_multiple_visitors_skip_independently(self, simple_doc):
        """Multiple visitors can skip different nodes independently."""

        class SkipInfo:
            def __init__(self):
                self.visited = []

            def visit_Info(self, path):
                self.visited.append("Info")
                return False  # Skip Info children

        class SkipPaths:
            def __init__(self):
                self.visited = []

            def visit_Paths(self, path):
                self.visited.append("Paths")
                return False  # Skip Paths children

        class VisitAll:
            def __init__(self):
                self.node_types = set()

            def visit_enter(self, path):
                self.node_types.add(path.node.__class__.__name__)

        skip_info = SkipInfo()
        skip_paths = SkipPaths()
        visit_all = VisitAll()

        merged = merge_visitors(skip_info, skip_paths, visit_all)
        traverse(simple_doc, merged)

        # VisitAll should see everything
        assert "Info" in visit_all.node_types
        assert "Paths" in visit_all.node_types
        assert "Operation" in visit_all.node_types


class TestPerVisitorResume:
    """Test that visitors resume after skipping a node."""

    def test_visitor_resumes_after_skip(self, multi_path_doc):
        """Visitor should resume when leaving the skipped node."""

        class SkipFirstPathItem:
            def __init__(self):
                self.path_items = 0
                self.operations = 0

            def visit_PathItem(self, path):
                self.path_items += 1
                if self.path_items == 1:
                    return False  # Skip first PathItem

            def visit_Operation(self, path):
                self.operations += 1

        visitor = SkipFirstPathItem()
        merged = merge_visitors(visitor)
        traverse(multi_path_doc, merged)

        # Should see both PathItems
        assert visitor.path_items == 2
        # Should see only second Operation (first was skipped)
        assert visitor.operations == 1

    def test_resume_allows_siblings(self, multi_path_doc):
        """After skipping, visitor should continue with siblings."""

        class PathCounter:
            def __init__(self):
                self.path_item_count = 0
                self.paths_visited = 0

            def visit_PathItem(self, path):
                self.path_item_count += 1
                if self.path_item_count == 1:
                    return False

            def visit_Paths(self, path):
                self.paths_visited += 1

        visitor = PathCounter()
        merged = merge_visitors(visitor)
        traverse(multi_path_doc, merged)

        # Should see both PathItems (resume after first skip)
        assert visitor.path_item_count == 2
        # Should see Paths once
        assert visitor.paths_visited == 1


class TestPerVisitorBreak:
    """Test per-visitor break semantics (ApiDOM pattern)."""

    def test_one_visitor_breaks_other_continues(self, multi_path_doc):
        """When one visitor breaks, other visitors continue."""

        class BreakerVisitor:
            def __init__(self):
                self.operations = 0

            def visit_Operation(self, path):
                self.operations += 1
                return BREAK  # Stop this visitor

        class NormalVisitor:
            def __init__(self):
                self.operations = 0

            def visit_Operation(self, path):
                self.operations += 1

        breaker = BreakerVisitor()
        normal = NormalVisitor()
        merged = merge_visitors(breaker, normal)
        traverse(multi_path_doc, merged)

        # Breaker stopped after first Operation
        assert breaker.operations == 1
        # Normal saw both Operations
        assert normal.operations == 2

    def test_break_stops_visitor_permanently(self, multi_path_doc):
        """BREAK should stop visitor for rest of traversal."""

        class BreakOnFirst:
            def __init__(self):
                self.visited = []

            def visit_enter(self, path):
                node_type = path.node.__class__.__name__
                self.visited.append(node_type)

            def visit_Operation(self, path):
                return BREAK

        visitor = BreakOnFirst()
        merged = merge_visitors(visitor)
        traverse(multi_path_doc, merged)

        # Should see nodes up to first Operation
        assert "Operation" in visitor.visited
        # Count how many times visitor was called
        operation_count = visitor.visited.count("Operation")
        # Should see only first Operation, not second
        assert operation_count == 1

    def test_multiple_visitors_break_independently(self, multi_path_doc):
        """Multiple visitors can break at different points."""

        class BreakOnInfo:
            def __init__(self):
                self.nodes = []

            def visit_enter(self, path):
                self.nodes.append(path.node.__class__.__name__)

            def visit_Info(self, path):
                return BREAK

        class BreakOnOperation:
            def __init__(self):
                self.nodes = []

            def visit_enter(self, path):
                self.nodes.append(path.node.__class__.__name__)

            def visit_Operation(self, path):
                return BREAK

        class NeverBreak:
            def __init__(self):
                self.count = 0

            def visit_enter(self, path):
                self.count += 1

        v1 = BreakOnInfo()
        v2 = BreakOnOperation()
        v3 = NeverBreak()

        merged = merge_visitors(v1, v2, v3)
        traverse(multi_path_doc, merged)

        # v1 stopped at Info (early)
        assert "Info" in v1.nodes
        assert "Operation" not in v1.nodes

        # v2 stopped at first Operation (later)
        assert "Info" in v2.nodes
        assert "Operation" in v2.nodes
        assert v2.nodes.count("Operation") == 1

        # v3 never stopped
        assert v3.count > len(v1.nodes)
        assert v3.count > len(v2.nodes)


class TestMixedBehavior:
    """Test visitors with mixed skip/break/normal behavior."""

    def test_skip_break_and_normal_together(self, multi_path_doc):
        """Mix of skip, break, and normal visitors."""

        class Skipper:
            def __init__(self):
                self.path_items = 0

            def visit_PathItem(self, path):
                self.path_items += 1
                return False  # Skip children

        class Breaker:
            def __init__(self):
                self.operations = 0

            def visit_Operation(self, path):
                self.operations += 1
                return BREAK

        class Normal:
            def __init__(self):
                self.operations = 0

            def visit_Operation(self, path):
                self.operations += 1

        skipper = Skipper()
        breaker = Breaker()
        normal = Normal()

        merged = merge_visitors(skipper, breaker, normal)
        traverse(multi_path_doc, merged)

        # Skipper saw both PathItems but no operations
        assert skipper.path_items == 2

        # Breaker saw only first operation
        assert breaker.operations == 1

        # Normal saw both operations
        assert normal.operations == 2


class TestAutomaticTraversal:
    """Test that merged visitor automatically traverses children."""

    def test_merged_visitor_visits_node_and_children(self, simple_doc):
        """Merged visitor should visit node and automatically traverse children."""

        class CustomVisitor(DataModelLowVisitor):
            def __init__(self):
                self.info_count = 0
                self.response_count = 0

            def visit_Info(self, path):
                self.info_count += 1
                # Children automatically visited (no return needed)

            def visit_Response(self, path):
                self.response_count += 1

        visitor = CustomVisitor()
        merged = merge_visitors(visitor)

        traverse(simple_doc, merged)

        # Should visit Info and also reach Response (proving children traversed)
        assert visitor.info_count == 1
        assert visitor.response_count == 1

    def test_merged_visitor_traverses_children_by_default(self, simple_doc):
        """Merged visitor should traverse children even without specific methods."""

        class LeafVisitor:
            """Only visits leaf nodes."""

            def __init__(self):
                self.responses = 0

            def visit_Response(self, path):
                self.responses += 1

        visitor = LeafVisitor()
        merged = merge_visitors(visitor)
        traverse(simple_doc, merged)

        # Should reach Response even though no visit methods for parents
        assert visitor.responses == 1


class TestEnterLeaveHooks:
    """Test that merged visitors support enter/leave hooks."""

    def test_generic_enter_leave_hooks(self, simple_doc):
        """Generic enter/leave hooks work with merged visitors."""

        class EnterLeaveVisitor:
            def __init__(self):
                self.enters = 0
                self.leaves = 0

            def visit_enter(self, path):
                self.enters += 1

            def visit_leave(self, path):
                self.leaves += 1

        visitor = EnterLeaveVisitor()
        merged = merge_visitors(visitor)
        traverse(simple_doc, merged)

        # Should match
        assert visitor.enters == visitor.leaves
        assert visitor.enters > 0

    def test_specific_enter_leave_hooks(self, simple_doc):
        """Specific enter/leave hooks work with merged visitors."""

        class OperationHooks:
            def __init__(self):
                self.enters = 0
                self.leaves = 0

            def visit_enter_Operation(self, path):
                self.enters += 1

            def visit_leave_Operation(self, path):
                self.leaves += 1

        visitor = OperationHooks()
        merged = merge_visitors(visitor)
        traverse(simple_doc, merged)

        assert visitor.enters == 1
        assert visitor.leaves == 1

    def test_enter_skip_prevents_leave_call(self, simple_doc):
        """When enter hook skips, visitor doesn't see node's leave."""

        class SkipOnEnter:
            def __init__(self):
                self.enters = 0
                self.leaves = 0

            def visit_enter_PathItem(self, path):
                self.enters += 1
                return False  # Skip

            def visit_leave_PathItem(self, path):
                self.leaves += 1

        visitor = SkipOnEnter()
        merged = merge_visitors(visitor)
        traverse(simple_doc, merged)

        # Enter was called, but leave was not (visitor was skipping)
        assert visitor.enters == 1
        assert visitor.leaves == 0


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_visitor_without_any_methods(self, simple_doc):
        """Visitor with no visit methods should not raise."""

        class EmptyVisitor:
            pass

        merged = merge_visitors(EmptyVisitor())
        # Should not raise
        traverse(simple_doc, merged)

    def test_none_return_value(self, simple_doc):
        """Returning None should continue normally."""

        class NoneReturner:
            def __init__(self):
                self.count = 0

            def visit_Operation(self, path):
                self.count += 1
                return None  # Explicit None

        visitor = NoneReturner()
        merged = merge_visitors(visitor)
        traverse(simple_doc, merged)

        assert visitor.count == 1

    def test_true_return_value_ignored(self, simple_doc):
        """Returning True should not affect traversal."""

        class TrueReturner:
            def __init__(self):
                self.operations = 0
                self.responses = 0

            def visit_Operation(self, path):
                self.operations += 1
                return True  # Should be ignored

            def visit_Response(self, path):
                self.responses += 1

        visitor = TrueReturner()
        merged = merge_visitors(visitor)
        traverse(simple_doc, merged)

        # Should see both Operation and its Response child
        assert visitor.operations == 1
        assert visitor.responses == 1


class TestStateIndependence:
    """Test that visitor states are truly independent."""

    def test_skip_state_independent(self, multi_path_doc):
        """Each visitor maintains independent skip state."""

        class Visitor1:
            def __init__(self):
                self.path_items = []

            def visit_PathItem(self, path):
                self.path_items.append("v1")
                # First visitor skips first PathItem
                if len(self.path_items) == 1:
                    return False

        class Visitor2:
            def __init__(self):
                self.path_items = []

            def visit_PathItem(self, path):
                self.path_items.append("v2")
                # Second visitor skips second PathItem
                if len(self.path_items) == 2:
                    return False

        v1 = Visitor1()
        v2 = Visitor2()
        merged = merge_visitors(v1, v2)
        traverse(multi_path_doc, merged)

        # Both saw both PathItems (resumed after their respective skips)
        assert len(v1.path_items) == 2
        assert len(v2.path_items) == 2

    def test_break_state_independent(self, multi_path_doc):
        """Each visitor maintains independent break state."""

        class CountToTwo:
            def __init__(self):
                self.count = 0

            def visit_enter(self, path):
                self.count += 1
                if self.count >= 2:
                    return BREAK

        class CountAll:
            def __init__(self):
                self.count = 0

            def visit_enter(self, path):
                self.count += 1

        breaker = CountToTwo()
        counter = CountAll()
        merged = merge_visitors(breaker, counter)
        traverse(multi_path_doc, merged)

        # Breaker stopped at 2
        assert breaker.count == 2
        # Counter continued
        assert counter.count > 2

    def test_mixed_state_isolation(self, multi_path_doc):
        """Skip and break states don't interfere between visitors."""

        class SkipAndBreak:
            def __init__(self):
                self.operations = 0

            def visit_PathItem(self, path):
                return False  # Skip all PathItems

            def visit_Info(self, path):
                return BREAK  # Break at Info

        class Normal:
            def __init__(self):
                self.operations = 0
                self.info_count = 0

            def visit_Operation(self, path):
                self.operations += 1

            def visit_Info(self, path):
                self.info_count += 1

        blocker = SkipAndBreak()
        normal = Normal()
        merged = merge_visitors(blocker, normal)
        traverse(multi_path_doc, merged)

        # Normal visitor unaffected by blocker's skip and break
        assert normal.operations == 2
        assert normal.info_count == 1
