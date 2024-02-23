from ast import Module, parse, stmt

from .plugin import Plugin


class PreludePlugin(Plugin):
    prelude_ast: list[stmt]

    def __init__(self, prelude: list[stmt] | str):
        if isinstance(prelude, str):
            prelude = parse(prelude).body
        self.prelude_ast = prelude

    def hook_output(self, module: Module) -> Module:
        module.body = self.prelude_ast + module.body
        return module
