"""Visitor merging utilities (ApiDOM pattern)."""

from .path import NodePath
from .traversal import BREAK


__all__ = ["merge_visitors"]


def merge_visitors(*visitors) -> object:
    """
    Merge multiple visitors into one composite visitor.

    Visitors are called in sequence on each node.
    If any visitor returns BREAK, traversal stops immediately.
    If any visitor returns False, children are skipped.

    Args:
        *visitors: Visitor objects (with visit_* methods)

    Returns:
        A new visitor object that runs all visitors in sequence

    Example:
        security_check = SecurityCheckVisitor()
        counter = OperationCounterVisitor()
        validator = SchemaValidatorVisitor()

        merged = merge_visitors(security_check, counter, validator)
        traverse(doc, merged)
    """

    class MergedVisitor:
        """Composite visitor that runs multiple visitors."""

        def __init__(self, visitors):
            self.visitors = visitors

        def __getattr__(self, name):
            """
            Dynamically handle visit_* method calls.

            Calls the same method on all child visitors in sequence.

            Args:
                name: Method name being called

            Returns:
                Callable that merges visitor results

            Raises:
                AttributeError: If not a visit_* method
            """
            if not name.startswith("visit"):
                raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

            def merged_visit_method(path: NodePath):
                skip_children = False

                for visitor in self.visitors:
                    if hasattr(visitor, name):
                        result = getattr(visitor, name)(path)

                        # BREAK stops everything
                        if result is BREAK:
                            return BREAK

                        # False marks to skip children
                        if result is False:
                            skip_children = True

                return False if skip_children else None

            return merged_visit_method

    return MergedVisitor(visitors)
