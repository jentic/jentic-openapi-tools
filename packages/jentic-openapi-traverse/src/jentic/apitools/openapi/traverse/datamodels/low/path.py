"""NodePath context for traversal."""

from dataclasses import dataclass
from typing import Any


__all__ = ["NodePath"]


@dataclass(frozen=True)
class NodePath:
    """
    Context for a node during traversal.

    Provides access to node, parent, ancestry, and path formatting.
    Supports Babel-style sub-traversal via traverse() method.
    """

    node: Any  # Current datamodel object
    parent: Any | None  # Parent datamodel object
    parent_field: str | None  # Field name in parent
    parent_key: str | int | None  # Key if parent field is list/dict
    ancestors: tuple[Any, ...]  # Tuple of ancestor nodes (root first)

    def create_child(
        self, node: Any, parent_field: str, parent_key: str | int | None
    ) -> "NodePath":
        """
        Create a child NodePath from this path.

        Helper for creating child paths during traversal.

        Args:
            node: Child node
            parent_field: Field name in current node
            parent_key: Key if field is list/dict

        Returns:
            New NodePath for the child
        """
        return NodePath(
            node=node,
            parent=self.node,
            parent_field=parent_field,
            parent_key=parent_key,
            ancestors=self.ancestors + (self.node,),
        )

    def traverse(self, visitor) -> None:
        """
        Traverse from this node as root (Babel pattern).

        Allows convenient sub-traversal with a different visitor.

        Args:
            visitor: Visitor object with visit_* methods

        Example:
            class PathItemVisitor:
                def visit_PathItem(self, path):
                    # Only traverse GET operations
                    if path.node.get:
                        operation_visitor = OperationOnlyVisitor()
                        get_path = path.create_child(
                            node=path.node.get.value,
                            parent_field="get",
                            parent_key=None
                        )
                        get_path.traverse(operation_visitor)
                    return False  # Skip automatic traversal
        """
        from .traversal import traverse

        traverse(self.node, visitor)

    def format_path(self) -> str:
        """
        Format path as JSONPath-like string.

        Returns:
            JSONPath string like "$.paths./pets.get.responses.200"

        Examples:
            $.info
            $.paths./pets.get
            $.paths./users/{id}.parameters[0]
            $.components.schemas.User.properties.name
        """
        if not self.ancestors and self.parent_field is None:
            return "$"

        parts = ["$"]

        # Build path by walking back through parent chain
        # This is a simplified implementation
        # A full implementation would need to track field names through the tree

        if self.parent_field:
            parts.append(self.parent_field)

        if self.parent_key is not None:
            if isinstance(self.parent_key, int):
                # Array index
                parts[-1] = f"{parts[-1]}[{self.parent_key}]"
            else:
                # Object key (like path "/pets" or schema "User")
                parts.append(str(self.parent_key))

        return ".".join(parts)

    def get_root(self) -> Any:
        """
        Get the root node of the tree.

        Returns:
            Root datamodel object
        """
        return self.ancestors[0] if self.ancestors else self.node
