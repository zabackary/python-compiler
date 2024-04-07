from ast import Module, fix_missing_locations, parse, unparse
from typing import Any

from ..python_minifier import minify, unparse  # type:ignore
from .plugin import Plugin


class MinifyPlugin(Plugin):
    minify_kwargs: dict[str, Any]

    def __init__(self, **minify_kwargs) -> None:
        self.minify_kwargs = minify_kwargs
        return super().__init__()

    def hook_unparse(self, module: Module) -> str:
        source = unparse(fix_missing_locations(module))
        source = minify(
            remove_annotations=True,
            combine_imports=True,
            hoist_literals=True,
            rename_locals=True,
            rename_globals=True,
            remove_pass=True,
            remove_object_base=True,
            remove_literal_statements=True,
            constant_folding=True,
            convert_posargs_to_args=True,
            remove_explicit_return_none=True,
            remove_debug=True,
            # user overrides
            **self.minify_kwargs,
            # input source
            source=source,
        )
        return source
