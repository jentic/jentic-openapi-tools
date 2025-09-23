from lsprotocol.types import Diagnostic


class ValidationResult:
    def __init__(self, diagnostics: list[Diagnostic]):
        self.diagnostics = diagnostics
        self.valid = True
        if diagnostics:
            self.valid = False
