class SemanticError(Exception):
    """Exception for semantic errors."""
    def __init__(self, message: str, node=None):
        self.message = message
        self.node = node
        super().__init__(message)
    
    def format_error(self) -> str:
        """
        Format error message with position and AST node info.
        
        Returns:
            String in format "Semantic error: line:col [ClassName#id]: message" or "Semantic error: message"
        """
        pos = ""
        node_info = ""
        
        if self.node is not None:
            # Add AST node class and ID
            node_class = self.node.__class__.__name__
            node_id = getattr(self.node, 'id', None)
            if node_id is not None:
                node_info = f"[{node_class}#{node_id}]"
            else:
                node_info = f"[{node_class}]"
            
            # Add position if span is available
            if hasattr(self.node, 'span') and self.node.span is not None:
                pos = f"{self.node.span.start.line}:{self.node.span.start.col}: "
                return f"Semantic error: {pos}{node_info}: {self.message}"
            else:
                return f"Semantic error: {node_info}: {self.message}"
        
        return f"Semantic error: {self.message}"