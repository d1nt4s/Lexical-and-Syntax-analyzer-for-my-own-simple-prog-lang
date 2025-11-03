from .ast import ASTNode
from typing import Any

class Parser:
    def parse(self, tokens: Any) -> ASTNode:
        return ASTNode("Program", [])