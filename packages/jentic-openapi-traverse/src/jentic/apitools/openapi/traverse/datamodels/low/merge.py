"""Visitor merging utilities (ApiDOM pattern)."""

from .path import NodePath
from .traversal import BREAK, _BreakType


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
        """Composite visitor with per-visitor state tracking (ApiDOM pattern).

        Uses method caching to avoid repeated __getattr__ overhead during
        traversal. Resolved closures are stored in self.__dict__ so Python's
        attribute lookup finds them directly on subsequent accesses.
        """

        def __init__(self, visitors):
            self.visitors = visitors
            # State per visitor: None = active, NodePath = skipping, BREAK = stopped
            self._skipping_state: list[NodePath | _BreakType | None] = [None] * len(visitors)
            # Negative cache: hook names where no visitor has an implementation
            self._absent_methods: set[str] = set()

        def __getattr__(self, name):
            if not name.startswith("visit"):
                raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

            # Fast negative cache check
            if name in self._absent_methods:
                raise AttributeError(name)

            is_leave_hook = name.startswith("visit_leave")

            # Resolve which visitors implement this method (once)
            implementors = [
                (i, getattr(v, name)) for i, v in enumerate(self.visitors) if hasattr(v, name)
            ]

            if is_leave_hook:
                # Leave hooks MUST always be callable (for skip-resume logic).
                # When a visitor returned False from an enter/visit hook, the
                # resume happens inside the leave closure when
                # state.node is path.node. If hasattr returned False for the
                # leave hook, resume would never trigger.
                method_map = {i: m for i, m in implementors}
                num_visitors = len(self.visitors)
                skipping_state = self._skipping_state

                def merged_leave(path):
                    for i in range(num_visitors):
                        state = skipping_state[i]
                        if state is None:
                            method = method_map.get(i)
                            if method is not None:
                                result = method(path)
                                if result is BREAK:
                                    skipping_state[i] = BREAK
                        elif isinstance(state, NodePath) and state.node is path.node:
                            skipping_state[i] = None
                    return None

                self.__dict__[name] = merged_leave
                return merged_leave
            else:
                # Enter/visit hooks: skip entirely if no visitor implements them
                if not implementors:
                    self._absent_methods.add(name)
                    raise AttributeError(name)

                skipping_state = self._skipping_state

                def merged_enter(path):
                    for i, method in implementors:
                        if skipping_state[i] is None:
                            result = method(path)
                            if result is BREAK:
                                skipping_state[i] = BREAK
                            elif result is False:
                                skipping_state[i] = path
                    return None

                self.__dict__[name] = merged_enter
                return merged_enter

    return MergedVisitor(visitors)
