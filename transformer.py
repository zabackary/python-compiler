import ast
import hashlib
import re
from _ast import Assign, Global, Module, Set
from dataclasses import dataclass
from typing import Any

from .options import ModuleMergerOptions

python_invalid_character_re = re.compile(r"[^A-Za-z0-9_]")


def purify_identifier(name: str):
    return python_invalid_character_re.sub("", name)


_ident_index = -1


@dataclass
class Import:
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


class AsteriskImportError(Exception):
    pass


class TransformError(Exception):
    pass


class AssignmentToConstantError(Exception):
    pass


class GlobalError(Exception):
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

    top_level_statements: list[ast.stmt]

    def __init__(self, imports: list[Import], argument_import_names: list[str], name: str, options: ModuleMergerOptions) -> None:
        self.imports = imports
        self.argument_import_names = argument_import_names
        self.name = name
        self.options = options
        self.top_level_statements = []
        super().__init__()

    def _resolve_module_argument_identifier(self, module_name: str) -> str:
        for i, item in enumerate(self.imports):
            if item.module == module_name:
                return self.argument_import_names[i]
        raise TransformError(
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
        return output

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        module = node.module
        if node.module in self.options.ignore_imports:
            # don't process
            return node
        elif node.module in self.options.remove_imports:
            # don't emit anything
            return None
        if module is None:
            raise TransformError(
                f"ImportFrom module is None on line {node.lineno}")
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
        if isinstance(node.ctx, ast.Load):
            if node.id == "__name__":
                return ast.Constant(value=self.name)
            elif node.id in self.options.compile_time_constants:
                return ast.Constant(value=self.options.compile_time_constants[node.id])
        return node

    def visit_Module(self, node: Module) -> Any:
        self.top_level_statements = node.body
        self.generic_visit(node)
        return node

    def visit_Assign(self, node: ast.Assign) -> Any:
        top_level = node in self.top_level_statements
        # raises errors if a constant is assigned to outside of the top-level
        # if it's top-level, silently deletes it
        for target in node.targets.copy():
            if (isinstance(target, ast.Name)
                and isinstance(target.ctx, ast.Store)
                    and target.id in self.options.compile_time_constants):
                if top_level:
                    node.targets.remove(target)
                else:
                    raise AssignmentToConstantError(
                        f"assignment to compile-time constant '{target.id}' on line {target.lineno} col {target.col_offset}")
        # delete the assignment if there's nothing it's assigning to
        if len(node.targets) == 0:
            return None
        return node

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:
        top_level = node in self.top_level_statements
        # raises errors if a constant is assigned to outside of the top-level
        # if it's top-level, silently deletes it
        if (isinstance(node.target, ast.Name)
            and isinstance(node.target.ctx, ast.Store)
                and node.target.id in self.options.compile_time_constants):
            if top_level:
                return None
            else:
                raise AssignmentToConstantError(
                    f"assignment to compile-time constant '{node.target.id}' on line {node.target.lineno} col {node.target.col_offset}")
        return node

    def visit_Global(self, node: Global) -> Any:
        raise GlobalError(
            f"global statements aren't supported on line {node.lineno} col {node.col_offset}")
