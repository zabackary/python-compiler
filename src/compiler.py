import ast

from . import exporthelper, graph
from .errors import CircularDependencyError, NestedModuleRecursionError
from .options import CompilerOptions
from .processedmodule import ProcessedModule


class Compiler:
    source: str
    path: str
    options: CompilerOptions

    def __init__(self, source: str, path: str, options: CompilerOptions = CompilerOptions()) -> None:
        self.source = source
        self.path = path
        self.options = options

    def __call__(self) -> str:
        try:
            # get the main module
            main_processed_module = ProcessedModule(
                self.source, self.path, "__main__", self.options)

            # sort out all the dependencies and find a good linear order for them to
            # be loaded in using `graph.py`
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
                        processed_module = ProcessedModule.resolve(
                            item.module, module.path, self.options)
                        dependency_tree_edges[module.path].append(
                            processed_module.path)
                        dependency_queue.append(processed_module)
            try:
                dependencies = list(reversed(graph.Graph(
                    dependency_tree_edges).topological_sort()))
            except graph.TopologicalSortError:
                raise CircularDependencyError()

            output: list[ast.AST] = []

            # add the docstring at the top
            if self.options.docstring != None:
                output.append(ast.Expr(
                    ast.Constant(
                        value=self.options.docstring)
                ))

            # add helpers needed by the module factories for each mode
            if self.options.export_dictionary_mode == "munch":
                output.append(exporthelper.get_export_helper(use_munch=True))
            elif self.options.export_dictionary_mode == "dict":
                output.append(exporthelper.get_export_helper(use_munch=False))
            else:
                # export_dictionary_mode == "class", we don't need a helper
                pass

            # actually do the code generation
            for dependency in dependencies:
                module = dependency_tree_modules[dependency]
                output.append(module.generate_factory_ast())
                output.append(module.generate_evaluated_factory_ast(
                    list(map(
                        lambda a: dependency_tree_modules[a].name_generator.get_evaluated_factory(
                        ),
                        dependency_tree_edges[module.path]
                    ))
                ))

            # put the output into a Module
            output_ast = ast.Module(
                body=output,
                type_ignores=[]
            )

            # let plugins do their thing
            for plugin in self.options.plugins:
                output_ast = plugin.hook_output(output_ast)

            # actually generate the output code string
            return ast.unparse(ast.fix_missing_locations(output_ast))
        except RecursionError:
            raise NestedModuleRecursionError()
