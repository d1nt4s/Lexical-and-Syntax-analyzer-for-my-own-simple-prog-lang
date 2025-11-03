from dataclasses import dataclass, field
from typing import Any, List

_node_id_counter = 0

def _next_id() -> int:
    global _node_id_counter
    _node_id_counter += 1
    return _node_id_counter

@dataclass
class ASTNode:
    kind: str
    children: List["ASTNode"] = field(default_factory=list)
    value: Any | None = None
    id: int = field(default_factory=_next_id)

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "value": self.value,
            "children": [c.to_json() for c in self.children],
        }

    def pretty(self, indent: int = 0) -> str:
        pad = " " * indent
        lines = [f"{pad}{self.kind}#{self.id}" + (f" value={self.value!r}" if self.value is not None else "")]
        for ch in self.children:
            lines.append(ch.pretty(indent + 1))
        return "\n".join(lines)