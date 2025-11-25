"""Core traversal functionality for low-level OpenAPI datamodels."""

from jentic.apitools.openapi.datamodels.low.fields import patterned_fields

from .introspection import get_traversable_fields, is_datamodel_node, unwrap_value
from .path import NodePath


__all__ = ["DataModelLowVisitor", "traverse", "BREAK"]


class _BreakType: ...


BREAK = _BreakType()


class DataModelLowVisitor:
    """
    Optional base class for OpenAPI datamodel visitors.

    You don't need to inherit from this class - just implement visit_* methods.
    Inheritance is optional and provides no functionality - use for organizational purposes only.

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
        4. [child traversal - automatic unless False returned]
        5. visit_leave_ClassName(path) - specific leave
        6. visit_leave(path) - generic leave

    Return Values:
        - None: Continue traversal normally (children visited automatically)
        - False: Skip visiting children of this node
        - BREAK: Stop entire traversal immediately

    Example (with enter/leave hooks):
        class MyVisitor(DataModelLowVisitor):  # Optional inheritance
            def visit_enter_Operation(self, path):
                print(f"Entering: {path.format_path()}")

            def visit_leave_Operation(self, path):
                print(f"Leaving: {path.format_path()}")

        class SimpleVisitor:  # No inheritance (duck typing works too)
            def visit_Operation(self, path):
                print(f"Found: {path.format_path()}")
                # Children automatically visited
    """

    pass


def traverse(root, visitor) -> None:
    """
    Traverse OpenAPI datamodel tree using visitor pattern.

    The visitor can be any object with visit_* methods (duck typing).
    Optionally inherit from DataModelLowVisitor for organizational purposes.

    Children are automatically traversed unless a visitor method returns False.
    Use enter/leave hooks for pre/post traversal logic.

    Args:
        root: Root datamodel object (OpenAPI30, OpenAPI31, or any datamodel node)
        visitor: Object with visit_* methods

    Example:
        # Using enter/leave hooks
        class MyVisitor(DataModelLowVisitor):
            def visit_enter_Operation(self, path):
                print(f"Entering operation: {path.format_path()}")

            def visit_leave_Operation(self, path):
                print(f"Leaving operation: {path.format_path()}")

        # Simple visitor (duck typing - no inheritance needed)
        class SimpleVisitor:
            def visit_Operation(self, path):
                print(f"Found operation: {path.format_path()}")
                # Children automatically visited

        doc = parser.parse(..., return_type=DataModelLow)
        traverse(doc, MyVisitor())
        traverse(doc, SimpleVisitor())
    """
    # Create initial root path
    initial_path = NodePath(
        node=root,
        parent_path=None,
        parent_field=None,
        parent_key=None,
    )

    # Start traversal
    _visit_node(visitor, initial_path)


def _default_traverse_children(visitor, path: NodePath) -> _BreakType | None:
    """
    Internal child traversal logic.

    Iterates through traversable fields and visits datamodel children.
    Called automatically during traversal.

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
            # Check if this field is a patterned field
            # Patterned fields (like Paths.paths, Components.schemas) should not
            # add their field name to the path when iterating dict items
            patterned_field_names = patterned_fields(type(path.node))
            is_patterned = field_name in patterned_field_names

            for key, value in unwrapped.items():
                unwrapped_key = unwrap_value(key)
                unwrapped_value = unwrap_value(value)

                if is_datamodel_node(unwrapped_value):
                    # Dict keys should be str after unwrapping (field names, paths, status codes, etc.)
                    assert isinstance(unwrapped_key, (str, int)), (
                        f"Expected str or int key, got {type(unwrapped_key)}"
                    )
                    # For patterned fields, don't include the field name in the path
                    # (e.g., Paths.paths is patterned, so /paths/{path-key} not /paths/paths/{path-key})
                    dict_field_name: str | None = None if is_patterned else field_name
                    child_path = path.create_child(
                        node=unwrapped_value,
                        parent_field=dict_field_name,
                        parent_key=unwrapped_key,
                    )
                    result = _visit_node(visitor, child_path)
                    if result is BREAK:
                        return BREAK

    return None


def _visit_node(visitor, path: NodePath) -> _BreakType | None:
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
        result = _default_traverse_children(visitor, path)
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
