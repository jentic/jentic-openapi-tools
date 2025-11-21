"""Core traversal functionality for low-level OpenAPI datamodels."""

from .introspection import get_traversable_fields, is_datamodel_node, unwrap_value
from .path import NodePath


# Control flow symbol
BREAK = object()

__all__ = ["DataModelLowVisitor", "traverse", "BREAK", "default_traverse_children"]


class DataModelLowVisitor:
    """
    Optional base class for OpenAPI datamodel visitors.

    You don't need to inherit from this class - just implement visit_* methods.
    This class provides generic_visit() utility for default child traversal.

    Visitor Method Signatures:
        Generic hooks (fire for ALL nodes):
        - visit_enter(path: NodePath) -> None | False | BREAK
        - visit_leave(path: NodePath) -> None | False | BREAK

        Class-specific hooks (fire for matching node types):
        - visit_ClassName(path: NodePath) -> None | False | BREAK
        - visit_enter_ClassName(path: NodePath) -> None | False | BREAK
        - visit_leave_ClassName(path: NodePath) -> None | False | BREAK

    Dispatch Order:
        1. visit_enter(path) - generic enter
        2. visit_enter_ClassName(path) - specific enter
        3. visit_ClassName(path) - main visitor
        4. [child traversal]
        5. visit_leave_ClassName(path) - specific leave
        6. visit_leave(path) - generic leave

    Return Values:
        - None: Continue traversal normally
        - False: Skip visiting children of this node
        - BREAK: Stop entire traversal immediately

    Example:
        class MyVisitor(DataModelLowVisitor):  # Optional inheritance
            def visit_Operation(self, path):
                print(path.format_path())
                return self.generic_visit(path)  # Use inherited utility

        class SimpleVisitor:  # No inheritance (duck typing)
            def visit_Operation(self, path):
                print(path.format_path())
    """

    def generic_visit(self, path: NodePath):
        """
        Default visitor that traverses all children.

        Useful when inheriting from DataModelLowVisitor.
        Discovers traversable fields and visits them automatically.

        Args:
            path: Current node path

        Returns:
            None (continues traversal)
        """
        return default_traverse_children(self, path)


def default_traverse_children(visitor, path: NodePath):
    """
    Default child traversal logic.

    Used when no visit method exists or when visit method returns None.
    Can be used by custom visitors that need standard child traversal behavior.

    Args:
        visitor: Visitor object with visit_* methods
        path: Current node path

    Returns:
        BREAK to stop traversal, None otherwise
    """
    # Get all traversable fields
    for field_name, field_value in get_traversable_fields(path.node):
        unwrapped = unwrap_value(field_value)

        # Handle single datamodel nodes
        if is_datamodel_node(unwrapped):
            child_path = path.create_child(node=unwrapped, parent_field=field_name, parent_key=None)
            result = _visit_node(visitor, child_path)
            if result is BREAK:
                return BREAK

        # Handle lists
        elif isinstance(unwrapped, list):
            for idx, item in enumerate(unwrapped):
                if is_datamodel_node(item):
                    child_path = path.create_child(
                        node=item, parent_field=field_name, parent_key=idx
                    )
                    result = _visit_node(visitor, child_path)
                    if result is BREAK:
                        return BREAK

        # Handle dicts
        elif isinstance(unwrapped, dict):
            for key, value in unwrapped.items():
                unwrapped_key = unwrap_value(key)
                unwrapped_value = unwrap_value(value)

                if is_datamodel_node(unwrapped_value):
                    # Dict keys should be str after unwrapping (field names, paths, status codes, etc.)
                    assert isinstance(unwrapped_key, (str, int)), (
                        f"Expected str or int key, got {type(unwrapped_key)}"
                    )
                    child_path = path.create_child(
                        node=unwrapped_value,
                        parent_field=field_name,
                        parent_key=unwrapped_key,
                    )
                    result = _visit_node(visitor, child_path)
                    if result is BREAK:
                        return BREAK

    return None


def _visit_node(visitor, path: NodePath):
    """
    Visit a single node with the visitor.

    Handles enter/main/leave dispatch and control flow.
    Duck typed - works with any object that has visit_* methods.

    Args:
        visitor: Visitor object with visit_* methods
        path: Current node path

    Returns:
        BREAK to stop traversal, None otherwise
    """
    node_class = path.node.__class__.__name__

    # Generic enter hook: visit_enter (fires for ALL nodes)
    if hasattr(visitor, "visit_enter"):
        result = visitor.visit_enter(path)
        if result is BREAK:
            return BREAK
        if result is False:
            return None  # Skip children, but continue traversal

    # Try enter hook: visit_enter_ClassName
    enter_method = f"visit_enter_{node_class}"
    if hasattr(visitor, enter_method):
        result = getattr(visitor, enter_method)(path)
        if result is BREAK:
            return BREAK
        if result is False:
            return None  # Skip children, but continue traversal

    # Try main visitor: visit_ClassName
    visit_method = f"visit_{node_class}"
    skip_auto_traverse = False

    if hasattr(visitor, visit_method):
        result = getattr(visitor, visit_method)(path)
        # Only care about BREAK and False:
        # - BREAK: stop entire traversal
        # - False: skip children of this node
        # - Any other value (None, True, etc.): continue normally
        if result is BREAK:
            return BREAK
        if result is False:
            skip_auto_traverse = True

    # Automatic child traversal (unless explicitly skipped)
    if not skip_auto_traverse:
        # Check if visitor has custom generic_visit
        if hasattr(visitor, "generic_visit"):
            result = visitor.generic_visit(path)
            if result is BREAK:
                return BREAK
        else:
            # Use default traversal
            result = default_traverse_children(visitor, path)
            if result is BREAK:
                return BREAK

    # Try leave hook: visit_leave_ClassName
    leave_method = f"visit_leave_{node_class}"
    if hasattr(visitor, leave_method):
        result = getattr(visitor, leave_method)(path)
        if result is BREAK:
            return BREAK

    # Generic leave hook: visit_leave (fires for ALL nodes)
    if hasattr(visitor, "visit_leave"):
        result = visitor.visit_leave(path)
        if result is BREAK:
            return BREAK

    return None


def traverse(root, visitor) -> None:
    """
    Traverse OpenAPI datamodel tree using visitor pattern.

    The visitor can be any object with visit_* methods (duck typing).
    Optionally inherit from DataModelLowVisitor for generic_visit() utility.

    Args:
        root: Root datamodel object (OpenAPI30, OpenAPI31, or any datamodel node)
        visitor: Object with visit_* methods

    Example:
        # With inheritance
        class MyVisitor(DataModelLowVisitor):
            def visit_Operation(self, path):
                print(f"Operation: {path.format_path()}")
                return self.generic_visit(path)

        # Without inheritance (duck typing)
        class SimpleVisitor:
            def visit_Operation(self, path):
                print(f"Operation: {path.format_path()}")

        doc = parser.parse(..., return_type=DataModelLow)
        traverse(doc, MyVisitor())
        traverse(doc, SimpleVisitor())
    """
    # Create initial root path
    initial_path = NodePath(
        node=root,
        parent=None,
        parent_field=None,
        parent_key=None,
        ancestors=(),
    )

    # Start traversal
    _visit_node(visitor, initial_path)
