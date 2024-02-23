import ast
from ast import Module
from typing import Any

from .plugin import Plugin


class AssignmentToConstantError(Exception):
    pass


class ConstantsTransformer(ast.NodeTransformer):
    top_level_statements: list[ast.stmt]
    constants: dict[str, str | bool | int | float]

    def __init__(self, constants: dict[str, str | bool | int | float]) -> None:
        self.constants = constants
        super().__init__()

    def visit_Name(self, node: ast.Name) -> Any:
        if isinstance(node.ctx, ast.Load):
            if node.id in self.constants:
                return ast.Constant(value=self.constants[node.id])
        return node

    def visit_Assign(self, node: ast.Assign) -> Any:
        top_level = node in self.top_level_statements
        # raises errors if a constant is assigned to outside of the top-level
        # if it's top-level, silently deletes it
        for target in node.targets.copy():
            if (isinstance(target, ast.Name)
                and isinstance(target.ctx, ast.Store)
                    and target.id in self.constants):
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
                and node.target.id in self.constants):
            if top_level:
                return None
            else:
                raise AssignmentToConstantError(
                    f"assignment to compile-time constant '{node.target.id}' on line {node.target.lineno} col {node.target.col_offset}")
        return node


class ConstantsPlugin(Plugin):
    constants: dict[str, str | bool | int | float]

    def __init__(self, constants: dict[str, str | bool | int | float]):
        self.constants = constants

    def hook_module(self, path: str, module: Module) -> Module:
        return ConstantsTransformer(self.constants).visit(module)
