import sys


class _terminal_colors:
    ISATTY = sys.stdout.isatty()

    if ISATTY:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
    else:
        HEADER = ''
        OKBLUE = ''
        OKCYAN = ''
        OKGREEN = ''
        WARNING = ''
        FAIL = ''
        ENDC = ''
        BOLD = ''
        UNDERLINE = ''


class CompilerError(Exception):
    errcode: str


class TransformError(CompilerError):
    path: str
    lineno: int
    colno: int

    errcode = "transform"


class AsteriskImportError(TransformError):
    module: str
    path: str
    lineno: int
    colno: int

    errcode = "asterisk-import"

    def __init__(self, module: str, path: str, lineno: int, colno: int) -> None:
        self.module = module
        self.path = path
        self.lineno = lineno
        self.colno = colno

    def __str__(self) -> str:
        return f"unsupported: asterisk glob imports aren't supported by python-compiler since the contents of modules aren't known at compile-time\n  {_terminal_colors.OKBLUE}{_terminal_colors.BOLD}note:{_terminal_colors.ENDC} the module imported from was {_terminal_colors.OKCYAN}{self.module}{_terminal_colors.ENDC}\n  at {self.path} {self.lineno}:{self.colno}"


class GlobalError(TransformError):
    path: str
    lineno: int
    colno: int

    errcode = "unexpected-global"

    def __init__(self, path: str, lineno: int, colno: int) -> None:
        self.path = path
        self.lineno = lineno
        self.colno = colno

    def __str__(self) -> str:
        return f"unsupported: global statements aren't supported by python-compiler\n  {_terminal_colors.OKGREEN}{_terminal_colors.BOLD}help:{_terminal_colors.ENDC} mutating global variables are bad practice and disallowed in some thread-safe languages. try refactoring your code to pass the variable as an argument instead.\n  at {self.path} {self.lineno}:{self.colno}"


class ReservedIdentifierError(TransformError):
    ident: str
    path: str
    lineno: int
    colno: int

    errcode = "unexpected-reserved-ident"

    def __init__(self, ident: str, path: str, lineno: int, colno: int) -> None:
        self.ident = ident
        self.path = path
        self.lineno = lineno
        self.colno = colno

    def __str__(self) -> str:
        return f"identifier reserved by python-compiler used\n  {_terminal_colors.OKBLUE}{_terminal_colors.BOLD}note:{_terminal_colors.ENDC} the reserved identifier was named {_terminal_colors.OKCYAN}{self.ident}{_terminal_colors.ENDC}\n  at {self.path} {self.lineno}:{self.colno}"


class ImportResolutionError(CompilerError):
    path: str
    module: str
    os_error_read_path: str | None

    errcode = "import-resolution"

    def __init__(self, path: str, module: str, os_error_read_path: str | None = None) -> None:
        self.path = path
        self.module = module
        self.os_error_read_path = os_error_read_path

    def __str__(self) -> str:
        if self.os_error_read_path is not None:
            return f"failed to read source for module {_terminal_colors.OKCYAN}{self.module}{_terminal_colors.ENDC} from the file {_terminal_colors.OKCYAN}{self.os_error_read_path}{_terminal_colors.ENDC}\n  {_terminal_colors.OKBLUE}{_terminal_colors.BOLD}note:{_terminal_colors.ENDC} this was caused by an OsError when reading the file\n  in {self.path}"
        else:
            return f"failed to resolve import {_terminal_colors.OKCYAN}{self.module}{_terminal_colors.ENDC}\n  in {self.path}"


class CircularDependencyError(CompilerError):
    modules: list[str]

    errcode = "circular-deps"

    def __init__(self, modules: list[str]) -> None:
        self.modules = modules

    def __str__(self) -> str:
        return f"circular dependencies detected\n  {_terminal_colors.OKBLUE}{_terminal_colors.BOLD}note:{_terminal_colors.ENDC} normally this would fail at runtime\n  {_terminal_colors.OKBLUE}{_terminal_colors.BOLD}note:{_terminal_colors.ENDC} modules which may be involved: {_terminal_colors.OKCYAN}{f'{_terminal_colors.ENDC}, {_terminal_colors.OKCYAN}'.join(self.modules)}{_terminal_colors.ENDC}"


class InternalCompilerError(CompilerError):
    message: str | None

    errcode = "internal"

    def __init__(self, message: str | None = None) -> None:
        self.message = message

    def __str__(self) -> str:
        return f"{_terminal_colors.BOLD}internal compiler error:{_terminal_colors.ENDC} {self.message if self.message is not None else 'something went wrong'}\n  note: this is a bug. if you wouldn't mind, please report it at {_terminal_colors.UNDERLINE}https://github.com/zabackary/python-compiler/issues{_terminal_colors.ENDC}\n  {_terminal_colors.OKBLUE}{_terminal_colors.BOLD}note:{_terminal_colors.ENDC} this is a logical precondition invalidation, not a crash"


class NestedModuleRecursionError(CompilerError):
    errcode = "recursion"

    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return f"excessive amount of nested modules\n  {_terminal_colors.OKGREEN}{_terminal_colors.BOLD}help:{_terminal_colors.ENDC} this means your project is too big for python-compiler to handle\n  {_terminal_colors.OKBLUE}{_terminal_colors.BOLD}note:{_terminal_colors.ENDC} this is caused by a RecursionError\n  {_terminal_colors.OKGREEN}{_terminal_colors.BOLD}help:{_terminal_colors.ENDC} try calling python-compiler as a library and using sys.setrecursionlimit to set a higher limit if needed"


class ModuleSyntaxError(TransformError):
    err: SyntaxError
    path: str

    errcode = "syntax"

    def __init__(self, path: str, err: SyntaxError) -> None:
        self.path = path
        self.err = err

    def __str__(self) -> str:
        return f"syntax error while parsing module\n  {_terminal_colors.OKBLUE}{_terminal_colors.BOLD}note:{_terminal_colors.ENDC} caused by {self.err.__class__.__name__}: {self.err.msg}\n  at {self.path} {self.err.lineno}:{self.err.offset}"
