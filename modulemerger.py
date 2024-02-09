import ast

from . import exporthelper, graph
from .options import ModuleMergerOptions
from .processimportedmodule import ProcessedModule, process_imported_module


class ModuleMerger:
    source: str
    path: str
    options: ModuleMergerOptions

    def __init__(self, source: str, path: str, options: ModuleMergerOptions = ModuleMergerOptions()) -> None:
        self.source = source
        self.path = path
        self.options = options

    def merge(self) -> str:
        main_processed_module = ProcessedModule(
            self.source, self.path, "__main__", self.options)
        dependency_tree_edges: dict[str, list[str]] = {}
        dependency_tree_modules: dict[str, ProcessedModule] = {}
        dependency_queue: list[ProcessedModule] = [main_processed_module]
        while len(dependency_queue) > 0:
            module = dependency_queue.pop()
            if module.path not in dependency_tree_modules:
                # Item hasn't been processed yet
                dependency_tree_modules[module.path] = module
                dependency_tree_edges[module.path] = []
                for item in module.imports:
                    processed_module = process_imported_module(
                        item.module, module.path, self.options)
                    dependency_tree_edges[module.path].append(
                        processed_module.path)
                    dependency_queue.append(processed_module)
        dependencies = []
        dependencies = list(reversed(graph.Graph(
            dependency_tree_edges).topological_sort()))
        output: list[ast.AST] = []
        if self.options.docstring != None:
            output.append(ast.Expr(
                ast.Constant(
                    value=self.options.docstring)
            ))
        if self.options.prelude != None:
            output.extend(ast.parse(self.options.prelude, mode="exec").body)
        output.append(exporthelper.get_export_helper())
        modules: list[ast.AST] = []
        for dependency in dependencies:
            module = dependency_tree_modules[dependency]
            modules.append(module.generate_factory_ast())
            modules.append(module.generate_evaluated_factory_ast(
                list(map(
                    lambda a: dependency_tree_modules[a].name_generator.get_evaluated_factory(
                    ),
                    dependency_tree_edges[module.path]
                ))
            ))
        output.extend(modules)
        output_ast = ast.Module(
            body=output,
            type_ignores=[]
        )
        return ast.unparse(ast.fix_missing_locations(output_ast))
