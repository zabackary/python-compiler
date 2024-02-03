import ast
import hashlib
import re
from dataclasses import dataclass
from typing import Any

from .options import ModuleMergerOptions

python_invalid_character_re = re.compile(r"[^A-Za-z0-9_]")


def purify_identifier(name: str):
    return python_invalid_character_re.sub("", name)


@dataclass
class Import:
    module: str
    module_alias: str | None
    context_path: str
    imports: list[ast.alias] | None
    is_asterisk_import: bool
    is_module_import: bool

    def generate_unique_identifier(self):
        id = hashlib.md5(f"{self.module}{self.module_alias}{self.context_path}".encode(
        ), usedforsecurity=False).hexdigest()
        return f"__generated_import_{purify_identifier(self.module)}_{id}__"


class AsteriskImportError(Exception):
    pass


class TransformError(Exception):
    pass


class ImportVisitor(ast.NodeVisitor):
    imports: list[Import]
    context_path: str

    def __init__(self, context_path: str) -> None:
        super().__init__()
        self.imports = []
        self.context_path = context_path

    def visit_Import(self, node: ast.Import) -> Any:
        for alias in node.names:
            self.imports.append(
                Import(
                    module=alias.name,
                    module_alias=alias.asname,
                    is_module_import=True,
                    is_asterisk_import=False,
                    imports=None,
                    context_path=self.context_path))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        if node.module is None:
            raise TypeError("ImportFrom module is None")
        self.imports.append(
            Import(
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
    imports: list[Import]
    argument_import_names: list[str]
    name: str
    options: ModuleMergerOptions

    def __init__(self, imports: list[Import], argument_import_names: list[str], name: str, options: ModuleMergerOptions) -> None:
        self.imports = imports
        self.argument_import_names = argument_import_names
        self.name = name
        self.options = options
        super().__init__()

    def _resolve_module_argument_identifier(self, module_name: str) -> str:
        for i, item in enumerate(self.imports):
            if item.module == module_name:
                return self.argument_import_names[i]
        raise Exception(
            "failed to transform module: can't find import in mapping")

    def visit_Import(self, node: ast.Import) -> Any:
        output: list[ast.Assign | ast.Import] = []
        for alias in node.names:
            if alias.name in self.options.ignore_imports:
                # don't process, just ignore
                output.append(ast.Import(names=[alias]))
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
        return output

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        module = node.module
        if node.module in self.options.ignore_imports:
            return node
        if module is None:
            raise TransformError(
                f"failed to transform module {self.name}: ImportFrom module is None")
        resolved_argument = self._resolve_module_argument_identifier(
            module)
        output: list[ast.Assign | ast.Import] = []
        for alias in node.names:
            if alias.name == "*":
                raise AsteriskImportError(self.name)
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
        return output

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id == "__name__" and isinstance(node.ctx, ast.Load):
            return ast.Constant(value=self.name)
        return node
