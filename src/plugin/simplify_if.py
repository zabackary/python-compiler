import ast
import typing
from ast import Module
from typing import Any

from .plugin import Plugin


class SimplifyIfTransformer(ast.NodeTransformer):
    def __init__(self) -> None:
        super().__init__()

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        left = super().visit(node.left)
        right = super().visit(node.right)
        if isinstance(left, ast.Constant) and isinstance(right, ast.Constant):
            result = None
            match type(node.op):
                case ast.Add:
                    result = left.value + right.value
                case ast.Sub:
                    result = left.value - right.value
                case ast.Mult:
                    result = left.value * right.value
                case ast.Div:
                    result = left.value / right.value
                case ast.FloorDiv:
                    result = left.value // right.value
                case ast.Mod:
                    result = left.value % right.value
                case ast.Pow:
                    result = left.value ** right.value
                case ast.LShift:
                    result = left.value << right.value
                case ast.RShift:
                    result = left.value >> right.value
                case ast.BitOr:
                    result = left.value | right.value
                case ast.BitXor:
                    result = left.value ^ right.value
                case ast.BitAnd:
                    result = left.value & right.value
                case ast.MatMult:
                    result = left.value @ right.value
            if result is None:
                raise Exception(
                    f"unsupported binary operation {type(node.op).__name__}. this is a bug.")
            return ast.Constant(value=result)
        else:
            return ast.BinOp(
                left=left,
                right=right,
                op=node.op
            )

    def visit_BoolOp(self, node: ast.BoolOp) -> Any:
        visit = super().visit
        values = [visit(value) for value in node.values]
        if all([isinstance(value, ast.Constant) for value in values]):
            values = typing.cast(list[ast.Constant], values)
            result = values[0].value
            match type(node.op):
                case ast.And:
                    for value in values[1:]:
                        result = result and value.value
                case ast.Or:
                    for value in values[1:]:
                        result = result or value.value
                case _:
                    raise Exception(
                        f"unsupported boolean operation {type(node.op).__name__}. this is a bug.")
            return ast.Constant(value=result)
        else:
            return ast.BoolOp(
                values=values,
                op=node.op
            )

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        operand = super().visit(node.operand)
        if isinstance(operand, ast.Constant):
            result = None
            match type(node.op):
                case ast.UAdd:
                    result = +operand.value
                case ast.USub:
                    result = -operand.value
                case ast.Not:
                    result = not operand.value
                case ast.Invert:
                    result = ~operand.value
            if result is None:
                raise Exception(
                    f"unsupported unary operation {type(node.op).__name__}. this is a bug.")
            return ast.Constant(value=result)
        else:
            return ast.UnaryOp(
                op=node.op,
                operand=operand
            )

    def visit_If(self, node: ast.If) -> Any:
        visit = super().visit
        test = visit(node.test)
        body = [visit(stmt) for stmt in node.body]
        orelse = [visit(stmt) for stmt in node.orelse]
        if isinstance(test, ast.Constant):
            if test.value:
                return body
            else:
                return orelse
        else:
            return ast.If(
                test=test,
                body=body,
                orelse=orelse
            )

    def visit_IfExp(self, node: ast.IfExp) -> Any:
        test = super().visit(node.test)
        body = super().visit(node.body)
        orelse = super().visit(node.orelse)
        if isinstance(test, ast.Constant):
            if test.value:
                return body
            else:
                return orelse
        else:
            return ast.IfExp(
                test=test,
                body=body,
                orelse=orelse
            )


class SimplifyIfPlugin(Plugin):
    def hook_module(self, path: str, module: Module) -> Module:
        return SimplifyIfTransformer().visit(module)
