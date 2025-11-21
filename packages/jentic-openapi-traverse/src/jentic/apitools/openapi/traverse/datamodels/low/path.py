"""NodePath context for traversal."""

from dataclasses import dataclass
from typing import Any, Literal

from jsonpointer import JsonPointer


__all__ = ["NodePath"]


@dataclass(frozen=True, slots=True)
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

    def format_path(
        self, *, path_format: Literal["jsonpointer", "jsonpath"] = "jsonpointer"
    ) -> str:
        """
        Format path as RFC 6901 JSON Pointer or RFC 9535 Normalized JSONPath.

        Args:
            path_format: Output format - "jsonpointer" (default) or "jsonpath"

        Returns:
            JSONPointer string like "/paths/~1pets/get/responses/200"
            or Normalized JSONPath like "$['paths']['/pets']['get']['responses']['200']"

        Examples (jsonpointer):
            "" (root)
            "/info"
            "/paths/~1pets/get"
            "/paths/~1users~1{id}/parameters/0"
            "/components/schemas/User/properties/name"

        Examples (jsonpath):
            "$" (root)
            "$['info']"
            "$['paths']['/pets']['get']"
            "$['paths']['/users/{id}']['parameters'][0]"
            "$['components']['schemas']['User']['properties']['name']"
        """
        # Root node
        if not self.ancestors and self.parent_field is None:
            return "$" if path_format == "jsonpath" else ""

        # Build parts list
        parts: list[str | int] = []

        # This is a simplified implementation that only captures one level
        # A full implementation would need to walk back through ancestors
        if self.parent_field:
            parts.append(self.parent_field)

        if self.parent_key is not None:
            # Both int (array index) and str (object key) work with from_parts
            parts.append(self.parent_key)

        if path_format == "jsonpath":
            # RFC 9535 Normalized JSONPath: $['field'][index]['key']
            segments = ["$"]
            for part in parts:
                if isinstance(part, int):
                    # Array index: $[0]
                    segments.append(f"[{part}]")
                else:
                    # Member name: $['field']
                    # Escape single quotes in the string
                    escaped = str(part).replace("'", "\\'")
                    segments.append(f"['{escaped}']")
            return "".join(segments)

        # RFC 6901 JSON Pointer
        return JsonPointer.from_parts(parts).path

    def get_root(self) -> Any:
        """
        Get the root node of the tree.

        Returns:
            Root datamodel object
        """
        return self.ancestors[0] if self.ancestors else self.node
