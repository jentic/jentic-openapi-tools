"""Visitor merging utilities (ApiDOM pattern)."""

from .path import NodePath
from .traversal import BREAK


__all__ = ["merge_visitors"]


def merge_visitors(*visitors) -> object:
    """
    Merge multiple visitors into one composite visitor (ApiDOM semantics).

    Each visitor maintains independent state:
    - If visitor[i] returns False, only that visitor skips children (resumes when leaving)
    - If visitor[i] returns BREAK, only that visitor stops permanently
    - Other visitors continue normally

    This matches ApiDOM's per-visitor control model where each visitor can
    independently skip subtrees or stop without affecting other visitors.

    Args:
        *visitors: Visitor objects (with visit_* methods)

    Returns:
        A new visitor object that runs all visitors with independent state

    Example:
        security_check = SecurityCheckVisitor()
        counter = OperationCounterVisitor()
        validator = SchemaValidatorVisitor()

        # Each visitor can skip/break independently
        merged = merge_visitors(security_check, counter, validator)
        traverse(doc, merged)

        # If security_check.visit_PathItem returns False:
        # - security_check skips PathItem's children
        # - counter and validator still visit children normally
    """

    class MergedVisitor:
        """Composite visitor with per-visitor state tracking (ApiDOM pattern)."""

        def __init__(self, visitors):
            self.visitors = visitors
            # State per visitor: None = active, NodePath = skipping, BREAK = stopped
            self._skipping_state: list[NodePath | object | None] = [None] * len(visitors)

        def _is_active(self, visitor_idx):
            """Check if visitor is active (not skipping or stopped)."""
            return self._skipping_state[visitor_idx] is None

        def _is_skipping_node(self, visitor_idx, path):
            """Check if we're leaving the exact node this visitor skipped."""
            state = self._skipping_state[visitor_idx]
            if state is None or state is BREAK:
                return False
            # At this point, state must be a NodePath
            # Compare node identity (not equality)
            assert isinstance(state, NodePath)
            return state.node is path.node

        def __getattr__(self, name):
            """
            Dynamically handle visit_* method calls.

            Maintains per-visitor state for skip/break control.

            Args:
                name: Method name being called

            Returns:
                Callable that merges visitor results with state tracking

            Raises:
                AttributeError: If not a visit_* method
            """
            if not name.startswith("visit"):
                raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

            # Determine if this is a leave hook
            is_leave_hook = name.startswith("visit_leave")

            def merged_visit_method(path: NodePath):
                for i, visitor in enumerate(self.visitors):
                    if is_leave_hook:
                        # Leave hook: only call if visitor is active
                        if self._is_active(i) and hasattr(visitor, name):
                            result = getattr(visitor, name)(path)
                            if result is BREAK:
                                self._skipping_state[i] = BREAK  # Stop this visitor
                        # Resume visitor if leaving the skipped node (don't call leave hook)
                        elif self._is_skipping_node(i, path):
                            self._skipping_state[i] = None  # Resume for next nodes
                    else:
                        # Enter/visit hook: only call if visitor is active
                        if self._is_active(i) and hasattr(visitor, name):
                            result = getattr(visitor, name)(path)

                            if result is BREAK:
                                self._skipping_state[i] = BREAK  # Stop this visitor
                            elif result is False:
                                self._skipping_state[i] = path  # Skip descendants

                # Never return BREAK or False - let traversal continue for all visitors
                return None

            return merged_visit_method

    return MergedVisitor(visitors)
