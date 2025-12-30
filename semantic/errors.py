class SemanticError(Exception):
    """Исключение для семантических ошибок."""
    def __init__(self, message: str, node=None):
        self.message = message
        self.node = node
        super().__init__(message)
    
    def format_error(self) -> str:
        """
        Форматирует сообщение об ошибке с позицией.
        
        Returns:
            Строка в формате "Semantic error: line:col: message" или "Semantic error: message"
        """
        pos = ""
        if self.node is not None and hasattr(self.node, 'span') and self.node.span is not None:
            pos = f"{self.node.span.start.line}:{self.node.span.start.col}: "
        return f"Semantic error: {pos}{self.message}"