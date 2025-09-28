from lsprotocol.types import Diagnostic


class JenticDiagnostic(Diagnostic):
    def __init__(self, **data):
        super().__init__(**data)
        if not hasattr(self, "data") or self.data is None:
            self.data = {}
        if "fixable" not in self.data:
            self.data["fixable"] = True
        if "path" not in self.data:
            self.data["path"] = []
        if "target" not in self.data:
            self.data["target"] = ""

    def set_fixable(self, fixable: bool = True):
        if not hasattr(self, "data") or self.data is None:
            self.data = {}
        self.data["fixable"] = fixable

    def set_path(self, path: list[str | int] | None):
        if path is None:
            return
        if not hasattr(self, "data") or self.data is None:
            self.data = {}
        self.data["path"] = path

    def set_target(self, target: str | None):
        if target is None:
            return
        if not hasattr(self, "data") or self.data is None:
            self.data = {}
        self.data["target"] = target

    def set_data_field(self, key: str, value: str | None):
        if value is None:
            return
        if not hasattr(self, "data") or self.data is None:
            self.data = {}
        self.data[key] = value


class ValidationResult:
    def __init__(self, diagnostics: list[JenticDiagnostic]):
        self.diagnostics = diagnostics
        self.valid = True
        if diagnostics:
            self.valid = False
