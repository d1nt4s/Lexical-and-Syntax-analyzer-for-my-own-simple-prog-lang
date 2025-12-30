class SemanticError(Exception):
    def __init__(self, message: str, node=None):
        self.message = message
        self.node = node
        super().__init__(message)