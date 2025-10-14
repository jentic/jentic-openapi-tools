from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from dataclasses import dataclass
from typing import Iterator, TypeAlias, Union


# Path segment can be a dict key (str) or list index (int)
PathSeg: TypeAlias = str | int

# Path is an immutable tuple of segments from root to a node
JSONPath: TypeAlias = tuple[PathSeg, ...]

# Any JSON-like value
JSONValue: TypeAlias = Union[
    None,
    bool,
    int,
    float,
    str,
    Mapping[str, "JSONValue"],
    Sequence["JSONValue"],
]

# Container types that can be traversed
JSONContainer: TypeAlias = MutableMapping[str, JSONValue] | MutableSequence[JSONValue]


@dataclass(frozen=True, slots=True)
class TraversalNode:
    """
    Represents a node encountered during traversal.

    Attributes:
        path: Path from root to the parent container
        parent: The parent container (dict or list)
        segment: The key (for dicts) or index (for lists) within parent
        value: The actual value at parent[segment]
        ancestors: Ordered tuple of values from root down to (but not including) parent
    """

    path: JSONPath
    parent: JSONContainer
    segment: PathSeg
    value: JSONValue
    ancestors: tuple[JSONValue, ...]

    @property
    def full_path(self) -> JSONPath:
        """Return the complete path from root to this value."""
        return self.path + (self.segment,)

    def format_path(self, separator: str = ".") -> str:
        """Format the full path as a human-readable string."""
        parts = []
        for seg in self.full_path:
            if isinstance(seg, int):
                parts.append(f"[{seg}]")
            else:
                if parts:
                    parts.append(f"{separator}{seg}")
                else:
                    parts.append(seg)
        return "".join(parts)


def traverse(root: JSONValue) -> Iterator[TraversalNode]:
    """
    Depth-first traversal of nested data structures.

    Yields a TraversalNode for each item in the tree:
    - For dicts: one node per key-value pair
    - For lists: one node per index-item pair
    - Scalars are not yielded (but accessible via parent nodes)

    Args:
        root: The data structure to traverse (dict, list, or scalar)

    Yields:
        TraversalNode: Dataclass with path, parent, segment, value, and ancestors

    Example:
        >>> data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        >>> for node in traverse(data):
        ...     print(f"{node.format_path()}: {node.value} (depth: {len(node.ancestors)})")
        users: [{'name': 'Alice'}, {'name': 'Bob'}] (depth: 0)
        users[0]: {'name': 'Alice'} (depth: 1)
        users[0].name: Alice (depth: 2)
        users[1]: {'name': 'Bob'} (depth: 1)
        users[1].name: Bob (depth: 2)
    """
    stack: list[tuple[JSONPath, JSONValue, tuple[JSONValue, ...]]] = [((), root, ())]
    while stack:
        path, current, ancestors = stack.pop()
        if isinstance(current, Mapping):
            for k, v in current.items():
                yield TraversalNode(path, current, k, v, ancestors)  # type: ignore[arg-type]
                # push child with updated ancestors
                stack.append((path + (k,), v, ancestors + (current,)))
        elif isinstance(current, Sequence) and not isinstance(current, str):
            for i, v in enumerate(current):
                yield TraversalNode(path, current, i, v, ancestors)  # type: ignore[arg-type]
                stack.append((path + (i,), v, ancestors + (current,)))
