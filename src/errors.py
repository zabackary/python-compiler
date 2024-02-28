class CompilerError(Exception):
    pass


class TransformError(CompilerError):
    pass


class AsteriskImportError(TransformError):
    pass


class GlobalError(TransformError):
    pass


class ReservedIdentifierError(TransformError):
    pass


class CircularDependencyError(CompilerError):
    pass


class InternalCompilerError(CompilerError):
    pass


class NestedModuleRecursionError(CompilerError):
    pass
