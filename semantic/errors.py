class SemanticError(Exception):
    def __init__(self, message: str, node=None):
        super().__init__(message)
        self.node = node