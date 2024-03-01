import ast
import hashlib
import re
from _ast import Global
from dataclasses import dataclass
from typing import Any

from .errors import (AsteriskImportError, GlobalError, InternalCompilerError,
                     ReservedIdentifierError)
from .options import CompilerOptions

python_invalid_character_re = re.compile(r"[^A-Za-z0-9_]")


def purify_identifier(name: str):
    return python_invalid_character_re.sub("", name)


_ident_index = -1


@dataclass
class FoundImport:
    module: str
    module_alias: str | None
    context_path: str
    imports: list[ast.alias] | None
    is_asterisk_import: bool
    is_module_import: bool

    def generate_unique_identifier(self, minified: bool, hash_length: int):
        if minified:
            # we use global state here because local parameters don't get
            # optimized by python-minifier, so we have to "minify" it ourselves
            global _ident_index
            _ident_index += 1
            return f"__{_ident_index}"
        else:
            id = hashlib.md5(f"{self.module}{self.module_alias}{self.context_path}".encode(
            ), usedforsecurity=False).hexdigest()[:hash_length]
            return f"__generated_import_{purify_identifier(self.module)}_{id}__"


class ImportVisitor(ast.NodeVisitor):
    imports: list[FoundImport]
    context_path: str

    def __init__(self, context_path: str) -> None:
        super().__init__()
        self.imports = []
        self.context_path = context_path

    def visit_Import(self, node: ast.Import) -> Any:
        for alias in node.names:
            self.imports.append(
                FoundImport(
                    module=alias.name,
                    module_alias=alias.asname,
                    is_module_import=True,
                    is_asterisk_import=False,
                    imports=None,
                    context_path=self.context_path))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        if node.module is None:
            raise InternalCompilerError("ImportFrom module is None")
        self.imports.append(
            FoundImport(
                module=node.module,
                module_alias=None,
                imports=node.names,
                is_asterisk_import=False,
                is_module_import=False,
                context_path=self.context_path))

    @classmethod
    def find_imports(cls, module: ast.Module, context_path: str):
        visitor = cls(context_path)
        visitor.visit(module)
        return visitor.imports


class ModuleTransformer(ast.NodeTransformer):
    imports: list[FoundImport]
    argument_import_names: list[str]
    name: str
    path: str
    options: CompilerOptions

    def __init__(self, path: str, imports: list[FoundImport], argument_import_names: list[str], name: str, options: CompilerOptions) -> None:
        self.imports = imports
        self.argument_import_names = argument_import_names
        self.name = name
        self.options = options
        self.path = path
        super().__init__()

    def _resolve_module_argument_identifier(self, module_name: str) -> str:
        for i, item in enumerate(self.imports):
            if item.module == module_name:
                return self.argument_import_names[i]
        raise InternalCompilerError(
            f"can't find '{module_name}' import in mapping")

    def visit_Import(self, node: ast.Import) -> Any:
        output: list[ast.Assign | ast.Import] = []
        for alias in node.names:
            if alias.name in self.options.ignore_imports:
                # don't process, just ignore
                output.append(ast.Import(names=[alias]))
            elif alias.name in self.options.remove_imports:
                # don't emit removed imports
                pass
            else:
                resolved_argument = self._resolve_module_argument_identifier(
                    alias.name)
                output.append(ast.Assign(
                    targets=[
                        ast.Name(
                            id=alias.asname if alias.asname is not None else alias.name,
                            ctx=ast.Store()
                        )
                    ],
                    value=ast.Name(id=resolved_argument, ctx=ast.Load())
                ))
        return [self.generic_visit(item) for item in output]

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        module = node.module
        if node.module in self.options.ignore_imports:
            # don't process
            return node
        elif node.module in self.options.remove_imports:
            # don't emit anything
            return None
        if module is None:
            raise InternalCompilerError(
                f"ImportFrom module is None")
        resolved_argument = self._resolve_module_argument_identifier(
            module)
        output: list[ast.Assign | ast.Import] = []
        for alias in node.names:
            if alias.name == "*":
                raise AsteriskImportError(
                    module=module,
                    path=self.path,
                    lineno=node.lineno,
                    colno=node.col_offset
                )
            output.append(ast.Assign(
                targets=[
                    ast.Name(
                        id=alias.asname if alias.asname is not None else alias.name,
                        ctx=ast.Store()
                    )
                ],
                value=ast.Attribute(
                    value=ast.Name(
                        id=resolved_argument,
                        ctx=ast.Load(),
                    ),
                    attr=alias.name,
                    ctx=ast.Load()
                )
            ))
        return [self.generic_visit(item) for item in output]

    def visit_Name(self, node: ast.Name) -> Any:
        if isinstance(node.ctx, ast.Load):
            if node.id == "__name__":
                return ast.Constant(value=self.name)
        # if it looks like it starts with a reserved name and has a line number
        # (generated ones don't), then raise
        if hasattr(node, "lineno") and node.id.startswith("__generated_"):
            raise ReservedIdentifierError(
                node.id, self.path, node.lineno, node.col_offset)
        # let other methods run their visitors
        return self.generic_visit(node)

    def visit_Global(self, node: Global) -> Any:
        raise GlobalError(self.path, node.lineno, node.col_offset)
