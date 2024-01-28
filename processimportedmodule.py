import ast
import hashlib
import os
import sys
from importlib import util as import_utils

from .exporthelper import EXPORT_HELPER_NAME
from .module_import_finder import (Import, ImportTransformer, ImportVisitor,
                                   purify_identifier)
from .options import ModuleMergerOptions


class ModuleUniqueIdentifierGenerator:
    module_name: str
    unique_module_name: str
    id: str

    def __init__(self, module_name: str, module_path: str) -> None:
        self.module_name = module_name
        self.id = hashlib.md5(module_path.encode(),
                              usedforsecurity=False).hexdigest()
        self.unique_module_name = f"{purify_identifier(self.module_name)}_{self.id}"

    def get_factory(self):
        return f"__generated_factory_{self.unique_module_name}__"

    def get_evaluated_factory(self):
        return f"__generated_module_{self.unique_module_name}__"

    def get_internal_name(self):
        return f"__generated_internal_{self.unique_module_name}__"


class ImportData:
    path: str
    resolved_name: str

    def __init__(self, path: str, resolved_name: str) -> None:
        pass


class ProcessedModule:
    name: str
    module: ast.Module | None
    imports: list[Import]
    path: str
    name_generator: ModuleUniqueIdentifierGenerator
    options: ModuleMergerOptions

    def __init__(self, source: str | None, path: str, imported_name: str, options: ModuleMergerOptions) -> None:
        self.options = options
        if path == "built-in":
            self.name = f"built-in:{imported_name}"
        elif imported_name == "__main__":
            self.name = "__main__"
        else:
            self.name = os.path.splitext(os.path.basename(path))[0]
        self.path = f"built-in:{imported_name}" if path == "built-in" else path
        self.module = ast.parse(
            source, self.name) if source is not None else None
        self.imports = []
        self.name_generator = ModuleUniqueIdentifierGenerator(
            self.name, self.path)
        if self.module is not None:
            for item in ImportVisitor.find_imports(self.module, self.path):
                if item.module not in self.options.ignore_imports:
                    self.imports.append(item)

    def generate_factory_ast(self) -> ast.FunctionDef | ast.Import:
        if self.module is None:
            return ast.FunctionDef(
                name=self.name_generator.get_factory(),
                args=ast.arguments(
                    posonlyargs=[],
                    args=[],
                    defaults=[],
                    kwonlyargs=[]
                ),
                body=[
                    ast.Import(
                        names=[
                            ast.alias(
                                name=self.name.removeprefix(
                                    "built-in:"),
                                asname=self.name_generator.get_internal_name()
                            )
                        ]
                    ),
                    ast.Return(
                        value=ast.Name(
                            id=self.name_generator.get_internal_name(),
                            ctx=ast.Load()
                        )
                    )
                ],
                decorator_list=[]
            )
        else:
            argument_import_names: list[str] = []
            for item in self.imports:
                argument_import_names.append(item.generate_unique_identifier())

            transformed_module = ImportTransformer(
                self.imports,
                argument_import_names,
                self.name, self.options).visit(self.module)

            body: list[ast.AST] = []
            body.extend(transformed_module.body)
            body.append(ast.Return(
                value=ast.Call(
                    func=ast.Name(id=EXPORT_HELPER_NAME, ctx=ast.Load()),
                    args=[
                        ast.Call(
                            func=ast.Name(id="locals", ctx=ast.Load()),
                            args=[],
                            keywords=[]
                        )
                    ],
                    keywords=[]
                )
            ))

            return ast.FunctionDef(
                name=self.name_generator.get_factory(),
                args=ast.arguments(
                    posonlyargs=[],
                    args=list(map(lambda item: ast.arg(
                        arg=item), argument_import_names)),
                    defaults=[],
                    kwonlyargs=[]
                ),
                body=body,
                decorator_list=[]
            )

    def generate_evaluated_factory_ast(self, argument_imports: list[str]) -> ast.Assign:
        return ast.Assign(
            targets=[
                ast.Name(
                    id=self.name_generator.get_evaluated_factory(), ctx=ast.Store())
            ],
            value=ast.Call(
                func=ast.Name(
                    id=self.name_generator.get_factory(),
                    ctx=ast.Load()
                ),
                args=list(map(
                    lambda a: ast.Name(
                        id=a,
                        ctx=ast.Load()
                    ),
                    argument_imports
                )),
                keywords=[]
            )
        )


def process_imported_module(module: str, context_path: str, options: ModuleMergerOptions):
    old_path = sys.path.copy()
    # this assumes that the directory of this current file is always the first
    # search path
    sys.path[0] = os.path.dirname(context_path)
    spec = import_utils.find_spec(module)
    sys.path = old_path
    if spec is None or spec.origin is None:
        raise ImportError(f"failed to resolve import {module}")
    elif spec.origin == "built-in" or module in options.ignore_imports or module in sys.stdlib_module_names:
        return ProcessedModule(None, "built-in", module, options)
    else:
        with open(spec.origin, "r") as file:
            return ProcessedModule(file.read(), spec.origin, module, options)
