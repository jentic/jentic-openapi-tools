"""NodePath context for traversal."""

from dataclasses import dataclass
from typing import Any, Literal

from jsonpointer import JsonPointer

from .introspection import get_yaml_field_name


__all__ = ["NodePath"]


@dataclass(frozen=True, slots=True)
class NodePath:
    """
    Context for a node during traversal.

    Provides access to node, parent, ancestry, and path formatting.
    Supports Babel-style sub-traversal via traverse() method.
    """

    node: Any  # Current datamodel object
    parent_path: "NodePath | None"  # Reference to parent's NodePath (chain)
    parent_field: str | None  # Field name in parent
    parent_key: str | int | None  # Key if parent field is list/dict

    @property
    def parent(self) -> Any | None:
        """Get parent node. Computed from parent_path for convenience."""
        return self.parent_path.node if self.parent_path else None

    @property
    def ancestors(self) -> tuple[Any, ...]:
        """Get ancestor nodes from root to parent. Computed for convenience."""
        result = []
        current = self.parent_path
        while current is not None:
            result.append(current.node)
            current = current.parent_path
        result.reverse()  # Root first
        return tuple(result)

    def create_child(
        self, node: Any, parent_field: str | None, parent_key: str | int | None
    ) -> "NodePath":
        """
        Create a child NodePath from this path.

        Helper for creating child paths during traversal.

        Args:
            node: Child node
            parent_field: Field name in current node (None for dict items to avoid duplicates)
            parent_key: Key if field is list/dict

        Returns:
            New NodePath for the child
        """
        return NodePath(
            node=node,
            parent_path=self,
            parent_field=parent_field,
            parent_key=parent_key,
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
        parts = self.to_parts()

        # Root node
        if not parts:
            return "$" if path_format == "jsonpath" else ""

        if path_format == "jsonpath":
            # RFC 9535 Normalized JSONPath: $['field'][index]['key']
            result = ["$"]
            for part in parts:
                if isinstance(part, int):
                    # Array index: $[0]
                    result.append(f"[{part}]")
                else:
                    # Member name: $['field']
                    # Escape single quotes in the string
                    escaped = str(part).replace("'", "\\'")
                    result.append(f"['{escaped}']")
            return "".join(result)

        # RFC 6901 JSON Pointer
        return JsonPointer.from_parts(parts).path

    def to_parts(self) -> list[str | int]:
        """
        Return path as a list of path parts (field names, keys, and array indices).

        Can be used with JsonPointer.from_parts() for conversion.

        Returns:
            List of path parts from root to this node.
            Empty list for root node.

        Examples:
            [] (root)
            ["info"]
            ["paths", "/users", "get"]
            ["paths", "/users", "get", "parameters", 0]
            ["components", "schemas", "User", "properties", "name"]
        """
        if self.parent_path is None:
            return []

        parts: list[str | int] = []
        current = self
        while current.parent_path is not None:
            if current.parent_key is not None:
                parts.append(current.parent_key)
            if current.parent_field:
                parent_class = type(current.parent_path.node)
                yaml_name = get_yaml_field_name(parent_class, current.parent_field)
                parts.append(yaml_name)
            current = current.parent_path

        parts.reverse()
        return parts

    def get_root(self) -> Any:
        """
        Get the root node of the tree.

        Returns:
            Root datamodel object
        """
        current = self
        while current.parent_path is not None:
            current = current.parent_path
        return current.node
