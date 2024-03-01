import ast
from ast import Module
from typing import Any

from ..errors import _terminal_colors
from .plugin import Plugin


class AssignmentToConstantError(Exception):
    path: str
    lineno: int
    colno: int
    ident: str

    errcode = "assignment-to-constant"

    def __init__(self, ident: str, path: str, lineno: int, colno: int) -> None:
        self.ident = ident
        self.path = path
        self.lineno = lineno
        self.colno = colno

    def __str__(self) -> str:
        return f"illegal assignment to a defined compiler constant\n  {_terminal_colors.OKBLUE}{_terminal_colors.BOLD}note:{_terminal_colors.ENDC} the identifier was named {_terminal_colors.OKCYAN}{self.ident}{_terminal_colors.ENDC}\n  at {self.path} {self.lineno}:{self.colno}"


class ConstantsTransformer(ast.NodeTransformer):
    top_level_statements: list[ast.stmt]
    constants: dict[str, str | bool | int | float]
    path: str

    def __init__(self, constants: dict[str, str | bool | int | float], path: str) -> None:
        self.constants = constants
        self.top_level_statements = []
        self.path = path
        super().__init__()

    def visit_Module(self, node: Module) -> Any:
        self.top_level_statements = node.body
        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> Any:
        if isinstance(node.ctx, ast.Load):
            if node.id in self.constants:
                return ast.Constant(value=self.constants[node.id])
        return self.generic_visit(node)

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
                        target.id, self.path, node.lineno, node.col_offset)
        # change the assignment to a expr if there's nothing it's assigning to
        if len(node.targets) == 0:
            # if it's a constant, we know for sure there are no side effects
            if isinstance(node.value, ast.Constant):
                return None
            return self.generic_visit(ast.Expr(value=node.value))
        return self.generic_visit(node)

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
                    node.target.id, self.path, node.lineno, node.col_offset)
        return self.generic_visit(node)


class ConstantsPlugin(Plugin):
    constants: dict[str, str | bool | int | float]

    def __init__(self, constants: dict[str, str | bool | int | float]):
        self.constants = constants

    def hook_module(self, path: str, module: Module) -> Module:
        return ConstantsTransformer(self.constants, path).visit(module)
