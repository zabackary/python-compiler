import ast
import hashlib
import os
import sys
from importlib import util as import_utils

from .exporthelper import EXPORT_HELPER_NAME
from .options import ModuleMergerOptions
from .transformer import (Import, ImportVisitor, ModuleTransformer,
                          TransformError, purify_identifier)

BUILTIN_EXPORT_INTERNAL_NAME = "exports_builtin"
CLASS_EXPORT_CLASS_NAME = "exports"


class ModuleUniqueIdentifierGenerator:
    unique_module_name: str
    id: str
    minified: bool

    def __init__(self, module_name: str, module_path: str, minified: bool, hash_length: int) -> None:
        self.id = hashlib.md5(module_path.encode(),
                              usedforsecurity=False).hexdigest()[:hash_length]
        self.minified = minified
        if self.minified:
            self.unique_module_name = self.id
        else:
            self.unique_module_name = f"{purify_identifier(module_name)}_{self.id}"

    def get_factory(self):
        if self.minified:
            return f"f{self.unique_module_name}"
        else:
            return f"__generated_factory_{self.unique_module_name}__"

    def get_evaluated_factory(self):
        if self.minified:
            return f"m{self.unique_module_name}"
        else:
            return f"__generated_module_{self.unique_module_name}__"

    def get_internal_name(self, name: str):
        if self.minified:
            return f"{name}{self.unique_module_name}"
        else:
            return f"__generated_{name}_{self.unique_module_name}__"

    def get_export_property_name(self, name: str):
        return self.get_internal_name(f"export_{name}")


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
            self.name, self.path, options.short_generated_names, options.hash_length)
        if self.module is not None:
            for item in ImportVisitor.find_imports(self.module, self.path):
                if item.module not in self.options.ignore_imports and item.module not in self.options.remove_imports:
                    self.imports.append(item)

    def _globals_names(self, module: ast.Module) -> list[str]:
        names: list[str] = []
        for top_level_stmt in module.body:
            if isinstance(top_level_stmt, ast.FunctionDef):
                names.append(top_level_stmt.name)
            elif isinstance(top_level_stmt, ast.AsyncFunctionDef):
                names.append(top_level_stmt.name)
            elif isinstance(top_level_stmt, ast.ClassDef):
                names.append(top_level_stmt.name)
            elif isinstance(top_level_stmt, ast.Assign):
                for target in top_level_stmt.targets:
                    if isinstance(target, ast.Name):
                        names.append(target.id)
            elif isinstance(top_level_stmt, ast.AnnAssign):
                if isinstance(top_level_stmt.target, ast.Name):
                    names.append(top_level_stmt.target.id)
        return [name for name in names if not name.startswith("_")]

    def _globals_dict(self, module: ast.Module) -> ast.Dict:
        """
        generates an ast.Dict mapping top-level module export name strings to
        the Name of the export.
        """
        names = self._globals_names(module)
        return ast.Dict(
            keys=map(lambda a: ast.Constant(value=a), names),
            values=map(lambda a: ast.Name(id=a, ctx=ast.Load()), names)
        )

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
                                asname=self.name_generator.get_internal_name(
                                    BUILTIN_EXPORT_INTERNAL_NAME)
                            )
                        ]
                    ),
                    ast.Return(
                        value=ast.Name(
                            id=self.name_generator.get_internal_name(
                                BUILTIN_EXPORT_INTERNAL_NAME),
                            ctx=ast.Load()
                        )
                    )
                ],
                decorator_list=[]
            )
        else:
            argument_import_names: list[str] = []
            for item in self.imports:
                argument_import_names.append(item.generate_unique_identifier(
                    self.options.short_generated_names, self.options.hash_length))

            try:
                transformed_module: ast.Module = ModuleTransformer(
                    self.imports,
                    argument_import_names,
                    self.name, self.options).visit(self.module)
            except Exception as err:
                raise TransformError(
                    f"failed to transform module at {self.path}: {str(err)}")

            body: list[ast.AST] = []
            body.extend(transformed_module.body)
            if self.options.export_dictionary_mode == "class" or self.options.export_dictionary_mode == "class_instance":
                globals_names = self._globals_names(transformed_module)
                body.extend([
                    ast.Assign(
                            targets=[
                                ast.Name(id=self.name_generator.get_export_property_name(
                                    name), ctx=ast.Store())
                            ],
                            value=ast.Name(id=name, ctx=ast.Load())
                            ) for name in globals_names
                ])
                body.append(ast.ClassDef(
                    name=self.name_generator.get_internal_name(
                        CLASS_EXPORT_CLASS_NAME),
                    bases=[],
                    keywords=[],
                    body=(
                        [ast.Assign(
                            targets=[
                                ast.Name(id=name, ctx=ast.Store())
                            ],
                            value=ast.Name(id=self.name_generator.get_export_property_name(
                                name), ctx=ast.Load())
                        ) for name in globals_names] if self.options.export_dictionary_mode == "class"
                        else [
                            ast.FunctionDef(
                                name="__init__",
                                args=ast.arguments(
                                    posonlyargs=[],
                                    args=[ast.arg(
                                        arg="self"
                                    )],
                                    kwonlyargs=[],
                                    kw_defaults=[],
                                    defaults=[]
                                ),
                                body=[ast.Assign(
                                    targets=[
                                        ast.Attribute(
                                            value=ast.Name(
                                                id="self", ctx=ast.Store()),
                                            attr=name,
                                            ctx=ast.Store()
                                        )
                                    ],
                                    value=ast.Name(id=self.name_generator.get_export_property_name(
                                        name), ctx=ast.Load())
                                ) for name in globals_names],
                                decorator_list=[],
                                type_params=[]
                            )
                        ]
                    ),
                    decorator_list=[],
                    type_params=[]
                ))
                body.append(ast.Return(
                    value=(ast.Name(
                        id=self.name_generator.get_internal_name(CLASS_EXPORT_CLASS_NAME), ctx=ast.Load()))
                    if self.options.export_dictionary_mode == "class"
                    else ast.Call(
                        func=ast.Name(id=self.name_generator.get_internal_name(
                            CLASS_EXPORT_CLASS_NAME), ctx=ast.Load()),
                        args=[],
                        keywords=[]
                    )
                ))
            else:
                body.append(ast.Return(
                    value=ast.Call(
                        func=ast.Name(id=EXPORT_HELPER_NAME, ctx=ast.Load()),
                        args=[
                            ast.Call(
                                func=ast.Name(id="locals", ctx=ast.Load()),
                                args=[],
                                keywords=[]
                            ) if self.options.export_names_mode == "locals"
                            else self._globals_dict(transformed_module)
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
    elif (spec.origin == "built-in"
          or module in options.ignore_imports
          or module in options.remove_imports
          or module in sys.stdlib_module_names):
        return ProcessedModule(None, "built-in", module, options)
    else:
        with open(spec.origin, "r") as file:
            return ProcessedModule(file.read(), spec.origin, module, options)
